# tlab-performance Agent

## Mission
Increase backtest throughput by expanding the worker pool and implementing data caching to avoid redundant API calls.

## Wave
1 (Backend Features - Parallel)

## Dependencies
- Wave 0 must be complete

## Owned Paths (Exclusive Write)
- `trading_lab/backtest/cache.py` (new file)
- `.gitignore` (add cache directory)

## Shared Paths (Read Only)
- `trading_lab/backtest/runner.py` (performance agent can modify max_workers)
- `trading_lab/backtest/engine.py`

## User Stories

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

## Implementation Notes

### Cache Key Format
```python
def _cache_key(asset: str, exchange: str, start_date: date, end_date: date) -> str:
    return f"{asset}_{exchange}_{start_date.isoformat()}_{end_date.isoformat()}"
```

### Cache Directory Structure
```
.backtest_cache/
├── BTC_binance_2024-01-01_2024-06-01.pkl
├── ETH_binance_2024-01-01_2024-03-01.pkl
└── ...
```

### DataCache Class Skeleton
```python
import os
import pickle
from datetime import date
from pathlib import Path
from typing import Optional
import pandas as pd

class DataCache:
    def __init__(self, cache_dir: str = ".backtest_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, asset: str, exchange: str, start_date: date, end_date: date) -> Optional[pd.DataFrame]:
        # Implementation here
        pass

    def set(self, asset: str, exchange: str, start_date: date, end_date: date, data: pd.DataFrame) -> None:
        # Implementation here
        pass

    def clear(self) -> None:
        # Implementation here
        pass
```

## Verification Commands
```bash
# Typecheck
cd trading_lab && python -m mypy backtest/cache.py

# Import test
cd trading_lab && python -c "from backtest.cache import DataCache; print('OK')"

# Check .gitignore
grep -q ".backtest_cache" .gitignore && echo "OK" || echo "Missing from .gitignore"
```

## Completion Signal
When all checkboxes are complete, update progress file at:
`Army-of-Ralph/progress/progress-tlab-performance.txt`

Mark all tasks complete and add at the end:
```
<promise>COMPLETE</promise>
```
