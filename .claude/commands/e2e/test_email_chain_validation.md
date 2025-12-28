# E2E Test: Email Chain Validation

Test the email chain similarity validation fix for the Fraud Risk module in the Finkargo Automation Hub application.

## User Story

As a Risk Analyst
I want to validate email chains containing company names and representative names against document-extracted data
So that I can detect potential fraud through name variations and mismatches without encountering AttributeError

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation in progress with at least one document uploaded (preferably Certificado de Existencia or RUT)

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (has access to all risk features)

## Test Steps

### Setup

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. Take a screenshot of the Risk Dashboard
7. Create a new risk evaluation or open an existing one (e.g., RISK-2025-034)

### Test Case 1: Email Chain Upload with Company Names

8. Navigate to the "Contactos Externos / Cadenas de Email" section (Tab 3)
9. **Verify** email chain upload area is present
10. Take a screenshot of the email chain section
11. Locate the text input or paste area for email chain content
12. Paste sample email text containing company names and representative names:
    ```
    From: comercial@multivalvulas.com.co
    To: operaciones@finkargo.com
    Date: Wed, 25 Dec 2024 09:30:00 -0500
    Subject: Datos de Pago - Multivalvulas Colombia S.A.S.

    Buenos dias,

    Les envio los datos para el pago correspondiente:

    Empresa: MULTIVALVULAS COLOMBIA S.A.S.
    NIT: 900.123.456-7
    Representante Legal: JUAN CARLOS RODRIGUEZ MARTINEZ
    Cuenta Bancaria: Bancolombia 123-456789-01

    Quedamos atentos.

    Cordialmente,
    Maria Jose Garcia
    Departamento Comercial
    Multivalvulas Colombia
    ```
13. Click "Subir" or "Guardar" button to upload the email chain
14. **Verify** email chain appears in the list without errors
15. Take a screenshot of the uploaded email chain

### Test Case 2: Email Chain Validation (Bug Fix Verification)

16. Locate the uploaded email chain in the list
17. Click "Validar" (Validate) button for the email chain
18. Wait for validation to complete (may take a few seconds)
19. **Verify** NO error message appears with text "'NormalizationService' object has no attribute 'calculate_similarity'"
20. **Verify** NO error message appears with text "'NormalizationService' object has no attribute 'normalize_name'"
21. **Verify** validation completes successfully
22. Take a screenshot of the validation results

### Test Case 3: Validation Results Analysis

23. **Verify** validation result summary is displayed with:
    - Total discrepancies count
    - Severity breakdown (critical, high, medium, low, info)
    - Overall status (Validado/Sospechoso/Crítico)
24. **Verify** company name comparison results are shown:
    - Company name from email vs document company name
    - Similarity percentage (if applicable)
25. **Verify** representative name comparison results are shown (if applicable):
    - Representative name from email vs document representative
    - Similarity percentage (if applicable)
26. Take a screenshot of the detailed validation breakdown

### Test Case 4: Similar Names Detection

27. Upload another email chain with a slightly different company name:
    ```
    From: ventas@multivalvulas.co
    To: comercial@finkargo.com
    Date: Thu, 26 Dec 2024 14:00:00 -0500
    Subject: Informacion Comercial

    Buen dia,

    Somos MULTI VALVULAS DE COLOMBIA S.A.S. (NIT 900.123.456-7)

    Representante: JUAN C. RODRIGUEZ M.

    Saludos,
    ```
28. Click "Subir" button
29. Click "Validar" button
30. **Verify** validation detects the company name variation:
    - "MULTI VALVULAS DE COLOMBIA S.A.S." vs "MULTIVALVULAS COLOMBIA S.A.S."
    - Similarity score should be displayed (expected: 70-90%)
31. **Verify** representative name variation is detected:
    - "JUAN C. RODRIGUEZ M." vs "JUAN CARLOS RODRIGUEZ MARTINEZ"
    - Similarity score should be displayed
32. Take a screenshot of the similarity detection results

### Cleanup

33. Delete the test email chains
34. **Verify** chains are removed from the list
35. Take a final screenshot

## Success Criteria

### Bug Fix Verification
- Email chain validation completes without AttributeError
- No error: "'NormalizationService' object has no attribute 'calculate_similarity'"
- No error: "'NormalizationService' object has no attribute 'normalize_name'"
- Validation results display properly

### Company Name Comparison
- Company names are normalized and compared
- Similarity percentage is calculated correctly
- Variations like "S.A.S." vs "S A S" are treated as equivalent
- Legal suffixes are properly removed for comparison

### Representative Name Comparison
- Person names are normalized (accents removed, uppercase)
- Similarity percentage is calculated for name variations
- Abbreviated names are compared against full names

### Validation Status
- Overall validation status reflects discrepancy severity
- Critical/High/Medium/Low severity levels work correctly
- Summary message is displayed in Spanish

## Screenshots to Capture

1. Risk Dashboard initial state
2. Email chain section before upload
3. Uploaded email chain (pending validation)
4. Validation results (after successful validation)
5. Detailed validation breakdown with similarity scores
6. Second email chain validation with name variations
7. Final state after cleanup

## Error Scenarios to Note

- If the bug fix was NOT applied, you will see:
  - Error: "Error validating email chain: 'NormalizationService' object has no attribute 'calculate_similarity'"
  - This should NOT happen after the fix

- If documents haven't been uploaded yet:
  - Company/representative comparison may show limited results
  - This is expected behavior, not an error

- If domain validation takes too long:
  - DNS/WHOIS lookups may timeout
  - Validation will still complete with available data
