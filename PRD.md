# PRD: Trading Lab Usability Enhancement

## Introduction

Enhance the Trading Lab backtest execution experience to be more verbose, visual, and responsive. Users currently lack feedback during backtest execution, cannot see error messages for failed runs, and experience slow perceived performance due to polling-only updates. This PRD addresses these gaps through progress tracking, real-time streaming, improved form UX, and performance optimizations.

## Goals

- Display clear error messages when backtests fail
- Provide real-time progress feedback during backtest execution
- Reduce perceived latency through SSE streaming instead of polling
- Improve form UX with validation, tooltips, and date presets
- Show live trade feed during execution
- Increase throughput with larger worker pool and data caching

---

## User Stories

### US-001: Add progress fields to database schema
**Description:** As a developer, I need to store backtest progress in the database so it can be queried and displayed.

**Acceptance Criteria:**
- [x] Add to `BacktestRun` model in `trading_lab/storage/models.py`:
  - `progress_percent = Column(Float, nullable=True, default=0.0)`
  - `progress_message = Column(String(255), nullable=True)`
  - `current_date = Column(DateTime, nullable=True)`
  - `total_days = Column(Integer, nullable=True)`
  - `processed_days = Column(Integer, nullable=True, default=0)`
- [x] Update `to_dict()` method to include all progress fields
- [x] Ensure `error_message` is included in `to_dict()` output
- [x] Application starts without errors
- [x] Typecheck passes

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

---

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

---

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

---

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

---

### US-009: Increase worker pool and optimize runner
**Description:** As a user, I want backtests to run faster through parallel execution.

**Acceptance Criteria:**
- [ ] Change `max_workers=2` to `max_workers=4` in `trading_lab/backtest/runner.py`
- [ ] Typecheck passes

---

### US-010: Create data cache module
**Description:** As a developer, I need to cache historical price data to avoid redundant API calls.

**Acceptance Criteria:**
- [ ] Create new file `trading_lab/backtest/cache.py`
- [ ] `DataCache` class with:
  - `get(asset: str, exchange: str, start_date: date, end_date: date) -> Optional[DataFrame]`
  - `set(asset: str, exchange: str, start_date: date, end_date: date, data: DataFrame) -> None`
  - `clear() -> None`
- [ ] Use pickle files in `.backtest_cache/` directory
- [ ] Cache key based on asset, exchange, and date range
- [ ] Add `.backtest_cache/` to `.gitignore`
- [ ] Typecheck passes

---

