"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator


# ============== Strategy Schemas ==============

class StrategyInfo(BaseModel):
    """Information about a registered strategy."""
    name: str
    description: str
    default_provider: str
    asset_types: list[str]
    class_name: str


class StrategyListResponse(BaseModel):
    """Response for listing strategies."""
    strategies: list[StrategyInfo]


# ============== Backtest Schemas ==============

class BacktestRequest(BaseModel):
    """Request to start a new backtest."""
    strategy_name: str = Field(..., description="Name of strategy to run")
    asset: str = Field(..., description="Asset symbol (e.g., BTC/USD)")
    asset_type: Literal["crypto", "stock", "forex"] = Field(default="crypto")
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    initial_cash: float = Field(default=100_000.0, ge=100)

    # Strategy parameters
    signal_provider: Optional[str] = Field(default=None)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    cash_at_risk: float = Field(default=0.25, ge=0.0, le=1.0)

    # Exchange settings
    exchange: str = Field(default="kraken")

    @model_validator(mode="after")
    def validate_date_range(self) -> "BacktestRequest":
        """Validate that end_date is after start_date and range <= 2 years."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")

        # Calculate days between dates
        days = (self.end_date - self.start_date).days
        if days > 730:
            raise ValueError(
                f"Date range must be <= 2 years (730 days). Got {days} days."
            )

        return self


class BacktestResponse(BaseModel):
    """Response with backtest information."""
    id: int
    strategy_name: str
    signal_provider: Optional[str]
    asset: str
    asset_type: str
    exchange: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    initial_cash: float
    final_value: Optional[float]
    total_return: Optional[float]
    total_trades: Optional[int]
    win_rate: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    status: str
    created_at: Optional[str]
    completed_at: Optional[str]
    # Progress tracking fields
    progress_percent: Optional[float] = None
    progress_message: Optional[str] = None
    current_date: Optional[str] = None
    total_days: Optional[int] = None
    processed_days: Optional[int] = None
    error_message: Optional[str] = None


class BacktestListResponse(BaseModel):
    """Response for listing backtests."""
    backtests: list[BacktestResponse]
    total: int


class BacktestSubmitResponse(BaseModel):
    """Response when submitting a backtest."""
    backtest_id: int
    status: str
    message: str


# ============== Trade Schemas ==============

class TradeResponse(BaseModel):
    """Response with trade information."""
    id: int
    timestamp: Optional[str]
    asset: str
    side: str
    quantity: float
    price: float
    total_value: Optional[float]
    signal_confidence: Optional[float]
    status: str


class TradeListResponse(BaseModel):
    """Response for listing trades."""
    trades: list[TradeResponse]
    total: int


# ============== Results Schemas ==============

class DailyStatResponse(BaseModel):
    """Daily portfolio statistics."""
    date: str
    portfolio_value: float
    cash: float
    daily_return: Optional[float]
    cumulative_return: Optional[float]


class BacktestResultsResponse(BaseModel):
    """Full backtest results with trades and daily stats."""
    backtest: BacktestResponse
    trades: list[TradeResponse]
    daily_stats: list[DailyStatResponse]


class CompareRequest(BaseModel):
    """Request to compare backtests."""
    backtest_ids: list[int] = Field(..., min_length=2, max_length=10)


class CompareResponse(BaseModel):
    """Response comparing multiple backtests."""
    backtests: list[BacktestResponse]


# ============== Error Schemas ==============

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
