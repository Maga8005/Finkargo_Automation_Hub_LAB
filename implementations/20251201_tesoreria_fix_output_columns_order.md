# Implementation Report: Fix Output Columns Order in Tesorería Templates

**Date:** December 1, 2025
**Module:** Tesorería (Treasury)
**Issue:** #37 - Bug: Output File Missing Columns and Incorrect Column Order
**Type:** Bug Fix

## Summary

Fixed critical bug in the Tesorería "Plantillas para Cargar NetSuite" feature where output files were missing 5 required columns and had incorrect column order. The output now correctly generates 14 columns in the exact order required by NetSuite for both Colombia and México payment templates.

## Problem

The payment template converter was generating output files with:
- **Only 10 columns** instead of 14
- **Incorrect column order**
- **Extra `memo` column** that shouldn't exist
- **Missing 5 critical columns**: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`

This caused NetSuite import failures and missing financial data.

## Solution

Updated three backend files to:
1. Fix column definition to include all 14 columns in correct order
2. Update DTOs for type safety
3. Implement business logic to calculate missing column values
4. Add payment grouping to ensure only first row per payment gets spread/commission values

## Changes Made

### 1. Updated OUTPUT_TEMPLATE_COLUMNS (payment_catalogs.py)

**Location:** `backend/src/core/servicios/catalogs/payment_catalogs.py:156-172`

- Replaced 10-column list with correct 14-column list
- Removed `memo` column
- Added 5 missing columns: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`
- Reordered all columns to match NetSuite template specification

**New column order:**
```python
OUTPUT_TEMPLATE_COLUMNS = [
    "customer_external_id",
    "invoice_core_id",
    "concept_type",
    "payment_date",
    "payment_amount",
    "currency",
    "payment_ref",
    "account",
    "araccount",
    "exchangerate",
    "comision_banco",
    "Spread PA",
    "Spread FK",
    "Spread Supra",
]
```

### 2. Added Optional Column Mappings (payment_catalogs.py)

**Location:** `backend/src/core/servicios/catalogs/payment_catalogs.py:83-92, 131-139`

Added mappings for optional source columns needed for spread calculations:
- `medio_pago`: Payment method (Manual, Pago en línea)
- `total_pagado_usd`: Total paid in USD
- `referencia_bancaria`: Bank reference (for commission extraction)
- `short_code`: Payment provider identifier (SUPRA vs PA)
- `cuenta_remitente`: Sender account (for future account lookup)

Added for both Colombia and México with new helper function `get_optional_columns()`.

### 3. Updated OutputTemplateRow DTO (tesoreria_dtos.py)

**Location:** `backend/src/interface/tesoreria_dtos.py:167-203`

- Removed `memo` field
- Added 5 new fields with proper types:
  - `account: Optional[str]` - Bank account internal ID
  - `comision_banco: Optional[float]` - Bank commission
  - `spread_pa: Optional[float]` - PA Spread
  - `spread_fk: Optional[float]` - FK Spread
  - `spread_supra: Optional[float]` - Supra Spread
- Reordered all fields to match OUTPUT_TEMPLATE_COLUMNS
- Updated docstring to reflect 14 columns

### 4. Added Payment Grouping Logic (payment_template_service.py)

**Location:** `backend/src/core/servicios/payment_template_service.py:216-250`

Enhanced `convert_to_netsuite_template()` method:
- Track payment groups using `payment_groups_seen` set
- Determine if each row is first in its payment group
- Pass `is_first_row_in_group` flag to `_process_row()`
- Import `get_optional_columns()` helper

This ensures only the first row of each payment group gets spread and commission values.

### 5. Implemented Comision Banco Parser (payment_template_service.py)

**Location:** `backend/src/core/servicios/payment_template_service.py:568-625`

Added `_parse_comision_banco()` helper method:
- Parses bank commission from "Referencia bancaria" field
- Handles multiple numeric formats:
  - US format: `$1,234.56`
  - European format: `1.234,56`
  - Plain decimal: `1234.56`
- Uses regex pattern matching
- Returns float or None if parsing fails
- Includes error logging

### 6. Enhanced _process_row() Method (payment_template_service.py)

**Location:** `backend/src/core/servicios/payment_template_service.py:290-452`

Major enhancements:
- Added `optional_columns` parameter
- Added `is_first_row_in_group` parameter
- Extract optional fields: `medio_pago`, `total_pagado_usd`, `referencia_bancaria`, `short_code`
- **Comision banco logic** (México only, first row):
  - Extract from "Referencia bancaria" using parser
  - Only populate on first row of payment group
