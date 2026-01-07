# Chore: Apply payment_ref Grouping Logic to Mexico Aplicación de Pagos

## Chore Description
Apply the same payment_ref grouping logic (based on invoice_core_id + payment_date + currency + cuenta_remitente) to the Mexico Aplicación de Pagos output template, matching the logic already implemented for Colombia.

**Finding:** After analyzing the codebase, the grouping logic is **already implemented** for both Colombia and Mexico. The `convert_to_netsuite_template()` and `_process_row()` methods are country-agnostic and use the `_generate_payment_ref()` helper for both countries.

However, there is one minor issue to fix:
- The default currency fallback is hardcoded to "COP" (Colombia Peso) instead of being country-aware
- For Mexico, the default should be "MXN" (Mexican Peso)

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/payment_template_service.py` - Contains the payment template conversion logic. The `_generate_payment_ref()` helper is already called for both Colombia and Mexico. Need to fix default currency fallback to be country-aware.
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains `MEXICO_OPTIONAL_COLUMNS` which already includes `cuenta_remitente` for bank account lookup.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Verify Current Implementation Works for Mexico
- Confirm that `MEXICO_OPTIONAL_COLUMNS` includes `cuenta_remitente` - **VERIFIED: Yes, it does**
- Confirm that `convert_to_netsuite_template()` uses `_generate_payment_ref()` for all countries - **VERIFIED: Yes, it does**
- Confirm that `_process_row()` uses `_generate_payment_ref()` for all countries - **VERIFIED: Yes, it does**

### Step 2: Fix Default Currency Fallback
- In `backend/src/core/servicios/payment_template_service.py`, update the default currency fallback to be country-aware
- Line ~244 in `convert_to_netsuite_template()`: Change `currency = get_row_value("currency", required_columns) or "COP"` to use country-specific default
- Line ~349 in `_process_row()`: Change `currency = get_value("currency", required_columns) or "COP"` to use country-specific default
- Line ~668 in `_generate_payment_ref()`: Update the fallback `currency.upper() if currency else "COP"` to accept a country parameter or use a passed default

**Proposed solution:** Pass the country to both places and use:
```python
default_currency = "MXN" if country.lower() == "mexico" else "COP"
currency = get_value("currency", required_columns) or default_currency
```

### Step 3: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Verify backend tests pass
- Verify Python syntax is correct
- Verify frontend build passes (no frontend changes expected)

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && source venv/bin/activate && python -c "import src.core.servicios.payment_template_service; print('Import OK')"` - Verify Python syntax
- `cd backend && source venv/bin/activate && python -m pytest` - Run backend tests to validate with zero regressions
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- **Key Finding:** The payment_ref grouping logic is already implemented for Mexico. The `_generate_payment_ref()` method is country-agnostic and is called in both `convert_to_netsuite_template()` and `_process_row()` for all countries.
- The only fix needed is updating the default currency fallback from hardcoded "COP" to country-aware logic ("MXN" for Mexico, "COP" for Colombia).
- This is a minor fix since the currency column should always be present in the source Excel files. The fallback only applies when the currency value is empty/missing.
- Mexico uses MXN (Mexican Peso) as their local currency, while Colombia uses COP (Colombian Peso).
