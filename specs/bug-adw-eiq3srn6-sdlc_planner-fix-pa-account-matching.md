# Bug: PA Account Matching Fails Due to Float Conversion in CSV Parsing

## Bug Description
When uploading a semicolon-delimited CSV file (MovimientoDetallado NOV_25.csv) to the PA Report processing feature, the system returns an error stating "No se encontraron registros que coincidan con cuentas PA del catálogo" (No records found matching PA catalog accounts). This happens even though the CSV contains valid PA accounts that exist in the catalog.

The expected behavior is that accounts like `11100530` in the CSV should match with the catalog entry `11100530` and map to PA account `13020500101001`.

The actual behavior is that the account numbers from the CSV are being parsed as floats (e.g., `'13050501.0'`) while catalog accounts are clean strings (e.g., `'11101030'`), causing the string comparison to fail.

## Problem Statement
Pandas is interpreting the account number column (`Cuenta (línea): Número`) as numeric values when parsing the CSV. When these values are later converted to strings using `.astype(str)`, they retain the `.0` decimal suffix (e.g., `13050501.0` instead of `13050501`). This prevents any matches with the PA account catalog which stores account numbers as clean integer strings.

## Solution Statement
Modify the PA report service to properly handle the conversion of account numbers from float to clean integer strings. When converting the account number column to string, strip the `.0` suffix if the value was parsed as a float. This can be done by:
1. Converting the column to string
2. Using regex to remove trailing `.0` from any numeric strings

## Steps to Reproduce
1. Navigate to Finance > Reporte PA in the application
2. Upload the file: `Requirements_Meetings/PA Report/Req_reporte_pa/CSVs/MovimientoDetallado NOV_25.csv`
3. Observe the error message: "No se encontraron registros que coincidan con cuentas PA del catálogo"
4. Check backend logs to see the mismatch:
   - File accounts: `['13050501.0', '13551511.0', ...]` (with `.0` suffix)
   - Catalog accounts: `['11101030', '11200530', ...]` (clean strings)

## Root Cause Analysis
The bug occurs in `backend/src/core/servicios/pa_report_service.py` at line 161:

```python
df["cuenta_linea_numero"] = df["cuenta_linea_numero"].astype(str).str.strip()
```

When pandas reads the CSV file, it automatically infers column types. The "Cuenta (línea): Número" column contains values like `13050501` which pandas interprets as integers or floats. When the DataFrame is created, these become numeric types.

The `.astype(str)` conversion then produces strings like `"13050501.0"` for float values, rather than the expected `"13050501"`.

The matching logic at line 174 uses `.isin()`:
```python
pa_df = df[df["cuenta_linea_numero"].isin(catalog_accounts)].copy()
```

Since `"13050501.0"` != `"13050501"`, no accounts match.

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

- `backend/src/core/servicios/pa_report_service.py` - Contains the CSV parsing and account matching logic. The bug is in the `upload_netsuite_file` method where `cuenta_linea_numero` is converted to string without handling the float-to-string decimal suffix issue.

- `backend/src/repositorio/pa_rules_repository.py` - Contains the `get_all_catalog_accounts` method that retrieves catalog accounts as strings. No changes needed here, but important for understanding the expected data format.

- `app_docs/feature-550a54d1-pa-report-classification.md` - Documentation for the PA Report Classification feature, useful for context.

### New Files
- `.claude/commands/e2e/test_pa_csv_upload.md` - E2E test specification for validating PA CSV upload functionality

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix the account number string conversion in pa_report_service.py

- Open `backend/src/core/servicios/pa_report_service.py`
- Locate the `upload_netsuite_file` method (around line 93)
- Find the line that converts `cuenta_linea_numero` to string (line 161):
  ```python
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].astype(str).str.strip()
  ```
