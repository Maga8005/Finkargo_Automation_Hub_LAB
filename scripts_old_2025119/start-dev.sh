#!/bin/bash

# Finkargo Automation Hub - Development Startup Script (macOS/Linux)
# This script starts both frontend and backend development servers

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Finkargo Automation Hub${NC}"
echo -e "${BLUE}Development Server Startup${NC}"
echo -e "${BLUE}=================================${NC}\n"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists node; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.11+"
    exit 1
fi

echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}\n"

# Check if .env files exist
if [ ! -f "$PROJECT_ROOT/frontend/.env" ]; then
    echo -e "${YELLOW}Warning: frontend/.env not found${NC}"
    echo "Copy frontend/.env.example to frontend/.env and configure it"
fi

if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
    echo -e "${YELLOW}Warning: backend/.env not found${NC}"
    echo "Copy backend/.env.example to backend/.env and configure it"
fi

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}Starting Backend (FastAPI)...${NC}"
cd "$PROJECT_ROOT/backend"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate

echo -e "${YELLOW}Installing/updating backend dependencies...${NC}"
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Backend dependencies ready${NC}"

# Start backend in background
echo -e "${BLUE}Starting backend server on http://localhost:8000${NC}"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/scripts/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null; then
    echo -e "${RED}Error: Backend failed to start${NC}"
    echo "Check backend.log for details"
    exit 1
fi

echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${GREEN}  API: http://localhost:8000/api${NC}"
echo -e "${GREEN}  Docs: http://localhost:8000/docs${NC}\n"

# Start Frontend
echo -e "${BLUE}Starting Frontend (Vite + React)...${NC}"
cd "$PROJECT_ROOT/frontend"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
else
    echo -e "${YELLOW}Updating frontend dependencies...${NC}"
    npm install
fi

echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

# Start frontend in background
echo -e "${BLUE}Starting frontend server on http://localhost:5173${NC}"
npm run dev > "$PROJECT_ROOT/scripts/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${RED}Error: Frontend failed to start${NC}"
    echo "Check frontend.log for details"
    cleanup
    exit 1
fi

echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}\n"

# Display summary
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Both servers are running!${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Frontend: http://localhost:5173${NC}"
echo -e "${GREEN}Backend:  http://localhost:8000/api${NC}"
echo -e "${GREEN}API Docs: http://localhost:8000/docs${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend: scripts/backend.log"
echo -e "  Frontend: scripts/frontend.log"
echo -e "${BLUE}=================================${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}\n"

# Follow logs (optional - you can comment this out)
echo -e "${BLUE}Tailing logs (Ctrl+C to stop)...${NC}\n"
tail -f "$PROJECT_ROOT/scripts/backend.log" "$PROJECT_ROOT/scripts/frontend.log"

# Keep script running
wait
