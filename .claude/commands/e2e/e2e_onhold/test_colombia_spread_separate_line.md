# E2E Test: Colombia Payment Conversion - Spread Separate Line

Test the special case where capital-only Pago en Linea payments generate a separate SPREAD output line.

## User Story

As a Treasury (Tesoreria) department user
I want spread amounts for capital-only online payments to appear as separate output lines
So that NetSuite can properly process and reconcile the spread revenue separately from the main payment application

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with capital-only Pago en Linea payment available

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_co_spread_separate.xlsx`

This fixture should contain:
1. A row with "Pago en linea" as Medio de pago and ONLY Capital with value (no other concepts)
2. A row with "Pago en linea" but multiple concepts (Capital + Intereses) for comparison
3. A row with "Manual" payment and only Capital (should NOT create separate spread line)

Required columns for the test file:
- Cliente: Test client name
- Identificacion del cliente: 123456789
- Codigo de desembolso: CO:900759388:1:7:PAG
- Codigo de recaudo: REC-001
- Fecha de pago: 01/12/2025
- Moneda: USD
- Capital: 1234.56 (for row 1)
- Banco remitente: Test Bank
- Medio de pago: "Pago en linea" (row 1), "Pago en linea" (row 2), "Manual" (row 3)
- Tasa de cambio de FK/en linea: 3854.70815
- Spread: 10 (spread value)
- Total pagado [USD]: 1000 (so spread amount = 10 * 1000 = 10000 COP)
- NT: empty (for Spread FK) or "NT" (for Spread PA)

## Test Steps

1. **Login as tesoreria or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite/colombia`

3. Take a screenshot of the Colombia converter page initial state

4. **Verify** Colombia converter page elements:
   - Page title "Aplicacion de Pagos - Colombia"
   - File upload area present
   - Convert button initially disabled

5. Upload the test Excel file with capital-only Pago en Linea payment

6. **Verify** validation preview appears:
   - Source row count displayed
   - Column validation status shows all required columns found
   - Estimated output rows displayed

7. Take a screenshot of validation preview

8. **Verify** Convert button is now enabled

9. Click "Convertir y Descargar" button

10. **Verify** conversion completes:
    - Download starts or download link appears
    - Success message with conversion statistics displayed

11. Take a screenshot of completion state with statistics

12. **Verify** the statistics show SPREAD concept in the breakdown (if displayed)

13. Download and inspect the generated Excel file

14. **Verify** the output file contains:
    - For capital-only Pago en Linea row:
      - One row with concept_type = "CAPITAL"
      - One row with concept_type = "SPREAD"
      - CAPITAL row has empty Spread FK and Spread PA columns
      - SPREAD row has:
        - Same customer_external_id, invoice_core_id, payment_date, payment_ref as CAPITAL row
        - payment_amount = spread_value * total_pagado_usd (10000 COP in test)
        - currency = "COP"
        - account = blank/empty
        - araccount = blank/empty
        - exchangerate = same as CAPITAL row
    - For multi-concept Pago en Linea row:
      - NO separate SPREAD row
      - Spread FK or Spread PA column populated on first concept row
    - For Manual payment with only Capital:
      - NO separate SPREAD row
      - Spread FK or Spread PA column populated (standard behavior)

## Success Criteria

- Upload and validation work correctly
- Conversion completes successfully
- Capital-only Pago en Linea creates separate SPREAD row
- SPREAD row has blank account and araccount fields
- SPREAD row has correct payment_amount (spread * total_pagado_usd)
- Multi-concept Pago en Linea keeps standard behavior (spread in columns)
- Manual payments keep standard behavior regardless of concept count
- 3 screenshots are captured:
  1. Colombia converter page initial state
  2. Validation preview after file upload
  3. Conversion completion with statistics

## Error Handling to Verify

- Empty spread value should not create SPREAD line (even if capital-only)
- Zero total_pagado_usd should not create SPREAD line
- Missing Medio de pago should default to standard behavior

## API Endpoints Exercised

- `POST /api/tesoreria/validate/colombia` - Validate uploaded file
- `POST /api/tesoreria/convert/colombia` - Convert and download template

## Notes

- This test validates the new capital-only Pago en Linea spread behavior
- The SPREAD concept type is Colombia-specific
- Exchange rate adjustment (subtracting spread) should still occur on the CAPITAL row
- The payment_ref should be identical for CAPITAL and SPREAD rows from the same source row
