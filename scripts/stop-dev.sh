#!/bin/bash

# Finkargo Automation Hub - Stop Development Servers
# This script stops both frontend and backend development servers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Finkargo Automation Hub servers...${NC}\n"

# Function to kill process on a port
kill_port() {
    local port=$1
    local name=$2

    PID=$(lsof -ti:$port 2>/dev/null)

    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}Stopping $name on port $port (PID: $PID)${NC}"
        kill -9 $PID 2>/dev/null
        echo -e "${GREEN}✓ $name stopped${NC}"
    else
        echo -e "${YELLOW}No process found on port $port ($name)${NC}"
    fi
}

# Stop backend (port 8000)
kill_port 8000 "Backend"

# Stop frontend (port 5173)
kill_port 5173 "Frontend"

echo -e "\n${GREEN}Done!${NC}"
