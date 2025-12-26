# E2E Test: Export Approved Contracts to Excel

Test Excel export functionality for approved contracts in the Finkargo Automation Hub operations module.

## User Story

As an operations team member
I want to export the approved contracts list to an Excel file
So that I can share the data with stakeholders, create reports, or analyze contract information offline

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with operations role
- At least one approved contract exists in the database

## Test Credentials

Use test account (configure in test environment):
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Take a screenshot of the login page
4. Enter test email in email field
5. Enter test password in password field
6. Click "Iniciar Sesión" button
7. Wait for authentication to complete

8. Navigate to Operations module via sidebar (click "Operaciones")
9. **Verify** operations dashboard loads
10. Take a screenshot of operations dashboard

11. Navigate to "Contratos Aprobados" tab
12. **Verify** approved contracts table is visible
13. **Verify** "Exportar Excel" button is present in the header section
14. Take a screenshot showing the "Exportar Excel" button

15. Click "Exportar Excel" button
16. **Verify** button shows loading state (spinner or disabled state)
17. **Verify** file download is triggered (browser download dialog or automatic download)
18. **Verify** downloaded file has .xlsx extension
19. **Verify** filename contains "contratos_aprobados" and current date
20. Take a screenshot after export completes

### Optional: Test with Filters
21. Click "Filtros" button to show filter panel
22. Apply a filter (e.g., select a specific contract type)
23. **Verify** table updates with filtered results
24. Click "Exportar Excel" button again
25. **Verify** export only includes filtered contracts (verify by file size or opening file)
26. Take a screenshot with filters applied and export button visible

### Test Paga Local CO Tab (if time permits)
27. Navigate to "Paga Local CO" tab under approved contracts
28. **Verify** "Exportar Excel" button is also present
29. Click "Exportar Excel" button
30. **Verify** file downloads with appropriate filename containing "paga_local_co"

## Success Criteria

- Login flow completes successfully
- Operations module is accessible to operations role user
- "Exportar Excel" button is visible and properly styled (matches existing UI buttons)
- Clicking export button triggers file download
- Downloaded file is a valid .xlsx file
- Filename includes date for version tracking (format: contratos_aprobados_YYYY-MM-DD.xlsx)
- Export respects active filters (exports visible data only)
- No console errors during export process
- Button shows loading state during export generation
- 4-5 screenshots are captured:
  1. Login page
  2. Operations dashboard
  3. Approved contracts tab with export button visible
  4. After successful export
  5. (Optional) Filters panel with export button

## Edge Cases to Verify

- Empty contracts list: Button should be disabled or show appropriate message
- Large number of contracts: Export should handle without timeout
- Missing data fields: Export should handle null values gracefully
- Special characters in client names: Export should not corrupt data

## Error Scenarios to Note

- Network errors should show user-friendly error message
- Invalid session should redirect to login
- Browser blocking download should show alternative download instructions
