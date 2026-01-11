"""Mock signal and data providers for testing."""

from __future__ import annotations

from trading_lab.core.signals import Signal, SignalProvider


class MockSignalProvider:
    """Deterministic signal provider for tests.

    Returns signals from a predefined list in order,
    cycling back to the beginning when exhausted.
    """

    def __init__(self, signals: list[Signal] | None = None):
        """Initialize with optional list of signals.

        Args:
            signals: List of signals to return. If None, returns hold signals.
        """
        self._signals = signals or [
            Signal(action="hold", confidence=0.5, reasoning="Mock signal")
        ]
        self._index = 0
        self._call_count = 0

    @property
    def name(self) -> str:
        return "mock"

    def get_signal(self, asset: str, context: dict) -> Signal:
        """Return next signal from the list."""
        signal = self._signals[self._index % len(self._signals)]
        self._index += 1
        self._call_count += 1
        return signal

    @property
    def call_count(self) -> int:
        """Number of times get_signal was called."""
        return self._call_count

    def reset(self):
        """Reset the index and call count."""
        self._index = 0
        self._call_count = 0


class MockNewsProvider:
    """Mock news provider returning canned headlines."""

    def __init__(self, headlines: list[str] | None = None):
        """Initialize with optional headlines.

        Args:
            headlines: List of headlines to return
        """
        self._headlines = headlines or [
            "Bitcoin reaches new highs amid market optimism",
            "Crypto market shows strong momentum",
            "Analysts predict continued growth",
        ]
        self._call_count = 0

    def get_headlines(
        self,
        symbol: str,
        start_date,
        end_date,
        limit: int = 50,
    ) -> list[str]:
        """Return canned headlines."""
        self._call_count += 1
        return self._headlines

    def get_news(
        self,
        symbol: str,
        start_date,
        end_date,
        limit: int = 50,
    ) -> list[dict]:
        """Return canned news articles."""
        self._call_count += 1
        return [
            {"headline": h, "summary": "", "source": "mock", "url": ""}
            for h in self._headlines
        ]

    @property
    def call_count(self) -> int:
        """Number of times provider was called."""
        return self._call_count


class AlwaysBuyProvider:
    """Signal provider that always returns buy signals."""

    def __init__(self, confidence: float = 0.9):
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "always_buy"

    def get_signal(self, asset: str, context: dict) -> Signal:
        return Signal(
            action="buy",
            confidence=self._confidence,
            reasoning="Always buy for testing",
            metadata={"provider": "always_buy"}
        )


class AlwaysSellProvider:
    """Signal provider that always returns sell signals."""

    def __init__(self, confidence: float = 0.9):
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "always_sell"

    def get_signal(self, asset: str, context: dict) -> Signal:
        return Signal(
            action="sell",
            confidence=self._confidence,
            reasoning="Always sell for testing",
            metadata={"provider": "always_sell"}
        )


class AlwaysHoldProvider:
    """Signal provider that always returns hold signals."""

    def __init__(self, confidence: float = 0.5):
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "always_hold"

    def get_signal(self, asset: str, context: dict) -> Signal:
        return Signal(
            action="hold",
            confidence=self._confidence,
            reasoning="Always hold for testing",
            metadata={"provider": "always_hold"}
        )
