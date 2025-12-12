# E2E Test: Colombia Payment Conversion - Payment Group-Level SPREAD Decision

Test the payment group-level SPREAD line creation logic for Colombia payments. The decision to create a separate SPREAD line must be made at the payment group level (all rows with the same payment_ref), not at the individual row level.

## User Story

As a Treasury (Tesorería) department user processing Colombia payments
I want the spread line creation logic to consider ALL concepts across the entire payment group
So that spread is correctly placed in columns (for mixed-concept payments) or as a separate line (for capital-only Pago en Linea payments)

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with multi-row payment groups

## Test Scenario Overview

This test validates the **CRITICAL FIX**: The decision to create a separate SPREAD line is now made at the payment GROUP level, not individual row level.

**Key Scenarios:**

1. **Single-row, capital-only, Pago en línea** → Should create separate SPREAD line
2. **Multi-row group where one row has CAPITAL only, another has INTERESES** → Should NOT create separate SPREAD line (spread goes to INTERESES row columns)
3. **Multi-row group where ALL rows have only CAPITAL** → Should create separate SPREAD line
4. **Manual payment** → Should NEVER create separate SPREAD line (spread goes to columns)

## Test Steps

### Part 1: Navigate to Colombia Payment Converter

1. Navigate to the `Application URL` (http://localhost:5173)
2. Login with test tesoreria credentials
3. Navigate to `/tesoreria/plantillas-netsuite/colombia`
4. **Verify** Colombia converter page loads with title "Aplicación de Pagos - Colombia"
5. Take a screenshot of the Colombia converter page

### Part 2: Test Multi-Row Payment Group with Mixed Concepts

This is the **CRITICAL TEST CASE** - Row 1 has only CAPITAL, Row 2 has INTERESES. At the row level, Row 1 would incorrectly create a separate SPREAD line. At the group level, no separate SPREAD line should be created because the group has mixed concepts.

6. Create a test Excel file with the following data:

**Test Data for Multi-Row Mixed Concepts Group:**
```
Row 1 (same payment group):
- Identificación del cliente: 123456789
- Código de desembolso: CO:001
- Fecha de pago: 01/12/2025
- Moneda: COP
- Capital: 1000
- 4x1000: 0
- Fondo de garantías: 0
- Intereses Corrientes: 0  (No interest in Row 1)
- Médio de pago: Pago en línea
- Spread: 10
- Total pagado [USD]: 500
- Tasa de cambio de FK/en línea: 4000
- Cuenta Remitente: (empty)

Row 2 (same payment group - same customer, date, currency, rate):
- Identificación del cliente: 123456789
- Código de desembolso: CO:002
- Fecha de pago: 01/12/2025
- Moneda: COP
- Capital: 0  (No capital in Row 2)
- 4x1000: 0
- Fondo de garantías: 0
- Intereses Corrientes: 50  (Has interest)
- Médio de pago: Pago en línea
- Spread: 10
- Total pagado [USD]: 500
- Tasa de cambio de FK/en línea: 4000
- Cuenta Remitente: (empty)
```

7. Upload the test Excel file
8. **Verify** validation preview shows 2 source rows
9. Take a screenshot of validation preview
10. Click "Convertir y Descargar" button
11. **Verify** conversion completes successfully

### Part 3: Verify Output File

12. Download and inspect the generated Excel file
13. **Verify** the output file contains:
    - 2 concept rows: CAPITAL (from Row 1) and INTERESES (from Row 2)
    - **NO separate SPREAD row** (this is the key fix!)
    - CAPITAL row should have `Spread FK = None` (spread does NOT go here)
    - INTERESES row should have `Spread FK = 10000` (spread = 10 * 1000 total_pagado_usd from group)
    - Both rows should have the same `payment_ref` (indicating same payment group)

14. Take a screenshot of the output preview or download confirmation

### Part 4: Test Capital-Only Group (Should Create SPREAD Line)

15. Create another test Excel file with a single-row capital-only payment:

**Test Data for Capital-Only Group:**
```
Row 1:
- Identificación del cliente: 987654321
- Código de desembolso: CO:003
- Fecha de pago: 02/12/2025
- Moneda: COP
- Capital: 2000
- 4x1000: 0
- Fondo de garantías: 0
- Intereses Corrientes: 0
- Médio de pago: Pago en línea
- Spread: 15
- Total pagado [USD]: 800
- Tasa de cambio de FK/en línea: 4100
- Cuenta Remitente: (empty)
```

16. Upload this file and convert
17. **Verify** output has:
    - CAPITAL row with `Spread FK = None`
    - SPREAD row with `payment_amount = 12000` (15 * 800)
    - SPREAD row has `currency = COP`, `account = None`, `araccount = None`

18. Take a screenshot of the conversion result

## Success Criteria

- Multi-row payment group with mixed concepts (CAPITAL + INTERESES) does NOT create separate SPREAD line
- Spread goes to the INTERESES row columns, not CAPITAL row
- Single-row capital-only Pago en línea creates separate SPREAD line
- Manual payments never create separate SPREAD lines
- All rows in a payment group have the same payment_ref
- 3 screenshots are captured:
  1. Colombia converter page
  2. Validation preview for mixed-concepts group
  3. Conversion completion showing concept breakdown

## Error Handling to Verify

- If the old (incorrect) logic were used, the multi-row mixed group would incorrectly create a SPREAD line when processing Row 1 (which only has CAPITAL)
- The fix ensures we check ALL concepts across the entire payment group before deciding

## API Endpoints Exercised

- `POST /api/tesoreria/validate/colombia` - Validate uploaded file
- `POST /api/tesoreria/convert/colombia` - Convert and download template

## Technical Notes

- Payment groups are identified by `payment_ref` which combines: customer_external_id + payment_date + cuenta_remitente + exchangerate
- **IMPORTANT**: Currency is NOT included in the payment_ref grouping key. This allows multi-currency payment groups (e.g., CAPITAL in USD + MORATORIOS in COP) to be correctly grouped together.
- The `_collect_payment_group_info()` method pre-processes all rows to collect group-level concept information
- The `_is_capital_only_pago_en_linea_for_group()` method takes a `Set[str]` of ALL concepts in the group, not just the current row's concepts

## Bug Fix Context

This E2E test validates a critical bug fix for multi-currency payment groups:

**Problem**: Previously, currency was included in the payment_ref grouping key. When a payment had:
- Row 1: USD, Capital=550.46
- Row 2: COP, Moratorios=1.54

These were treated as separate groups because `payment_ref` included currency. This caused:
- A separate SPREAD row to be incorrectly created for the USD CAPITAL row
- The COP MORATORIOS row only received partial spread in columns

**Fix**: Currency is now excluded from payment_ref generation. Rows with the same customer, date, cuenta_remitente, and exchange rate are grouped together regardless of currency.

**Expected behavior after fix**:
- Only 1 SPREAD row (for truly capital-only groups with different exchange rates)
- MORATORIOS row receives the full aggregated spread (~27600) in Spread PA column
