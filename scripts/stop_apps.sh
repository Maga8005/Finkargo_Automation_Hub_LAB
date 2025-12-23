#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Finkargo Automation Hub...${NC}"

# Kill any running start.sh processes
echo -e "${GREEN}Killing start.sh processes...${NC}"
pkill -f "start.sh" 2>/dev/null

# Kill uvicorn processes
echo -e "${GREEN}Killing uvicorn processes...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null

# Kill vite processes
echo -e "${GREEN}Killing vite processes...${NC}"
pkill -f "vite" 2>/dev/null

# Kill webhook server
echo -e "${GREEN}Killing webhook server...${NC}"
pkill -f "trigger_webhook.py" 2>/dev/null

# Kill processes on specific ports
echo -e "${GREEN}Killing processes on ports 5173 and 8000...${NC}"
lsof -ti:5173 | xargs -r kill -9 2>/dev/null || true
lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true

echo -e "${GREEN}✓ Services stopped successfully!${NC}"