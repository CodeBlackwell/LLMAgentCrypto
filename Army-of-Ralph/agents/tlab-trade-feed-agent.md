# tlab-trade-feed Agent

## Mission
Create a LiveTradeFeed component to display trades in real-time during backtest execution.

## Wave
3 (Frontend - Parallel)

## Dependencies
- Wave 2 must be complete (SSE backend for trades stream)

## Owned Paths (Exclusive Write)
- `trading_lab/web/src/components/LiveTradeFeed.jsx` (new file)

## Shared Paths (Read Only)
- `trading_lab/web/src/pages/BacktestDetail.jsx` (to see integration pattern)
- `trading_lab/web/src/hooks/useBacktestStream.js`

## User Stories

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

## Implementation Notes

### LiveTradeFeed Component
```jsx
import { useEffect, useRef } from 'react';

export function LiveTradeFeed({ trades = [] }) {
  const containerRef = useRef(null);

  // Auto-scroll to bottom when new trades arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [trades]);

  // Show only last 10 trades
  const recentTrades = trades.slice(-10);

  return (
    <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
      <div className="flex items-center gap-2 mb-3 text-gray-400">
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
        Live Trade Feed
      </div>

      <div
        ref={containerRef}
        className="h-48 overflow-y-auto space-y-1"
      >
        {recentTrades.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            Waiting for trades...
          </div>
        ) : (
          recentTrades.map((trade, index) => (
            <TradeRow key={index} trade={trade} />
          ))
        )}
      </div>
    </div>
  );
}

function TradeRow({ trade }) {
  const isBuy = trade.side === 'BUY';
  const colorClass = isBuy ? 'text-green-400' : 'text-red-400';
  const timestamp = new Date(trade.timestamp).toLocaleTimeString();

  return (
    <div className={`flex items-center justify-between ${colorClass}`}>
      <div className="flex items-center gap-3">
        <span className={`w-12 font-bold ${colorClass}`}>
          {trade.side}
        </span>
        <span className="text-gray-300">
          {trade.quantity.toFixed(4)}
        </span>
        <span className="text-gray-500">@</span>
        <span className="text-gray-300">
          ${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      </div>
      <span className="text-gray-500 text-xs">
        {timestamp}
      </span>
    </div>
  );
}
```

### Integration in BacktestDetail.jsx
```jsx
import { LiveTradeFeed } from '../components/LiveTradeFeed';

// Inside component, after progress bar:
{isRunning && (
  <div className="mt-6">
    <LiveTradeFeed trades={streamData?.recent_trades || []} />
  </div>
)}
```

### Expected Trade Data Structure
```javascript
{
  side: 'BUY' | 'SELL',
  quantity: 0.5,
  price: 45000.00,
  timestamp: '2024-01-15T10:30:00Z'
}
```

### SSE Trades Event Format
The SSE backend should emit trades in this format:
```
event: trades
data: {"trades": [{"side": "BUY", "quantity": 0.5, "price": 45000, "timestamp": "2024-01-15T10:30:00"}]}
```

## Verification Commands
```bash
# Check for TypeScript/ESLint errors
cd trading_lab/web && npm run lint

# Start dev server
cd trading_lab/web && npm run dev

# Visual verification:
# 1. Start a backtest
# 2. Verify LiveTradeFeed appears with dark terminal style
# 3. Watch for trades to appear in real-time
# 4. Verify BUY trades are green, SELL trades are red
# 5. Verify auto-scroll as new trades arrive
# 6. Verify component hides when backtest completes
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-trade-feed.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
