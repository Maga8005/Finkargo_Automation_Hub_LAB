# Bug: PA Accounts CSV Semicolon Delimiter Not Properly Handled

## Bug Description
When uploading the CSV file `MovimientoDetallado NOV_25.csv` to the PA Report feature, the system returns the error "No se encontraron registros que coincidan con cuentas PA del catálogo." even though the file contains valid PA account transactions for the entire month. The CSV file uses semicolon (`;`) as the delimiter instead of comma, and is encoded in Latin-1 (ISO-8859-1) rather than UTF-8.

**Expected behavior**: The system should detect the semicolon delimiter, properly parse the CSV file with the correct encoding (Latin-1), and match PA accounts from the CSV against the catalog.

**Actual behavior**: The system returns an error claiming no PA accounts were found in the file.

## Problem Statement
The PA Report CSV upload fails to find matching PA accounts due to one or both of the following issues:
1. The CSV parsing may not correctly handle the encoding/delimiter detection in edge cases where pandas doesn't fail cleanly on UTF-8 before falling back to Latin-1
2. The PA account catalog table in the database may be empty, causing all account matches to fail

## Solution Statement
Improve the CSV parsing robustness by:
1. Reordering encoding attempts to try Latin-1 before UTF-8 for semicolon-delimited files (since semicolon delimiters are more common in European/Latin regions where Latin-1 is prevalent)
2. Add better logging and error messages that distinguish between "empty catalog" and "no matches found"
3. Validate that the parsed DataFrame actually contains the expected columns before proceeding with account matching

## Steps to Reproduce
1. Navigate to Finance → Reporte PA
2. Ensure a PA account catalog is loaded (upload the catalog Excel file first)
3. Upload the file `MovimientoDetallado NOV_25.csv` from the CSVs folder
4. Observe the error: "No se encontraron registros que coincidan con cuentas PA del catálogo."

## Root Cause Analysis
Investigation revealed:

1. **CSV File Characteristics**:
   - Delimiter: Semicolon (`;`)
   - Encoding: Latin-1 (ISO-8859-1), NOT UTF-8
   - Header row: Row 6 (0-indexed), with 6 title rows before it
   - Contains 294 unique account numbers
   - 52 of these accounts match the expected PA catalog

2. **Current Code Flow**:
   - `_detect_csv_delimiter()` correctly detects `;` as delimiter
   - `_detect_header_row()` correctly finds header at row 6
   - `_parse_csv()` tries encodings in order: `["utf-8", "utf-8-sig", "latin-1", "iso-8859-1"]`
   - UTF-8 fails at position 281 due to Latin-1 byte `0xed` (í character)
   - Falls back to Latin-1 which works correctly
   - Column renaming via `SOURCE_COLUMN_MAPPING` works correctly for most columns

3. **Potential Issue Points**:
   - The pandas `read_csv` with UTF-8 encoding may not fail cleanly in all cases, potentially producing partial/corrupted data that passes the `len(df.columns) > 1 and len(df) > 0` validation but has incorrect column names
   - The error message doesn't distinguish between "catalog is empty" vs "no matches found"
   - Missing validation step to confirm critical columns like `cuenta_linea_numero` exist after renaming

