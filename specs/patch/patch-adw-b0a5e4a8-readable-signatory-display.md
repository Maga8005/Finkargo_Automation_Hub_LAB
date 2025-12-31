# Patch: Improve signatory values display readability

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `The values for the signatory check are shown in a format that is not as easy to read for a person. Can you please adjust it so that it is easier to read for the people reviewing the values?`

## Issue Summary
**Original Spec:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md
**Issue:** The `values_found` display for contador/revisor fiscal validation shows raw JSON with technical field names (e.g., `signatory_name`, `signatory_id`, `all_signatories`) which is difficult for reviewers to read.
**Solution:** Enhance the frontend `formatValueForDisplay` function to render nested signatory data with human-readable Spanish labels in a structured format.

## Files to Modify

1. `frontend/src/components/risk/FKCrossValidationResults.tsx` - Enhance `formatValueForDisplay` function to handle contador/revisor fiscal nested objects with readable labels

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add field label mapping for signatory data
- Add a constant object that maps technical field names to Spanish labels
- Include mappings for: `signatory_name` → "Firmante", `signatory_id` → "Cédula Firmante", `auditor_name` → "Auditor", `auditor_license` → "Licencia Auditor", `all_signatories` → "Todos los Firmantes", `contador_name` → "Contador", `contador_cedula` → "Cédula Contador", `revisor_fiscal_name` → "Revisor Fiscal", `revisor_fiscal_cedula` → "Cédula Revisor Fiscal", `revisor_fiscal_principal_name` → "Revisor Fiscal Principal", `revisor_fiscal_principal_cedula` → "Cédula Revisor Fiscal Principal", `revisor_fiscal_suplente_name` → "Revisor Fiscal Suplente", `revisor_fiscal_suplente_cedula` → "Cédula Revisor Fiscal Suplente", `name` → "Nombre", `id` → "Cédula", `role` → "Rol"

### Step 2: Enhance formatValueForDisplay for nested objects
- Modify the `formatValueForDisplay` function to detect nested objects with known signatory fields
- For objects containing fields like `signatory_name`, `contador_name`, `revisor_fiscal_name`, format them as multi-line strings using the field labels
- For the `all_signatories` array, format each signatory as "Nombre (Rol) - Cédula: XXX"
- Skip empty/null values to reduce clutter
- Use bullet points or line breaks for multi-value display

### Step 3: Test rendering of formatted values
- Ensure the formatted output is readable in the table cell
- Use `\n` for line breaks which will render properly in the Typography component with `whiteSpace: 'pre-line'`
- Update the TableCell Typography to include `whiteSpace: 'pre-line'` style for proper line break rendering

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npm run lint` - Verify no linting errors
2. `cd frontend && npx tsc --noEmit` - Verify no TypeScript errors
3. `cd frontend && npm run build` - Verify build succeeds
4. `cd backend && python -m pytest tests/test_fraud_detection_service.py -v` - Verify backend tests still pass

## Patch Scope
**Lines of code to change:** ~40-60
**Risk level:** low
**Testing required:** Visual verification that signatory values display with readable labels
