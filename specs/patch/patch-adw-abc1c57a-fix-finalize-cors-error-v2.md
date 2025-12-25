# Patch: Fix CORS Error on Finalize Evaluation Endpoint (v2)

## Metadata
adw_id: `abc1c57a`
review_change_request: `CORS error on finalize endpoint persists after previous patch - No 'Access-Control-Allow-Origin' header present when calling http://localhost:8000/api/risk/evaluations/{id}/finalize`

## Issue Summary
**Original Spec:** `specs/issue-34-adw-abc1c57a-sdlc_planner-defer-fraud-checks-finalization.md`
**Issue:** After the previous CORS fix (commit 82d5593), the finalize endpoint still throws a CORS error. The previous patch added exception handling inside the route handler, but CORS errors can also occur when:
1. Exceptions occur in FastAPI dependencies (authentication/RBAC) BEFORE the route handler runs
2. The global exception handler doesn't properly propagate CORS headers
3. Server crashes completely before returning any response

The root cause is that FastAPI's `CORSMiddleware` only adds CORS headers to successful responses and `HTTPException` responses. If an unhandled exception propagates before being converted to an HTTP response, CORS headers are missing.

**Solution:** Add a global exception handler that catches all unhandled exceptions and converts them to proper HTTPException responses, ensuring CORS headers are always included. This must be added at the application level in `main.py`.

## Files to Modify
Use these files to implement the patch:

- `backend/main.py` - Add global exception handler that catches all unhandled exceptions and returns HTTPException with proper status codes

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add global exception handler to main.py
- Import `Request` from fastapi and `JSONResponse` from fastapi.responses
- Add an exception handler decorator `@app.exception_handler(Exception)` AFTER the middleware configuration but BEFORE including routers
- The handler should:
  - Log the full exception with traceback
  - Return a `JSONResponse` with status_code 500 and a generic error message
  - The JSONResponse will automatically get CORS headers from the middleware

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unhandled exceptions.
    Ensures CORS headers are included in error responses.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )
```

### Step 2: Verify imports are correct
- Ensure `Request` is imported from fastapi
- Ensure `JSONResponse` is imported from fastapi.responses
- The handler must be placed after middleware but before router includes

### Step 3: Run syntax and lint checks
- Verify Python syntax compiles correctly
- Run ruff linter to check code quality

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && python -m py_compile main.py` - Validate Python syntax for main.py
2. `cd backend && ./venv/bin/ruff check main.py` - Run linter on modified file
3. `cd backend && python -m py_compile src/adapter/rest/risk_routes.py` - Validate risk routes syntax
4. `cd backend && python -m pytest tests/ -v --tb=short` - Run all backend tests
5. `cd frontend && npm run lint` - Run frontend linting
6. `cd frontend && npm run build` - Build frontend to verify no regressions

## Patch Scope
**Lines of code to change:** ~15 lines (adding global exception handler)
**Risk level:** low
**Testing required:** Manual test by triggering finalization in the UI to verify error responses include CORS headers. Test with a valid evaluation ID to confirm successful finalization also works.
