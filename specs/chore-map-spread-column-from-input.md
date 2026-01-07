# Chore: Map Spread Column from Input Data

## Chore Description
The spread values (Spread PA, Spread FK) in the output template are currently blank because the code uses placeholder calculations with hardcoded zero values. However, the spread data is already available in the input file:

- **Input Column AX**: Named "Spread" - contains the spread value
- **Input Column NR**: Named "NIT" - determines which output column receives the spread value

**Mapping Logic:**
- If the "NIT" column (column NR) contains the text "NT" → the spread value goes to **"Spread PA"** output column
- If the "NIT" column does NOT contain "NT" → the spread value goes to **"Spread FK"** output column

This is a simpler approach than the current complex calculation logic, as the data is pre-calculated in the input file.

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains column mappings for Colombia. Need to add the "spread" column to `COLOMBIA_OPTIONAL_COLUMNS` and potentially update the "nt_flag" mapping to match "NIT" column.
- `backend/src/core/servicios/payment_template_service.py` - Contains the `_process_row` method where spread values are calculated. Need to replace the complex calculation logic (lines 380-417) with simple column value extraction and NT-based routing.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Colombia Optional Columns in payment_catalogs.py

- Add a new entry to `COLOMBIA_OPTIONAL_COLUMNS` dictionary for the spread column:
  ```python
  "spread": "Spread",  # Spread value from input (column AX)
  ```
- Verify the "nt_flag" mapping points to the correct column name. The current mapping is `"nt_flag": "NT"` but the chore mentions column NR is called "NIT". Update if needed:
  ```python
  "nit": "NIT",  # NIT column (column NR) - used to determine NT status for spread routing
  ```

### Step 2: Update _process_row method in payment_template_service.py

- Extract the spread value from the input file using the new optional column mapping:
  ```python
  spread_value_raw = get_value("spread", optional_columns)
  spread_value = None
  if spread_value_raw:
      try:
          spread_value = float(spread_value_raw)
      except (ValueError, TypeError):
          pass
  ```

- Extract the NIT value to determine NT status for spread routing:
  ```python
  nit_value = get_value("nit", optional_columns)
  ```

- Replace the complex spread calculation logic (lines 380-417) with simple NT-based routing:
  ```python
  # Determine spread column based on NIT containing "NT"
  spread_pa = None
  spread_fk = None
  spread_supra = None  # Keep for compatibility but will be None

  if spread_value is not None:
      # Check if NIT contains "NT" text
      is_nt_spread = nit_value and "NT" in str(nit_value).upper()

      if is_nt_spread:
          spread_pa = spread_value
      else:
          spread_fk = spread_value
  ```

- Remove the old complex calculation logic that used `medio_pago`, `total_pagado_usd`, `exchangerate`, `tasa_banrep`, `spread_rate`, and `short_code` for spread calculations.

### Step 3: Update NT Detection Logic (if needed)

- The current NT detection for AR accounts uses:
  ```python
  nt_col_normalized = "nt"
  for col_name, source_col in df_columns_normalized.items():
      if col_name == nt_col_normalized:
          nt_value = row.get(source_col)
          is_nt = pd.notna(nt_value) and str(nt_value).strip() != ""
          break
  ```
- This may need to be updated to also check the "NIT" column for AR account determination, or keep separate logic for:
  1. AR account NT detection (existing "NT" column)
  2. Spread routing NT detection (new "NIT" column containing "NT" text)

- Clarify with the business logic whether these are the same or different columns. If they are the same, consolidate the logic.

### Step 4: Run Validation Commands

Execute every command to validate the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **Column Letter References**: The chore mentions "column AX" (Spread) and "column NR" (NIT). These are Excel column letters which may change if columns are added/removed. The implementation should use column names ("Spread", "NIT") rather than column letters.

2. **NT Text Detection**: The logic checks if NIT column "contains the text NT". This should be a case-insensitive substring check (e.g., "NT123" or "CLIENTENT" would both match).

3. **Spread Supra Column**: The output template has three spread columns (Spread PA, Spread FK, Spread Supra). This chore only mentions PA and FK. Spread Supra will remain empty/None unless future requirements specify its usage.

4. **First Row in Group Logic**: The current implementation only applies spread values to the first row in a payment group (`is_first_row_in_group`). Verify if this behavior should be preserved with the new direct mapping approach.

5. **México Support**: This chore appears to be Colombia-specific. México optional columns may need similar updates if the spread column exists in México input files.

6. **Cleanup**: After implementing the new logic, consider removing unused optional column mappings that were only used for the old spread calculation logic (e.g., `medio_pago`, `total_pagado_usd`, `short_code` if they're not used elsewhere).
