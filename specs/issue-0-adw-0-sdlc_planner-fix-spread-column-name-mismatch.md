# Bug: Spread Calculation Not Appearing in Output Due to Column Name Mismatch

## Bug Description
When processing the "Historial de Pagos" file through the Tesorería payment template converter, no spread calculations appear in the resulting Excel file despite the source file containing valid spread values. The output file shows `NaN` for all "Spread PA", "Spread FK", and "Spread Supra" columns.

**Expected Behavior:** Spread values should be calculated (Spread × Total Pagado USD) and appear on the first concept row for each source row.

**Actual Behavior:** All spread columns contain `NaN` values.

## Problem Statement
The column mapping in `COLOMBIA_OPTIONAL_COLUMNS` expects the column name `"Total pagado USD"`, but the actual source file uses `"Total pagado [USD]"` (with square brackets). This mismatch causes the `total_pagado_usd` value to always be `None`, which results in no spread calculation being performed.

## Solution Statement
Update the column mapping in `payment_catalogs.py` to use the correct column name with square brackets: `"Total pagado [USD]"`.

## Steps to Reproduce
1. Upload the file `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251208 Historial de Pagos example.xlsx` to the Tesorería Colombia converter
2. Convert to NetSuite template
3. Check the output file - all Spread PA, Spread FK, and Spread Supra columns are empty/NaN

## Root Cause Analysis
The source file has the column named `"Total pagado [USD]"` with square brackets:
```
Column 14: Total pagado [USD]
Values: [10799.335, 1380.665]
```

But the catalog mapping in `COLOMBIA_OPTIONAL_COLUMNS` (line 113) defines:
```python
"total_pagado_usd": "Total pagado USD",  # WITHOUT square brackets
```

When the code tries to find the column using normalized matching, it looks for `"total pagado usd"` but the actual normalized column name is `"total pagado [usd]"`. Since the column isn't found, `total_pagado_usd` remains `None`, and the spread calculation condition `total_pagado_usd is not None` fails, resulting in no spread being calculated.

## Affected Layer
- [x] Backend: core/servicios (business logic) - specifically the catalogs configuration

## Relevant Files
Use these files to fix the bug:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (line 113)
  - Contains `COLOMBIA_OPTIONAL_COLUMNS` with incorrect column name `"Total pagado USD"`
  - Needs to be changed to `"Total pagado [USD]"` to match the actual source file format

- **`backend/src/core/servicios/payment_template_service.py`** (lines 371-378)
  - Contains the code that extracts `total_pagado_usd` using the column mapping
  - No changes needed here, but useful to understand the extraction logic

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Column Name in Colombia Optional Columns
In `backend/src/core/servicios/catalogs/payment_catalogs.py`, update line 113:

- Change from:
  ```python
  "total_pagado_usd": "Total pagado USD",  # Total paid in USD for spread calculations
  ```

- Change to:
  ```python
  "total_pagado_usd": "Total pagado [USD]",  # Total paid in USD for spread calculations
  ```

### Step 2: Fix Column Name in México Optional Columns (if applicable)
In `backend/src/core/servicios/catalogs/payment_catalogs.py`, check line 160 and update if México files also use the same format:

- If México files use `"Total pagado [USD]"`, change from:
  ```python
  "total_pagado_usd": "Total pagado USD",
  ```

- Change to:
  ```python
  "total_pagado_usd": "Total pagado [USD]",
  ```

### Step 3: Verify Fix with Test Script
Run a test script to verify the column mapping now matches:

```bash
cd backend && source venv/bin/activate && python -c "
import pandas as pd
from src.core.servicios.catalogs.payment_catalogs import COLOMBIA_OPTIONAL_COLUMNS

source_file = '/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251208 Historial de Pagos example.xlsx'
df = pd.read_excel(source_file, engine='openpyxl')

expected_col = COLOMBIA_OPTIONAL_COLUMNS.get('total_pagado_usd', '')
df_columns_normalized = {col.strip().lower(): col for col in df.columns}
expected_normalized = expected_col.strip().lower()

print(f'Expected column: {expected_col}')
print(f'Normalized: {expected_normalized}')
print(f'Found in file: {expected_normalized in df_columns_normalized}')
if expected_normalized in df_columns_normalized:
    actual_col = df_columns_normalized[expected_normalized]
    print(f'Actual column name: {actual_col}')
    print(f'Values: {df[actual_col].tolist()}')
"
```

### Step 4: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- Verify column mapping fix works:
```bash
cd backend && source venv/bin/activate && python -c "
import pandas as pd
from src.core.servicios.catalogs.payment_catalogs import COLOMBIA_OPTIONAL_COLUMNS

source_file = '/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251208 Historial de Pagos example.xlsx'
df = pd.read_excel(source_file, engine='openpyxl')
expected_col = COLOMBIA_OPTIONAL_COLUMNS.get('total_pagado_usd', '')
df_columns_normalized = {col.strip().lower(): col for col in df.columns}
found = expected_col.strip().lower() in df_columns_normalized
print(f'Column mapping correct: {found}')
assert found, 'Column mapping still incorrect!'
print('SUCCESS: Column mapping is now correct')
"
```

- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

### Verification After Fix
After fixing the column mapping, the spread calculation should work as follows:

**Source Row 1:**
- Spread: 28
- Total pagado [USD]: 10799.335
- NT: "NT247" (contains "NT" → use Spread PA)
- Expected Spread PA: 28 × 10799.335 = **302,381.38**

**Source Row 2:**
- Spread: 28
- Total pagado [USD]: 1380.665
- NT: "NT247" (contains "NT" → use Spread PA)
- Expected Spread PA: 28 × 1380.665 = **38,658.62**

### One-Line Fix
This is a simple one-line fix - just changing the column name from `"Total pagado USD"` to `"Total pagado [USD]"`.
