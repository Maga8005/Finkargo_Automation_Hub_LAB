# Chore: Multiply Spread Value by Payment Amount

## Chore Description
Currently, the spread value from the input file (column "Spread") is directly copied to the output file's "Spread PA" or "Spread FK" column. The requirement is to multiply the spread value by the corresponding payment amount instead of just showing the raw spread value.

**Current behavior:** `Spread PA/FK = spread_value` (raw value from input)
**Expected behavior:** `Spread PA/FK = spread_value × payment_amount`

Since the spread is only applied to the first output row for each payment group (idx == 0), the spread should be multiplied by that row's payment amount.

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/payment_template_service.py` - Contains the `_process_row` method where spread values are calculated and assigned. The spread calculation happens around lines 387-396, and the spread is assigned to output rows around lines 415-417. The multiplication needs to happen when assigning the spread to the first output row.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update spread calculation in payment_template_service.py

- Open `backend/src/core/servicios/payment_template_service.py`
- Locate the section where spread values are assigned to output rows (around lines 413-417)
- Currently the code assigns:
  ```python
  row_spread_pa = spread_pa if idx == 0 else None
  row_spread_fk = spread_fk if idx == 0 else None
  ```
- Change the logic to multiply by the payment amount when idx == 0:
  ```python
  # Multiply spread by payment amount for the first row
  row_spread_pa = round(spread_pa * amount, 2) if idx == 0 and spread_pa is not None else None
  row_spread_fk = round(spread_fk * amount, 2) if idx == 0 and spread_fk is not None else None
  ```
- Update the debug log messages to reflect the calculation (optional but recommended)

### Step 2: Run Validation Commands

Execute every command to validate the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. The spread value from the input file appears to be a rate/percentage, so multiplying by the payment amount converts it to an absolute value.

2. The `amount` variable in the loop represents the `payment_amount` for each concept type row. Since spread is only applied to the first row (idx == 0), we multiply by that specific row's amount.

3. Using `round(..., 2)` ensures the calculated spread value has consistent decimal precision matching other monetary values in the output.

4. The `spread_supra` column remains None as per existing logic and doesn't need multiplication.
