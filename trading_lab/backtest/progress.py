"""Progress tracking for backtest execution."""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..storage.repository import BacktestRepository


class ProgressTracker:
    """Tracks and persists backtest progress.

    Calculates progress percentage based on date range and
    throttles database updates to avoid excessive writes.
    """

    # Minimum interval between database updates (seconds)
    THROTTLE_INTERVAL_MS = 500

    def __init__(
        self,
        backtest_id: int,
        start_date: date,
        end_date: date,
        repository: BacktestRepository,
    ):
        """Initialize progress tracker.

        Args:
            backtest_id: ID of the backtest run
            start_date: Start date of the backtest
            end_date: End date of the backtest
            repository: BacktestRepository for persisting progress
        """
        self.backtest_id = backtest_id
        self.start_date = start_date
        self.end_date = end_date
        self.repository = repository

        # Calculate total days in range
        self.total_days = (end_date - start_date).days + 1

        self._last_update_time: float = 0.0
        self._current_progress: float = 0.0
        self._current_message: str = ""

    def update(self, current_date: date, message: str = "") -> None:
        """Update progress based on current simulation date.

        Calculates progress percentage and persists to database.
        Updates are throttled to max once per 500ms.

        Args:
            current_date: Current date in the simulation
            message: Optional status message
        """
        # Calculate progress
        days_processed = (current_date - self.start_date).days + 1
        progress_percent = min(100.0, (days_processed / self.total_days) * 100)

        # Check throttle
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self._last_update_time < self.THROTTLE_INTERVAL_MS:
            # Store values for next update but don't persist
            self._current_progress = progress_percent
            self._current_message = message
            return

        # Persist to database
        self._persist_progress(
            progress_percent=progress_percent,
            message=message,
            current_date=current_date,
            processed_days=days_processed,
        )
        self._last_update_time = current_time

    def set_phase(self, phase: str) -> None:
        """Update status message without changing date progress.

        Args:
            phase: Phase description (e.g., "Fetching data...", "Simulating trades...")
        """
        # Check throttle
        current_time = time.time() * 1000
        if current_time - self._last_update_time < self.THROTTLE_INTERVAL_MS:
            self._current_message = phase
            return

        # Persist only the message update
        self._persist_progress(
            progress_percent=self._current_progress,
            message=phase,
        )
        self._last_update_time = current_time

    def complete(self) -> None:
        """Mark progress as 100% complete.

        Always persists immediately, ignoring throttle.
        """
        self._persist_progress(
            progress_percent=100.0,
            message="Complete",
            processed_days=self.total_days,
        )

    def _persist_progress(
        self,
        progress_percent: float,
        message: str = "",
        current_date: date | None = None,
        processed_days: int | None = None,
    ) -> None:
        """Persist progress to database.

        Args:
            progress_percent: Progress percentage (0-100)
            message: Status message
            current_date: Current simulation date
            processed_days: Number of days processed
        """
        # Convert date to datetime for database
        current_datetime = None
        if current_date is not None:
            current_datetime = datetime.combine(current_date, datetime.min.time())

        self.repository.update_progress(
            backtest_id=self.backtest_id,
            progress_percent=progress_percent,
            progress_message=message,
            current_date=current_datetime,
            processed_days=processed_days,
        )

        # Update cached values
        self._current_progress = progress_percent
        self._current_message = message
