#!/bin/bash
# Army-of-Ralph Orchestrator
# Manages wave execution for Trading Lab usability improvements
# Compatible with Bash 3 (macOS default)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PROGRESS_DIR="$SCRIPT_DIR/progress"
POLL_INTERVAL=30

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
    echo -e "\n${BLUE}=== Army-of-Ralph Status ===${NC}\n"

    for wave in 0 1 2 3; do
        local agents=$(get_wave_agents $wave)

        echo -e "${YELLOW}Wave $wave:${NC}"
        for agent in $agents; do
            if check_agent_complete "$agent"; then
                echo -e "  ${GREEN}[COMPLETE]${NC} tlab-$agent"
            elif command -v tmux &> /dev/null && tmux has-session -t "tlab-$agent" 2>/dev/null; then
                echo -e "  ${BLUE}[RUNNING]${NC}  tlab-$agent"
            else
                echo -e "  ${NC}[PENDING]${NC}  tlab-$agent"
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
