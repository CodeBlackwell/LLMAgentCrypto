# Trading Lab Usability Enhancement - Pre-PRD

## Overview
Make the backtest execution process **more verbose**, **more visual**, and **faster** (or at least feel faster with proper feedback).

---

## Phase 1: Quick Wins - Error Display & Loading States

### 1.1 Display Error Messages for Failed Backtests
- [ ] **`trading_lab/api/schemas.py`** (~line 46-65)
  - Add `error_message: Optional[str] = None` to `BacktestResponse`

- [ ] **`trading_lab/storage/models.py`** (~line 93-114)
  - Ensure `to_dict()` includes `"error_message": self.error_message`

- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`** (~line 139)
  - Add error banner component when `backtest.status === 'failed'`
  - Show red alert box with error message and icon
  - Use `<pre>` tag for formatted error display

### 1.2 Skeleton Loading States
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`** (lines 73-75)
  - Replace "Loading backtest..." with animated skeleton UI
  - Add skeleton for header, metrics grid (8 cards), and chart area
  - Use Tailwind `animate-pulse` with gray placeholders

### 1.3 Enhanced Running State Indicator
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`**
  - Add prominent blue banner when `isRunning` is true
  - Include spinning loader animation (CSS border spinner)
  - Show "Processing historical data for {asset}..."
  - Display elapsed time since `created_at`

---

## Phase 2: Progress Tracking System

### 2.1 Database Schema Extension
- [ ] **`trading_lab/storage/models.py`** - Add to `BacktestRun`:
  ```python
  progress_percent = Column(Float, nullable=True, default=0.0)
  progress_message = Column(String(255), nullable=True)
  current_date = Column(DateTime, nullable=True)
  total_days = Column(Integer, nullable=True)
  processed_days = Column(Integer, nullable=True, default=0)
  ```
- [ ] Update `to_dict()` to include all progress fields

### 2.2 Repository Progress Methods
- [ ] **`trading_lab/storage/repository.py`** - Add to `BacktestRepository`:
  ```python
  def update_progress(self, backtest_id, progress_percent,
                      progress_message="", current_date=None,
                      processed_days=None) -> Optional[BacktestRun]
  ```

### 2.3 Progress Callback in Engine
- [ ] **`trading_lab/backtest/engine.py`**
  - Add `progress_callback` parameter to `__init__`
  - Calculate total_days from date range at start
  - Call callback with progress updates during simulation

### 2.4 Create Progress Tracker Module
- [ ] **`trading_lab/backtest/progress.py`** (new file)
  - `ProgressTracker` class with:
    - `__init__(backtest_id, start_date, end_date, callback)`
    - `update(current_date, message)` - calculate % and notify
    - `set_phase(phase)` - for stage transitions

### 2.5 API Schema Updates
- [ ] **`trading_lab/api/schemas.py`** - Add to `BacktestResponse`:
  ```python
  progress_percent: Optional[float] = None
  progress_message: Optional[str] = None
  current_date: Optional[str] = None
  total_days: Optional[int] = None
  processed_days: Optional[int] = None
  ```

### 2.6 Frontend Progress Display
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`**
  - Add progress bar (blue, animated width transition)
  - Show percentage in large bold text
  - Display "Day X/Y" and current simulation date
  - Show phase messages ("Loading data...", "Simulating trades...")

---

## Phase 3: Real-Time Updates via Server-Sent Events (SSE)

### 3.1 SSE Streaming Endpoint
- [ ] **`trading_lab/api/routes/backtests.py`**
  - Add `GET /{backtest_id}/stream` endpoint
  - Return `StreamingResponse` with `text/event-stream`
  - Event types: `progress`, `trades`, `complete`, `error`
  - Poll database every 500ms, emit on changes only
  - Auto-close when status is terminal

### 3.2 Frontend SSE Hook
- [ ] **`trading_lab/web/src/hooks/useBacktestStream.js`** (new file)
  ```javascript
  export function useBacktestStream(backtestId, enabled) {
    // Returns { data, error, isConnected }
    // Uses EventSource API
    // Handles reconnection automatically
  }
  ```

