# tlab-ui-feedback Agent

## Mission
Enhance the BacktestDetail page with error banners, loading spinners, running state indicators, and progress bar display.

## Wave
3 (Frontend - Parallel)

## Dependencies
- Wave 2 must be complete (SSE backend)

## Owned Paths (Exclusive Write)
- `trading_lab/web/src/pages/BacktestDetail.jsx` (error, spinner, running state, progress - coordinate with sse-frontend agent)

## Shared Paths (Read Only)
- `trading_lab/api/schemas.py`
- `trading_lab/web/src/hooks/useBacktestStream.js` (after sse-frontend creates it)

## User Stories

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

## Implementation Notes

### Error Banner Component
```jsx
{backtest.status === 'failed' && (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
    <div className="flex items-center gap-2 text-red-800 font-medium mb-2">
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
      Backtest Failed
    </div>
    <pre className="text-red-700 text-sm whitespace-pre-wrap">{backtest.error_message}</pre>
  </div>
)}
```

### Loading Spinner
```jsx
{isLoading && (
  <div className="flex justify-center items-center py-12">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
)}
```

### Progress Bar
```jsx
{isRunning && (
  <div className="mb-6">
    <div className="flex justify-between items-center mb-2">
      <span className="text-2xl font-bold">{Math.round(backtest.progress_percent || 0)}%</span>
      <span className="text-gray-600">Day {backtest.processed_days || 0}/{backtest.total_days || '?'}</span>
    </div>
    <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-600 transition-all duration-300 ease-out"
        style={{ width: `${backtest.progress_percent || 0}%` }}
      />
    </div>
    <p className="text-gray-600 mt-2">{backtest.progress_message || 'Starting...'}</p>
  </div>
)}
```

### Elapsed Time Hook
```jsx
const [elapsed, setElapsed] = useState(0);

useEffect(() => {
  if (!isRunning || !backtest?.created_at) return;

  const interval = setInterval(() => {
    const start = new Date(backtest.created_at);
    const now = new Date();
    setElapsed(Math.floor((now - start) / 1000));
  }, 1000);

  return () => clearInterval(interval);
}, [isRunning, backtest?.created_at]);

const formatElapsed = (seconds) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
};
```

## Verification Commands
```bash
# Start dev server
cd trading_lab/web && npm run dev

# Check for TypeScript/ESLint errors
cd trading_lab/web && npm run lint

# Visual verification in browser at http://localhost:3847
# 1. Create a backtest and verify loading spinner
# 2. Watch running state with progress bar
# 3. Trigger a failure and verify error banner
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-ui-feedback.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
