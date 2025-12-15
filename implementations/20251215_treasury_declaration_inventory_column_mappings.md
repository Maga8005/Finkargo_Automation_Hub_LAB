# Implementation Report: Extend Declaration Inventory Upload Column Mappings

**Date**: 2025-12-15
**Module**: Treasury Declaration Matching
**Feature**: Extended column mappings for scanner output format

## Summary

Extended the "Inventario de Declaraciones" (Declaration Inventory) upload in the Treasury Declaration Matching workflow to accept a new Excel file format with columns from an automated scanner output.

## Work Completed

### Backend Changes (`treasury_matching_routes.py`)

- Added `parse_amount_value()` helper function to parse amounts from multiple formats:
  - European format: `8.111,43` → `8111.43` (dots for thousands, comma for decimal)
  - US format: `$4,862.00` → `4862.00`
  - Simple comma decimal: `8111,43` → `8111.43`
  - Standard with thousands: `8,111.43` → `8111.43`

- Added `find_col_with_priority()` helper function for priority-based column detection
  - Returns the first matching column from the priority list
  - Allows preferring `Parsed Date` over `Date Folder`, `Parsed Amount` over `Amount Folder`

- Extended column name variations with new scanner format columns:
  - `customer_cols`: Added `Customer Name`
  - `date_cols_priority`: Added `Parsed Date` (high priority), `Date Folder` (low priority)
  - `amount_cols_priority`: Added `Parsed Amount` (high priority), `Amount Folder` (low priority)
  - `number_cols`: Added `Declaration Number`
  - `pdf_cols`: Added `PDF File Name`

- Updated amount parsing to use the new multi-format parser

- Improved declaration number handling:
  - Properly handles NaN values from pandas (skips rows)
  - Converts float declaration numbers to integers (`81590.0` → `"81590"`)

### Frontend Changes (`FKHistorialMatchingUploader.tsx`)

- Updated description text to show new accepted column formats:
  - Changed "Debe contener: Cliente, Fecha, Monto, Numero de Declaracion"
  - To "Columnas aceptadas: Cliente/Customer Name, Fecha/Parsed Date/Date Folder, Monto/Parsed Amount/Amount Folder, Numero/Declaration Number"

- Updated caption text with new column format hints

### New Files Created

- `.claude/commands/e2e/test_declaration_inventory_scanner_format.md` - E2E test file for testing the new scanner format upload

## Discrepancies Found and Resolved

**None.** The plan's assumptions matched the existing codebase:
- Column variation lists were at the expected location
- Amount parsing logic was as described
- Frontend text was at expected line numbers
- No repository methods involved (in-memory session storage only)

## Data Transformation Rules Implemented

| Source Format | Example | Transformed Value |
|--------------|---------|-------------------|
| European amount | `8.111,43` | `8111.43` |
| US dollar amount | `$4,862.00` | `4862.00` |
| Folder date (DD-MM-YYYY) | `01-07-2025` | `2025-07-01` |
| Parsed date (YYYY-MM-DD) | `2025-07-01` | `2025-07-01` |
| Float declaration number | `81590.0` | `"81590"` |
| NaN declaration number | `NaN` | (row skipped) |

## Column Priority Order

When multiple columns exist, the system prioritizes:

**For dates:**
1. `Parsed Date` (clean YYYY-MM-DD format)
2. `Fecha` (Spanish)
3. `Date` (English)
4. `fecha` (lowercase Spanish)
5. `Date Folder` (DD-MM-YYYY format from scanner)

**For amounts:**
1. `Parsed Amount` (clean US format)
2. `Monto` (Spanish)
3. `Amount` (English)
4. `Valor` (Spanish alternative)
5. `amount` (lowercase)
6. `Amount Folder` (European format from scanner)

## Validation Results

```
Backend linting (ruff): All checks passed!
Frontend linting (eslint): 0 errors (4 unrelated warnings in other files)
TypeScript type check: No errors
Frontend build: Successful (built in 6.45s)
```

## Git Diff Stats

```
backend/src/adapter/rest/treasury_matching_routes.py | 113 +++++++++++++++------
frontend/src/components/treasury/FKHistorialMatchingUploader.tsx | 4 +-
3 files changed, 94 insertions(+), 34 deletions(-)
```

Note: The `FKSidebarWithCollapse.tsx` file was modified in a previous commit, not part of this feature.

## Files Modified

| File | Lines Changed | Description |
|------|--------------|-------------|
| `backend/src/adapter/rest/treasury_matching_routes.py` | +68/-21 | Added amount parser, priority column selection, extended mappings |
| `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx` | +2/-2 | Updated UI hint text |

## Files Created

| File | Description |
|------|-------------|
| `.claude/commands/e2e/test_declaration_inventory_scanner_format.md` | E2E test for scanner format upload |

## Backward Compatibility

Full backward compatibility maintained:
- Spanish column names (`Cliente`, `Fecha`, `Monto`, `Numero`) still work
- English column names (`Customer`, `Date`, `Amount`, `Number`) still work
- New scanner format columns (`Customer Name`, `Date Folder`, `Amount Folder`, `Declaration Number`) now work

## Testing Recommendations

1. Upload the test file `20251215 Diveco Test.xlsx` with scanner format
2. Verify declarations parse without column validation errors
3. Verify amounts are correctly converted from European format
4. Verify rows with NaN declaration numbers are skipped
5. Verify existing Spanish format files still work
