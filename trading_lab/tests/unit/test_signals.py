"""Unit tests for signal generation."""

from __future__ import annotations

import pytest
from trading_lab.core.signals import (
    Signal,
    SignalProvider,
    RandomSignalProvider,
    CompositeSignalProvider,
)
from trading_lab.tests.fixtures.mock_providers import (
    AlwaysBuyProvider,
    AlwaysSellProvider,
    AlwaysHoldProvider,
)


class TestSignal:
    """Tests for the Signal dataclass."""

    def test_valid_buy_signal(self):
        """Test creating a valid buy signal."""
        signal = Signal(action="buy", confidence=0.8, reasoning="Test")
        assert signal.action == "buy"
        assert signal.confidence == 0.8
        assert signal.reasoning == "Test"
        assert signal.metadata == {}

    def test_valid_sell_signal(self):
        """Test creating a valid sell signal."""
        signal = Signal(action="sell", confidence=0.5)
        assert signal.action == "sell"
        assert signal.confidence == 0.5

    def test_valid_hold_signal(self):
        """Test creating a valid hold signal."""
        signal = Signal(action="hold", confidence=0.0)
        assert signal.action == "hold"
        assert signal.confidence == 0.0

    def test_signal_with_metadata(self):
        """Test signal with metadata dict."""
        metadata = {"sentiment": "positive", "source": "news"}
        signal = Signal(action="buy", confidence=0.9, metadata=metadata)
        assert signal.metadata == metadata
        assert signal.metadata["sentiment"] == "positive"

    def test_confidence_boundary_zero(self):
        """Test confidence at lower boundary."""
        signal = Signal(action="hold", confidence=0.0)
        assert signal.confidence == 0.0

    def test_confidence_boundary_one(self):
        """Test confidence at upper boundary."""
        signal = Signal(action="buy", confidence=1.0)
        assert signal.confidence == 1.0

    def test_invalid_confidence_above_one(self):
        """Test that confidence > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Signal(action="buy", confidence=1.5)

    def test_invalid_confidence_negative(self):
        """Test that negative confidence raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
            Signal(action="sell", confidence=-0.1)

    def test_invalid_action(self):
        """Test that invalid action raises ValueError."""
        with pytest.raises(ValueError, match="Action must be buy, sell, or hold"):
            Signal(action="invalid", confidence=0.5)

    def test_signal_default_reasoning(self):
        """Test default empty reasoning."""
        signal = Signal(action="buy", confidence=0.5)
        assert signal.reasoning == ""


class TestSignalProviderProtocol:
    """Tests for SignalProvider protocol compliance."""

    def test_random_provider_implements_protocol(self):
        """Test that RandomSignalProvider implements SignalProvider."""
        provider = RandomSignalProvider()
        assert isinstance(provider, SignalProvider)

    def test_always_buy_implements_protocol(self):
        """Test that AlwaysBuyProvider implements SignalProvider."""
        provider = AlwaysBuyProvider()
        assert isinstance(provider, SignalProvider)

    def test_always_sell_implements_protocol(self):
        """Test that AlwaysSellProvider implements SignalProvider."""
        provider = AlwaysSellProvider()
        assert isinstance(provider, SignalProvider)


class TestRandomSignalProvider:
    """Tests for RandomSignalProvider."""

    def test_name_property(self):
        """Test provider name."""
        provider = RandomSignalProvider()
        assert provider.name == "random"

    def test_get_signal_returns_signal(self):
        """Test that get_signal returns a Signal object."""
        provider = RandomSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert isinstance(signal, Signal)

    def test_get_signal_valid_action(self):
        """Test that signal has valid action."""
        provider = RandomSignalProvider()
        for _ in range(100):
            signal = provider.get_signal("BTC/USD", {})
            assert signal.action in ("buy", "sell", "hold")

    def test_get_signal_valid_confidence(self):
        """Test that confidence is in valid range."""
        provider = RandomSignalProvider(seed=42)
        for _ in range(100):
            signal = provider.get_signal("BTC/USD", {})
            assert 0.3 <= signal.confidence <= 0.9

    def test_seeded_provider_is_deterministic(self):
        """Test that same seed produces same signals."""
        provider1 = RandomSignalProvider(seed=123)
        provider2 = RandomSignalProvider(seed=123)

        for _ in range(10):
            signal1 = provider1.get_signal("BTC/USD", {})
            signal2 = provider2.get_signal("BTC/USD", {})
            assert signal1.action == signal2.action
            assert signal1.confidence == signal2.confidence

    def test_different_seeds_different_signals(self):
        """Test that different seeds produce different signals."""
        provider1 = RandomSignalProvider(seed=1)
        provider2 = RandomSignalProvider(seed=2)

        signals1 = [provider1.get_signal("BTC/USD", {}).action for _ in range(10)]
        signals2 = [provider2.get_signal("BTC/USD", {}).action for _ in range(10)]

        # Very unlikely to be identical
        assert signals1 != signals2

    def test_signal_has_reasoning(self):
        """Test that signal includes reasoning."""
        provider = RandomSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert "Random" in signal.reasoning or "baseline" in signal.reasoning

    def test_signal_has_metadata(self):
        """Test that signal includes provider metadata."""
        provider = RandomSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.metadata.get("provider") == "random"


