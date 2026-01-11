"""Random trading strategy - baseline for comparison."""

from ..core.strategy import BaseStrategy
from ..core.signals import RandomSignalProvider
from .registry import register


@register(
    name="random",
    description="Random buy/sell/hold baseline strategy",
    default_provider="random",
)
class RandomStrategy(BaseStrategy):
    """Random trading strategy for baseline comparison.

    Makes random buy/sell/hold decisions each trading iteration.
    Useful for establishing baseline performance metrics.
    """

    def initialize(self, seed: int | None = None, **kwargs):
        """Initialize random strategy.

        Args:
            seed: Random seed for reproducibility
            **kwargs: Passed to BaseStrategy.initialize()
        """
        # Create random signal provider
        signal_provider = RandomSignalProvider(seed=seed)

        # Initialize base strategy with random provider
        super().initialize(
            signal_provider=signal_provider,
            threshold=0.0,  # Always act on random signals
            **kwargs
        )

    def on_trading_iteration(self):
        """Execute random trading decision."""
        signal = self.get_signal()
        self.execute_signal(signal)
