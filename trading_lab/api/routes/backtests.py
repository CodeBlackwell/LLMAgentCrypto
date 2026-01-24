"""Backtest-related API routes."""

import asyncio
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator

from ...core.config import BacktestConfig
from ...storage.database import get_db
from ...storage.repository import BacktestRepository, TradeRepository
from ...backtest.runner import get_runner
from ..schemas import (
    BacktestRequest,
    BacktestResponse,
    BacktestListResponse,
    BacktestSubmitResponse,
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


async def _stream_backtest_updates(backtest_id: int) -> AsyncGenerator[str, None]:
    """Generate SSE events for backtest progress updates.

    Polls database every 500ms and emits events only on changes.
    Auto-closes when status is terminal (completed or failed).
    """
    last_progress_percent: Optional[float] = None
    last_status: Optional[str] = None
    last_trade_count: int = 0

    while True:
        with get_db() as db:
            repo = BacktestRepository(db)
            run = repo.get(backtest_id)

            if run is None:
                # Backtest was deleted
                yield f"event: error\ndata: {json.dumps({'error': 'Backtest not found'})}\n\n"
                return

            # Check if there are changes to emit
            current_status = run.status
            current_progress = run.progress_percent

            # Get trades for this backtest
            trade_repo = TradeRepository(db)
            trades = trade_repo.list_for_backtest(backtest_id)
            current_trade_count = len(trades)

            # Emit progress event if changed
            if current_progress != last_progress_percent:
                progress_data = {
                    "progress_percent": current_progress,
                    "progress_message": run.progress_message,
                    "current_date": run.current_date.isoformat() if run.current_date else None,
                    "total_days": run.total_days,
                    "processed_days": run.processed_days,
                }
                yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"
                last_progress_percent = current_progress

            # Emit trades event if new trades
            if current_trade_count > last_trade_count:
                new_trades = trades[last_trade_count:]
                trades_data = [
                    {
                        "id": t.id,
                        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        "asset": t.asset,
                        "side": t.side,
                        "quantity": t.quantity,
                        "price": t.price,
                        "total_value": t.total_value,
                    }
                    for t in new_trades
                ]
                yield f"event: trades\ndata: {json.dumps(trades_data)}\n\n"
                last_trade_count = current_trade_count

            # Check for terminal status
            if current_status in ("completed", "failed"):
                if current_status != last_status:
                    if current_status == "completed":
                        complete_data = {
                            "status": "completed",
                            "final_value": run.final_value,
                            "total_return": run.total_return,
                            "total_trades": run.total_trades,
                        }
                        yield f"event: complete\ndata: {json.dumps(complete_data)}\n\n"
                    else:  # failed
                        error_data = {
                            "status": "failed",
                            "error_message": run.error_message,
                        }
                        yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
                return  # Close stream on terminal status

            last_status = current_status

        # Poll every 500ms
        await asyncio.sleep(0.5)


@router.get("/{backtest_id}/stream")
async def stream_backtest(backtest_id: int):
    """Stream real-time backtest updates via SSE.

    Emits events:
    - progress: Progress updates during execution
    - trades: New trades as they occur
    - complete: Backtest completed successfully
    - error: Backtest failed or not found

    Stream auto-closes when backtest reaches terminal status.
    """
    # Verify backtest exists before starting stream
    with get_db() as db:
        repo = BacktestRepository(db)
        run = repo.get(backtest_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest not found")

    return StreamingResponse(
        _stream_backtest_updates(backtest_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
