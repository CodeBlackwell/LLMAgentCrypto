"""RSI (Relative Strength Index) signal provider."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta

from trading_lab.core.signals import Signal
from .base import TechnicalSignalProvider


class RSISignalProvider(TechnicalSignalProvider):
    """Signal provider based on RSI indicator.

    RSI measures momentum to identify overbought/oversold conditions:
    - RSI < oversold threshold → Buy signal
    - RSI > overbought threshold → Sell signal
    - Between thresholds → Hold
    """

    def __init__(
        self,
        period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
    ):
        """Initialize RSI signal provider.

        Args:
            period: RSI calculation period (default 14)
            oversold: Level below which asset is oversold (default 30)
            overbought: Level above which asset is overbought (default 70)
        """
        if period < 1:
            raise ValueError(f"period must be >= 1, got {period}")
        if not 0 < oversold < overbought < 100:
            raise ValueError(
                f"Invalid thresholds: 0 < oversold ({oversold}) < overbought ({overbought}) < 100"
            )

        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    @property
    def indicator_name(self) -> str:
        return f"RSI({self.period})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate RSI from close prices.

        Args:
            prices: DataFrame with 'close' column

        Returns:
            Dict with rsi value and zone (oversold/overbought/neutral)
        """
        close = prices["close"]
        rsi = ta.rsi(close, length=self.period)

        if rsi is None or rsi.empty or rsi.isna().all():
            return {"rsi": None, "zone": "unknown"}

        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return {"rsi": None, "zone": "unknown"}

        if current_rsi < self.oversold:
            zone = "oversold"
        elif current_rsi > self.overbought:
            zone = "overbought"
        else:
            zone = "neutral"

        return {
            "rsi": float(current_rsi),
            "zone": zone,
            "oversold_threshold": self.oversold,
            "overbought_threshold": self.overbought,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on RSI zone.

        Args:
            indicator_values: Dict with rsi and zone
            prices: Original price data

        Returns:
            Buy when oversold, sell when overbought, hold otherwise
        """
        rsi = indicator_values.get("rsi")
        zone = indicator_values.get("zone", "unknown")

        if rsi is None or zone == "unknown":
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="RSI calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        # Calculate confidence based on how extreme the RSI is
        if zone == "oversold":
            # More oversold = higher confidence
            extremity = (self.oversold - rsi) / self.oversold
            confidence = min(0.5 + (extremity * 0.5), 1.0)
            return Signal(
                action="buy",
                confidence=confidence,
                reasoning=f"RSI at {rsi:.1f} indicates oversold conditions",
                metadata={
                    "indicator": self.indicator_name,
                    "rsi": rsi,
                    "zone": zone,
                },
            )

        elif zone == "overbought":
            # More overbought = higher confidence
            extremity = (rsi - self.overbought) / (100 - self.overbought)
            confidence = min(0.5 + (extremity * 0.5), 1.0)
            return Signal(
                action="sell",
                confidence=confidence,
                reasoning=f"RSI at {rsi:.1f} indicates overbought conditions",
                metadata={
                    "indicator": self.indicator_name,
                    "rsi": rsi,
                    "zone": zone,
                },
            )

        else:
            # Neutral zone - confidence based on distance from edges
            distance_from_middle = abs(rsi - 50) / 20  # 0-1 scale
            confidence = 0.3 + (0.2 * (1 - distance_from_middle))
            return Signal(
                action="hold",
                confidence=confidence,
                reasoning=f"RSI at {rsi:.1f} in neutral zone",
                metadata={
                    "indicator": self.indicator_name,
                    "rsi": rsi,
                    "zone": zone,
                },
            )
