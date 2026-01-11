"""Sample data for testing."""

from __future__ import annotations

from datetime import date, datetime
from trading_lab.core.signals import Signal


def sample_signal(
    action: str = "buy",
    confidence: float = 0.8,
    reasoning: str = "Test signal",
) -> Signal:
    """Create a sample signal for testing."""
    return Signal(
        action=action,
        confidence=confidence,
        reasoning=reasoning,
        metadata={"test": True}
    )


def sample_backtest_config() -> dict:
    """Create a sample backtest configuration dict for API requests."""
    return {
        "strategy_name": "random",
        "asset": "BTC/USD",
        "asset_type": "crypto",
        "start_date": "2024-01-01",
        "end_date": "2024-03-01",
        "initial_cash": 100000.0,
        "signal_provider": "random",  # Required field
        "threshold": 0.7,
        "cash_at_risk": 0.25,
        "exchange": "kraken",
    }


def sample_backtest_result() -> dict:
    """Create a sample backtest result."""
    return {
        "strategy_name": "random",
        "asset": "BTC/USD",
        "initial_cash": 100000.0,
        "final_value": 105000.0,
        "total_return": 5.0,
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.08,
        "trades": 15,
    }


def sample_trade() -> dict:
    """Create a sample trade record."""
    return {
        "timestamp": datetime.now(),
        "asset": "BTC/USD",
        "side": "buy",
        "quantity": 0.5,
        "price": 45000.0,
        "signal_confidence": 0.85,
    }


# Common test dates
TEST_START_DATE = date(2024, 1, 1)
TEST_END_DATE = date(2024, 3, 1)

# Common test context for signal providers
TEST_CONTEXT = {
    "current_date": "2024-03-01",
    "lookback_date": "2024-02-27",
    "lookback_days": 3,
    "asset_type": "crypto",
}
