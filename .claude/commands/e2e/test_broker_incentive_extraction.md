# E2E Test: Broker Incentive Extraction (Extracción Incentivos)

Test the broker incentive extraction feature in the Alianzas module that scans directories for broker contracts and extracts incentive percentages.

## User Story

As an Alianzas user
I want to scan a directory of broker contract PDFs and extract incentive data
So that I can consolidate broker incentive information from multiple contracts into a single report

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with `alianzas` or `admin` role exists in Supabase
- Test directory with broker contract PDFs exists at `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024`

## Test Credentials

Use test account (configure in test environment):
- Email: test-alianzas@finkargo.com or test-admin@finkargo.com
- Password: [configured test password]
- Expected Role: alianzas or admin

## Test Steps

### Part 1: Login and Navigation

1. Navigate to the Application URL (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter test email and password
4. Click "Iniciar Sesión" button
5. Wait for authentication to complete
6. **Verify** successful redirect occurs
7. Navigate to Alianzas > Extracción Incentivos (/alianzas/incentivos)
8. **Verify** incentive extraction page loads
9. Take a screenshot of the initial page state

### Part 2: Configure Directory Scan

10. **Verify** the page contains:
    - Directory path input field
    - "Incluir Subcarpetas" checkbox
    - "Escanear Directorio" button
    - Results data grid (empty initially)
11. Enter the directory path: `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024`
12. Check the "Incluir Subcarpetas" checkbox
13. Take a screenshot of the configured scan settings

### Part 3: Execute Directory Scan

14. Click "Escanear Directorio" button
15. **Verify** loading indicator appears
16. Wait for scan to complete (may take 30+ seconds for large directories)
17. **Verify** NO "Not Found" error appears (this was the bug being fixed)
18. **Verify** one of the following outcomes:
    - Success: Results appear in the data grid with broker data
    - No PDFs found: Appropriate message is displayed
    - Directory not found: Clear error message (not "Not Found" 404)
19. Take a screenshot of the scan results

### Part 4: Review Results (if PDFs found)

20. **Verify** data grid displays columns:
    - Broker Name
    - RFC
    - Firmante (Signatory)
    - Credit Line Incentive %
    - Operations Incentive %
    - Contract Type (Bono, Incentivos, Colaboración, Desconocido)
    - **Contract Status** (Encontrado, Sin Contrato, Error) - NEW
    - Contract Date
    - Notas (Warnings)
21. **Verify** statistics section shows:
    - Contratos Bono count
    - Contratos Incentivos count
    - Desconocidos count
    - **Encontrados count** (contracts found) - NEW
    - **Sin Contrato count** (no contract file found) - NEW
    - **Errores count** (extraction errors) - NEW
    - Average credit line percentage
    - Average operations percentage
22. **Verify** Contract Status column displays:
    - Green "Encontrado" chip for folders where a contract PDF was found
    - Orange "Sin Contrato" chip for folders with no matching contract patterns
    - Red "Error" chip for extraction errors
23. Take a screenshot of the detailed results

### Part 5: Export Results (if data available)

24. **Verify** "Exportar Excel" button is enabled when results exist
25. Click "Exportar Excel" button
26. **Verify** file download is triggered
27. **Verify** downloaded file is named appropriately (e.g., `broker_incentives.xlsx`)
28. **Verify** Excel file includes "Estado Contrato" column with status values

## Success Criteria

- Login succeeds with alianzas/admin role
- Navigation to Extracción Incentivos page works
- Directory path can be entered in the input field
- "Incluir Subcarpetas" checkbox is functional
- Scan request goes to `/api/alianzas/broker-contracts/scan` (NOT `/api/api/...`)
- No "Not Found" 404 error appears (the bug this test validates)
- Results display correctly if PDFs are found
- **Contract Status column displays correctly** (Encontrado, Sin Contrato, Error)
- **Statistics show contract status counts** (Encontrados, Sin Contrato, Errores)
- Export functionality works when results exist
- Excel export includes "Estado Contrato" column
- 4 screenshots are captured:
  1. Initial page state
  2. Configured scan settings
  3. Scan results
  4. Detailed results view

## Error Scenarios to Note

- "Not Found" error = BUG (duplicate /api/ prefix in URL)
- Directory not found = valid error (directory doesn't exist)
- No PDFs found = valid message (directory exists but has no broker PDFs)
- Timeout = scan took too long (increase timeout in settings)
- Network error = connection issue to backend

## Bug Verification

This test specifically validates the fix for the duplicate `/api/` prefix bug:

**Before Fix:**
- Request URL: `/api/api/alianzas/broker-contracts/scan`
- Result: 404 Not Found error

**After Fix:**
- Request URL: `/api/alianzas/broker-contracts/scan`
- Result: Successful scan or appropriate error message

## Notes

- The scan operation can take several minutes for directories with many PDFs
- Each PDF is processed sequentially for text extraction
- Results include confidence scores based on extraction quality
- The Excel export includes styled formatting with color coding
- **Contract Status Feature**: Shows if contract was found, not found, or had errors
  - "Encontrado" (Found): Contract PDF with valid filename patterns was processed
  - "Sin Contrato" (Not Found): Folder exists but no PDF matches contract patterns
  - "Error": Contract exists but extraction failed
- Contract filename patterns include: contrato, corretaje, bono, incentivo, Complete_con_Docusign, etc.