### 3.3 Integrate SSE in BacktestDetail
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`**
  - Import and use `useBacktestStream` hook
  - Enable only when status is `running` or `pending`
  - Merge stream data with React Query data
  - Show connection status indicator

---

## Phase 4: Form UX Improvements

### 4.1 Add Tooltips to Form Fields
- [ ] **`trading_lab/web/src/pages/NewBacktest.jsx`**
  - Create `FormField` component with tooltip support
  - Add tooltips for:
    - **Threshold**: "Minimum confidence score (0-1) required to execute a trade"
    - **Position Size**: "Fraction of available cash to use per trade (0.25 = 25%)"
    - **Initial Cash**: "Starting capital for the backtest simulation"

### 4.2 Form Validation with Feedback
- [ ] **`trading_lab/web/src/pages/NewBacktest.jsx`**
  - Add `validationErrors` state
  - Validate:
    - Strategy is selected
    - End date > Start date
    - Date range <= 2 years
    - Initial cash >= $100
  - Show inline error messages below fields
  - Disable submit button when invalid

### 4.3 Estimated Duration Display
- [ ] **`trading_lab/web/src/pages/NewBacktest.jsx`**
  - Add `EstimatedDuration` component
  - Calculate based on date range (~2 sec/day estimate)
  - Show "Estimated duration: Xm Ys (N trading days)"

### 4.4 Date Picker Enhancement
- [ ] **`trading_lab/web/src/pages/NewBacktest.jsx`**
  - Change date inputs from text to `type="date"`
  - Add preset buttons: "Last 3 months", "Last 6 months", "YTD", "Last year"

---

## Phase 5: Live Trade Feed During Execution

### 5.1 Extend SSE to Stream Trades
- [ ] **`trading_lab/api/routes/backtests.py`** (update stream endpoint)
  - Track last seen trade count
  - Query new trades since last check
  - Emit `trades` event with new trade data

### 5.2 Live Trade Feed Component
- [ ] **`trading_lab/web/src/components/LiveTradeFeed.jsx`** (new file)
  - Dark terminal-style design (gray-900 background)
  - Show last 10 trades with auto-scroll
  - Color-coded: green for BUY, red for SELL
  - Display: side, quantity, price, timestamp
  - "Waiting for trades..." placeholder

### 5.3 Integrate Trade Feed in Detail Page
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`**
  - Show `LiveTradeFeed` when `isRunning`
  - Pass streamed trades to component
  - Position below progress bar

---

## Phase 6: Performance Optimizations

### 6.1 Increase Worker Pool
- [ ] **`trading_lab/backtest/runner.py`**
  - Change `max_workers=2` to `max_workers=4`

### 6.2 Faster Polling for Running Backtests
- [ ] **`trading_lab/web/src/pages/BacktestDetail.jsx`**
  - Change `refetchInterval`:
    - `running`: 500ms (was 2000ms)
    - `pending`: 1000ms
    - terminal: false (no polling)

### 6.3 Data Caching (Optional)
- [ ] **`trading_lab/backtest/cache.py`** (new file)
  - Cache historical price data by asset/exchange/date range
  - Use pickle files in `.backtest_cache/` directory
  - Check cache before fetching from exchange

---

## File Summary

| File | Changes |
|------|---------|
| `trading_lab/storage/models.py` | Add progress fields, expose error_message |
| `trading_lab/storage/repository.py` | Add `update_progress()` method |
| `trading_lab/api/schemas.py` | Add progress + error fields to response |
| `trading_lab/api/routes/backtests.py` | Add SSE streaming endpoint |
| `trading_lab/backtest/engine.py` | Add progress callback support |
| `trading_lab/backtest/runner.py` | Increase workers, integrate progress |
| `trading_lab/backtest/progress.py` | New - ProgressTracker class |
| `web/src/pages/BacktestDetail.jsx` | Major - skeleton, progress, errors, trades |
| `web/src/pages/NewBacktest.jsx` | Tooltips, validation, date pickers |
| `web/src/hooks/useBacktestStream.js` | New - SSE hook |
| `web/src/components/LiveTradeFeed.jsx` | New - trade feed component |

---

## Verification Plan

1. **Phase 1 Testing**:
   - Trigger a failed backtest (invalid asset like "XXX/YYY")
   - Verify error message displays in red banner
   - Check skeleton loading appears on refresh

2. **Phase 2 Testing**:
   - Run a 6-month backtest
   - Verify progress bar updates every 500ms
   - Check percentage and day counter increment

3. **Phase 3 Testing**:
   - Open browser DevTools Network tab
   - Run backtest, verify SSE connection opens
   - Check events stream with progress updates

4. **Phase 4 Testing**:
   - Hover over form fields, verify tooltips appear
   - Submit with invalid dates, check error messages
   - Use date presets, verify values populate

5. **Phase 5 Testing**:
   - Run backtest on RSI strategy (generates trades)
   - Verify trades appear in live feed during execution
   - Check color coding (green/red) is correct

6. **E2E Test**:
   ```bash
   cd trading_lab/web && npm run test:e2e
   ```

---

## Implementation Order

Start with **Phase 1** (immediate user feedback improvements), then proceed sequentially. Phases 4 and 6 can be done in parallel with Phase 3 or 5 as they are independent.

---

## Usability Gaps Identified

| Issue | Severity | Phase |
|-------|----------|-------|
| No progress indicator during execution | Critical | 2, 3 |
| No error messages for failed backtests | Critical | 1 |
| No real-time updates (2s polling only) | High | 3 |
| No trade history during execution | High | 5 |
| Form fields lack tooltips/explanations | Medium | 4 |
| No skeleton loading states | Medium | 1 |
| Slow perceived performance | Medium | 6 |
| No date picker presets | Low | 4 |
