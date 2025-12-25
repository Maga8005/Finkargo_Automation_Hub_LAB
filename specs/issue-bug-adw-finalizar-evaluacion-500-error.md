# Bug: Finalizar Evaluación returns 500 error due to missing database columns

## Bug Description
When users click "Finalizar Evaluación" button on the Risk Evaluation Detail page, the application returns a 500 Internal Server Error with the message "Request failed with status code 500". The finalization workflow is designed to run all deferred fraud checks, calculate the final risk score, and update the assessment status, but fails during the database update operation.

**Symptoms:**
- User clicks "Finalizar Evaluación" button
- Dialog confirms finalization
- Spinner shows "Finalizando..."
- Error alert appears: "Error al finalizar la evaluación"
- Browser console shows: "Request failed with status code 500"
- Backend logs show database column error

**Expected Behavior:**
- Finalization completes successfully
- Risk score is calculated incorporating all validation results
- Status updates to completed/pending/escalated/rejected
- Success message appears: "Evaluación finalizada exitosamente"
- Assessment detail page shows updated score and status

## Problem Statement
The `finalize_evaluation_complete()` method in `fraud_detection_service.py` attempts to update three columns (`verification_status`, `has_discrepancies`, `discrepancy_count`) that don't exist in the `risk_assessments` database table. The migration `migration_add_finalization_workflow.sql` only adds `finalized_by` and `finalized_at` columns, but the verification-related columns were never added.

## Solution Statement
Create a new database migration to add the missing columns to the `risk_assessments` table:
- `verification_status VARCHAR(50)` - Stores 'pass' or 'requires_manual_verification'
- `has_discrepancies BOOLEAN` - Boolean flag for whether discrepancies were found
- `discrepancy_count INTEGER` - Count of triggered indicators/discrepancies

This is a minimal fix that adds the missing columns without modifying any business logic or service code.

## Steps to Reproduce
1. Log in as a user with `risk_analyst` or `risk_manager` role
2. Navigate to Risk Dashboard (/department/riesgo)
3. Create a new evaluation or select an existing one with status `pending_documents` or `pending_finalization`
4. Upload at least 2 documents (RUT, Bank Certificate, etc.)
5. Run cross-validation on the documents
6. Click "Finalizar Evaluación" button
7. Confirm in the dialog
8. **OBSERVE**: 500 error appears instead of successful finalization

## Root Cause Analysis
The root cause is a **data contract mismatch** between the service layer and the database schema:

1. **Service Layer** (`fraud_detection_service.py`, lines 881-893): The `finalize_evaluation_complete()` method builds an update payload with:
   ```python
   update_data = {
       'risk_score': float(final_score),
       'risk_level': final_level.value,
       'fraud_indicators': [...],
       'status': final_status,
       'verification_status': verification_status,  # MISSING COLUMN
       'has_discrepancies': has_discrepancies,       # MISSING COLUMN
       'discrepancy_count': discrepancy_count,       # MISSING COLUMN
       'finalized_by': user_id,
       'finalized_at': datetime.utcnow().isoformat(),
       'updated_at': datetime.utcnow().isoformat(),
   }
   ```

2. **Database Schema** (`migration_create_risk_tables.sql`, `migration_add_finalization_workflow.sql`): The `risk_assessments` table only has:
   - Core columns: id, assessment_id, client_nit, risk_level, risk_score, fraud_indicators, status, etc.
   - Finalization columns: finalized_by, finalized_at (added in workflow migration)
   - **Missing**: verification_status, has_discrepancies, discrepancy_count

3. **Error Flow**: When Supabase tries to update non-existent columns, PostgreSQL returns an error which propagates as a 500 Internal Server Error through FastAPI.

## Affected Layer
- [x] Backend: adapter/rest (API routes) - Error handling in finalize endpoint
- [x] Backend: core/servicios (business logic) - finalize_evaluation_complete method
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/database/migration_add_finalization_workflow.sql` - Existing migration that added finalized_by/finalized_at columns. Reference for creating new migration.
- `backend/database/migration_create_risk_tables.sql` - Original risk tables schema. Shows current columns in risk_assessments table.
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Contains `finalize_evaluation_complete()` method that uses the missing columns (lines 881-893).
- `backend/src/interface/risk_dtos.py` - Contains `VerificationStatus` enum and `FinalizationRequirements` dataclass to verify column values.

### New Files

- `backend/database/migration_add_verification_status_columns.sql` - New migration to add the missing columns.
- `.claude/commands/e2e/test_finalize_evaluation.md` - E2E test to validate finalization workflow works.

## Step by Step Tasks

### Task 1: Create Database Migration for Missing Columns

- Create new migration file: `backend/database/migration_add_verification_status_columns.sql`
- Add the following columns to `risk_assessments` table:
  - `verification_status VARCHAR(50)` - to store 'pass' or 'requires_manual_verification' values
  - `has_discrepancies BOOLEAN DEFAULT FALSE` - boolean flag for discrepancy presence
  - `discrepancy_count INTEGER DEFAULT 0` - count of discrepancies found
- Add appropriate indexes for query performance
- Add column comments for documentation
- Include verification queries to confirm migration success

### Task 2: Create E2E Test for Finalization Workflow

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_risk_score_after_validation.md` for reference
- Create new E2E test file: `.claude/commands/e2e/test_finalize_evaluation.md`
- Test steps should include:
  1. Login as risk_analyst
  2. Navigate to Risk Dashboard
  3. Create or select an evaluation with pending_finalization status
  4. Click "Finalizar Evaluación" button
  5. Confirm in dialog
  6. **Verify** success message appears (not error)
  7. **Verify** status changes from pending_finalization to completed/pending/escalated
  8. **Verify** risk score and level are displayed
  9. Take screenshots of each step

### Task 3: Apply Migration to Database

- Execute the migration SQL in Supabase SQL Editor
- Verify columns were added correctly with:
  ```sql
  SELECT column_name, data_type, column_default
  FROM information_schema.columns
  WHERE table_name = 'risk_assessments'
  AND column_name IN ('verification_status', 'has_discrepancies', 'discrepancy_count');
  ```

### Task 4: Run Validation Commands

- Run all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Pre-fix verification (should fail before migration):**
```bash
# Test finalization endpoint - should return 500 before fix
curl -X POST "http://localhost:8000/api/risk/evaluations/{evaluation_id}/finalize" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{"force_complete": true}'
```

**Post-fix verification:**
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

**E2E Test validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_finalize_evaluation.md` test file to validate this functionality works.

**Database verification:**
```sql
-- Verify columns exist
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'risk_assessments'
AND column_name IN ('verification_status', 'has_discrepancies', 'discrepancy_count');

-- Should return 3 rows
```

## Notes

- This bug was introduced when the `finalize_evaluation_complete()` method was enhanced to track verification status and discrepancy counts, but the corresponding database migration was not created.
- The fix is purely at the database layer - no Python or TypeScript code changes are needed.
- After applying the migration, existing assessments will have NULL for verification_status and FALSE/0 for the boolean/integer columns, which is acceptable for historical data.
- The migration should be added to the deployment documentation or migration order in README.md if applicable.
- Consider adding a check in the codebase to prevent similar data contract mismatches in the future.
