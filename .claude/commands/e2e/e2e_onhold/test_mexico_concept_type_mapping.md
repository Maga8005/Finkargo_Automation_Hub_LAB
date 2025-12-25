# E2E Test: Mexico Concept Type Mapping Validation

Test the Mexico payment template converter to verify that concept types use space-separated names and MORATORIOS is calculated correctly using PAR 60/61 columns.

## User Story

As a Treasury (Tesorería) department user working with Mexico payment data
I want the payment template converter to produce concept types with the correct names (space-separated) and column mappings
So that the generated NetSuite template aligns with our finance team's requirements and naming conventions

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with Mexico Historial de Pagos format available with PAR 60/61 columns

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_mx.xlsx`

This fixture must contain test rows with:
- Required columns: Cliente, Identificación del cliente, Código de desembolso, etc.
- Concept columns with exact names:
  - Capital (column P)
  - Seguro + IVA (column T)
  - Comision del desembolso + IVA (column U)
  - Comision por disposicion de crédito + IVA (column V)
  - Comision swift (column W)
  - Comision administracion y manejo (column X)
  - Comision de apertura (column Y)
  - Costos adicionales (column AA)
  - Intereses Corrientes (column AB)
  - Intereses de Mora (Tasa corriente) PAR 60 (column AC)
  - Intereses de Mora (Tasa restante de mora) PAR 60 (column AD)
  - Intereses de Mora (Tasa corriente) PAR 61 (column AE)
  - Intereses de Mora (Tasa restante de mora) PAR 61 (column AF)

## Test Steps

1. **Login as tesorería or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite/mexico`

3. Take a screenshot of the Mexico converter page

4. **Verify** page elements are present:
   - Page title "Aplicación de Pagos - México"
   - File upload area present
   - Instructions showing updated column requirements (PAR 60/61)

5. Click on upload area or file input

6. Select test Mexico Historial de Pagos Excel file (.xlsx) with PAR 60/61 columns

7. **Verify** file upload begins (loading indicator)

8. Wait for file validation to complete

9. **Verify** validation preview appears:
   - Source row count displayed
   - Column validation status shows required columns found
   - No critical validation errors

10. Take a screenshot of validation preview

11. Click "Convertir y Descargar" button

12. Wait for conversion to complete

13. **Verify** conversion completes with download

14. Take a screenshot of completion state with statistics

15. **Open the downloaded Excel file and verify concept_type values**:
    - Verify concept_type values use SPACE-separated names, NOT underscore-separated:
      - `COMISION DESEMBOLSO` (not `COMISION_DESEMBOLSO`)
      - `COMISION DISPOSICION` (not `COMISION_DISPOSICION`)
      - `COMISION SWIFT` (not `COMISION_SWIFT`)
      - `COMISION ADMINISTRACION` (not `COMISION_ADMINISTRACION`)
      - `COMISION APERTURA` (not `COMISION_APERTURA`)
      - `COSTOS ADICIONALES` (not `COSTOS_ADICIONALES`)
    - Verify MORATORIOS row exists if PAR 60/61 columns had values
    - Verify MORATORIOS value equals sum of AC+AD+AE+AF columns

16. Take a screenshot of the downloaded Excel file showing concept_type column

## Success Criteria

- Mexico converter page loads correctly
- File validation passes for file with PAR 60/61 column structure
- Conversion generates downloadable Excel file
- **CRITICAL**: Output concept_type values use SPACE-separated names:
  - "COMISION DESEMBOLSO"
  - "COMISION DISPOSICION"
  - "COMISION SWIFT"
  - "COMISION ADMINISTRACION"
  - "COMISION APERTURA"
  - "COSTOS ADICIONALES"
- **CRITICAL**: MORATORIOS is calculated as sum of PAR 60/61 columns (AC+AD+AE+AF)
- Colombia output remains unchanged (still uses underscore naming)
- 4 screenshots are captured:
  1. Mexico converter page initial state
  2. Validation preview after file upload
  3. Conversion completion with statistics
  4. Downloaded Excel showing concept_type values

## Concept Type Mapping Reference

| Excel Column Name | Expected concept_type Output |
|-------------------|------------------------------|
| Capital | CAPITAL |
| Seguro + IVA | SEGUROS |
| Comision del desembolso + IVA | COMISION DESEMBOLSO |
| Comision por disposicion de crédito + IVA | COMISION DISPOSICION |
| Comision swift | COMISION SWIFT |
| Comision administracion y manejo | COMISION ADMINISTRACION |
| Comision de apertura | COMISION APERTURA |
| Costos adicionales | COSTOS ADICIONALES |
| Intereses Corrientes | INTERESES |
| Sum of PAR 60/61 columns | MORATORIOS |

## Error Handling to Verify

- File missing PAR 60/61 columns shows appropriate column validation errors
- Empty concept values are correctly skipped (no output row generated)
- Zero values in concept columns are correctly skipped

## API Endpoints Exercised

- `POST /api/tesoreria/validate/mexico` - Validate uploaded file
- `POST /api/tesoreria/convert/mexico` - Convert and download template

## Notes

- This test specifically validates the Mexico concept type naming convention change from underscore to space separation
- Colombia logic must remain completely unchanged by this update
- The MORATORIOS calculation now uses PAR 60/61 columns (same structure as Colombia) instead of PAR 30/60/90/120+
