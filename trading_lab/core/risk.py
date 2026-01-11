"""Risk management for trading strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Literal, Optional, runtime_checkable
from datetime import date

from .signals import Signal


@dataclass
class RiskState:
    """Current risk management state.

    Tracks position, drawdown, and daily P&L for risk calculations.
    """
    # Position tracking
    current_position: float = 0.0
    entry_price: Optional[float] = None
    position_value: float = 0.0

    # High water mark for drawdown
    peak_portfolio_value: float = 0.0
    current_portfolio_value: float = 0.0

    # Daily tracking
    day_start_value: float = 0.0
    current_date: Optional[date] = None
    daily_pnl: float = 0.0
    daily_trades: int = 0

    # Order tracking
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None

    @property
    def drawdown(self) -> float:
        """Current drawdown as decimal (0.10 = 10% drawdown)."""
        if self.peak_portfolio_value <= 0:
            return 0.0
        return (self.peak_portfolio_value - self.current_portfolio_value) / self.peak_portfolio_value

    @property
    def daily_return(self) -> float:
        """Current day's return as decimal."""
        if self.day_start_value <= 0:
            return 0.0
        return (self.current_portfolio_value - self.day_start_value) / self.day_start_value


@dataclass
class RiskDecision:
    """Decision from risk manager.

    Indicates whether a trade should proceed and any modifications.
    """
    allow_trade: bool
    reason: str = ""
    modified_quantity: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None

    # Risk metrics at time of decision
    current_drawdown: float = 0.0
    daily_pnl: float = 0.0


@runtime_checkable
class RiskRule(Protocol):
    """Protocol for individual risk rules.

    Each rule evaluates a specific risk condition and
    can block or modify trades.
    """

    @property
    def name(self) -> str:
        """Rule identifier."""
        ...

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        """Evaluate if trade passes this risk rule."""
        ...


class MaxPositionSizeRule:
    """Limits maximum position size as % of portfolio."""

    def __init__(self, max_percent: float = 0.25):
        """Initialize with max position percentage.

        Args:
            max_percent: Maximum position as fraction (0.25 = 25%)
        """
        if not 0.0 < max_percent <= 1.0:
            raise ValueError(f"max_percent must be between 0 and 1, got {max_percent}")
        self.max_percent = max_percent

    @property
    def name(self) -> str:
        return f"max_position_{self.max_percent:.0%}"

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        if state.current_portfolio_value <= 0 or price <= 0:
            return RiskDecision(allow_trade=True, reason="No portfolio value to check")

        max_value = state.current_portfolio_value * self.max_percent
        proposed_value = quantity * price

        if proposed_value > max_value:
            allowed_quantity = max_value / price
            return RiskDecision(
                allow_trade=True,
                reason=f"Position reduced to {self.max_percent:.0%} of portfolio",
                modified_quantity=allowed_quantity,
            )

        return RiskDecision(allow_trade=True, reason="Within position limits")


class StopLossRule:
    """Attaches stop-loss orders to positions."""

    def __init__(self, percent: float = 0.05):
        """Initialize with stop-loss percentage.

        Args:
            percent: Stop loss as fraction below entry (0.05 = 5%)
        """
        if not 0.0 < percent < 1.0:
            raise ValueError(f"percent must be between 0 and 1, got {percent}")
        self.percent = percent

    @property
    def name(self) -> str:
        return f"stop_loss_{self.percent:.0%}"

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        if signal.action == "buy" and price > 0:
            stop_price = price * (1 - self.percent)
            return RiskDecision(
                allow_trade=True,
                reason=f"Stop-loss set at {stop_price:.2f}",
                stop_loss_price=stop_price,
            )
        return RiskDecision(allow_trade=True, reason="No stop-loss for sell/hold")


class TakeProfitRule:
    """Attaches take-profit orders to positions."""

    def __init__(self, percent: float = 0.10):
        """Initialize with take-profit percentage.

        Args:
            percent: Take profit as fraction above entry (0.10 = 10%)
        """
        if not 0.0 < percent:
            raise ValueError(f"percent must be positive, got {percent}")
        self.percent = percent

    @property
    def name(self) -> str:
        return f"take_profit_{self.percent:.0%}"

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        if signal.action == "buy" and price > 0:
            target_price = price * (1 + self.percent)
            return RiskDecision(
                allow_trade=True,
                reason=f"Take-profit set at {target_price:.2f}",
                take_profit_price=target_price,
            )
        return RiskDecision(allow_trade=True, reason="No take-profit for sell/hold")


class DrawdownCircuitBreaker:
    """Stops trading when drawdown exceeds threshold."""

    def __init__(self, max_drawdown: float = 0.20):
        """Initialize with max drawdown threshold.

        Args:
            max_drawdown: Maximum drawdown before halting (0.20 = 20%)
        """
        if not 0.0 < max_drawdown < 1.0:
            raise ValueError(f"max_drawdown must be between 0 and 1, got {max_drawdown}")
        self.max_drawdown = max_drawdown

    @property
    def name(self) -> str:
        return f"drawdown_breaker_{self.max_drawdown:.0%}"

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        if state.drawdown >= self.max_drawdown:
            return RiskDecision(
                allow_trade=False,
                reason=f"Trading halted: drawdown {state.drawdown:.1%} exceeds {self.max_drawdown:.1%}",
                current_drawdown=state.drawdown,
            )
        return RiskDecision(
            allow_trade=True,
            reason=f"Drawdown {state.drawdown:.1%} within limits",
            current_drawdown=state.drawdown,
        )


