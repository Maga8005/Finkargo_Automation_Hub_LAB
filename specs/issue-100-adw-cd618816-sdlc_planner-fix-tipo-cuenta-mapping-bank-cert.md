# Bug: Bank Certificate tipo_cuenta Not Populating in Form Dropdown

## Bug Description
When generating a MANDATO (IM) with multiple creditors, the second creditor's bank account information is not fully populating after extracting data from the "certificado bancario" (bank certificate) PDF. Specifically, the "Tipo de Cuenta" field shows empty in the dropdown even though the bank certificate data was successfully extracted.

The generated document shows the first DIAN creditor correctly populated, but the second non-DIAN creditor only shows "Razón Social" and "NIT" columns populated - the "Banco", "Tipo de Cuenta", and "Número de Cuenta" columns appear empty in the final document.

**Expected behavior**: After clicking "Extraer Datos" on a bank certificate PDF, all fields (Razón Social, NIT, Banco, Tipo de Cuenta, Número de Cuenta) should populate in the form, and the dropdown should display the selected account type.

**Actual behavior**: The "Tipo de Cuenta" dropdown appears empty after extraction, even though the value exists in the component state. This causes validation to fail or the document to generate with missing bank account information.

## Problem Statement
There is a mismatch between the values returned by the backend bank certificate parser and the available options in the frontend dropdown:

- **Backend returns**: `"CUENTA DE AHORROS"` or `"CUENTA CORRIENTE"` (from `bank_certificate_parser_service.py:231-233`)
- **Frontend dropdown options**: `['Ahorros', 'Corriente', 'PSE']` (from `FKInstruccionMandatoForm.tsx:56`)

The MUI `<Select>` component's `value` attribute is set to `"CUENTA DE AHORROS"` but none of the `<MenuItem>` components have this value, so the dropdown appears empty/unselected.

## Solution Statement
Normalize the `tipo_cuenta` value in the frontend when extracting bank certificate data. Add a helper function that maps backend values like `"CUENTA DE AHORROS"` to frontend dropdown values like `"Ahorros"`. This ensures consistency between the extracted data and the available dropdown options.

The fix should be applied in the `handleExtractBankCert` function where the bank certificate data is processed and used to update the creditor form fields.

## Steps to Reproduce
1. Navigate to Operaciones > Paga Local Colombia
2. Search and select a client (e.g., "My Home")
3. Upload a Cotización PDF to extract initial creditor data
4. For the first creditor, check the DIAN checkbox (this works correctly)
5. Add a second creditor by clicking "Agregar Acreedor"
6. Upload a bank certificate PDF for the second creditor (e.g., a Bancolombia certificate)
7. Click "Extraer Datos" button to extract bank certificate data
8. **Observe**: The "Tipo de Cuenta" dropdown shows empty, even though Razón Social, NIT, Banco, and Número de Cuenta are populated
9. Try to submit the form - validation fails for "Tipo de Cuenta es requerido"
10. If manually selecting a tipo_cuenta and submitting, the document generates with missing data

## Root Cause Analysis
The root cause is a **value format mismatch** between the backend and frontend:

1. **Backend `bank_certificate_parser_service.py`** (lines 229-234):
   - Returns normalized values: `"CUENTA DE AHORROS"` or `"CUENTA CORRIENTE"`
   - This is the standard format extracted from Colombian bank certificates

2. **Frontend `FKInstruccionMandatoForm.tsx`** (line 56):
   - Defines `ACCOUNT_TYPES = ['Ahorros', 'Corriente', 'PSE']`
   - The dropdown `<MenuItem>` elements use these short-form values

3. **Frontend form population** (line 261):
   - Sets `tipo_cuenta: data.tipo_cuenta || ''` directly from backend response
   - No normalization is applied

4. **MUI Select behavior**:
   - When `value="CUENTA DE AHORROS"` but no `<MenuItem value="CUENTA DE AHORROS">` exists
   - The Select component renders as empty/unselected
   - The user sees an empty dropdown despite the state having a value

5. **Backend DTO validator** (`legal_dtos.py:439-451`):
   - Accepts and normalizes both formats on submission
   - But this doesn't help the frontend display issue

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

