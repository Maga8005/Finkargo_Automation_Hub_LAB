# Bug: Risk Evaluation CORS Error due to Database Constraint Mismatch

## Bug Description
When a user attempts to create a new risk evaluation in the Risk Dashboard by entering a NIT, the request fails with a CORS error:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/risk/evaluate' from origin 'http://localhost:5173'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

The error appears as a "Network error" in the frontend console, with the AxiosError originating from `RiskDashboard.tsx:126` in the `handleEvaluate` function.

**Expected behavior:** The risk evaluation should be created successfully and the user should be redirected to the evaluation detail page.

**Actual behavior:** The request fails with a CORS error and no evaluation is created.

## Problem Statement
The CORS error is a symptom, not the root cause. The actual problem is a **database CHECK constraint violation** that occurs when the backend tries to insert a risk assessment record with `status: 'pending_documents'`.

The `AssessmentStatus` enum in `backend/src/interface/risk_dtos.py` includes `PENDING_DOCUMENTS = "pending_documents"`, but the database table `risk_assessments` was created with a CHECK constraint that only allows: `'pending', 'in_progress', 'completed', 'escalated', 'approved', 'rejected'`.

When the database throws the constraint violation exception, FastAPI returns a 500 error without CORS headers because the exception occurs after the request is parsed but before the CORS middleware can process the response.

## Solution Statement
Update the database CHECK constraint to include the `pending_documents` status value that is used by the application code. This requires creating a new SQL migration that alters the `risk_assessments` table to expand the allowed values for the `status` column.

## Steps to Reproduce
1. Start the backend server: `cd backend && python -m uvicorn main:app --reload`
2. Start the frontend server: `cd frontend && npm run dev`
3. Login with a user that has `risk_analyst` or `risk_manager` role
4. Navigate to `/risk/dashboard`
5. Click "Nueva Evaluacion" button
6. Enter any valid NIT (e.g., `900123456`)
7. Click "Evaluar"
8. Observe the CORS error in the browser console

## Root Cause Analysis
The root cause is a mismatch between the application code and the database schema:

1. **Application code** (`backend/src/interface/risk_dtos.py:25`):
   ```python
   class AssessmentStatus(str, Enum):
       PENDING = "pending"
       PENDING_DOCUMENTS = "pending_documents"  # <- This value is used in code
       IN_PROGRESS = "in_progress"
       COMPLETED = "completed"
       ESCALATED = "escalated"
       APPROVED = "approved"
       REJECTED = "rejected"
   ```

2. **Database schema** (`backend/database/migration_create_risk_tables.sql:41`):
   ```sql
   status VARCHAR(20) NOT NULL DEFAULT 'pending'
   CHECK (status IN ('pending', 'in_progress', 'completed', 'escalated', 'approved', 'rejected'))
   -- Missing: 'pending_documents' !!
   ```

3. **Usage in fraud_detection_service.py** (lines 139, 516):
   ```python
   'status': AssessmentStatus.PENDING_DOCUMENTS.value,  # Tries to insert 'pending_documents'
   ```

4. When the INSERT fails due to the CHECK constraint, PostgreSQL throws an error. FastAPI's exception handler returns a 500 response, but since the exception happens during request processing (after CORS middleware's request phase but before response phase), the CORS headers are not added to the error response.

5. The browser sees a response without `Access-Control-Allow-Origin` headers and reports it as a CORS error, masking the actual database constraint violation.

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/database/migration_create_risk_tables.sql` - Contains the original CHECK constraint definition (line 41). Reference for understanding the current constraint.
- `backend/src/interface/risk_dtos.py` - Contains the `AssessmentStatus` enum (line 22-30) which defines `PENDING_DOCUMENTS`. This is the source of truth for allowed status values.
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Uses `AssessmentStatus.PENDING_DOCUMENTS.value` when creating new assessments (lines 139, 516). No changes needed here.
- `backend/src/repositorio/risk_repository.py` - Repository that inserts records into `risk_assessments` table. No changes needed.
- `backend/src/adapter/rest/risk_routes.py` - API routes for risk module. May need to add better error handling for database exceptions.

### New Files
- `backend/database/migration_add_pending_documents_status.sql` - New migration to add `pending_documents` to the CHECK constraint

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Database Migration
Create a new SQL migration file to update the CHECK constraint on the `risk_assessments` table:

- Create file: `backend/database/migration_add_pending_documents_status.sql`
- The migration should:
  1. Drop the existing CHECK constraint on the `status` column
  2. Add a new CHECK constraint that includes `pending_documents`
  3. Include verification queries to confirm the constraint was updated
- Reference the existing `AssessmentStatus` enum values from `risk_dtos.py` to ensure all values are included

### Step 2: Apply Migration to Database
- Read the migration file and apply it to the Supabase database
- This should be done via the Supabase SQL Editor or migration tool
- Document the verification steps

### Step 3: Add Exception Handling to Risk Routes (Optional but Recommended)
- Update `backend/src/adapter/rest/risk_routes.py` to catch database exceptions and return proper HTTP error responses with CORS headers
- This ensures that even if a database error occurs, the response includes CORS headers so the frontend can see the actual error message instead of a cryptic CORS error
- Add try/catch around the `create_evaluation` endpoint to handle database constraint violations gracefully

### Step 4: Run Validation Commands
Execute all validation commands to ensure the bug is fixed with zero regressions.

### Step 5: E2E Test Validation
- Read `.claude/commands/test_e2e.md` to understand the E2E test framework
- Read `.claude/commands/e2e/test_risk_dashboard.md` as reference for risk module testing
- Execute the existing risk dashboard E2E test to validate the fix works end-to-end
- The test should now pass Part 3 (Create Risk Evaluation) without CORS errors

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Before Fix (reproduce the bug):**
```bash
# Start backend server and attempt to create an evaluation via curl
curl -X POST http://localhost:8000/api/risk/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{"client_nit": "900123456"}'
# Expected: 500 error with constraint violation message
```

**After Fix:**
```bash
# Verify migration was applied - check the constraint
# Run this in Supabase SQL Editor or via psql:
# SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'risk_assessments'::regclass AND contype = 'c';
# Expected: Should show 'pending_documents' in the status constraint
```

**Standard Validation:**
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

**E2E Test Validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_risk_dashboard.md` E2E test to validate the risk evaluation functionality works end-to-end

## Notes
- The CORS error is a classic symptom of backend exceptions that occur before CORS headers are added. When debugging similar "CORS errors", always check the backend logs first for actual exceptions.
- The `pending_documents` status was added to support a document upload workflow where new evaluations start in this status before documents are uploaded and cross-validated.
- No frontend changes are required - the frontend code is correct and will work once the database constraint is fixed.
- The migration is safe to apply to production as it only expands the allowed values, it doesn't remove any existing functionality.
- Consider adding a global exception handler in FastAPI that ensures CORS headers are always present in error responses to prevent similar debugging confusion in the future.
