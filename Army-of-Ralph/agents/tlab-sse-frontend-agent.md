# tlab-sse-frontend Agent

## Mission
Create a React hook to consume the SSE stream for real-time backtest updates and integrate it with BacktestDetail.

## Wave
3 (Frontend - Parallel)

## Dependencies
- Wave 2 must be complete (SSE backend endpoint)

## Owned Paths (Exclusive Write)
- `trading_lab/web/src/hooks/useBacktestStream.js` (new file)

## Shared Paths (Read Only)
- `trading_lab/web/src/pages/BacktestDetail.jsx` (ui-feedback agent owns, but this agent provides integration code)

## User Stories

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

## Implementation Notes

### useBacktestStream Hook
```javascript
import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8847/api';

export function useBacktestStream(backtestId, enabled = true) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef(null);
  const retryCountRef = useRef(0);
  const retryTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!backtestId || !enabled) return;

    const url = `${API_BASE}/backtests/${backtestId}/stream`;
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      retryCountRef.current = 0;
    };

    eventSource.addEventListener('progress', (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(parsed);
      } catch (e) {
        console.error('Failed to parse progress event:', e);
      }
    });

    eventSource.addEventListener('complete', (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(parsed);
      } catch (e) {
        console.error('Failed to parse complete event:', e);
      }
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.addEventListener('error', (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(parsed);
        setError(parsed.error_message || 'Backtest failed');
      } catch (e) {
        // Connection error, not data error
      }
      eventSource.close();
      setIsConnected(false);
    });

    eventSource.onerror = () => {
      eventSource.close();
      setIsConnected(false);

      // Exponential backoff: 1s, 2s, 4s, 8s, ... max 30s
      const delay = Math.min(1000 * Math.pow(2, retryCountRef.current), 30000);
      retryCountRef.current++;

      retryTimeoutRef.current = setTimeout(() => {
        connect();
      }, delay);
    };
  }, [backtestId, enabled]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [connect]);

  return { data, error, isConnected };
}
```

### Integration in BacktestDetail.jsx
```jsx
import { useBacktestStream } from '../hooks/useBacktestStream';

// Inside component:
const isRunningOrPending = backtest?.status === 'running' || backtest?.status === 'pending';
const { data: streamData, isConnected } = useBacktestStream(
  backtestId,
  isRunningOrPending
);

// Merge stream data with query data
useEffect(() => {
  if (streamData) {
    queryClient.setQueryData(['backtest', backtestId], streamData);
  }
}, [streamData, backtestId, queryClient]);

// Adjust polling based on SSE connection
const refetchInterval = useMemo(() => {
  if (isConnected) return false; // SSE handles updates
  if (backtest?.status === 'running') return 500;
  if (backtest?.status === 'pending') return 1000;
  return false;
}, [backtest?.status, isConnected]);
```

### Connection Status Indicator
```jsx
{isRunningOrPending && (
  <div className="flex items-center gap-2 text-sm">
    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-yellow-500 animate-pulse'}`} />
    <span className="text-gray-600">
      {isConnected ? 'Live updates' : 'Reconnecting...'}
    </span>
  </div>
)}
```

## Verification Commands
```bash
# Check for TypeScript/ESLint errors
cd trading_lab/web && npm run lint

# Start dev server
cd trading_lab/web && npm run dev

# Visual verification:
# 1. Start a backtest
# 2. Verify green connection indicator appears
# 3. Verify progress updates without page refresh
# 4. Close/restart backend - verify yellow reconnecting indicator
# 5. Verify polling is disabled when SSE connected
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-sse-frontend.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
