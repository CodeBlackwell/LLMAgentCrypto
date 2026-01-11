"""Signal generation abstractions for trading strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


@dataclass
class Signal:
    """Trading signal with action, confidence, and metadata.

    Attributes:
        action: Trading action to take (buy, sell, or hold)
        confidence: Confidence score from 0.0 to 1.0
        reasoning: Human-readable explanation of the signal
        metadata: Additional data (e.g., sentiment scores, news sources)
    """
    action: Literal["buy", "sell", "hold"]
    confidence: float
    reasoning: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
        if self.action not in ("buy", "sell", "hold"):
            raise ValueError(f"Action must be buy, sell, or hold, got {self.action}")


@runtime_checkable
class SignalProvider(Protocol):
    """Protocol for all signal generation methods.

    Signal providers analyze data sources (news, prices, indicators)
    and generate trading signals with confidence scores.

    Implementations should be stateless and thread-safe.
    """

    @property
    def name(self) -> str:
        """Unique identifier for this signal provider."""
        ...

    def get_signal(self, asset: str, context: dict) -> Signal:
        """Generate a trading signal for the given asset.

        Args:
            asset: Asset symbol (e.g., "BTC/USD", "AAPL")
            context: Additional context including:
                - current_date: datetime of signal generation
                - lookback_days: number of days of history to consider
                - asset_type: "crypto", "stock", or "forex"

        Returns:
            Signal with action, confidence, and reasoning
        """
        ...


class RandomSignalProvider:
    """Baseline signal provider using random selection.

    Useful for establishing baseline performance and testing.
    """

    def __init__(self, seed: int | None = None):
        import random
        self._random = random.Random(seed)

    @property
    def name(self) -> str:
        return "random"

    def get_signal(self, asset: str, context: dict) -> Signal:
        action = self._random.choice(["buy", "sell", "hold"])
        confidence = self._random.uniform(0.3, 0.9)
        return Signal(
            action=action,
            confidence=confidence,
            reasoning="Random selection (baseline)",
            metadata={"provider": "random"}
        )


class CompositeSignalProvider:
    """Combines multiple signal providers with configurable weights.

    Aggregates signals from multiple providers and produces a
    weighted consensus signal.
    """

    def __init__(self, providers: list[tuple[SignalProvider, float]]):
        """Initialize with weighted providers.

        Args:
            providers: List of (provider, weight) tuples
        """
        self._providers = providers
        total_weight = sum(w for _, w in providers)
        self._weights = [(p, w / total_weight) for p, w in providers]

    @property
    def name(self) -> str:
        names = [p.name for p, _ in self._providers]
        return f"composite({'+'.join(names)})"

    def get_signal(self, asset: str, context: dict) -> Signal:
        signals = []
        for provider, weight in self._weights:
            signal = provider.get_signal(asset, context)
            signals.append((signal, weight))

        # Aggregate by weighted voting
        action_scores = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        weighted_confidence = 0.0
        reasonings = []

        for signal, weight in signals:
            action_scores[signal.action] += weight * signal.confidence
            weighted_confidence += weight * signal.confidence
            reasonings.append(f"{signal.action}@{signal.confidence:.2f}")

        best_action = max(action_scores, key=action_scores.get)

        return Signal(
            action=best_action,
            confidence=min(action_scores[best_action], 1.0),
            reasoning=f"Composite: {', '.join(reasonings)}",
            metadata={
                "action_scores": action_scores,
                "component_signals": [s.action for s, _ in signals]
            }
        )
