# Patch: Skip header rows in PA report CSV upload

## Metadata
adw_id: `61cc8e96`
review_change_request: `The file has 6 title rows before the column headers. Adjust the upload so that it can accept the file but ignore these first 6 rows.`

## Issue Summary
**Original Spec:** N/A - This is a patch for CSV upload handling
**Issue:** When uploading the MovimientoDetallado CSV file, the system fails with "Faltan columnas requeridas: Cuenta (línea): Número, Cuenta (línea): Nombre, Débito, Crédito, Saldo" because the file has 6 title/header rows before the actual column headers on row 7.
**Solution:** Modify the `_parse_csv` method in `pa_report_service.py` to auto-detect and skip header rows by looking for the row that contains the expected column headers (specifically "Cuenta (línea): Número").

## Files to Modify
Use these files to implement the patch:

1. `backend/src/core/servicios/pa_report_service.py` - Update `_parse_csv` method to detect and skip header rows

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update the `_parse_csv` method to detect header row
- Modify the `_parse_csv` method to scan the first N lines (e.g., 20) of the CSV to find the row containing the expected column header "Cuenta (línea): Número"
- Once found, use `skiprows` parameter in `pd.read_csv` to skip all rows before the header row
- If no header row is found, proceed with normal parsing (backward compatible)

### Step 2: Implement header detection logic
- Add a helper method `_detect_header_row` that:
  - Takes file content and delimiter as input
  - Scans the first 20 lines looking for "Cuenta (línea): Número" or "Cuenta (linea): Numero" (handle encoding variations)
  - Returns the row number (0-indexed) where headers are found, or 0 if not found
- Update `_parse_csv` to call this method and use the result as `skiprows`

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check**
   - Command: `cd backend && python -m py_compile src/core/servicios/pa_report_service.py`

2. **Backend Linting**
   - Command: `cd backend && ./venv/bin/ruff check src/core/servicios/pa_report_service.py`

3. **Import Validation**
   - Command: `cd backend && python -c "from src.core.servicios.pa_report_service import PAReportService; print('PAReportService OK')"`

4. **All Backend Tests**
   - Command: `cd backend && python -m pytest -v --tb=short`

5. **Manual Test**
   - Upload the MovimientoDetallado NOV_25.csv file through the PA report upload endpoint
   - Verify it no longer shows "Faltan columnas requeridas" error
   - Verify the file is parsed correctly with data starting from row 7

## Patch Scope
**Lines of code to change:** ~30
**Risk level:** low
**Testing required:** Unit test for header detection, manual upload test with the provided CSV file
