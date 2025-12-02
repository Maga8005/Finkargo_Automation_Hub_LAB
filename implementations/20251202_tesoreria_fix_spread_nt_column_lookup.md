# Bug Fix: Spread Values Always Going to Spread FK Column

**Date:** 2025-12-02
**Spec:** specs/bug-fix-spread-nt-column-lookup.md

## Summary

Fixed a bug where all spread values were incorrectly routed to the "Spread FK" output column, even when the input file's "NT" column contained the text "NT". The spread should go to "Spread PA" when the NT column contains "NT".

## Root Cause

The spread routing logic was looking for a column named "NIT" (via `get_value("nit", optional_columns)`), but the actual column in the input file is named "NT". Since the "NIT" column doesn't exist, `nit_value` was always `None`, causing all spreads to route to "Spread FK".

## Changes Made

### 1. Removed incorrect "nit" mapping (`payment_catalogs.py`)

- Removed the line `"nit": "NIT",` from `COLOMBIA_OPTIONAL_COLUMNS`
- Updated comment on `"nt_flag": "NT"` to indicate it's also used for spread routing

### 2. Fixed spread routing logic (`payment_template_service.py`)

- Changed the variable from `nit_value` to `nt_value_for_spread`
- Changed the column lookup from `get_value("nit", optional_columns)` to `get_value("nt_flag", optional_columns)`
- Updated comments and debug log messages to reference "NT column" instead of "NIT"

## Before vs After

| Scenario | Before | After |
|----------|--------|-------|
| NT column contains "NT" | Spread FK (wrong) | Spread PA (correct) |
| NT column empty/other | Spread FK | Spread FK |

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py    |  3 +-
backend/src/core/servicios/payment_template_service.py     | 65 ++++++++--------------
2 files changed, 24 insertions(+), 44 deletions(-)
```

## Validation Results

- **Backend Tests:** 8 passed
- **TypeScript Check:** No errors
- **Frontend Build:** Successful (4.00s)
