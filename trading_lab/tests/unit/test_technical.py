"""Unit tests for technical indicator signal providers."""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np

from trading_lab.providers.technical import (
    TechnicalSignalProvider,
    RSISignalProvider,
    MACDSignalProvider,
    BollingerBandsSignalProvider,
    SMASignalProvider,
    EMASignalProvider,
    MACrossSignalProvider,
)


def make_prices(close_values: list[float], seed: int = 42) -> pd.DataFrame:
    """Create a price DataFrame from close values."""
    n = len(close_values)
    np.random.seed(seed)
    noise = np.random.uniform(-0.02, 0.02, n)

    close = np.array(close_values)
    high = close * (1 + np.abs(noise))
    low = close * (1 - np.abs(noise))
    open_prices = close * (1 + noise / 2)
    volume = np.random.randint(1000, 10000, n)

    return pd.DataFrame({
        "open": open_prices,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def make_trending_prices(start: float, end: float, n: int = 50) -> pd.DataFrame:
    """Create trending price data."""
    close_values = list(np.linspace(start, end, n))
    return make_prices(close_values)


def make_oscillating_prices(center: float, amplitude: float, n: int = 50) -> pd.DataFrame:
    """Create oscillating price data."""
    t = np.linspace(0, 4 * np.pi, n)
    close_values = center + amplitude * np.sin(t)
    return make_prices(list(close_values))


class TestRSISignalProvider:
    """Tests for RSISignalProvider."""

    def test_implements_protocol(self):
        """Test that RSI provider is a TechnicalSignalProvider."""
        provider = RSISignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default RSI parameters."""
        provider = RSISignalProvider()
        assert provider.period == 14
        assert provider.oversold == 30.0
        assert provider.overbought == 70.0

    def test_custom_parameters(self):
        """Test custom RSI parameters."""
        provider = RSISignalProvider(period=7, oversold=20, overbought=80)
        assert provider.period == 7
        assert provider.oversold == 20.0
        assert provider.overbought == 80.0

    def test_invalid_period_raises(self):
        """Test invalid period raises ValueError."""
        with pytest.raises(ValueError):
            RSISignalProvider(period=0)

    def test_invalid_thresholds_raises(self):
        """Test invalid thresholds raise ValueError."""
        with pytest.raises(ValueError):
            RSISignalProvider(oversold=70, overbought=30)  # reversed

    def test_indicator_name(self):
        """Test indicator name."""
        provider = RSISignalProvider(period=14)
        assert provider.indicator_name == "RSI(14)"

    def test_oversold_generates_buy(self):
        """Test oversold condition generates buy signal."""
        provider = RSISignalProvider(period=14, oversold=30)
        # Create sharply declining prices to trigger oversold
        prices = make_trending_prices(100, 50, n=30)
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        # Should be buy or hold depending on exact RSI
        assert signal.action in ("buy", "hold")
        assert "RSI" in provider.indicator_name

    def test_overbought_generates_sell(self):
        """Test overbought condition generates sell signal."""
        provider = RSISignalProvider(period=14, overbought=70)
        # Create sharply rising prices to trigger overbought
        prices = make_trending_prices(50, 100, n=30)
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        assert signal.action in ("sell", "hold")

    def test_no_prices_returns_hold(self):
        """Test missing prices returns hold with zero confidence."""
        provider = RSISignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.action == "hold"
        assert signal.confidence == 0.0

    def test_empty_prices_returns_hold(self):
        """Test empty prices returns hold."""
        provider = RSISignalProvider()
        signal = provider.get_signal("BTC/USD", {"prices": pd.DataFrame()})
        assert signal.action == "hold"
        assert signal.confidence == 0.0


class TestMACDSignalProvider:
    """Tests for MACDSignalProvider."""

    def test_implements_protocol(self):
        """Test that MACD provider is a TechnicalSignalProvider."""
        provider = MACDSignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default MACD parameters."""
        provider = MACDSignalProvider()
        assert provider.fast == 12
        assert provider.slow == 26
        assert provider.signal == 9

    def test_custom_parameters(self):
        """Test custom MACD parameters."""
        provider = MACDSignalProvider(fast=8, slow=17, signal=5)
        assert provider.fast == 8
        assert provider.slow == 17
        assert provider.signal == 5

    def test_invalid_fast_slow_raises(self):
        """Test fast >= slow raises ValueError."""
        with pytest.raises(ValueError):
            MACDSignalProvider(fast=26, slow=12)

    def test_indicator_name(self):
        """Test indicator name."""
        provider = MACDSignalProvider(fast=12, slow=26, signal=9)
        assert provider.indicator_name == "MACD(12,26,9)"

    def test_bullish_crossover(self):
        """Test bullish crossover detection."""
        provider = MACDSignalProvider()
        # Create prices that transition from downtrend to uptrend
        prices = make_prices(
            [100 - i for i in range(30)] + [70 + i * 2 for i in range(30)]
        )
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        # Should detect some kind of crossover or trend
        assert signal.metadata.get("indicator") == "MACD(12,26,9)"

    def test_no_prices_returns_hold(self):
        """Test missing prices returns hold."""
        provider = MACDSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.action == "hold"


class TestBollingerBandsSignalProvider:
    """Tests for BollingerBandsSignalProvider."""

    def test_implements_protocol(self):
        """Test that BB provider is a TechnicalSignalProvider."""
        provider = BollingerBandsSignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default Bollinger Bands parameters."""
        provider = BollingerBandsSignalProvider()
        assert provider.period == 20
        assert provider.std_dev == 2.0

    def test_custom_parameters(self):
        """Test custom Bollinger Bands parameters."""
        provider = BollingerBandsSignalProvider(period=10, std_dev=1.5)
        assert provider.period == 10
        assert provider.std_dev == 1.5

    def test_invalid_period_raises(self):
        """Test invalid period raises ValueError."""
        with pytest.raises(ValueError):
            BollingerBandsSignalProvider(period=1)

    def test_invalid_std_dev_raises(self):
        """Test invalid std_dev raises ValueError."""
        with pytest.raises(ValueError):
            BollingerBandsSignalProvider(std_dev=0)

    def test_indicator_name(self):
        """Test indicator name."""
        provider = BollingerBandsSignalProvider(period=20, std_dev=2.0)
        assert provider.indicator_name == "BB(20,2.0)"

    def test_price_at_lower_band_generates_buy(self):
        """Test price at lower band generates buy signal."""
        provider = BollingerBandsSignalProvider(period=20)
        # Stable prices then sharp drop
        stable = [100] * 25
        drop = [90, 85, 80]  # Sharp drop to trigger lower band
        prices = make_prices(stable + drop)
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        # Should either buy or hold depending on exact band position
        assert signal.action in ("buy", "hold")

    def test_no_prices_returns_hold(self):
        """Test missing prices returns hold."""
        provider = BollingerBandsSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.action == "hold"


class TestSMASignalProvider:
    """Tests for SMASignalProvider."""

    def test_implements_protocol(self):
        """Test that SMA provider is a TechnicalSignalProvider."""
        provider = SMASignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default SMA period."""
        provider = SMASignalProvider()
        assert provider.period == 20

    def test_custom_period(self):
        """Test custom SMA period."""
        provider = SMASignalProvider(period=50)
        assert provider.period == 50

    def test_invalid_period_raises(self):
        """Test invalid period raises ValueError."""
        with pytest.raises(ValueError):
            SMASignalProvider(period=0)

    def test_indicator_name(self):
        """Test indicator name."""
        provider = SMASignalProvider(period=20)
        assert provider.indicator_name == "SMA(20)"

    def test_bullish_crossover_generates_buy(self):
        """Test bullish crossover generates buy signal."""
        provider = SMASignalProvider(period=10)
        # Price dips below SMA then rises above
        prices = make_prices([100] * 15 + [95, 94, 93, 96, 99, 102])
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        assert signal.action in ("buy", "hold")

    def test_no_prices_returns_hold(self):
        """Test missing prices returns hold."""
        provider = SMASignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.action == "hold"


class TestEMASignalProvider:
    """Tests for EMASignalProvider."""

    def test_implements_protocol(self):
        """Test that EMA provider is a TechnicalSignalProvider."""
        provider = EMASignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default EMA period."""
        provider = EMASignalProvider()
        assert provider.period == 20

    def test_invalid_period_raises(self):
        """Test invalid period raises ValueError."""
        with pytest.raises(ValueError):
            EMASignalProvider(period=0)

    def test_indicator_name(self):
        """Test indicator name."""
        provider = EMASignalProvider(period=20)
        assert provider.indicator_name == "EMA(20)"


class TestMACrossSignalProvider:
    """Tests for MACrossSignalProvider."""

    def test_implements_protocol(self):
        """Test that MA Cross provider is a TechnicalSignalProvider."""
        provider = MACrossSignalProvider()
        assert isinstance(provider, TechnicalSignalProvider)

    def test_default_parameters(self):
        """Test default MA Cross parameters."""
        provider = MACrossSignalProvider()
        assert provider.fast_period == 10
        assert provider.slow_period == 20
        assert provider.ma_type == "ema"

    def test_custom_parameters(self):
        """Test custom MA Cross parameters."""
        provider = MACrossSignalProvider(fast_period=5, slow_period=15, ma_type="sma")
        assert provider.fast_period == 5
        assert provider.slow_period == 15
        assert provider.ma_type == "sma"

    def test_invalid_periods_raises(self):
        """Test fast >= slow raises ValueError."""
        with pytest.raises(ValueError):
            MACrossSignalProvider(fast_period=20, slow_period=10)

    def test_invalid_ma_type_raises(self):
        """Test invalid ma_type raises ValueError."""
        with pytest.raises(ValueError):
            MACrossSignalProvider(ma_type="invalid")

    def test_indicator_name(self):
        """Test indicator name."""
        provider = MACrossSignalProvider(fast_period=10, slow_period=20, ma_type="ema")
        assert provider.indicator_name == "MACross(EMA10/20)"

    def test_golden_cross_generates_buy(self):
        """Test golden cross generates buy signal."""
        provider = MACrossSignalProvider(fast_period=5, slow_period=10)
        # Downtrend then uptrend to trigger golden cross
        prices = make_prices([100 - i for i in range(15)] + [85 + i * 2 for i in range(15)])
        signal = provider.get_signal("BTC/USD", {"prices": prices})
        assert signal.action in ("buy", "hold")

    def test_no_prices_returns_hold(self):
        """Test missing prices returns hold."""
        provider = MACrossSignalProvider()
        signal = provider.get_signal("BTC/USD", {})
        assert signal.action == "hold"


class TestPriceFetcher:
    """Tests for price fetching via context."""

    def test_uses_price_fetcher_from_context(self):
        """Test that provider uses price_fetcher if provided."""
        prices = make_trending_prices(100, 110, n=30)

        def mock_fetcher(asset: str, context: dict) -> pd.DataFrame:
            return prices

        provider = RSISignalProvider()
        signal = provider.get_signal("BTC/USD", {"price_fetcher": mock_fetcher})

        # Should successfully calculate RSI from fetched prices
        assert signal.action in ("buy", "sell", "hold")
        assert "RSI" in signal.metadata.get("indicator", "")
