# Implementation: Map Spread Column from Input Data

**Date:** 2025-12-02
**Spec:** specs/chore-map-spread-column-from-input.md

## Summary

Replaced the complex placeholder-based spread calculation logic with simple direct mapping from input file columns. The spread value is now read directly from the input file's "Spread" column (column AX) and routed to either "Spread PA" or "Spread FK" output column based on whether the "NIT" column (column NR) contains the text "NT".

## Changes Made

### 1. Updated Colombia Optional Columns (`payment_catalogs.py`)

Added two new column mappings to `COLOMBIA_OPTIONAL_COLUMNS`:
- `"nit": "NIT"` - NIT column used to determine NT status for spread routing
- `"spread": "Spread"` - Spread value from input file (column AX)

### 2. Simplified Spread Logic (`payment_template_service.py`)

**Removed** complex calculation logic that used:
- `medio_pago` (payment method)
- `total_pagado_usd` (total paid in USD)
- `short_code` (provider identifier)
- Placeholder calculations with `tasa_banrep = 0.0` and `spread_rate = 0.0`

**Replaced with** simple NIT-based routing:
- Extract spread value from input file's "Spread" column
- Extract NIT value from input file's "NIT" column
- If NIT contains "NT" (case-insensitive) → spread goes to "Spread PA"
- If NIT does NOT contain "NT" → spread goes to "Spread FK"
- "Spread Supra" remains None (kept for output template compatibility)

## Mapping Logic

| NIT Column Contains | Output Column |
|---------------------|---------------|
| "NT" (any case)     | Spread PA     |
| Anything else       | Spread FK     |

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py    |  2 +
backend/src/core/servicios/payment_template_service.py     | 65 ++++++++--------------
2 files changed, 24 insertions(+), 43 deletions(-)
```

## Validation Results

- **Backend Tests:** 8 passed
- **TypeScript Check:** No errors
- **Frontend Build:** Successful (4.02s)

## Notes

1. The `medio_pago`, `total_pagado_usd`, and `short_code` optional column mappings were retained in case they are used elsewhere, but they are no longer extracted in `_process_row()` for spread calculations.

2. The "Spread Supra" column in the output template will remain empty/None. This can be updated if future requirements specify its usage.

3. This implementation simplifies the code significantly by using pre-calculated spread values from the input file rather than attempting to calculate them with placeholder rates.
