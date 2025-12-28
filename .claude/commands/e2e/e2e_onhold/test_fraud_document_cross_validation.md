# E2E Test: Fraud Detection Document Cross-Validation

Test the AI-powered document extraction and cross-validation feature for detecting fraud through document inconsistencies.

## User Story

As a Risk Analyst
I want to upload multiple client documents and have them automatically analyzed for cross-document discrepancies
So that I can detect potential fraud attempts through document inconsistencies (like the Azelis fraud case)

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with `risk_analyst` or `risk_manager` role
- `LANDINGAI_API_KEY` environment variable configured in backend
- Test PDF documents available for each document type:
  - Financial Statement (Current Year)
  - Financial Statement (Prior Year)
  - Cedula (Legal Representative ID)
  - Composicion Accionaria (Shareholders)
  - RUT
  - Certificado de Existencia (optional)

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Part 1: Create New Evaluation with Document Analysis

1. **Login as Risk Analyst** (or verify already logged in)
2. Navigate to `/risk/dashboard`
3. **Verify** dashboard loads with metrics and evaluation list
4. Click "Nueva Evaluacion" button
5. **Verify** evaluation form appears
6. Enter a test client NIT in the NIT field
7. Select "Completa con Documentos" as assessment type (if available)
8. Click "Iniciar Evaluacion" button
9. **Verify** evaluation is created and redirects to detail page
10. Take a screenshot of the new evaluation detail page

### Part 2: Upload Documents

11. **Verify** "Documentos" tab or section is visible
12. Navigate to the Documents section
13. **Verify** 6 document upload slots are visible:
    - Estados Financieros (Año Actual)
    - Estados Financieros (Año Anterior)
    - Cédula del Representante Legal
    - Composición Accionaria
    - RUT
    - Certificado de Existencia
14. Take a screenshot showing empty document upload slots

15. **Upload Financial Statement (Current Year)**:
    - Click upload button for "Estados Financieros (Año Actual)"
    - Select a PDF file
    - **Verify** file name appears after upload
    - **Verify** status shows "Pendiente" or upload indicator

16. **Upload Financial Statement (Prior Year)**:
    - Click upload button for "Estados Financieros (Año Anterior)"
    - Select a PDF file
    - **Verify** upload success

17. **Upload Cedula**:
    - Click upload button for "Cédula del Representante Legal"
    - Select a PDF or image file
    - **Verify** upload success

18. **Upload Composicion Accionaria**:
    - Click upload button for "Composición Accionaria"
    - Select a PDF file
    - **Verify** upload success

19. **Upload RUT**:
    - Click upload button for "RUT"
    - Select a PDF file
    - **Verify** upload success

20. Take a screenshot showing all uploaded documents with pending status

### Part 3: Trigger AI Extraction

21. **Verify** "Extraer Datos" or similar button is visible
22. Click the extraction trigger button
23. **Verify** loading/processing indicators appear for all documents
24. Wait for extraction to complete (allow up to 3 minutes for all documents)
25. **Verify** extraction status changes to "Completado" for each document
26. Take a screenshot showing completed extractions

27. **Verify** extracted data preview is available:
    - Click on a completed extraction
    - **Verify** extracted fields are displayed (company name, NIT, etc.)
    - Take a screenshot of extracted data preview

### Part 4: Run Cross-Validation

28. Navigate to "Validación Cruzada" tab or section
29. **Verify** "Ejecutar Validación" button is visible (or validation runs automatically)
30. Click validation button if manual trigger required
31. Wait for cross-validation to complete
32. **Verify** validation results are displayed

### Part 5: Review Discrepancies

33. **Verify** discrepancy summary is shown:
    - Total discrepancies count
    - Breakdown by severity (Critical, High, Medium, Low)
34. Take a screenshot of discrepancy summary

35. **Verify** individual discrepancies are listed with:
    - Severity indicator (icon/color)
    - Description of the discrepancy
    - Documents compared
    - Field values found in each document
    - Score impact

