# E2E Test: Contratos Colombia Word Document Download

Test Word (DOCX) document download functionality for approved contracts in Contratos Colombia - Solicitar.

## User Story

As an operations team member
I want to download approved contracts from Contratos Colombia - Solicitar as Word documents
So that I can send editable contract documents to clients for review and signature

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with operations role
- At least one approved contract exists in the database (activos, otrosi, or inventario_bodega type)

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
6. Click "Iniciar Sesion" button
7. Wait for authentication to complete

8. Navigate to Operations module via sidebar (click "Operaciones")
9. **Verify** operations dashboard loads
10. Take a screenshot of operations dashboard

11. Click on "Contratos Colombia - Solicitar" card/link
12. **Verify** Contratos Colombia page loads with tabs
13. Navigate to "Contratos Aprobados" tab
14. **Verify** approved contracts table is visible
15. Take a screenshot showing the contracts table

16. Locate a contract with an enabled download button (Word/DOCX icon)
17. **Verify** download button shows Word document icon (Description icon, not PDF icon)
18. **Verify** tooltip shows "Descargar Word aprobado"
19. Take a screenshot showing download button with tooltip

20. Click the download button
21. **Verify** button shows loading state (spinner)
22. **Verify** file download is triggered
23. **Verify** downloaded file has .docx extension
24. **Verify** filename follows pattern: `{contract_code}-{client_name}.docx`
25. Take a screenshot after download completes

### Test Instructions Alert

26. Scroll to bottom of the page
27. **Verify** instructions alert mentions Word/DOCX document download
28. Take a screenshot of the instructions alert

## Success Criteria

- Login flow completes successfully
- Operations user can access Contratos Colombia - Solicitar module
- "Contratos Aprobados" tab shows approved contracts (activos, otrosi, inventario_bodega types)
- Download button displays Word/DOCX icon (Description icon)
- Tooltip text reads "Descargar Word aprobado"
- Clicking download button retrieves DOCX file
- Downloaded file has correct .docx extension
- Filename follows convention: `{contract_id}-{client_name}.docx`
- Client names with special characters are properly sanitized in filename
- Instructions alert references Word documents
- No console errors during download process
- 5-6 screenshots captured:
  1. Login page
  2. Operations dashboard
  3. Contratos Colombia Contratos Aprobados tab
  4. Download button with tooltip visible
  5. After successful download
  6. Instructions alert

## Edge Cases to Verify

- Contract with long client name: Filename should be truncated appropriately (max 50 chars)
- Client name with special characters (accents, &): Should be sanitized in filename
- Multiple rapid download clicks: Should not trigger multiple downloads (loading state prevents)

## Error Scenarios to Note

- Network errors should show user-friendly alert message ("Error al descargar el documento Word")
- Contract not found: Should return 404 error
- Non-approved contract access: Should return 400 error
- Invalid session should redirect to login

## Technical Verification

After completing the E2E test, verify backend endpoint:
```bash
# Test endpoint exists and requires auth
curl -v http://localhost:8000/api/operations/contracts/{contract_uuid}/download/docx

# Should return 401 Unauthorized without token
# Should return 400 if contract not approved
# Should return 404 if contract not found
# Should return DOCX file with proper headers if valid
```