### US-011: Display error banner for failed backtests
**Description:** As a user, I want to see why my backtest failed so I can fix the issue.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/BacktestDetail.jsx`, add error banner when `backtest.status === 'failed'`
- [ ] Banner has red background with error icon
- [ ] Display `backtest.error_message` in `<pre>` tag for formatting
- [ ] Banner appears prominently at top of results section
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-012: Add loading spinner for BacktestDetail
**Description:** As a user, I want visual feedback while the backtest details are loading.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/BacktestDetail.jsx`, replace "Loading backtest..." text
- [ ] Show centered spinner animation using Tailwind CSS
- [ ] Spinner visible until data loads
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-013: Add running state indicator with elapsed time
**Description:** As a user, I want to see that my backtest is running and how long it's been processing.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/BacktestDetail.jsx`, add blue banner when `isRunning`
- [ ] Include spinning loader animation
- [ ] Show "Processing historical data for {asset}..."
- [ ] Display elapsed time since `created_at` (updates every second)
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-014: Add progress bar display
**Description:** As a user, I want to see backtest progress as a percentage so I know how much longer to wait.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/BacktestDetail.jsx`, add progress bar when running
- [ ] Progress bar shows `progress_percent` with animated width transition
- [ ] Display percentage as large bold text
- [ ] Show "Day X/Y" using `processed_days` and `total_days`
- [ ] Show `progress_message` below progress bar
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-015: Create SSE hook for real-time updates
**Description:** As a developer, I need a React hook to consume the SSE stream for real-time backtest updates.

**Acceptance Criteria:**
- [ ] Create `trading_lab/web/src/hooks/useBacktestStream.js`
- [ ] Hook signature: `useBacktestStream(backtestId, enabled)`
- [ ] Returns `{ data, error, isConnected }`
- [ ] Uses native `EventSource` API
- [ ] Implements automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, max 30s)
- [ ] Cleans up connection on unmount or when disabled
- [ ] Typecheck passes

---

### US-016: Integrate SSE hook in BacktestDetail
**Description:** As a user, I want real-time updates without page refresh while my backtest runs.

**Acceptance Criteria:**
- [ ] Import and use `useBacktestStream` in `BacktestDetail.jsx`
- [ ] Enable stream only when status is `running` or `pending`
- [ ] Merge stream data with React Query cache
- [ ] Show connection status indicator (green dot = connected, yellow = reconnecting)
- [ ] Disable polling when SSE is connected
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-017: Add tooltips to form fields
**Description:** As a user, I want to understand what each backtest parameter means.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add tooltip icons next to form labels
- [ ] Tooltips for:
  - Threshold: "Minimum confidence score (0-1) required to execute a trade"
  - Position Size: "Fraction of available cash to use per trade (0.25 = 25%)"
  - Initial Cash: "Starting capital for the backtest simulation"
- [ ] Tooltip appears on hover with dark background
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-018: Add client-side form validation
**Description:** As a user, I want immediate feedback when I enter invalid values before submitting.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add `validationErrors` state
- [ ] Validate on blur and on submit:
  - Strategy is selected
  - End date > Start date
  - Date range <= 2 years
  - Initial cash >= $100
  - Threshold between 0 and 1
  - Position size between 0 and 1
- [ ] Show inline error messages below invalid fields (red text)
- [ ] Disable submit button when any validation fails
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-019: Add estimated duration display
**Description:** As a user, I want to know approximately how long my backtest will take before I start it.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, add duration estimate section
- [ ] Calculate based on date range (~2 seconds per trading day)
- [ ] Display: "Estimated duration: Xm Ys (N trading days)"
- [ ] Updates dynamically as dates change
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-020: Add date picker presets
**Description:** As a user, I want quick preset buttons for common date ranges.

**Acceptance Criteria:**
- [ ] In `trading_lab/web/src/pages/NewBacktest.jsx`, change date inputs to `type="date"`
- [ ] Add preset buttons: "Last 3 months", "Last 6 months", "YTD", "Last year"
- [ ] Clicking preset populates both start and end date fields
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-021: Create LiveTradeFeed component
**Description:** As a user, I want to see trades happening in real-time during backtest execution.

**Acceptance Criteria:**
- [ ] Create `trading_lab/web/src/components/LiveTradeFeed.jsx`
- [ ] Dark terminal-style design (gray-900 background, monospace font)
- [ ] Show last 10 trades with auto-scroll to bottom
- [ ] Color-coded: green text for BUY, red for SELL
- [ ] Display: side, quantity, price, timestamp
- [ ] Show "Waiting for trades..." when empty
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-022: Integrate LiveTradeFeed in BacktestDetail
**Description:** As a user, I want to see the live trade feed while my backtest is running.

**Acceptance Criteria:**
- [ ] Import `LiveTradeFeed` in `BacktestDetail.jsx`
- [ ] Show component only when `isRunning` is true
- [ ] Pass trades from SSE stream to component
- [ ] Position below progress bar
- [ ] Hide when backtest completes
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

### US-023: Optimize polling intervals
**Description:** As a user, I want faster updates when my backtest is running.

**Acceptance Criteria:**
- [ ] In `BacktestDetail.jsx`, update `refetchInterval` logic:
  - `running`: 500ms (reduced from 2000ms)
  - `pending`: 1000ms
  - terminal states: `false` (no polling)
- [ ] Polling disabled when SSE is connected
- [ ] Typecheck passes
- [ ] Verify changes work in browser

---

## Non-Goals

- No WebSocket implementation (SSE is simpler and sufficient)
- No priority queue for backtests
- No cancellation of running backtests
- No persistence of SSE connection across page reloads
- No mobile-specific UI optimizations
- No internationalization of error messages
- No historical progress data storage (only current run)

## Technical Considerations

- SQLite supports the required column types; no migration tool needed for dev
- SSE is natively supported by browsers via `EventSource` API
- React Query cache can be manually updated via `queryClient.setQueryData()`
- Tailwind CSS already configured with animation utilities
- Lumibot may not expose per-day callbacks; may need to poll internal state
- ThreadPoolExecutor max_workers=4 is reasonable for most systems; make configurable via env var if needed
