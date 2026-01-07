# E2E Test: Contador/Revisor Fiscal Cross-Validation

Test the Contador/Revisor Fiscal cross-validation feature in the Riesgos (Risk/Fraud Detection) module.

## User Story

As a Risk Analyst or Risk Manager
I want to validate that the contador/revisor fiscal signing financial statements matches the one registered in official documents
So that I can detect potential fraud involving fake or unauthorized financial statement signatories

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied
- Admin account exists with access to risk module
- Test documents prepared:
  - Certificado de Existencia PDF with contador/revisor fiscal information
  - Financial Statement PDF with signatory/auditor information

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL`
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (can access all risk features)

## Test Steps

### Part 1: Setup - Create Risk Evaluation

1. Navigate to the `Application URL` (http://localhost:5175)
2. Login with admin credentials
3. Navigate to `/risk/dashboard`
4. Click "Nueva Evaluación" button
5. Enter a valid client NIT
6. Click "Evaluar" button
7. **Verify** evaluation is created with status "pending_documents"
8. Navigate to the evaluation detail page (`/risk/evaluations/:id`)
9. Take a screenshot of the evaluation detail page

### Part 2: Upload Documents

10. In the "Documentos" section, upload a Certificado de Existencia PDF
    - The document should contain:
      - contador_name (registered accountant name)
      - contador_cedula (accountant ID)
      - revisor_fiscal_name (fiscal auditor name)
      - revisor_fiscal_cedula (auditor ID)
11. **Verify** Certificado upload shows "Pendiente" or "Procesando" status
12. Wait for extraction to complete
13. **Verify** extraction shows "Completado" status
14. Take a screenshot of successful Certificado extraction

15. Upload Financial Statement (Current Year) PDF
    - The document should contain:
      - signatory_name (person who signed the statement)
      - signatory_id (signatory's ID number)
      - auditor_name (auditor if different from signatory)
16. **Verify** Financial Statement upload shows extraction progress
17. Wait for extraction to complete
18. Take a screenshot of successful Financial Statement extraction

### Part 3: Trigger Cross-Validation

19. Click "Ejecutar Validación Cruzada" button
20. Wait for cross-validation to complete
21. **Verify** cross-validation results section appears
22. Take a screenshot of cross-validation results overview

### Part 4: Verify Contador/Revisor Fiscal Validation

23. In the cross-validation results, look for "Contador/Revisor Fiscal" validation type
24. **Verify** the validation type "Contador/Revisor Fiscal" appears in results
25. **Verify** the result shows one of the following:
    - **Verified (INFO)**: "Firmante verificado como contador/revisor fiscal registrado"
      - Shown in green
      - is_discrepancy = false
    - **Name Mismatch (HIGH)**: "Firmante no coincide con profesionales registrados"
      - Shown in red/orange
      - is_discrepancy = true
      - severity = high
    - **ID Mismatch (MEDIUM)**: "Discrepancia de cédula"
      - Shown in yellow/orange
      - is_discrepancy = true
      - severity = medium
    - **Not Found (CRITICAL)**: "Firmante no puede ser verificado"
      - Shown in red
      - is_discrepancy = true
      - severity = critical

26. Take a screenshot of the Contador/Revisor Fiscal validation result
27. **Verify** the `values_found` section shows extracted data:
    - From financial statement: signatory_name, signatory_id, auditor_name
    - From certificate: contador_name, contador_cedula, revisor_fiscal_name, revisor_fiscal_cedula
28. **Verify** the `documents_compared` shows both documents

### Part 5: Test Scenarios

#### Scenario A: Matching Contador (Verified)

29. Upload documents where:
    - Certificado has: contador_name = "JUAN CARLOS PEREZ"
    - Financial Statement has: signatory_name = "JUAN CARLOS PEREZ"
30. Run cross-validation
31. **Verify** result shows:
    - is_discrepancy = false
    - Description contains "verificado"
    - No score impact

#### Scenario B: Name Mismatch (HIGH Severity)

32. Upload documents where:
    - Certificado has: contador_name = "JUAN CARLOS PEREZ"
    - Financial Statement has: signatory_name = "MARIA GARCIA LOPEZ"
33. Run cross-validation
34. **Verify** result shows:
    - is_discrepancy = true
    - severity = high
    - score_impact = 15
    - Description contains "no coincide"

#### Scenario C: Cedula Mismatch (MEDIUM Severity)

35. Upload documents where:
    - Certificado has: contador_name = "JUAN CARLOS PEREZ", contador_cedula = "12345678"
    - Financial Statement has: signatory_name = "JUAN CARLOS PEREZ", signatory_id = "99999999"
36. Run cross-validation
37. **Verify** result shows:
    - is_discrepancy = true
    - severity = medium
    - score_impact = 8
    - Description contains "cédula"

#### Scenario D: No Registered Professionals (CRITICAL Severity)

38. Upload documents where:
    - Certificado has: contador_name = "", revisor_fiscal_name = ""
    - Financial Statement has: signatory_name = "JUAN CARLOS PEREZ"
39. Run cross-validation
40. **Verify** result shows:
    - is_discrepancy = true
    - severity = critical
    - score_impact = 25
    - Description contains "no puede ser verificado"

### Part 6: UI Label Verification

41. Navigate to the cross-validation results
42. **Verify** the validation type label shows "Contador/Revisor Fiscal" (Spanish)
43. **Verify** severity badges show correct colors:
    - Info: Green
    - Medium: Yellow/Orange
    - High: Orange/Red
    - Critical: Dark Red
44. Take a screenshot of the styled validation results

## Success Criteria

- Contador/Revisor Fiscal validation type appears in cross-validation results
- Correct severity levels are assigned based on match status:
  - INFO (0 points): Verified match
  - MEDIUM (8 points): Cedula mismatch only
  - HIGH (15 points): Name mismatch
  - CRITICAL (25 points): No registered professionals to compare
- Frontend displays "Contador/Revisor Fiscal" label correctly
- Values found section shows all relevant extracted data
- Documents compared shows both financial statement and certificate
- Fuzzy name matching works (e.g., "PEREZ GARCIA JUAN" matches "JUAN PEREZ GARCIA")
- Both current and prior financial statements are validated if present

## Error Scenarios to Note

- If no financial statement is uploaded, validation is skipped gracefully
- If certificate has no contador/revisor fiscal, CRITICAL severity is assigned
- If extraction fails, validation cannot proceed
- Network errors during validation should be handled gracefully

## Expected Screenshots

1. Evaluation detail page before document upload
2. Successful Certificado de Existencia extraction
3. Successful Financial Statement extraction
4. Cross-validation results overview
5. Contador/Revisor Fiscal validation result (matching)
6. Contador/Revisor Fiscal validation result (mismatch)
7. Styled validation results with severity colors