36. Click on a discrepancy to expand details
37. **Verify** expanded view shows:
    - Full values from each document
    - Explanation of why this is flagged
38. Take a screenshot of expanded discrepancy details

### Part 6: Verify Risk Score Update

39. Navigate back to main evaluation view
40. **Verify** risk score has been updated based on document discrepancies
41. **Verify** fraud indicators include document-based indicators
42. Take a screenshot of updated risk score with document indicators

### Part 7: Make Decision (Risk Manager Only)

43. If logged in as risk_manager:
    - **Verify** decision section is available
    - Select "Rechazar" or appropriate decision
    - Enter notes referencing document discrepancies
    - Click confirm button
    - **Verify** decision is saved and status updates
44. Take a screenshot of final evaluation status

## Success Criteria

- All 6 document upload slots are functional
- Documents can be uploaded in PDF format (images for Cedula)
- AI extraction processes all documents successfully
- Extraction status is clearly visible for each document
- Cross-validation identifies discrepancies between documents
- Discrepancies are displayed with appropriate severity levels
- Risk score incorporates document-based discrepancies
- Total processing time is reasonable (< 5 minutes for all documents)
- 8+ screenshots are captured:
  1. New evaluation detail page
  2. Empty document upload slots
  3. Documents with pending status
  4. Completed extractions
  5. Extracted data preview
  6. Discrepancy summary
  7. Expanded discrepancy details
  8. Updated risk score with document indicators

## Document Upload Elements to Verify

| Document Type | Label (Spanish) | Accepted Formats | Max Size |
|--------------|-----------------|------------------|----------|
| Financial Statement Current | Estados Financieros (Año Actual) | PDF | 50MB |
| Financial Statement Prior | Estados Financieros (Año Anterior) | PDF | 50MB |
| Cedula | Cédula del Representante Legal | PDF, PNG, JPG | 5MB |
| Composicion Accionaria | Composición Accionaria | PDF | 10MB |
| RUT | RUT | PDF, PNG | 5MB |
| Certificado Existencia | Certificado de Existencia | PDF | 10MB |

## Expected Cross-Validation Checks

The system should validate:
1. **Company Name Consistency**: Same company name across all documents
2. **NIT Consistency**: Matching NIT across all documents
3. **Legal Representative**: Name and ID match between Cedula, RUT, and Certificado
4. **Shareholder-Board Alignment**: Majority shareholder appears in board (if applicable)
5. **Financial Continuity**: Reasonable year-over-year changes
6. **Email Domain**: Company email domain matches expected pattern

## Error Scenarios to Test

1. **Invalid File Type**: Upload non-PDF to PDF-only slot
   - Expected: Error message, upload rejected
2. **File Too Large**: Upload file exceeding limit (>50MB for financial statements, >10MB for others)
   - Expected: Error message, upload rejected
3. **Extraction Timeout**: If document takes >2 minutes
   - Expected: Timeout error with retry option
4. **Missing API Key**: If LANDINGAI_API_KEY not configured
   - Expected: Server error message
5. **Partial Extraction**: If some fields cannot be extracted
   - Expected: Proceed with available data, show warnings

## Test Data Recommendations

For best results, use documents with known discrepancies:
- Different company names (e.g., "ROCSA COLOMBIA S.A." vs "AZELIS COLOMBIA S.A.S.")
- Mismatched NIT numbers
- Different legal representative names/IDs
- Suspicious email domains

Test documents from the Azelis fraud case are available at:
`/Example Files for Reqs/Azelis fraud case/`

## Notes

- AI extraction takes 30-60 seconds per document
- Full test with 6 documents may take 3-5 minutes for extraction
- Cross-validation runs quickly after extraction completes
- If LANDINGAI_API_KEY is not configured, extraction will fail
- Certificates of Existence (Certificado de Existencia) are optional - test can proceed without
