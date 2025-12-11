# Implementation Report: Colombia Payment Conversion - Spread Separate Line

**Date:** 2025-12-10
**Module:** Tesorería (Treasury)
**Feature:** Capital-Only Pago en Línea Spread Separate Line

## Summary

Implemented a feature to handle a special case in the Colombia Historial de Pagos to Aplicación de Pagos conversion. When a payment is made via "Pago en Línea" and the entire payment goes only to capital (no other concepts), the spread amount is now output as a separate line with `concept_type` = `SPREAD` instead of being included in the Spread FK/PA columns.

## Changes Made

### Backend Changes

1. **`backend/src/core/servicios/payment_template_service.py`**
   - Added `_is_capital_only_pago_en_linea()` method to detect when:
     - Country is Colombia
     - Payment method is "Pago en línea" (case-insensitive)
     - CAPITAL is the only non-zero concept
   - Added `_create_spread_output_row()` method to generate the SPREAD output row with:
     - `concept_type` = "SPREAD"
     - `currency` = "COP"
     - `account` = None (blank)
     - `araccount` = None (blank)
     - `payment_amount` = spread_value × total_pagado_usd
   - Modified `_process_row()` to:
     - Detect capital-only Pago en Línea payments
     - Create separate SPREAD row when condition is met
     - Ensure Spread FK/PA columns are blank when separate line is created

2. **`backend/tests/test_payment_template_service.py`** (NEW)
   - Added 17 unit tests covering:
     - `_is_capital_only_pago_en_linea()` detection logic
     - `_create_spread_output_row()` output format
     - Integration tests for full `_process_row()` behavior
     - Edge cases: zero spread, missing total_pagado_usd, manual payments

### Frontend Changes

1. **`frontend/src/types/tesoreria.ts`**
   - Added `'SPREAD'` to the `ConceptType` union type

### Test Files

1. **`.claude/commands/e2e/test_colombia_spread_separate_line.md`** (NEW)
   - E2E test specification for validating the spread separate line behavior

## Discrepancies Found

No discrepancies found between the plan and implementation. All assumptions in the plan were correct:
- The `_process_row` method structure matched expectations
- Column mappings were as documented
- No database changes were needed

## Test Results

```
17 passed in 0.94s (new tests)
118 passed in 1.92s (all backend tests)
```

## Validation Results

| Command | Status |
|---------|--------|
| `pytest tests/test_payment_template_service.py` | ✅ 17 passed |
| `pytest tests/` | ✅ 118 passed |
| `ruff check src/core/servicios/payment_template_service.py` | ✅ All checks passed |
| `npm run lint` | ✅ No new errors |
| `npx tsc --noEmit` | ✅ No errors |
| `npm run build` | ✅ Built successfully |

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 115 ++++++++++++++++++++-
frontend/src/types/tesoreria.ts                        |  17 ++-
```

## New Files

```
backend/tests/test_payment_template_service.py
.claude/commands/e2e/test_colombia_spread_separate_line.md
specs/issue-none-adw-none-sdlc_planner-colombia-spread-separate-line.md
```

## Business Logic Summary

### Detection Criteria
A separate SPREAD row is created when ALL of the following are true:
1. Country is Colombia
2. `Médio de pago` contains "pago en l" (case-insensitive)
3. CAPITAL is the only concept with a non-zero value

### Output Format
When creating a separate SPREAD row:
- **CAPITAL row**: Spread FK and Spread PA columns are blank
- **SPREAD row**:
  - Same customer_external_id, invoice_core_id, payment_date, payment_ref
  - `concept_type` = "SPREAD"
  - `payment_amount` = spread_value × total_pagado_usd
  - `currency` = "COP"
  - `account` = blank
  - `araccount` = blank
  - `exchangerate` = same as CAPITAL row

### Standard Behavior (unchanged)
When multiple concepts exist or payment method is not "Pago en línea":
- Spread values are placed in Spread FK or Spread PA columns on the first concept row
- No separate SPREAD row is created

## Notes

- This feature is Colombia-specific. México conversion is not affected.
- The exchange rate adjustment for Pago en línea (subtracting spread from rate) still occurs on the CAPITAL row.
- The payment_ref is identical for CAPITAL and SPREAD rows from the same source row.
