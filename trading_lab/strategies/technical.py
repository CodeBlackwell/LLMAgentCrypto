"""Technical analysis trading strategies."""

from ..core.strategy import BaseStrategy
from ..providers.technical import (
    RSISignalProvider,
    MACDSignalProvider,
    BollingerBandsSignalProvider,
    MACrossSignalProvider,
)
from .registry import register


@register(
    name="rsi",
    description="RSI-based momentum strategy (buy oversold, sell overbought)",
    default_provider="rsi",
)
class RSIStrategy(BaseStrategy):
    """RSI momentum trading strategy.

    Buys when RSI indicates oversold conditions (< 30)
    Sells when RSI indicates overbought conditions (> 70)
    """

    def initialize(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        **kwargs
    ):
        """Initialize RSI strategy.

        Args:
            period: RSI calculation period (default 14)
            oversold: Buy threshold (default 30)
            overbought: Sell threshold (default 70)
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = RSISignalProvider(
            period=period,
            oversold=oversold,
            overbought=overbought,
        )

        super().initialize(
            signal_provider=signal_provider,
            **kwargs
        )


@register(
    name="macd",
    description="MACD crossover strategy (buy bullish, sell bearish)",
    default_provider="macd",
)
class MACDStrategy(BaseStrategy):
    """MACD crossover trading strategy.

    Buys on bullish MACD crossover (histogram goes positive)
    Sells on bearish MACD crossover (histogram goes negative)
    """

    def initialize(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        **kwargs
    ):
        """Initialize MACD strategy.

        Args:
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = MACDSignalProvider(
            fast=fast,
            slow=slow,
            signal=signal,
        )

        super().initialize(
            signal_provider=signal_provider,
            **kwargs
        )


@register(
    name="bollinger",
    description="Bollinger Bands mean reversion strategy",
    default_provider="bollinger",
)
class BollingerStrategy(BaseStrategy):
    """Bollinger Bands mean reversion strategy.

    Buys when price touches lower band (oversold)
    Sells when price touches upper band (overbought)
    """

    def initialize(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        **kwargs
    ):
        """Initialize Bollinger Bands strategy.

        Args:
            period: SMA period for middle band (default 20)
            std_dev: Standard deviations for bands (default 2.0)
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = BollingerBandsSignalProvider(
            period=period,
            std_dev=std_dev,
        )

        super().initialize(
            signal_provider=signal_provider,
            **kwargs
        )


@register(
    name="ma_cross",
    description="Moving average crossover strategy (golden/death cross)",
    default_provider="ma_cross",
)
class MACrossStrategy(BaseStrategy):
    """Moving average crossover trading strategy.

    Buys on golden cross (fast MA crosses above slow MA)
    Sells on death cross (fast MA crosses below slow MA)
    """

    def initialize(
        self,
        fast_period: int = 10,
        slow_period: int = 20,
        ma_type: str = "ema",
        **kwargs
    ):
        """Initialize MA crossover strategy.

        Args:
            fast_period: Fast MA period (default 10)
            slow_period: Slow MA period (default 20)
            ma_type: Type of MA - "sma" or "ema" (default "ema")
            **kwargs: Passed to BaseStrategy.initialize()
        """
        signal_provider = MACrossSignalProvider(
            fast_period=fast_period,
            slow_period=slow_period,
            ma_type=ma_type,
        )

        super().initialize(
            signal_provider=signal_provider,
            **kwargs
        )
