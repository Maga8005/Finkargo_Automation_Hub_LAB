# Quick Start Guide

## ✅ App is Currently Running!

Your Finkargo Automation Hub is now running locally:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## How to Use the Startup Scripts

### macOS/Linux

```bash
# Run the startup script
./scripts/start-dev.sh

# Stop the servers
Press Ctrl+C in the terminal
```

### Windows

```cmd
# Double-click this file or run from command prompt:
scripts\start-dev.bat

# Stop the servers
Close the backend and frontend windows
```

## What the Scripts Do

The startup scripts automatically:
1. ✅ Check for Node.js and Python
2. ✅ Create Python virtual environment (if needed)
3. ✅ Install/update all dependencies
4. ✅ Start the backend server (FastAPI/Uvicorn)
5. ✅ Start the frontend server (Vite/React)
6. ✅ Create log files for monitoring
7. ✅ Handle graceful shutdown

## Current Status

**Backend Server**
- Status: ✅ Running
- Port: 8000
- Process: Uvicorn with auto-reload
- Logs: `scripts/backend.log`

**Frontend Server**
- Status: ✅ Running
- Port: 5173
- Process: Vite dev server with HMR
- Logs: `scripts/frontend.log`

## Monitoring Logs

### View logs in real-time:

**macOS/Linux:**
```bash
# Both logs together
tail -f scripts/backend.log scripts/frontend.log

# Backend only
tail -f scripts/backend.log

# Frontend only
tail -f scripts/frontend.log
```

**Windows:**
```cmd
# PowerShell
Get-Content scripts\backend.log -Wait

# Or just watch the separate windows that opened
```

## Important Notes

### Environment Variables

The `.env` files have been created from `.env.example` templates, but you'll need to configure your Supabase credentials:

**Frontend** (`frontend/.env`):
```bash
VITE_SUPABASE_URL=https://[your-project-id].supabase.co
VITE_SUPABASE_ANON_KEY=[your-anon-key]
```

**Backend** (`backend/.env`):
```bash
SUPABASE_URL=https://[your-project-id].supabase.co
SUPABASE_ANON_KEY=[your-anon-key]
SUPABASE_SERVICE_KEY=[your-service-key]
SUPABASE_JWT_SECRET=[your-jwt-secret]
SECRET_KEY=[generate-a-secure-key]
DATABASE_URL=postgresql://[your-connection-string]
```

**To get your Supabase credentials:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Settings → API
4. Copy the URL and keys

### Port Conflicts

If you see "Address already in use" errors:

**macOS/Linux:**
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

**Windows:**
```cmd
# Find process on port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual PID)
taskkill /PID <PID> /F
```

## Stopping the Servers

### macOS/Linux (start-dev.sh)
Press `Ctrl+C` in the terminal where the script is running. The script will gracefully shut down both servers.

### Windows (start-dev.bat)
Close the two command windows that opened (Backend and Frontend), or press `Ctrl+C` in each window.

## Troubleshooting

### Backend won't start

1. **Check Python version**: Must be 3.11+ (yours is 3.9.6 - may cause issues)
   ```bash
   python3 --version
   ```

2. **Check virtual environment**:
   ```bash
   cd backend
   source venv/bin/activate  # Mac/Linux
   venv\Scripts\activate.bat  # Windows
   pip install -r requirements.txt
   ```

3. **Check Supabase credentials**: Make sure `.env` has valid credentials

4. **View logs**:
   ```bash
   cat scripts/backend.log
   ```

### Frontend won't start

1. **Check Node.js version**: Should be 18.x or 20.x (yours is 24.x - should work)
   ```bash
   node --version
   ```

2. **Clear cache and reinstall**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **View logs**:
   ```bash
   cat scripts/frontend.log
   ```

### Still having issues?

1. Check `scripts/backend.log` and `scripts/frontend.log` for detailed errors
2. Review `scripts/README.md` for comprehensive troubleshooting
3. See `CLAUDE.md` for architecture and setup details
4. Review `COLLABORATIVE_LOCAL_SETUP_GUIDE.md` for step-by-step setup

## Next Steps

1. **Configure Supabase** (required for auth and database):
   - Update `frontend/.env` and `backend/.env` with your Supabase credentials
   - Restart the servers: `./scripts/start-dev.sh`

2. **Access the app**:
   - Open http://localhost:5173 in your browser
   - Try the API docs at http://localhost:8000/docs

3. **Start developing**:
   - Both servers support hot reload
   - Edit files and see changes automatically
   - Frontend: Changes reflect instantly
   - Backend: Server auto-restarts on file changes

4. **View documentation**:
   - `CLAUDE.md` - Comprehensive codebase guide
   - `TECHNICAL_INTEGRATION_BLUEPRINT.md` - Architecture details
   - `backend/database/README.md` - Database setup
   - `scripts/README.md` - Detailed script documentation

## Pro Tips

- **Keep the terminal open**: The startup script runs both servers and shows live logs
- **Use separate terminals**: For running other commands while servers are running
- **Monitor logs**: Watch `scripts/backend.log` and `scripts/frontend.log` for errors
- **Hot reload works**: No need to restart - just save your files
- **API testing**: Use http://localhost:8000/docs for interactive API testing

---

**Created**: November 22, 2025
**Last Updated**: November 22, 2025
**Servers Running**: ✅ Yes
