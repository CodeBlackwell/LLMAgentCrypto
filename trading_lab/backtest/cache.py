"""Data cache for backtest historical price data."""

from __future__ import annotations

import hashlib
import pickle
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame


class DataCache:
    """Cache for historical price data using pickle files.

    Stores DataFrames in .backtest_cache/ directory to avoid
    redundant API calls for the same data.
    """

    CACHE_DIR = ".backtest_cache"

    def __init__(self, cache_dir: str | None = None):
        """Initialize the data cache.

        Args:
            cache_dir: Optional custom cache directory path.
                       Defaults to .backtest_cache/ in current working directory.
        """
        self._cache_dir = Path(cache_dir) if cache_dir else Path(self.CACHE_DIR)

    def _get_cache_key(
        self,
        asset: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> str:
        """Generate a unique cache key for the given parameters.

        Args:
            asset: Asset symbol (e.g., "BTC")
            exchange: Exchange name (e.g., "binance")
            start_date: Start date of the data range
            end_date: End date of the data range

        Returns:
            A hash string to use as the cache filename
        """
        key_string = f"{asset}_{exchange}_{start_date.isoformat()}_{end_date.isoformat()}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_path(
        self,
        asset: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> Path:
        """Get the full path to the cache file.

        Args:
            asset: Asset symbol
            exchange: Exchange name
            start_date: Start date
            end_date: End date

        Returns:
            Path to the cache file
        """
        cache_key = self._get_cache_key(asset, exchange, start_date, end_date)
        return self._cache_dir / f"{cache_key}.pkl"

    def get(
        self,
        asset: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> DataFrame | None:
        """Retrieve cached data for the given parameters.

        Args:
            asset: Asset symbol (e.g., "BTC")
            exchange: Exchange name (e.g., "binance")
            start_date: Start date of the data range
            end_date: End date of the data range

        Returns:
            Cached DataFrame if found, None otherwise
        """
        cache_path = self._get_cache_path(asset, exchange, start_date, end_date)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, OSError, EOFError):
            # Cache file is corrupted, remove it
            cache_path.unlink(missing_ok=True)
            return None

    def set(
        self,
        asset: str,
        exchange: str,
        start_date: date,
        end_date: date,
        data: DataFrame,
    ) -> None:
        """Store data in the cache.

        Args:
            asset: Asset symbol (e.g., "BTC")
            exchange: Exchange name (e.g., "binance")
            start_date: Start date of the data range
            end_date: End date of the data range
            data: DataFrame to cache
        """
        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        cache_path = self._get_cache_path(asset, exchange, start_date, end_date)

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(data, f)
        except (pickle.PickleError, OSError):
            # Failed to write cache, silently ignore
            pass

    def clear(self) -> None:
        """Clear all cached data.

        Removes all pickle files from the cache directory.
        """
        if not self._cache_dir.exists():
            return

        for cache_file in self._cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except OSError:
                # Failed to delete file, silently ignore
                pass
