# E2E Test: Solicitud de Desembolso Generation

Test the Solicitud de Desembolso contract generation workflow for Operations users in Paga Local Colombia.

## User Story

As an Operations team member
I want to generate a Solicitud de Desembolso document by uploading a Cotización PDF
So that Legal can review and approve the disbursement request for a client

## Prerequisites

- User logged in with `operations` role
- Backend and frontend servers running
- At least one client exists in the database (searchable by NIT)
- A valid Cotización PDF file is available for upload

## Test Steps

1. **Login as Operations user** (or verify already logged in with operations role)
2. Navigate to `/operations/paga-local-colombia`
3. Take a screenshot of the Paga Local Colombia dashboard
4. **Verify** dashboard loads with Solicitud de Desembolso option visible

5. Click on "Solicitud de Desembolso" tab or navigation item
6. **Verify** Solicitud de Desembolso form appears (FKSolicitudDesembolsoRequest component)
7. Take a screenshot of the empty Solicitud de Desembolso form

8. **Fill out Section 1 - Client Search:**
   - Search for client by NIT or name (use a test client e.g., "strong" or NIT: 900436389)
   - **Verify** client autocomplete/search returns results
   - Select a client from results
   - **Verify** client information is shown (company name, NIT)
   - Take a screenshot showing selected client

9. **Fill out Section 2 - Cotización PDF Upload:**
   - Click "Seleccionar Archivo PDF" button
   - Upload a valid Cotización PDF file
   - **Verify** file name is displayed after upload
   - Click "Extraer Datos del PDF" button
   - Wait for PDF extraction to complete
   - **Verify** success message shows extracted items count
   - Take a screenshot after data extraction

10. **Verify Section 3 - Extracted Data:**
    - **Verify** "Número de Cotización de Desembolso" field is populated
    - **Verify** "Fecha del Contrato de Crédito" field is populated
    - **Verify** "Días de Plazo" field shows default value (120)
    - **Verify** "Monto Total" field shows calculated total

11. **Verify Section 4 - Anexo I Table:**
    - **Verify** table has at least one row with acreedor, instrumento, monto data
    - **Verify** total amount row matches sum of all items
    - Take a screenshot of the filled form with Anexo I table

12. **Submit the request:**
    - Click "Solicitar Documento" button
    - Wait for form submission to complete
    - **Verify** success message appears showing "Solicitud de Desembolso Generada Exitosamente"
    - **Verify** contract ID is displayed (format: PLSD-{YEAR}-{SEQUENCE})
    - **Verify** status shows "En Revisión"
    - Take a screenshot of the success confirmation

## Success Criteria
- Solicitud de Desembolso form loads correctly
- Client search functionality works
- PDF upload and extraction works
- Extracted data populates form fields correctly
- Anexo I table displays extracted items
- Form submission succeeds (NO 500 error - this was the bug)
- Contract is created with correct status ("under_review")
- Contract ID follows format: PLSD-{YEAR}-{SEQUENCE}
- Success feedback is displayed to user with contract details
- 6 screenshots are captured:
  1. Paga Local Colombia dashboard
  2. Empty Solicitud de Desembolso form
  3. Form with selected client
  4. Form after PDF data extraction
  5. Filled form with Anexo I table
  6. Success confirmation screen

## Form Fields to Verify
- Client NIT (selected from search)
- Client company name (displayed after selection)
- Cotización PDF file (uploaded)
- Número de Cotización de Desembolso (extracted from PDF)
- Fecha del Contrato de Crédito (extracted from PDF or entered)
- Días de Plazo (default: 120)
- Monto Total (calculated from Anexo I items)
- Anexo I table items: Acreedor, No. Instrumento, Monto

## Bug Validation
This test validates the fixes for multiple bugs:

1. **Missing template record bug:**
   - **Error:** "No active contract template found for type: pl_co_solicitud_desembolso"
   - **Fix:** Added database migration `migration_add_solicitud_desembolso_template.sql` to insert template record

2. **Dict attribute error bug:**
   - **Error:** "'dict' object has no attribute 'nit'" (HTTP 500)
   - **Fix:** Updated backend code to handle dict response properly

**Before fixes:** Clicking "Solicitar Documento" returned error messages
**After fixes:** Contract is generated successfully with PLSD-YYYY-XXX ID and confirmation message
