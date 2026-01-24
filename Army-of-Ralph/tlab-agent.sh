#!/bin/bash
# tlab-agent.sh - Launches a single Trading Lab agent
# Usage: ./tlab-agent.sh <agent-name> [wave-number]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_NAME=$1
WAVE_NUM=${2:-0}

if [[ -z "$AGENT_NAME" ]]; then
    echo "Usage: $0 <agent-name> [wave-number]"
    echo ""
    echo "Available agents:"
    echo "  Wave 0: foundation"
    echo "  Wave 1: progress, validation, performance"
    echo "  Wave 2: sse-backend"
    echo "  Wave 3: ui-feedback, sse-frontend, form-ux, trade-feed"
    exit 1
fi

AGENT_SPEC="$SCRIPT_DIR/agents/tlab-${AGENT_NAME}-agent.md"
LOG_FILE="$SCRIPT_DIR/logs/tlab-${AGENT_NAME}-agent.log"
BRANCH_NAME="wave-${WAVE_NUM}/tlab-${AGENT_NAME}-agent"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1"
}

# Validate agent spec exists
if [[ ! -f "$AGENT_SPEC" ]]; then
    log "${RED}Error: Agent spec not found: $AGENT_SPEC${NC}"
    exit 1
fi

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/logs"

# Navigate to project root
cd "$SCRIPT_DIR/.."

log "${BLUE}========================================${NC}"
log "${BLUE}Starting tlab-${AGENT_NAME} Agent${NC}"
log "${BLUE}Wave: $WAVE_NUM${NC}"
log "${BLUE}Branch: $BRANCH_NAME${NC}"
log "${BLUE}========================================${NC}"

# Create git branch
log "Creating git branch: $BRANCH_NAME"
git checkout main 2>/dev/null || true
git pull origin main 2>/dev/null || true

if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    log "${YELLOW}Branch already exists, checking out...${NC}"
    git checkout "$BRANCH_NAME"
else
    git checkout -b "$BRANCH_NAME"
    log "${GREEN}Created new branch: $BRANCH_NAME${NC}"
fi

# Read agent spec
AGENT_SPEC_CONTENT=$(cat "$AGENT_SPEC")

log "Launching Claude with agent spec..."
log "Agent spec: $AGENT_SPEC"
log "Log file: $LOG_FILE"

# Launch Claude with the agent spec as context
# The agent spec serves as the system prompt/instructions
exec claude --dangerously-skip-permissions -p "$AGENT_SPEC_CONTENT

Please implement all the user stories listed above. Follow the acceptance criteria exactly.

When you complete all tasks:
1. Commit your changes with a descriptive message
2. Update the progress file at Army-of-Ralph/progress/progress-tlab-${AGENT_NAME}.txt
3. Mark all checkboxes as complete
4. Add <promise>COMPLETE</promise> at the end of the progress file

Start by reading the files you need to modify, then implement each user story systematically."
