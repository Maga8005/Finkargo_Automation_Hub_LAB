# E2E Test: AI Contract Extraction

Test AI-powered contract data extraction for broker management in the Alianzas module.

## User Story

As an alianzas team member
I want to extract contract data from scanned PDF contracts using AI
So that I can process image-based documents that standard text extraction cannot handle

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- LandingAI API key configured in backend `.env`
- Test user account with `alianzas` role exists in Supabase
- Sample scanned PDF contract file available for testing

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: alianzas

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Take a screenshot of the login page
4. Login with test alianzas credentials
5. **Verify** successful login and redirect to dashboard
6. Navigate to Alianzas section (click "Alianzas" in sidebar)
7. Take a screenshot of Alianzas dashboard
8. Click "Nuevo Broker" button to create a new broker
9. **Verify** broker creation form appears
10. Take a screenshot of empty broker form
11. Scroll to "Extracción de Contrato" section
12. **Verify** contract upload component is visible with:
    - Drop zone for file upload
    - "Arrastra tu contrato aquí" text
    - Format information (PDF, DOCX)
13. **Verify** extraction method selection is visible:
    - "Estándar" radio option (default)
    - "IA (para escaneados)" radio option
14. Take a screenshot of contract upload section with extraction options
15. Select "IA (para escaneados)" radio option
16. **Verify** warning helper text appears about longer processing time
17. Upload a scanned PDF contract file (drag & drop or click)
18. **Verify** file appears with name and size
19. Take a screenshot of selected file with AI option
20. Click "Extraer Datos" button
21. **Verify** progress indicator appears with steps:
    - "Subiendo documento..."
    - "Convirtiendo a texto (IA)..."
    - "Extrayendo datos (IA)..."
22. Take a screenshot of progress stepper during extraction
23. Wait for extraction to complete (up to 120 seconds)
24. **Verify** extraction results appear with:
    - "Datos Extraídos" header
    - Confidence score chip
    - "Método: IA" chip indicator
    - Editable form fields
25. Take a screenshot of AI extraction results
26. **Verify** extracted fields are editable:
    - % Comisión Apertura
    - % Comisión Operativa
    - Banco
    - Cuenta Bancaria (CLABE)
    - RFC
    - Fecha Contrato
27. Modify one extracted field (e.g., adjust commission percentage)
28. Click "Aplicar al Formulario" button
29. **Verify** extracted data populates the main broker form
30. Take a screenshot of form populated with AI-extracted data
31. **Verify** the form fields contain the extracted (and edited) values

## Success Criteria

- Login succeeds with alianzas role
- Alianzas dashboard loads without errors
- Broker creation form appears correctly
- Contract upload component shows extraction method options
- AI extraction option can be selected
- File upload works with drag & drop
- Progress indicator shows during AI extraction
- AI extraction completes within 120 seconds
- Extraction results show "Método: IA" indicator
- Extracted data is editable
- Data can be applied to the main form
- 8 screenshots are captured:
  1. Initial login page
  2. Alianzas dashboard
  3. Empty broker form
  4. Contract upload section with extraction options
  5. Selected file with AI option
  6. Progress stepper during extraction
  7. AI extraction results
  8. Form populated with extracted data

## Error Scenarios to Note

- If AI extraction times out (>120s), error message should appear
- If API key is invalid, appropriate error should be shown
- If standard extraction returns 0% confidence, AI suggestion should appear
- Form should be disabled during AI extraction
- Partial results (HTTP 206) should show warning but allow manual completion

## Notes

- AI extraction takes 30-60 seconds typically
- For testing without real scanned PDF, use a PDF with minimal text to trigger low confidence
- The "Use IA" suggestion appears when standard extraction returns 0% confidence
