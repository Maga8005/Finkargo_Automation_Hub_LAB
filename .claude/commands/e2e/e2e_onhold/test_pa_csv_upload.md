# E2E Test: PA Report CSV Upload

Test the CSV file upload functionality for the PA Report Classification feature.

## User Story

As a Finance user
I want to upload CSV files to the PA Report processing page
So that I can process NetSuite exports in their native CSV format without converting to Excel first

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied (migration_pa_classification.sql)
- PA classification rules already uploaded (catalog, classification, clasificacion-cuenta, nexo)
- Admin or finance_admin account for testing
- Sample CSV file with NetSuite movement data containing required columns:
  - Cuenta (linea): Numero
  - Cuenta (linea): Nombre
  - Debito
  - Credito
  - Saldo

## Test Credentials

Use credentials from `backend/.env`:
- **Admin/Finance Admin**: `$TEST_ADMIN_EMAIL` / `$TEST_ADMIN_PASSWORD`

## Test Steps

### Part 1: Authentication

1. Navigate to the `Application URL` (http://localhost:5175)
2. **Verify** login page is displayed
3. Enter admin email in email field
4. Enter admin password in password field
5. Click "Iniciar sesion" button
6. **Verify** login succeeds and redirects to homepage
7. Take a screenshot of authenticated homepage

### Part 2: Navigate to PA Report Page

8. Click on "Finanzas" in the sidebar to expand the menu
9. Click on "Reporte PA" submenu item
10. **Verify** PA Report page loads at `/finance/reporte-pa`
11. **Verify** page title shows "Reporte PA"
12. Take a screenshot of PA Report page

### Part 3: Verify CSV File Acceptance

13. **Verify** file upload input is visible in the "Procesar Reporte" tab
14. **Verify** the file input accepts CSV files (check accept attribute includes .csv)
15. Take a screenshot showing the upload section

### Part 4: Upload CSV File

16. Click on the file upload button "Cargar Archivo NetSuite"
17. Select a sample CSV file with NetSuite movement data
18. **Verify** file is accepted (no error message appears)
19. **Verify** upload progress or success indicator appears
20. **Verify** upload response shows:
    - Filename is displayed
    - Total rows count
    - PA rows count (filtered count)
21. Take a screenshot of successful CSV upload

### Part 5: Step 1 - Clean Data

22. **Verify** "Ejecutar Limpieza" button is visible and enabled
23. Click "Ejecutar Limpieza" button
24. Wait for cleaning process to complete
25. **Verify** cleanup results are displayed with:
    - Registros PA count
    - Total Filas count
    - Balance validation status
26. Take a screenshot of cleanup results

### Part 6: Step 2 - Classify Data

27. **Verify** "Ejecutar Clasificacion" button is visible and enabled
28. Click "Ejecutar Clasificacion" button
29. Wait for classification process to complete
30. **Verify** classification results are displayed with:
    - Classified count
    - Classification summary by category
31. Take a screenshot of classification results

### Part 7: Download Classified File

32. **Verify** "Descargar Archivo Clasificado" button is visible
33. Click "Descargar Archivo Clasificado" button
34. **Verify** file download is triggered (xlsx format)
35. Take a screenshot after download completes

### Part 8: Verify in History Tab

36. Click on "Historial" tab
37. **Verify** the processing session appears in history
38. **Verify** session shows the original CSV filename
39. **Verify** session status shows "classified"
40. Take a screenshot of history showing CSV upload session

## Success Criteria

- CSV file can be uploaded at `/finance/reporte-pa`
- CSV file is accepted by the file input (no validation error)
- CSV data is parsed and filtered for PA accounts
- Cleanup step completes successfully with correct stats
- Classification step completes successfully
- Classified Excel file can be downloaded
- Processing history shows the CSV upload session
- No errors or regressions from existing Excel functionality

## Error Scenarios to Note

- Empty CSV file should show appropriate error message
- CSV with missing required columns should show validation error
- CSV with encoding issues should be handled gracefully
- Malformed CSV should show clear error message
- Files larger than 50 MB should show file size error before upload
- Connection refused errors should show user-friendly message

## Large File Handling

The PA report system is designed to handle large files:
- **Maximum file size**: 50 MB
- **Maximum rows**: ~50,000 records
- **Timeout**: 10 minutes for processing

### Client-side validation
- Files over 50 MB are rejected immediately with a clear error message
- File size is displayed in the error: "El archivo es demasiado grande (XX.X MB). El tamaño máximo es 50 MB."

### Server-side handling
- Request body size is validated by middleware
- Memory-efficient CSV parsing with error recovery
- Proper error logging for debugging
- Graceful handling of memory errors

### Connection Error Handling
If the backend server is unavailable:
- User sees: "No se pudo conectar al servidor. Verifique que el servidor esté activo e intente nuevamente."
- Original error is logged to console for debugging

## Expected Screenshots

1. Authenticated homepage
2. PA Report page loaded
3. Upload section visible
4. Successful CSV upload with stats
5. Cleanup results
6. Classification results
7. After download
8. History showing CSV session
