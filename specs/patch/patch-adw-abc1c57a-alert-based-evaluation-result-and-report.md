# Patch: Alert-Based Evaluation Result and Comprehensive Report

## Metadata
adw_id: `abc1c57a`
review_change_request: `Even though there were alerts for typosquatting and domain not existing or domain being very young, the evaluation resulted in <Aprobado>. Any time there is an alert, the result of the evaluation when clicking <Finalizar Evaluación> should be <Fallido-Requiere Revisión> in red font. Additionally, after finalizing the process, the user should be able to generate a report that displays the full evaluation. It should be similar to the report available in Cross Check, but with the additional information from the alerts or review from <contacto externo>.`

## Issue Summary
**Original Spec:** specs/issue-34-adw-abc1c57a-sdlc_planner-defer-fraud-checks-finalization.md
**Issue:** When alerts exist (typosquatting, domain not existing, young domain), the finalized evaluation shows "APROBADO" instead of "FALLIDO-REQUIERE REVISIÓN" in red. Also missing comprehensive report that includes all validation results (cross-validation, external contacts, alerts).
**Solution:** (1) Update `finalize_evaluation_complete()` to set `requires_manual_verification` status when any fraud indicators are triggered (not just based on score), (2) Update `FKVerificationStatusCard` to display "FALLIDO-REQUIERE REVISIÓN" in red for this status, (3) Add comprehensive PDF report export that includes cross-validation results, external contact alerts, and all fraud indicators.

## Files to Modify
Use these files to implement the patch:

1. `backend/src/core/servicios/risk/fraud_detection_service.py` - Update `finalize_evaluation_complete()` to set `requires_manual_verification` when any indicator is triggered
2. `frontend/src/types/risk.ts` - Update `VERIFICATION_STATUS_CONFIG` to use "FALLIDO-REQUIERE REVISIÓN" label in red
3. `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Add "Generar Reporte" button after finalization
4. `frontend/src/utils/crossValidationPdfExport.ts` - Create new `exportComprehensiveEvaluationReport()` function

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Verification Status Label and Colors
- Edit `frontend/src/types/risk.ts`
- Change `requires_manual_verification` config from `label: 'REQUIERE VERIFICACIÓN MANUAL'` to `label: 'FALLIDO-REQUIERE REVISIÓN'`
- Keep existing red colors (`bgColor: '#FFE4E4'`, `textColor: '#CC071E'`) - they are already correct

### Step 2: Update `finalize_evaluation_complete()` to Set Correct Verification Status
- Edit `backend/src/core/servicios/risk/fraud_detection_service.py`
- In `finalize_evaluation_complete()`, after calculating `final_score` and before updating assessment:
  - Check if ANY fraud indicator has `indicator_value=True` (meaning alert was triggered)
  - If any indicator is triggered, set `verification_status = 'requires_manual_verification'`
  - If no indicators triggered, set `verification_status = 'pass'`
- Add `verification_status` and `has_discrepancies`, `discrepancy_count` to the `update_data` dict
- The `discrepancy_count` should be the count of triggered indicators

### Step 3: Create Comprehensive Evaluation Report Export Function
- Edit `frontend/src/utils/crossValidationPdfExport.ts`
- Add new interface `ComprehensiveReportContext` that extends `AssessmentContext` with:
  - `risk_score: number`
  - `risk_level: string`
  - `verification_status: string`
  - `fraud_indicators: FraudIndicator[]`
  - `external_contacts?: ExternalContact[]`
- Create new function `exportComprehensiveEvaluationReport()`:
  - Accept: `results: CrossValidationResponse`, `assessment: ComprehensiveReportContext`
  - Generate PDF with sections:
    1. Header (same as cross-validation report)
    2. Evaluation Summary (NIT, company, finalized by/at, verification status)
    3. Risk Assessment (verification status prominently displayed, risk indicators count)
    4. Fraud Indicators Table (indicator name, severity, evidence, triggered status)
    5. Cross-Validation Results (reuse existing table generation)
    6. External Contact Alerts (if any contacts have suspicious/critical status)
    7. Final Recommendation (based on verification status)

### Step 4: Add "Generar Reporte" Button to RiskEvaluationDetail
- Edit `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Import `exportComprehensiveEvaluationReport` from `crossValidationPdfExport.ts`
- In the Evaluación tab (activeTab === 3), after the FKVerificationStatusCard:
  - Add a "Generar Reporte Completo" button
  - Button should only be visible when assessment status is finalized (not `pending_documents` or `pending_finalization`)
  - On click, call `exportComprehensiveEvaluationReport()` with current assessment data and validation results
- Add state to store external contacts for the report (fetch them when loading assessment)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && ./venv/bin/ruff check src/` - Run backend linting
2. `cd frontend && npm run lint` - Run frontend linting
3. `cd frontend && npx tsc --noEmit` - Run TypeScript type check
4. `cd frontend && npm run build` - Run frontend build to validate production compilation

## Patch Scope
**Lines of code to change:** ~150 lines
**Risk level:** medium
**Testing required:** Manual verification that (1) finalized evaluations with alerts show "FALLIDO-REQUIERE REVISIÓN" in red, (2) "Generar Reporte" button appears after finalization, (3) PDF report includes all validation sections including external contact alerts