### Frontend Files
- `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` - Contains the `handleExtractBankCert` function (lines 241-273) that needs to normalize the `tipo_cuenta` value before setting state. Also contains the `ACCOUNT_TYPES` constant (line 56) used for the dropdown options.

### Backend Files (Reference Only - No Changes Needed)
- `backend/src/core/servicios/bank_certificate_parser_service.py` - Returns `"CUENTA DE AHORROS"` and `"CUENTA CORRIENTE"` from `_extract_tipo_cuenta` method (lines 206-238). This is correct behavior; the frontend should handle normalization.
- `backend/src/interface/legal_dtos.py` - The `validate_tipo_cuenta` validator already handles normalization on submission (lines 432-451), confirming the fix should be in frontend.

### Documentation Reference
- `.claude/commands/e2e/test_login.md` - Reference for E2E test format
- `.claude/commands/test_e2e.md` - Reference for E2E test execution

### New Files
- `.claude/commands/e2e/test_bank_certificate_extraction.md` - New E2E test to validate bank certificate extraction populates all fields correctly

## Step by Step Tasks

### 1. Add Helper Function to Normalize tipo_cuenta Values
- Open `frontend/src/components/forms/FKInstruccionMandatoForm.tsx`
- Add a helper function after the `isDianCreditor` function (around line 82) to normalize account type values:
  ```typescript
  /**
   * Normalize account type from bank certificate format to dropdown format
   * Maps: "CUENTA DE AHORROS" → "Ahorros", "CUENTA CORRIENTE" → "Corriente"
   */
  const normalizeTipoCuenta = (tipoCuenta: string): string => {
    const lower = tipoCuenta.toLowerCase();
    if (lower.includes('ahorr')) return 'Ahorros';
    if (lower.includes('corriente')) return 'Corriente';
    if (lower.includes('pse')) return 'PSE';
    // Return original if no match (let validation catch it)
    return tipoCuenta;
  };
  ```

### 2. Update handleExtractBankCert to Use Normalization
- In the `handleExtractBankCert` function (lines 241-273), update line 261 to use the normalization helper:
  - Change: `tipo_cuenta: data.tipo_cuenta || '',`
  - To: `tipo_cuenta: data.tipo_cuenta ? normalizeTipoCuenta(data.tipo_cuenta) : '',`
- This ensures the extracted value matches the dropdown options

### 3. Create E2E Test for Bank Certificate Extraction
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_dian_mandato_generation.md` to understand E2E test format
- Create new E2E test file: `.claude/commands/e2e/test_bank_certificate_extraction.md`
- Test steps should include:
  1. Login as operations/admin user
  2. Navigate to Operaciones > Paga Local Colombia
  3. Search and select a test client
  4. Upload a Cotización PDF
  5. Add a second creditor (non-DIAN)
  6. Upload a bank certificate PDF for the creditor
  7. Click "Extraer Datos"
  8. **Verify** Tipo de Cuenta dropdown shows selected value (not empty)
  9. **Verify** all other fields (Razón Social, NIT, Banco, Número de Cuenta) are populated
  10. Take screenshot of populated form
  11. Submit and verify document generates successfully with all bank account data

### 4. Run Validation Commands
- Run all validation commands to ensure bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Run backend tests to validate bug fix with zero regressions
cd backend && python -m pytest tests/ -v

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

After fixing, manually test by:
1. Start the dev servers: `npm run dev` (frontend) and `python -m uvicorn main:app --reload` (backend)
2. Navigate to Operaciones > Paga Local Colombia
3. Select a client, upload cotización, add non-DIAN creditor
4. Upload bank certificate and click "Extraer Datos"
5. **Verify** Tipo de Cuenta dropdown shows the correct value (e.g., "Ahorros" or "Corriente")
6. Submit and verify document generates with all bank account info populated

Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test `.claude/commands/e2e/test_bank_certificate_extraction.md` to validate this functionality works.

## Notes
- The backend validator already normalizes these values on submission, so the fix is purely a frontend display issue
- The fix is minimal and surgical - only the `tipo_cuenta` value needs normalization, not other fields
- The normalization function mirrors the backend's logic in `validate_tipo_cuenta` for consistency
- No backend changes are required since the DTO validator already handles both formats
- This bug may have been introduced when the bank certificate parser was updated to return standardized Colombian bank format values
