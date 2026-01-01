# Patch: Fix cross_validation_results table reference in migration

## Metadata
adw_id: `6a9aabdc`
review_change_request: `when running migration_add_discrepancy_validations.sql, I get this error Error: Failed to run sql query: ERROR: 42P01: relation "cross_validation_results" does not exist`

## Issue Summary
**Original Spec:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md
**Issue:** The migration file `migration_add_discrepancy_validations.sql` references `cross_validation_results` table on line 11, but the actual table name is `risk_cross_validation_results` (created in `migration_add_document_extractions_table.sql`)
**Solution:** Update the foreign key reference from `cross_validation_results(id)` to `risk_cross_validation_results(id)`

## Files to Modify
Use these files to implement the patch:

- `backend/database/migration_add_discrepancy_validations.sql` - Fix table reference

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix foreign key reference in discrepancy_validations table
- Open `backend/database/migration_add_discrepancy_validations.sql`
- On line 11, change `cross_validation_results(id)` to `risk_cross_validation_results(id)`
- This aligns with the actual table name defined in `migration_add_document_extractions_table.sql`

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. Review the migration file to confirm the table reference is correct
2. `cd backend && ruff check src/` - Run backend linting
3. `cd frontend && npm run lint` - Run frontend linting
4. `cd frontend && npx tsc --noEmit` - Run TypeScript type check
5. `cd frontend && npm run build` - Run frontend build to validate production compilation

## Patch Scope
**Lines of code to change:** 1
**Risk level:** low
**Testing required:** Re-run the SQL migration in Supabase to confirm no errors
