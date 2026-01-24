#!/bin/bash
# format-logs.sh - Colorizes and formats log output
# Usage: ./format-logs.sh logs/*.log

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 <log-file(s)>"
    echo "Example: $0 logs/*.log"
    echo "         $0 logs/tlab-foundation-agent.log"
    exit 1
fi

tail -f "$@" 2>/dev/null | while IFS= read -r line; do
    # Extract timestamp if present
    timestamp=""
    if [[ "$line" =~ ^\[([0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2})\] ]]; then
        timestamp="${CYAN}[${BASH_REMATCH[1]}]${NC} "
        line="${line#*] }"
    fi

    # Colorize based on content
    if [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"Error"* ]] || [[ "$line" == *"error"* ]] || [[ "$line" == *"FAILED"* ]]; then
        echo -e "${timestamp}${RED}$line${NC}"
    elif [[ "$line" == *"[x]"* ]] || [[ "$line" == *"COMPLETE"* ]] || [[ "$line" == *"✓"* ]] || [[ "$line" == *"success"* ]]; then
        echo -e "${timestamp}${GREEN}$line${NC}"
    elif [[ "$line" == *"Starting"* ]] || [[ "$line" == *"Launching"* ]] || [[ "$line" == *"=========="* ]]; then
        echo -e "${timestamp}${BLUE}$line${NC}"
    elif [[ "$line" == *"WARNING"* ]] || [[ "$line" == *"Warning"* ]] || [[ "$line" == *"YELLOW"* ]]; then
        echo -e "${timestamp}${YELLOW}$line${NC}"
    elif [[ "$line" == *"Wave"* ]] || [[ "$line" == *"Agent"* ]]; then
        echo -e "${timestamp}${CYAN}$line${NC}"
    else
        echo -e "${timestamp}$line"
    fi
done
