# Chore: Change Spread Calculation to Use Total Pagado (USD)

## Chore Description
Modify the spread calculation in the Tesorería payment template conversion to multiply the `<Spread>` value by `<Total Pagado (USD)>` from the upload file instead of the current behavior which multiplies by the first concept's payment amount.

**Current Behavior:**
- Spread is calculated as: `Spread Value × First Concept Payment Amount`
- Example: If spread = 0.05 and first concept (Capital) = 1,000,000 COP, result = 50,000

**New Behavior:**
- Spread should be calculated as: `Spread Value × Total Pagado (USD)`
- Example: If spread = 0.05 and Total Pagado (USD) = 10,000 USD, result = 500

**Row Assignment Rule (Unchanged):**
- The spread calculation should only appear on the **first output row** generated from each source row
- Whatever concept happens to be first (Capital, Intereses, Costos Fijos, Moratorios, etc.) gets the spread value
- All subsequent concept rows from the same source row receive `None` for spread columns

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/payment_template_service.py`** (lines 358-418)
  - Contains the `_process_row` method where spread calculation occurs
  - Line 363: Extracts spread value from input
  - Lines 416-417: Current multiplication logic (`spread_pa * amount`, `spread_fk * amount`)
  - Need to extract `total_pagado_usd` and use it instead of `amount`

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (lines 108-117, 157-164)
  - Already defines `"total_pagado_usd": "Total pagado USD"` in both `COLOMBIA_OPTIONAL_COLUMNS` (line 113) and `MEXICO_OPTIONAL_COLUMNS` (line 160)
  - No changes needed to this file

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Extract Total Pagado (USD) Value in `_process_row`
In `backend/src/core/servicios/payment_template_service.py`, add extraction of `total_pagado_usd` value after the spread extraction (around line 369):

- Add after line 369 (after spread_value extraction):
  ```python
  # Extract Total Pagado (USD) for spread calculation
  total_pagado_usd_raw = get_value("total_pagado_usd", optional_columns)
  total_pagado_usd = None
  if total_pagado_usd_raw:
      try:
          total_pagado_usd = float(total_pagado_usd_raw)
      except (ValueError, TypeError):
          pass
  ```

### Step 2: Update Spread Calculation to Use Total Pagado (USD)
In `backend/src/core/servicios/payment_template_service.py`, modify lines 416-417 to use `total_pagado_usd` instead of `amount`:

- Change from:
  ```python
  row_spread_pa = round(spread_pa * amount, 2) if idx == 0 and spread_pa is not None else None
  row_spread_fk = round(spread_fk * amount, 2) if idx == 0 and spread_fk is not None else None
  ```

- Change to:
  ```python
  row_spread_pa = round(spread_pa * total_pagado_usd, 2) if idx == 0 and spread_pa is not None and total_pagado_usd is not None else None
  row_spread_fk = round(spread_fk * total_pagado_usd, 2) if idx == 0 and spread_fk is not None and total_pagado_usd is not None else None
  ```

### Step 3: Update Comment to Reflect New Logic
In `backend/src/core/servicios/payment_template_service.py`, update the comment on line 415:

- Change from:
  ```python
  # Multiply spread by payment amount for the first row
  ```

- Change to:
  ```python
  # Multiply spread by Total Pagado (USD) for the first row only
  ```

### Step 4: Add Debug Logging for New Calculation
Add debug logging to help troubleshoot spread calculations:

- Add after the spread routing logic (after line 396):
  ```python
  if spread_value is not None and total_pagado_usd is not None:
      logger.debug(f"Spread calculation: {spread_value} × {total_pagado_usd} USD")
  ```

### Step 5: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Column Mapping Already Exists
The column mapping for `total_pagado_usd` is already defined in both Colombia and México optional columns:
- Colombia: `"total_pagado_usd": "Total pagado USD"` (line 113 in payment_catalogs.py)
- México: `"total_pagado_usd": "Total pagado USD"` (line 160 in payment_catalogs.py)

No changes to column mappings are required.

### Edge Cases to Consider
1. **Missing Total Pagado (USD)**: If the input file doesn't have this column or the value is empty/null, the spread columns will be `None` (no spread calculated). This is handled by the `and total_pagado_usd is not None` condition.

2. **First Row Assignment**: The `idx == 0` check ensures spread only appears on the first concept row, regardless of which concept type comes first. This behavior is unchanged.

3. **NT Routing**: The routing logic (Spread PA vs Spread FK based on NT column) remains unchanged.

### Example Calculation
**Input Row:**
- Spread: 0.02
- Total Pagado (USD): 15,000
- NT Column: empty (so use Spread FK)
- Concepts generated: CAPITAL, INTERESES, COSTOS_FIJOS

**Output:**
| Concept | Spread PA | Spread FK | Spread Supra |
|---------|-----------|-----------|--------------|
| CAPITAL | None | 300.00 | None |
| INTERESES | None | None | None |
| COSTOS_FIJOS | None | None | None |

Calculation: `0.02 × 15,000 = 300.00` appears only on first row (CAPITAL in this example)
