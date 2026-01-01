# Bug Fix: Validation Status Enum Case Mismatch

**Date:** 2026-01-01
**Specification:** specs/bug/bug-adw-584b6bdd-email-chain-validation-status-enum.md

## Summary

Fixed `AttributeError` exceptions in the Riesgos module's External Communication endpoints caused by incorrect enum member name casing. Both `EmailChainValidationStatus` and `ExternalContactValidationStatus` enums were affected.

## What Was Fixed

- **Root Cause:** Both enums are defined with uppercase member names (`PENDING`, `VALIDATED`) but the code in `risk_routes.py` was incorrectly using lowercase (`pending`, `validated`)
- **Symptom:** Browser showed CORS errors, but the actual issue was 500 Internal Server Errors in the backend
- **Fix:** Changed 6 enum references from lowercase to uppercase

## Changes Made

### EmailChainValidationStatus (Initial Fix)
- **Line 2601:** `EmailChainValidationStatus.pending` → `EmailChainValidationStatus.PENDING`
- **Line 2623:** `EmailChainValidationStatus.pending` → `EmailChainValidationStatus.PENDING`
- **Line 2624:** `EmailChainValidationStatus.validated` → `EmailChainValidationStatus.VALIDATED`

### ExternalContactValidationStatus (Additional Fix)
- **Line 2794:** `ExternalContactValidationStatus.pending` → `ExternalContactValidationStatus.PENDING`
- **Line 2818:** `ExternalContactValidationStatus.pending` → `ExternalContactValidationStatus.PENDING`
- **Line 2819:** `ExternalContactValidationStatus.validated` → `ExternalContactValidationStatus.VALIDATED`

## Discrepancies Found

- **Plan identified 2 fixes (lines 2623-2624)**, but during verification found:
  - **1 additional fix at line 2601** for EmailChainValidationStatus
  - **3 additional fixes at lines 2794, 2818, 2819** for ExternalContactValidationStatus
- Both enums had identical bugs from the same implementation pattern

## Files Changed

```
backend/src/adapter/rest/risk_routes.py | 12 ++++++------
1 file changed, 6 insertions(+), 6 deletions(-)
```

## Validation Results

- ✅ Backend linting: `ruff check src/` - All checks passed
- ✅ Frontend linting: `npm run lint` - 0 errors (4 pre-existing warnings)
- ✅ TypeScript check: `npx tsc --noEmit` - Passed
- ✅ Frontend build: `npm run build` - Built successfully
- ✅ No remaining lowercase enum references found

## Testing

The backend server was restarted and is now running on port 8003. Both endpoints in the "Contacto Externo" tab should now load without CORS/500 errors:
- `/api/risk/evaluations/{id}/email-chains-with-validations`
- `/api/risk/evaluations/{id}/external-contacts-with-validations`
