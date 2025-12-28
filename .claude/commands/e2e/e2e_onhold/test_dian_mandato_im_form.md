# E2E Test: DIAN Mandato (IM) Form

Test the DIAN Mandato (IM) document generation workflow for Paga Local Colombia operations.

## User Story

As an operations team member
I want to upload a Cotización PDF and generate DIAN Mandato (IM) documents
So that I can quickly authorize Finkargo to make payments to DIAN on behalf of clients without needing to collect bank certificates

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with operations or legal role exists
- Test client exists (NIT: 900436389 - DOM SAFETY PUERTO S.A.S.)
- Test Cotización PDF available in `Example FIles for Reqs/`:
  - `Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf` (Cotización)
- Database migration for DIAN template has been run

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: operations

## Test Steps

1. Navigate to http://localhost:5173
2. Complete login as operations user (if not already authenticated)
3. Navigate to `/operations/contratos-paga-local-colombia`
4. **Verify** page loads with main tabs visible
5. Click "Documentos de Operación" tab
6. **Verify** subtabs are visible: "Mandato (IM)", "Solicitud Desembolso", "DIAN Mandato (IM)"
7. Click "DIAN Mandato (IM)" subtab (third tab)
8. Take a screenshot: `01_empty_dian_mandato_form.png` - Empty DIAN Mandato (IM) form
9. **Verify** form sections visible:
   - "Template DIAN - Mandato (IM)" header
   - "Documento simplificado para pagos a la DIAN" description
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
20. **Verify** success message appears: "Datos extraídos exitosamente del documento de cotización"
21. Take a screenshot: `02_cotizacion_extracted.png` - Form with extracted Cotización data

### Verify Extracted Data (Section 3)
22. **Verify** new form section "3. Datos del DIAN Mandato (IM)" appears with:
    - Número de Cotización de Desembolso (pre-filled)
    - Fecha del Contrato de Mandato (date field)
    - Monto Total (COP) (pre-filled)
23. **Verify** info alert: "Este documento es para pagos a la DIAN. No se requiere información bancaria adicional."
24. **Verify** NO Bank Certificate upload section is shown (key difference from regular Mandato)
25. Take a screenshot: `03_dian_mandato_data_review.png` - Data review section

### Manual Data Edit
26. Edit the "Fecha del Contrato de Mandato" field if not already set
27. **Verify** all required fields are filled:
    - Client selected
    - Número de Cotización de Desembolso filled
    - Fecha del Contrato de Mandato filled
    - Monto Total greater than 0

### Document Generation (Section 4)
28. **Verify** section "4. Generar Documento" is visible
29. **Verify** "Generar DIAN Mandato (IM)" button is enabled
30. Click "Generar DIAN Mandato (IM)" button
31. Wait for generation to complete (loading spinner)
32. **Verify** success message appears with contract ID
33. Take a screenshot: `04_generation_success.png` - Success message with contract ID
34. **Verify** contract ID format starts with "PLDI-" (DIAN prefix)
35. **Verify** "Tipo de Documento" shows "DIAN Mandato (IM)"
36. **Verify** "Estado" shows "En Revisión"

### Reset and New Document
37. Click "Generar Nuevo DIAN Mandato (IM)" button
38. **Verify** form resets to initial state (section 1 and 2 visible, section 3 hidden)
39. Take a screenshot: `05_form_reset.png` - Form after reset

## Success Criteria

- [x] DIAN Mandato (IM) tab displays specialized form (not generic form)
- [x] Form shows "Documento simplificado para pagos a la DIAN" description
- [x] Client search works (search by NIT)
- [x] Client can be selected from search results
- [x] Cotización PDF upload accepts only PDF files
- [x] "Extraer Datos" button parses Cotización and populates form
- [x] Extracted data is displayed (numero_cotizacion, fecha, monto)
- [x] **NO Bank Certificate upload section is shown** (key difference)
- [x] Info alert explains this is for DIAN payments
- [x] Generate button calls API and succeeds
- [x] Success message shows contract ID starting with "PLDI-"
- [x] Document type shows "DIAN Mandato (IM)"
- [x] Form can be reset for new document
- [x] 5 screenshots are captured

## Error Scenarios to Note

- Invalid PDF file type should show error: "Solo se permiten archivos PDF"
- PDF over 5MB should show error: "El archivo no debe superar 5MB"
- Cotización parsing failure should show user-friendly error
- Client not found should show error message
- Missing required fields should disable Generate button
- Monto zero or negative should show validation error
- Generate without client should show error: "Por favor seleccione un cliente"

## Key Differences from Regular Mandato (IM)

| Aspect | Regular Mandato (IM) | DIAN Mandato (IM) |
|--------|---------------------|-------------------|
| Bank Certificate | Required | NOT required |
| Creditor fields | Shown (banco, cuenta) | NOT shown |
| Contract ID prefix | PLMI- | PLDI- |
| Info message | - | "para pagos a la DIAN" |