class DailyLossLimit:
    """Stops trading when daily loss limit is reached."""

    def __init__(self, max_daily_loss: float = 0.05):
        """Initialize with max daily loss.

        Args:
            max_daily_loss: Maximum daily loss as fraction (0.05 = 5%)
        """
        if not 0.0 < max_daily_loss < 1.0:
            raise ValueError(f"max_daily_loss must be between 0 and 1, got {max_daily_loss}")
        self.max_daily_loss = max_daily_loss

    @property
    def name(self) -> str:
        return f"daily_loss_limit_{self.max_daily_loss:.0%}"

    def evaluate(
        self,
        signal: Signal,
        quantity: float,
        price: float,
        state: RiskState,
    ) -> RiskDecision:
        if state.daily_return <= -self.max_daily_loss:
            return RiskDecision(
                allow_trade=False,
                reason=f"Daily loss limit hit: {state.daily_return:.1%}",
                daily_pnl=state.daily_pnl,
            )
        return RiskDecision(
            allow_trade=True,
            reason=f"Daily P&L {state.daily_return:.1%} within limits",
            daily_pnl=state.daily_pnl,
        )


class RiskManager:
    """Aggregates risk rules and evaluates trades.

    Applies all configured risk rules to proposed trades
    and combines their decisions.
    """

    def __init__(self, rules: list[RiskRule] | None = None):
        """Initialize with list of risk rules.

        Args:
            rules: List of RiskRule implementations
        """
        self.rules: list[RiskRule] = rules or []
        self.state = RiskState()

    def add_rule(self, rule: RiskRule) -> "RiskManager":
        """Add a risk rule (fluent interface)."""
        self.rules.append(rule)
        return self

    def update_state(
        self,
        portfolio_value: float,
        position: float = 0.0,
        entry_price: Optional[float] = None,
    ) -> None:
        """Update risk state with current portfolio status."""
        today = date.today()

        # Reset daily tracking on new day
        if self.state.current_date != today:
            self.state.day_start_value = portfolio_value
            self.state.current_date = today
            self.state.daily_pnl = 0.0
            self.state.daily_trades = 0

        # Update portfolio tracking
        self.state.current_portfolio_value = portfolio_value
        self.state.peak_portfolio_value = max(
            self.state.peak_portfolio_value,
            portfolio_value
        )

        # Update position tracking
        self.state.current_position = position
        if entry_price:
            self.state.entry_price = entry_price

    def evaluate_trade(
        self,
        signal: Signal,
        quantity: float,
        price: float,
    ) -> RiskDecision:
        """Evaluate a proposed trade against all risk rules.

        Returns combined decision from all rules.
        All rules must pass for trade to be allowed.
        Quantity modifications are accumulated.
        """
        final_decision = RiskDecision(allow_trade=True, reason="")
        final_quantity = quantity
        reasons = []

        for rule in self.rules:
            decision = rule.evaluate(signal, final_quantity, price, self.state)

            if not decision.allow_trade:
                # Any rule can block the trade
                return RiskDecision(
                    allow_trade=False,
                    reason=f"[{rule.name}] {decision.reason}",
                    current_drawdown=self.state.drawdown,
                    daily_pnl=self.state.daily_pnl,
                )

            # Accumulate modifications
            if decision.modified_quantity is not None:
                final_quantity = min(final_quantity, decision.modified_quantity)

            if decision.stop_loss_price is not None:
                final_decision.stop_loss_price = decision.stop_loss_price

            if decision.take_profit_price is not None:
                final_decision.take_profit_price = decision.take_profit_price

            reasons.append(f"[{rule.name}] OK")

        final_decision.modified_quantity = final_quantity if final_quantity != quantity else None
        final_decision.reason = "; ".join(reasons) if reasons else "No rules applied"
        final_decision.current_drawdown = self.state.drawdown
        final_decision.daily_pnl = self.state.daily_pnl

        return final_decision

    def check_stop_loss(self, current_price: float) -> bool:
        """Check if stop-loss should trigger."""
        if self.state.stop_loss_price and current_price <= self.state.stop_loss_price:
            return True
        return False

    def check_take_profit(self, current_price: float) -> bool:
        """Check if take-profit should trigger."""
        if self.state.take_profit_price and current_price >= self.state.take_profit_price:
            return True
        return False

    def reset_exit_prices(self) -> None:
        """Clear stop-loss and take-profit prices."""
        self.state.stop_loss_price = None
        self.state.take_profit_price = None


# Factory functions for common configurations

def create_default_risk_manager() -> RiskManager:
    """Create RiskManager with sensible defaults."""
    return RiskManager([
        MaxPositionSizeRule(max_percent=0.25),
        StopLossRule(percent=0.05),
        TakeProfitRule(percent=0.10),
        DrawdownCircuitBreaker(max_drawdown=0.20),
        DailyLossLimit(max_daily_loss=0.05),
    ])


def create_aggressive_risk_manager() -> RiskManager:
    """Create RiskManager for aggressive trading."""
    return RiskManager([
        MaxPositionSizeRule(max_percent=0.50),
        StopLossRule(percent=0.10),
        TakeProfitRule(percent=0.20),
        DrawdownCircuitBreaker(max_drawdown=0.30),
    ])


def create_conservative_risk_manager() -> RiskManager:
    """Create RiskManager for conservative trading."""
    return RiskManager([
        MaxPositionSizeRule(max_percent=0.10),
        StopLossRule(percent=0.02),
        TakeProfitRule(percent=0.05),
        DrawdownCircuitBreaker(max_drawdown=0.10),
        DailyLossLimit(max_daily_loss=0.02),
    ])
