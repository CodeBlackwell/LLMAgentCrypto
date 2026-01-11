# Changelog

All notable changes to Trading Lab are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-01-11

### Added

#### Core Framework
- **BaseStrategy** (`trading_lab/core/strategy.py`) - Abstract base class with common trading functionality:
  - Position sizing integration
  - Signal provider composition
  - Unified order execution with trade tracking
  - Multi-asset support (crypto, stock, forex)

- **Signal System** (`trading_lab/core/signals.py`):
  - `Signal` dataclass with action, confidence, reasoning, and metadata
  - `SignalProvider` protocol for pluggable signal sources
  - `RandomSignalProvider` for baseline testing
  - `CompositeSignalProvider` for combining multiple providers

- **Position Sizing** (`trading_lab/core/sizing.py`):
  - `PositionSizer` protocol
  - `PercentOfCash` - Fixed percentage allocation
  - `FixedQuantity` - Predetermined trade size
  - `VolatilityAdjusted` - Risk-based sizing
  - `KellyCriterion` - Optimal growth sizing

- **Configuration** (`trading_lab/core/config.py`):
  - `Settings` - Pydantic settings with .env support
  - `BacktestConfig` - Validated backtest parameters
  - `StrategyConfig` - Strategy configuration schema

#### Strategies
- **Strategy Registry** (`trading_lab/strategies/registry.py`):
  - `@register` decorator for strategy discovery
  - `get_strategy()`, `list_strategies()`, `get_strategy_info()`

- **Built-in Strategies**:
  - `random` - Random buy/sell/hold baseline
  - `llm_sentiment` - Ollama-based sentiment analysis
  - `llm_recommendation` - Direct LLM buy/sell/hold recommendations
  - `finbert` - FinBERT transformer sentiment
  - `sentiment` - Configurable LLM or FinBERT
  - `contrarian` - Buy on negative sentiment
  - `dip_buyer` - Buy-only on dips

#### Signal Providers
- **News Providers** (`trading_lab/providers/news/`):
  - `SerperNewsProvider` - Google Serper API web search
  - `AlpacaNewsProvider` - Alpaca Markets news API (using alpaca-py)

- **Sentiment Providers** (`trading_lab/providers/sentiment/`):
  - `LLMSignalProvider` - Ollama + web search sentiment
  - `LLMSentimentProvider` - Sentiment classification mode
  - `LLMRecommendationProvider` - Direct recommendation mode
  - `FinBERTSignalProvider` - ProsusAI/finbert transformer
  - `FinBERTContrarianProvider` - Inverted sentiment signals

#### Backtesting
- **BacktestEngine** (`trading_lab/backtest/engine.py`):
  - Lumibot wrapper with multi-exchange support
  - Trading fee configuration
  - SQLite result persistence

- **BacktestRunner** (`trading_lab/backtest/runner.py`):
  - Async background execution
  - Job queue with callbacks
  - Cancel support

#### Storage Layer
- **Database** (`trading_lab/storage/database.py`):
  - SQLite with SQLAlchemy ORM
  - Context manager for sessions
  - Auto table creation

- **Models** (`trading_lab/storage/models.py`):
  - `BacktestRun` - Backtest execution records
  - `Trade` - Individual trade records
  - `DailyStat` - Daily portfolio statistics

- **Repository** (`trading_lab/storage/repository.py`):
  - `BacktestRepository` - CRUD for backtests
  - `TradeRepository` - Trade queries and bulk insert
  - `DailyStatRepository` - Statistics queries

#### REST API
- **FastAPI Application** (`trading_lab/api/main.py`):
  - CORS configuration for frontend
  - Lifespan management (startup/shutdown)
  - Health check endpoint

- **API Endpoints**:
  - `GET /api/strategies` - List available strategies
  - `GET /api/strategies/{name}` - Strategy details
  - `POST /api/backtests` - Start new backtest
  - `GET /api/backtests` - List backtests with filters
  - `GET /api/backtests/{id}` - Backtest status
  - `DELETE /api/backtests/{id}` - Delete backtest
  - `POST /api/backtests/{id}/cancel` - Cancel running backtest
  - `GET /api/results/{id}` - Full results with trades
  - `GET /api/results/{id}/trades` - Trade list
  - `GET /api/results/{id}/export` - CSV export
  - `POST /api/results/compare` - Compare multiple backtests

- **Schemas** (`trading_lab/api/schemas.py`):
  - Request/response Pydantic models
  - Validation for all endpoints

#### Web Frontend
- **React + Vite + TailwindCSS** (`trading_lab/web/`):
  - Dashboard with stats and recent backtests
  - Strategy browser with descriptions
  - Backtest list with filtering
  - New backtest form with validation
  - Backtest detail with equity curve chart
  - Trade history table

- **Components**:
  - Status badges (pending, running, completed, failed)
  - Metric cards
  - Navigation with active state

- **API Client** (`trading_lab/web/src/api/client.js`):
  - Fetch wrapper with error handling
  - All endpoint methods

#### Development Tooling
- **justfile** - Task runner with recipes:
  - `install` - Install Python + Node dependencies
  - `api` - Start FastAPI server
  - `web` - Start React dev server
  - `dev` - Start both servers
  - `db-init`, `db-tables`, `db-backtests`, `db-clear`
  - `test`, `fmt`, `lint`
  - `build`, `build-web`, `clean`
  - `health`, `docs`, `open`

- **pyproject.toml** - Modern Python packaging:
  - All dependencies with version constraints
  - Package discovery configuration
  - Dev dependency group

### Changed

- **Upgraded Alpaca SDK**: Replaced `alpaca-trade-api` with `alpaca-py>=0.30.0` to resolve websocket version conflict with lumibot
- **Upgraded Lumibot**: Updated to `lumibot>=4.0.0`
- **Project renamed**: From `29-05-2024-tradingv2` to `trading-lab`

### Fixed

- **Type annotation conflict**: Added `from __future__ import annotations` to resolve Lumibot overriding built-in `list` type
- **Package discovery**: Added explicit `[tool.setuptools.packages.find]` to exclude `archive/` and `logs/` directories

### Deprecated

- **Legacy strategy files**: Moved to `archive/` directory:
  - `0. randobot.py`
  - `1. cryptobot_aggregate_sentiment.py`
  - `1. cryptobot_aggregate_sentiment-r1.py`
  - `2. cryptobot_direct_recommendation.py`
  - `3. solana_direct_recommendation.py`
  - `4. old_bot_new_ml.py`
  - `5. dip.py`
  - `6. dip_contra.py`
  - `7. dip_contra_fees.py`
  - `crypto_journey/` directory

### Security

- **Credentials management**: API keys loaded from `.env` file via pydantic-settings, not hardcoded in source

---

## Architecture Overview

```
trading_lab/
├── core/           # Base abstractions (Strategy, Signal, Sizing, Config)
├── strategies/     # Strategy implementations with registry
├── providers/      # News and sentiment data providers
├── backtest/       # Lumibot wrapper and async runner
├── storage/        # SQLite with SQLAlchemy ORM
├── api/            # FastAPI REST endpoints
└── web/            # React + Vite frontend
```

## Quick Start

```bash
# Setup
uv venv && source .venv/bin/activate
just install

# Run
just dev  # Starts API on :8000 and Web on :3000
```
