# Implementation Report: Default verification status to PENDING for incomplete evaluations

**Date:** 2025-12-25
**ADW ID:** a89d9b6e
**Patch Plan:** specs/patch/patch-adw-a89d9b6e-verification-status-pending-default.md

## Summary

Fixed the issue where new risk evaluations with incomplete document uploads incorrectly showed "APROBADO" (PASS) in the Verificación column on the RiskDashboard. The fix ensures that incomplete evaluations now correctly display "PENDIENTE" (PENDING) status.

## Changes Made

- **Added `PENDING` status to `VerificationStatus` enum** (`backend/src/interface/risk_dtos.py:73`)
  - Added `PENDING = "pending"` as the first value in the enum
  - Updated docstring to reflect all three states

- **Updated `_compute_verification_info` function** (`backend/src/adapter/rest/risk_routes.py:575-681`)
  - Added check for `pending_documents` status before computing verification info
  - Returns `PENDING` status when assessment is not finalized
  - Applied same logic in both sync path (when running loop exists) and async path

- **Updated `_compute_verification_info_async` function** (`backend/src/adapter/rest/risk_routes.py:684-749`)
  - Added check for `pending_documents` status after stored status check
  - Returns `PENDING` status when assessment is not finalized

- **Updated default verification_info in mapping functions**
  - `_map_to_response` (`backend/src/adapter/rest/risk_routes.py:752-779`): Default changed from `PASS` to `PENDING`
  - `_map_to_detail` (`backend/src/adapter/rest/risk_routes.py:782-829`): Default changed from `PASS` to `PENDING`

## Verification Logic Priority

The updated verification computation now follows this priority:
1. If assessment has stored `verification_status` (from finalization) → use it
2. If assessment status is `pending_documents` → return `PENDING`
3. Otherwise → compute based on fraud indicators and cross-validation discrepancies

## Discrepancies Found

None. The plan accurately described the file locations and code structure.

## Files Changed

```
backend/src/adapter/rest/risk_routes.py | 43 +++++++++++++++++++++++++++------
backend/src/interface/risk_dtos.py      |  3 ++-
2 files changed, 38 insertions(+), 8 deletions(-)
```

## Validation Results

- Python syntax validation: PASSED
- Frontend linting: PASSED (only pre-existing warnings)
- TypeScript type check: PASSED
- Frontend build: PASSED

## Testing Required

Manual verification:
1. Create a new evaluation via the RiskDashboard
2. Do not upload any documents
3. Verify the RiskDashboard shows "PENDIENTE" in the Verificación column instead of "APROBADO"
4. Finalize an evaluation with documents to verify it correctly shows "APROBADO" or "REQUIERE VERIFICACIÓN"
