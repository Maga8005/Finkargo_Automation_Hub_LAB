# Bug: DIAN Checkbox Validation Error on Instrucción de Mandato Generation

## Bug Description
When generating an Instrucción de Mandato (MANDATO IM) with DIAN as one creditor and another creditor with a certificación bancaria upload, the system displays the error: `Error al generar documento: [object Object],[object Object],[object Object]`. The error appears cryptic because Pydantic validation errors are returned as an array of objects that aren't properly stringified in the frontend error handling.

**Expected behavior**: Document generation should succeed when DIAN checkbox is checked for one creditor and another creditor has bank certificate details filled in.

**Actual behavior**: Pydantic validation fails because the `tipo_cuenta` field for DIAN creditors now contains the long N/A message: `"N/A – En la medida en que el pago del instrumento de pago se deberá realizar por el Mandato usando el link de pago enviado por el Mandante."` which doesn't match the validator's allowed values.

## Problem Statement
The backend DTO validator for `AcreedorGastosNacionales.tipo_cuenta` only accepts specific values: `['Ahorros', 'Corriente', 'PSE', 'CUENTA DE AHORROS', 'CUENTA CORRIENTE']`. After updating the DIAN checkbox feature to use new values (per recent spec changes), the `tipo_cuenta` now contains the N/A message for DIAN creditors. This message doesn't match any valid account type, causing Pydantic validation to fail.

## Solution Statement
Modify the `AcreedorGastosNacionales` validators in the backend to bypass or handle validation for DIAN creditors differently. When `es_dian=True`, the validators should:
1. Skip validation for `banco`, `tipo_cuenta`, and `numero_cuenta` fields since these are N/A for DIAN payments
2. Accept any value for these fields when the creditor is flagged as DIAN

Additionally, improve the frontend error handling to properly display Pydantic validation errors as readable messages rather than `[object Object]`.

## Steps to Reproduce
1. Navigate to Operaciones > Paga Local Colombia
2. Search and select a client (e.g., "My Home")
3. Upload a Cotización PDF that contains at least 2 creditors (one DIAN and one non-DIAN)
4. Check the DIAN checkbox for the DIAN creditor
5. For the non-DIAN creditor, upload a certificación bancaria PDF
6. Fill in all required fields (monto, fecha, etc.)
7. Click "Generar Instrucción de Mandato"
8. Observe the error: `Error al generar documento: [object Object],[object Object],[object Object]`

## Root Cause Analysis
The root cause is a mismatch between the updated DIAN values and the backend validation rules:

1. **Frontend Change**: The DIAN checkbox now sets:
   - `tipo_cuenta = "N/A – En la medida en que el pago del instrumento de pago se deberá realizar por el Mandato usando el link de pago enviado por el Mandante."`
   - `banco = "N/A – En la medida en que..."` (same message)
   - `numero_cuenta = "N/A – En la medida en que..."` (same message)

2. **Backend Validator** (`legal_dtos.py:429-444`): The `validate_tipo_cuenta` validator only accepts:
   - `['Ahorros', 'Corriente', 'PSE', 'CUENTA DE AHORROS', 'CUENTA CORRIENTE']`
   - Or normalizes values containing "ahorr", "corriente", or "pse"
   - The N/A message doesn't contain any of these, so validation fails

3. **Error Display**: The frontend catches `error.response?.data?.detail` which contains Pydantic's validation error array. When stringified implicitly, objects display as `[object Object]`.

## Affected Layer
- [x] Backend: adapter/rest (API routes) - error response format
- [x] Backend: core/servicios (business logic) - no changes needed
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components - error display handling
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

### Backend Files
- `backend/src/interface/legal_dtos.py` - Contains `AcreedorGastosNacionales` model with validators that need to be updated to handle DIAN creditors. Lines 406-444 define the model and validators that are failing.

### Frontend Files
- `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` - Contains the error handling at line 424-427 that displays `[object Object]` instead of readable messages. Needs improved error parsing.

### Documentation Reference
- `.claude/commands/e2e/test_login.md` - Reference for E2E test format
- `.claude/commands/test_e2e.md` - Reference for E2E test execution

### New Files
- `.claude/commands/e2e/test_dian_mandato_generation.md` - New E2E test to validate DIAN checkbox functionality

## Step by Step Tasks

### 1. Update AcreedorGastosNacionales Validators to Handle DIAN Creditors
- Read `backend/src/interface/legal_dtos.py` lines 406-444
- Modify the `validate_banco` validator (lines 422-427) to skip validation when the value starts with "N/A" (indicating DIAN payment)
- Modify the `validate_tipo_cuenta` validator (lines 429-444) to:
  - Check if the value starts with "N/A" and allow it (for DIAN creditors)
  - Keep existing validation for normal account types
- Add a `validate_numero_cuenta` validator that allows values starting with "N/A"
- This approach is cleaner than checking `es_dian` flag in each validator since the validators run before all fields are set

### 2. Add Root Validator to Skip Field Validation for DIAN Creditors
- As an alternative/additional safeguard, add a Pydantic `root_validator` that runs after all fields are set
- The root validator can check if `es_dian=True` and ensure the DIAN-specific values are properly set
- This provides a second layer of validation logic

### 3. Update Frontend Error Handling for Better Error Display
- Read `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` lines 420-430
- Update the error handling in the catch block to properly parse Pydantic validation errors
- If `error.response?.data?.detail` is an array, map and join the error messages
- Handle nested error objects that Pydantic returns (e.g., `{loc: [...], msg: "...", type: "..."}`)

### 4. Create E2E Test for DIAN Mandato Generation
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand E2E test format
- Create new E2E test file: `.claude/commands/e2e/test_dian_mandato_generation.md`
- Test steps should include:
  1. Login as admin/operations user
  2. Navigate to Operaciones > Paga Local Colombia
  3. Search and select a test client
  4. Upload a test Cotización PDF
  5. Check DIAN checkbox for one creditor
  6. Fill in non-DIAN creditor with bank details
  7. Submit and verify success (no `[object Object]` error)
  8. Take screenshot of success state

### 5. Run Validation Commands
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
3. Test generating a Mandato (IM) with DIAN checkbox checked for one creditor
4. Verify document generates successfully without `[object Object]` error

Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test `.claude/commands/e2e/test_dian_mandato_generation.md` to validate this functionality works.

## Notes
- The validation error format `[object Object],[object Object],[object Object]` indicates 3 validation errors - likely for `banco`, `tipo_cuenta`, and potentially `numero_cuenta` fields
- The validators use Pydantic V1 style `@validator` decorators (there's a deprecation warning but it still works)
- The fix should maintain backwards compatibility - normal creditors should still have their account types validated
- Consider adding a constant for the N/A prefix check to ensure consistency between frontend and backend
