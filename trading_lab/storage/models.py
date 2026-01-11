"""SQLAlchemy models for Trading Lab."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, JSON,
    ForeignKey, Text, Index, Enum
)
from sqlalchemy.orm import declarative_base, relationship
import enum


Base = declarative_base()


class BacktestStatus(enum.Enum):
    """Status of a backtest run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestRun(Base):
    """Record of a single backtest execution."""

    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Strategy info
    strategy_name = Column(String(100), nullable=False, index=True)
    signal_provider = Column(String(100), nullable=True)

    # Asset info
    asset = Column(String(50), nullable=False, index=True)
    asset_type = Column(String(20), nullable=False)  # crypto, stock, forex
    exchange = Column(String(50), nullable=True)

    # Time range
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Initial conditions
    initial_cash = Column(Float, nullable=False, default=100000.0)

    # Results
    final_value = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)  # As percentage
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)

    # Metrics
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    volatility = Column(Float, nullable=True)

    # Configuration
    parameters = Column(JSON, nullable=True)  # Full strategy parameters

    # Status
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStat", back_populates="backtest", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_backtest_strategy_asset", "strategy_name", "asset"),
        Index("ix_backtest_created", "created_at"),
    )

    def __repr__(self):
        return f"<BacktestRun {self.id}: {self.strategy_name} on {self.asset}>"

    @property
    def win_rate(self) -> Optional[float]:
        """Calculate win rate from winning/total trades."""
        if self.total_trades and self.total_trades > 0:
            return (self.winning_trades or 0) / self.total_trades
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "strategy_name": self.strategy_name,
            "signal_provider": self.signal_provider,
            "asset": self.asset,
            "asset_type": self.asset_type,
            "exchange": self.exchange,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_cash": self.initial_cash,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Trade(Base):
    """Individual trade within a backtest."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False)

    # Trade details
    timestamp = Column(DateTime, nullable=False)
    asset = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=True)  # quantity * price

    # Signal info
    signal_action = Column(String(10), nullable=True)
    signal_confidence = Column(Float, nullable=True)
    signal_reasoning = Column(Text, nullable=True)

    # Status
    status = Column(String(20), default="filled")  # filled, cancelled, rejected

    # Relationships
    backtest = relationship("BacktestRun", back_populates="trades")

    __table_args__ = (
        Index("ix_trade_backtest", "backtest_id"),
        Index("ix_trade_timestamp", "timestamp"),
    )

    def __repr__(self):
        return f"<Trade {self.id}: {self.side} {self.quantity} {self.asset} @ {self.price}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "asset": self.asset,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "total_value": self.total_value,
            "signal_confidence": self.signal_confidence,
            "status": self.status,
        }


class DailyStat(Base):
    """Daily portfolio statistics."""

    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backtest_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False)

    # Date
    date = Column(DateTime, nullable=False)

    # Portfolio state
    portfolio_value = Column(Float, nullable=False)
    cash = Column(Float, nullable=False)
    positions_value = Column(Float, nullable=True)

    # Returns
    daily_return = Column(Float, nullable=True)  # As percentage
    cumulative_return = Column(Float, nullable=True)

    # Relationships
    backtest = relationship("BacktestRun", back_populates="daily_stats")

    __table_args__ = (
        Index("ix_dailystat_backtest", "backtest_id"),
        Index("ix_dailystat_date", "date"),
    )

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat() if self.date else None,
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "daily_return": self.daily_return,
            "cumulative_return": self.cumulative_return,
        }
