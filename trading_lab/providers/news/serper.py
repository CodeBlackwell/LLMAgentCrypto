"""Serper API news provider for web search."""

from __future__ import annotations

import json
from typing import Optional

from langchain_community.utilities import GoogleSerperAPIWrapper
from dotenv import load_dotenv

from ...core.config import get_settings


class SerperNewsProvider:
    """Fetches news articles using Google Serper API.

    Provides web search capabilities for fetching news about
    assets within specific date ranges.
    """

    def __init__(self, api_key: Optional[str] = None, max_results: int = 15):
        """Initialize the Serper news provider.

        Args:
            api_key: Serper API key (defaults to env var)
            max_results: Maximum number of search results
        """
        load_dotenv()

        if api_key:
            import os
            os.environ["SERPER_API_KEY"] = api_key

        self._search = GoogleSerperAPIWrapper(k=max_results, type="news")
        self.max_results = max_results

    def search(
        self,
        asset_name: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """Search for news about an asset in a date range.

        Args:
            asset_name: Name of asset (e.g., "bitcoin", "AAPL")
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            String containing search results
        """
        query = f"{asset_name} price before:{end_date} after:{start_date}"
        return self._search.run(query)

    def search_detailed(
        self,
        asset_name: str,
        start_date: str,
        end_date: str,
    ) -> dict:
        """Search for news with full result details.

        Args:
            asset_name: Name of asset
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with full search results including links, snippets
        """
        query = f"{asset_name} price before:{end_date} after:{start_date}"
        return self._search.results(query)

    def get_headlines(
        self,
        asset_name: str,
        start_date: str,
        end_date: str,
    ) -> list[str]:
        """Extract just headlines from search results.

        Args:
            asset_name: Name of asset
            start_date: Start date
            end_date: End date

        Returns:
            List of news headlines
        """
        results = self.search_detailed(asset_name, start_date, end_date)
        headlines = []

        if "news" in results:
            for item in results["news"]:
                if "title" in item:
                    headlines.append(item["title"])

        return headlines
