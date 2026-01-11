"""Backtest-related API routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional

from ...core.config import BacktestConfig
from ...storage.database import get_db
from ...storage.repository import BacktestRepository
from ...backtest.runner import get_runner
from ..schemas import (
    BacktestRequest,
    BacktestResponse,
    BacktestListResponse,
    BacktestSubmitResponse,
    ErrorResponse,
)

router = APIRouter(tags=["backtests"])


@router.post("", response_model=BacktestSubmitResponse)
async def create_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Start a new backtest.

    The backtest runs in the background. Use GET /backtests/{id}
    to check status.
    """
    # Convert request to config
    config = BacktestConfig(
        strategy_name=request.strategy_name,
        asset=request.asset,
        asset_type=request.asset_type,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_cash=request.initial_cash,
        signal_provider=request.signal_provider,
        threshold=request.threshold,
        cash_at_risk=request.cash_at_risk,
        exchange=request.exchange,
    )

    # Submit to runner
    runner = get_runner()
    backtest_id = await runner.submit(config)

    return BacktestSubmitResponse(
        backtest_id=backtest_id,
        status="pending",
        message=f"Backtest submitted. Check status at /api/backtests/{backtest_id}"
    )


@router.get("", response_model=BacktestListResponse)
async def list_backtests(
    strategy_name: Optional[str] = None,
    asset: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List backtests with optional filters."""
    with get_db() as db:
        repo = BacktestRepository(db)
        runs = repo.list(
            strategy_name=strategy_name,
            asset=asset,
            status=status,
            limit=limit,
            offset=offset,
        )

        backtests = [BacktestResponse(**run.to_dict()) for run in runs]

        return BacktestListResponse(
            backtests=backtests,
            total=len(backtests),
        )


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(backtest_id: int):
    """Get details of a specific backtest."""
    with get_db() as db:
        repo = BacktestRepository(db)
        run = repo.get(backtest_id)

        if run is None:
            raise HTTPException(status_code=404, detail="Backtest not found")

        return BacktestResponse(**run.to_dict())


@router.delete("/{backtest_id}")
async def delete_backtest(backtest_id: int):
    """Delete a backtest and all associated data."""
    with get_db() as db:
        repo = BacktestRepository(db)

        if not repo.delete(backtest_id):
            raise HTTPException(status_code=404, detail="Backtest not found")

        return {"message": f"Backtest {backtest_id} deleted"}


@router.post("/{backtest_id}/cancel")
async def cancel_backtest(backtest_id: int):
    """Cancel a running backtest."""
    runner = get_runner()

    if await runner.cancel(backtest_id):
        return {"message": f"Backtest {backtest_id} cancelled"}
    else:
        raise HTTPException(
            status_code=400,
            detail="Backtest is not running or already completed"
        )
