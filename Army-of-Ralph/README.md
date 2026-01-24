# Army-of-Ralph: Trading Lab Usability Enhancement

Multi-agent orchestration system for implementing Trading Lab usability improvements. Agents work in waves based on dependencies, with exclusive file ownership and progress tracking.

## Quick Start

```bash
# 1. Make scripts executable
chmod +x orchestrator.sh tlab-agent.sh

# 2. Dry run to see what will execute
./orchestrator.sh --dry-run

# 3. Run single agent (for testing)
./tlab-agent.sh foundation

# 4. Run full orchestration
./orchestrator.sh
```

## Wave Architecture

```
Wave 0: Foundation (Sequential)
    └── tlab-foundation ──┐
                          │
Wave 1: Backend Features (Parallel)
    ├── tlab-progress ────┤
    ├── tlab-validation ──┤
    └── tlab-performance ─┤
                          │
Wave 2: SSE Backend       │
    └── tlab-sse-backend ─┤
                          │
Wave 3: Frontend (Parallel)
    ├── tlab-ui-feedback ─┤
    ├── tlab-sse-frontend ┤
    ├── tlab-form-ux ─────┤
    └── tlab-trade-feed ──┘
```

## Agents

| Wave | Agent | User Stories | Owned Files |
|------|-------|--------------|-------------|
| 0 | foundation | US-001, US-002, US-003 | `storage/models.py`, `storage/repository.py`, `api/schemas.py` |
| 1 | progress | US-004, US-005, US-006 | `backtest/progress.py`, `backtest/engine.py`, `backtest/runner.py` |
| 1 | validation | US-008 | `api/routes/backtests.py` (validation) |
| 1 | performance | US-009, US-010 | `backtest/cache.py`, `.gitignore` |
| 2 | sse-backend | US-007 | `api/routes/backtests.py` (SSE endpoint) |
| 3 | ui-feedback | US-011-014 | `web/src/pages/BacktestDetail.jsx` |
| 3 | sse-frontend | US-015, US-016, US-023 | `web/src/hooks/useBacktestStream.js` |
| 3 | form-ux | US-017-020 | `web/src/pages/NewBacktest.jsx` |
| 3 | trade-feed | US-021, US-022 | `web/src/components/LiveTradeFeed.jsx` |

## Git Branch Strategy

Each agent works on its own branch:

```
main
├── wave-0/tlab-foundation-agent
├── wave-1/tlab-progress-agent
├── wave-1/tlab-validation-agent
├── wave-1/tlab-performance-agent
├── wave-2/tlab-sse-backend-agent
├── wave-3/tlab-ui-feedback-agent
├── wave-3/tlab-sse-frontend-agent
├── wave-3/tlab-form-ux-agent
└── wave-3/tlab-trade-feed-agent
```

Each wave merges to main before the next wave starts.

## Monitoring

### Check Status
```bash
./orchestrator.sh --status
```

### View Agent Logs
```bash
tail -f logs/tlab-foundation-agent.log
```

### View Orchestrator Log
```bash
tail -f logs/orchestrator.log
```

### Attach to Agent Session
```bash
tmux attach-session -t tlab-foundation
```

### List All Sessions
```bash
tmux list-sessions
```

## Progress Tracking

Each agent updates its progress file in `progress/`:

```
progress/
├── progress-tlab-foundation.txt
├── progress-tlab-progress.txt
├── progress-tlab-validation.txt
├── progress-tlab-performance.txt
├── progress-tlab-sse-backend.txt
├── progress-tlab-ui-feedback.txt
├── progress-tlab-sse-frontend.txt
├── progress-tlab-form-ux.txt
└── progress-tlab-trade-feed.txt
```

Completion is signaled by adding `<promise>COMPLETE</promise>` to the progress file.

## Troubleshooting

### Agent not starting
1. Check if agent spec exists: `ls agents/tlab-*-agent.md`
2. Check for tmux session: `tmux list-sessions`
3. Check log file: `cat logs/tlab-<name>-agent.log`

### Wave stuck
1. Check which agents haven't completed: `./orchestrator.sh --status`
2. Check individual progress files: `cat progress/progress-tlab-<name>.txt`
3. Attach to stuck agent: `tmux attach-session -t tlab-<name>`

### Merge conflicts
1. The orchestrator will stop if merge conflicts occur
2. Resolve manually: `git checkout main && git merge wave-N/tlab-<name>-agent`
3. Resume: `./orchestrator.sh --wave N`

### Restart from specific wave
```bash
./orchestrator.sh --wave 2  # Start from Wave 2
```

## Directory Structure

```
Army-of-Ralph/
├── agents/                    # Agent specifications
│   ├── tlab-foundation-agent.md
│   ├── tlab-progress-agent.md
│   ├── tlab-validation-agent.md
│   ├── tlab-performance-agent.md
│   ├── tlab-sse-backend-agent.md
│   ├── tlab-ui-feedback-agent.md
│   ├── tlab-sse-frontend-agent.md
│   ├── tlab-form-ux-agent.md
│   └── tlab-trade-feed-agent.md
├── progress/                  # Agent progress tracking
│   └── progress-tlab-*.txt
├── logs/                      # Execution logs
│   ├── orchestrator.log
│   └── tlab-*-agent.log
├── orchestrator.sh            # Main orchestrator script
├── tlab-agent.sh              # Single agent launcher
└── README.md                  # This file
```
