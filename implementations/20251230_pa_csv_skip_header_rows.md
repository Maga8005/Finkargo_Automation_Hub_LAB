# Implementation Report: PA CSV Upload - Skip Header Rows

**Date:** 2025-12-30
**ADW ID:** `61cc8e96`
**Module:** PA Report Service
**Type:** Patch

## Summary

Implemented auto-detection and skipping of title/header rows in PA report CSV uploads. The system now automatically detects the actual column header row by searching for the expected "Cuenta (línea): Número" column header within the first 20 lines of the file.

## Changes Made

- Added `_detect_header_row()` helper method to `PAReportService` that:
  - Scans the first 20 lines of the CSV file
  - Searches for the expected column header patterns (with encoding variations)
  - Returns the 0-indexed row number where headers are found
  - Returns 0 (no skip) if pattern not found, maintaining backward compatibility

- Updated `_parse_csv()` method to:
  - Call `_detect_header_row()` before parsing
  - Use `skiprows` parameter in `pd.read_csv()` to skip title rows
  - Log when title rows are detected and skipped

## Technical Details

### Header Pattern Detection
The implementation handles encoding variations by checking for multiple patterns:
- `Cuenta (línea): Número` (with accents)
- `Cuenta (linea): Numero` (without accents)
- Mixed accent variations

### Encoding Support
The header detection tries multiple encodings in order:
1. UTF-8
2. UTF-8 with BOM
3. Latin-1
4. ISO-8859-1

## Files Changed

```
backend/src/core/servicios/pa_report_service.py | 64 +++++++++++++++++++++++--
 1 file changed, 60 insertions(+), 4 deletions(-)
```

## Discrepancies Found

**None.** The plan was accurate and matched the existing codebase structure.

## Validation Results

| Check | Status |
|-------|--------|
| Python syntax check | Passed |
| Ruff linting | Pre-existing warnings only (unused imports) |
| Backend tests | Environment not configured |

**Note:** The validation environment does not have pandas installed. The syntax checks confirm the code is valid Python. Full import validation should be performed in the deployment environment.

## Testing Required

1. Upload the MovimientoDetallado NOV_25.csv file through the PA report upload endpoint
2. Verify it no longer shows "Faltan columnas requeridas" error
3. Verify the file is parsed correctly with data starting from row 7 (after 6 title rows)
4. Test backward compatibility with CSV files that have headers on row 1

## Risk Assessment

- **Risk Level:** Low
- **Backward Compatibility:** Maintained - files without title rows will continue to work as before
- **Edge Cases:** If the header pattern is not found in the first 20 lines, the system falls back to default behavior (no skipping)