class TestCompositeSignalProvider:
    """Tests for CompositeSignalProvider."""

    def test_name_with_single_provider(self):
        """Test composite name with single provider."""
        buy = AlwaysBuyProvider()
        composite = CompositeSignalProvider([(buy, 1.0)])
        assert "always_buy" in composite.name

    def test_name_with_multiple_providers(self):
        """Test composite name combines provider names."""
        buy = AlwaysBuyProvider()
        sell = AlwaysSellProvider()
        composite = CompositeSignalProvider([(buy, 0.5), (sell, 0.5)])
        assert "always_buy" in composite.name
        assert "always_sell" in composite.name
        assert "+" in composite.name

    def test_single_provider_passthrough(self):
        """Test that single provider signal passes through."""
        buy = AlwaysBuyProvider(confidence=0.9)
        composite = CompositeSignalProvider([(buy, 1.0)])
        signal = composite.get_signal("BTC/USD", {})
        assert signal.action == "buy"

    def test_unanimous_buy_returns_buy(self):
        """Test that unanimous buy providers return buy."""
        providers = [
            (AlwaysBuyProvider(confidence=0.8), 0.5),
            (AlwaysBuyProvider(confidence=0.9), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        assert signal.action == "buy"

    def test_unanimous_sell_returns_sell(self):
        """Test that unanimous sell providers return sell."""
        providers = [
            (AlwaysSellProvider(confidence=0.8), 0.5),
            (AlwaysSellProvider(confidence=0.9), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        assert signal.action == "sell"

    def test_weighted_voting_high_confidence_wins(self):
        """Test that higher weighted confidence action wins."""
        # Buy with high confidence, sell with low
        providers = [
            (AlwaysBuyProvider(confidence=0.9), 0.5),
            (AlwaysSellProvider(confidence=0.3), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        # Buy should win because 0.9 * 0.5 > 0.3 * 0.5
        assert signal.action == "buy"

    def test_weights_are_normalized(self):
        """Test that weights are normalized to sum to 1."""
        providers = [
            (AlwaysBuyProvider(confidence=0.8), 2.0),  # Unnormalized
            (AlwaysSellProvider(confidence=0.8), 2.0),
        ]
        composite = CompositeSignalProvider(providers)
        # Should not error and weights should be 0.5, 0.5
        signal = composite.get_signal("BTC/USD", {})
        assert signal is not None

    def test_composite_includes_component_signals_in_metadata(self):
        """Test that metadata includes component signals."""
        providers = [
            (AlwaysBuyProvider(), 0.5),
            (AlwaysSellProvider(), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        assert "component_signals" in signal.metadata
        assert "buy" in signal.metadata["component_signals"]
        assert "sell" in signal.metadata["component_signals"]

    def test_composite_includes_action_scores(self):
        """Test that metadata includes action scores."""
        providers = [
            (AlwaysBuyProvider(confidence=0.8), 0.5),
            (AlwaysSellProvider(confidence=0.6), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        scores = signal.metadata.get("action_scores", {})
        assert "buy" in scores
        assert "sell" in scores
        assert "hold" in scores

    def test_confidence_capped_at_one(self):
        """Test that composite confidence doesn't exceed 1.0."""
        providers = [
            (AlwaysBuyProvider(confidence=1.0), 0.5),
            (AlwaysBuyProvider(confidence=1.0), 0.5),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        assert signal.confidence <= 1.0

    def test_three_way_voting(self):
        """Test three-way voting scenario."""
        providers = [
            (AlwaysBuyProvider(confidence=0.8), 0.4),
            (AlwaysSellProvider(confidence=0.7), 0.3),
            (AlwaysHoldProvider(confidence=0.6), 0.3),
        ]
        composite = CompositeSignalProvider(providers)
        signal = composite.get_signal("BTC/USD", {})
        # Buy has highest weighted score: 0.8 * 0.4 = 0.32
        # Sell: 0.7 * 0.3 = 0.21
        # Hold: 0.6 * 0.3 = 0.18
        assert signal.action == "buy"
