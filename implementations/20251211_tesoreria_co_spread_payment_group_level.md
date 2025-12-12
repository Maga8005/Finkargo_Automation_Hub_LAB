# Implementation Report: Colombia SPREAD Line Payment Group-Level Decision

## Summary

Fixed the logic that creates separate SPREAD lines in the Colombia payment template conversion. The decision to create a separate SPREAD line is now made at the **payment group level** (all rows with the same `payment_ref`), NOT at the individual row level.

---

## Update: 2025-12-11 - Spread Calculation Uses Aggregated Total Pagado USD

### Additional Fix Applied

Extended the group-level processing to also use the **aggregated `Total Pagado [USD]`** for spread amount calculation. Previously, even though group-level decision logic was implemented, each row still calculated spread using its own row-level `Total Pagado [USD]` value.

### Problem Addressed

**Before This Fix:**
- Each row calculated spread independently using its own `Total Pagado [USD]`
- Example: Row 1 (50 USD) calculated spread as `rate × 50`, Row 2 (500 USD) calculated `rate × 500`
- Result: Incorrect spread values for multi-row payment groups

**After This Fix:**
- Spread is calculated using the SUM of `Total Pagado [USD]` across ALL rows in the payment group
- Example: Aggregated total = 550, spread = `rate × 550` (calculated ONCE)
- Spread is assigned to only ONE output row per payment group (tracked via `spread_assigned` flag)

### Changes Made

#### `_process_row()` - Separate SPREAD line (lines 568-578):
```python
# Use aggregated total_pagado_usd from group_info if available
group_total_usd = group_info["total_pagado_usd"] if group_info else total_pagado_usd
if should_create_separate_spread_line and spread_value is not None and group_total_usd:
    separate_spread_amount = spread_value * group_total_usd
```

#### `_process_row()` - Spread columns (lines 626-646):
```python
# Check if spread was already assigned to another row in this payment group
spread_already_assigned = group_info.get("spread_assigned", False) if group_info else False

if is_spread_target and not spread_already_assigned:
    row_spread_pa = round(spread_pa * group_total_usd, 2) if spread_pa is not None and group_total_usd else None
    row_spread_fk = round(spread_fk * group_total_usd, 2) if spread_fk is not None and group_total_usd else None

    # Mark spread as assigned for this payment group
    if (row_spread_pa is not None or row_spread_fk is not None) and group_info:
        group_info["spread_assigned"] = True
```

### New Tests Added

**`TestSpreadAggregatedTotalPagadoUSD` class (5 tests):**
1. `test_spread_uses_aggregated_total_pagado_usd_from_group` - Verifies group-level aggregation
2. `test_spread_assigned_only_once_per_group_via_flag` - Verifies duplicate prevention
3. `test_spread_assignment_sets_flag_to_true` - Verifies flag tracking
4. `test_separate_spread_line_uses_aggregated_total` - Verifies SPREAD line uses aggregated total
5. `test_single_row_group_uses_same_value` - Verifies backward compatibility

### Test Results

```
============================= test session starts ==============================
TestSpreadAggregatedTotalPagadoUSD: 5 passed
Full test suite: 152 passed, 49 warnings
```

### Files Changed (This Update Only)

```
backend/src/core/servicios/payment_template_service.py | +20 lines (spread aggregation logic)
backend/tests/test_payment_template_service.py         | +374 lines (5 new test methods)
```

---

## Problem Statement

**Previous Behavior (Incorrect):**
- The check for capital-only Pago en Linea was done per-row using `_is_capital_only_pago_en_linea()`
- When a payment group had multiple input rows, each row was evaluated independently
- Row 1 with only CAPITAL would incorrectly trigger a separate SPREAD line, even if Row 2 in the same group had INTERESES or other concepts

**Correct Behavior (After Fix):**
- Pre-process all rows to collect group-level concept information
- Aggregate ALL concepts across the entire payment group
- Only create separate SPREAD line when the ENTIRE group has only CAPITAL and uses "Pago en línea"
- If ANY row in the group has non-CAPITAL concepts, spread goes to columns

## Implementation Details

### New Methods Added

1. **`_is_capital_only_pago_en_linea_for_group()`** (lines 990-1028)
   - Accepts a `Set[str]` of all concepts in the payment group
   - Returns True only if `group_concepts == {"CAPITAL"}` and payment method is "Pago en línea"
   - Country must be Colombia

2. **`_collect_payment_group_info()`** (lines 1108-1240)
   - Pre-processing phase that scans all rows before main processing loop
   - Groups rows by `payment_ref`
   - Collects: all concepts, medio_pago, total_pagado_usd, first non-CAPITAL COP row index
   - Returns `Dict[str, Dict]` keyed by payment_ref

### Modified Methods

1. **`convert_to_netsuite_template()`** (lines 217-294)
   - Added call to `_collect_payment_group_info()` before main loop
   - Passes `group_info` to `_process_row()` for each row

2. **`_process_row()`** (lines 326-357, 531-582, 600-628)
   - Added `group_info: Optional[Dict] = None` parameter
   - Updated SPREAD line decision to use group-level check
   - Added spread placement logic to skip CAPITAL-only rows when group has mixed concepts

## Key Scenarios Handled

| Payment Group | Row 1 Concepts | Row 2 Concepts | Combined | Separate SPREAD? |
|--------------|----------------|----------------|----------|------------------|
| Group A | CAPITAL | (none) | {CAPITAL} | YES (Pago en línea) |
| Group B | CAPITAL | INTERESES | {CAPITAL, INTERESES} | NO → to INTERESES |
| Group C | CAPITAL | CAPITAL, COSTOS_FIJOS | {CAPITAL, COSTOS_FIJOS} | NO → to COSTOS_FIJOS |
| Group D | CAPITAL | CAPITAL | {CAPITAL} | NO (Manual payment) |

## Tests Added

- `TestPaymentGroupLevelSpreadDecision` class (6 tests)
- `TestPaymentGroupPreProcessing` class (2 tests)
- `TestProcessRowWithGroupContext` class (3 tests)

Total: **11 new tests**, all passing

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 316 +++++++++-
backend/tests/test_payment_template_service.py         | 659 +++++++++++++++++++++
```

Total: **975 lines added**

## New Files Created

- `.claude/commands/e2e/test_co_spread_payment_group_level.md` - E2E test specification

## Validation Results

- **Backend tests**: 149 passed, 50 warnings
- **Payment template service tests**: 46 passed
- **Ruff check (payment_template_service.py)**: All checks passed
- **Frontend lint**: 0 errors, 4 warnings (pre-existing)
- **TypeScript check**: Passed
- **Frontend build**: Successful

## Discrepancies Found

None. The plan accurately reflected the codebase structure and implementation approach.

## Backward Compatibility

- The `_is_capital_only_pago_en_linea()` method is preserved (marked as deprecated) for backward compatibility
- Single-row payment groups work identically to before (the group context just confirms what the row-level check would have found)
- All existing tests continue to pass

## Technical Notes

- The key insight is that `payment_ref` is already used for grouping payments, so we leverage the same grouping key
- The pre-processing phase adds minimal overhead (single pass through DataFrame)
- Logging added at INFO level for group-level decisions to aid debugging
