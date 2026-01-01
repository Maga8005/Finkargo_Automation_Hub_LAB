# E2E Test: Email Chain Alerts PDF Table

Test that the email chain alerts table appears correctly in the comprehensive evaluation PDF report.

## User Story

As a Mesa de Control analyst (mesa_control role)
I want to see email chain alerts with their validation comments in the comprehensive evaluation PDF report
So that I can have a complete audit trail of all communication-related fraud indicators and the validation decisions made for each alert

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied (including email chain validations)
- Admin or mesa_control account exists with access to risk module
- At least one risk evaluation with email chains that have validated discrepancies

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) or a mesa_control user
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin or mesa_control

## Test Steps

### Part 1: Authentication and Navigation

1. Navigate to the `Application URL` (http://localhost:5175)
2. **Verify** login page is displayed
3. Enter admin/mesa_control email in email field
4. Enter password in password field
5. Click "Iniciar sesion" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/risk/dashboard`
8. **Verify** user can access `/risk/dashboard` (page loads successfully)
9. Take a screenshot of successful dashboard access

### Part 2: Navigate to Evaluation with Email Chain Data

10. Find an evaluation with email chains that have discrepancies
    - Look for evaluations with suspicious/critical email chain validation results
11. Click on the evaluation row to view details
12. **Verify** navigation to `/risk/evaluations/:id`
13. Navigate to the "Comunicacion Externa" tab (Tab 2)
14. **Verify** the tab shows email chain uploader section
15. Take a screenshot of external communication tab with email chains

### Part 3: Verify Email Chain Discrepancies Exist

16. Locate an email chain with HIGH, CRITICAL, or MEDIUM severity discrepancies
17. Expand the email chain to view its discrepancies
18. **Verify** at least one discrepancy shows:
    - Severity indicator (color-coded chip for critical, high, or medium)
    - Field label (e.g., "Dominio del Remitente", "Nombre de Empresa", "NIT")
    - Description of the issue
    - Validation controls (if user has permission)
19. If discrepancies exist but are not validated, validate at least one:
    - Select a validation reason from the dropdown
    - Enter a comment
    - Click "Guardar Validacion" button
20. Take a screenshot showing email chain with validated discrepancy

### Part 4: Export PDF Report

21. Navigate to the evaluation header area
22. Locate the "Exportar PDF" or "Reporte Completo" button
23. Click the button to generate the comprehensive evaluation PDF
24. **Verify** PDF downloads successfully (file appears in downloads)
25. Take a screenshot of the download confirmation or button state

### Part 5: Verify Email Chain Alerts Table in PDF

26. Open the downloaded PDF
27. **Verify** the PDF contains a section titled "Discrepancias en Cadenas de Email"
28. **Verify** the table includes columns:
    - Cadena (chain identifier/filename)
    - Campo (field - e.g., "Dominio del Remitente")
    - Severidad (severity - with color coding)
    - Valor (the email value that caused the discrepancy)
    - Descripcion (description of the issue)
    - Validacion (validation status - "Pendiente" or reason label)
    - Comentarios (analyst comments)
29. **Verify** only HIGH, CRITICAL, and MEDIUM severity discrepancies appear (no INFO)
30. **Verify** validated discrepancies show:
    - The validation reason label (e.g., "Validacion manual")
    - The analyst's comments (truncated if > 80 chars)
31. **Verify** unvalidated discrepancies show "Pendiente" in the validation column
32. Take a screenshot of the email chain alerts table in the PDF

### Part 6: Edge Cases

33. If no email chains exist, verify the table section does not appear
34. If email chains exist but all discrepancies are INFO severity, verify the table does not appear
35. If email chains have discrepancies but none are validated, verify "Pendiente" appears for all

## Success Criteria

- PDF export button works and generates a downloadable PDF
- PDF contains "Discrepancias en Cadenas de Email" table section
- Table only appears when HIGH, CRITICAL, or MEDIUM severity discrepancies exist
- Table columns match specification: Cadena, Campo, Severidad, Valor, Descripcion, Validacion, Comentarios
- Validated discrepancies show validation reason label (e.g., "Validacion manual")
- Validated discrepancies show analyst comments (truncated at 80 chars with "...")
- Unvalidated discrepancies show "Pendiente" in validation column
- Severity column uses color-coding (critical=red, high=orange, medium=yellow)
- Validation status column uses color-coding (Pendiente=orange, Validated=green)
- Table styling matches other tables in the report (grid theme, alternating rows)

## Error Scenarios to Note

- No email chains uploaded -> Table section should not appear
- Email chains with no discrepancies -> Table section should not appear
- All discrepancies are INFO severity -> Table section should not appear
- Discrepancy without validation -> Shows "Pendiente" status
- Discrepancy with validation but no comments -> Shows reason, "-" for comments
- Very long comments -> Truncated at 80 characters with "..."

## Expected Screenshots

1. Dashboard access (after login)
2. External communication tab with email chains
3. Email chain with validated discrepancy
4. Download confirmation or button state
5. Email chain alerts table in PDF (if viewable)
