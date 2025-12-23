# E2E Test: Cross-Validation Multiple Representantes Legales

Test that the cross-validation system correctly handles companies with multiple legal representatives (Principal and Suplente), preventing false positive fraud alerts.

## User Story

As a Risk Analyst
I want the system to correctly validate companies with multiple Representantes Legales
So that I don't get false positive fraud alerts when the uploaded Cedula belongs to a Representante Legal Suplente

## Bug Context (Issue #10)

Colombian companies can have multiple legal representatives:
- **Representante Legal Principal** (marked as `REPRS LEGAL PRIN` in RUT)
- **Representantes Legales Suplentes** (marked as `REPRS LEGAL SUPL` in RUT)

Previously, the system only extracted and validated a single representative, causing false positives when a Cedula from a Suplente was uploaded.

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with `risk_analyst` or `risk_manager` role
- `LANDINGAI_API_KEY` environment variable configured in backend
- Test documents:
  - RUT with multiple representatives (Principal + at least one Suplente)
  - Cedula of a Representante Legal Suplente (NOT the principal)
  - Certificado de Existencia listing multiple representatives

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Part 1: Setup - Create New Evaluation

1. **Login as Risk Analyst** (or verify already logged in)
2. Navigate to `/risk/dashboard`
3. Click "Nueva Evaluación" button
4. Enter a test client NIT for a company known to have multiple representatives
5. Click "Iniciar Evaluación" button
6. **Verify** evaluation is created and redirects to detail page
7. Take a screenshot of the new evaluation

### Part 2: Upload Documents with Multiple Representatives

8. Navigate to the Documents section
9. **Upload RUT** with multiple representatives:
   - The RUT should have at least one REPRS LEGAL PRIN and one REPRS LEGAL SUPL
   - Take note of the Suplente's name and Cedula number
   - Click upload button for "RUT"
   - Select the PDF file
   - **Verify** upload success

10. **Upload Cedula of the SUPLENTE** (this is the key test case):
    - This Cedula should belong to the Representante Legal Suplente, NOT the principal
    - Click upload button for "Cédula del Representante Legal"
    - Select the Suplente's Cedula PDF/image
    - **Verify** upload success

11. **Upload Certificado de Existencia** (optional but recommended):
    - Should list multiple representatives if available
    - Click upload button for "Certificado de Existencia"
    - Select the PDF file
    - **Verify** upload success

12. Take a screenshot showing all uploaded documents

### Part 3: Trigger AI Extraction

13. Click the "Extraer Datos" button
14. Wait for extraction to complete (allow up to 2 minutes per document)
15. **Verify** extraction status changes to "Completado" for each document
16. **Verify** extracted data shows multiple representatives:
    - Click on RUT extraction preview
    - **Verify** `legal_representatives` array contains multiple entries
    - **Verify** both "principal" and "suplente" roles are present
17. Take a screenshot of the RUT extracted data showing multiple representatives

### Part 4: Run Cross-Validation

18. Navigate to "Validación Cruzada" tab or section
19. Click "Ejecutar Validación" button if manual trigger required
20. Wait for cross-validation to complete
21. Take a screenshot of validation results

### Part 5: Verify No False Positive (Critical Check)

22. **CRITICAL VERIFICATION**: Check legal representative validation result
    - Find the "Representante Legal" section in validation results
    - **Verify** NO discrepancy is shown for legal representative name
    - **Verify** NO discrepancy is shown for legal representative ID (Cédula)
    - The message should indicate the Suplente was matched successfully

23. **Verify** the validation message includes:
    - The matched representative's name
    - Their role (should show "Suplente")
    - The documents compared (RUT, Certificado)

24. Take a screenshot of the legal representative validation result showing:
    - ✅ No discrepancy
    - "Suplente" role identified
    - Successful match message

### Part 6: Negative Test - Unknown Person

25. Upload a Cedula for someone NOT in the representative list
26. Run cross-validation again
27. **Verify** discrepancy IS flagged:
    - Severity should be HIGH
    - Message should list all representatives that were checked
    - Both Principal and Suplente names should be mentioned in the error
28. Take a screenshot of the HIGH severity discrepancy

## Success Criteria

- [ ] RUT extraction includes `legal_representatives` array with multiple entries
- [ ] Each representative has `name`, `id_number`, and `role` fields
- [ ] Suplente's Cedula does NOT trigger false positive discrepancy
- [ ] Validation result shows "Suplente" role when matching Suplente
- [ ] Unknown person's Cedula correctly triggers HIGH severity discrepancy
- [ ] Discrepancy message lists all representatives that were checked
- [ ] No regression in Principal representative matching
- [ ] 5+ screenshots are captured:
  1. New evaluation page
  2. Uploaded documents
  3. RUT extracted data showing multiple representatives
  4. Validation results with NO discrepancy for Suplente
  5. Validation results WITH discrepancy for unknown person

## Expected Validation Messages

### Success Case (Suplente Match)
```
Nombre del representante legal verificado: MARIA GARCIA RODRIGUEZ (Suplente) - Coincide con RUT
Cédula del representante legal verificado: 87654321 (Suplente) - Coincide con RUT
```

### Failure Case (No Match)
```
Nombre en cédula (PEDRO UNKNOWN) no coincide con ningún representante legal.
Representantes encontrados: JUAN PEREZ (principal, rut), MARIA GARCIA (suplente, rut)
```

## Document Requirements

### RUT Document
The test RUT should contain the "Representación" section with:
- At least one entry marked as `REPRS LEGAL PRIN`
- At least one entry marked as `REPRS LEGAL SUPL`
- Clear identification numbers for each representative

### Cedula Document
- Must be the Cedula of one of the Suplente representatives
- Name and ID number should match the Suplente in the RUT

### Certificado de Existencia (Optional)
- Should list all representatives under "REPRESENTANTES LEGALES" section
- Should indicate which are principal and which are suplente

## Notes

- This test specifically targets Issue #10 (Azelis false positive case)
- The key behavioral change is that the system now checks ALL representatives, not just the principal
- Backward compatibility: Companies with only one representative should still work correctly
- Extraction may take 30-60 seconds per document due to AI processing
