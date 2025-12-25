# E2E Test: DIAN Checkbox for Instruccion de Mandato

Test the unified DIAN checkbox feature in the Mandato (IM) document generation workflow.

## User Story

As an Operations team member
I want to mark individual creditors as DIAN payments in a single Instruccion de Mandato form
So that I can generate a unified document for mixed DIAN and non-DIAN creditors without manual document merging

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with operations role exists
- Test client exists (NIT: 900436389 - DOM SAFETY PUERTO S.A.S.)
- Test PDFs available in `Example FIles for Reqs/`:
  - `Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf` (Cotizacion)
  - `certificado bancario.pdf` (Bank Certificate)

## Test Credentials

Use test account:
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

### Setup and Navigation
1. Navigate to http://localhost:5173
2. Complete login as operations user (if not already authenticated)
3. Navigate to `/operations/contratos-paga-local-colombia`
4. **Verify** page loads with main tabs visible
5. Click "Documentos de Operacion" tab
6. Click "Mandato (IM)" subtab
7. Take a screenshot: `01_empty_mandato_form.png` - Empty Mandato (IM) form

### Client Search Flow
8. In "Buscar por NIT o Nombre" field, enter: `900436389`
9. Click "Buscar" button
10. **Verify** search completes and client appears in results
11. Select the client from search results
12. **Verify** "Cliente seleccionado" message appears

### Cotizacion Upload and DIAN Auto-Detection
13. Click "Seleccionar Archivo PDF" button in section 2
14. Upload the Cotizacion PDF file
15. Click "Extraer Datos del PDF" button
16. Wait for extraction to complete
17. **Verify** success message appears with creditor count
18. Take a screenshot: `02_cotizacion_extracted.png` - Form with extracted data

### Verify DIAN Checkbox Presence
19. Scroll to "4. Informacion Bancaria de Acreedores" section
20. **Verify** each creditor card has an "Es DIAN" checkbox visible
21. **Verify** checkbox label reads "Es DIAN (Transferencia electronica PSE a la DIAN)"
22. Take a screenshot: `03_dian_checkbox_visible.png` - Creditor card with DIAN checkbox

### Test DIAN Checkbox Toggle ON
23. Check the "Es DIAN" checkbox for the first creditor
24. **Verify** the following auto-fill occurs:
    - Razon Social: "Transferencia electronica PSE a favor de la DIAN"
    - Banco: "DIAN"
    - Tipo de Cuenta: "PSE"
    - Numero de Cuenta: "N/A"
25. **Verify** bank certificate upload section is hidden for DIAN creditor
26. **Verify** DIAN creditor card has visual indicator (DIAN chip/badge)
27. **Verify** info alert appears: "Este acreedor es un pago DIAN..."
28. Take a screenshot: `04_dian_checkbox_checked.png` - Creditor with DIAN checked

### Test DIAN Checkbox Toggle OFF
29. Uncheck the "Es DIAN" checkbox for the first creditor
30. **Verify** fields are cleared for manual entry
31. **Verify** bank certificate upload section reappears
32. **Verify** DIAN chip/badge is removed
33. Take a screenshot: `05_dian_checkbox_unchecked.png` - Creditor with DIAN unchecked

### Test Mixed DIAN and Non-DIAN Creditors
34. If only one creditor exists, click "Agregar Acreedor" to add a second
35. Check "Es DIAN" for the first creditor
36. Leave second creditor as non-DIAN
37. For the non-DIAN creditor, upload bank certificate and extract data (or fill manually)
38. **Verify** first creditor shows DIAN read-only info
39. **Verify** second creditor shows editable fields and bank cert upload
40. Take a screenshot: `06_mixed_dian_nondian.png` - Mixed creditor types

### Verify Form Validation
41. Set "Fecha del Contrato de Mandato" field to today's date
42. **Verify** "Generar Instruccion de Mandato" button is enabled
43. For non-DIAN creditor, ensure all required fields are filled:
    - Razon Social
    - Banco
    - Tipo de Cuenta
    - Numero de Cuenta

### Document Generation with Mixed Creditors
44. Click "Generar Instruccion de Mandato" button
45. Wait for generation to complete
46. **Verify** success message appears with contract ID
47. Take a screenshot: `07_generation_success.png` - Success with mixed creditors

### Reset and Verify
48. Click "Generar Nueva Instruccion de Mandato" button
49. **Verify** form resets to initial state
50. Take a screenshot: `08_form_reset.png` - Form after reset

## Success Criteria

- [x] "Es DIAN" checkbox is visible for each creditor row
- [x] Checking DIAN auto-fills predefined wording ("Transferencia electronica PSE a favor de la DIAN")
- [x] Checking DIAN disables/hides bank certificate upload for that row
- [x] Checking DIAN auto-fills: banco="DIAN", tipo_cuenta="PSE", numero_cuenta="N/A"
- [x] Unchecking DIAN enables all fields and bank cert upload
- [x] Multiple mixed creditors (DIAN + non-DIAN) can be in same form
- [x] Account type correctly shows "PSE" for DIAN (not "PC")
- [x] DIAN creditors show visual indicator (chip/badge)
- [x] Generated document is created successfully with mixed creditors
- [x] User can manually override auto-detection (toggle DIAN checkbox)
- [x] 8 screenshots are captured

## Error Scenarios to Note

- Toggling DIAN checkbox should clear bank certificate file for that creditor
- DIAN creditor without proper auto-fill should show validation error
- Form should not submit if non-DIAN creditor is missing required fields
- DIAN auto-detection should NOT trigger on words like "GUARDIAN" (false positive)

## DIAN Auto-Detection Keywords

The following patterns should auto-check the DIAN checkbox when found in creditor name:
- "DIAN" (as standalone word, not part of other words)
- "Direccion de Impuestos"
- "Aduanas Nacionales"
- "Entidad de pago de Impuestos"

## Expected DIAN Creditor Values

When DIAN checkbox is checked:
```
razon_social: "Transferencia electronica PSE a favor de la DIAN"
nit: "N/A"
banco: "DIAN"
tipo_cuenta: "PSE"
numero_cuenta: "N/A"
es_dian: true
```
