# E2E Test: Paga Local Colombia Word Document Download

Test Word (DOCX) document download functionality for approved Paga Local Colombia contracts.

## User Story

As an operations team member
I want to download approved Paga Local Colombia contracts as Word documents
So that I can send the final contracts to clients for signature

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with operations role
- At least one approved Paga Local Colombia contract exists in the database

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
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

11. Click on "Paga Local Colombia" card/link
12. **Verify** Paga Local Colombia page loads with tabs
13. Navigate to "Contratos Aprobados" tab
14. **Verify** approved contracts table is visible
15. Take a screenshot showing the contracts table

16. Locate a contract with an enabled download button (Word/DOCX icon)
17. **Verify** download button shows Word document icon (not PDF icon)
18. **Verify** tooltip shows "Descargar Word aprobado"
19. Take a screenshot showing download button with tooltip

20. Click the download button
21. **Verify** button shows loading state (spinner)
22. **Verify** file download is triggered
23. **Verify** downloaded file has .docx extension
24. **Verify** filename follows pattern: `{contract_code}-{client_name}.docx`
25. Take a screenshot after download completes

### Test Download Button State

26. Locate a contract without approved_document_url (if any)
27. **Verify** download button is disabled for contracts without documents
28. **Verify** info icon appears next to disabled button with tooltip explaining unavailability

### Test Instructions Alert

29. Scroll to bottom of the page
30. **Verify** instructions alert mentions Word/DOCX format (not PDF)
31. Take a screenshot of the instructions alert

## Success Criteria

- Login flow completes successfully
- Operations user can access Paga Local Colombia module
- "Contratos Aprobados" tab shows approved Paga Local CO contracts
- Download button displays Word/DOCX icon (not PDF icon)
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
  3. Paga Local Colombia Contratos Aprobados tab
  4. Download button with tooltip visible
  5. After successful download
  6. Instructions alert

## Edge Cases to Verify

- Contract with long client name: Filename should be truncated appropriately
- Client name with special characters (ñ, accents, &): Should be sanitized in filename
- Contract without approved document: Button should be disabled with info tooltip
- Multiple rapid download clicks: Should not trigger multiple downloads

## Error Scenarios to Note

- Network errors should show user-friendly alert message
- Contract not found: Should show appropriate error
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
