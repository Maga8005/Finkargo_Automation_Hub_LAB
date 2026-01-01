# Patch: Fix CORS error in email-chains-with-validations endpoint

## Metadata
adw_id: `584b6bdd`
review_change_request: `When I go to <Contacto Externo> I get this error in the console and the email validation alerts do not load - CORS policy error on /email-chains-with-validations endpoint`

## Issue Summary
**Original Spec:** N/A (patch for existing implementation)
**Issue:** The `/api/risk/evaluations/{id}/email-chains-with-validations` endpoint fails with a CORS error. The root cause is the backend calling a non-existent method `get_by_assessment_id()` on the EmailChainRepository, causing the server to crash before sending proper CORS headers.
**Solution:** Change the method call from `get_by_assessment_id()` to `get_by_assessment()` which is the correct method name defined in `EmailChainRepository`.

## Files to Modify
Use these files to implement the patch:

1. `backend/src/adapter/rest/risk_routes.py` - Fix method call at lines 2523 and 2759

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix email_chain_repo method call (already done)
- Line 2523: Change `await email_chain_repo.get_by_assessment_id(id)` to `await email_chain_repo.get_by_assessment(id)`
- This is in the `get_email_chains_with_validations` function

### Step 2: Fix external_contact_repo method call (already done)
- Line 2759: Change `await external_contact_repo.get_by_assessment_id(id)` to `await external_contact_repo.get_by_assessment(id)`
- This is in the `get_external_contacts_with_validations` function

### Step 3: Restart backend server
- The changes have already been made in the working directory
- User must restart the backend server to pick up the changes:
  ```bash
  cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8003
  ```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Verify method calls are correct**: `cd backend && grep -n "get_by_assessment" src/adapter/rest/risk_routes.py | grep -E "(email_chain_repo|external_contact_repo)" | head -5`
2. **Verify no get_by_assessment_id calls remain**: `cd backend && grep -n "get_by_assessment_id" src/adapter/rest/risk_routes.py || echo "No occurrences found - OK"`
3. **Backend linting**: `cd backend && ./venv/bin/ruff check src/adapter/rest/risk_routes.py`
4. **Repository import validation**: `cd backend && python -c "from src.repositorio.risk_repository import EmailChainRepository; print('Repository OK')"`
5. **Manual test**: Restart the backend server and navigate to Contacto Externo page - should load without CORS errors

## Patch Scope
**Lines of code to change:** 2 (already changed, uncommitted)
**Risk level:** low
**Testing required:** Restart backend server and verify email chains load in Contacto Externo tab
