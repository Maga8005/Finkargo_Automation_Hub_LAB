# Implementation Report: Change Spread Calculation to Use Total Pagado (USD)

## Date: 2025-12-08

## Summary
Modified the spread calculation in the Tesorería payment template conversion to multiply the `Spread` value by `Total Pagado (USD)` from the input file, instead of the first concept's payment amount.

## Changes Made

### `backend/src/core/servicios/catalogs/payment_catalogs.py`

**Bug Fix:** Updated column mapping to match actual source file format:
- Changed from: `"Total pagado USD"` (without brackets)
- Changed to: `"Total pagado [USD]"` (with square brackets)
- Applied to both `COLOMBIA_OPTIONAL_COLUMNS` (line 113) and `MEXICO_OPTIONAL_COLUMNS` (line 160)

### `backend/src/core/servicios/payment_template_service.py`

1. **Added extraction of `total_pagado_usd`** (lines 371-378):
   - Extracts the "Total pagado [USD]" column value from the input file
   - Parses it as a float, handles None/invalid values gracefully

2. **Added debug logging** (lines 407-409):
   - Logs spread calculation details when both spread_value and total_pagado_usd are present
   - Format: `Spread calculation: {spread_value} × {total_pagado_usd} USD`

3. **Updated spread calculation formula** (lines 428-430):
   - Changed from: `spread × amount` (first concept payment amount)
   - Changed to: `spread × total_pagado_usd` (Total Pagado USD from input)
   - Added null check for `total_pagado_usd` to ensure no calculation when value is missing

4. **Updated comment** (line 428):
   - Changed from: "Multiply spread by payment amount for the first row"
   - Changed to: "Multiply spread by Total Pagado (USD) for the first row only"

## Behavior Changes

### Previous Calculation
```
Spread PA/FK = Spread Value × First Concept Payment Amount
Example: 0.05 × 1,000,000 COP = 50,000
```

### New Calculation
```
Spread PA/FK = Spread Value × Total Pagado (USD)
Example: 0.05 × 10,000 USD = 500
```

### Unchanged Behaviors
- Spread only appears on the **first concept row** (idx == 0)
- NT routing logic (Spread PA vs Spread FK based on NT column) unchanged
- Spread Supra remains always `None`

## Discrepancies Found
**Column Name Mismatch Bug:** During testing, discovered the column mapping used `"Total pagado USD"` but the actual source file uses `"Total pagado [USD]"` (with square brackets). This was fixed by updating `payment_catalogs.py`.

## Files Changed
```
backend/src/core/servicios/catalogs/payment_catalogs.py |  4 ++--
backend/src/core/servicios/payment_template_service.py  | 19 ++++++++++++++++---
2 files changed, 18 insertions(+), 5 deletions(-)
```

## Validation Results
- ✅ Backend tests: 48 passed
- ✅ Backend linting (ruff): All checks passed
- ✅ Frontend linting (eslint): Passed
- ✅ Frontend TypeScript check: Passed
- ✅ Frontend build: Successful

## Edge Cases Handled
1. **Missing Total Pagado (USD)**: If the input file doesn't have this column or the value is empty/null, spread columns will be `None` (no spread calculated)
2. **Invalid numeric values**: ValueError/TypeError exceptions are caught and `total_pagado_usd` remains `None`
