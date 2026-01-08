# E2E Test: PA Report Cleanup Improvements

Test that the PA Report cleanup process correctly preserves data, maintains column names, adds new classification columns, and applies USD sign correction.

## User Story

As a Finance user
I want the PA Report cleanup process to preserve my original column names and financial values
So that I can accurately process PA transactions without losing important data or having incorrect sign values for USD transactions

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied (including pa_account_catalog table)
- Finance or admin account exists with access to finance module
- PA account catalog has been loaded with at least one account
- Test Excel file available with:
  - Known Débito and Crédito values
  - USD transactions (Moneda: Nombre = "USD")
  - Columns including "Mensajes" and "notas"
  - "Fecha de vencimiento" column (to verify removal)

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) or a finance user
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin, finance, or finance_admin

## Test Steps

### Part 1: Authentication and Navigation

1. Navigate to the Application URL (http://localhost:5175)
2. **Verify** login page is displayed
3. Enter admin/finance email in email field
4. Enter password in password field
5. Click "Iniciar sesion" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/finance/reporte-pa` (Finance > Reporte PA)
8. **Verify** user can access the PA Report page (page loads successfully)
9. Take a screenshot of successful PA Report page access

### Part 2: Upload Test File

10. Locate the file upload section on the PA Report page
11. Click the file input or drag-and-drop area
12. Select a test Excel file containing:
    - Column "Mensajes" with text values
    - Column "notas" with text values
    - Column "Débito" with values like `$37.634,41`
    - Column "Crédito" with values
    - Column "Saldo" (to be renamed to "Valor COP")
    - Column "Importe (moneda extranjera)" (to be renamed to "Valor USD")
    - Column "Fecha de vencimiento" (to be removed)
    - USD transactions where Moneda: Nombre = "USD"
13. **Verify** file is selected and displayed (filename shown)
14. Click the "Cargar Archivo NetSuite" button
15. Wait for the upload to complete (loading indicator disappears)
16. Take a screenshot of successful upload result

### Part 3: Execute Cleanup Step

17. **Verify** upload shows success message with PA rows count
18. Click "Ejecutar Limpieza" button
19. Wait for cleanup to complete (loading indicator disappears)
20. **Verify** cleanup shows success message "Datos limpiados correctamente"
21. Take a screenshot of cleanup results with statistics

### Part 4: Download and Verify Cleaned File

22. Click "Descargar Archivo Limpio" button
23. Wait for file download to complete
24. Take a screenshot showing download completed
25. Open the downloaded Excel file and verify:

#### Column Name Verification
26. **Verify** column "Mensajes" exists with original name (NOT renamed to "notas")
27. **Verify** column "notas" exists with original name
28. **Verify** column "Saldo" has been renamed to "Valor COP"
29. **Verify** column "Importe (moneda extranjera)" has been renamed to "Valor USD"
30. **Verify** column "Fecha de vencimiento" has been REMOVED
31. **Verify** column "Tipo de Transacción" is now in position E (after fecha_vencimiento removal)
32. Take a screenshot of column headers in Excel

#### Data Preservation Verification
33. **Verify** Débito column contains original values (not cleared/zeroed)
34. **Verify** Crédito column contains original values (not cleared/zeroed)
35. **Verify** financial values are converted to numeric (e.g., `$37.634,41` → `37634.41`)
36. Take a screenshot showing preserved Débito/Crédito values

#### New Columns Verification
37. **Verify** column AA is named "PA" (with capital letters)
38. **Verify** all rows in "PA" column have value "X"
39. **Verify** column AB is named "Categoria"
40. **Verify** column AC is named "Subcategoria"
41. **Verify** column AD is named "Clasificacion"
42. **Verify** column AE is named "Nexo"
43. **Verify** column AF is named "Comprobacion saldos"
44. **Verify** column AG is named "Cuenta Homologacion"
45. **Verify** column AH is named "Nombre Homologacion"
46. Take a screenshot of new columns AA-AH

### Part 5: USD Sign Correction Verification

47. Find a row where:
    - "Moneda: Nombre" = "USD"
    - "Débito" has a non-zero value
48. **Verify** "Valor USD" for this row is POSITIVE (> 0)
49. Find a row where:
    - "Moneda: Nombre" = "USD"
    - "Crédito" has a non-zero value
50. **Verify** "Valor USD" for this row is NEGATIVE (< 0)
51. Take a screenshot showing USD sign correction results

### Part 6: Column Order Verification

52. **Verify** column Z is "Entidad (línea): ID interno"
53. **Verify** new columns start at AA
54. Take a screenshot of column Z and AA

## Success Criteria

### Column Name Preservation
- [ ] "Mensajes" column keeps original name
- [ ] "notas" column keeps original name
- [ ] Only "Saldo" → "Valor COP" rename occurred
- [ ] Only "Importe (moneda extranjera)" → "Valor USD" rename occurred

### Column Removal and Reordering
- [ ] "Fecha de vencimiento" column removed
- [ ] "Tipo de Transacción" is now column E
- [ ] "Entidad (línea): ID interno" is column Z

### Data Preservation
- [ ] Débito values preserved (not zeroed)
- [ ] Crédito values preserved (not zeroed)
- [ ] Financial values converted from text to numeric

### New Columns
- [ ] PA column (AA) exists with value "X" in all rows
- [ ] Categoria column (AB) exists
- [ ] Subcategoria column (AC) exists
- [ ] Clasificacion column (AD) exists
- [ ] Nexo column (AE) exists
- [ ] Comprobacion saldos column (AF) exists
- [ ] Cuenta Homologacion column (AG) exists
- [ ] Nombre Homologacion column (AH) exists

### USD Sign Correction
- [ ] USD Débito transactions have positive Valor USD
- [ ] USD Crédito transactions have negative Valor USD

### Performance
- [ ] File processes without timeout errors
- [ ] No memory errors during processing

## Error Scenarios to Note

**Before Fix (Bug):**
- Column names incorrectly renamed (Mensajes → notas)
- Débito/Crédito values cleared during cleanup
- New columns use lowercase names (pa, categoria, subcategoria)
- USD sign correction not applied
- Fecha de vencimiento column not removed

**After Fix (Expected):**
- Original column names preserved (except Saldo and Importe)
- Débito/Crédito values intact
- New columns use proper capitalization (PA, Categoria, Subcategoria)
- USD Débito = positive, USD Crédito = negative
- Fecha de vencimiento column removed

## Expected Screenshots

1. PA Report page access (after login)
2. Successful file upload result
3. Cleanup results with statistics
4. Download completed
5. Column headers in downloaded Excel
6. Preserved Débito/Crédito values
7. New columns AA-AH
8. USD sign correction results
9. Column Z and AA positions
