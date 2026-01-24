# tlab-progress Agent

## Mission
Create a ProgressTracker module and integrate it into the backtest engine and runner to provide real-time progress updates during backtest execution.

## Wave
1 (Backend Features - Parallel)

## Dependencies
- Wave 0 must be complete (foundation agent provides schema and repository methods)

## Owned Paths (Exclusive Write)
- `trading_lab/backtest/progress.py` (new file)
- `trading_lab/backtest/engine.py`
- `trading_lab/backtest/runner.py`

## Shared Paths (Read Only)
- `trading_lab/storage/models.py`
- `trading_lab/storage/repository.py`

## User Stories

### US-004: Create ProgressTracker module
**Description:** As a developer, I need a ProgressTracker class to calculate and emit progress updates during backtest execution.

**Acceptance Criteria:**
- [ ] Create new file `trading_lab/backtest/progress.py`
- [ ] `ProgressTracker` class with:
  - `__init__(self, backtest_id: str, start_date: date, end_date: date, repository: BacktestRepository)`
  - `update(self, current_date: date, message: str = "") -> None` - calculates percent, calls repository
  - `set_phase(self, phase: str) -> None` - updates message without changing date
  - `complete(self) -> None` - sets progress to 100%
- [ ] Progress updates throttled to max once per 500ms to avoid DB thrashing
- [ ] Typecheck passes

---

### US-005: Integrate progress tracking into backtest engine
**Description:** As a developer, I need the backtest engine to report progress so users see real-time updates.

**Acceptance Criteria:**
- [ ] Modify `BacktestEngine.__init__()` in `trading_lab/backtest/engine.py` to accept optional `progress_tracker` parameter
- [ ] Calculate `total_days` from date range at start of run
- [ ] Call `progress_tracker.update()` during simulation loop with current date
- [ ] Call `progress_tracker.set_phase()` for stage transitions ("Fetching data...", "Simulating trades...")
- [ ] Typecheck passes

---

### US-006: Wire progress tracker into BacktestRunner
**Description:** As a developer, I need the runner to create and pass a ProgressTracker to the engine.

**Acceptance Criteria:**
- [ ] Modify `BacktestRunner._run_backtest()` in `trading_lab/backtest/runner.py`
- [ ] Create `ProgressTracker` instance before engine execution
- [ ] Pass tracker to `BacktestEngine`
- [ ] Update progress to 100% on successful completion
- [ ] Typecheck passes

## Verification Commands
```bash
# Typecheck
cd trading_lab && python -m mypy backtest/progress.py backtest/engine.py backtest/runner.py

# Import test
cd trading_lab && python -c "from backtest.progress import ProgressTracker; print('OK')"

# Run a backtest and verify progress updates in database
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-progress.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
