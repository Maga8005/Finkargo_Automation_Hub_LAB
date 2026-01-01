# Patch: Fix risk_email_chains table reference in migration

## Metadata
adw_id: `584b6bdd`
review_change_request: `When running "migration_add_external_communication_validations.sql" I get the error: Error: Failed to run sql query: ERROR: 42P01: relation "risk_email_chains" does not exist`

## Issue Summary
**Original Spec:** specs/issue-65-adw-584b6bdd-sdlc_planner-external-communication-validation-comments.md
**Issue:** The migration file `migration_add_external_communication_validations.sql` references a non-existent table `risk_email_chains`. The actual table is named `email_chains` as defined in `migration_add_email_chains_table.sql`.
**Solution:** Update the migration to reference the correct table name `email_chains` instead of `risk_email_chains`. Also update the repository code that incorrectly uses `risk_email_chains`.

## Files to Modify
Use these files to implement the patch:

1. `backend/database/migration_add_external_communication_validations.sql` - Fix foreign key reference from `risk_email_chains` to `email_chains`
2. `backend/src/repositorio/risk_repository.py` - Fix table references from `risk_email_chains` to `email_chains` (lines 1435, 1531)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix migration SQL file
- Open `backend/database/migration_add_external_communication_validations.sql`
- Change line 14 foreign key reference from `REFERENCES risk_email_chains(id)` to `REFERENCES email_chains(id)`
- Update comments if they reference the incorrect table name

### Step 2: Fix repository code
- Open `backend/src/repositorio/risk_repository.py`
- Change line 1435: `self.db.table('risk_email_chains')` to `self.db.table('email_chains')`
- Change line 1531: `self.db.table('risk_email_chains')` to `self.db.table('email_chains')`

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Verify SQL syntax**: `cd backend && cat database/migration_add_external_communication_validations.sql | grep -i "email_chains"` - Should show `email_chains` (not `risk_email_chains`)
2. **Verify repository code**: `cd backend && grep -n "email_chains" src/repositorio/risk_repository.py` - All references should be to `email_chains`
3. **Backend linting**: `cd backend && ./venv/bin/ruff check src/`
4. **Backend tests**: `cd backend && python -m pytest -v --tb=short`
5. **Repository import validation**: `cd backend && python -c "from src.repositorio.risk_repository import *; print('Repository OK')"`

## Patch Scope
**Lines of code to change:** 3
**Risk level:** low
**Testing required:** Run migration in Supabase SQL Editor after applying patch, verify backend tests pass
