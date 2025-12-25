# E2E Test: Colombia Payment Conversion - Spread Assignment to Non-Capital Concepts

Test that spread values are assigned to non-CAPITAL concept rows when multiple concepts exist in a payment.

## User Story

As a Treasury (Tesoreria) department user
I want spread values to be assigned to non-CAPITAL concept lines when multiple concepts exist
So that NetSuite correctly associates spread revenue with the appropriate concept type for accurate financial reporting

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with multiple concepts (CAPITAL + COSTOS_FIJOS) available

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_co_multi_concept.xlsx`

This fixture should contain:
1. A row with CAPITAL + COSTOS_FIJOS (4x1000) - spread should go to COSTOS_FIJOS
2. A row with CAPITAL + INTERESES - spread should go to INTERESES
3. A row with only CAPITAL (Manual payment) - spread should go to CAPITAL

Required columns for the test file:
- Cliente: Test client name
- Identificacion del cliente: 123456789
- Codigo de desembolso: CO:900759388:1:6:PAG
- Codigo de recaudo: REC-001
- Fecha de pago: 01/12/2025
- Moneda: USD
- Capital: 1234.56
- 4x1000: 100.00 (for row 1, creates COSTOS_FIJOS)
- Intereses Corrientes: 50.00 (for row 2)
- Banco remitente: Test Bank
- Medio de pago: "Manual" (all rows)
- Tasa de cambio de FK/en linea: 3854.70815
- Spread: 10 (spread value)
- Total pagado [USD]: 1000 (so spread amount = 10 * 1000 = 10000 COP)
- NT: empty (for Spread FK)

## Test Steps

1. **Login as tesoreria or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite/colombia`

3. Take a screenshot of the Colombia converter page initial state

4. **Verify** Colombia converter page elements:
   - Page title "Aplicacion de Pagos - Colombia"
   - File upload area present
   - Convert button initially disabled

5. Upload the test Excel file with multiple concepts

6. **Verify** validation preview appears:
   - Source row count displayed
   - Column validation status shows all required columns found

7. Take a screenshot of validation preview

8. **Verify** Convert button is now enabled

9. Click "Convertir y Descargar" button

10. **Verify** conversion completes:
    - Download starts or download link appears
    - Success message with conversion statistics displayed

11. Take a screenshot of completion state with statistics

12. Download and inspect the generated Excel file

13. **Verify** the output file contains correct spread assignment:
    - For rows with CAPITAL + COSTOS_FIJOS:
      - CAPITAL row has `Spread FK` = None/empty
      - COSTOS_FIJOS row has `Spread FK` = 10000 (spread * total_pagado_usd)
    - For rows with CAPITAL + INTERESES:
      - CAPITAL row has `Spread FK` = None/empty
      - INTERESES row has `Spread FK` = calculated value
    - For rows with only CAPITAL (Manual payment):
      - CAPITAL row has `Spread FK` = calculated value (no other option)

14. **Verify** comision_banco continues to go to first row (idx == 0), which is CAPITAL

## Success Criteria

- Upload and validation work correctly
- Conversion completes successfully
- When multiple concepts exist, spread goes to first non-CAPITAL concept
- CAPITAL row has no spread values when other concepts exist
- When only CAPITAL exists (Manual), spread goes to CAPITAL
- comision_banco stays on first row regardless of concept type
- 3 screenshots are captured:
  1. Colombia converter page initial state
  2. Validation preview after file upload
  3. Conversion completion with statistics

## Error Handling to Verify

- Empty spread value should result in no spread on any row
- Zero CAPITAL with other concepts should still assign spread to non-CAPITAL

## API Endpoints Exercised

- `POST /api/tesoreria/validate/colombia` - Validate uploaded file
- `POST /api/tesoreria/convert/colombia` - Convert and download template

## Notes

- This test validates that spread is never assigned to CAPITAL when other concepts exist
- The ordering of concepts in the output follows: CAPITAL, SEGUROS, COSTOS_FIJOS, INTERESES, MORATORIOS
- comision_banco is independent of spread assignment and always goes to first row
- Mexico conversion should remain unchanged (spread always on first row)
