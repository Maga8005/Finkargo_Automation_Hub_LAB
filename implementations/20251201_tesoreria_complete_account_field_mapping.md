# Treasury Module: Complete Account Field Mapping for Colombia

**Date:** 2025-12-01
**Module:** Tesorería (Treasury)
**Type:** Chore

## Summary

Implemented bank account mapping for the Colombia treasury module to populate the `account` field in the NetSuite payment template output (`Aplicacion_Pagos_Co`). Previously, this field was always blank/null.

## Problem

The treasury module's Colombia functionality was not generating a value for the `account` field in the output Excel file. All rows showed blank values for this field, which should be populated from the upload file using the `Cuenta Remitente` column.

## Solution

Added a mapping dictionary and lookup function to convert bank account numbers from the source file's `Cuenta Remitente` column to their corresponding NetSuite internal account IDs.

### Bank Account Mapping

| CTA (Cuenta Remitente) | ID Interno (account) |
|------------------------|---------------------|
| 60100001091 | 230 |
| 60100005374 | 2346 |
| 42861435 | 231 |
| 60100004638 | 1439 |
| 2600000313 | 2439 |
| 1250001972 | 232 |
| 36449096 | 235 |
| 3644-6725 | 236 |
| 709396827 | 2441 |
| 3304261649 | 1493 |
| 5089889016 | 239 |
| 3304296965 | 1492 |
| 9562345678749720 | 2418 |
| 8482979559 | 2498 |

## Changes Made

### 1. `backend/src/core/servicios/catalogs/payment_catalogs.py`

- Added `COLOMBIA_BANK_ACCOUNT_MAPPING` dictionary mapping bank account numbers (strings) to NetSuite internal IDs (integers)
- Added `get_bank_account_id(cuenta_remitente, country)` helper function that:
  - Normalizes the input by stripping whitespace
  - Looks up the account in the mapping dictionary
  - Returns the internal ID or None if not found
  - Only applies to Colombia (returns None for other countries)

### 2. `backend/src/core/servicios/payment_template_service.py`

- Added import for `get_bank_account_id` function
- In `_process_row` method:
  - Added extraction of `cuenta_remitente` from optional columns
  - Added call to `get_bank_account_id()` to get the internal account ID
  - Updated output row generation to use `account_id` instead of `None`

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py    | 49 ++++++++++++++++++++
backend/src/core/servicios/payment_template_service.py     |  7 ++-
2 files changed, 55 insertions(+), 1 deletion(-)
```

## Validation

- ✅ Backend tests pass (8 tests)
- ✅ Backend linting passes (ruff check)
- ✅ Frontend TypeScript type check passes
- ✅ Frontend build succeeds

## Notes

- The `cuenta_remitente` column was already defined in `COLOMBIA_OPTIONAL_COLUMNS` as `"Cuenta Remitente"`, so the column mapping infrastructure was already in place
- Account numbers are stored as strings to handle variations (e.g., "3644-6725" with hyphen)
- México mapping is not yet implemented; the function returns None for non-Colombia countries
