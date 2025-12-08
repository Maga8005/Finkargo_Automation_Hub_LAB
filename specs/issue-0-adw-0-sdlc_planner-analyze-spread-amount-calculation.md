# Chore: Analyze How Spread Amount is Determined in Resulting Excel File

## Chore Description
This chore is a **code analysis task** to document and understand how the spread amount is being calculated and populated in the resulting Excel file from the Tesorería "Aplicación de Pagos" payment template conversion feature.

The analysis should detail:
1. Where the spread value comes from in the input file
2. How the spread routing decision is made (Spread PA vs Spread FK vs Spread Supra)
3. How the final spread amount is calculated for the output
4. Which rows receive spread values and which don't

## Relevant Files
Use these files to analyze the spread calculation logic:

- **`backend/src/core/servicios/payment_template_service.py`** - The core business logic service that performs the conversion. Lines 358-436 contain the spread calculation and assignment logic within the `_process_row` method.

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** - Contains the column mappings including optional columns that define where spread and NT flag values come from in the input file (lines 108-117 for Colombia, lines 157-164 for México).

- **`backend/src/interface/tesoreria_dtos.py`** - Contains the DTOs including `OutputTemplateRow` (lines 168-205) which documents the spread fields: `spread_pa`, `spread_fk`, and `spread_supra`.

## Step by Step Tasks

### Step 1: Document Input Source for Spread Value
Analyze how the spread value is extracted from the input file:

- The input "Spread" value comes from the optional column defined in `COLOMBIA_OPTIONAL_COLUMNS` as `"spread": "Spread"` (line 111 in payment_catalogs.py)
- In `_process_row` (lines 362-369 in payment_template_service.py), the spread value is extracted:
  ```python
  spread_value_raw = get_value("spread", optional_columns)
  spread_value = float(spread_value_raw) if spread_value_raw else None
  ```

### Step 2: Document NT Flag Extraction for Spread Routing
Analyze how the NT flag determines spread routing:

- The NT flag value comes from `"nt_flag": "NT"` column (line 110 in payment_catalogs.py)
- In `_process_row` (lines 371-372), the NT flag is extracted:
  ```python
  nt_value_for_spread = get_value("nt_flag", optional_columns)
  ```

### Step 3: Document Spread Routing Logic (PA vs FK vs Supra)
Analyze the decision logic for which spread column receives the value:

- Lines 381-396 in payment_template_service.py implement the routing:
  ```python
  if spread_value is not None:
      is_nt_spread = nt_value_for_spread and "NT" in str(nt_value_for_spread).upper()
      if is_nt_spread:
          spread_pa = spread_value  # NT operations -> Spread PA
      else:
          spread_fk = spread_value  # Non-NT operations -> Spread FK
  ```
- **Key Finding**: `Spread Supra` is always `None` (line 385) - it's kept for compatibility but never populated

### Step 4: Document Final Spread Amount Calculation
Analyze how the spread is multiplied by the payment amount:

- Lines 413-418 show the final calculation applied to the **first concept row only**:
  ```python
  row_spread_pa = round(spread_pa * amount, 2) if idx == 0 and spread_pa is not None else None
  row_spread_fk = round(spread_fk * amount, 2) if idx == 0 and spread_fk is not None else None
  row_spread_supra = spread_supra if idx == 0 else None
  ```
- **Key Finding**: The spread value from input is **multiplied by the payment_amount** of the first concept

### Step 5: Document Which Rows Receive Spread Values
Analyze the row-level assignment logic:

- Lines 217-242 track payment groups using `payment_groups_seen` set
- `is_first_row_in_group` is determined by whether the `payment_ref` has been seen before
- The `is_first_row_in_group` flag is passed to `_process_row` but **NOT used for spread** (only for `comision_banco`)
- Instead, **idx == 0** check (line 407) ensures only the **first concept output row** from each input row gets spread values
- **Key Finding**: Spread is assigned to the first **concept** (e.g., CAPITAL), not necessarily tied to payment_ref grouping

### Step 6: Create Summary Documentation
Document the complete spread calculation flow:

| Step | Source | Logic | Destination |
|------|--------|-------|-------------|
| 1. Extract | Input column "Spread" | `get_value("spread", optional_columns)` | `spread_value` (float) |
| 2. Extract NT | Input column "NT" | `get_value("nt_flag", optional_columns)` | `nt_value_for_spread` (str) |
| 3. Route | Check if "NT" in `nt_value_for_spread` | If True → `spread_pa`, else → `spread_fk` | Either `spread_pa` or `spread_fk` |
| 4. Calculate | `spread * payment_amount` | Only for `idx == 0` (first concept) | `row_spread_pa` or `row_spread_fk` |
| 5. Output | Write to Excel | Columns "Spread PA", "Spread FK", "Spread Supra" | First concept row only |

## Validation Commands
Execute every command to validate the analysis is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Current Spread Calculation Summary

**Input Required:**
- Column "Spread" (optional, typically column AX in source file)
- Column "NT" (optional, used for routing decision)

**Routing Decision:**
- If "NT" column contains the text "NT" (case-insensitive) → **Spread PA** is populated
- If "NT" column is empty or doesn't contain "NT" → **Spread FK** is populated
- **Spread Supra** is **never populated** (hardcoded to `None`)

**Calculation Formula:**
```
Final Spread Amount = Input Spread Value × First Concept Payment Amount
```

**Assignment Rule:**
- Only the **first concept row** (idx == 0) in each source row receives the spread value
- All subsequent concept rows from the same source row receive `None` for all spread columns

### Potential Areas for Improvement (Out of Scope for This Analysis)
1. The `Spread Supra` column is never used - consider removing or implementing
2. The spread is multiplied by the first concept amount, which may not be the intended behavior
3. Payment group tracking (`is_first_row_in_group`) exists but is not used for spread assignment
4. Consider whether spread should be distributed across concepts or tied to payment_ref grouping
