# E2E Test: PA Report Classification

Test the PA Report Classification feature for the Finance module in the Finkargo Automation Hub application.

## User Story

As a Finance user
I want to upload NetSuite movement files and have them automatically filtered and classified for PA accounts
So that I can generate accurate PA reports with proper categorization without manual Excel manipulation

As a Finance Administrator
I want to upload and manage PA classification rules
So that the classification logic can be updated without code changes

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (migration_pa_classification.sql)
- Admin/finance_admin account exists with full system access
- Finance account exists for testing report processing
- Sample Excel files available for testing:
  - PA Account Catalog Excel
  - Classification Rules Excel
  - Clasificación Cuenta Rules Excel
  - Nexo Rules Excel
  - NetSuite Movement Excel (~100 rows for testing)

## Test Credentials

Use credentials from `backend/.env`:
- **Admin/Finance Admin**: `$TEST_ADMIN_EMAIL` / `$TEST_ADMIN_PASSWORD`
  - Expected Role: admin or finance_admin (can access rules management)
- **Finance User**: `$TEST_FINANCE_EMAIL` / `$TEST_FINANCE_PASSWORD`
  - Expected Role: finance (can process reports but not manage rules)

## Test Steps

### Part 1: Authentication and Rules Access (Finance Admin)

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter admin email (`$TEST_ADMIN_EMAIL`) in email field
4. Enter admin password (`$TEST_ADMIN_PASSWORD`) in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/finance/reglas-clasificacion-pa`
8. **Verify** user can access the Rules page (page loads successfully)
9. Take a screenshot of Rules page access

### Part 2: Upload PA Classification Rules

10. **Verify** page title shows "Reglas de Clasificación PA"
11. **Verify** four upload sections are visible:
    - Catálogo de Cuentas PA
    - Reglas de Clasificación
    - Reglas Clasificación por Cuenta
    - Reglas de Nexo
12. Upload PA Account Catalog Excel file
13. **Verify** upload success message appears
14. Take a screenshot of catalog upload success
15. Upload Classification Rules Excel file
16. **Verify** upload success message appears
17. Upload Clasificación Cuenta Rules Excel file
18. **Verify** upload success message appears
19. Upload Nexo Rules Excel file
20. **Verify** upload success message appears
21. Take a screenshot of all rules uploaded successfully

### Part 3: View Uploaded Rules

22. **Verify** "Ver Reglas Actuales" section is visible
23. Click on "Catálogo de Cuentas" tab
24. **Verify** data grid shows uploaded catalog entries with columns:
    - cuenta_finkargo
    - cuenta_homologacion
    - nombre_homologacion
25. Take a screenshot of catalog data
26. Click on "Reglas Clasificación" tab
27. **Verify** classification rules are displayed
28. Click on "Clasificación Cuenta" tab
29. **Verify** clasificacion cuenta rules are displayed
30. Click on "Nexo" tab
31. **Verify** nexo rules are displayed
32. Take a screenshot of rules viewer tabs

### Part 4: Navigate to Report Processing

33. Navigate to `/finance/reporte-pa`
34. **Verify** user can access the Reporte PA page
35. **Verify** page title shows "Reporte PA"
36. **Verify** two tabs are present: "Procesar Reporte", "Historial"
37. Take a screenshot of report processing page

### Part 5: Step 1 - Upload NetSuite File and Clean

38. **Verify** file upload section is visible in "Procesar Reporte" tab
39. Upload NetSuite movement Excel file
40. **Verify** file is accepted and file name is displayed
41. Take a screenshot of file uploaded
42. Click "Procesar (Paso 1 - Limpieza)" button
43. Wait for processing to complete (loading state)
44. **Verify** cleanup results are displayed with:
    - Total Filas: shows total row count
    - Filas PA: shows filtered PA row count
    - Suma Débito: shows sum of debit column
    - Suma Crédito: shows sum of credit column
    - Validación de Saldos: shows green check if balanced (or warning if not)
45. Take a screenshot of cleanup results
46. Click "Descargar Archivo Limpio" button
47. **Verify** cleaned Excel file downloads successfully
48. Take a screenshot after download

### Part 6: Step 2 - Apply Classification

49. **Verify** "Procesar (Paso 2 - Clasificación)" button is visible
50. Click "Procesar (Paso 2 - Clasificación)" button
51. Wait for classification to complete (loading state)
52. **Verify** classification results are displayed with:
    - Registros Clasificados: shows count
    - Registros Sin Clasificar: shows count (ideally 0)
53. **Verify** success message or warning about unclassified records
54. Take a screenshot of classification results
55. Click "Descargar Reporte Final" button
56. **Verify** classified Excel file downloads successfully
57. Take a screenshot of final download

### Part 7: Verify Output Columns

58. Open downloaded classified Excel file
59. **Verify** all 8 output columns are present:
    - PA (should contain "X" for all rows)
    - Categoría
    - Subcategoría
    - Clasificación
    - Nexo
    - Comprobación saldos
    - Cuenta Homologación
    - Nombre Homologación
60. **Verify** renamed columns are present:
    - "Valor COP" (was "Saldo")
    - "Valor USD" (was "Importe (moneda extranjera)")
61. Take a screenshot of Excel output

### Part 8: Processing History

62. Navigate to "Historial" tab
63. **Verify** history table displays with columns:
    - Session ID
    - Fecha
    - Archivo
    - Total Filas
    - Filas PA
    - Estado
    - Acciones
64. **Verify** recent processing session appears in history
65. **Verify** download buttons are visible for completed sessions
66. Take a screenshot of processing history

### Part 9: Role Restriction Test (Optional)

67. Sign out from admin account
68. Login with finance user account (`$TEST_FINANCE_EMAIL`)
69. Navigate to `/finance/reglas-clasificacion-pa`
70. **Verify** access is denied (403 or redirect)
71. Navigate to `/finance/reporte-pa`
72. **Verify** access is granted (finance users can process reports)
73. Take a screenshot of role restriction

## Success Criteria

- Finance Admin can upload all 4 rule types successfully
- Finance Admin can view uploaded rules in tabular format
- Finance/Admin users can upload NetSuite files
- Cleanup step filters PA accounts and validates balances
- Cleaned file can be downloaded after Step 1
- Classification step applies rules to all records
- Classified file can be downloaded after Step 2
- All 8 output columns are populated correctly
- Processing history tracks all sessions
- Role protection works (only finance_admin can manage rules)
- Screenshots captured at each major step (minimum 12)

## Error Scenarios to Note

- Empty NetSuite file should show appropriate error
- Invalid Excel format should show validation error
- No matching PA accounts should show informative message
- Balance mismatch should show warning (not block processing)
- Unclassified records should be flagged with warnings
- Missing rules should show clear error messages

## Expected Screenshots

1. Rules page access (after login)
2. Catalog upload success
3. All rules uploaded successfully
4. Rules viewer with data
5. Report processing page
6. File uploaded state
7. Cleanup results with validation
8. After cleanup download
9. Classification results
10. Final report download
11. Excel output verification
12. Processing history
13. Role restriction test (optional)
