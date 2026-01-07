# Implementation Report: Tesorería Subsidiary and Retencion Columns

**Date:** 2025-12-23
**Feature:** Add subsidiary and retencion_en_fuente columns to Aplicacion de Pagos CO
**Issue:** #6 ADW-91b5007b

## Summary

Added two new columns to the Colombia payment template output file:

1. **subsidiary** - Static column with value `4` for every output row (Colombia subsidiary ID in NetSuite)
2. **retencion_en_fuente** - Withholding tax column from input "Retención", appearing only on the first output row per source row

## Changes Made

- Added `retencion` to `COLOMBIA_OPTIONAL_COLUMNS` mapping for input column parsing
- Extended `OUTPUT_TEMPLATE_COLUMNS` from 14 to 16 columns
- Modified `_process_row()` to extract retencion value and add new columns to output
- Updated `_create_spread_output_row()` to include new columns for SPREAD rows
- Added 7 new unit tests for the new functionality
- Created E2E test file for end-to-end validation

## Discrepancies Found

None. The plan accurately described the existing code structure and patterns.

## Files Changed

```
 backend/src/core/servicios/catalogs/payment_catalogs.py    |   5 +-
 backend/src/core/servicios/payment_template_service.py     |  20 ++
 backend/tests/test_payment_template_service.py             | 324 +++++++++++++++++++++
 3 files changed, 348 insertions(+), 1 deletion(-)
```

## New Files Created

- `.claude/commands/e2e/test_tesoreria_new_columns.md` - E2E test specification

## Validation Results

| Command | Result |
|---------|--------|
| `pytest tests/test_payment_template_service.py` | 91 passed |
| `ruff check src/` | All checks passed |
| `npm run lint` | 0 errors (4 pre-existing warnings) |
| `npx tsc --noEmit` | No errors |
| `npm run build` | Success |

## Technical Details

### Column Positions
- Column 15: `subsidiary` - Always 4 for Colombia, None for México
- Column 16: `retencion_en_fuente` - Value from input "Retención" column, first row only

### Business Logic
- **subsidiary**: Fixed value `4` representing Colombia subsidiary in NetSuite
- **retencion_en_fuente**: Follows "first row only" pattern (same as `comision_banco` for México)
  - When a source row expands to multiple concepts (1:N), retencion only appears on idx=0
  - Zero values are preserved (not treated as None)
  - SPREAD rows get subsidiary=4 but retencion=None

### Input Column Handling
- Expected column name: "Retención" (with accent)
- Column is optional; when absent, retencion_en_fuente is None for all rows
- Values are parsed as float

## Test Coverage

New tests added:
1. `test_subsidiary_present_on_all_rows_colombia` - Verifies subsidiary=4 on all Colombia rows
2. `test_subsidiary_none_for_mexico` - Verifies subsidiary=None for México
3. `test_retencion_on_first_row_only` - Verifies retencion only on first expanded row
4. `test_retencion_none_when_not_in_input` - Verifies None when column missing
5. `test_retencion_zero_value_is_preserved` - Verifies 0.0 is preserved
6. `test_spread_row_has_subsidiary_but_not_retencion` - Verifies SPREAD row handling
7. `test_multiple_concepts_expansion_retencion_first_only` - Tests 1:N expansion

## Notes

- This is a Colombia-only feature; México does not require these columns
- No frontend changes needed - this is purely backend Excel generation
- Existing 84 tests continue to pass (no regressions)
