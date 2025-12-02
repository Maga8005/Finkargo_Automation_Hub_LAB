# Bug: Spread Values Always Going to Spread FK Column

## Bug Description
All spread values are being routed to the "Spread FK" output column, even when the input file's "NT" column contains the text "NT". When the NT column contains "NT", the spread value should go to the "Spread PA" column instead.

**Expected behavior:** When the "NT" column contains "NT" text → spread goes to "Spread PA"
**Actual behavior:** All spread values go to "Spread FK" regardless of NT column value

## Problem Statement
The spread routing logic is looking for a column named "NIT" (`"nit": "NIT"` in optional columns), but the actual column in the input file is named "NT" (which already exists as `"nt_flag": "NT"`). Since there is no "NIT" column in the input file, the `nit_value` is always `None`, causing all spreads to route to "Spread FK".

## Solution Statement
Change the spread routing logic to use the existing `"nt_flag"` optional column mapping (which maps to the "NT" column) instead of the incorrect `"nit"` mapping. Remove the unnecessary `"nit": "NIT"` entry from the optional columns since it duplicates the purpose of `"nt_flag"`.

## Steps to Reproduce
1. Upload a Historial de Pagos file for Colombia
2. Ensure the file has values in the "Spread" column (column AX)
3. Ensure some rows have "NT" text in the "NT" column
4. Convert the file to NetSuite template
5. Observe that ALL spread values appear in "Spread FK" column, even rows with "NT" in the NT column

## Root Cause Analysis
In `payment_template_service.py` line 372:
```python
nit_value = get_value("nit", optional_columns)
```

This looks up the internal name `"nit"` which maps to column name `"NIT"` in the optional columns. However, the input file's column is actually named `"NT"` (not `"NIT"`).

The existing `"nt_flag": "NT"` mapping in optional columns already correctly maps to the "NT" column, but the spread routing code uses the wrong internal name `"nit"` instead of `"nt_flag"`.

Since `get_value("nit", optional_columns)` returns `None` (column "NIT" doesn't exist), the condition `nit_value and "NT" in str(nit_value).upper()` is always `False`, causing all spreads to go to "Spread FK".

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/payment_template_service.py` - Contains the `_process_row` method with the spread routing logic. Line 372 uses the wrong internal column name `"nit"` instead of `"nt_flag"`.
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains the `COLOMBIA_OPTIONAL_COLUMNS` dictionary. The `"nit": "NIT"` entry should be removed as it's incorrect and duplicates `"nt_flag": "NT"`.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Remove incorrect "nit" mapping from payment_catalogs.py

- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Remove the line `"nit": "NIT",  # NIT column - used to determine NT status for spread routing` from `COLOMBIA_OPTIONAL_COLUMNS`
- The existing `"nt_flag": "NT"` mapping is correct and should be used for spread routing

### Step 2: Fix spread routing in payment_template_service.py

- Open `backend/src/core/servicios/payment_template_service.py`
- Change line 372 from:
  ```python
  nit_value = get_value("nit", optional_columns)
  ```
  To:
  ```python
  nt_value_for_spread = get_value("nt_flag", optional_columns)
  ```
- Update the spread routing condition (around line 389) from:
  ```python
  is_nt_spread = nit_value and "NT" in str(nit_value).upper()
  ```
  To:
  ```python
  is_nt_spread = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()
  ```
- Update the debug log messages to reference `nt_value_for_spread` instead of `nit_value`

### Step 3: Run Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

1. The `"nt_flag": "NT"` mapping already exists and correctly maps to the "NT" column in the input file. We don't need a separate "nit" mapping.

2. The variable `is_nt` (used for AR account selection around line 340) and `is_nt_spread` (used for spread routing) both check the same "NT" column but serve different purposes:
   - `is_nt`: Checks if NT column has ANY non-empty value → determines which AR account catalog to use
   - `is_nt_spread`: Checks if NT column contains the text "NT" → determines which spread column to use

3. This is a backend-only fix. No frontend changes are required.
