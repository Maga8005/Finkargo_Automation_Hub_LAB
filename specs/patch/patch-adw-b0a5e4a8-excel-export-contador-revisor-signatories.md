# Patch: Add contador, revisor fiscal, and signatories to Excel export

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `include these values in the excel export in documentos please. So basically, the export for RUT and Certificado de Existencia to show revisor fiscal and contador when available and the signatories for the financial statements data export`

## Issue Summary
**Original Spec:** `specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md`
**Issue:** The Excel export for document extractions does not include contador, revisor fiscal fields from RUT and Certificado de Existencia, nor the signatories array from financial statements.
**Solution:** Add Spanish field labels for contador/revisor fiscal fields in the `FIELD_LABELS` mapping and add a dedicated section to expand the `signatories` array (similar to how `shareholders` is currently handled).

## Files to Modify
Use these files to implement the patch:

1. `frontend/src/utils/riskExcelExport.ts` - Add field labels and expand signatories array

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Spanish field labels for contador and revisor fiscal fields
- Open `frontend/src/utils/riskExcelExport.ts`
- In the `FIELD_LABELS` constant (around line 30-73), add the following new entries:
  ```typescript
  // Contador (Accountant) fields
  contador_name: 'Nombre del Contador',
  contador_cedula: 'Cédula del Contador',
  contador_license: 'Tarjeta Profesional Contador',
  // Revisor Fiscal fields (Certificado de Existencia)
  revisor_fiscal_name: 'Nombre del Revisor Fiscal',
  revisor_fiscal_cedula: 'Cédula del Revisor Fiscal',
  revisor_fiscal_license: 'Tarjeta Profesional Revisor Fiscal',
  // Revisor Fiscal fields (RUT - principal and suplente)
  revisor_fiscal_principal_name: 'Nombre del Revisor Fiscal Principal',
  revisor_fiscal_principal_cedula: 'Cédula del Revisor Fiscal Principal',
  revisor_fiscal_suplente_name: 'Nombre del Revisor Fiscal Suplente',
  revisor_fiscal_suplente_cedula: 'Cédula del Revisor Fiscal Suplente',
  ```

### Step 2: Add signatories array expansion in createDocumentSheet function
- In the `createDocumentSheet` function (after the shareholders handling around line 273-285), add similar handling for the `signatories` array:
  ```typescript
  // Handle signatories array separately (expand to multiple rows) - Financial Statements
  const signatories = extractedData.signatories as Array<Record<string, unknown>> | undefined;
  if (signatories && Array.isArray(signatories) && signatories.length > 0) {
    data.push(['']); // Empty row
    data.push(['--- Firmantes ---', '']);

    signatories.forEach((signatory, idx) => {
      data.push([`Firmante ${idx + 1}`, '']);
      Object.entries(signatory).forEach(([key, value]) => {
        data.push([`  ${getFieldLabel(key)}`, formatValueForExcel(value, key)]);
      });
    });
  }
  ```

### Step 3: Update the skip condition for arrays
- In the forEach loop that processes extracted data (around line 265-271), ensure `signatories` is also skipped since it will be handled separately:
  ```typescript
  Object.entries(extractedData).forEach(([key, value]) => {
    // Skip arrays (handled separately)
    if (Array.isArray(value)) {
      return;
    }
    data.push([getFieldLabel(key), formatValueForExcel(value, key)]);
  });
  ```
  - NOTE: This condition already exists and works correctly since it skips ALL arrays. No change needed here.

## Validation
Execute every command to validate the patch is complete with zero regressions.

```bash
# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

## Patch Scope
**Lines of code to change:** ~25 lines
**Risk level:** low
**Testing required:** Manual verification by uploading documents with contador/revisor fiscal data and financial statements with signatories, then exporting to Excel and verifying the fields appear correctly with Spanish labels.
