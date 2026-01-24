# tlab-validation Agent

## Mission
Add server-side validation for backtest creation to provide clear error messages for invalid parameters.

## Wave
1 (Backend Features - Parallel)

## Dependencies
- Wave 0 must be complete

## Owned Paths (Exclusive Write)
- `trading_lab/api/routes/backtests.py` (validation logic only - coordinate with sse-backend agent)

## Shared Paths (Read Only)
- `trading_lab/api/schemas.py`
- `trading_lab/backtest/strategies/registry.py`

## User Stories

### US-008: Add server-side validation for backtest creation
**Description:** As a user, I want clear error messages when I submit invalid backtest parameters.

**Acceptance Criteria:**
- [ ] Add validation in `POST /backtests` endpoint or schema:
  - Strategy must exist in registry
  - End date must be after start date
  - Date range must be <= 2 years (730 days)
  - Initial cash must be >= 100
  - Threshold must be between 0 and 1
  - Position size must be between 0 and 1
- [ ] Return 422 with descriptive error messages for each validation failure
- [ ] Typecheck passes

## Implementation Notes

Add validation either:
1. In the Pydantic schema with validators, OR
2. In the route handler before creating the backtest

Example validation error response:
```json
{
  "detail": [
    {
      "loc": ["body", "threshold"],
      "msg": "Threshold must be between 0 and 1",
      "type": "value_error"
    }
  ]
}
```

## Verification Commands
```bash
# Typecheck
cd trading_lab && python -m mypy api/routes/backtests.py

# Test invalid threshold
curl -X POST http://localhost:8847/api/backtests \
  -H "Content-Type: application/json" \
  -d '{"strategy": "momentum", "threshold": 1.5, ...}'
# Should return 422

# Test invalid date range
curl -X POST http://localhost:8847/api/backtests \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-01-01", "end_date": "2020-01-01", ...}'
# Should return 422
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-validation.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
