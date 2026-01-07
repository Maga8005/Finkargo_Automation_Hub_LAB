# Bug: PA CSV Upload Connection Refused Error

## Bug Description
When attempting to upload a large CSV file (~12.4 MB / 12371 KB) to the PA report in the "finanzas" functionality, the frontend receives a `net::ERR_CONNECTION_REFUSED` error. The error occurs at `financeServicePA.ts:208` when making a POST request to `http://localhost:8003/api/finance/pa/process/upload`.

**Symptoms:**
- User attempts to upload a ~12 MB CSV file to the PA report
- The frontend makes a POST request to the backend upload endpoint
- Instead of receiving a response, the connection is refused
- Error displayed: `net::ERR_CONNECTION_REFUSED`

**Expected behavior:**
- Large CSV files (12+ MB) should upload successfully
- The backend should process the file and return a session ID
- If the file is too large, a clear error message should be shown

**Actual behavior:**
- Connection is refused, suggesting the backend server crashed or is not running

## Problem Statement
The PA report CSV upload fails for large files (~12.4 MB) with a connection refused error. This could be caused by:
1. The backend server is not running
2. The backend server crashes when processing large files (memory issues with Pandas)
3. FastAPI/Uvicorn request body size limits
4. Frontend axios timeout issues for large uploads

## Solution Statement
1. Add explicit request body size limits to FastAPI to handle large file uploads (50 MB max for PA reports)
2. Optimize memory usage for large CSV processing in `pa_report_service.py`
3. Add better error handling and logging to identify the exact failure point
4. Increase frontend timeout for large file uploads (already set to 600000ms / 10 min)
5. Ensure the frontend properly catches and displays connection errors

## Steps to Reproduce
1. Navigate to Finance → Reporte PA page (http://localhost:5175/finance/reporte-pa)
2. Ensure the backend server is running on port 8003
3. Upload a CSV file that is approximately 12 MB or larger
4. Observe the `net::ERR_CONNECTION_REFUSED` error in the browser console

## Root Cause Analysis
The `net::ERR_CONNECTION_REFUSED` error indicates that the TCP connection to the backend server could not be established. This happens when:

1. **Backend server not running**: The server at `localhost:8003` is not listening for connections
2. **Backend server crashed**: During processing of the large file, the server may crash due to:
   - Memory exhaustion when reading the entire file into memory with Pandas
   - Python process terminated by OOM killer
   - Uncaught exception in the file processing code

Looking at the code:
- `pa_routes.py:308` reads the entire file content into memory: `content = await file.read()`
- `pa_report_service.py:551-555` parses the CSV using Pandas into memory
- For a 12+ MB file, this could cause memory issues, especially if the server has limited RAM

**Most likely root cause**: The backend server crashes when processing large files due to memory pressure from loading the entire file into a Pandas DataFrame. When the Python process terminates, it stops listening on port 8003, causing subsequent requests to receive `CONNECTION_REFUSED`.

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [x] Frontend: pages
- [ ] Frontend: components
- [x] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/main.py` - FastAPI application entry point, may need to configure request body size limits
- `backend/src/adapter/rest/pa_routes.py` - PA API routes, contains the `/process/upload` endpoint that receives the file
- `backend/src/core/servicios/pa_report_service.py` - PA report service, contains the `_parse_csv` method and file processing logic
- `backend/src/config/settings.py` - Application settings, contains `MAX_UPLOAD_SIZE` setting (currently 10 MB)
- `frontend/src/services/financeServicePA.ts` - Frontend service that makes the upload request, has 600000ms timeout
- `frontend/src/pages/finance/ReportePA.tsx` - The PA report page with the file upload UI
- `app_docs/feature-550a54d1-pa-report-classification.md` - Documentation for the PA report classification feature

### New Files
- `.claude/commands/e2e/test_pa_csv_upload.md` - E2E test for PA CSV upload with large files

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Increase MAX_UPLOAD_SIZE in settings
- Edit `backend/src/config/settings.py`
- Increase `MAX_UPLOAD_SIZE` from 10485760 (10 MB) to 52428800 (50 MB) to support PA report files
- This is the feature documentation recommendation for PA reports: "Designed to handle ~50k rows"
- A 50k row CSV can easily be 15-25 MB

### 2. Add request body size limit middleware to FastAPI
- Edit `backend/main.py`
- Add a middleware or configuration to allow larger request bodies for the PA upload endpoint
- Uvicorn/Starlette default limit is typically unlimited, but some deployments may have limits
- Add explicit configuration to ensure large files are accepted

### 3. Optimize memory usage in CSV parsing
- Edit `backend/src/core/servicios/pa_report_service.py`
- In `_parse_csv` method, consider using `chunksize` parameter for very large files
- Add try-except block around file parsing to catch memory errors
- Log file size before processing for debugging

### 4. Add better error handling in pa_routes.py
- Edit `backend/src/adapter/rest/pa_routes.py`
- In `upload_netsuite_file` endpoint, add logging for file size
- Add try-except to catch any exceptions during file read
- Return proper error responses instead of letting exceptions crash the server

### 5. Add connection error handling in frontend service
- Edit `frontend/src/services/financeServicePA.ts`
- In `uploadNetSuiteFile` function, add specific handling for network errors
- Convert `ERR_CONNECTION_REFUSED` to a user-friendly message like "No se pudo conectar al servidor. Verifique que el servidor esté activo."

### 6. Add error handling in frontend page
- Edit `frontend/src/pages/finance/ReportePA.tsx`
- In `handleFileUpload` function, improve error message display for connection errors
- Show a specific message when the backend is unavailable

### 7. Create E2E test for PA CSV upload
- Read `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_pa_csv_upload.md` with test cases for:
  - Uploading a small CSV file successfully
  - Uploading a large CSV file (simulate with proper test data)
  - Handling connection errors gracefully

### 8. Run validation commands
- Execute all validation commands to ensure the fix works and no regressions are introduced

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Pre-fix verification (reproduce the bug)
```bash
# Check if backend is running
curl -s http://localhost:8003/api/health

# Check backend logs for any errors during upload attempts
# The backend should be started with: cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### Post-fix verification
```bash
# Start the application
cd /mnt/c/Users/guill/danke_apps/fkhub/lab-automation-hub-amplify && sh ./scripts/start.sh

# Test health endpoint
curl -s http://localhost:8003/api/health

# Test that PA upload endpoint responds (without actual file)
curl -X POST http://localhost:8003/api/finance/pa/process/upload -H "Content-Type: multipart/form-data" -F "file=@/dev/null" 2>&1 | head -20
```

### Backend tests
```bash
cd backend && python -m pytest
```

### Backend linting
```bash
cd backend && ruff check src/
```

### Frontend linting
```bash
cd frontend && npm run lint
```

### TypeScript type check
```bash
cd frontend && npx tsc --noEmit
```

### Frontend build
```bash
cd frontend && npm run build
```

### E2E Test (after creating test file)
Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_csv_upload.md` to validate this functionality works.

## Notes
- The PA report feature is designed to handle ~50k rows within 2 minutes according to `app_docs/feature-550a54d1-pa-report-classification.md`
- A 50k row CSV can be 15-25 MB depending on the data
- The current `MAX_UPLOAD_SIZE` of 10 MB is insufficient for production PA reports
- The frontend already has a 10-minute timeout (600000ms) which is appropriate for large file processing
- Memory usage should be monitored when processing very large files - consider chunked processing for files over 25 MB
- In production (Render), memory limits may be more restrictive than local development
