"""Contrarian trading strategies."""

from ..core.strategy import BaseStrategy
from ..core.signals import Signal
from ..providers.sentiment.finbert import FinBERTContrarianProvider
from .registry import register


@register(
    name="contrarian",
    description="Contrarian strategy - buy on negative sentiment",
    default_provider="finbert_contrarian",
)
class ContrarianStrategy(BaseStrategy):
    """Contrarian trading strategy.

    Buys when sentiment is negative (others are fearful)
    and sells when sentiment is positive (others are greedy).
    """

    def initialize(
        self,
        threshold: float = 0.99,
        **kwargs
    ):
        """Initialize contrarian strategy.

        Args:
            threshold: Minimum probability to trade
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = FinBERTContrarianProvider()

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold,
            **kwargs
        )


@register(
    name="dip_buyer",
    description="Buy-the-dip strategy on negative sentiment",
    default_provider="finbert_contrarian",
)
class DipBuyerStrategy(BaseStrategy):
    """Dip buying strategy - only buys, never shorts.

    Waits for negative sentiment (dips) and buys,
    but never initiates short positions.
    """

    def initialize(
        self,
        threshold: float = 0.99,
        **kwargs
    ):
        """Initialize dip buyer strategy.

        Args:
            threshold: Minimum negative sentiment probability to buy
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = FinBERTContrarianProvider()

        super().initialize(
            signal_provider=signal_provider,
            threshold=threshold,
            **kwargs
        )

    def execute_signal(self, signal: Signal) -> bool:
        """Execute signal - only buy signals, ignore sells.

        Override to implement buy-only behavior.
        """
        # Only act on buy signals
        if signal.action != "buy":
            return False

        if signal.confidence < self.threshold:
            return False

        cash, last_price, quantity = self.position_sizing()

        if last_price is None or quantity <= 0:
            return False

        if cash < quantity * last_price:
            return False

        return self._execute_buy(quantity)
