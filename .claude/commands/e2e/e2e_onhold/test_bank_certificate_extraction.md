# E2E Test: Bank Certificate Extraction tipo_cuenta Normalization

Test the bank certificate extraction functionality and verify that the tipo_cuenta dropdown correctly displays the extracted account type.

## User Story

As an Operations user
I want to upload a bank certificate and have all fields automatically populated
So that I can quickly fill creditor information without manual data entry

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with operations or admin role
- Test client exists in the database (e.g., "My Home" or similar)
- Test bank certificate PDF file available (e.g., Bancolombia certificate)
- Test cotizacion PDF file available

## Test Steps

### Part 1: Navigate to Form

1. Navigate to Application URL (http://localhost:5173)
2. Login with test credentials if not already logged in
3. Navigate to "Operaciones" > "Paga Local Colombia" from the sidebar
4. **Verify** the Instruccion de Mandato form is accessible
5. Take a screenshot of the form page

### Part 2: Select Client and Upload Cotizacion

6. In the client search field, type a test client name (e.g., "My Home")
7. Wait for search results to appear
8. Click on the client to select it
9. **Verify** client information is displayed
10. Upload a test cotizacion PDF file
11. Click "Extraer Datos del PDF" button
12. Wait for extraction to complete
13. **Verify** creditors are populated from cotizacion
14. Take a screenshot of the populated form

### Part 3: Upload Bank Certificate for Non-DIAN Creditor

15. For a non-DIAN creditor row (one without the DIAN checkbox checked):
    - Click "Cargar Certificado Bancario" button
    - Select a test bank certificate PDF file
16. Click "Extraer Datos" button next to the uploaded file
17. Wait for bank certificate extraction to complete

### Part 4: Verify Tipo de Cuenta Normalization (CRITICAL)

18. **Verify** the "Tipo de Cuenta" dropdown shows a selected value (NOT empty)
    - Should show "Ahorros" if certificate had "CUENTA DE AHORROS"
    - Should show "Corriente" if certificate had "CUENTA CORRIENTE"
19. **Verify** the dropdown is not empty/unselected
20. Take a screenshot showing the populated dropdown
21. **Verify** the following fields are also populated:
    - Razon Social: Company name from certificate
    - NIT: Tax ID from certificate
    - Banco: Bank name (e.g., "BANCOLOMBIA")
    - Numero de Cuenta: Account number from certificate

### Part 5: Fill Remaining Fields and Submit

22. Fill in any missing required fields:
    - Numero de Cotizacion (if not auto-filled)
    - Fecha Contrato Mandato (today's date)
23. Take a screenshot of the completed form
24. Click "Generar Instruccion de Mandato" button
25. Wait for the request to complete
26. **Verify** success message appears OR document is generated
27. Take a screenshot of the result

## Success Criteria

- Bank certificate extraction completes without errors
- **Tipo de Cuenta dropdown shows the normalized value** (not empty):
  - "CUENTA DE AHORROS" from backend → "Ahorros" in dropdown
  - "CUENTA CORRIENTE" from backend → "Corriente" in dropdown
- All other bank certificate fields populate correctly
- Form validation passes for tipo_cuenta field
- Document generates successfully with complete bank account information
- 5+ screenshots captured demonstrating the flow

## Error Scenarios to Note

- If tipo_cuenta dropdown shows empty after extraction → BUG NOT FIXED
- If validation shows "Tipo de Cuenta es requerido" after extraction → BUG NOT FIXED
- If generated document has empty bank account columns → BUG NOT FIXED
- Network errors during extraction should show clear error messages

## Bug Regression Check

This test specifically validates that the bug fix for issue #100 works:
- Before fix: Tipo de Cuenta dropdown appears empty after extraction
- After fix: Dropdown correctly shows "Ahorros" or "Corriente"

## Technical Details

The fix normalizes backend values to frontend dropdown values:
- Backend returns: "CUENTA DE AHORROS" or "CUENTA CORRIENTE"
- Frontend dropdown options: "Ahorros", "Corriente", "PSE"
- The `normalizeTipoCuenta()` helper function maps backend → frontend format
