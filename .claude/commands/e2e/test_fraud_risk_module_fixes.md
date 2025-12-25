# E2E Test: Fraud Risk Module Bug Fixes

Test the three bug fixes for the fraud risk module in the Finkargo Automation Hub application.

## User Story

As a Risk Analyst
I want to upload large Certificado de Existencia documents, validate external contacts with domain info, and validate email chains with NIT mentions
So that I can complete comprehensive risk evaluations without encountering file size limits or validation errors

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation in progress
- A PDF file larger than 10MB but smaller than 50MB for testing file upload
- Sample email text containing NIT mentions

## Test Credentials

Use test account with appropriate role:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Setup

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. Take a screenshot of the Risk Dashboard
7. Create a new risk evaluation or open an existing one

### Bug 1: Large File Upload for Certificado de Existencia

8. Navigate to the "Documentos" tab (Tab 1)
9. **Verify** document upload section is visible
10. Take a screenshot of the document upload area
11. Locate the "Certificado de Existencia" upload section
12. **Verify** the section displays maximum file size of 50MB (not 10MB)
13. Attempt to upload a PDF file between 10MB and 50MB (e.g., 30MB)
14. **Verify** upload succeeds without "File too large" error
15. **Verify** file appears in the uploaded documents list
16. Take a screenshot of the successful upload
17. **Verify** document processing/extraction begins

### Bug 2: Domain DNS/Age Check for External Contacts

18. Navigate to "Contactos Externos" tab (Tab 3)
19. **Verify** external contact section is visible
20. Click "Agregar Contacto" or equivalent button
21. Add a new external contact with a corporate email (e.g., contact@example-company.com)
22. Click "Guardar" to save the contact
23. Take a screenshot of the saved contact
24. Click "Validar" button for the contact
25. Wait for validation to complete
26. **Verify** validation results display domain information:
    - Domain existence status (resolved/not resolved)
    - Domain age in days/months/years
    - Color-coded chip for domain age (red <90 days, yellow <1 year, green >=1 year)
27. Take a screenshot of the validation results with domain info

### Bug 3: Email Chain Validation with NIT Mentions

28. Navigate to "Cadenas de Email" section within the External Contact tab
29. **Verify** email chain upload area is present
30. Paste sample email text containing NIT mentions:
    ```
    From: proveedor@empresa.com.co
    To: comercial@finkargo.com
    Date: Tue, 24 Dec 2024 10:00:00 -0500
    Subject: Datos Bancarios - Empresa XYZ

    Estimados,

    Adjunto los datos para el pago:
    NIT: 830.116.134-9
    Cuenta Bancaria: 1234567890

    Saludos,
    Empresa XYZ
    ```
31. Click "Subir" button
32. **Verify** email chain appears in the list without errors
33. Take a screenshot of the uploaded email chain
34. Click "Validar" button for the email chain
35. Wait for validation to complete
36. **Verify** validation completes without Pydantic validation errors
37. **Verify** NIT is extracted and displayed correctly (830116134-9 or similar format)
38. **Verify** NIT comparison against document data is displayed (if documents contain NIT)
39. Take a screenshot of the validation results with NIT information
40. **Verify** validation status shows appropriate level (Validado/Sospechoso/Crítico)

### Cleanup

41. Delete the test email chain
42. **Verify** chain is removed from the list
43. Take a final screenshot

## Success Criteria

### Bug 1: File Size Limit
- Certificado de Existencia section shows 50MB limit (not 10MB)
- Files between 10MB and 50MB upload successfully
- No "File too large. Maximum: 10MB" error appears
- Document appears in uploaded list after successful upload

### Bug 2: Domain DNS/Age Check
- External contact validation shows domain existence status
- Domain age information is displayed when available
- Domain age is color-coded appropriately:
  - Red: <90 days (high risk)
  - Yellow: <1 year (medium risk)
  - Green: >=1 year (low risk)
- Domain registrar info shown when available

### Bug 3: Email Chain NIT Validation
- Email chain with NIT mentions uploads without errors
- Validation completes without Pydantic validation errors
- NIT is extracted and displayed in proper format
- NIT comparison with document data works correctly
- No error like "Input should be a valid string [type=string_type, input_value=['830116134', '9'], input_type=list]"

## Screenshots to Capture

1. Risk Dashboard initial state
2. Document upload area showing 50MB limit
3. Successful large file upload
4. External contact validation with domain info
5. Email chain upload (pending status)
6. Email chain validation results with NIT
7. Final state after cleanup

## Error Scenarios to Note

- Files larger than 50MB should still be rejected for Certificado de Existencia
- Files larger than 5MB should be rejected for RUT and Cedula (unchanged limits)
- Domain validation may show "unavailable" for some domains (WHOIS restrictions)
- NITs without check digit should still validate correctly
