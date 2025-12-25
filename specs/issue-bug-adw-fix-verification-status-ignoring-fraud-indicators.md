# Bug: Verification Status Shows "APROBADO" When Fraud Indicators Are Triggered

## Bug Description
The Risk Evaluation Detail page and PDF report show "APROBADO" (green checkmark) as the verification status even when there are triggered fraud indicators (alerts). The business requirement is that ANY triggered fraud indicator should result in "FALLIDO-REQUIERE REVISIÓN" (red warning) status requiring manual verification.

**Symptoms:**
- Evaluation shows "Estado de Verificación: APROBADO" (green)
- PDF report shows "RESULTADO DE EVALUACIÓN: APROBADO" (green)
- But there are 2 "Alertas Detectadas" shown in red box
- The alerts are CRITICAL severity (email domain validation issues)

**Expected Behavior:**
- When ANY fraud indicator is triggered (indicator_value=True), the verification status should be "FALLIDO-REQUIERE REVISIÓN" (red)
- The PDF report should show "RESULTADO DE EVALUACIÓN: FALLIDO-REQUIERE REVISIÓN" (red)
- Only when there are ZERO triggered fraud indicators AND ZERO cross-validation discrepancies should the status be "APROBADO"

## Problem Statement
The `_compute_verification_info_async` function in `risk_routes.py` recalculates the verification status by **only checking cross-validation discrepancies**, completely ignoring:
1. The stored `verification_status` in the database (set correctly during finalization)
2. Triggered fraud indicators (alerts)

This causes the verification status to show "APROBADO" when there are 0 cross-validation discrepancies, even if there are multiple critical fraud alerts.

## Solution Statement
Modify `_compute_verification_info_async` and `_compute_verification_info` to also check fraud indicators from the assessment data. The function should:
1. First check if there are any triggered fraud indicators (indicator_value=True)
2. Then check if there are any cross-validation discrepancies
3. If EITHER has any triggered/discrepancy, return `REQUIRES_MANUAL_VERIFICATION`
4. Only return `PASS` if BOTH have zero issues

Alternative approach: Use the stored verification_status from the database when available (set during finalization), and only compute it dynamically if not yet finalized.

## Steps to Reproduce
1. Log in as risk_analyst or risk_manager
2. Navigate to Risk Dashboard (/department/riesgo)
3. Open evaluation RISK-2025-023 (or any evaluation with triggered fraud indicators)
4. **OBSERVE**: "Estado de Verificación" shows "APROBADO" (green) despite having 2 alerts
5. Click "Generar Reporte" to export PDF
6. **OBSERVE**: PDF shows "RESULTADO DE EVALUACIÓN: APROBADO" despite listing 2 triggered fraud indicators

## Root Cause Analysis
The root cause is in `backend/src/adapter/rest/risk_routes.py`:

**`_compute_verification_info_async` (lines 621-646):**
```python
async def _compute_verification_info_async(assessment_id: str) -> dict:
    validation_repo = get_validation_repo()
    results = await validation_repo.get_by_assessment(assessment_id)

    discrepancy_count = sum(1 for r in results if r.get('is_discrepancy', False))
    has_discrepancies = discrepancy_count > 0
    verification_status = (
        VerificationStatus.REQUIRES_MANUAL_VERIFICATION
        if has_discrepancies
        else VerificationStatus.PASS
    )
    # ...
```

This function:
1. Only queries `risk_cross_validation_results` table for discrepancies
2. Does NOT check `fraud_indicators` from the assessment
3. Does NOT use the stored `verification_status` from `risk_assessments` table (which IS set correctly during finalization)

Meanwhile, the finalization code in `fraud_detection_service.py` (lines 866-874) correctly sets:
```python
triggered_indicators = [ind for ind in indicators if ind.indicator_value]
has_any_alert = len(triggered_indicators) > 0
verification_status = 'requires_manual_verification' if has_any_alert else 'pass'
```

But this stored value is ignored when the evaluation is loaded.

