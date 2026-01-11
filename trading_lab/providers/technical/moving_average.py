"""Moving Average signal providers."""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd
import pandas_ta as ta

from trading_lab.core.signals import Signal
from .base import TechnicalSignalProvider


class SMASignalProvider(TechnicalSignalProvider):
    """Signal provider based on Simple Moving Average.

    Generates signals based on price position relative to SMA:
    - Price crosses above SMA → Buy signal
    - Price crosses below SMA → Sell signal
    """

    def __init__(self, period: int = 20):
        """Initialize SMA signal provider.

        Args:
            period: SMA period (default 20)
        """
        if period < 1:
            raise ValueError(f"period must be >= 1, got {period}")
        self.period = period

    @property
    def indicator_name(self) -> str:
        return f"SMA({self.period})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate SMA from close prices."""
        close = prices["close"]
        sma = ta.sma(close, length=self.period)

        if sma is None or sma.empty or len(sma) < 2:
            return {"crossover": "unknown", "sma": None}

        if sma.isna().iloc[-1] or sma.isna().iloc[-2]:
            return {"crossover": "unknown", "sma": None}

        current_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        current_sma = float(sma.iloc[-1])
        prev_sma = float(sma.iloc[-2])

        # Detect crossover
        if prev_price <= prev_sma and current_price > current_sma:
            crossover = "bullish"
        elif prev_price >= prev_sma and current_price < current_sma:
            crossover = "bearish"
        else:
            crossover = "none"

        return {
            "sma": current_sma,
            "current_price": current_price,
            "crossover": crossover,
            "above_sma": current_price > current_sma,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on SMA crossover."""
        crossover = indicator_values.get("crossover", "unknown")
        sma = indicator_values.get("sma")
        current_price = indicator_values.get("current_price")

        if crossover == "unknown" or sma is None:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="SMA calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        if crossover == "bullish":
            return Signal(
                action="buy",
                confidence=0.7,
                reasoning=f"Price ({current_price:.2f}) crossed above SMA({self.period}) at {sma:.2f}",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        elif crossover == "bearish":
            return Signal(
                action="sell",
                confidence=0.7,
                reasoning=f"Price ({current_price:.2f}) crossed below SMA({self.period}) at {sma:.2f}",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        else:
            above = indicator_values.get("above_sma", False)
            trend = "above" if above else "below"
            return Signal(
                action="hold",
                confidence=0.4,
                reasoning=f"Price ({current_price:.2f}) remains {trend} SMA({self.period})",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )


class EMASignalProvider(TechnicalSignalProvider):
    """Signal provider based on Exponential Moving Average.

    Similar to SMA but gives more weight to recent prices.
    """

    def __init__(self, period: int = 20):
        """Initialize EMA signal provider.

        Args:
            period: EMA period (default 20)
        """
        if period < 1:
            raise ValueError(f"period must be >= 1, got {period}")
        self.period = period

    @property
    def indicator_name(self) -> str:
        return f"EMA({self.period})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate EMA from close prices."""
        close = prices["close"]
        ema = ta.ema(close, length=self.period)

        if ema is None or ema.empty or len(ema) < 2:
            return {"crossover": "unknown", "ema": None}

        if ema.isna().iloc[-1] or ema.isna().iloc[-2]:
            return {"crossover": "unknown", "ema": None}

        current_price = float(close.iloc[-1])
        prev_price = float(close.iloc[-2])
        current_ema = float(ema.iloc[-1])
        prev_ema = float(ema.iloc[-2])

        if prev_price <= prev_ema and current_price > current_ema:
            crossover = "bullish"
        elif prev_price >= prev_ema and current_price < current_ema:
            crossover = "bearish"
        else:
            crossover = "none"

        return {
            "ema": current_ema,
            "current_price": current_price,
            "crossover": crossover,
            "above_ema": current_price > current_ema,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on EMA crossover."""
        crossover = indicator_values.get("crossover", "unknown")
        ema = indicator_values.get("ema")
        current_price = indicator_values.get("current_price")

        if crossover == "unknown" or ema is None:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="EMA calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        if crossover == "bullish":
            return Signal(
                action="buy",
                confidence=0.7,
                reasoning=f"Price ({current_price:.2f}) crossed above EMA({self.period}) at {ema:.2f}",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        elif crossover == "bearish":
            return Signal(
                action="sell",
                confidence=0.7,
                reasoning=f"Price ({current_price:.2f}) crossed below EMA({self.period}) at {ema:.2f}",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        else:
            above = indicator_values.get("above_ema", False)
            trend = "above" if above else "below"
            return Signal(
                action="hold",
                confidence=0.4,
                reasoning=f"Price ({current_price:.2f}) remains {trend} EMA({self.period})",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )


class MACrossSignalProvider(TechnicalSignalProvider):
    """Signal provider based on Moving Average Crossover.

    Uses two MAs (fast and slow) to identify trend changes:
    - Fast MA crosses above slow MA → Buy signal (golden cross)
    - Fast MA crosses below slow MA → Sell signal (death cross)
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 20,
        ma_type: Literal["sma", "ema"] = "ema",
    ):
        """Initialize MA Crossover signal provider.

        Args:
            fast_period: Fast MA period (default 10)
            slow_period: Slow MA period (default 20)
            ma_type: Type of moving average ("sma" or "ema", default "ema")
        """
        if fast_period >= slow_period:
            raise ValueError(
                f"fast_period ({fast_period}) must be less than slow_period ({slow_period})"
            )
        if ma_type not in ("sma", "ema"):
            raise ValueError(f"ma_type must be 'sma' or 'ema', got {ma_type}")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type

    @property
    def indicator_name(self) -> str:
        return f"MACross({self.ma_type.upper()}{self.fast_period}/{self.slow_period})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate MA crossover from close prices."""
        close = prices["close"]

        if self.ma_type == "sma":
            fast_ma = ta.sma(close, length=self.fast_period)
            slow_ma = ta.sma(close, length=self.slow_period)
        else:
            fast_ma = ta.ema(close, length=self.fast_period)
            slow_ma = ta.ema(close, length=self.slow_period)

        if fast_ma is None or slow_ma is None or fast_ma.empty or slow_ma.empty:
            return {"crossover": "unknown"}

        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return {"crossover": "unknown"}

        if fast_ma.isna().iloc[-1] or slow_ma.isna().iloc[-1]:
            return {"crossover": "unknown"}

        if fast_ma.isna().iloc[-2] or slow_ma.isna().iloc[-2]:
            return {"crossover": "unknown"}

        current_fast = float(fast_ma.iloc[-1])
        current_slow = float(slow_ma.iloc[-1])
        prev_fast = float(fast_ma.iloc[-2])
        prev_slow = float(slow_ma.iloc[-2])

        # Detect crossover
        if prev_fast <= prev_slow and current_fast > current_slow:
            crossover = "golden"  # bullish
        elif prev_fast >= prev_slow and current_fast < current_slow:
            crossover = "death"  # bearish
        else:
            crossover = "none"

        return {
            "fast_ma": current_fast,
            "slow_ma": current_slow,
            "crossover": crossover,
            "fast_above_slow": current_fast > current_slow,
            "spread": current_fast - current_slow,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on MA crossover."""
        crossover = indicator_values.get("crossover", "unknown")
        fast_ma = indicator_values.get("fast_ma")
        slow_ma = indicator_values.get("slow_ma")

        if crossover == "unknown" or fast_ma is None:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="MA crossover calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        if crossover == "golden":
            return Signal(
                action="buy",
                confidence=0.8,
                reasoning=f"Golden cross: {self.ma_type.upper()}{self.fast_period} ({fast_ma:.2f}) crossed above {self.ma_type.upper()}{self.slow_period} ({slow_ma:.2f})",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        elif crossover == "death":
            return Signal(
                action="sell",
                confidence=0.8,
                reasoning=f"Death cross: {self.ma_type.upper()}{self.fast_period} ({fast_ma:.2f}) crossed below {self.ma_type.upper()}{self.slow_period} ({slow_ma:.2f})",
                metadata={"indicator": self.indicator_name, **indicator_values},
            )

        else:
            fast_above = indicator_values.get("fast_above_slow", False)
            spread = indicator_values.get("spread", 0)
            if fast_above:
                reasoning = f"Uptrend continues: fast MA above slow by {spread:.2f}"
            else:
                reasoning = f"Downtrend continues: fast MA below slow by {abs(spread):.2f}"

            return Signal(
                action="hold",
                confidence=0.4,
                reasoning=reasoning,
                metadata={"indicator": self.indicator_name, **indicator_values},
            )
