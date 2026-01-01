# Patch: Fix CORS error by restarting backend server

## Metadata
adw_id: `584b6bdd`
review_change_request: `CORS policy error on /email-chains-with-validations endpoint when accessing Contacto Externo tab`

## Issue Summary
**Original Spec:** N/A (patch for existing implementation)
**Issue:** The `/api/risk/evaluations/{id}/email-chains-with-validations` endpoint fails with a CORS error. Previous patches (commits a9e3f9d, 615cad5, 6ffeab0) corrected the repository method calls from `get_by_assessment_id()` to `get_by_assessment()`. However, the user is still seeing the error, which indicates the backend server needs to be restarted to pick up the changes.
**Solution:** Restart the backend server. If the issue persists, verify the database migrations have been applied.

## Files to Modify
No code changes required - the fixes have already been applied:

1. `backend/src/adapter/rest/risk_routes.py` - Lines 2523 and 2759 already use correct `get_by_assessment()` method

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify current code is correct
- Check that line 2523 uses `await email_chain_repo.get_by_assessment(id)`
- Check that line 2759 uses `await external_contact_repo.get_by_assessment(id)`

Command to verify:
```bash
grep -n "get_by_assessment" backend/src/adapter/rest/risk_routes.py | grep -E "2523|2759"
```

Expected output:
```
2523:    chains = await email_chain_repo.get_by_assessment(id)
2759:    contacts = await external_contact_repo.get_by_assessment(id)
```

### Step 2: Restart the backend server
- Stop any running uvicorn process on port 8003
- Start the backend server with:
```bash
cd backend
# Windows: kill any process on port 8003 first
# Linux/Mac: lsof -ti :8003 | xargs kill -9 2>/dev/null || true

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8003
```

### Step 3: Verify database migrations are applied (if error persists)
If the error persists after server restart, the database tables may not exist. Apply the migrations in Supabase SQL Editor:

1. `backend/database/migration_add_email_chains_table.sql` - Creates `email_chains` table
2. `backend/database/migration_add_external_communication_validations.sql` - Creates `email_chain_discrepancy_validations` and `external_contact_validations` tables

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Verify method calls are correct**:
   ```bash
   cd backend && grep -n "get_by_assessment" src/adapter/rest/risk_routes.py | grep -E "email_chain_repo|external_contact_repo" | head -5
   ```

2. **Verify no get_by_assessment_id calls remain**:
   ```bash
   cd backend && grep -n "get_by_assessment_id" src/adapter/rest/risk_routes.py | grep -E "email_chain_repo|external_contact_repo" || echo "No occurrences found - OK"
   ```

3. **Test the endpoint directly**:
   ```bash
   curl -X GET "http://localhost:8003/api/risk/evaluations/ab868d98-2eb3-4a4a-adee-aaed9e1cfa44/email-chains-with-validations" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json"
   ```

4. **Manual browser test**: Navigate to Contacto Externo tab - should load without CORS errors

5. **Check backend logs**: If CORS error persists, check backend terminal for Python exceptions

## Patch Scope
**Lines of code to change:** 0 (code already fixed)
**Risk level:** low
**Testing required:** Restart server and verify Contacto Externo tab loads email chains without errors
