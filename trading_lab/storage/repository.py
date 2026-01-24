"""Data access layer for Trading Lab."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from .models import BacktestRun, Trade, DailyStat


class BacktestRepository:
    """Repository for backtest run operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        strategy_name: str,
        asset: str,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 100000.0,
        signal_provider: str | None = None,
        exchange: str | None = None,
        parameters: dict | None = None,
    ) -> BacktestRun:
        """Create a new backtest run."""
        run = BacktestRun(
            strategy_name=strategy_name,
            signal_provider=signal_provider,
            asset=asset,
            asset_type=asset_type,
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash,
            parameters=parameters,
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.flush()  # Get ID without committing
        return run

    def get(self, backtest_id: int) -> Optional[BacktestRun]:
        """Get a backtest by ID."""
        return self.db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()

    def list(
        self,
        strategy_name: str | None = None,
        asset: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BacktestRun]:
        """List backtests with optional filters."""
        query = self.db.query(BacktestRun)

        if strategy_name:
            query = query.filter(BacktestRun.strategy_name == strategy_name)
        if asset:
            query = query.filter(BacktestRun.asset == asset)
        if status:
            query = query.filter(BacktestRun.status == status)

        return query.order_by(desc(BacktestRun.created_at)).offset(offset).limit(limit).all()

    def update_status(
        self,
        backtest_id: int,
        status: str,
        error_message: str | None = None
    ) -> Optional[BacktestRun]:
        """Update backtest status."""
        run = self.get(backtest_id)
        if run:
            run.status = status
            if error_message:
                run.error_message = error_message
            if status == "running":
                run.started_at = datetime.utcnow()
            elif status in ("completed", "failed"):
                run.completed_at = datetime.utcnow()
        return run

    def update_progress(
        self,
        backtest_id: int,
        progress_percent: float,
        progress_message: str = "",
        current_date: datetime | None = None,
        processed_days: int | None = None,
    ) -> Optional[BacktestRun]:
        """Update backtest progress.

        Args:
            backtest_id: ID of the backtest to update
            progress_percent: Progress percentage (0-100)
            progress_message: Optional status message
            current_date: Current simulation date
            processed_days: Number of days processed so far

        Returns:
            Updated BacktestRun or None if not found
        """
        run = self.get(backtest_id)
        if run:
            run.progress_percent = progress_percent
            if progress_message:
                run.progress_message = progress_message
            if current_date is not None:
                run.current_date = current_date
            if processed_days is not None:
                run.processed_days = processed_days
        return run

    def update_results(
        self,
        backtest_id: int,
        final_value: float,
        total_return: float,
        total_trades: int = 0,
        winning_trades: int = 0,
        losing_trades: int = 0,
        sharpe_ratio: float | None = None,
        max_drawdown: float | None = None,
        volatility: float | None = None,
    ) -> Optional[BacktestRun]:
        """Update backtest results."""
        run = self.get(backtest_id)
        if run:
            run.final_value = final_value
            run.total_return = total_return
            run.total_trades = total_trades
            run.winning_trades = winning_trades
            run.losing_trades = losing_trades
            run.sharpe_ratio = sharpe_ratio
            run.max_drawdown = max_drawdown
            run.volatility = volatility
            run.status = "completed"
            run.completed_at = datetime.utcnow()
        return run

    def delete(self, backtest_id: int) -> bool:
        """Delete a backtest and all associated data."""
        run = self.get(backtest_id)
        if run:
            self.db.delete(run)
            return True
        return False

    def compare(self, backtest_ids: list[int]) -> list[BacktestRun]:
        """Get multiple backtests for comparison."""
        return self.db.query(BacktestRun).filter(
            BacktestRun.id.in_(backtest_ids)
        ).all()


class TradeRepository:
    """Repository for trade operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        backtest_id: int,
        timestamp: datetime,
        asset: str,
        side: str,
        quantity: float,
        price: float,
        signal_action: str | None = None,
        signal_confidence: float | None = None,
        signal_reasoning: str | None = None,
    ) -> Trade:
        """Create a new trade record."""
        trade = Trade(
            backtest_id=backtest_id,
            timestamp=timestamp,
            asset=asset,
            side=side,
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            signal_action=signal_action,
            signal_confidence=signal_confidence,
            signal_reasoning=signal_reasoning,
            status="filled",
        )
        self.db.add(trade)
        self.db.flush()
        return trade

    def list_for_backtest(
        self,
        backtest_id: int,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[Trade]:
        """Get all trades for a backtest."""
        return self.db.query(Trade).filter(
            Trade.backtest_id == backtest_id
        ).order_by(Trade.timestamp).offset(offset).limit(limit).all()

    def bulk_create(self, trades: list[dict], backtest_id: int) -> int:
        """Bulk insert trades for a backtest."""
        trade_objects = [
            Trade(
                backtest_id=backtest_id,
                timestamp=t["timestamp"],
                asset=t["asset"],
                side=t["side"],
                quantity=t["quantity"],
                price=t["price"],
                total_value=t["quantity"] * t["price"],
                signal_action=t.get("signal_action"),
                signal_confidence=t.get("signal_confidence"),
                status="filled",
            )
            for t in trades
        ]
        self.db.bulk_save_objects(trade_objects)
        return len(trade_objects)


class DailyStatRepository:
    """Repository for daily statistics."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        backtest_id: int,
        date: datetime,
        portfolio_value: float,
        cash: float,
        positions_value: float | None = None,
        daily_return: float | None = None,
        cumulative_return: float | None = None,
    ) -> DailyStat:
        """Create a daily stat record."""
        stat = DailyStat(
            backtest_id=backtest_id,
            date=date,
            portfolio_value=portfolio_value,
            cash=cash,
            positions_value=positions_value,
            daily_return=daily_return,
            cumulative_return=cumulative_return,
        )
        self.db.add(stat)
        self.db.flush()
        return stat

    def list_for_backtest(self, backtest_id: int) -> list[DailyStat]:
        """Get all daily stats for a backtest."""
        return self.db.query(DailyStat).filter(
            DailyStat.backtest_id == backtest_id
        ).order_by(DailyStat.date).all()

    def bulk_create(self, stats: list[dict], backtest_id: int) -> int:
        """Bulk insert daily stats."""
        stat_objects = [
            DailyStat(
                backtest_id=backtest_id,
                date=s["date"],
                portfolio_value=s["portfolio_value"],
                cash=s["cash"],
                positions_value=s.get("positions_value"),
                daily_return=s.get("daily_return"),
                cumulative_return=s.get("cumulative_return"),
            )
            for s in stats
        ]
        self.db.bulk_save_objects(stat_objects)
        return len(stat_objects)
