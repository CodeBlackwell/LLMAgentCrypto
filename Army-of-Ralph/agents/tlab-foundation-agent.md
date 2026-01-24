# tlab-foundation Agent

## Mission
Add progress tracking fields to the database schema, repository, and API schema to enable backtest progress monitoring.

## Wave
0 (Foundation - Must Complete First)

## Owned Paths (Exclusive Write)
- `trading_lab/storage/models.py`
- `trading_lab/storage/repository.py`
- `trading_lab/api/schemas.py`

## Shared Paths (Read Only)
- `trading_lab/api/routes/backtests.py`
- `trading_lab/backtest/engine.py`

## User Stories

### US-001: Add progress fields to database schema
**Description:** As a developer, I need to store backtest progress in the database so it can be queried and displayed.

**Acceptance Criteria:**
- [ ] Add to `BacktestRun` model in `trading_lab/storage/models.py`:
  - `progress_percent = Column(Float, nullable=True, default=0.0)`
  - `progress_message = Column(String(255), nullable=True)`
  - `current_date = Column(DateTime, nullable=True)`
  - `total_days = Column(Integer, nullable=True)`
  - `processed_days = Column(Integer, nullable=True, default=0)`
- [ ] Update `to_dict()` method to include all progress fields
- [ ] Ensure `error_message` is included in `to_dict()` output
- [ ] Application starts without errors
- [ ] Typecheck passes

---

### US-002: Add repository method for progress updates
**Description:** As a developer, I need a repository method to update backtest progress so the engine can persist progress state.

**Acceptance Criteria:**
- [ ] Add `update_progress()` method to `BacktestRepository` in `trading_lab/storage/repository.py`
- [ ] Method signature: `update_progress(self, backtest_id: str, progress_percent: float, progress_message: str = "", current_date: datetime = None, processed_days: int = None) -> Optional[BacktestRun]`
- [ ] Method updates only non-None fields
- [ ] Method returns updated BacktestRun or None if not found
- [ ] Typecheck passes

---

### US-003: Add progress fields to API schema
**Description:** As a developer, I need the API response schema to include progress fields so the frontend can display them.

**Acceptance Criteria:**
- [ ] Add to `BacktestResponse` in `trading_lab/api/schemas.py`:
  - `progress_percent: Optional[float] = None`
  - `progress_message: Optional[str] = None`
  - `current_date: Optional[str] = None`
  - `total_days: Optional[int] = None`
  - `processed_days: Optional[int] = None`
  - `error_message: Optional[str] = None`
- [ ] Verify GET `/backtests/{id}` returns progress fields
- [ ] Typecheck passes

## Verification Commands
```bash
# Typecheck
cd trading_lab && python -m mypy storage/models.py storage/repository.py api/schemas.py

# Application starts
cd trading_lab && python -c "from storage.models import BacktestRun; print('OK')"

# Test API response includes new fields
curl http://localhost:8847/api/backtests | python -m json.tool
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-foundation.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
