# tlab-sse-backend Agent

## Mission
Add a Server-Sent Events (SSE) streaming endpoint for real-time backtest updates without polling.

## Wave
2 (Depends on Wave 1)

## Dependencies
- Wave 0 must be complete (schema and repository)
- Wave 1 must be complete (progress tracking)

## Owned Paths (Exclusive Write)
- `trading_lab/api/routes/backtests.py` (SSE endpoint only - validation agent owns validation logic)

## Shared Paths (Read Only)
- `trading_lab/storage/repository.py`
- `trading_lab/storage/models.py`
- `trading_lab/api/schemas.py`

## User Stories

### US-007: Add SSE streaming endpoint
**Description:** As a developer, I need an SSE endpoint so the frontend can receive real-time backtest updates without polling.

**Acceptance Criteria:**
- [ ] Add `GET /backtests/{backtest_id}/stream` endpoint in `trading_lab/api/routes/backtests.py`
- [ ] Return `StreamingResponse` with `media_type="text/event-stream"`
- [ ] Emit event types: `progress`, `trades`, `complete`, `error`
- [ ] Poll database every 500ms, emit only on changes
- [ ] Auto-close stream when status is terminal (`completed` or `failed`)
- [ ] Include `Cache-Control: no-cache` and `Connection: keep-alive` headers
- [ ] Typecheck passes

## Implementation Notes

### SSE Event Format
```
event: progress
data: {"progress_percent": 45.5, "progress_message": "Simulating trades...", "processed_days": 45, "total_days": 100}

event: trades
data: {"trades": [{"side": "BUY", "quantity": 0.5, "price": 45000, "timestamp": "2024-01-15T10:30:00"}]}

event: complete
data: {"status": "completed", "final_value": 12500.00}

event: error
data: {"status": "failed", "error_message": "Insufficient data for date range"}
```

### FastAPI Implementation Pattern
```python
from fastapi.responses import StreamingResponse
import asyncio
import json

async def generate_events(backtest_id: str):
    last_progress = None
    while True:
        backtest = repository.get_by_id(backtest_id)
        if not backtest:
            yield f"event: error\ndata: {json.dumps({'error': 'Backtest not found'})}\n\n"
            break

        # Emit progress if changed
        current_progress = backtest.progress_percent
        if current_progress != last_progress:
            yield f"event: progress\ndata: {json.dumps(backtest.to_dict())}\n\n"
            last_progress = current_progress

        # Check terminal state
        if backtest.status in ('completed', 'failed'):
            event_type = 'complete' if backtest.status == 'completed' else 'error'
            yield f"event: {event_type}\ndata: {json.dumps(backtest.to_dict())}\n\n"
            break

        await asyncio.sleep(0.5)

@router.get("/backtests/{backtest_id}/stream")
async def stream_backtest(backtest_id: str):
    return StreamingResponse(
        generate_events(backtest_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

## Verification Commands
```bash
# Typecheck
cd trading_lab && python -m mypy api/routes/backtests.py

# Test SSE endpoint (start a backtest first)
curl -N http://localhost:8847/api/backtests/{id}/stream

# Verify headers
curl -I http://localhost:8847/api/backtests/{id}/stream
# Should show: Content-Type: text/event-stream
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-sse-backend.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
