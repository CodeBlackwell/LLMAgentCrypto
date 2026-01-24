#!/bin/bash
# Army-of-Ralph Orchestrator
# Manages wave execution for Trading Lab usability improvements
# Compatible with Bash 3 (macOS default)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PROGRESS_DIR="$SCRIPT_DIR/progress"
POLL_INTERVAL=30
TIMING_FILE="$LOG_DIR/timing.txt"
ORCHESTRATOR_START=""

# Wave definitions
WAVE_0_AGENTS="foundation"
WAVE_1_AGENTS="progress validation performance"
WAVE_2_AGENTS="sse-backend"
WAVE_3_AGENTS="ui-feedback sse-frontend form-ux trade-feed"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1" | tee -a "$LOG_DIR/orchestrator.log"
}

check_agent_complete() {
    local agent_name=$1
    local progress_file="$PROGRESS_DIR/progress-tlab-${agent_name}.txt"

    if [[ -f "$progress_file" ]]; then
        if grep -q "<promise>COMPLETE</promise>" "$progress_file" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Progress tracking functions
count_tasks() {
    local file=$1
    local total=0
    local done=0
    if [[ -f "$file" ]]; then
        total=$(grep -c '^[[:space:]]*- \[' "$file" 2>/dev/null) || total=0
        done=$(grep -c '^[[:space:]]*- \[x\]' "$file" 2>/dev/null) || done=0
    fi
    # Ensure clean output without newlines
    printf "%d/%d" "$done" "$total"
}

get_progress_percent() {
    local file=$1
    local total=0
    local done=0
    if [[ -f "$file" ]]; then
        total=$(grep -c '^[[:space:]]*- \[' "$file" 2>/dev/null) || total=0
        done=$(grep -c '^[[:space:]]*- \[x\]' "$file" 2>/dev/null) || done=0
    fi
    if [[ "$total" -eq 0 ]] || [[ -z "$total" ]]; then
        echo 0
    else
        echo $((done * 100 / total))
    fi
}

get_current_task() {
    local file=$1
    # Get first unchecked item as current task
    local task=$(grep '^\s*- \[ \]' "$file" 2>/dev/null | head -1 | sed 's/.*\] //' | cut -c1-40)
    if [[ -n "$task" ]]; then
        echo "$task"
    else
        echo "-"
    fi
}

# Timing functions
record_timing() {
    local agent=$1
    local event=$2  # start or end
    mkdir -p "$LOG_DIR"
    echo "${agent}:${event}:$(date +%s)" >> "$TIMING_FILE"
}

get_elapsed() {
    local agent=$1
    if [[ ! -f "$TIMING_FILE" ]]; then
        echo "waiting"
        return
    fi
    local start=$(grep "^${agent}:start:" "$TIMING_FILE" 2>/dev/null | tail -1 | cut -d: -f3)
    if [[ -n "$start" ]]; then
        local now=$(date +%s)
        local elapsed=$((now - start))
        printf "%dm %ds" $((elapsed/60)) $((elapsed%60))
    else
        echo "waiting"
    fi
}

get_total_elapsed() {
    if [[ -n "$ORCHESTRATOR_START" ]]; then
        local now=$(date +%s)
        local elapsed=$((now - ORCHESTRATOR_START))
        printf "%dm %ds" $((elapsed/60)) $((elapsed%60))
    else
        echo "0m 0s"
    fi
}

get_wave_name() {
    local wave=$1
    case $wave in
        0) echo "Foundation" ;;
        1) echo "Backend Features" ;;
        2) echo "SSE Backend" ;;
        3) echo "Frontend" ;;
    esac
}

get_wave_agents() {
    local wave_num=$1
    case $wave_num in
        0) echo "$WAVE_0_AGENTS" ;;
        1) echo "$WAVE_1_AGENTS" ;;
        2) echo "$WAVE_2_AGENTS" ;;
        3) echo "$WAVE_3_AGENTS" ;;
    esac
}

