# Implementation: Colombia Manual COP Spread Group Aggregation Fix

**Date:** 2025-12-11
**Module:** Tesorería - Colombia Payment Template Conversion
**Author:** Claude Code

## Summary

Fixed a bug where Manual COP spread calculation was using only the individual row's `Total pagado [USD]` instead of aggregating across all rows in the same payment group. This resulted in incorrect (partial) spread values when payment groups had multiple input rows.

## Changes Made

### 1. Fixed Manual COP spread calculation to use group total (lines 617-624)
**File:** `backend/src/core/servicios/payment_template_service.py`

**Before:**
```python
manual_spread = self._calculate_manual_cop_spread(
    tasa_fincargo=original_exchangerate,
    tasa_trm=tasa_trm,
    total_pagado_usd=total_pagado_usd
)
```

**After:**
```python
# Use group total USD for aggregated spread calculation
# This ensures spread is calculated across ALL rows in the payment group
group_total_usd_for_spread = group_info["total_pagado_usd"] if group_info else total_pagado_usd

manual_spread = self._calculate_manual_cop_spread(
    tasa_fincargo=original_exchangerate,
    tasa_trm=tasa_trm,
    total_pagado_usd=group_total_usd_for_spread
)
```

### 2. Updated INFO logging to show both row and group totals (lines 639-645)
Added clarity to logging by showing both `row_total_usd` and `group_total_usd` values.

### 3. Added unit tests
**File:** `backend/tests/test_payment_template_service.py`

Added new test class `TestManualCOPSpreadGroupAggregation` with 3 tests:
- `test_manual_cop_spread_uses_group_total_usd` - Verifies spread uses aggregated group total
- `test_manual_cop_spread_single_row_group` - Verifies single-row groups work correctly
- `test_manual_cop_spread_assigned_only_once_per_group` - Verifies spread assigned only once

## Business Logic

For Manual COP payments in Colombia:
- **Formula:** `Spread = (Tasa Fincargo - TRM) × Total Pagado USD (GROUP)`
- The `Total Pagado USD` must be the SUM across ALL rows in the payment group
- Spread is assigned only once per group (to the first eligible row)

## Test Results

**Verified with test file:** `20251211 CASOS RECOMPRAS.xlsx`

| Customer | Rows | Total USD | Before Fix | After Fix |
|----------|------|-----------|------------|-----------|
| CAPITAL INVESTMENTS | 2 | 250,000 | 17,070,426.75 | **17,300,000.00** |

**Calculation verification:**
- TRM for 2025-12-04: 3780.8
- Tasa Fincargo: 3850
- Before: (3850 - 3780.8) × 246,682.47 = 17,070,426.75 (partial)
- After: (3850 - 3780.8) × 250,000 = **17,300,000.00** (correct)

## Validation

- ✅ `pytest tests/test_payment_template_service.py` - 84 tests passed (3 new)
- ✅ `ruff check src/core/servicios/payment_template_service.py` - All checks passed
- ✅ `npm run lint` - Frontend linting passed (0 errors, 4 pre-existing warnings)
- ✅ `npm run build` - Frontend builds successfully
- ✅ Manual verification with test file confirmed fix

## Discrepancies from Plan

**None.** The implementation followed the plan exactly.

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 11 lines changed
backend/tests/test_payment_template_service.py        | 254 lines added
```

Note: The git diff also shows changes to unrelated files (`docs/PRD_Alianzas_Implementation_Prompts.md` and `frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx`) which were modified in a previous session.
