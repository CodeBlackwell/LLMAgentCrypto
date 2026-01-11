"""Base class for technical analysis signal providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from trading_lab.core.signals import Signal


class TechnicalSignalProvider(ABC):
    """Abstract base class for technical indicator-based signal providers.

    Technical signal providers calculate indicators from price data
    and generate trading signals based on indicator values.

    Subclasses must implement:
    - calculate_indicator(): Compute indicator values from prices
    - generate_signal(): Convert indicator values to a trading signal
    """

    def get_signal(self, asset: str, context: dict) -> Signal:
        """Get trading signal based on technical indicators.

        Args:
            asset: Asset symbol (e.g., "BTC/USD")
            context: Context dict with price data or fetching info

        Returns:
            Signal with action, confidence, and reasoning
        """
        prices = self._get_prices(asset, context)

        if prices is None or prices.empty:
            return Signal(
                action="hold",
                confidence=0.0,
                reasoning="No price data available",
                metadata={"indicator": self.indicator_name},
            )

        indicator_values = self.calculate_indicator(prices)
        return self.generate_signal(indicator_values, prices)

    @property
    @abstractmethod
    def indicator_name(self) -> str:
        """Name of the technical indicator."""
        ...

    @abstractmethod
    def calculate_indicator(self, prices: pd.DataFrame) -> dict[str, Any]:
        """Calculate indicator values from price data.

        Args:
            prices: DataFrame with OHLCV columns (open, high, low, close, volume)

        Returns:
            Dict with indicator values (e.g., {"rsi": 35.5, "signal": "oversold"})
        """
        ...

    @abstractmethod
    def generate_signal(
        self, indicator_values: dict[str, Any], prices: pd.DataFrame
    ) -> Signal:
        """Generate trading signal from indicator values.

        Args:
            indicator_values: Dict returned by calculate_indicator()
            prices: Original price DataFrame

        Returns:
            Signal with action based on indicator analysis
        """
        ...

    def _get_prices(self, asset: str, context: dict) -> pd.DataFrame | None:
        """Get price data from context.

        Context should contain either:
        - "prices": pd.DataFrame with OHLCV data
        - "price_fetcher": Callable to fetch prices

        Args:
            asset: Asset symbol
            context: Context dict

        Returns:
            DataFrame with price data or None if unavailable
        """
        if "prices" in context:
            return context["prices"]

        if "price_fetcher" in context:
            fetcher = context["price_fetcher"]
            return fetcher(asset, context)

        return None
