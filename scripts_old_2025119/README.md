# Development Scripts

This folder contains scripts to help you run the Finkargo Automation Hub locally.

## Available Scripts

### 1. `start-dev.sh` (macOS/Linux)

Bash script that starts both frontend and backend development servers.

**Usage:**
```bash
# Make script executable (first time only)
chmod +x scripts/start-dev.sh

# Run the script
./scripts/start-dev.sh
```

**What it does:**
- Checks for Node.js and Python installation
- Creates Python virtual environment if needed
- Installs/updates dependencies for both frontend and backend
- Starts backend server on `http://localhost:8000`
- Starts frontend server on `http://localhost:5173`
- Creates log files (`backend.log` and `frontend.log`) in the scripts folder
- Handles graceful shutdown with Ctrl+C

**Features:**
- Color-coded output
- Automatic dependency installation
- Log file generation
- Clean shutdown on Ctrl+C
- Environment file validation

### 2. `start-dev.bat` (Windows)

Windows batch script that starts both servers in separate command windows.

**Usage:**
```cmd
# Run from project root
scripts\start-dev.bat

# Or double-click the file in File Explorer
```

**What it does:**
- Checks for Node.js and Python installation
- Creates Python virtual environment if needed
- Installs/updates dependencies
- Opens two separate command windows:
  - Backend window (FastAPI/Uvicorn)
  - Frontend window (Vite/React)

**Features:**
- Separate windows for each server
- Easy to monitor logs in real-time
- Simple to stop (close the windows)

## Prerequisites

Before running these scripts, ensure you have:

1. **Node.js** (18.x or 20.x)
   - Download: https://nodejs.org/

2. **Python** (3.11.9 recommended)
   - Download: https://www.python.org/

3. **Environment Variables**
   - Copy `frontend/.env.example` to `frontend/.env`
   - Copy `backend/.env.example` to `backend/.env`
   - Configure with your Supabase credentials

## First-Time Setup

```bash
# 1. Install Node.js and Python (see above)

# 2. Clone the repository (if you haven't already)
git clone <repo-url>
cd Finkargo_Automation_Hub

# 3. Set up environment variables
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env

# Edit .env files with your credentials
nano frontend/.env
nano backend/.env

# 4. Run the startup script
# macOS/Linux:
chmod +x scripts/start-dev.sh
./scripts/start-dev.sh

# Windows:
scripts\start-dev.bat
```

## Access Points

Once both servers are running:

- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Troubleshooting

### Script won't run (macOS/Linux)

```bash
# Make sure script is executable
chmod +x scripts/start-dev.sh
```

### Port already in use

If you get "port already in use" errors:

```bash
# Find and kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Find and kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Dependencies not installing

```bash
# Frontend issues
cd frontend
rm -rf node_modules package-lock.json
npm install

# Backend issues
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

### Environment variables not loading

Make sure you have:
- `frontend/.env` with all `VITE_*` variables
- `backend/.env` with all required variables
- Correct Supabase credentials

### Backend fails to start

Check `scripts/backend.log` for errors:
```bash
tail -f scripts/backend.log
```

Common issues:
- Missing dependencies: `pip install -r backend/requirements.txt`
- Wrong Python version: Use Python 3.11.9
- Database connection issues: Check `SUPABASE_URL` in `.env`

### Frontend fails to start

Check `scripts/frontend.log` for errors:
```bash
tail -f scripts/frontend.log
```

Common issues:
- Missing dependencies: `npm install` in frontend folder
- Wrong Node version: Use Node 18.x or 20.x
- Port 5173 in use: Kill process or use different port

## Manual Startup (Alternative)

If you prefer to run servers manually in separate terminals:

**Terminal 1 - Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Stopping the Servers

**macOS/Linux (start-dev.sh):**
- Press `Ctrl+C` in the terminal running the script
- Script will gracefully shut down both servers

**Windows (start-dev.bat):**
- Close the backend command window
- Close the frontend command window
- Or press `Ctrl+C` in each window

## Log Files

When using `start-dev.sh` (macOS/Linux), logs are saved to:
- `scripts/backend.log` - Backend server logs
- `scripts/frontend.log` - Frontend server logs

View logs in real-time:
```bash
tail -f scripts/backend.log
tail -f scripts/frontend.log
```

## Tips

1. **Keep terminals open**: Don't close the terminal running the script
2. **Check logs first**: If something fails, check the log files
3. **Update dependencies**: Scripts automatically install/update dependencies
4. **Use health check**: Visit `/api/health` to verify backend is running
5. **Hot reload**: Both servers support hot reload - changes will reflect automatically

## Need Help?

- Check `CLAUDE.md` for comprehensive setup instructions
- Review `COLLABORATIVE_LOCAL_SETUP_GUIDE.md` for detailed setup
- See `TECHNICAL_INTEGRATION_BLUEPRINT.md` for architecture details
- Open an issue on GitHub if problems persist
