"""FastAPI application for Trading Lab."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..storage.database import init_db
from ..strategies import random, sentiment, contrarian  # Import to register
from .routes import strategies, backtests, results


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    init_db()
    yield
    # Shutdown
    from ..backtest.runner import get_runner
    get_runner().shutdown(wait=False)


app = FastAPI(
    title="Trading Lab",
    description="Algorithmic Trading Development and Backtesting Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategies.router, prefix="/api/strategies")
app.include_router(backtests.router, prefix="/api/backtests")
app.include_router(results.router, prefix="/api/results")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Trading Lab API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
