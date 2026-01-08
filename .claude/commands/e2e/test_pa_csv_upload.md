# E2E Test: PA Report CSV Upload with Account Matching

Test that semicolon-delimited CSV files with account numbers parsed as floats are correctly matched with the PA account catalog.

## User Story

As a Finance user
I want to upload a NetSuite movements CSV file (semicolon-delimited) to the PA Report feature
So that I can process PA account transactions for classification and reporting

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied (including pa_account_catalog table)
- Finance or admin account exists with access to finance module
- PA account catalog has been loaded with at least one account (e.g., 11100530 -> 13020500101001)
- Test CSV file available: `Requirements_Meetings/PA Report/Req_reporte_pa/CSVs/MovimientoDetallado NOV_25.csv`

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) or a finance user
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin, finance, or finance_admin

## Test Steps

### Part 1: Authentication and Navigation

1. Navigate to the `Application URL` (http://localhost:5175)
2. **Verify** login page is displayed
3. Enter admin/finance email in email field
4. Enter password in password field
5. Click "Iniciar sesion" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/finance/reporte-pa` (Finance > Reporte PA)
8. **Verify** user can access the PA Report page (page loads successfully)
9. Take a screenshot of successful PA Report page access

### Part 2: Upload CSV File

10. Locate the file upload section on the PA Report page
11. Click the file input or drag-and-drop area
12. Select the test file: `Requirements_Meetings/PA Report/Req_reporte_pa/CSVs/MovimientoDetallado NOV_25.csv`
13. **Verify** file is selected and displayed (filename shown)
14. Click the "Upload" or "Cargar" button
15. Wait for the upload to complete (loading indicator disappears)
16. Take a screenshot of the upload in progress or result

### Part 3: Verify Successful Account Matching

17. **Verify** the upload response shows:
    - Success message (NOT "No se encontraron registros que coincidan")
    - Number of PA rows matched (should be > 0)
    - Total rows in file
18. **Verify** the message does NOT contain:
    - "No se encontraron coincidencias"
    - "No se encontraron registros que coincidan con cuentas PA"
19. **Verify** the response shows matched account statistics
20. Take a screenshot of successful upload result

### Part 4: Verify Account 11100530 is Matched

21. Check backend logs or response for account matching details
22. **Verify** account `11100530` from row 211 of the CSV is recognized
23. **Verify** it maps to the expected PA account (e.g., 13020500101001 if configured)
24. Take a screenshot showing account matching confirmation

### Part 5: Proceed to Data Cleaning (Optional)

25. If upload was successful, click "Step 1: Clean Data" or equivalent
26. **Verify** cleaning process completes successfully
27. **Verify** sample data preview shows correctly normalized account numbers:
    - Account numbers should be clean strings (e.g., "11100530" not "11100530.0")
28. Take a screenshot of cleaned data preview

## Success Criteria

- CSV file uploads without error
- Account numbers from CSV are correctly matched with PA catalog
- No "No se encontraron registros" error message appears
- Message shows positive PA rows count (pa_rows > 0)
- Account 11100530 (from row 211) is successfully matched
- Account numbers in cleaned preview are clean strings without ".0" suffix
- Semicolon delimiter is correctly detected and parsed

## Error Scenarios to Note

**Before Fix (Bug):**
- Upload fails with "No se encontraron registros que coincidan con cuentas PA del catálogo"
- Backend logs show account mismatch:
  - File accounts: `['13050501.0', '13551511.0', ...]` (with .0 suffix)
  - Catalog accounts: `['11101030', '11200530', ...]` (clean strings)

**After Fix (Expected):**
- Upload succeeds with matched PA rows
- Backend logs show clean account matching:
  - File accounts: `['13050501', '13551511', ...]` (clean strings)
  - Catalog accounts: `['11101030', '11200530', ...]` (clean strings)

## Technical Verification

Check backend logs for:
```
INFO - Found X unique accounts in uploaded file
DEBUG - Sample normalized accounts from file: ['13050501', '13551511', ...]
```

Accounts should NOT have `.0` suffix (e.g., NOT `'13050501.0'`)

## Expected Screenshots

1. PA Report page access (after login)
2. File upload in progress or completion
3. Successful upload result (showing PA rows matched)
4. Account matching confirmation
5. Cleaned data preview (if proceeding to step 2)
