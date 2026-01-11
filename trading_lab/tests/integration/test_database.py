"""Integration tests for database operations."""

from __future__ import annotations

import pytest
from datetime import datetime, date

from trading_lab.storage.models import BacktestRun, Trade, DailyStat
from trading_lab.storage.repository import (
    BacktestRepository,
    TradeRepository,
    DailyStatRepository,
)


class TestBacktestRepository:
    """Tests for BacktestRepository."""

    def test_create_backtest(self, db_session):
        """Test creating a backtest run."""
        repo = BacktestRepository(db_session)

        run = repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
            initial_cash=100000.0,
            signal_provider="random",
            exchange="kraken",
        )

        assert run.id is not None
        assert run.strategy_name == "random"
        assert run.asset == "BTC/USD"
        assert run.status == "pending"

    def test_get_backtest(self, db_session):
        """Test getting a backtest by ID."""
        repo = BacktestRepository(db_session)

        # Create a backtest
        created = repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        # Get it back
        retrieved = repo.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.strategy_name == "random"

    def test_get_nonexistent_returns_none(self, db_session):
        """Test getting nonexistent backtest returns None."""
        repo = BacktestRepository(db_session)
        result = repo.get(99999)
        assert result is None

    def test_list_backtests_empty(self, db_session):
        """Test listing empty backtests."""
        repo = BacktestRepository(db_session)
        runs = repo.list()
        assert runs == []

    def test_list_backtests_with_data(self, db_session):
        """Test listing backtests with data."""
        repo = BacktestRepository(db_session)

        # Create multiple backtests
        for i in range(3):
            repo.create(
                strategy_name=f"strategy_{i}",
                asset="BTC/USD",
                asset_type="crypto",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 3, 1),
            )
        db_session.commit()

        runs = repo.list()
        assert len(runs) == 3

    def test_list_filter_by_strategy(self, db_session):
        """Test filtering by strategy name."""
        repo = BacktestRepository(db_session)

        repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        repo.create(
            strategy_name="sentiment",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        runs = repo.list(strategy_name="random")
        assert len(runs) == 1
        assert runs[0].strategy_name == "random"

    def test_list_filter_by_asset(self, db_session):
        """Test filtering by asset."""
        repo = BacktestRepository(db_session)

        repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        repo.create(
            strategy_name="random",
            asset="ETH/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        runs = repo.list(asset="ETH/USD")
        assert len(runs) == 1
        assert runs[0].asset == "ETH/USD"

    def test_list_with_pagination(self, db_session):
        """Test pagination."""
        repo = BacktestRepository(db_session)

        for i in range(5):
            repo.create(
                strategy_name=f"strategy_{i}",
                asset="BTC/USD",
                asset_type="crypto",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 3, 1),
            )
        db_session.commit()

        # Get first 2
        first_page = repo.list(limit=2, offset=0)
        assert len(first_page) == 2

        # Get next 2
        second_page = repo.list(limit=2, offset=2)
        assert len(second_page) == 2

        # Verify they're different
        assert first_page[0].id != second_page[0].id

    def test_update_status(self, db_session):
        """Test updating backtest status."""
        repo = BacktestRepository(db_session)

        run = repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        repo.update_status(run.id, "running")
        db_session.commit()

        updated = repo.get(run.id)
        assert updated.status == "running"
        assert updated.started_at is not None

    def test_update_results(self, db_session):
        """Test updating backtest results."""
        repo = BacktestRepository(db_session)

        run = repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        repo.update_results(
            run.id,
            final_value=110000.0,
            total_return=10.0,
            total_trades=15,
            sharpe_ratio=1.5,
            max_drawdown=0.08,
        )
        db_session.commit()

        updated = repo.get(run.id)
        assert updated.final_value == 110000.0
        assert updated.total_return == 10.0
        assert updated.status == "completed"

    def test_delete_backtest(self, db_session):
        """Test deleting a backtest."""
        repo = BacktestRepository(db_session)

        run = repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()
        run_id = run.id

        result = repo.delete(run_id)
        db_session.commit()

        assert result is True
        assert repo.get(run_id) is None

    def test_delete_nonexistent(self, db_session):
        """Test deleting nonexistent backtest."""
        repo = BacktestRepository(db_session)
        result = repo.delete(99999)
        assert result is False


class TestTradeRepository:
    """Tests for TradeRepository."""

    def test_create_trade(self, db_session):
        """Test creating a trade."""
        backtest_repo = BacktestRepository(db_session)
        trade_repo = TradeRepository(db_session)

        # Create backtest first
        run = backtest_repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        # Create trade
        trade = trade_repo.create(
            backtest_id=run.id,
            timestamp=datetime(2024, 1, 15),
            asset="BTC/USD",
            side="buy",
            quantity=0.5,
            price=45000.0,
            signal_action="buy",
            signal_confidence=0.85,
        )
        db_session.commit()

        assert trade.id is not None
        assert trade.total_value == 22500.0

    def test_list_trades_for_backtest(self, db_session):
        """Test listing trades for a backtest."""
        backtest_repo = BacktestRepository(db_session)
        trade_repo = TradeRepository(db_session)

        run = backtest_repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        # Create multiple trades
        for i in range(3):
            trade_repo.create(
                backtest_id=run.id,
                timestamp=datetime(2024, 1, i + 1),
                asset="BTC/USD",
                side="buy" if i % 2 == 0 else "sell",
                quantity=0.5,
                price=45000.0 + i * 1000,
            )
        db_session.commit()

        trades = trade_repo.list_for_backtest(run.id)
        assert len(trades) == 3

    def test_bulk_create_trades(self, db_session):
        """Test bulk creating trades."""
        backtest_repo = BacktestRepository(db_session)
        trade_repo = TradeRepository(db_session)

        run = backtest_repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        trades_data = [
            {
                "timestamp": datetime(2024, 1, i + 1),
                "asset": "BTC/USD",
                "side": "buy",
                "quantity": 0.1,
                "price": 45000.0,
            }
            for i in range(10)
        ]

        count = trade_repo.bulk_create(trades_data, run.id)
        db_session.commit()

        assert count == 10
        assert len(trade_repo.list_for_backtest(run.id)) == 10


class TestDailyStatRepository:
    """Tests for DailyStatRepository."""

    def test_create_daily_stat(self, db_session):
        """Test creating a daily stat."""
        backtest_repo = BacktestRepository(db_session)
        stat_repo = DailyStatRepository(db_session)

        run = backtest_repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        stat = stat_repo.create(
            backtest_id=run.id,
            date=datetime(2024, 1, 15),
            portfolio_value=102000.0,
            cash=50000.0,
            positions_value=52000.0,
            daily_return=0.02,
        )
        db_session.commit()

        assert stat.id is not None
        assert stat.portfolio_value == 102000.0

    def test_list_daily_stats_ordered(self, db_session):
        """Test that daily stats are ordered by date."""
        backtest_repo = BacktestRepository(db_session)
        stat_repo = DailyStatRepository(db_session)

        run = backtest_repo.create(
            strategy_name="random",
            asset="BTC/USD",
            asset_type="crypto",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 3, 1),
        )
        db_session.commit()

        # Create stats out of order
        for day in [3, 1, 2]:
            stat_repo.create(
                backtest_id=run.id,
                date=datetime(2024, 1, day),
                portfolio_value=100000.0 + day * 1000,
                cash=50000.0,
            )
        db_session.commit()

        stats = stat_repo.list_for_backtest(run.id)

        # Should be ordered by date
        assert stats[0].date < stats[1].date < stats[2].date
