"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from trading_lab.storage.models import Base
from trading_lab.storage import database
from trading_lab.core.signals import Signal, RandomSignalProvider
from trading_lab.core.sizing import PercentOfCash

from .fixtures.mock_providers import (
    MockSignalProvider,
    MockNewsProvider,
    AlwaysBuyProvider,
    AlwaysSellProvider,
    AlwaysHoldProvider,
)
from .fixtures.sample_data import (
    sample_signal,
    sample_backtest_config,
    TEST_CONTEXT,
)


# ============== Database Fixtures ==============

@pytest.fixture
def in_memory_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(in_memory_engine):
    """Create a database session for testing.

    Yields a session and rolls back after the test.
    """
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=in_memory_engine
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def override_db(in_memory_engine):
    """Override the global database for testing.

    Patches the database module to use in-memory database.
    """
    original_engine = database._engine
    original_session = database._SessionLocal

    database._engine = in_memory_engine
    database._SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=in_memory_engine
    )

    yield

    database._engine = original_engine
    database._SessionLocal = original_session


# ============== FastAPI Test Client ==============

@pytest.fixture
def reset_runner():
    """Reset the global backtest runner between tests."""
    from trading_lab.backtest import runner

    # Store original runner
    original_runner = runner._runner

    # Create a fresh runner for this test
    runner._runner = None

    yield

    # Shutdown the test runner if it was created
    if runner._runner is not None:
        runner._runner.shutdown(wait=False)

    # Restore original (don't restore if it was shutdown)
    runner._runner = None


@pytest.fixture
def test_client(override_db, reset_runner):
    """Create a FastAPI test client with in-memory database."""
    from fastapi.testclient import TestClient
    from trading_lab.api.main import app

    with TestClient(app) as client:
        yield client


# ============== Signal Provider Fixtures ==============

@pytest.fixture
def mock_provider():
    """Create a mock signal provider."""
    return MockSignalProvider()


@pytest.fixture
def random_provider():
    """Create a seeded random signal provider."""
    return RandomSignalProvider(seed=42)


@pytest.fixture
def buy_provider():
    """Create a provider that always returns buy."""
    return AlwaysBuyProvider()


@pytest.fixture
def sell_provider():
    """Create a provider that always returns sell."""
    return AlwaysSellProvider()


@pytest.fixture
def hold_provider():
    """Create a provider that always returns hold."""
    return AlwaysHoldProvider()


@pytest.fixture
def mock_news_provider():
    """Create a mock news provider."""
    return MockNewsProvider()


# ============== Position Sizer Fixtures ==============

@pytest.fixture
def percent_sizer():
    """Create a PercentOfCash sizer at 25%."""
    return PercentOfCash(percent=0.25)


# ============== Sample Data Fixtures ==============

@pytest.fixture
def sample_buy_signal():
    """Create a sample buy signal."""
    return sample_signal(action="buy", confidence=0.85)


@pytest.fixture
def sample_sell_signal():
    """Create a sample sell signal."""
    return sample_signal(action="sell", confidence=0.75)


@pytest.fixture
def sample_hold_signal():
    """Create a sample hold signal."""
    return sample_signal(action="hold", confidence=0.5)


@pytest.fixture
def test_context():
    """Create a sample context dict for signal providers."""
    return TEST_CONTEXT.copy()


@pytest.fixture
def backtest_config():
    """Create a sample backtest configuration."""
    return sample_backtest_config()
