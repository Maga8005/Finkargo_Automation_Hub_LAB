# Implementation Report: Fix CORS Error in Email-Chains-With-Validations Endpoint

**Date:** 2026-01-01
**ADW ID:** 584b6bdd
**Module:** Risk
**Type:** Patch/Bug Fix

## Summary

Fixed a CORS error in the `/api/risk/evaluations/{id}/email-chains-with-validations` and `/api/risk/evaluations/{id}/external-contacts-with-validations` endpoints caused by calling non-existent repository methods.

## Changes Made

- **Line 2523:** Changed `await email_chain_repo.get_by_assessment_id(id)` to `await email_chain_repo.get_by_assessment(id)` in the `get_email_chains_with_validations` function
- **Line 2759:** Changed `await external_contact_repo.get_by_assessment_id(id)` to `await external_contact_repo.get_by_assessment(id)` in the `get_external_contacts_with_validations` function

## Root Cause

The backend was calling `get_by_assessment_id()` which does not exist on `EmailChainRepository` and `ExternalContactRepository`. The correct method name is `get_by_assessment()`. This caused the server to crash before it could send proper CORS headers, resulting in the browser reporting a CORS error instead of the actual 500 server error.

## Discrepancies from Plan

**None.** The plan accurately described the issue and solution. The changes were already staged in the working directory as indicated in the plan.

## Validation

1. **Ruff linting:** Passed with no errors
2. **Method verification:** Confirmed `get_by_assessment()` is used at lines 2523 and 2759
3. **No regression:** Confirmed no `get_by_assessment_id()` calls remain in risk_routes.py

## Files Changed

```
backend/src/adapter/rest/risk_routes.py | 4 ++--
1 file changed, 2 insertions(+), 2 deletions(-)
```

## Testing Required

1. Restart the backend server
2. Navigate to the "Contacto Externo" tab in a risk evaluation
3. Verify email validation alerts load without CORS errors
