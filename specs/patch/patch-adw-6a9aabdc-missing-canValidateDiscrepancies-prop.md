# Patch: Pass canValidateDiscrepancies prop to FKCrossValidationResults

## Metadata
adw_id: `6a9aabdc`
review_change_request: `"I cannot find the per validation checkbox with the dropdown and text box for the analyst to report the review done. I still see the general checkbox in the /risk/evaluations/ page"`

## Issue Summary
**Original Spec:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md
**Issue:** The `canValidateDiscrepancies` prop is not being passed to `FKCrossValidationResults` in `RiskEvaluationDetail.tsx`, causing the per-discrepancy validation UI (dropdown + text box) to never render. The component defaults `canValidateDiscrepancies` to `false`, so users with mesa_control, risk_manager, or admin roles see the old general checkbox instead of individual discrepancy validation controls.
**Solution:** Add the `canValidateDiscrepancies` prop to the `FKCrossValidationResults` component usage in `RiskEvaluationDetail.tsx`, passing `true` when the logged-in user has one of the required roles (mesa_control, risk_manager, admin).

## Files to Modify
Use these files to implement the patch:

- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Add canValidateDiscrepancies prop calculation and pass to FKCrossValidationResults

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add role check variable for discrepancy validation permission
- In `RiskEvaluationDetail.tsx`, after the existing `isRiskManager` check (around line 78), add a new variable to check if user can validate discrepancies
- Check if user role is `mesa_control`, `risk_manager`, or `admin`
- Example: `const canValidateDiscrepancies = userProfile?.role && ['mesa_control', 'risk_manager', 'admin'].includes(userProfile.role);`

### Step 2: Pass canValidateDiscrepancies prop to FKCrossValidationResults
- In the Cross-Validation Tab section (around line 387-398), add the `canValidateDiscrepancies` prop to the `FKCrossValidationResults` component
- Pass the computed boolean value: `canValidateDiscrepancies={canValidateDiscrepancies}`

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npm run lint` - Verify no linting errors
2. `cd frontend && npx tsc --noEmit` - Verify TypeScript compiles without type errors
3. `cd frontend && npm run build` - Verify production build succeeds

## Patch Scope
**Lines of code to change:** ~3 lines (1 new variable, 1 prop addition)
**Risk level:** low
**Testing required:** Login as mesa_control/risk_manager/admin user, navigate to /risk/evaluations/{id}, go to Cross-Validation tab, and verify individual discrepancy validation controls (dropdown + text box) appear instead of general checkbox
