"""Results and analysis API routes."""

import csv
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ...storage.database import get_db
from ...storage.repository import BacktestRepository, TradeRepository, DailyStatRepository
from ..schemas import (
    BacktestResponse,
    TradeResponse,
    TradeListResponse,
    DailyStatResponse,
    BacktestResultsResponse,
    CompareRequest,
    CompareResponse,
)

router = APIRouter(tags=["results"])


@router.get("/{backtest_id}", response_model=BacktestResultsResponse)
async def get_backtest_results(backtest_id: int):
    """Get full results for a backtest including trades and daily stats."""
    with get_db() as db:
        backtest_repo = BacktestRepository(db)
        trade_repo = TradeRepository(db)
        stat_repo = DailyStatRepository(db)

        run = backtest_repo.get(backtest_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest not found")

        trades = trade_repo.list_for_backtest(backtest_id)
        daily_stats = stat_repo.list_for_backtest(backtest_id)

        return BacktestResultsResponse(
            backtest=BacktestResponse(**run.to_dict()),
            trades=[TradeResponse(**t.to_dict()) for t in trades],
            daily_stats=[DailyStatResponse(**s.to_dict()) for s in daily_stats],
        )


@router.get("/{backtest_id}/trades", response_model=TradeListResponse)
async def get_backtest_trades(
    backtest_id: int,
    limit: int = 1000,
    offset: int = 0,
):
    """Get trades for a specific backtest."""
    with get_db() as db:
        backtest_repo = BacktestRepository(db)
        trade_repo = TradeRepository(db)

        run = backtest_repo.get(backtest_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest not found")

        trades = trade_repo.list_for_backtest(backtest_id, limit=limit, offset=offset)

        return TradeListResponse(
            trades=[TradeResponse(**t.to_dict()) for t in trades],
            total=len(trades),
        )


@router.post("/compare", response_model=CompareResponse)
async def compare_backtests(request: CompareRequest):
    """Compare multiple backtests side by side."""
    with get_db() as db:
        repo = BacktestRepository(db)
        runs = repo.compare(request.backtest_ids)

        if len(runs) != len(request.backtest_ids):
            found_ids = {r.id for r in runs}
            missing = [id for id in request.backtest_ids if id not in found_ids]
            raise HTTPException(
                status_code=404,
                detail=f"Backtests not found: {missing}"
            )

        return CompareResponse(
            backtests=[BacktestResponse(**run.to_dict()) for run in runs]
        )


@router.get("/{backtest_id}/export")
async def export_backtest_csv(backtest_id: int):
    """Export backtest results as CSV."""
    with get_db() as db:
        backtest_repo = BacktestRepository(db)
        trade_repo = TradeRepository(db)

        run = backtest_repo.get(backtest_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Backtest not found")

        trades = trade_repo.list_for_backtest(backtest_id)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "timestamp", "asset", "side", "quantity",
            "price", "total_value", "signal_confidence"
        ])

        # Write trades
        for trade in trades:
            writer.writerow([
                trade.timestamp.isoformat() if trade.timestamp else "",
                trade.asset,
                trade.side,
                trade.quantity,
                trade.price,
                trade.total_value,
                trade.signal_confidence,
            ])

        output.seek(0)

        filename = f"backtest_{backtest_id}_trades.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
