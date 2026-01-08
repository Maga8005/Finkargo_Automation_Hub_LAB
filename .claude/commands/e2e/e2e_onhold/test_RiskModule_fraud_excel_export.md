# E2E Test: Fraud Risk Module - Excel Export for Document Extractions

Test the Excel export functionality for extracted document data in the fraud risk evaluation workflow.

## User Story

As a Risk Analyst or Risk Manager
I want to export extracted document data to Excel from the fraud evaluation documents screen
So that I can perform additional manual analysis on the extracted information using spreadsheet tools

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (risk tables)
- Admin account exists (admin@finkargo.com) with full system access
- At least one risk evaluation with completed document extractions exists

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (can access all risk features)

## Test Steps

### Part 1: Authentication and Access

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter admin email (`$TEST_ADMIN_EMAIL`) in email field
4. Enter admin password (`$TEST_ADMIN_PASSWORD`) in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/risk/dashboard`
8. **Verify** user can access `/risk/dashboard` (page loads successfully)
9. Take a screenshot of successful dashboard access

### Part 2: Navigate to Evaluation with Document Extractions

10. Find an evaluation in the table that has documents uploaded (look for status "pending_documents" or completed evaluations)
11. Click on the evaluation row to view details
12. **Verify** navigation to `/risk/evaluations/:id`
13. Take a screenshot of evaluation detail page

### Part 3: Access Documents Tab

14. Click on the "Documentos" tab if not already active
15. **Verify** the FKDocumentUploader component is visible
16. **Verify** document cards are displayed showing document types:
    - Estados Financieros (Año Actual)
    - Estados Financieros (Año Anterior)
    - Cédula del Representante Legal
    - Composición Accionaria
    - RUT
    - Certificado de Existencia
17. Take a screenshot of the documents section

### Part 4: Verify Export Button Visibility

18. **Verify** "Exportar a Excel" button is visible in the documents header section (next to "Actualizar" button)
19. **Verify** button has a download icon
20. Check if the button is enabled or disabled based on completed extractions:
    - If no completed extractions → Button should be disabled with tooltip explaining why
    - If at least 1 completed extraction → Button should be enabled
21. Take a screenshot showing the export button state

### Part 5: Export Excel File (with completed extractions)

22. If there are completed extractions (status shows "Completado" chip):
    a. Click the "Exportar a Excel" button
    b. **Verify** button shows loading indicator during export generation
    c. **Verify** Excel file downloads (file named `documentos_extraidos_{assessment_id}_{date}.xlsx`)
    d. **Verify** success feedback is shown (snackbar or visual confirmation)
    e. Take a screenshot after successful export
23. If no completed extractions exist:
    a. **Verify** button shows disabled state
    b. Hover over button to see tooltip message "No hay datos extraídos para exportar"
    c. Take a screenshot of disabled state with tooltip

### Part 6: Verify Excel File Contents (Manual Verification)

24. Open the downloaded Excel file
25. **Verify** file contains "Resumen" sheet with:
    - ID Evaluación
    - NIT Cliente
    - Fecha Exportación
    - Documentos Procesados
    - Documentos Totales
26. **Verify** file contains sheets for each completed document type:
    - "Estados Financieros" (if financial statements were extracted)
    - "Cédula" (if ID document was extracted)
    - "Composición Accionaria" (if shareholder data was extracted)
    - "RUT" (if tax registration was extracted)
    - "Certificado Existencia" (if existence certificate was extracted)
27. **Verify** data in sheets matches the extracted data shown in the UI
28. Take a screenshot of Excel file contents (if possible)

### Part 7: Edge Cases

29. Navigate to a new evaluation or one without documents
30. **Verify** export button is disabled when no completed extractions exist
31. **Verify** tooltip shows "No hay datos extraídos para exportar"
32. Take a screenshot of disabled export button

## Success Criteria

- Export button is visible in the Documents section header
- Button is disabled when no completed extractions exist
- Button shows appropriate tooltip when disabled
- Clicking enabled button triggers Excel file download
- Excel file name follows pattern: `documentos_extraidos_{assessment_id}_{date}.xlsx`
- Excel file contains Resumen sheet with metadata
- Excel file contains sheets for each completed document type
- No console errors during export process
- Button re-enables after export completes
- Success feedback is shown to user after export

## Error Scenarios to Note

- Network errors should be handled gracefully
- Empty extractions should show info message, not error
- Large datasets should not cause browser to freeze
- Special characters in company names should be handled properly

## Expected Screenshots

1. Dashboard access after login
2. Evaluation detail page
3. Documents section with document cards
4. Export button state (enabled/disabled)
5. Export in progress (loading state)
6. Successful export completion
7. Excel file contents (optional)
8. Disabled button with tooltip (edge case)
