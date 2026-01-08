# Patch: Add Comments Column to PDF Validation Table

## Metadata
adw_id: `6a9aabdc`
review_change_request: `The comments added by the mesa de control analyst when manually validating the cross validations discrepancies must be included in the PDF report generated at the end of the process in the Evaluación page. Please make sure they are properly fitted and formatted in the report. They should be included in the <Resultados de Validación Cruzada> table on an additional column`

## Issue Summary
**Original Spec:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md
**Issue:** The `exportCrossValidationToPDF` function in the cross-validation PDF export shows the validation status (Validado/Pendiente) but does NOT include the analyst's comments. The `exportComprehensiveEvaluationReport` function already has a "Comentarios" column, but `exportCrossValidationToPDF` is missing this column.
**Solution:** Add a "Comentarios" column to the discrepancy table in `exportCrossValidationToPDF` to display the validation comments alongside the status, following the same pattern used in `exportComprehensiveEvaluationReport`.

## Files to Modify
Use these files to implement the patch:

- `frontend/src/utils/crossValidationPdfExport.ts` - Add comments column to `exportCrossValidationToPDF` discrepancy table

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add `truncateComment` helper function before or inside `exportCrossValidationToPDF`
- Add the helper function that already exists in `exportComprehensiveEvaluationReport` (lines 761-765) to be reusable or accessible within `exportCrossValidationToPDF`
- The function truncates comments to a max length with ellipsis for display

### Step 2: Update discrepancy data mapping in `exportCrossValidationToPDF`
- Modify the `discrepancyData` mapping (lines 320-344) to add a 7th column for comments when validations are present
- Use the validation comments from `resultWithValidation?.validation?.comments`
- Apply the `truncateComment` function to format the comments

### Step 3: Update table headers for comments column
- Modify the `headers` definition (lines 347-349) to include "Comentarios" as a 7th column when validations are present
- Change from 6 columns (`['Tipo de Validación', 'Campo', 'Severidad', 'Impacto', 'Descripción', 'Estado']`) to 7 columns including "Comentarios"

### Step 4: Adjust column widths for the new layout
- Update `validationColumnStyles` (lines 361-367) to accommodate the 7th column
- Reduce widths of other columns slightly to fit comments column (approximately 35-40mm)
- Ensure the table fits within A4 page margins

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npm run lint` - Verify no linting errors
2. `cd frontend && npx tsc --noEmit` - Verify TypeScript compiles without errors
3. `cd frontend && npm run build` - Verify production build succeeds

## Patch Scope
**Lines of code to change:** ~25 lines
**Risk level:** low
**Testing required:** Manual testing - generate a PDF with validated discrepancies and verify the comments column displays correctly with proper formatting and truncation
