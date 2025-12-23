# Implementation Report: Fix Risk Evaluation CORS Error

**Date:** 2025-12-23
**Module:** Risk Management
**Issue:** CORS error when creating new risk evaluations

## Summary

Fixed a bug where creating new risk evaluations in the Risk Dashboard resulted in a CORS error. The root cause was a mismatch between the `AssessmentStatus` enum in the application code and the CHECK constraint in the `risk_assessments` database table.

## Changes Made

### 1. Database Migration (New File)
**File:** `backend/database/migration_add_pending_documents_status.sql`

Created a new SQL migration that:
- Dynamically finds and drops the existing CHECK constraint on the `status` column
- Adds a new CHECK constraint that includes all 7 status values from the `AssessmentStatus` enum:
  - `pending` - Initial status
  - `pending_documents` - Awaiting document upload (was missing!)
  - `in_progress` - Evaluation in progress
  - `completed` - Evaluation completed
  - `escalated` - Escalated for review
  - `approved` - Approved by risk manager
  - `rejected` - Rejected by risk manager
- Includes verification queries to confirm the constraint was updated

### 2. Exception Handling (Modified)
**File:** `backend/src/adapter/rest/risk_routes.py`

Added try/catch exception handling to the `create_evaluation` endpoint:
- Catches any exceptions during evaluation creation
- Logs the error with full stack trace
- Re-raises as `HTTPException` with proper 500 status code
- This ensures CORS headers are always present in error responses, preventing cryptic CORS errors in the browser

## Root Cause Analysis

The `AssessmentStatus` enum (line 25 in `risk_dtos.py`) included `PENDING_DOCUMENTS = "pending_documents"`, which was used in the fraud detection service when creating new evaluations. However, the database CHECK constraint (line 40 in `migration_create_risk_tables.sql`) only allowed 6 values and did not include `pending_documents`.

When PostgreSQL rejected the INSERT due to the constraint violation, FastAPI's default exception handler returned a 500 error. Because the exception occurred during request processing (after CORS middleware's request phase), the CORS headers were not added to the error response. The browser then reported this as a CORS error, masking the actual database constraint violation.

## Discrepancies Found

None - the plan accurately identified the root cause and solution.

## Validation Results

- **Backend linting:** `ruff check src/` - All checks passed
- **Frontend linting:** `npm run lint` - 0 errors (4 pre-existing warnings unrelated to this change)
- **TypeScript check:** `npx tsc --noEmit` - Passed
- **Frontend build:** `npm run build` - Successful

## Files Changed

```
 backend/src/adapter/rest/risk_routes.py | 22 +++++++++++++++-------
 1 file changed, 15 insertions(+), 7 deletions(-)
```

## New Files

```
 backend/database/migration_add_pending_documents_status.sql (67 lines)
 specs/issue-none-adw-none-sdlc_planner-fix-risk-evaluation-cors-error.md (157 lines)
```

## Deployment Notes

**IMPORTANT:** The database migration must be applied before the fix will take effect:

1. Open Supabase SQL Editor
2. Copy and paste the contents of `backend/database/migration_add_pending_documents_status.sql`
3. Execute the migration
4. Verify the constraint was updated by checking the output of the verification queries

The migration is safe to apply to production as it only expands the allowed values in the constraint - it does not remove any existing functionality or data.

## Testing

After applying the migration:
1. Navigate to `/risk/dashboard`
2. Click "Nueva Evaluacion"
3. Enter a valid NIT
4. Click "Evaluar"
5. Verify the evaluation is created successfully without CORS errors
