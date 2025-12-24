# E2E Test: Mexico Tesorería Columns (Subsidiary & Retencion)

Test that the "Aplicacion de Pagos MX" output file includes the subsidiary and retencion_en_fuente columns with Mexico-specific values.

## User Story

As a Treasury (Tesorería) department user
I want the "Aplicacion de Pagos MX" output to include subsidiary and retencion en fuente columns
So that I can upload payment applications to NetSuite with complete withholding tax information and correct subsidiary assignment for Mexico

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with Historial de Pagos format containing Retención column

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_mx_with_retencion.xlsx`

This fixture contains 2 test rows with:
- Required columns: Cliente, Identificación del cliente, Código de desembolso, etc.
- Concept columns: Capital, Intereses Corrientes (to test 1:N expansion)
- Optional columns: Cuenta Remitente
- **NEW**: Retención column with value (e.g., 2500.00)

If the fixture file doesn't exist, create it with the following data:
| Cliente | Identificación del cliente | Código de desembolso | Código de recaudo | Fecha de pago | Moneda | Capital | Banco remitente | Intereses Corrientes | Retención | Cuenta Remitente |
|---------|---------------------------|---------------------|-------------------|---------------|--------|---------|-----------------|---------------------|-----------|------------------|
| Test Client MX 1 | RFC123456ABC | MX:RFC123:1:1:PAG | REC-001 | 2025-12-01 | MXN | 50000 | Banco Test | 5000 | 2500 | 0123270165 |
| Test Client MX 2 | RFC789012XYZ | MX:RFC789:1:1:PAG | REC-002 | 2025-12-02 | MXN | 100000 | Banco Test | 0 | 0 | 0123270165 |

## Test Steps

1. **Login as tesorería or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite/mexico`

3. Take a screenshot of the Mexico converter page

4. **Verify** Mexico converter page loads with file upload area

5. Upload the test Historial de Pagos Excel file with Retención column

6. Wait for file validation to complete

7. **Verify** validation preview appears with no errors

8. Take a screenshot of validation preview

9. Click "Convertir y Descargar" button

10. Wait for conversion to complete

11. **Verify** conversion succeeds and file download starts

12. Take a screenshot of completion state

13. Open the downloaded Excel file and verify the output structure:
    - **Verify** output has 16 columns (same as Colombia)
    - **Verify** column 15 is "subsidiary"
    - **Verify** column 16 is "retencion_en_fuente"

14. **Verify** subsidiary column values:
    - ALL rows should have value "6" (Mexico subsidiary ID)
    - This applies to all concept rows (CAPITAL, INTERESES, etc.)

15. **Verify** retencion_en_fuente column values:
    - Row 1 (first row from source row 1): should have value 2500 (the Retención value)
    - Row 2 (second row from source row 1 - INTERESES): should be empty/None
    - Row 3 (first row from source row 2): should have value 0
    - Retencion only appears on FIRST output row for each source row

16. Take a screenshot showing the output Excel columns

## Success Criteria

1. Output Excel file has 16 columns (same structure as Colombia)
2. Column 15 is named "subsidiary" with value 6 on EVERY row (Mexico subsidiary ID)
3. Column 16 is named "retencion_en_fuente" with value ONLY on first output row per source row
4. Existing columns and values are unchanged
5. When source row expands to multiple output rows (e.g., CAPITAL + INTERESES):
   - subsidiary=6 appears on ALL expanded rows
   - retencion_en_fuente appears ONLY on first expanded row
6. Zero retencion values are preserved (not treated as None)

## Expected Output Column Order (16 columns)

1. customer_external_id
2. invoice_core_id
3. concept_type
4. payment_date
5. payment_amount
6. currency
7. payment_ref
8. account
9. araccount
10. exchangerate
11. comision_banco
12. Spread PA
13. Spread FK
14. Spread Supra
15. **subsidiary** (value: 6 for Mexico)
16. **retencion_en_fuente** (first row only)

## Error Handling to Verify

- If Retención column is missing from input: retencion_en_fuente should be None for all rows
- If Retención value is empty/blank: retencion_en_fuente should be None
- If Retención value is 0: retencion_en_fuente should be 0.0 (preserved)

## API Endpoints Exercised

- `POST /api/tesoreria/validate/mexico` - Validate uploaded file
- `POST /api/tesoreria/convert/mexico` - Convert and download template

## Notes

- The subsidiary value of `6` corresponds to the Mexico subsidiary in NetSuite (Colombia uses `4`)
- This mirrors the Colombia implementation but with Mexico-specific values
- The "first row only" pattern for retencion follows the same logic as Colombia
- No frontend changes are needed - this is purely backend Excel generation
