# Patch: Default verification status to PENDING for incomplete evaluations

## Metadata
adw_id: `a89d9b6e`
review_change_request: `"when a new Evaluación is started and the user stops mid way, even when not having uploaded documents, the table in <Gestión de Riesgos y Fraude> shows the record as <Aprobado> in the <Verificación> column. This is incorrect as the evaluation has not been finalized. This should default to <Pendiente> pending until the evaluation is finalized."`

## Issue Summary
**Original Spec:** specs/issue-42-adw-a89d9b6e-sdlc_planner-fraud-excel-export-documents.md
**Issue:** When a new evaluation is created and the user stops midway without uploading/validating documents, the RiskDashboard table incorrectly shows "APROBADO" in the Verificación column. This happens because the backend `VerificationStatus` enum only has `PASS` and `REQUIRES_MANUAL_VERIFICATION` values, and the verification computation logic defaults to `PASS` when there are no discrepancies (which is the case for incomplete evaluations).
**Solution:** Add `PENDING` status to the backend `VerificationStatus` enum and update the verification computation logic in `_compute_verification_info` and `_compute_verification_info_async` to return `PENDING` when the evaluation hasn't been finalized (i.e., no stored verification_status and assessment status is still `pending_documents`).

## Files to Modify
Use these files to implement the patch:

- `backend/src/interface/risk_dtos.py` - Add `PENDING` value to `VerificationStatus` enum
- `backend/src/adapter/rest/risk_routes.py` - Update `_compute_verification_info` and `_compute_verification_info_async` to return `PENDING` for non-finalized evaluations

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add PENDING to VerificationStatus enum
- Open `backend/src/interface/risk_dtos.py`
- Locate the `VerificationStatus` enum (around line 71-74)
- Add `PENDING = "pending"` as the first value in the enum (before PASS)
- This aligns with the frontend's existing `VerificationStatus` type which already includes 'pending'

### Step 2: Update _compute_verification_info function
- Open `backend/src/adapter/rest/risk_routes.py`
- Locate the `_compute_verification_info` function (around line 573)
- After checking for stored verification_status, add logic to check if the assessment status is `pending_documents` or the assessment has not been finalized
- If the assessment is not finalized (status is `pending_documents` and no stored verification_status), return `PENDING` instead of computing based on discrepancies
- The logic should be:
  1. If stored verification_status exists → use it (current behavior)
  2. If assessment status is `pending_documents` → return `PENDING`
  3. Otherwise → compute based on discrepancies (current behavior)

### Step 3: Update _compute_verification_info_async function
- In the same file, locate `_compute_verification_info_async` (around line 665)
- Apply the same logic change as Step 2:
  1. If stored verification_status exists → use it (current behavior)
  2. If assessment status is `pending_documents` → return `PENDING`
  3. Otherwise → compute based on discrepancies (current behavior)

### Step 4: Update default verification_info in mapping functions
- In `_map_to_response` and `_map_to_detail` functions, update the default `verification_info` to use `VerificationStatus.PENDING` instead of `VerificationStatus.PASS`
- This ensures that if no verification_info is passed, the default is `PENDING` (safe fallback)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && python -m py_compile src/main.py` - Validate Python syntax
2. `cd backend && ./venv/bin/ruff check src/` - Backend linting
3. `cd backend && python -m pytest -v --tb=short` - All backend tests
4. `cd frontend && npm run lint` - Frontend linting
5. `cd frontend && npx tsc --noEmit` - TypeScript type check
6. `cd frontend && npm run build` - Frontend build

## Patch Scope
**Lines of code to change:** ~25-35 lines
**Risk level:** low
**Testing required:** Backend unit tests should continue to pass. Manual verification: create a new evaluation, do not upload documents, verify the RiskDashboard shows "PENDIENTE" instead of "APROBADO"
