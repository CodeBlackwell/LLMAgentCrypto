"""Position sizing strategies for trading."""

from typing import Protocol, runtime_checkable
from abc import ABC, abstractmethod


@runtime_checkable
class PositionSizer(Protocol):
    """Protocol for position sizing calculations.

    Position sizers determine how much of an asset to trade
    based on available capital and risk parameters.
    """

    def calculate(self, cash: float, price: float, **kwargs) -> float:
        """Calculate the quantity to trade.

        Args:
            cash: Available cash for trading
            price: Current price of the asset
            **kwargs: Additional parameters (volatility, risk metrics, etc.)

        Returns:
            Quantity of asset to trade
        """
        ...


class PercentOfCash:
    """Size positions as a percentage of available cash.

    The simplest sizing strategy - allocate a fixed percentage
    of cash to each position.
    """

    def __init__(self, percent: float = 0.25):
        """Initialize with allocation percentage.

        Args:
            percent: Fraction of cash to allocate (0.0 to 1.0)
        """
        if not 0.0 < percent <= 1.0:
            raise ValueError(f"Percent must be between 0 and 1, got {percent}")
        self.percent = percent

    def calculate(self, cash: float, price: float, **kwargs) -> float:
        if price <= 0:
            return 0.0
        return (cash * self.percent) / price


class FixedQuantity:
    """Trade a fixed quantity regardless of price or cash.

    Useful for testing or when position size is predetermined.
    """

    def __init__(self, quantity: float):
        """Initialize with fixed quantity.

        Args:
            quantity: Fixed quantity to trade
        """
        if quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {quantity}")
        self.quantity = quantity

    def calculate(self, cash: float, price: float, **kwargs) -> float:
        # Ensure we have enough cash
        if cash < price * self.quantity:
            return cash / price if price > 0 else 0.0
        return self.quantity


class VolatilityAdjusted:
    """Adjust position size based on asset volatility.

    Reduces position size for volatile assets and increases
    for stable assets, maintaining consistent risk exposure.
    """

    def __init__(
        self,
        target_risk: float = 0.02,
        max_position_pct: float = 0.25
    ):
        """Initialize with risk parameters.

        Args:
            target_risk: Target portfolio risk per trade (default 2%)
            max_position_pct: Maximum position as % of cash
        """
        self.target_risk = target_risk
        self.max_position_pct = max_position_pct

    def calculate(self, cash: float, price: float, **kwargs) -> float:
        volatility = kwargs.get("volatility", 0.02)  # Default 2% daily vol

        if volatility <= 0 or price <= 0:
            return 0.0

        # Risk-adjusted position size
        risk_adjusted = (cash * self.target_risk) / (price * volatility)

        # Cap at maximum position
        max_quantity = (cash * self.max_position_pct) / price

        return min(risk_adjusted, max_quantity)


class KellyCriterion:
    """Position sizing using the Kelly Criterion.

    Optimal sizing based on win rate and win/loss ratio.
    Uses fractional Kelly for more conservative sizing.
    """

    def __init__(
        self,
        win_rate: float = 0.55,
        win_loss_ratio: float = 1.5,
        fraction: float = 0.25,
        max_position_pct: float = 0.25
    ):
        """Initialize with Kelly parameters.

        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            win_loss_ratio: Average win / average loss
            fraction: Kelly fraction (0.25 = quarter Kelly)
            max_position_pct: Maximum position as % of cash
        """
        self.win_rate = win_rate
        self.win_loss_ratio = win_loss_ratio
        self.fraction = fraction
        self.max_position_pct = max_position_pct

    def calculate(self, cash: float, price: float, **kwargs) -> float:
        if price <= 0:
            return 0.0

        # Kelly formula: f = (bp - q) / b
        # where b = win/loss ratio, p = win rate, q = 1 - p
        b = self.win_loss_ratio
        p = self.win_rate
        q = 1 - p

        kelly_pct = (b * p - q) / b
        kelly_pct = max(0, kelly_pct)  # Don't go negative

        # Apply fractional Kelly and cap
        position_pct = min(kelly_pct * self.fraction, self.max_position_pct)

        return (cash * position_pct) / price
