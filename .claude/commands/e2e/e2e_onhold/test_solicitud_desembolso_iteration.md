# E2E Test: Solicitud de Desembolso - Contract Iteration Field

Test the new "Iteración del Contrato" input field functionality in the Solicitud de Desembolso form for Paga Local Colombia.

## User Story

As a Commercial team member
I want to input the contract iteration number when generating a Solicitud de Desembolso
So that the generated document contains the correct contract code with the proper iteration number as provided by Mesa de Control

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with operations or comercial_paga_local role
- Test client exists in database with valid NIT

## Test Credentials

Use test account (configure in test environment):
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations or comercial_paga_local

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. **Verify** successful redirect to dashboard
5. Navigate to Paga Local Colombia section (Operations → Paga Local Colombia)
6. Click on "Solicitud de Desembolso" menu item
7. Take a screenshot of the empty Solicitud de Desembolso form
8. **Verify** the form loads with Section 1 (Seleccionar Cliente) visible

### Client Search
9. Enter a valid test client NIT in the search field
10. Click "Buscar" button
11. **Verify** search results appear
12. Select the test client from results
13. **Verify** client is marked as selected with green confirmation

### PDF Upload & Data Extraction
14. Upload a test Cotización PDF file
15. Click "Extraer Datos del PDF" button
16. Wait for extraction to complete
17. **Verify** success message appears with extracted items count

### Section 3 - Datos de la Solicitud (Main Test Focus)
18. Take a screenshot showing Section 3 with the new "Iteración del Contrato" field
19. **Verify** the following fields are present in Section 3:
    - "Número de Cotización de Desembolso" text field
    - "Iteración del Contrato" number field (NEW)
    - "Fecha del Contrato de Crédito" date field
    - "Días de Plazo" number field
    - "Monto Total" read-only field
20. **Verify** "Iteración del Contrato" field has:
    - Default value of 1
    - Helper text: "Número de iteración proporcionado por Mesa de Control (1-99)"
    - Input type is number
21. **Verify** field validation by testing boundaries:
    - Clear the field and verify it's required
    - Enter 0 and verify validation prevents it
    - Enter 100 and verify validation prevents it
    - Enter 50 and verify it's accepted
22. Set the iteration value back to 2 (simulating second iteration)
23. Take a screenshot showing the filled iteration field with value 2

### Anexo I Table Verification
24. **Verify** Anexo I table is populated with extracted data
25. **Verify** total amount is calculated and displayed

### Form Submission
26. Fill in all remaining required fields if not already filled
27. Take a screenshot of the complete form before submission
28. Click "Solicitar Documento" button
29. Wait for generation to complete
30. **Verify** success message appears with contract ID
31. Take a screenshot of the success confirmation
32. **Verify** the generated contract ID follows format: PLSD-YYYY-XXX

### Form Reset Verification
33. Click "Generar Nueva Solicitud" button
34. **Verify** all form fields are reset to defaults
35. **Verify** "Iteración del Contrato" field is reset to 1

## Success Criteria

- Login succeeds and redirects to operations dashboard
- Solicitud de Desembolso form loads correctly
- **NEW FIELD PRESENT**: "Iteración del Contrato" field appears in Section 3
- Field has correct default value of 1
- Field has correct helper text explaining its purpose
- Field validates input range (1-99 only)
- Field value is included in the submitted request
- Generated document is created successfully
- Form reset returns iteration field to default value of 1
- 5 screenshots are captured:
  1. Empty Solicitud de Desembolso form
  2. Section 3 showing the new iteration field
  3. Filled iteration field with test value (2)
  4. Complete form before submission
  5. Success confirmation after generation

## Error Scenarios to Note

- Iteration value of 0 should fail validation
- Iteration value of 100+ should fail validation
- Non-integer values should be rejected
- Empty iteration field should default to 1 on submission

## Notes

- This test validates the new "Iteración del Contrato" field added for Paga Local Colombia
- The iteration number is used in the contract code format: CO:NIT:ITERATION:D:M:DOM
- The value replaces the `[ITERACION]` placeholder in the generated Word document
- This feature supports clients who exceed their 290M COP credit limit and need new contracts with incremented iteration numbers
