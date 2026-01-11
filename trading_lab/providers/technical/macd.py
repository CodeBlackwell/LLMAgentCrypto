"""MACD (Moving Average Convergence Divergence) signal provider."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta

from trading_lab.core.signals import Signal
from .base import TechnicalSignalProvider


class MACDSignalProvider(TechnicalSignalProvider):
    """Signal provider based on MACD indicator.

    MACD measures trend momentum using moving average convergence/divergence:
    - Histogram crosses above 0 (bullish crossover) → Buy signal
    - Histogram crosses below 0 (bearish crossover) → Sell signal
    - No crossover → Hold
    """

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ):
        """Initialize MACD signal provider.

        Args:
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)
        """
        if fast >= slow:
            raise ValueError(f"fast ({fast}) must be less than slow ({slow})")
        if signal < 1:
            raise ValueError(f"signal must be >= 1, got {signal}")

        self.fast = fast
        self.slow = slow
        self.signal = signal

    @property
    def indicator_name(self) -> str:
        return f"MACD({self.fast},{self.slow},{self.signal})"

    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate MACD from close prices.

        Args:
            prices: DataFrame with 'close' column

        Returns:
            Dict with macd, signal, histogram values and crossover state
        """
        close = prices["close"]
        macd = ta.macd(close, fast=self.fast, slow=self.slow, signal=self.signal)

        if macd is None or macd.empty:
            return {"crossover": "unknown", "histogram": None}

        # pandas-ta returns columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        hist_col = f"MACDh_{self.fast}_{self.slow}_{self.signal}"
        macd_col = f"MACD_{self.fast}_{self.slow}_{self.signal}"
        signal_col = f"MACDs_{self.fast}_{self.slow}_{self.signal}"

        if hist_col not in macd.columns:
            return {"crossover": "unknown", "histogram": None}

        histogram = macd[hist_col]

        if len(histogram) < 2 or histogram.isna().iloc[-1] or histogram.isna().iloc[-2]:
            return {"crossover": "unknown", "histogram": None}

        current_hist = float(histogram.iloc[-1])
        prev_hist = float(histogram.iloc[-2])

        # Detect crossover
        if prev_hist <= 0 and current_hist > 0:
            crossover = "bullish"
        elif prev_hist >= 0 and current_hist < 0:
            crossover = "bearish"
        else:
            crossover = "none"

        return {
            "macd": float(macd[macd_col].iloc[-1]) if macd_col in macd.columns else None,
            "signal_line": float(macd[signal_col].iloc[-1]) if signal_col in macd.columns else None,
            "histogram": current_hist,
            "prev_histogram": prev_hist,
            "crossover": crossover,
        }

    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate signal based on MACD crossover.

        Args:
            indicator_values: Dict with histogram and crossover info
            prices: Original price data

        Returns:
            Buy on bullish crossover, sell on bearish, hold otherwise
        """
        crossover = indicator_values.get("crossover", "unknown")
        histogram = indicator_values.get("histogram")

        if crossover == "unknown" or histogram is None:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="MACD calculation failed or insufficient data",
                metadata={"indicator": self.indicator_name},
            )

        if crossover == "bullish":
            # Confidence based on histogram strength
            confidence = min(0.6 + abs(histogram) * 0.01, 0.95)
            return Signal(
                action="buy",
                confidence=confidence,
                reasoning=f"MACD bullish crossover (histogram: {histogram:.4f})",
                metadata={
                    "indicator": self.indicator_name,
                    "histogram": histogram,
                    "crossover": crossover,
                    **{k: v for k, v in indicator_values.items() if k not in ["crossover", "histogram"]},
                },
            )

        elif crossover == "bearish":
            confidence = min(0.6 + abs(histogram) * 0.01, 0.95)
            return Signal(
                action="sell",
                confidence=confidence,
                reasoning=f"MACD bearish crossover (histogram: {histogram:.4f})",
                metadata={
                    "indicator": self.indicator_name,
                    "histogram": histogram,
                    "crossover": crossover,
                    **{k: v for k, v in indicator_values.items() if k not in ["crossover", "histogram"]},
                },
            )

        else:
            # No crossover - indicate trend direction
            if histogram > 0:
                reasoning = f"MACD positive ({histogram:.4f}), uptrend continues"
            elif histogram < 0:
                reasoning = f"MACD negative ({histogram:.4f}), downtrend continues"
            else:
                reasoning = "MACD at zero, trend unclear"

            return Signal(
                action="hold",
                confidence=0.4,
                reasoning=reasoning,
                metadata={
                    "indicator": self.indicator_name,
                    "histogram": histogram,
                    "crossover": crossover,
                },
            )
