# E2E Test: Mexico COMISION Concept Type Mapping

Test that Mexico COMISION concept types are correctly generated in output when the source Excel file contains values in commission columns.

## User Story

As a Treasury (Tesorería) department user
I want to upload a Mexico payment history file with COMISION values
So that the output file correctly generates rows for all COMISION concept types (COMISION DESEMBOLSO, COMISION DISPOSICION, COMISION SWIFT, etc.)

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with Mexico Historial de Pagos format containing COMISION values

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_mx_comision.xlsx`

This fixture must contain test rows with:
- Required columns: Cliente, Identificación del cliente, Código de desembolso, etc.
- **COMISION columns with proper Spanish accents** (these are the columns being tested):
  - `Comisión del desembolso + IVA` - Value > 0
  - `Comisión por disposición de crédito + IVA` - Value > 0
  - `Comisión swift` - Value > 0
  - `Comisión administración y manejo` - Value > 0
  - `Comisión de apertura` - Value > 0
- Other concept columns: Capital, Seguro + IVA, Costos adicionales, Intereses Corrientes

## Test Steps

1. **Login as tesorería or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite/mexico`

3. Take a screenshot of the Mexico converter page

4. **Verify** Mexico converter page elements:
   - Page title "Aplicación de Pagos - México"
   - File upload area (drag & drop zone)
   - Instructions about required file format
   - Convert button (initially disabled)

5. Click on upload area or file input

6. Select test Historial de Pagos Excel file (.xlsx) with COMISION values

7. **Verify** file upload begins (loading indicator)

8. Wait for file validation to complete

9. **Verify** validation preview appears:
   - Source row count displayed
   - Column validation status (all required columns found)
   - Estimated output rows calculation
   - No critical validation errors

10. Take a screenshot of validation preview

11. **Verify** Convert button is now enabled

12. Click "Convertir y Descargar" button

13. **Verify** conversion starts:
    - Loading/progress indicator appears
    - Button becomes disabled during processing

14. **Verify** conversion completes:
    - Download starts automatically or download link appears
    - Success message with conversion statistics displayed

15. Take a screenshot of completion state with statistics

16. **Manually verify downloaded file** (post-automation):
    - Open the downloaded Excel file
    - **CRITICAL**: Verify the `concept_type` column contains rows with:
      - `COMISION DESEMBOLSO`
      - `COMISION DISPOSICION`
      - `COMISION SWIFT`
      - `COMISION ADMINISTRACION`
      - `COMISION APERTURA`
    - Verify `payment_amount` values match source column values

## Success Criteria

- Mexico converter page loads correctly
- File upload accepts .xlsx files with accented column names
- Validation preview displays correct statistics
- Convert button enables after successful validation
- Conversion generates downloadable Excel file
- **CRITICAL**: Downloaded file contains rows with COMISION concept types:
  - concept_type = "COMISION DESEMBOLSO" with correct payment_amount
  - concept_type = "COMISION DISPOSICION" with correct payment_amount
  - concept_type = "COMISION SWIFT" with correct payment_amount
  - concept_type = "COMISION ADMINISTRACION" with correct payment_amount
  - concept_type = "COMISION APERTURA" with correct payment_amount
- 3 screenshots are captured:
  1. Mexico converter page initial state
  2. Validation preview after file upload
  3. Conversion completion with statistics

## Bug Verification

This test validates the fix for the bug where COMISION concept types were not appearing in output.

### Root Cause
The column names in `payment_catalogs.py` were defined without Spanish accents (e.g., "Comision" instead of "Comisión"), while the actual Excel files use accented column names. Since Python's `.lower()` does not normalize accents, the column lookup failed silently.

### Fix Applied
Updated `MEXICO_CONCEPT_COLUMNS` in `backend/src/core/servicios/catalogs/payment_catalogs.py` to use correct accented column names:
- `"Comisión del desembolso + IVA"` (was "Comision del desembolso + IVA")
- `"Comisión por disposición de crédito + IVA"` (was "Comision por disposicion de crédito + IVA")
- `"Comisión swift"` (was "Comision swift")
- `"Comisión administración y manejo"` (was "Comision administracion y manejo")
- `"Comisión de apertura"` (was "Comision de apertura")

## Error Handling to Verify

- Invalid file format shows appropriate error message
- Missing required columns are flagged with specific column names
- Network errors during upload/conversion show user-friendly message

## API Endpoints Exercised

- `POST /api/tesoreria/validate/mexico` - Validate uploaded file
- `POST /api/tesoreria/convert/mexico` - Convert and download template

## Notes

- The key difference from Colombia is that México uses "COMISION" concept types instead of "4X1000" and "FONDO_GARANTIAS"
- Column name accents are critical for correct column matching
- Each source row with non-zero COMISION values should generate corresponding output rows
