# Bug: PA Report Upload Fails with CORS/413 Error for Large Files

## Bug Description
When uploading a CSV file (~12MB) to the PA Report upload feature at `/api/finance/pa/process/upload`, the upload fails with a CORS policy error in the browser console. The actual underlying issue is a 413 "Request Entity Too Large" error from the backend, which is incorrectly configured with a 10MB limit despite documentation and code comments stating 50MB support.

**Symptoms:**
- Browser console shows: `Access to XMLHttpRequest at 'http://localhost:8003/api/finance/pa/process/upload' from origin 'http://localhost:5175' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`
- Frontend error: `No se pudo conectar al servidor. Verifique que el servidor esté activo e intente nuevamente.`
- Backend logs show: `Request body too large: 12667111 bytes (max: 10485760)` followed by `413 Request Entity Too Large`

**Expected behavior:** Files up to 50MB should upload successfully as documented.

**Actual behavior:** Files larger than ~10MB fail with misleading CORS error.

## Problem Statement
The `MAX_UPLOAD_SIZE` setting in `backend/src/config/settings.py` is set to `10485760` (10MB) but the code comments and documentation state the limit should be 50MB (`52428800` bytes). This mismatch causes large PA report files (~12MB in this case) to be rejected by the `RequestSizeLimitMiddleware`. When the middleware returns a 413 response, the CORS headers may not be properly included in the error response, causing the browser to report a CORS error instead of the actual file size error.

## Solution Statement
1. Update `MAX_UPLOAD_SIZE` in `backend/src/config/settings.py` to `52428800` (50MB) to match documentation
2. Ensure the `RequestSizeLimitMiddleware` 413 response includes proper CORS headers by updating the middleware to use `JSONResponse` with CORS headers or by ensuring CORS middleware processes it correctly
3. Update frontend error handling to better detect and report 413 errors

## Steps to Reproduce
1. Navigate to Finance > Reporte PA in the application
2. Upload the file `MovimientoDetallado NOV_25.csv` (~12MB)
3. Observe CORS error in browser console and generic connection error in UI
4. Check backend logs showing 413 error due to file size limit

## Root Cause Analysis
The root cause is a configuration mismatch:

1. **Incorrect MAX_UPLOAD_SIZE value**: In `backend/src/config/settings.py`, the default `MAX_UPLOAD_SIZE` is set to `10485760` (10MB), but the comment above it says "50 MB max upload size". The value should be `52428800` for 50MB.

2. **CORS header missing on 413 response**: When `RequestSizeLimitMiddleware` returns a 413 response directly, it bypasses the normal request flow where CORS headers are added by the `CORSMiddleware`. Since middleware order matters in FastAPI/Starlette, and the `RequestSizeLimitMiddleware` is added after `CORSMiddleware`, the 413 response doesn't go through CORS processing.

3. **Frontend error masking**: The frontend's `getNetworkErrorMessage` function in `financeServicePA.ts` doesn't properly detect the 413 status from axios errors, leading to a generic "connection error" message.

## Affected Layer
- [x] Backend: adapter/rest (API routes) - main.py middleware
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [x] Frontend: services - financeServicePA.ts error handling
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/config/settings.py` - Contains the `MAX_UPLOAD_SIZE` setting that needs to be corrected to 50MB
- `backend/main.py` - Contains `RequestSizeLimitMiddleware` that needs to ensure CORS headers are included in 413 responses
- `frontend/src/services/financeServicePA.ts` - Contains `getNetworkErrorMessage` function that needs to better detect 413 errors

### New Files
None required.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix MAX_UPLOAD_SIZE Configuration
- Open `backend/src/config/settings.py`
- Change `MAX_UPLOAD_SIZE: int = 10485760` to `MAX_UPLOAD_SIZE: int = 52428800`
- This aligns the actual limit (50MB) with the documented behavior

### Step 2: Update RequestSizeLimitMiddleware for CORS Compatibility
- Open `backend/main.py`
- Modify the `RequestSizeLimitMiddleware` to include CORS headers in the 413 response
- Add the `Access-Control-Allow-Origin` header to the JSONResponse for 413 errors
- Alternatively, move the middleware to be added before CORS middleware (but this may have other implications)

The simplest fix is to update the 413 response in `RequestSizeLimitMiddleware.dispatch()`:
```python
return JSONResponse(
    status_code=413,
    content={
        "detail": f"El archivo es demasiado grande. Tamaño máximo: {self.max_upload_size // (1024 * 1024)} MB"
    },
    headers={
        "Access-Control-Allow-Origin": "*",  # Or specific origins
        "Access-Control-Allow-Credentials": "true",
    }
)
```

### Step 3: Improve Frontend 413 Error Detection
- Open `frontend/src/services/financeServicePA.ts`
- Update `getNetworkErrorMessage` to check for axios error response status 413
- Add proper detection of HTTP 413 status code from `error.response?.status`
- Provide user-friendly message about file size limit

Example update:
```typescript
const getNetworkErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    // Check for 413 status from response
    if (error.response?.status === 413) {
      return 'El archivo es demasiado grande. El tamaño máximo es 50 MB.';
    }
    // ... rest of existing checks
  }
  // ... existing logic
};
```

### Step 4: Restart Backend and Test
- Restart the backend server to pick up configuration changes
- Test uploading the ~12MB CSV file
- Verify the file uploads successfully

### Step 5: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Verify the MAX_UPLOAD_SIZE is correctly set to 50MB
grep -n "MAX_UPLOAD_SIZE" backend/src/config/settings.py
# Expected: MAX_UPLOAD_SIZE: int = 52428800

# Restart backend (if running)
# The user should restart their backend server

# Test the health endpoint to ensure backend is running
curl -s http://localhost:8003/api/health | jq .

# Test CORS preflight for the upload endpoint
curl -X OPTIONS http://localhost:8003/api/finance/pa/process/upload \
  -H "Origin: http://localhost:5175" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep -i "access-control"

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

## Notes
- The bug manifests as a CORS error in the browser, but the actual root cause is a file size limit configuration issue
- The `MAX_UPLOAD_SIZE` default value of 10MB contradicts the comment directly above it that says "50 MB max upload size"
- This is a development environment issue; production may have different `MAX_UPLOAD_SIZE` configured via environment variables
- The frontend timeout of 10 minutes (600000ms) is appropriate for large file processing
- Consider adding a file size validation on the frontend before upload to provide immediate feedback to users
