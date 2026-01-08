# Patch: Add Validation Comments to Cross-Validation PDF Report

## Metadata
adw_id: `6a9aabdc`
review_change_request: `The comments added by the mesa de control analyst when manually validating the cross validations discrepancies must be included in the PDF report generated at the end of the process in the Evaluación page. Please make sure they are properly fitted and formatted in the report. They should be included in the <Resultados de Validación Cruzada> table on an additional column`

## Issue Summary
**Original Spec:** `app_docs/feature-6a9aabdc-discrepancy-validation-checkboxes.md`
**Issue:** The PDF report generated from the Evaluación page (`exportComprehensiveEvaluationReport`) displays the cross-validation discrepancies table but does not include the validation comments added by mesa de control analysts. The current implementation only shows validation status (Validado/Pendiente) without the analyst's comments.
**Solution:** Modify the `exportComprehensiveEvaluationReport` function in `crossValidationPdfExport.ts` to:
1. Accept `CrossValidationResponseWithValidations` type instead of `CrossValidationResponse`
2. Add a new "Comentarios" column to the discrepancy table
3. Display validation comments from the `validation.comments` field
4. Update the caller in `RiskEvaluationDetail.tsx` to use `getDiscrepanciesWithValidations` instead of `getDiscrepancies`

## Files to Modify

1. `frontend/src/utils/crossValidationPdfExport.ts` - Modify `exportComprehensiveEvaluationReport` to include comments column
2. `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Update to use `getDiscrepanciesWithValidations` for report generation

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `exportComprehensiveEvaluationReport` type signature
- Change parameter type from `CrossValidationResponse` to `CrossValidationResponseWithValidations`
- Update the import to include `CrossValidationResponseWithValidations` if not already imported

### Step 2: Add "Comentarios" column to the discrepancy table in comprehensive report
- In the `exportComprehensiveEvaluationReport` function, locate the "Resultados de Validación Cruzada" table section (around line 759-820)
- Modify the `discrepancyData` mapping to include a 6th column for validation comments
- Extract comments from `results.results.find(res => res.id === r.id)?.validation?.comments`
- Truncate long comments to fit the table cell (max ~100 chars with ellipsis)
- Update table headers to include 'Comentarios'
- Adjust column widths:
  - Reduce 'Tipo' width from 30 to 25
  - Reduce 'Campo' width from 25 to 20
  - Reduce 'Descripción' width to 35 (from auto)
  - Add 'Comentarios' column with width 40

### Step 3: Update RiskEvaluationDetail.tsx to fetch validations with comments
- In `handleGenerateReport` function, change `riskService.getDiscrepancies(id)` to `riskService.getDiscrepanciesWithValidations(id)`
- Update the `generateReportWithData` function parameter type from `CrossValidationResponse` to `CrossValidationResponseWithValidations`
- Update `validationResults` state type if needed to `CrossValidationResponseWithValidations`

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npx tsc --noEmit` - TypeScript type check passes
2. `cd frontend && npm run lint` - No linting errors
3. `cd frontend && npm run build` - Build succeeds without errors
4. Manual test: Navigate to a risk evaluation with validated discrepancies, generate PDF report, verify "Comentarios" column appears with validation comments in the "Resultados de Validación Cruzada" table

## Patch Scope
**Lines of code to change:** ~40
**Risk level:** low
**Testing required:** TypeScript check, lint, build, manual PDF generation test
