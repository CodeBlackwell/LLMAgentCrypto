# Trading Lab Development Recipes
# Run `just --list` to see all available recipes

# Use bash for all recipes
set shell := ["bash", "-c"]

# Activate venv for Python commands
venv_activate := "source .venv/bin/activate &&"

# Default recipe - show available commands
default:
    @just --list

# ============== Setup ==============

# Install all dependencies (Python + Node)
install:
    {{venv_activate}} uv pip install -e .
    cd trading_lab/web && npm install

# Install Python dependencies only
install-python:
    {{venv_activate}} uv pip install -e .

# Install frontend dependencies only
install-web:
    cd trading_lab/web && npm install

# Create virtual environment
venv:
    uv venv
    @echo "Run 'source .venv/bin/activate' to activate"

# ============== Development ==============

# Start the FastAPI backend server
api:
    {{venv_activate}} uvicorn trading_lab.api.main:app --reload --host 0.0.0.0 --port 8847

# Start the React frontend dev server
web:
    cd trading_lab/web && npm run dev

# Start both API and web servers (requires terminal multiplexer)
dev:
    @echo "Starting API server on :8847 and Web server on :3847"
    @echo "Press Ctrl+C to stop"
    (trap 'kill 0' SIGINT; \
        {{venv_activate}} uvicorn trading_lab.api.main:app --reload --port 8847 & \
        cd trading_lab/web && npm run dev & \
        wait)

# Start API in background and return
api-bg:
    {{venv_activate}} uvicorn trading_lab.api.main:app --reload --port 8847 &
    @echo "API server started in background on :8847"

# ============== Database ==============

# Initialize/reset the database
db-init:
    {{venv_activate}} python -c "from trading_lab.storage.database import init_db; init_db()"
    @echo "Database initialized at trading_lab.db"

# Show database tables
db-tables:
    sqlite3 trading_lab.db ".tables"

# Show recent backtests
db-backtests:
    sqlite3 -header -column trading_lab.db "SELECT id, strategy_name, asset, status, total_return, created_at FROM backtest_runs ORDER BY created_at DESC LIMIT 10"

# Clear all backtest data
db-clear:
    rm -f trading_lab.db
    @echo "Database cleared"

# ============== Testing ==============

# Run a quick random backtest via API
test-backtest:
    curl -s -X POST http://localhost:8847/api/backtests \
        -H "Content-Type: application/json" \
        -d '{"strategy_name": "random", "asset": "BTC/USD", "start_date": "2024-01-01", "end_date": "2024-03-01"}' \
        | python -m json.tool

# List available strategies via API
test-strategies:
    curl -s http://localhost:8847/api/strategies | python -m json.tool

# Check API health
health:
    curl -s http://localhost:8847/health | python -m json.tool

# Run Python tests
test:
    {{venv_activate}} pytest

# Run tests with coverage
test-cov:
    {{venv_activate}} pytest --cov=trading_lab --cov-report=term-missing

# Run only unit tests
test-unit:
    {{venv_activate}} pytest trading_lab/tests/unit/ -v

# Run only integration tests
test-int:
    {{venv_activate}} pytest trading_lab/tests/integration/ -v

# Run tests matching a pattern
test-match pattern:
    {{venv_activate}} pytest -k "{{pattern}}" -v

# ============== Build ==============

# Build the frontend for production
build-web:
    cd trading_lab/web && npm run build

# Build Python package
build:
    {{venv_activate}} uv build

# ============== Linting & Formatting ==============

# Format Python code
fmt:
    {{venv_activate}} ruff format trading_lab/

# Lint Python code
lint:
    {{venv_activate}} ruff check trading_lab/

# Lint frontend code
lint-web:
    cd trading_lab/web && npm run lint

# ============== Teardown ==============

# Kill API and web servers running on default ports
kill:
    @echo "Killing processes on ports 8847 (API) and 3847 (Web)..."
    -lsof -ti:8847 | xargs -r kill -9 2>/dev/null || true
    -lsof -ti:3847 | xargs -r kill -9 2>/dev/null || true
    @echo "Done"

# ============== Utilities ==============

# Show project structure
tree:
    @echo "=== Project Structure ==="
    find trading_lab -type f \( -name "*.py" -o -name "*.jsx" \) | head -40

# Show environment variables
env:
    @echo "=== Environment Variables ==="
    @echo "SERPER_API_KEY: ${SERPER_API_KEY:-not set}"
    @echo "ALPACA_API_KEY: ${ALPACA_API_KEY:-not set}"
    @echo "ALPACA_API_SECRET: ${ALPACA_API_SECRET:+[set]}"

# Open API docs in browser
docs:
    xdg-open http://localhost:8847/docs 2>/dev/null || open http://localhost:8847/docs

# Open web UI in browser
open:
    xdg-open http://localhost:3847 2>/dev/null || open http://localhost:3847

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info/
    rm -rf trading_lab/web/dist/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ============== Docker (future) ==============

# Build docker image
# docker-build:
#     docker build -t trading-lab .

# Run in docker
# docker-run:
#     docker run -p 8847:8847 -p 3847:3847 trading-lab
