# Chore: Adjust exchangerate column for Pago en línea with COP currency

## Chore Description
Adjust the `exchangerate` column logic in the payment template conversion service for Colombia. The business rule is:

**When "Medio de pago" is "Pago en línea" AND currency is COP:**
- Take the exchange rate from the "Tasa de cambio de FK/en línea" column
- Subtract the spread value from it
- Use the adjusted rate as the output exchangerate

**Otherwise (any other payment method or non-COP currency):**
- Keep the exchange rate unchanged (use the original value from the source file)

This adjustment is needed because online payments (Pago en línea) with COP currency require the spread to be deducted from the exchange rate for proper NetSuite reconciliation.

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/payment_template_service.py` - Main service file where `_process_row` method handles exchange rate extraction and processing. Lines 349-356 currently extract exchangerate without any adjustment. This is where the conditional logic needs to be added.

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains `COLOMBIA_OPTIONAL_COLUMNS` which already defines:
  - `"exchangerate": "Tasa de cambio de FK/en línea"` (line 131)
  - `"medio_pago": "Medio de pago"` (line 134)
  - `"spread": "Spread"` (line 133)
  These columns are already mapped and available for use.

- `backend/tests/test_payment_template_service.py` - Test file for the payment template service (if exists, otherwise create tests)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify column mappings exist
- Confirm that `COLOMBIA_OPTIONAL_COLUMNS` in `payment_catalogs.py` includes:
  - `medio_pago` mapped to `"Medio de pago"`
  - `spread` mapped to `"Spread"`
  - `exchangerate` mapped to `"Tasa de cambio de FK/en línea"`
- These should already exist based on current code review

### Step 2: Update `_process_row` method in `payment_template_service.py`
Modify the exchange rate processing logic in `_process_row` method (around lines 349-369):

- Extract the `medio_pago` value from optional columns using the existing `get_value` helper function
- After extracting `exchangerate` (lines 350-356), add conditional logic:
  ```python
  # Extract payment method for exchange rate adjustment
  medio_pago = get_value("medio_pago", optional_columns)

  # Adjust exchange rate for "Pago en línea" with COP currency
  # Business rule: When Medio de pago is "Pago en línea" and currency is COP,
  # subtract the spread from the exchange rate
  if (exchangerate is not None
      and spread_value is not None
      and medio_pago
      and "pago en línea" in medio_pago.lower()
      and currency.upper() == "COP"):
      exchangerate = exchangerate - spread_value
      logger.debug(
          f"Adjusted exchangerate for Pago en línea COP: "
          f"original={exchangerate + spread_value}, spread={spread_value}, adjusted={exchangerate}"
      )
  ```
- The `spread_value` is already extracted at lines 362-369
- The `currency` is already available from line 333
- Important: The spread subtraction should happen BEFORE the spread is used for other calculations

### Step 3: Ensure correct order of operations
The current code extracts values in this order:
1. `currency` (line 333)
2. `exchangerate` (lines 350-356)
3. `spread_value` (lines 362-369)

We need to adjust the order or move the exchangerate adjustment to after spread_value is extracted. The best approach is to:
- Keep the current extraction order
- Add the exchangerate adjustment logic right after `spread_value` is extracted (after line 369)
- This ensures all required values are available before the adjustment

### Step 4: Add logging for debugging
- Add debug logging when the adjustment is applied to help troubleshoot
- Log the original rate, spread value, and adjusted rate
- This follows the existing pattern of debug logging in the service (e.g., line 388)

### Step 5: Run validation commands
Execute all validation commands to ensure zero regressions:
- Run backend tests
- Run linting
- Run type checking

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- The `medio_pago` column is already defined in `COLOMBIA_OPTIONAL_COLUMNS` as `"Medio de pago"`, so no catalog changes are needed
- The comparison should be case-insensitive since the source file may have variations like "Pago en Línea", "pago en línea", etc.
- The spread value is already being extracted for spread calculations (Spread PA/FK), so we reuse that value
- This change only affects Colombia (`country.lower() == "colombia"`) since the business rule specifically mentions COP currency which is Colombian Peso
- For México (MXN currency), no adjustment is needed - the exchange rate passes through unchanged
- The adjustment should happen at the row level, not the output row level, since one source row can generate multiple output rows (one per concept)