launch_agent() {
    local agent_name=$1
    local wave_num=$2
    local session_name="tlab-${agent_name}"

    log "${BLUE}Launching agent: $agent_name (Wave $wave_num)${NC}"

    # Record timing
    record_timing "$agent_name" "start"

    # Check if tmux is available
    if ! command -v tmux &> /dev/null; then
        log "${YELLOW}tmux not available, running agent directly...${NC}"
        "$SCRIPT_DIR/tlab-agent.sh" "$agent_name" "$wave_num" 2>&1 | tee "$LOG_DIR/tlab-${agent_name}-agent.log" &
        log "${GREEN}Agent $agent_name launched in background${NC}"
        return
    fi

    if tmux has-session -t "$session_name" 2>/dev/null; then
        log "${YELLOW}Session $session_name already exists, skipping...${NC}"
        return
    fi

    tmux new-session -d -s "$session_name" \
        "$SCRIPT_DIR/tlab-agent.sh $agent_name $wave_num 2>&1 | tee $LOG_DIR/tlab-${agent_name}-agent.log"

    log "${GREEN}Agent $agent_name launched in tmux session: $session_name${NC}"
}

run_wave() {
    local wave_num=$1
    local wave_name=$2
    local agents=$(get_wave_agents $wave_num)

    log "${BLUE}========================================${NC}"
    log "${BLUE}Starting Wave $wave_num: $wave_name${NC}"
    log "${BLUE}========================================${NC}"

    # Launch all agents in this wave
    for agent in $agents; do
        launch_agent "$agent" "$wave_num"
    done

    # Poll for completion
    log "Polling for Wave $wave_num completion (every ${POLL_INTERVAL}s)..."

    while true; do
        sleep "$POLL_INTERVAL"

        local completed=0
        local total=0

        for agent in $agents; do
            total=$((total + 1))
            if check_agent_complete "$agent"; then
                completed=$((completed + 1))
            fi
        done

        log "Wave $wave_num progress: $completed/$total agents complete"

        if [[ $completed -eq $total ]]; then
            log "${GREEN}Wave $wave_num complete!${NC}"
            break
        fi
    done
}

merge_wave_branches() {
    local wave_num=$1
    local agents=$(get_wave_agents $wave_num)

    log "Merging Wave $wave_num branches to main..."

    cd "$SCRIPT_DIR/.."
    git checkout main

    for agent in $agents; do
        local branch_name="wave-${wave_num}/tlab-${agent}-agent"
        if git show-ref --verify --quiet "refs/heads/$branch_name"; then
            log "Merging $branch_name..."
            git merge "$branch_name" --no-edit || {
                log "${RED}Merge conflict in $branch_name - manual resolution required${NC}"
                return 1
            }
        else
            log "${YELLOW}Branch $branch_name not found, skipping...${NC}"
        fi
    done

    log "${GREEN}Wave $wave_num branches merged successfully${NC}"
}

