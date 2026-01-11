# Trading Lab

An elegant, extensible Algorithmic Trading Development and Backtesting Platform.

## Features

- **Modular Strategy Framework** - Build strategies by composing signal providers and position sizers
- **Multiple Signal Providers** - LLM-based (Ollama), FinBERT, or custom providers
- **Multi-Asset Support** - Crypto, stocks, and forex
- **Web Interface** - React-based dashboard for running and comparing backtests
- **REST API** - FastAPI backend for programmatic access
- **SQLite Storage** - Structured storage for backtest results

## Architecture

```
trading_lab/
├── core/           # Base abstractions (Strategy, Signal, Sizing)
├── strategies/     # Strategy implementations
├── providers/      # News and sentiment providers
├── backtest/       # Backtesting engine
├── storage/        # Database layer
├── api/            # FastAPI REST API
└── web/            # React frontend
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install Python dependencies
uv pip install -e .
```

### 2. Configure Environment

Create or update `.env` with your API keys:

```env
SERPER_API_KEY=your_serper_key
ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret
ALPACA_PAPER_TRADING_ENDPOINT=https://paper-api.alpaca.markets/v2
```

### 3. Start the API Server

```bash
uvicorn trading_lab.api.main:app --reload
```

The API will be available at http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- OpenAPI spec: http://localhost:8000/openapi.json

### 4. Start the Web UI (Optional)

```bash
cd trading_lab/web
npm install
npm run dev
```

The UI will be available at http://localhost:3000

## Usage

### Running a Backtest via API

```bash
curl -X POST http://localhost:8000/api/backtests \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "random",
    "asset": "BTC/USD",
    "asset_type": "crypto",
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "initial_cash": 100000
  }'
```

### Running a Backtest via Python

```python
from datetime import date
from trading_lab.core.config import BacktestConfig
from trading_lab.backtest.engine import run_backtest

config = BacktestConfig(
    strategy_name="sentiment",
    asset="BTC/USD",
    asset_type="crypto",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 6, 30),
    initial_cash=100_000,
    threshold=0.7,
)

results = run_backtest(config)
print(f"Total Return: {results['total_return']:.2f}%")
```

### Creating a Custom Strategy

```python
from trading_lab.core.strategy import BaseStrategy
from trading_lab.core.signals import Signal, SignalProvider
from trading_lab.strategies.registry import register

class MySignalProvider:
    @property
    def name(self) -> str:
        return "my_provider"

    def get_signal(self, asset: str, context: dict) -> Signal:
        # Your signal logic here
        return Signal(action="buy", confidence=0.8, reasoning="Custom logic")

@register(name="my_strategy", description="My custom strategy")
class MyStrategy(BaseStrategy):
    def initialize(self, **kwargs):
        super().initialize(
            signal_provider=MySignalProvider(),
            threshold=0.7,
            **kwargs
        )
```

## Available Strategies

| Strategy | Description | Signal Provider |
|----------|-------------|-----------------|
| `random` | Random buy/sell/hold baseline | Random |
| `llm_sentiment` | LLM-based sentiment analysis | Ollama + Serper |
| `llm_recommendation` | LLM direct recommendations | Ollama + Serper |
| `finbert` | FinBERT transformer sentiment | FinBERT + Alpaca |
| `contrarian` | Buy on negative sentiment | FinBERT (inverted) |
| `dip_buyer` | Buy-only on dips | FinBERT contrarian |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/strategies` | List available strategies |
| GET | `/api/strategies/{name}` | Get strategy details |
| POST | `/api/backtests` | Start new backtest |
| GET | `/api/backtests` | List all backtests |
| GET | `/api/backtests/{id}` | Get backtest status |
| DELETE | `/api/backtests/{id}` | Delete backtest |
| GET | `/api/results/{id}` | Get full results |
| GET | `/api/results/{id}/trades` | Get trades |
| GET | `/api/results/{id}/export` | Export as CSV |
| POST | `/api/results/compare` | Compare backtests |

## Requirements

- Python 3.12+
- Node.js 18+ (for web UI)
- Ollama (for LLM strategies)

## Legacy Strategies

The original strategy files are preserved in the `archive/` directory for reference.

## License

MIT License
