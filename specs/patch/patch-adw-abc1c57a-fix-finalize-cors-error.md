# Patch: Fix CORS Error on Finalize Evaluation Endpoint

## Metadata
adw_id: `abc1c57a`
review_change_request: `CORS error on finalize endpoint - No 'Access-Control-Allow-Origin' header present`

## Issue Summary
**Original Spec:** `specs/issue-34-adw-abc1c57a-sdlc_planner-defer-fraud-checks-finalization.md`
**Issue:** The `/api/risk/evaluations/{id}/finalize` endpoint throws a CORS error because unhandled exceptions bypass the CORS middleware, resulting in responses without the `Access-Control-Allow-Origin` header.
**Solution:** Wrap the `finalize_evaluation` endpoint body in a try/except block that catches exceptions and re-raises them as HTTPException, ensuring CORS headers are properly included in error responses. This pattern is already used in the `create_evaluation` endpoint.

## Files to Modify
Use these files to implement the patch:

- `backend/src/adapter/rest/risk_routes.py` - Add exception handling to `finalize_evaluation` endpoint (lines 1257-1360)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add exception handling to finalize_evaluation endpoint
- Locate the `finalize_evaluation` function at line 1257 in `risk_routes.py`
- Wrap the main logic (after initial validation) in a try/except block
- Catch generic `Exception` and re-raise as `HTTPException` with status 500
- Include the original error message in the detail field
- Log the exception with full traceback using `logger.error()` with `exc_info=True`

The pattern to follow is from `create_evaluation` endpoint (lines 313-328):
```python
try:
    # existing finalization logic
except Exception as e:
    logger.error(f"Error finalizing evaluation {id}: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error finalizing evaluation: {str(e)}"
    )
```

### Step 2: Verify the fix compiles correctly
- Run Python syntax check to ensure no syntax errors introduced
- Run ruff linter to check code quality

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && python -m py_compile src/adapter/rest/risk_routes.py` - Validate Python syntax
2. `cd backend && ./venv/bin/ruff check src/adapter/rest/risk_routes.py` - Run linter on modified file
3. `cd backend && python -m pytest tests/ -v --tb=short` - Run all backend tests
4. `cd frontend && npm run lint` - Run frontend linting
5. `cd frontend && npm run build` - Build frontend to verify no regressions

## Patch Scope
**Lines of code to change:** ~15 lines (adding try/except wrapper)
**Risk level:** low
**Testing required:** Manual test by triggering finalization in the UI to verify error responses include CORS headers
