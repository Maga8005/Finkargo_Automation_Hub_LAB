# E2E Test: Broker Contract Extraction

Test the contract data extraction feature for the Alianzas broker management module.

## User Story

As an Alianzas user
I want to upload a broker contract (PDF or DOCX) and have it automatically extract the commercial terms
So that I can quickly populate broker information without manual data entry and reduce transcription errors

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with `alianzas` role exists in Supabase

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: alianzas or admin

## Test Steps

### Part 1: Login and Navigation

1. Navigate to the Application URL (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter test email and password
4. Click "Iniciar Sesión" button
5. Wait for authentication to complete
6. **Verify** successful redirect occurs
7. Navigate to Alianzas module (/alianzas/brokers)
8. **Verify** broker management page loads
9. Take a screenshot of the broker list page

### Part 2: Access Contract Upload Feature

10. Click "Nuevo Broker" button to open broker creation form
11. **Verify** broker form modal/dialog appears
12. **Verify** "Importar desde Contrato" accordion section is visible
13. Click on the accordion to expand it
14. Take a screenshot of the expanded contract upload section

### Part 3: File Upload Validation

15. **Verify** drop zone is displayed with text "Arrastra tu contrato aquí"
16. **Verify** accepted formats (.pdf, .docx) and max size (10MB) are shown
17. Attempt to upload an invalid file type (if test file available)
18. **Verify** error message appears for invalid file type

### Part 4: Contract Extraction (if test contract available)

19. Upload a valid broker contract (PDF or DOCX)
20. **Verify** file name and size are displayed
21. Click "Extraer Datos" button
22. **Verify** loading indicator appears
23. Wait for extraction to complete
24. **Verify** extraction results card appears with:
    - Confidence percentage chip
    - Editable fields for:
      - % Comisión Apertura
      - % Comisión Operativa
      - Banco
      - Cuenta Bancaria (CLABE)
      - RFC
      - Fecha Contrato
25. Take a screenshot of extraction results

### Part 5: Apply Extracted Data to Form

26. Modify any extracted field value (optional)
27. Click "Aplicar al Formulario" button
28. **Verify** accordion collapses
29. **Verify** snackbar success message appears
30. **Verify** form fields are populated with extracted data:
    - % Comisión Apertura field has value
    - % Comisión Operativa field has value
    - Banco field has value
    - Cuenta Bancaria field has value
    - RFC field has value
    - Fecha Contrato field has value
31. Take a screenshot of the populated form

### Part 6: Cancel and Reset

32. Click "Cancelar" button to close the form
33. **Verify** form is closed/reset

## Success Criteria

- Login succeeds with alianzas role
- Broker management page loads without errors
- Contract upload accordion is visible and expandable
- File validation works (rejects invalid types/sizes)
- Contract extraction API is called successfully
- Extraction results are displayed with confidence score
- Extracted data populates the form correctly
- User can edit extracted values before applying
- Success notification appears after applying data
- 4 screenshots are captured:
  1. Broker list page
  2. Expanded contract upload section
  3. Extraction results with confidence
  4. Populated broker form

## Error Scenarios to Note

- Network errors should show error message
- Scanned PDF (no selectable text) should show low confidence warning
- Empty file should be rejected
- File too large (>10MB) should be rejected
- Extraction failure should suggest AI extraction alternative

## Notes

- The AI extraction feature is disabled (future enhancement)
- Test with sample broker contracts from the Marzo 2024 or current template versions
- Confidence score is based on number of fields successfully extracted
