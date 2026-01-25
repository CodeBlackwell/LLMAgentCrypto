#!/bin/bash
set -e

MAX=${1:-10}
SLEEP=${2:-2}

# Timing tracking
START_TIME=$(date +%s)
TIMING_LOG="ralph_timing.log"

# Helper function to format duration as HH:MM:SS
format_duration() {
    local seconds=$1
    local hours=$((seconds / 3600))
    local minutes=$(((seconds % 3600) / 60))
    local secs=$((seconds % 60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

# Initialize timing log
echo "Ralph Timing Log - Started $(date)" > "$TIMING_LOG"
echo "Max Iterations: $MAX" >> "$TIMING_LOG"
echo "---" >> "$TIMING_LOG"

echo "Starting Ralph - Max $MAX iterations"
echo "Timing log: $TIMING_LOG"
echo ""

for ((i=1; i<=$MAX; i++)); do
    echo "==========================================="
    echo "  Iteration $i of $MAX"
    echo "==========================================="

    # Start iteration timer
    ITER_START=$(date +%s)

    result=$(claude --dangerously-skip-permissions -p "You are Ralph, an autonomous coding agent. Do exactly ONE task per iteration.

## Steps

1. Read PRD.md and find the first task that is NOT complete (marked [ ]).
2. Read progress.txt - check the Learnings section first for patterns from previous iterations.
3. Implement that ONE task only.
4. Run tests/typecheck to verify it works.

## Critical: Only Complete If Tests Pass

- If tests PASS:
  - Update PRD.md to mark the task complete (change [ ] to [x])
  - Commit your changes with message: feat: [task description]
  - Append what worked to progress.txt

- If tests FAIL:
  - Do NOT mark the task complete
  - Do NOT commit broken code
  - Append what went wrong to progress.txt (so next iteration can learn)

## Progress Notes Format

Append to progress.txt using this format:

## Iteration [N] - [Task Name]
- What was implemented
- Files changed
- Learnings for future iterations:
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---

## Update AGENTS.md (If Applicable)

If you discover a reusable pattern that future work should know about:
- Check if AGENTS.md exists in the project root
- Add patterns like: 'This codebase uses X for Y' or 'Always do Z when changing W'
- Only add genuinely reusable knowledge, not task-specific details

## End Condition

After completing your task, check PRD.md:
- If ALL tasks are [x], output exactly: <promise>COMPLETE</promise>
- If tasks remain [ ], just end your response (next iteration will continue)")

    echo "$result"

    # End iteration timer and calculate durations
    ITER_END=$(date +%s)
    ITER_DURATION=$((ITER_END - ITER_START))
    TOTAL_ELAPSED=$((ITER_END - START_TIME))

    # Log to file
    echo "Iteration $i: $(format_duration $ITER_DURATION) | Total: $(format_duration $TOTAL_ELAPSED)" >> "$TIMING_LOG"

    # Real-time status line (updates in place)
    echo ""
    printf "⏱  Iter %d: %s | Total: %s | Avg: %s/iter\n" \
        "$i" \
        "$(format_duration $ITER_DURATION)" \
        "$(format_duration $TOTAL_ELAPSED)" \
        "$(format_duration $((TOTAL_ELAPSED / i)))"
    echo ""

    if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
        echo "==========================================="
        echo "  All tasks complete after $i iterations!"
        echo "==========================================="
        echo ""
        echo "==========================================="
        echo "  Timing Summary"
        echo "==========================================="
        echo "  Total Time: $(format_duration $TOTAL_ELAPSED)"
        echo "  Iterations: $i"
        echo "  Avg/Iter:   $(format_duration $((TOTAL_ELAPSED / i)))"
        echo "==========================================="

        # Append summary to log
        echo "---" >> "$TIMING_LOG"
        echo "SUMMARY (COMPLETED)" >> "$TIMING_LOG"
        echo "Total Time: $(format_duration $TOTAL_ELAPSED)" >> "$TIMING_LOG"
        echo "Iterations Completed: $i" >> "$TIMING_LOG"
        echo "Average per Iteration: $(format_duration $((TOTAL_ELAPSED / i)))" >> "$TIMING_LOG"

        exit 0
    fi

    sleep $SLEEP
done

# Calculate final elapsed time
FINAL_ELAPSED=$(($(date +%s) - START_TIME))

echo "==========================================="
echo "  Reached max iterations ($MAX)"
echo "==========================================="
echo ""
echo "==========================================="
echo "  Timing Summary"
echo "==========================================="
echo "  Total Time: $(format_duration $FINAL_ELAPSED)"
echo "  Iterations: $MAX"
echo "  Avg/Iter:   $(format_duration $((FINAL_ELAPSED / MAX)))"
echo "==========================================="

# Append summary to log
echo "---" >> "$TIMING_LOG"
echo "SUMMARY (MAX ITERATIONS)" >> "$TIMING_LOG"
echo "Total Time: $(format_duration $FINAL_ELAPSED)" >> "$TIMING_LOG"
echo "Iterations Completed: $MAX" >> "$TIMING_LOG"
echo "Average per Iteration: $(format_duration $((FINAL_ELAPSED / MAX)))" >> "$TIMING_LOG"

exit 1
