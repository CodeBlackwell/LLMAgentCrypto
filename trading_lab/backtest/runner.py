"""Async backtest runner for background execution."""

import asyncio
import signal
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Callable
import logging

from ..core.config import BacktestConfig
from ..storage.database import get_db
from ..storage.repository import BacktestRepository
from .engine import BacktestEngine
from .progress import ProgressTracker

logger = logging.getLogger(__name__)


@contextmanager
def safe_signal_handling():
    """Context manager that allows signal.signal calls in non-main threads.

    Lumibot calls signal.signal() internally, which raises ValueError
    when called from a non-main thread. This context manager monkey-patches
    signal.signal to be a no-op when not in the main thread.
    """
    original_signal = signal.signal

    def patched_signal(signalnum, handler):
        if threading.current_thread() is threading.main_thread():
            return original_signal(signalnum, handler)
        # In non-main threads, just return the current handler without setting
        try:
            return signal.getsignal(signalnum)
        except Exception:
            return signal.SIG_DFL

    signal.signal = patched_signal
    try:
        yield
    finally:
        signal.signal = original_signal


class BacktestRunner:
    """Async runner for executing backtests in the background.

    Manages a queue of backtest jobs and executes them
    using a thread pool.
    """

    def __init__(
        self,
        max_workers: int = 2,
        on_complete: Optional[Callable[[int, dict], None]] = None,
        on_error: Optional[Callable[[int, Exception], None]] = None,
    ):
        """Initialize the backtest runner.

        Args:
            max_workers: Maximum concurrent backtests
            on_complete: Callback when backtest completes (id, results)
            on_error: Callback when backtest fails (id, exception)
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running: dict[int, asyncio.Future] = {}
        self._on_complete = on_complete
        self._on_error = on_error

    async def submit(self, config: BacktestConfig, **engine_kwargs) -> int:
        """Submit a backtest for execution.

        Args:
            config: Backtest configuration
            **engine_kwargs: Passed to BacktestEngine

        Returns:
            Backtest ID
        """
        # Create database record
        with get_db() as db:
            repo = BacktestRepository(db)
            run = repo.create(
                strategy_name=config.strategy_name,
                asset=config.asset,
                asset_type=config.asset_type,
                start_date=datetime.combine(config.start_date, datetime.min.time()),
                end_date=datetime.combine(config.end_date, datetime.min.time()),
                initial_cash=config.initial_cash,
                signal_provider=config.signal_provider,
                exchange=config.exchange,
                parameters={
                    "cash_at_risk": config.cash_at_risk,
                    "threshold": config.threshold,
                },
            )
            backtest_id = run.id

        # Submit to thread pool
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self._executor,
            self._run_backtest,
            backtest_id,
            config,
            engine_kwargs,
        )
        self._running[backtest_id] = future

        # Set up completion callback
        future.add_done_callback(
            lambda f: self._handle_completion(backtest_id, f)
        )

        return backtest_id

    def _run_backtest(
        self,
        backtest_id: int,
        config: BacktestConfig,
        engine_kwargs: dict,
    ) -> dict:
        """Run backtest in thread pool."""
        # Update status to running and initialize progress tracker
        with get_db() as db:
            repo = BacktestRepository(db)
            repo.update_status(backtest_id, "running")

            # Create progress tracker for this backtest
            progress_tracker = ProgressTracker(
                backtest_id=backtest_id,
                start_date=config.start_date,
                end_date=config.end_date,
                repository=repo,
            )

            # Initialize total_days in database
            run = repo.get(backtest_id)
            if run:
                run.total_days = progress_tracker.total_days
                db.commit()

        # Run the backtest with safe signal handling for non-main threads
        with safe_signal_handling():
            # Create a new progress tracker with fresh db session for engine use
            with get_db() as db:
                repo = BacktestRepository(db)
                progress_tracker = ProgressTracker(
                    backtest_id=backtest_id,
                    start_date=config.start_date,
                    end_date=config.end_date,
                    repository=repo,
                )

                # Pass progress tracker to engine
                engine = BacktestEngine(progress_tracker=progress_tracker, **engine_kwargs)
                # Don't save to DB again since we already created the record
                result = engine.run(config, save_to_db=False)

                # Mark progress as 100% complete on successful completion
                progress_tracker.complete()

        result["backtest_id"] = backtest_id

        # Update results
        with get_db() as db:
            repo = BacktestRepository(db)
            repo.update_results(
                backtest_id=backtest_id,
                final_value=result.get("final_value", config.initial_cash),
                total_return=result.get("total_return", 0),
                sharpe_ratio=result.get("sharpe_ratio"),
                max_drawdown=result.get("max_drawdown"),
            )

        return result

    def _handle_completion(self, backtest_id: int, future: asyncio.Future):
        """Handle backtest completion or failure."""
        self._running.pop(backtest_id, None)

        try:
            result = future.result()
            if self._on_complete:
                self._on_complete(backtest_id, result)
        except Exception as e:
            logger.exception(f"Backtest {backtest_id} failed: {e}")

            # Update status to failed
            with get_db() as db:
                repo = BacktestRepository(db)
                repo.update_status(backtest_id, "failed", str(e))

            if self._on_error:
                self._on_error(backtest_id, e)

    async def get_status(self, backtest_id: int) -> dict:
        """Get status of a backtest.

        Args:
            backtest_id: Backtest ID

        Returns:
            Status dictionary
        """
        with get_db() as db:
            repo = BacktestRepository(db)
            run = repo.get(backtest_id)

            if run is None:
                return {"error": "Backtest not found"}

            return run.to_dict()

    async def cancel(self, backtest_id: int) -> bool:
        """Cancel a running backtest.

        Args:
            backtest_id: Backtest ID

        Returns:
            True if cancelled, False if not running
        """
        future = self._running.get(backtest_id)
        if future is None:
            return False

        future.cancel()
        self._running.pop(backtest_id, None)

        with get_db() as db:
            repo = BacktestRepository(db)
            repo.update_status(backtest_id, "cancelled")

        return True

    def shutdown(self, wait: bool = True):
        """Shutdown the executor.

        Args:
            wait: Whether to wait for running backtests
        """
        self._executor.shutdown(wait=wait)


# Global runner instance
_runner: Optional[BacktestRunner] = None


def get_runner() -> BacktestRunner:
    """Get or create the global backtest runner."""
    global _runner
    if _runner is None:
        _runner = BacktestRunner()
    return _runner
