# E2E Test: RUT DV (Dígito de Verificación) Extraction

Test the correct extraction of the verification digit (DV) from Colombian RUT documents in the Riesgos (Risk) module.

## User Story

As a Risk Analyst
I want the system to correctly extract the DV (dígito de verificación) from field 6.DV in RUT documents
So that the NIT validation and cross-document verification works correctly

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk analyst role exists
- Test RUT document available (e.g., Azelis RUT where DV should be 3)

## Test Credentials

Use test account (configure in test environment):
- Email: test-riesgos@finkargo.com
- Password: [configured test password]
- Expected Role: analyst or riesgos

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Enter test email in email field
4. Enter test password in password field
5. Click "Iniciar Sesión" button
6. Wait for authentication to complete
7. **Verify** successful login and redirect to dashboard
8. Navigate to the Riesgos (Risk) module via sidebar menu
9. Take a screenshot of the Risk dashboard
10. Create a new risk evaluation or select an existing one for a test client
11. Take a screenshot of the risk evaluation page
12. Upload a test RUT document (use a document where the DV is known, e.g., Azelis with DV=3)
13. Wait for the document upload to complete
14. Trigger AI extraction for the RUT document (click extract button or wait for auto-extraction)
15. Wait for extraction to complete (loading state ends)
16. Take a screenshot of the extracted data
17. **Verify** the extracted NIT field:
    - NIT should be in format "XXXXXXXXX-D" where D is a single digit
    - The DV (digit after the hyphen) should match the expected value from field 6.DV in the document
    - For Azelis RUT test document, the DV should be 3 (e.g., "830027231-3")
18. **Verify** the NIT components are correctly extracted:
    - Base NIT (9 digits before the hyphen) matches field 5 in the RUT
    - DV (single digit after the hyphen) matches field 6.DV in the RUT
19. Take a screenshot showing the verified NIT with correct DV

## Success Criteria

- Risk module loads without errors
- RUT document upload completes successfully
- AI extraction runs without errors
- Extracted NIT is in correct format (XXXXXXXXX-D)
- The DV digit matches the value from field 6.DV in the RUT document
- For test documents with known DV values:
  - Azelis RUT: DV should be 3
  - Other test documents: DV should match the value shown in field 6.DV
- 4 screenshots are captured:
  1. Risk dashboard after login
  2. Risk evaluation page
  3. Extracted data showing NIT
  4. Verified NIT with correct DV

## Error Scenarios to Note

- If DV is extracted incorrectly (different from field 6.DV value), mark test as FAILED
- If NIT format is incorrect (missing hyphen, wrong digit count), mark test as FAILED
- Document upload failures should be reported
- Extraction timeout or errors should be handled gracefully

## Technical Notes

- The DV (dígito de verificación) is located in field 6.DV in Colombian RUT documents
- Field 6.DV is a small field immediately to the right of field 5 (NIT)
- The AI extraction should identify this specific field labeled "6.DV"
- The extraction schema in `document_extraction_service.py` provides explicit guidance about field 6.DV location
