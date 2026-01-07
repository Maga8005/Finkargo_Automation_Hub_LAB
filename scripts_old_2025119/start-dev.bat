@echo off
REM Finkargo Automation Hub - Development Startup Script (Windows)
REM This script starts both frontend and backend development servers

echo ================================
echo Finkargo Automation Hub
echo Development Server Startup
echo ================================
echo.

REM Get project root directory
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo Checking prerequisites...

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i

echo ✓ Node.js found: %NODE_VERSION%
echo ✓ Python found: %PYTHON_VERSION%
echo.

REM Check if .env files exist
if not exist "%PROJECT_ROOT%\frontend\.env" (
    echo Warning: frontend\.env not found
    echo Copy frontend\.env.example to frontend\.env and configure it
    echo.
)

if not exist "%PROJECT_ROOT%\backend\.env" (
    echo Warning: backend\.env not found
    echo Copy backend\.env.example to backend\.env and configure it
    echo.
)

REM Start Backend
echo Starting Backend (FastAPI)...
cd /d "%PROJECT_ROOT%\backend"

REM Check if venv exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

echo Installing/updating backend dependencies...
pip install -q -r requirements.txt

echo ✓ Backend dependencies ready
echo.

REM Start backend in new window
echo Starting backend server on http://localhost:8000
start "Finkargo Backend" cmd /k "cd /d %PROJECT_ROOT%\backend && venv\Scripts\activate.bat && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo ✓ Backend started
echo   API: http://localhost:8000/api
echo   Docs: http://localhost:8000/docs
echo.

REM Start Frontend
echo Starting Frontend (Vite + React)...
cd /d "%PROJECT_ROOT%\frontend"

REM Install dependencies
echo Installing/updating frontend dependencies...
call npm install

echo ✓ Frontend dependencies ready
echo.

REM Start frontend in new window
echo Starting frontend server on http://localhost:5173
start "Finkargo Frontend" cmd /k "cd /d %PROJECT_ROOT%\frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo ✓ Frontend started
echo.

REM Display summary
echo ================================
echo Both servers are running!
echo ================================
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000/api
echo API Docs: http://localhost:8000/docs
echo ================================
echo.
echo Two separate windows have been opened:
echo   1. Backend window (FastAPI/Uvicorn)
echo   2. Frontend window (Vite/React)
echo.
echo Close those windows to stop the servers
echo ================================
echo.

pause
