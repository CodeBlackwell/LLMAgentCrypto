"""Backtest engine wrapper around Lumibot."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
import logging

from lumibot.backtesting import CcxtBacktesting
from lumibot.entities import Asset, TradingFee
from lumibot.strategies.strategy import Strategy

from ..core.config import BacktestConfig
from ..strategies.registry import get_strategy
from ..storage.database import get_db
from ..storage.repository import BacktestRepository, TradeRepository, DailyStatRepository

if TYPE_CHECKING:
    from .progress import ProgressTracker

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Wrapper around Lumibot for running backtests.

    Provides a clean interface for running backtests and
    storing results in the database.
    """

    # Supported exchanges
    EXCHANGES = {
        "kraken": "kraken",
        "coinbase": "coinbasepro",
        "binance": "binance",
        "bitfinex": "bitfinex",
    }

    def __init__(
        self,
        min_timestep: str = "day",
        trading_fees: Optional[dict] = None,
        progress_tracker: Optional[ProgressTracker] = None,
    ):
        """Initialize backtest engine.

        Args:
            min_timestep: Minimum time granularity ("day", "hour", "minute")
            trading_fees: Dict with "buy" and "sell" fee percentages
            progress_tracker: Optional progress tracker for reporting execution progress
        """
        self.min_timestep = min_timestep
        self.trading_fees = trading_fees or {}
        self.progress_tracker = progress_tracker

    def _build_fees(self) -> tuple[list, list]:
        """Build trading fee objects."""
        buy_fees = []
        sell_fees = []

        if "buy" in self.trading_fees:
            buy_fees.append(TradingFee(percent_fee=self.trading_fees["buy"]))
        if "sell" in self.trading_fees:
            sell_fees.append(TradingFee(percent_fee=self.trading_fees["sell"]))

        return buy_fees, sell_fees

    def _build_asset(self, symbol: str, asset_type: str) -> Asset:
        """Build a Lumibot Asset from symbol and type."""
        if asset_type == "crypto":
            return Asset(symbol=symbol, asset_type=Asset.AssetType.CRYPTO)
        elif asset_type == "stock":
            return Asset(symbol=symbol, asset_type=Asset.AssetType.STOCK)
        else:
            return Asset(symbol=symbol, asset_type=Asset.AssetType.FOREX)

    def run(
        self,
        config: BacktestConfig,
        save_to_db: bool = True,
    ) -> dict:
        """Run a backtest with the given configuration.

        Args:
            config: Backtest configuration
            save_to_db: Whether to save results to database

        Returns:
            Dictionary with backtest results
        """
        # Get strategy class
        strategy_class = get_strategy(config.strategy_name)

        # Configure backtesting
        CcxtBacktesting.MIN_TIMESTEP = self.min_timestep
        exchange_id = self.EXCHANGES.get(config.exchange, config.exchange)

        # Build parameters
        parameters = {
            "cash_at_risk": config.cash_at_risk,
            "coin": config.asset.split("/")[0],
            "quote": config.asset.split("/")[1] if "/" in config.asset else "USD",
            "asset_type": config.asset_type,
            "threshold": config.threshold,
        }

        # Build assets
        quote_symbol = parameters["quote"]
        quote_asset = self._build_asset(
            quote_symbol,
            "crypto" if config.asset_type == "crypto" else "forex"
        )

        # Build fees
        buy_fees, sell_fees = self._build_fees()

        # Calculate total_days for progress tracking
        total_days = (config.end_date - config.start_date).days + 1

        # Create database record if saving
        backtest_id = None
        if save_to_db:
            with get_db() as db:
                repo = BacktestRepository(db)
                run = repo.create(
                    strategy_name=config.strategy_name,
                    asset=config.asset,
                    asset_type=config.asset_type,
                    start_date=datetime.combine(config.start_date, datetime.min.time()),
                    end_date=datetime.combine(config.end_date, datetime.min.time()),
                    initial_cash=config.initial_cash,
                    signal_provider=config.signal_provider,
                    exchange=config.exchange,
                    parameters=parameters,
                )
                backtest_id = run.id
                repo.update_status(backtest_id, "running")

                # Set total_days in database for progress display
                if self.progress_tracker:
                    repo.update_progress(
                        backtest_id=backtest_id,
                        progress_percent=0.0,
                        progress_message="Initializing...",
                        processed_days=0,
                    )
                    # Update total_days via direct update since it's not in update_progress
                    run.total_days = total_days
                    db.commit()

        try:
            # Set phase for data fetching
            if self.progress_tracker:
                self.progress_tracker.set_phase("Fetching data...")

            # Run backtest
            kwargs = {"exchange_id": exchange_id}
            if buy_fees:
                kwargs["buy_trading_fees"] = buy_fees
            if sell_fees:
                kwargs["sell_trading_fees"] = sell_fees

            # Skip benchmark comparison to avoid CCXT data fetch issues
            # The benchmark stats would fail if CCXT can't find data for the symbol
            # Note: Lumibot handles data fetching and simulation internally
            # Progress updates during simulation require strategy-level integration (see US-006)
            if self.progress_tracker:
                self.progress_tracker.set_phase("Simulating trades...")

            results, strat_obj = strategy_class.run_backtest(
                CcxtBacktesting,
                datetime.combine(config.start_date, datetime.min.time()),
                datetime.combine(config.end_date, datetime.min.time()),
                benchmark_asset=None,  # Skip benchmark to avoid data issues
                quote_asset=quote_asset,
                parameters=parameters,
                budget=config.initial_cash,
                show_plot=False,  # Disable plotting in background
                show_tearsheet=False,  # Disable tearsheet generation
                save_tearsheet=False,  # Don't save tearsheet files
                stats_file=None,  # Don't write stats file
                **kwargs,
            )

            # Update progress tracker with final date after simulation completes
            if self.progress_tracker:
                self.progress_tracker.update(config.end_date, "Processing results...")

            # Extract results - handle dict format for max_drawdown
            max_dd = results.get("max_drawdown")
            if isinstance(max_dd, dict):
                max_dd = float(max_dd.get("drawdown", 0))
            elif max_dd is not None:
                max_dd = float(max_dd)

            sharpe = results.get("sharpe")
            if sharpe is not None:
                sharpe = float(sharpe)

            total_ret = results.get("total_return", 0)
            if total_ret is not None:
                total_ret = float(total_ret) * 100  # As percentage

            result_data = {
                "backtest_id": backtest_id,
                "strategy_name": config.strategy_name,
                "asset": config.asset,
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "initial_cash": config.initial_cash,
                "final_value": float(results.get("portfolio_value", config.initial_cash)),
                "total_return": total_ret,
                "sharpe_ratio": sharpe,
                "max_drawdown": max_dd,
                "status": "completed",
            }

            # Save to database
            if save_to_db and backtest_id:
                with get_db() as db:
                    repo = BacktestRepository(db)
                    repo.update_results(
                        backtest_id=backtest_id,
                        final_value=result_data["final_value"],
                        total_return=result_data["total_return"],
                        sharpe_ratio=result_data.get("sharpe_ratio"),
                        max_drawdown=result_data.get("max_drawdown"),
                    )

            return result_data

        except Exception as e:
            logger.exception(f"Backtest failed: {e}")

            if save_to_db and backtest_id:
                with get_db() as db:
                    repo = BacktestRepository(db)
                    repo.update_status(backtest_id, "failed", str(e))

            raise


def run_backtest(config: BacktestConfig, **engine_kwargs) -> dict:
    """Convenience function to run a backtest.

    Args:
        config: Backtest configuration
        **engine_kwargs: Passed to BacktestEngine

    Returns:
        Dictionary with results
    """
    engine = BacktestEngine(**engine_kwargs)
    return engine.run(config)