4. **Encoding Mismatch Details**:
   - CSV file: `í` = `0xed`, `ú` = `0xfa` (Latin-1 single bytes)
   - Python source: `í` = `\xc3\xad`, `ú` = `\xc3\xba` (UTF-8 multi-byte)
   - When properly decoded with Latin-1, the Unicode codepoints match (U+00ED, U+00FA)

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/pa_report_service.py` - Main file to fix. Contains `_parse_csv()`, `_detect_csv_delimiter()`, `_detect_header_row()`, and `upload_netsuite_file()` methods. The fix should improve encoding detection reliability and add better error messaging.
- `backend/src/repositorio/pa_rules_repository.py` - Contains `get_all_catalog_accounts()` method. May need to add logging to help diagnose empty catalog issues.
- `backend/src/adapter/rest/pa_routes.py` - API routes for PA report processing. No changes needed but useful for understanding the flow.
- `backend/src/interface/pa_dtos.py` - DTOs for PA report. May need to add a field to PAUploadResponse to indicate why matching failed.
- `app_docs/feature-550a54d1-pa-report-classification.md` - Feature documentation for PA Report Classification.

## Step by Step Tasks

### 1. Improve CSV Parsing Encoding Detection
- Read `backend/src/core/servicios/pa_report_service.py`
- Modify `_parse_csv()` method to:
  - Change encoding order to `["latin-1", "utf-8", "utf-8-sig", "iso-8859-1"]` when semicolon delimiter is detected (since semicolon CSVs are typically Latin-1)
  - Add a pre-validation step that tries to decode the first 1000 bytes with the selected encoding before passing to pandas
  - Add logging to show which encoding was successfully used

### 2. Add Column Validation After Parsing
- After `_rename_columns()` is called in `upload_netsuite_file()`, add validation to ensure the critical column `cuenta_linea_numero` exists
- If the column doesn't exist, return a clear error message listing the actual columns found
- This helps diagnose cases where encoding issues cause column name corruption

### 3. Improve Error Messages for Account Matching
- Modify `upload_netsuite_file()` to distinguish between:
  - Empty catalog: "No hay catálogo de cuentas PA cargado. Por favor suba el catálogo primero."
  - Catalog exists but no matches: "No se encontraron coincidencias. Cuentas en archivo: X, Cuentas en catálogo: Y. Verifique que el catálogo contenga las cuentas correctas."
- Log the first 5 account numbers from the CSV and first 5 from the catalog for debugging

### 4. Add Debug Logging to Repository
- Read `backend/src/repositorio/pa_rules_repository.py`
- Add debug logging to `get_all_catalog_accounts()` to log the number of accounts retrieved
- This helps diagnose if the catalog is actually loaded

### 5. Write Backend Tests for CSV Parsing
- Create test cases in `backend/tests/test_pa_report_service.py` for:
  - Semicolon-delimited CSV with Latin-1 encoding
  - CSV with title rows before header
  - CSV where account column renaming is verified
  - Empty catalog scenario
  - Successful matching scenario

### 6. Execute Validation Commands
- Run all validation commands to ensure the fix works correctly with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Before Fix - Reproduce the Bug
```bash
# Start the backend server (if not already running)
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8003

# Upload the CSV file via the API (this should show the error currently)
# Note: Requires authentication token - test via frontend UI
```

### After Fix - Verify Bug is Resolved
```bash
# Run backend tests for PA report service
cd backend && python -m pytest tests/test_pa_report_service.py -v

# Run all backend tests to ensure no regressions
cd backend && python -m pytest

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

### Manual Verification
1. Start the application (backend + frontend)
2. Log in with a user that has `finance` or `finance_admin` role
3. Navigate to Finance → Reporte PA
4. First, upload the PA account catalog file: `Catálogo de Cuenta.xlsx`
5. Then upload the CSV file: `MovimientoDetallado NOV_25.csv`
6. Verify that:
   - The file is parsed successfully
   - The system reports finding PA account matches
   - No encoding or delimiter errors occur

## Notes

1. **Encoding Priority Change Rationale**: Semicolon as a CSV delimiter is predominantly used in countries that use comma as a decimal separator (European/Latin countries), which also tend to use Latin-1 or ISO-8859-1 encoding. By detecting the semicolon delimiter first and prioritizing Latin-1 encoding for such files, we reduce the chance of encoding detection failures.

2. **Title Row Handling**: The current `_detect_header_row()` implementation correctly handles files with title rows before the actual header. The CSV in question has 6 title rows, and the code correctly detects the header at row 6.

3. **Catalog Dependency**: The PA Report feature requires the PA account catalog to be loaded before processing files. The improved error messages will make this dependency clearer to users.

4. **No New Libraries Required**: This fix uses existing dependencies (pandas, logging) and doesn't require new packages.

5. **Performance Consideration**: The pre-validation step that decodes the first 1000 bytes adds minimal overhead (microseconds) but significantly improves reliability for encoding detection.