## Affected Layer
- [x] Backend: adapter/rest (API routes) - `_compute_verification_info_async`, `_compute_verification_info`
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/adapter/rest/risk_routes.py` - Contains `_compute_verification_info_async` (lines 621-646) and `_compute_verification_info` (lines 575-604) functions that need to be updated to also check fraud indicators or use stored values.
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Reference for correct verification logic during finalization (lines 866-874). Shows how fraud indicators should be checked.
- `frontend/src/types/risk.ts` - Contains `VERIFICATION_STATUS_CONFIG` showing the correct labels for each status.

### Reference Files (for E2E test creation)
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_finalize_evaluation.md` - Related E2E test for finalization

### New Files
- `.claude/commands/e2e/test_verification_status_with_alerts.md` - E2E test to validate verification status is correct when fraud indicators are triggered

## Step by Step Tasks

### Task 1: Update `_compute_verification_info_async` to Use Stored Values or Check Fraud Indicators

- Open `backend/src/adapter/rest/risk_routes.py`
- Locate `_compute_verification_info_async` function (line 621)
- Modify the function to:
  - Accept the assessment data as a parameter (or fetch it)
  - Check if the assessment has stored `verification_status` (from finalization)
  - If stored value exists and assessment is finalized, use it
  - Otherwise, compute verification status considering BOTH:
    - Cross-validation discrepancies (existing logic)
    - Triggered fraud indicators (fraud_indicators where indicator_value=True)
  - Count discrepancies should include BOTH cross-validation discrepancies AND triggered fraud indicators

### Task 2: Update `_compute_verification_info` Synchronous Version

- In the same file, locate `_compute_verification_info` function (line 575)
- Apply the same logic changes as Task 1
- This is the synchronous version used in some mapping functions

### Task 3: Update Callers to Pass Assessment Data

- Update calls to `_compute_verification_info_async` in `get_evaluation`, `list_evaluations`, etc.
- Pass the assessment data so the function can check fraud indicators
- Example locations:
  - Line 262: `verification_info = await _compute_verification_info_async(eval_data['id'])`
  - Line 295: `verification_info = await _compute_verification_info_async(id)`
  - Line 378: `verification_info = await _compute_verification_info_async(id)`
  - Line 1359: `verification_info = await _compute_verification_info_async(id)`

### Task 4: Create E2E Test for Verification Status with Alerts

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_finalize_evaluation.md` for reference
- Create new E2E test file: `.claude/commands/e2e/test_verification_status_with_alerts.md`
- Test steps should include:
  1. Login as risk_analyst
  2. Navigate to an evaluation with triggered fraud indicators (e.g., RISK-2025-023)
  3. **Verify** "Estado de Verificación" shows "FALLIDO-REQUIERE REVISIÓN" (red)
  4. Click "Generar Reporte"
  5. **Verify** PDF shows "RESULTADO DE EVALUACIÓN: FALLIDO-REQUIERE REVISIÓN" (red)
  6. Take screenshots showing the correct red status

### Task 5: Run Validation Commands

- Run all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Pre-fix verification (should show bug):**
- Navigate to evaluation RISK-2025-023 → observe green "APROBADO" despite alerts

**Post-fix verification:**
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

**Manual verification:**
- Navigate to evaluation RISK-2025-023
- **Verify** "Estado de Verificación" shows "FALLIDO-REQUIERE REVISIÓN" (red)
- Click "Generar Reporte"
- **Verify** PDF shows "RESULTADO DE EVALUACIÓN: FALLIDO-REQUIERE REVISIÓN" (red)
- **Verify** evaluations with 0 alerts AND 0 discrepancies still show "APROBADO"

**E2E Test validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_verification_status_with_alerts.md` test file to validate this functionality works.

## Notes

- The finalization code in `fraud_detection_service.py` is correct - it properly sets `verification_status = 'requires_manual_verification'` when any fraud indicator is triggered
- The bug is that this stored value is ignored when the evaluation is loaded for display
- The simplest fix is to use the stored `verification_status` from the database when available, falling back to computing it only when needed
- The `discrepancy_count` field should probably be renamed or semantically clarified - it currently represents "triggered_indicators" count in finalization but "cross_validation_discrepancies" count in the compute function
- Consider adding a separate `triggered_alerts_count` field for clarity in future
