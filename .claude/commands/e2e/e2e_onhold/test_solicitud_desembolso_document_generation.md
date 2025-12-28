# E2E Test: Solicitud de Desembolso Document Generation

Test that Solicitud de Desembolso Word documents are generated with all placeholders correctly filled in.

## User Story

As a Legal reviewer
I want to view a Solicitud de Desembolso document with all data populated
So that I can review and approve/reject the disbursement request

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with operations role
- Test client exists in database (NIT: 900436389 - SAFETY PUERTO S.A.S. or similar)
- Sample Cotización PDF available for upload (from previous tests or fixtures)

## Test Credentials

Operations user:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: operations

Legal user (for review):
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: legal

## Test Steps

### Part 1: Create Solicitud de Desembolso Request

1. Navigate to http://localhost:5173
2. Login as operations user
3. Navigate to Operations → Paga Local Colombia (`/operations/contratos-paga-local-colombia`)
4. Click the "Solicitud de Desembolso" tab
5. Take a screenshot of the Solicitud de Desembolso form
6. In the NIT search field, enter test client NIT (e.g., "900436389")
7. **Verify** client is found and selected (client name appears)
8. Upload a valid Cotización PDF file using the file upload button
9. Click "Extraer Datos" button
10. Wait for PDF parsing to complete
11. **Verify** extracted data appears in form:
    - Número de Cotización field is populated
    - Anexo items table shows extracted payment items
    - Monto total is calculated
12. Take a screenshot showing extracted data
13. Fill in any required fields:
    - Fecha Contrato Crédito (if not auto-filled)
    - Días de Plazo (e.g., 120)
14. Click "Solicitar Documento" button
15. Wait for success notification
16. **Verify** success message appears indicating document was created
17. Take a screenshot of success state

### Part 2: Download and Verify Document in Legal Review

18. Navigate to Legal module → Review Queue (`/department/legal` or similar)
19. **Verify** new contract appears with type "pl_co_solicitud_desembolso" or "PLSD"
20. Find the newly created Solicitud de Desembolso contract
21. Click to view/download the Word document
22. Take a screenshot of the review queue with the new contract highlighted

### Part 3: Verify Document Placeholders are Filled

23. Open the downloaded Word document
24. **Verify** the following placeholders are replaced with actual data:

| Placeholder | Expected Value | Location |
|-------------|----------------|----------|
| `[Número de cotización de desembolso]` | Quote number (e.g., CO:900436389:1:2:DOM) | Header table, Row 0 |
| `[día]` | Current day number (1-31) | Header table, Row 0 |
| `[mes]` | Current month name in Spanish | Header table, Row 0 |
| `202[•]` | Full year (e.g., 2025) | Header table, Row 0 |
| `[día de firma del contrato de crédito]` | Contract date day | Body text |
| `[mes de firma del contrato de crédito]` | Contract date month (Spanish) | Body text |
| `[ año de firma del contrato de crédito]` | Contract date year | Body text |
| `COP$[monto]` | Formatted amount (e.g., COP$739,860.00) | Condiciones section |
| `[número de días de plazo]` | Days (e.g., 120) | Condiciones section |

25. **Verify** Anexo I table is populated:
    - Data rows contain acreedor names
    - Data rows contain instrument numbers
    - Data rows contain formatted amounts
    - TOTAL row shows sum of all amounts
    - Empty placeholder rows (`[•]`) are cleared

26. Take a screenshot of the Word document showing:
    - Header with replaced placeholders
    - Body text with replaced date components
    - Condiciones section with monto and dias plazo
    - Anexo I table with populated data

## Success Criteria

- All form interactions work without errors
- PDF parsing extracts data correctly
- Document request is submitted successfully
- Document appears in Legal review queue
- Downloaded Word document has NO remaining `[...]` placeholders (except `[•]` which was handled)
- Specific data values appear in the document:
  - Quote number matches the extracted/entered value
  - Dates are formatted in Spanish (e.g., "7 de diciembre de 2025")
  - Amounts are formatted correctly (e.g., "739,860.00")
  - Dias de plazo matches entered value
  - Anexo I table has actual data rows with payment details

## Verification Checklist

- [ ] Login successful as operations user
- [ ] Client search by NIT works
- [ ] File upload accepts PDF
- [ ] "Extraer Datos" parses PDF and populates form
- [ ] "Solicitar Documento" creates contract successfully
- [ ] Contract visible in Legal review queue
- [ ] Word document downloadable
- [ ] `[Número de cotización de desembolso]` → replaced with quote number
- [ ] `[día]`, `[mes]`, `[•]` → replaced with current date components
- [ ] `[día de firma...]`, `[mes de firma...]`, `[ año de firma...]` → replaced with contract date
- [ ] `[monto]` → replaced with formatted amount
- [ ] `[número de días de plazo]` → replaced with days number
- [ ] Anexo I table populated with payment items
- [ ] TOTAL row shows correct sum
- [ ] 4-5 screenshots captured documenting the flow

## Error Scenarios to Note

- Empty Cotización PDF should show parsing error
- Invalid date format should be handled gracefully
- Missing required fields should show validation errors
- Network errors during document generation should show error message