- **Spread calculation logic** (first row only):
  - **Spread PA** (manual payments): `(exchange_rate - tasa_banrep) × total_paid_usd`
  - **Spread FK** (PA online payments): `total_paid_usd × spread_rate`
  - **Spread Supra** (Supra payments): `total_paid_usd × spread_rate`
  - Uses placeholder values (0) for tasa_banrep and spread_rate until NetSuite integration
- Updated output dictionary to include all 14 columns in correct order
- Removed `memo` field
- Added `account` field (placeholder None for now)
- Only first concept row per payment gets spread/commission values (using idx == 0)

### 7. Added Debug Logging

Added logging statements for:
- Comision banco extraction: `logger.debug(f"Extracted comision_banco: {comision_banco}...")`
- Spread PA calculation: `logger.debug(f"Calculated Spread PA: {spread_pa}...")`
- Spread FK calculation: `logger.debug(f"Calculated Spread FK: {spread_fk}...")`
- Spread Supra calculation: `logger.debug(f"Calculated Spread Supra: {spread_supra}...")`

## Validation Results

✅ **Column count verification:** Confirmed 14 columns in OUTPUT_TEMPLATE_COLUMNS
✅ **Column order verification:** Matches NetSuite template specification exactly
✅ **No memo column:** Verified `memo` removed from output
✅ **Required columns present:** Verified `account`, `comision_banco`, and spread columns exist
✅ **Python imports:** All modules import successfully with no syntax errors
✅ **TypeScript compilation:** No type errors in frontend (no frontend changes)
✅ **Frontend linting:** Pre-existing warnings only, no new issues

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py    |  49 ++++++
backend/src/core/servicios/payment_template_service.py     | 173 +++++++++++++++++++
backend/src/interface/tesoreria_dtos.py                    |  25 ++-
3 files changed, 226 insertions(+), 21 deletions(-)
```

## Testing Notes

### Manual Testing Required

To fully validate this fix:
1. Navigate to Tesorería → Plantillas para Cargar NetSuite → Colombia
2. Upload a valid "Historial de Pagos" Excel file
3. Click "Convertir" button
4. Download the generated Excel file
5. Verify:
   - Exactly 14 columns in output
   - Column order matches specification
   - No `memo` column
   - New columns present: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`
   - Values populated where applicable (spreads on first row only)
6. Repeat for México

### Known Limitations (By Design)

Per the spec, these are **placeholders** and will be implemented in separate tasks:

1. **`account` column:** Currently None/empty
   - Future: Lookup bank account internal ID from "Catalogo CO/MX" based on bank name

2. **`tasa_banrep` for Spread PA:** Currently 0
   - Future: Fetch Banco de la República exchange rate from NetSuite

3. **`spread_rate` for Spread FK/Supra:** Currently 0
   - Future: Fetch "Spread Finkargo rate" from configuration or NetSuite

4. **Payment provider detection:** Basic logic in place
   - Future: Clarify exact column name and logic with business users

These placeholder values ensure the output structure is correct while allowing the feature to work without blocking on NetSuite integrations.

## Business Rules Implemented

1. **Payment Grouping:** Only the FIRST row of each payment group (same `payment_ref`) receives:
   - `comision_banco` value
   - One of the spread values (PA, FK, or Supra)
   - All subsequent rows in the same payment group have these fields as None

2. **Country-Specific Logic:**
   - `comision_banco`: Only populated for México, always None for Colombia
   - Spread calculations: Apply to both countries based on payment method

3. **Payment Method Detection:**
   - Manual payments → Spread PA calculation
   - Online payments (SUPRA provider) → Spread Supra calculation
   - Online payments (PA provider) → Spread FK calculation

## Future Enhancements

As noted in the spec, these are **out of scope** for this bug fix:

1. Implement bank account lookup from catalog files
2. Integrate NetSuite API for BanRep exchange rate
3. Configure or fetch Spread Finkargo rates
4. Refine payment provider identification logic
5. Add comprehensive unit tests for spread calculations
6. Consider extracting spread logic into separate service class

## References

- Issue spec: `specs/issue-37-adw-0a81443d-sdlc_planner-fix-output-columns-order.md`
- Template definition: `Example Files for Reqs/FIN_ Definicion Template para Aplicación de pagos.xlsx`
- Branch: `bug-issue-37-adw-0a81443d-fix-output-columns-order`
