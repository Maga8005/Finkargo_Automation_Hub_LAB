#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Finkargo Automation Hub - Local Dev  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

# Check if .env exists in backend directory
if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
    echo -e "${RED}Warning: No .env file found in backend/.${NC}"
    echo "Please:"
    echo "  1. cd backend"
    echo "  2. cp .env.example .env"
    echo "  3. Edit .env and add your API keys"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"

    # Kill all child processes
    jobs -p | xargs -r kill 2>/dev/null

    # Wait for processes to terminate
    wait 2>/dev/null

    echo -e "${GREEN}Services stopped successfully.${NC}"
    exit 0
}

# Trap EXIT, INT, and TERM signals
trap cleanup EXIT INT TERM

# Kill existing processes on ports
echo -e "${YELLOW}Clearing ports 5175 and 8003...${NC}"
lsof -ti:5175 | xargs -r kill -9 2>/dev/null || true
lsof -ti:8003 | xargs -r kill -9 2>/dev/null || true
sleep 1

# Start backend using uv (handles dependencies automatically)
echo -e "${GREEN}Starting backend server (uv)...${NC}"
cd "$PROJECT_ROOT/backend"
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8003 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Backend failed to start!${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$PROJECT_ROOT/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}Installing frontend dependencies...${NC}"
    npm install
fi

npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 5

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}Frontend failed to start!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Services started successfully!${NC}"
echo -e "${BLUE}Frontend: http://localhost:5175${NC}"
echo -e "${BLUE}Backend:  http://localhost:8003${NC}"
echo -e "${BLUE}API Docs: http://localhost:8003/docs${NC}"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for user to press Ctrl+C
wait
