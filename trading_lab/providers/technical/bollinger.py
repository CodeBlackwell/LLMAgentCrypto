"""Bollinger Bands signal provider."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta

from trading_lab.core.signals import Signal
from .base import TechnicalSignalProvider


class BollingerBandsSignalProvider(TechnicalSignalProvider):
    """Signal provider based on Bollinger Bands indicator.

    Bollinger Bands measure volatility and identify overbought/oversold:
    - Price at or below lower band → Buy signal (oversold)
    - Price at or above upper band → Sell signal (overbought)
    - Price in middle → Hold
    """

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
    ):
        """Initialize Bollinger Bands signal provider.

        Args:
            period: SMA period for middle band (default 20)
            std_dev: Number of standard deviations for bands (default 2.0)
        """
        if period < 2:
            raise ValueError(f"period must be >= 2, got {period}")
        if std_dev <= 0:
            raise ValueError(f"std_dev must be > 0, got {std_dev}")

        self.period = period
        self.std_dev = std_dev

    @property
    def indicator_name(self) -> str:
        return f"BB({self.period},{self.std_dev})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate Bollinger Bands from close prices.

        Args:
            prices: DataFrame with 'close' column

        Returns:
            Dict with band values and %B position
        """
        close = prices["close"]
        bbands = ta.bbands(close, length=self.period, std=self.std_dev)

        if bbands is None or bbands.empty:
            return {"position": "unknown", "percent_b": None}

        # pandas-ta returns columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0, BBB_20_2.0, BBP_20_2.0
        lower_col = f"BBL_{self.period}_{self.std_dev}"
        middle_col = f"BBM_{self.period}_{self.std_dev}"
        upper_col = f"BBU_{self.period}_{self.std_dev}"
        percent_b_col = f"BBP_{self.period}_{self.std_dev}"

        if lower_col not in bbands.columns:
            return {"position": "unknown", "percent_b": None}

        current_price = float(close.iloc[-1])
        lower = float(bbands[lower_col].iloc[-1])
        middle = float(bbands[middle_col].iloc[-1])
        upper = float(bbands[upper_col].iloc[-1])

        if pd.isna(lower) or pd.isna(upper):
            return {"position": "unknown", "percent_b": None}

        # %B shows where price is relative to bands (0 = lower, 1 = upper)
        band_width = upper - lower
        if band_width > 0:
            percent_b = (current_price - lower) / band_width
        else:
            percent_b = 0.5

        # Determine position
        if current_price <= lower:
            position = "below_lower"
        elif current_price >= upper:
            position = "above_upper"
        elif current_price < middle:
            position = "lower_half"
        else:
            position = "upper_half"

        return {
            "lower_band": lower,
            "middle_band": middle,
            "upper_band": upper,
            "current_price": current_price,
            "percent_b": percent_b,
            "position": position,
            "band_width": band_width,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on Bollinger Band position.

        Args:
            indicator_values: Dict with band values and position
            prices: Original price data

        Returns:
            Buy at lower band, sell at upper band, hold in middle
        """
        position = indicator_values.get("position", "unknown")
        percent_b = indicator_values.get("percent_b")
        current_price = indicator_values.get("current_price")

        if position == "unknown" or percent_b is None:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="Bollinger Bands calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        if position == "below_lower":
            # Price below lower band - strong buy signal
            # More below = higher confidence
            extremity = abs(min(percent_b, 0))
            confidence = min(0.7 + (extremity * 0.3), 0.95)
            return Signal(
                action="buy",
                confidence=confidence,
                reasoning=f"Price ({current_price:.2f}) below lower Bollinger Band",
                metadata={
                    "indicator": self.indicator_name,
                    "percent_b": percent_b,
                    "position": position,
                    **{k: v for k, v in indicator_values.items() if k not in ["position", "percent_b"]},
                },
            )

        elif position == "above_upper":
            # Price above upper band - strong sell signal
            extremity = max(percent_b - 1, 0)
            confidence = min(0.7 + (extremity * 0.3), 0.95)
            return Signal(
                action="sell",
                confidence=confidence,
                reasoning=f"Price ({current_price:.2f}) above upper Bollinger Band",
                metadata={
                    "indicator": self.indicator_name,
                    "percent_b": percent_b,
                    "position": position,
                    **{k: v for k, v in indicator_values.items() if k not in ["position", "percent_b"]},
                },
            )

        else:
            # Price within bands
            if position == "lower_half":
                reasoning = f"Price in lower half of Bollinger Bands (%B: {percent_b:.2f})"
            else:
                reasoning = f"Price in upper half of Bollinger Bands (%B: {percent_b:.2f})"

            # Lower confidence when in middle
            confidence = 0.3 + (0.2 * abs(percent_b - 0.5))

            return Signal(
                action="hold",
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "indicator": self.indicator_name,
                    "percent_b": percent_b,
                    "position": position,
                },
            )
