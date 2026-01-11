"""Base strategy class with common trading functionality."""

from typing import Literal, Optional
from datetime import timedelta

from lumibot.entities import Asset
from lumibot.strategies.strategy import Strategy

from .signals import Signal, SignalProvider
from .sizing import PositionSizer, PercentOfCash
from .risk import RiskManager


class BaseStrategy(Strategy):
    """Abstract base class for all trading strategies.

    Provides common functionality:
    - Position sizing
    - Order execution with trade tracking
    - Signal provider integration
    - Multi-asset support

    Subclasses should implement `on_trading_iteration()` to define
    trading logic, calling `get_signal()` and `execute_signal()`.
    """

    def initialize(
        self,
        signal_provider: SignalProvider | None = None,
        sizer: PositionSizer | None = None,
        risk_manager: RiskManager | None = None,
        threshold: float = 0.7,
        cash_at_risk: float = 0.25,
        coin: str = "BTC",
        quote: str = "USD",
        asset_type: Literal["crypto", "stock", "forex"] = "crypto",
        lookback_days: int = 3,
        **kwargs
    ):
        """Initialize the strategy with common parameters.

        Args:
            signal_provider: Provider for trading signals (optional)
            sizer: Position sizing strategy (default: PercentOfCash)
            risk_manager: Risk management rules (optional)
            threshold: Minimum confidence to act on signals
            cash_at_risk: Position size as fraction of cash (if no sizer)
            coin: Asset symbol to trade
            quote: Quote currency
            asset_type: Type of asset (crypto, stock, forex)
            lookback_days: Days of history for signal generation
            **kwargs: Additional strategy-specific parameters
        """
        # Market configuration
        if asset_type == "crypto":
            self.set_market("24/7")
        else:
            self.set_market("NYSE")

        self.sleeptime = "1D"

        # Core parameters
        self.signal_provider = signal_provider
        self.sizer = sizer or PercentOfCash(cash_at_risk)
        self.risk_manager = risk_manager
        self.threshold = threshold
        self.cash_at_risk = cash_at_risk
        self.lookback_days = lookback_days

        # Asset configuration
        self.coin = coin
        self.quote = quote
        self.asset_type = asset_type

        # Build asset objects
        self._asset = self._build_asset(coin, asset_type)
        self._quote_asset = self._build_asset(quote, "crypto" if asset_type == "crypto" else "forex")

        # Trading state
        self.last_trade: str | None = None
        self.last_signal: Signal | None = None

    def _build_asset(self, symbol: str, asset_type: str) -> Asset:
        """Build a Lumibot Asset object."""
        if asset_type == "crypto":
            return Asset(symbol=symbol, asset_type=Asset.AssetType.CRYPTO)
        elif asset_type == "stock":
            return Asset(symbol=symbol, asset_type=Asset.AssetType.STOCK)
        else:
            return Asset(symbol=symbol, asset_type=Asset.AssetType.FOREX)

    def position_sizing(self) -> tuple[float, float | None, float]:
        """Calculate position size for current trade.

        Returns:
            Tuple of (cash, last_price, quantity)
            If price is unavailable, returns (cash, None, 0)
        """
        cash = self.get_cash()
        last_price = self.get_last_price(self._asset, quote=self._quote_asset)

        if last_price is None:
            return cash, None, 0

        quantity = self.sizer.calculate(cash, last_price)
        return cash, last_price, quantity

    def get_dates(self) -> tuple[str, str]:
        """Get current date and lookback date for signal generation.

        Returns:
            Tuple of (today, lookback_date) as YYYY-MM-DD strings
        """
        today = self.get_datetime()
        lookback = today - timedelta(days=self.lookback_days)
        return today.strftime("%Y-%m-%d"), lookback.strftime("%Y-%m-%d")

    def get_signal(self) -> Signal:
        """Get trading signal from the signal provider.

        Returns:
            Signal with action, confidence, and reasoning

        Raises:
            ValueError: If no signal provider configured
        """
        if self.signal_provider is None:
            raise ValueError("No signal provider configured")

        today, lookback = self.get_dates()
        context = {
            "current_date": today,
            "lookback_date": lookback,
            "lookback_days": self.lookback_days,
            "asset_type": self.asset_type,
        }

        signal = self.signal_provider.get_signal(
            asset=f"{self.coin}/{self.quote}",
            context=context
        )
        self.last_signal = signal
        return signal

    def execute_signal(self, signal: Signal) -> bool:
        """Execute a trading signal if it meets threshold.

        Args:
            signal: Trading signal to execute

        Returns:
            True if an order was placed, False otherwise
        """
        # Check confidence threshold
        if signal.confidence < self.threshold:
            return False

        cash, last_price, quantity = self.position_sizing()

        if last_price is None or quantity <= 0:
            return False

        if cash < quantity * last_price:
            return False

        # Evaluate through risk manager if configured
        if self.risk_manager is not None:
            decision = self.risk_manager.evaluate_trade(signal, quantity, last_price)

            if not decision.allow_trade:
                return False

            # Apply quantity modification if any
            if decision.modified_quantity is not None:
                quantity = decision.modified_quantity

            # Store exit prices on the risk manager state
            if decision.stop_loss_price is not None:
                self.risk_manager.state.stop_loss_price = decision.stop_loss_price
            if decision.take_profit_price is not None:
                self.risk_manager.state.take_profit_price = decision.take_profit_price

        if signal.action == "buy":
            return self._execute_buy(quantity)
        elif signal.action == "sell":
            return self._execute_sell(quantity)

        return False  # hold

    def _execute_buy(self, quantity: float) -> bool:
        """Execute a buy order."""
        # Close any short position first
        if self.last_trade == "sell":
            self.sell_all()
            if self.risk_manager:
                self.risk_manager.reset_exit_prices()

        order = self.create_order(
            self._asset,
            quantity,
            "buy",
            type="market",
            quote=self._quote_asset,
        )
        self.submit_order(order)
        self.last_trade = "buy"

        # Track entry price for risk management
        if self.risk_manager:
            last_price = self.get_last_price(self._asset, quote=self._quote_asset)
            if last_price:
                self.risk_manager.state.entry_price = last_price

        return True

    def _execute_sell(self, quantity: float) -> bool:
        """Execute a sell order."""
        # Close any long position first
        if self.last_trade == "buy":
            self.sell_all()
            if self.risk_manager:
                self.risk_manager.reset_exit_prices()

        order = self.create_order(
            self._asset,
            quantity,
            "sell",
            type="market",
            quote=self._quote_asset,
        )
        self.submit_order(order)
        self.last_trade = "sell"
        return True

    def on_trading_iteration(self):
        """Main trading logic - override in subclasses.

        Default implementation uses signal provider if configured.
        Includes risk management checks for stop-loss and take-profit.
        """
        # Update risk manager state
        self._update_risk_state()

        # Check stop-loss and take-profit triggers
        if self._check_exit_triggers():
            return  # Position was closed, skip signal processing

        if self.signal_provider is not None:
            signal = self.get_signal()
            self.execute_signal(signal)

    def _update_risk_state(self) -> None:
        """Update the risk manager with current portfolio state."""
        if self.risk_manager is None:
            return

        portfolio_value = self.get_portfolio_value()
        position = self.get_position(self._asset)
        position_quantity = position.quantity if position else 0.0

        self.risk_manager.update_state(
            portfolio_value=portfolio_value,
            position=position_quantity,
            entry_price=self.risk_manager.state.entry_price,
        )

    def _check_exit_triggers(self) -> bool:
        """Check and execute stop-loss or take-profit exits.

        Returns:
            True if an exit was triggered and position closed.
        """
        if self.risk_manager is None:
            return False

        # Only check if we have a position
        position = self.get_position(self._asset)
        if not position or position.quantity <= 0:
            return False

        last_price = self.get_last_price(self._asset, quote=self._quote_asset)
        if last_price is None:
            return False

        # Check stop-loss
        if self.risk_manager.check_stop_loss(last_price):
            self.sell_all()
            self.risk_manager.reset_exit_prices()
            self.last_trade = None
            return True

        # Check take-profit
        if self.risk_manager.check_take_profit(last_price):
            self.sell_all()
            self.risk_manager.reset_exit_prices()
            self.last_trade = None
            return True

        return False
