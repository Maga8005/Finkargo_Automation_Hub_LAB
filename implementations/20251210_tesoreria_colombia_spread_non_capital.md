# Implementation Report: Colombia Payment Conversion - Spread Assignment to Non-Capital Concepts

**Date:** 2025-12-10
**Module:** Tesorería (Treasury)
**Feature:** Spread Assignment to First Non-CAPITAL Concept

## Summary

Modified the Colombia Historial de Pagos to Aplicación de Pagos conversion so that when a source row has multiple concepts (CAPITAL plus other concepts like COSTOS_FIJOS, INTERESES, etc.), the spread values (Spread FK/Spread PA) are now assigned to the first non-CAPITAL concept line rather than to the CAPITAL line.

## Problem Statement

Previously, when processing a Colombia payment with multiple concepts (e.g., CAPITAL + COSTOS_FIJOS + INTERESES), the spread value was assigned to the first output row (idx == 0), which is typically CAPITAL due to dictionary ordering. This was incorrect because:
1. Spread represents revenue from the payment processing, not principal repayment
2. NetSuite reporting requires spread to be associated with fee/interest concepts, not capital
3. The current behavior could cause reconciliation issues in financial reporting

## Solution Implemented

### Backend Changes

1. **`backend/src/core/servicios/payment_template_service.py`**
   - Added `_get_spread_target_index()` helper method to determine which output row index should receive spread values:
     - For Colombia: returns index of first non-CAPITAL concept (or 0 if only CAPITAL)
     - For México: always returns 0 (standard behavior unchanged)
   - Modified `_process_row()` to use `spread_target_index` instead of `idx == 0`:
     - `comision_banco` still goes to first row (idx == 0)
     - `spread` (FK, PA, Supra) goes to `spread_target_index`

2. **`backend/tests/test_payment_template_service.py`**
   - Updated `test_multi_concept_pago_en_linea_no_spread_row` to verify:
     - CAPITAL row has no Spread FK/PA when other concepts exist
     - COSTOS_FIJOS row receives the Spread FK value
   - Added 10 new unit tests for `_get_spread_target_index()`:
     - `test_colombia_capital_only_returns_zero`
     - `test_colombia_capital_plus_costos_fijos_returns_one`
     - `test_colombia_capital_plus_intereses_returns_one`
     - `test_colombia_capital_plus_multiple_concepts_returns_first_non_capital`
     - `test_colombia_only_non_capital_concepts_returns_zero`
     - `test_colombia_zero_capital_with_others_returns_non_capital_index`
     - `test_mexico_always_returns_zero`
     - `test_mexico_case_insensitive`
     - `test_colombia_case_insensitive`
     - `test_empty_concepts_returns_zero`
   - Added 3 new integration tests for spread assignment:
     - `test_spread_assigned_to_intereses_not_capital`
     - `test_comision_banco_stays_on_first_row`
     - `test_spread_on_capital_when_only_capital_manual`

### Test Files

1. **`.claude/commands/e2e/test_colombia_spread_non_capital.md`** (NEW)
   - E2E test specification for validating spread is assigned to non-CAPITAL concepts

## Technical Details

### `_get_spread_target_index()` Method

```python
def _get_spread_target_index(
    self,
    processed_concepts: Dict[str, float],
    country: str
) -> int:
    """
    Determine which output row index should receive spread values.
    For Colombia: return index of first non-CAPITAL concept
    For México: return 0 (standard behavior)
    """
    if country.lower() != "colombia":
        return 0

    non_zero_concepts = [k for k, v in processed_concepts.items() if abs(v) > 0.001]

    for idx, concept in enumerate(non_zero_concepts):
        if concept != "CAPITAL":
            return idx

    return 0
```

### Spread Assignment Logic in `_process_row()`

```python
# Determine which row should get spread values (first non-CAPITAL for Colombia)
spread_target_index = self._get_spread_target_index(processed_concepts, country)

for idx, (concept_type, amount) in enumerate(processed_concepts.items()):
    if abs(amount) > 0.001:
        # comision_banco always goes to first row (idx == 0)
        row_comision_banco = comision_banco if idx == 0 else None

        # Spread goes to spread_target_index (first non-CAPITAL for Colombia)
        is_spread_target = (idx == spread_target_index)

        if should_create_separate_spread_line:
            row_spread_pa = None
            row_spread_fk = None
        else:
            row_spread_pa = ... if is_spread_target else None
            row_spread_fk = ... if is_spread_target else None
        row_spread_supra = spread_supra if is_spread_target else None
```

## Test Results

```
30 passed in 0.46s (payment template service tests)
131 passed in 1.64s (all backend tests)
```

## Validation Results

| Command | Status |
|---------|--------|
| `pytest tests/test_payment_template_service.py` | ✅ 30 passed |
| `pytest tests/` | ✅ 131 passed |
| `ruff check src/core/servicios/payment_template_service.py` | ✅ All checks passed |
| `npm run lint` | ✅ No new errors (4 pre-existing warnings) |
| `npx tsc --noEmit` | ✅ No errors |
| `npm run build` | ✅ Built successfully |

## Acceptance Criteria Validation

1. ✅ When a Colombia payment has CAPITAL plus other concepts:
   - Spread FK/PA is assigned to the first non-CAPITAL concept row
   - CAPITAL row has `Spread PA` = None and `Spread FK` = None

2. ✅ When a Colombia payment has only CAPITAL (Manual payment):
   - Spread FK/PA is assigned to CAPITAL row (no other option)

3. ✅ When a Colombia payment has only CAPITAL (Pago en Línea):
   - Separate SPREAD row is created (existing behavior from previous feature)

4. ✅ México conversion is not affected by this change (uses idx == 0)

5. ✅ All existing unit tests continue to pass (with updated expectations)

6. ✅ comision_banco continues to go to first row (idx == 0), independent of spread

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 35 ++++++++++++++++++++
backend/tests/test_payment_template_service.py         | 250 +++++++++++++++++++
```

## New Files

```
.claude/commands/e2e/test_colombia_spread_non_capital.md
implementations/20251210_tesoreria_colombia_spread_non_capital.md
```

## Notes

- This feature is Colombia-specific. México continues to use idx == 0 for spread assignment.
- The `comision_banco` field is independent and always assigned to the first row (idx == 0).
- Dictionary ordering in Python 3.7+ is guaranteed to be insertion order.
- The order of concepts in `processed_concepts` is: CAPITAL, SEGUROS, COSTOS_FIJOS, INTERESES, MORATORIOS.
- This change builds on top of the previous "Spread Separate Line" feature implemented earlier today.
