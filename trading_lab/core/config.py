"""Configuration management for Trading Lab."""

from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables can be set directly or via .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys
    alpaca_api_key: str = Field(default="", description="Alpaca API key")
    alpaca_api_secret: str = Field(default="", description="Alpaca API secret")
    alpaca_paper_trading_endpoint: str = Field(
        default="https://paper-api.alpaca.markets/v2",
        description="Alpaca paper trading endpoint"
    )
    serper_api_key: str = Field(default="", description="Serper API key for web search")

    # Database
    database_url: str = Field(
        default="sqlite:///./trading_lab.db",
        description="Database connection URL"
    )

    # Ollama (local LLM)
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API host")
    ollama_model: str = Field(default="qwen2.5:14b", description="Default Ollama model")

    # Defaults
    default_exchange: str = Field(default="kraken", description="Default crypto exchange")
    default_initial_cash: float = Field(default=100_000.0, description="Default backtest cash")


class BacktestConfig(BaseModel):
    """Configuration for a single backtest run."""

    strategy_name: str = Field(..., description="Name of strategy to run")
    asset: str = Field(..., description="Asset symbol (e.g., BTC/USD, AAPL)")
    asset_type: Literal["crypto", "stock", "forex"] = Field(
        default="crypto",
        description="Asset class"
    )
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    initial_cash: float = Field(default=100_000.0, ge=0, description="Starting cash")

    # Strategy parameters
    signal_provider: str = Field(default="random", description="Signal provider to use")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Signal threshold")
    cash_at_risk: float = Field(default=0.25, ge=0.0, le=1.0, description="Position size %")

    # Exchange settings
    exchange: str = Field(default="kraken", description="Exchange for crypto data")

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class StrategyConfig(BaseModel):
    """Configuration for a trading strategy."""

    name: str = Field(..., description="Strategy name")
    description: str = Field(default="", description="Strategy description")
    signal_provider: str = Field(..., description="Signal provider name")
    sizer: str = Field(default="percent_of_cash", description="Position sizer name")

    # Signal parameters
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Signal threshold")
    lookback_days: int = Field(default=3, ge=1, description="Days of history for signals")

    # Position sizing parameters
    cash_at_risk: float = Field(default=0.25, ge=0.0, le=1.0, description="Position size %")

    # Trading parameters
    sleeptime: str = Field(default="1D", description="Trading frequency")

    # Asset configuration
    default_asset: str = Field(default="BTC/USD", description="Default asset to trade")
    asset_type: Literal["crypto", "stock", "forex"] = Field(default="crypto")


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
