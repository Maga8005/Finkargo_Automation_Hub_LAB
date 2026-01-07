# Implementation Report: Remove Database Existence Check from Risk Score

**Date:** 2025-12-23
**Module:** Risk/Fraud Detection
**Issue:** #14

## Summary

Removed the database existence check (`_check_company_history`) from contributing to the risk score calculation. Per business requirements, only document cross-validation results should affect the risk score, not whether a customer has previous evaluations in the system.

## Changes Made

- Modified `_check_company_history` method in `fraud_detection_service.py` to:
  - Always return `indicator_value=False` (never triggers as a risk factor)
  - Always return `score_impact=0` (no score contribution)
  - Provide informational evidence only (e.g., "Primera evaluacion para este cliente" or "Historial: X evaluaciones previas")
  - Removed the "Cupo muy alto para cliente sin historial" check that also added score impact

- Updated unit tests in `test_fraud_detection_service.py`:
  - Modified `test_critical_risk_score` to use `nit_format_validation` instead of `company_history`
  - Added new test class `TestCompanyHistoryCheck` with 3 tests:
    - `test_company_history_no_previous_assessments_no_score_impact`
    - `test_company_history_with_previous_assessments_no_score_impact`
    - `test_company_history_high_credit_no_history_no_score_impact`

- Created new E2E test file `.claude/commands/e2e/test_database_existence_check_removal.md`

## Discrepancies Found

**None.** The plan accurately described the implementation location and approach. The code structure matched the plan exactly.

## Files Changed

```
backend/src/core/servicios/risk/fraud_detection_service.py | 32 ++++-----
backend/tests/test_fraud_detection_service.py              | 83 +++++++++++++++++++++-
.claude/commands/e2e/test_database_existence_check_removal.md | (new file)
```

**Total: 2 files modified, 1 file created, 92 insertions(+), 23 deletions(-)**

## Validation Results

- Backend import test: PASSED
- Backend linting (ruff): PASSED (All checks passed!)
- Backend unit tests: PASSED (22/22 tests)
- Frontend linting: PASSED (warnings only, no errors)
- Frontend TypeScript: PASSED
- Frontend build: PASSED

## Behavior Change

**Before:**
- New customers received a risk indicator "Primera evaluacion para este cliente - sin historial previo" that contributed to the risk score
- High credit limits (>500M COP) for new customers triggered additional score impact

**After:**
- `company_history` indicator always returns `indicator_value: false` and `score_impact: 0`
- Evidence is purely informational (e.g., "Primera evaluacion para este cliente" or "Historial: 3 evaluaciones previas")
- No score inflation for new customers - risk score reflects only document cross-validation results