- Replace it with a more robust conversion that handles float-to-integer-string conversion:
  ```python
  # Convert account numbers to clean integer strings (remove .0 suffix from floats)
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].apply(
      lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace('.', '', 1).replace('-', '', 1).isdigit() else str(x).strip() if pd.notna(x) else ''
  )
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].str.strip()
  ```

  Alternatively, a simpler regex-based approach:
  ```python
  # Convert to string and remove trailing .0 from float representations
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].astype(str).str.strip()
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].str.replace(r'\.0$', '', regex=True)
  ```

### 2. Add a helper method for robust account number normalization

- Add a new private method `_normalize_account_number` in the `PAReportService` class to handle account number normalization consistently:
  ```python
  def _normalize_account_number(self, value) -> str:
      """
      Normalize account number to a clean string.

      Handles:
      - Float values (removes .0 suffix)
      - Integer values
      - String values (strips whitespace)
      - NaN/None values (returns empty string)
      """
      if pd.isna(value):
          return ""

      # Convert to string first
      str_value = str(value).strip()

      # Remove trailing .0 from float representations
      if str_value.endswith('.0'):
          str_value = str_value[:-2]

      return str_value
  ```

- Update the account number conversion to use this method:
  ```python
  df["cuenta_linea_numero"] = df["cuenta_linea_numero"].apply(self._normalize_account_number)
  ```

### 3. Add debug logging to verify the fix

- After the account number normalization, add logging to confirm values are now clean:
  ```python
  logger.debug(f"Sample normalized accounts from file: {df['cuenta_linea_numero'].head(5).tolist()}")
  ```

### 4. Create E2E test specification

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_pa_report_classification.md` to understand the E2E test format
- Create a new E2E test file at `.claude/commands/e2e/test_pa_csv_upload.md` that validates:
  1. Upload of a semicolon-delimited CSV file with account numbers
  2. Successful matching of accounts with the PA catalog
  3. No "No se encontraron registros" error when valid PA accounts are present
  4. Take screenshots to prove the bug is fixed

### 5. Run Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Backend validation
```bash
# Run backend tests
cd backend && python -m pytest

# Run backend linting
cd backend && ruff check src/

# Test the specific fix manually
cd backend && python -c "
import pandas as pd

# Simulate the bug scenario
test_data = {'cuenta_linea_numero': [13050501.0, 11100530.0, 13551511.0]}
df = pd.DataFrame(test_data)

# OLD behavior (bug)
old_result = df['cuenta_linea_numero'].astype(str).str.strip()
print('OLD (buggy):', old_result.tolist())

# NEW behavior (fix)
new_result = df['cuenta_linea_numero'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
print('NEW (fixed):', new_result.tolist())

# Verify fix
assert new_result.tolist() == ['13050501', '11100530', '13551511'], 'Fix verification failed'
print('Fix verified successfully!')
"
```

### Frontend validation
```bash
# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build
cd frontend && npm run build
```

### E2E validation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_csv_upload.md` to validate the PA CSV upload functionality works correctly

### Manual testing
1. Start the application locally (frontend on port 5175, backend on port 8003)
2. Log in as a finance user
3. Navigate to Finance > Reporte PA
4. Upload the file: `Requirements_Meetings/PA Report/Req_reporte_pa/CSVs/MovimientoDetallado NOV_25.csv`
5. Verify that:
   - The upload completes successfully
   - The message shows matched PA accounts (not "No se encontraron registros")
   - Account `11100530` is recognized and matched with the catalog

## Notes

- The bug affects all CSV files where pandas interprets account number columns as numeric types
- This is particularly common with semicolon-delimited CSVs from European/Latin regions
- The fix should be backward compatible - it won't break files that already have clean string account numbers
- Consider also applying similar normalization in the `_parse_csv` method's `dtype` parameter to prevent float interpretation in the first place, though the string normalization approach is safer and handles edge cases better
- An alternative prevention approach is to specify `dtype={'Cuenta (línea): Número': str}` in the pandas read_csv call, but this requires knowing the exact column name beforehand which may vary
