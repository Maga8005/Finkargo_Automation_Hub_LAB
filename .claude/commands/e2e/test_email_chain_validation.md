# E2E Test: Email Chain Validation

Test email chain upload and cross-validation flow for the Finkargo Risk Assessment system.

## User Story

As a Risk Analyst or Admin
I want to upload email chains/threads received during commercial communications
So that I can automatically cross-validate sender information against document-extracted data and detect potential fraud indicators like typosquatting, company name mismatches, or NIT discrepancies

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation with documents uploaded (for cross-validation comparison)

## Test Credentials

Use test account with appropriate role:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. **Verify** risk evaluations list is displayed
7. Take a screenshot of the Risk Dashboard
8. Click on an existing evaluation with documents
9. **Verify** evaluation detail page loads
10. Navigate to "Contacto Externo" tab (Tab 3)
11. Take a screenshot of the External Contact tab
12. **Verify** the "Cadenas de Email" section is visible at the top
13. **Verify** email chain upload area is present with:
    - File drop zone for .eml/.msg files
    - Textarea for pasting raw email text
    - "Subir" button
14. Test pasting raw email text:
    - Paste sample email text into the textarea:
      ```
      From: fraudster@empresa-fake.com.co
      To: comercial@finkargo.com
      Date: Mon, 23 Dec 2024 10:00:00 -0500
      Subject: Solicitud de Pago - Azelis Colombia

      Estimados,

      Por favor proceder con el pago a la cuenta indicada.
      NIT: 900.123.456-7
      Representante Legal: Juan Pérez

      Saludos,
      Equipo Azelis
      ```
15. Click "Subir" button
16. **Verify** email chain appears in the list with "Pendiente" status
17. Take a screenshot of the uploaded email chain
18. Click "Validar" button for the uploaded chain
19. Wait for validation to complete
20. **Verify** validation results are displayed:
    - Sender domain analysis (empresa-fake.com.co)
    - Company name mentions (Azelis)
    - NIT mentions (900.123.456-7)
    - Representative name mentions (Juan Pérez)
21. **Verify** discrepancy indicators are shown if any:
    - Domain comparison result
    - Company name comparison result
    - NIT comparison result
22. Take a screenshot of the validation results
23. **Verify** validation status changes from "Pendiente" to appropriate status:
    - "Validado" if no issues
    - "Sospechoso" if suspicious indicators
    - "Crítico" if critical discrepancies (like typosquatting)
24. Test deleting the email chain:
    - Click delete button on the uploaded chain
    - **Verify** chain is removed from the list
25. Take a screenshot of the final state

## Success Criteria

- Login completes successfully
- Risk Dashboard loads with evaluations
- External Contact tab shows email chain section
- Email chain can be uploaded via text paste
- Uploaded chain appears in the list
- Validation triggers and completes
- Validation results display with:
  - Sender domain analysis
  - Company name extraction
  - NIT extraction
  - Representative name extraction
- Discrepancy indicators show correct severity
- Email chain can be deleted
- 5 screenshots are captured:
  1. Risk Dashboard
  2. External Contact tab with email chain uploader
  3. Uploaded email chain (pending status)
  4. Validation results
  5. Final state after deletion

## Error Scenarios to Note

- Invalid email format should show validation error
- File upload errors should show appropriate message
- Network errors should be handled gracefully
- Large files (>10MB for .eml/.msg, >500KB for text) should be rejected with message
