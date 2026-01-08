# Patch: Restore Discrepancy Text Formatting for Readability

## Metadata
adw_id: `6a9aabdc`
review_change_request: `now that the validation review fields per discrepancy are available, the formatting of the text is no longer easy to read. We need to return the way the text is presented to how it was before where it was easy to read by an analyst.`

## Issue Summary
**Original Spec:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md
**Issue:** The `FKDiscrepancyValidationItem` component displays discrepancy values in a hard-to-read format using simple text lines with `JSON.stringify` for objects. The original `renderResult` function in `FKCrossValidationResults` had proper table formatting with document labels and formatted values.
**Solution:** Update `FKDiscrepancyValidationItem` to use the same table-based value rendering and formatting utilities from `FKCrossValidationResults`, displaying "Valores encontrados" in a proper table with document labels and formatted values.

## Files to Modify
Use these files to implement the patch:

- `frontend/src/components/risk/FKDiscrepancyValidationItem.tsx` - Add table-based value rendering with proper formatting
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Extract and export formatting utilities for reuse

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Extract formatting utilities from FKCrossValidationResults for reuse
- Extract `SIGNATORY_FIELD_LABELS`, `isSignatoryObject`, `formatSignatory`, `formatSignatoryObject`, and `formatValueForDisplay` functions
- Export these utilities from `FKCrossValidationResults.tsx` so they can be imported by `FKDiscrepancyValidationItem`
- Also export `getDocumentLabel` function for document type label lookups

### Step 2: Update FKDiscrepancyValidationItem to use table-based formatting
- Import the exported formatting utilities from `FKCrossValidationResults`
- Import `Table`, `TableBody`, `TableCell`, `TableContainer`, `TableHead`, `TableRow` from MUI
- Replace the simple text-based values display (lines 254-265) with a proper `TableContainer` structure
- Use `getDocumentLabel` to show proper Spanish document labels in the first column
- Use `formatValueForDisplay` to properly format values with signatory handling in the second column
- Add `whiteSpace: 'pre-line'` styling to preserve line breaks in formatted values

### Step 3: Ensure consistent styling with original rendering
- Match the table styling from `renderValuesComparison` in `FKCrossValidationResults`
- Use `Paper` variant="outlined" for the table container
- Use `size="small"` for the Table
- Apply proper typography variants (body2 for content)

## Validation
Execute every command to validate the patch is complete with zero regressions.

- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Patch Scope
**Lines of code to change:** ~30-50 lines
**Risk level:** low
**Testing required:** Visual verification that discrepancy values are displayed in table format with proper labels and formatting matching the original renderResult display