show_status() {
    # Get total elapsed if orchestrator start time exists in timing file
    local total_elapsed=""
    if [[ -f "$TIMING_FILE" ]]; then
        local orch_start=$(grep "^orchestrator:start:" "$TIMING_FILE" 2>/dev/null | tail -1 | cut -d: -f3)
        if [[ -n "$orch_start" ]]; then
            local now=$(date +%s)
            local elapsed=$((now - orch_start))
            total_elapsed=$(printf "[Elapsed: %dm %ds]" $((elapsed/60)) $((elapsed%60)))
        fi
    fi

    echo -e "\n${BLUE}=== Army-of-Ralph Status ===${NC} ${YELLOW}$total_elapsed${NC}\n"

    for wave in 0 1 2 3; do
        local agents=$(get_wave_agents $wave)
        local wave_name=$(get_wave_name $wave)

        # Determine wave status
        local wave_complete=true
        local wave_running=false
        for agent in $agents; do
            if check_agent_complete "$agent"; then
                :
            elif command -v tmux &> /dev/null && tmux has-session -t "tlab-$agent" 2>/dev/null; then
                wave_complete=false
                wave_running=true
            else
                # Check if agent is running as background process
                if pgrep -f "tlab-agent.sh $agent" > /dev/null 2>&1; then
                    wave_complete=false
                    wave_running=true
                else
                    wave_complete=false
                fi
            fi
        done

        local wave_status=""
        if $wave_complete; then
            wave_status="${GREEN}[COMPLETE]${NC}"
        elif $wave_running; then
            wave_status="${BLUE}[IN PROGRESS]${NC}"
        else
            wave_status="${NC}[PENDING]${NC}"
        fi

        echo -e "${YELLOW}Wave $wave: $wave_name${NC} $wave_status"

        for agent in $agents; do
            local progress_file="$PROGRESS_DIR/progress-tlab-${agent}.txt"
            local tasks=$(count_tasks "$progress_file")
            local percent=$(get_progress_percent "$progress_file")
            local elapsed=$(get_elapsed "$agent")
            local current=$(get_current_task "$progress_file")

            # Truncate current task if too long
            if [[ ${#current} -gt 35 ]]; then
                current="${current:0:32}..."
            fi

            if check_agent_complete "$agent"; then
                printf "  ${GREEN}✓${NC} %-18s ${GREEN}[%3d%%]${NC} %s │ %s\n" \
                    "tlab-$agent" "$percent" "$tasks" "$elapsed"
            elif command -v tmux &> /dev/null && tmux has-session -t "tlab-$agent" 2>/dev/null; then
                printf "  ${BLUE}●${NC} %-18s ${BLUE}[%3d%%]${NC} %s │ %s │ %s\n" \
                    "tlab-$agent" "$percent" "$tasks" "$elapsed" "$current"
            elif pgrep -f "tlab-agent.sh $agent" > /dev/null 2>&1; then
                printf "  ${BLUE}●${NC} %-18s ${BLUE}[%3d%%]${NC} %s │ %s │ %s\n" \
                    "tlab-$agent" "$percent" "$tasks" "$elapsed" "$current"
            else
                printf "  ${NC}○${NC} %-18s ${NC}[%3d%%]${NC} %s │ %s\n" \
                    "tlab-$agent" "$percent" "$tasks" "$elapsed"
            fi
        done
        echo ""
    done
}

dry_run() {
    echo -e "${YELLOW}=== Dry Run Mode ===${NC}\n"
    echo "Would execute the following waves:"
    echo ""

    echo "Wave 0 (Sequential):"
    for agent in $WAVE_0_AGENTS; do
        echo "  - tlab-$agent"
    done
    echo ""

    echo "Wave 1 (Parallel):"
    for agent in $WAVE_1_AGENTS; do
        echo "  - tlab-$agent"
    done
    echo ""

    echo "Wave 2 (Sequential):"
    for agent in $WAVE_2_AGENTS; do
        echo "  - tlab-$agent"
    done
    echo ""

    echo "Wave 3 (Parallel):"
    for agent in $WAVE_3_AGENTS; do
        echo "  - tlab-$agent"
    done
    echo ""

    local total=0
    for agent in $WAVE_0_AGENTS $WAVE_1_AGENTS $WAVE_2_AGENTS $WAVE_3_AGENTS; do
        total=$((total + 1))
    done
    echo "Total agents: $total"
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be executed without running"
    echo "  --status     Show current status of all agents"
    echo "  --wave N     Start from wave N (0-3)"
    echo "  --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all waves from the beginning"
    echo "  $0 --wave 2     # Start from wave 2"
    echo "  $0 --status     # Show agent status"
}

main() {
    local start_wave=0

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --wave)
                start_wave=$2
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Ensure log directory exists
    mkdir -p "$LOG_DIR"

    # Record orchestrator start time
    ORCHESTRATOR_START=$(date +%s)
    record_timing "orchestrator" "start"

    log "${GREEN}Army-of-Ralph Orchestrator Starting${NC}"
    log "Starting from Wave $start_wave"

    # Execute waves
    if [[ $start_wave -le 0 ]]; then
        run_wave 0 "Foundation"
        merge_wave_branches 0
    fi

    if [[ $start_wave -le 1 ]]; then
        run_wave 1 "Backend Features"
        merge_wave_branches 1
    fi

    if [[ $start_wave -le 2 ]]; then
        run_wave 2 "SSE Backend"
        merge_wave_branches 2
    fi

    if [[ $start_wave -le 3 ]]; then
        run_wave 3 "Frontend"
        merge_wave_branches 3
    fi

    log "${GREEN}========================================${NC}"
    log "${GREEN}All waves complete! Army-of-Ralph finished.${NC}"
    log "${GREEN}========================================${NC}"
}

main "$@"
