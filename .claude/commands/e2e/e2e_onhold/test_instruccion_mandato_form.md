# E2E Test: Instrucción de Mandato Form

Test the Mandato (IM) document generation workflow for Paga Local Colombia operations.

## User Story

As an operations team member or legal specialist
I want to upload Cotización and Certificado Bancario PDFs when generating Mandato (IM) documents
So that I can automatically extract creditor bank account information and generate accurate mandate instruction documents without manual data entry

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with operations or legal role exists
- Test client exists (NIT: 900436389 - DOM SAFETY PUERTO S.A.S.)
- Test PDFs available in `Example FIles for Reqs/`:
  - `Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf` (Cotización)
  - `certificado bancario.pdf` (Bank Certificate)

## Test Credentials

Use test account:
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

1. Navigate to http://localhost:5173
2. Complete login as operations user (if not already authenticated)
3. Navigate to `/operations/contratos-paga-local-colombia`
4. **Verify** page loads with main tabs visible
5. Click "Documentos de Operación" tab
6. **Verify** subtabs are visible: "Mandato (IM)", "Solicitud Desembolso", "DIAN Mandato (IM)"
7. Click "Mandato (IM)" subtab (should be first/default)
8. Take a screenshot: `01_empty_mandato_form.png` - Empty Mandato (IM) form
9. **Verify** form sections visible:
   - "1. Seleccionar Cliente" section with search input
   - "2. Cargar Cotización PDF" section

### Client Search Flow
10. In "Buscar por NIT o Nombre" field, enter: `900436389`
11. Click "Buscar" button
12. **Verify** search completes and client appears in results
13. Select the client from search results (or auto-select if only one result)
14. **Verify** "Cliente seleccionado" message appears with client name

### Cotización Upload Flow
15. Click "Seleccionar Archivo PDF" button in section 2
16. Upload the Cotización PDF file: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
17. **Verify** file name appears on the button
18. Click "Extraer Datos del PDF" button
19. Wait for extraction to complete (loading spinner)
20. **Verify** success message appears: "Datos extraídos exitosamente: X acreedor(es) encontrado(s)"
21. Take a screenshot: `02_cotizacion_extracted.png` - Form with extracted Cotización data

### Verify Extracted Data
22. **Verify** new form sections appear:
    - "3. Datos de la Instrucción de Mandato" with:
      - Número de Cotización de Desembolso (pre-filled)
      - Fecha del Contrato de Mandato (date field)
      - Monto Total (read-only)
    - "4. Información Bancaria de Acreedores" with creditor cards
23. **Verify** at least one creditor card is visible with fields:
    - Razón Social (pre-filled from Cotización)
    - NIT (optional)
    - Banco
    - Tipo de Cuenta (dropdown)
    - Número de Cuenta

### Bank Certificate Upload Flow
24. For the first creditor, click "Cargar Certificado Bancario" button
25. Upload the Bank Certificate PDF: `Example FIles for Reqs/certificado bancario.pdf`
26. **Verify** file name appears on the button
27. Click "Extraer Datos" button next to the file input
28. Wait for extraction to complete
29. **Verify** creditor fields are populated with extracted bank info:
    - Banco field has value
    - Tipo de Cuenta has value
    - Número de Cuenta has value
30. Take a screenshot: `03_bank_cert_extracted.png` - Form with extracted bank certificate data

### Manual Data Edit
31. Edit the "Fecha del Contrato de Mandato" field if not already set
32. **Verify** all required fields are filled:
    - Client selected
    - Número de Cotización de Desembolso filled
    - Fecha del Contrato de Mandato filled
    - At least one creditor with Banco, Tipo de Cuenta, and Número de Cuenta

### Document Generation
33. Scroll to section "5. Generar Documento"
34. **Verify** "Generar Instrucción de Mandato" button is enabled
35. Click "Generar Instrucción de Mandato" button
36. Wait for generation to complete (loading spinner)
37. **Verify** success message appears with contract ID
38. Take a screenshot: `04_generation_success.png` - Success message with contract ID
39. **Verify** contract ID format starts with "ACT-" or "IM-"

### Reset and New Document
40. Click "Generar Nueva Instrucción de Mandato" button
41. **Verify** form resets to initial state (section 1 and 2 visible, others hidden)
42. Take a screenshot: `05_form_reset.png` - Form after reset

## Success Criteria

- [x] Mandato (IM) tab displays specialized form (not generic form)
- [x] Client search works (search by NIT)
- [x] Client can be selected from search results
- [x] Cotización PDF upload accepts only PDF files
- [x] "Extraer Datos" button parses Cotización and populates form
- [x] Extracted data is displayed (numero_cotizacion, fecha, monto)
- [x] Creditor list displays from extracted anexo_items
- [x] Bank Certificate PDF upload works for each creditor
- [x] Bank Certificate extraction populates creditor bank info
- [x] Creditor bank info fields are visible (razon_social, nit, banco, tipo_cuenta, numero_cuenta)
- [x] Generate button calls API and succeeds
- [x] Success message shows contract ID after generation
- [x] Form can be reset for new document
- [x] 5 screenshots are captured

## Error Scenarios to Note

- Invalid PDF file type should show error: "Solo se permiten archivos PDF"
- PDF over 5MB should show error: "El archivo no debe superar 5MB"
- Cotización parsing failure should show user-friendly error
- Bank Certificate parsing failure should allow manual entry fallback
- Client not found should show error message
- Missing required creditor fields should show validation error
- Generate without client or acreedores should show validation error
