"""Alpaca API news provider."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...core.config import get_settings


class AlpacaNewsProvider:
    """Fetches news from Alpaca Markets API.

    Provides access to financial news for stocks and crypto
    through the Alpaca REST API using alpaca-py.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        """Initialize Alpaca news provider.

        Args:
            api_key: Alpaca API key (defaults to env var)
            api_secret: Alpaca API secret (defaults to env var)
        """
        from alpaca.data.historical.news import NewsClient
        from alpaca.data.requests import NewsRequest

        settings = get_settings()

        self._client = NewsClient(
            api_key=api_key or settings.alpaca_api_key,
            secret_key=api_secret or settings.alpaca_api_secret,
        )
        self._NewsRequest = NewsRequest

    def get_news(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch news for a symbol.

        Args:
            symbol: Asset symbol (e.g., "BTC", "AAPL")
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of articles

        Returns:
            List of news article dictionaries
        """
        # Alpaca wants symbols without slash for crypto
        clean_symbol = symbol.replace("/", "").replace("-", "")

        request = self._NewsRequest(
            symbols=[clean_symbol],
            start=start_date,
            end=end_date,
            limit=limit,
        )

        news = self._client.get_news(request)

        return [
            {
                "headline": article.headline or "",
                "summary": article.summary or "",
                "source": article.source or "",
                "url": article.url or "",
                "created_at": article.created_at.isoformat() if article.created_at else "",
                "symbols": article.symbols or [],
            }
            for article in news.news
        ]

    def get_headlines(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 50,
    ) -> list[str]:
        """Get just the headlines for a symbol.

        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            limit: Maximum articles

        Returns:
            List of headline strings
        """
        news = self.get_news(symbol, start_date, end_date, limit)
        return [article["headline"] for article in news if article["headline"]]
