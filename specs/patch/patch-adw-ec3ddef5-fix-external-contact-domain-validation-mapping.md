# Patch: Fix External Contact Domain Validation Mapping

## Metadata
adw_id: `ec3ddef5`
review_change_request: `when validating the email domain using <contactos externos individuales> the app throws an error 500`

## Issue Summary
**Original Spec:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md
**Issue:** The `_map_to_external_contact_response()` function in `risk_routes.py` is missing the domain validation fields when constructing the `EmailValidationResult` object, causing a 500 error when domain validation data is present in the database.
**Solution:** Add the missing domain validation fields (`domain_exists`, `domain_age_days`, `domain_creation_date`, `age_lookup_status`, `domain_registrar`) to the `EmailValidationResult` mapping.

## Files to Modify
Use these files to implement the patch:

- `backend/src/adapter/rest/risk_routes.py` (lines 1668-1696) - Add missing domain validation fields to `_map_to_external_contact_response()` function

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_map_to_external_contact_response` function
- Read `backend/src/adapter/rest/risk_routes.py`
- Locate `_map_to_external_contact_response` function (around line 1668)
- Update the `EmailValidationResult` construction to include all domain validation fields:
  - Add `domain_exists=vr.get('domain_exists')`
  - Add `domain_age_days=vr.get('domain_age_days')`
  - Add `domain_creation_date=_parse_datetime(vr.get('domain_creation_date'))` (parse the datetime properly)
  - Add `age_lookup_status=vr.get('age_lookup_status', 'pending')`
  - Add `domain_registrar=vr.get('domain_registrar')`

### Step 2: Verify the fix
- Ensure the fields match what's defined in `EmailValidationResult` in `backend/src/interface/risk_dtos.py` (lines 560-575)
- Confirm `_parse_datetime` helper is used for the `domain_creation_date` field

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && ./venv/bin/ruff check src/adapter/rest/risk_routes.py` - Verify no linting errors
2. `cd backend && python -c "from src.adapter.rest.risk_routes import _map_to_external_contact_response; print('Import OK')"` - Verify function imports correctly
3. `cd backend && python -m pytest tests/test_external_contact_service.py -v --tb=short` - Run external contact service tests
4. `cd frontend && npm run build` - Verify frontend build succeeds

## Patch Scope
**Lines of code to change:** ~5-7 lines
**Risk level:** low
**Testing required:** Validate external contact email domain validation works without 500 error
