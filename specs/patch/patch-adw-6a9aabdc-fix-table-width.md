# Patch: Fix table width mismatch in PDF report

## Metadata
adw_id: `6a9aabdc`
review_change_request: `The PDF report has a different table width for <Resultados de Validación Cruzada> table than for the <Indicadores de Fraude Activados> table. Please make the table for <Resultados de Validación Cruzada> the same width as the table for <Indicadores de Fraude Activados>`

## Issue Summary
**Original Spec:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md
**Issue:** The "Resultados de Validación Cruzada" table has fixed column widths (25+20+18+15+35+40=153mm) that don't fill the same width as the "Indicadores de Fraude Activados" table, which uses 'auto' for its last column to span the full page width.
**Solution:** Change one of the fixed column widths in the "Resultados de Validación Cruzada" table to 'auto' so it expands to fill the full page width, matching the behavior of the other table.

## Files to Modify
Use these files to implement the patch:

- `frontend/src/utils/crossValidationPdfExport.ts`: Modify the columnStyles for the "Resultados de Validación Cruzada" table (around line 818) to use 'auto' for one column width

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update column styles for cross-validation table
- In `frontend/src/utils/crossValidationPdfExport.ts`, locate the `columnStyles` object for the "Resultados de Validación Cruzada" table (around lines 818-825)
- Change column 4 (Descripción) or column 5 (Comentarios) to use `cellWidth: 'auto'` instead of a fixed width
- This will allow the table to expand to fill the full page width, matching the "Indicadores de Fraude Activados" table behavior

Current code:
```typescript
columnStyles: {
  0: { cellWidth: 25 },
  1: { cellWidth: 20 },
  2: { cellWidth: 18, halign: 'center' },
  3: { cellWidth: 15, halign: 'center', textColor: FINKARGO_COLORS.error },
  4: { cellWidth: 35 },
  5: { cellWidth: 40 },
},
```

Updated code:
```typescript
columnStyles: {
  0: { cellWidth: 40 },
  1: { cellWidth: 20 },
  2: { cellWidth: 18, halign: 'center' },
  3: { cellWidth: 15, halign: 'center', textColor: FINKARGO_COLORS.error },
  4: { cellWidth: 'auto' },
  5: { cellWidth: 40 },
},
```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npx tsc --noEmit` - Verify TypeScript compilation succeeds
2. `cd frontend && npm run lint` - Verify no linting errors
3. `cd frontend && npm run build` - Verify production build succeeds
4. Manual verification: Generate a PDF report with cross-validation discrepancies and verify both tables have the same width

## Patch Scope
**Lines of code to change:** ~3 lines
**Risk level:** low
**Testing required:** Visual verification of PDF output to confirm tables match in width
