# E2E Test: DIAN Checkbox Instrucción de Mandato Generation

Test the DIAN checkbox functionality in the Instrucción de Mandato form for Paga Local Colombia.

## User Story

As an Operations user
I want to generate an Instrucción de Mandato with DIAN creditors
So that DIAN payments are properly documented with the correct N/A messaging

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with operations or admin role
- Test client exists in the database (e.g., "My Home" or similar)

## Test Steps

### Part 1: Navigate to Form

1. Navigate to Application URL (http://localhost:5173)
2. Login with test credentials if not already logged in
3. Navigate to "Operaciones" > "Paga Local Colombia" from the sidebar
4. **Verify** the Instrucción de Mandato form is accessible
5. Take a screenshot of the form page

### Part 2: Select Client

6. In the client search field, type a test client name (e.g., "My Home")
7. Wait for search results to appear
8. Click on the client to select it
9. **Verify** client information is displayed

### Part 3: Add DIAN Creditor

10. Click "Agregar Acreedor" to add a creditor row
11. Check the "DIAN" checkbox for this creditor
12. **Verify** the DIAN info card appears showing:
    - Razón Social: "DIAN"
    - NIT: "800.197.268-4"
    - N/A message for Banco/Tipo de Cuenta/Número de Cuenta
13. Take a screenshot of the DIAN creditor card

### Part 4: Add Non-DIAN Creditor (Optional - Mixed Test)

14. Click "Agregar Acreedor" to add another creditor row
15. For the non-DIAN creditor, manually fill in:
    - Razón Social: "Test Creditor"
    - Banco: "Bancolombia"
    - Tipo de Cuenta: "Ahorros"
    - Número de Cuenta: "123456789"
16. **Verify** the editable fields are visible for non-DIAN creditor

### Part 5: Fill Required Fields

17. Enter a test value for "Número de Cotización" (e.g., "COT-TEST-001")
18. Enter today's date for "Fecha Contrato Mandato"
19. Enter a test amount for "Monto" (e.g., 1000000)
20. Take a screenshot of the filled form

### Part 6: Submit and Verify Success

21. Click "Generar Instrucción de Mandato" button
22. Wait for the request to complete
23. **Verify** NO `[object Object]` error appears
24. **Verify** success message appears OR document is generated
25. Take a screenshot of the result

## Success Criteria

- Form loads without errors
- DIAN checkbox correctly auto-fills the N/A message fields
- DIAN creditor displays the correct information:
  - Razón Social: "DIAN"
  - NIT: "800.197.268-4"
  - Banco/Tipo de Cuenta/Número de Cuenta show N/A message
- Form submission does NOT show `[object Object]` error
- If validation errors occur, they show as readable text (not `[object Object]`)
- Mixed DIAN + non-DIAN creditors submit successfully
- 4+ screenshots captured demonstrating the flow

## Error Scenarios to Note

- If validation errors occur, they should display as readable messages
- Invalid client NIT should show clear error
- Network errors should be handled gracefully
- Missing required fields should show field-level validation

## Bug Regression Check

This test specifically validates that the bug fix for issue #99 works:
- Before fix: `[object Object],[object Object],[object Object]` error
- After fix: Document generates successfully OR shows readable validation messages
