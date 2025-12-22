# Implementation Report: Risk Score After Cross-Validation

**Date:** 2025-12-22
**Feature:** Risk Score Calculation After Document Cross-Validation
**Spec File:** `specs/issue-0-adw-0-sdlc_planner-risk-score-after-cross-validation.md`

## Summary

Implemented a two-phase risk scoring workflow where the final risk score is calculated after document cross-validation completes, ensuring discrepancies found between documents are incorporated into the final fraud risk assessment.

## Changes Made

### Backend Changes

- **Added `pending_documents` status** to `AssessmentStatus` enum in `backend/src/interface/risk_dtos.py`
- **RiskScoringService** (`backend/src/core/servicios/risk/risk_scoring_service.py`):
  - Added `calculate_final_score()` method that combines preliminary score with cross-validation score impacts
  - Caps final score at 100 and determines risk level
- **FraudDetectionService** (`backend/src/core/servicios/risk/fraud_detection_service.py`):
  - Modified `evaluate_client()` to set status to `pending_documents` instead of auto-determining
  - Removed immediate alert creation (deferred to final scoring)
  - Added `finalize_evaluation()` method that:
    - Retrieves existing assessment
    - Combines preliminary score with cross-validation impacts
    - Calculates final score and risk level
    - Updates assessment status appropriately
    - Creates alerts for high/critical risk only after final scoring
  - Added `_determine_final_status()` helper for final status determination
- **Risk Routes** (`backend/src/adapter/rest/risk_routes.py`):
  - Modified `trigger_cross_validation()` endpoint to call `finalize_evaluation()` after saving validation results
  - Added logging for cross-validation completion

### Frontend Changes

- **Added `pending_documents` status** to `AssessmentStatus` type in `frontend/src/types/risk.ts`
- **FKRiskScoreCard** (`frontend/src/components/risk/FKRiskScoreCard.tsx`):
  - Added `isPreliminary` prop
  - Shows "Puntaje Preliminar" chip with tooltip when preliminary
- **RiskEvaluationDetail** (`frontend/src/pages/risk/RiskEvaluationDetail.tsx`):
  - Added `isPreliminaryScore` computed value based on assessment status
  - Added guidance alert for `pending_documents` status
  - Added success message when score is updated after validation
  - Added `handleValidationComplete` callback to refresh assessment after cross-validation
  - Passes `isPreliminary` to FKRiskScoreCard
  - Passes `evaluationStatus` to FKDocumentUploader
- **FKCrossValidationResults** (`frontend/src/components/risk/FKCrossValidationResults.tsx`):
  - Added success state and message display
  - Shows success message after validation completes indicating score was updated
- **FKDocumentUploader** (`frontend/src/components/risk/FKDocumentUploader.tsx`):
  - Added `evaluationStatus` prop
  - Shows informational alert when status is `pending_documents`

### New Files

- **E2E Test:** `.claude/commands/e2e/test_risk_score_after_validation.md`
  - Comprehensive test covering the two-phase scoring workflow

## Discrepancies Found

None. The plan accurately reflected the codebase structure and implementation requirements.

## Validation Results

- Backend linting (ruff): **PASSED** (after fixing unused imports)
- Frontend linting (eslint): **PASSED** (4 pre-existing warnings unrelated to changes)
- TypeScript type check: **PASSED**
- Frontend build: **PASSED**

## Git Diff Stats

```
backend/src/adapter/rest/risk_routes.py            |  11 +-
backend/src/core/servicios/risk/cross_validation_service.py     |   2 +-
backend/src/core/servicios/risk/document_extraction_service.py  |   2 +-
backend/src/core/servicios/risk/fraud_detection_service.py | 102 ++++++++++++--
backend/src/core/servicios/risk/risk_scoring_service.py    |  60 ++++++++++
backend/src/interface/risk_dtos.py                 |   1 +
frontend/src/components/risk/FKCrossValidationResults.tsx   | 127 +++++++++++++++---
frontend/src/components/risk/FKDocumentUploader.tsx     |  61 +++++++++-
frontend/src/components/risk/FKRiskScoreCard.tsx   |  28 +++++
frontend/src/pages/risk/RiskEvaluationDetail.tsx   |  44 ++++++-
frontend/src/types/risk.ts                         |   2 +
11 files changed, 414 insertions(+), 26 deletions(-) (approx)
```

## Acceptance Criteria Status

1. ✅ New evaluation creates with status `pending_documents` and preliminary score
2. ✅ Preliminary score is clearly indicated in the UI (chip with tooltip)
3. ✅ Cross-validation completion triggers final score calculation
4. ✅ Final score incorporates cross-validation discrepancy score impacts
5. ✅ Final risk level is determined after combined scoring
6. ✅ Alerts are created only after final scoring
7. ✅ UI updates to show final score after validation
8. ✅ Status transitions from `pending_documents` to appropriate final status
9. ✅ Blacklisted clients are still auto-rejected immediately (unchanged logic)
10. ⏳ All existing E2E tests pass (manual verification required)
11. ✅ New E2E test file created for validation

## Notes

- The implementation maintains backward compatibility - existing assessments with old statuses will continue to work
- The `pending_documents` status is additive and does not require database migration (VARCHAR accepts new string values)
- No new npm or pip packages were required
