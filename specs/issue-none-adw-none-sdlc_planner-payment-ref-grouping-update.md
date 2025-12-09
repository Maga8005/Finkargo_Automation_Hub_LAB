# Chore: Update payment_ref Grouping Logic - Use Customer ID and Add Exchange Rate

## Chore Description
Adjust the payment_ref grouping logic for both Colombia and Mexico to:

1. **Replace "Código de desembolso" with "Identificación del cliente"** - The grouping key should use `customer_external_id` (Identificación del cliente) instead of `invoice_core_id` (Código de desembolso)

2. **Add "Tasa de cambio de FK/en línea" to the payment reference** - Include the exchange rate (`exchangerate`) as part of the composite grouping key

**Current grouping logic:**
- invoice_core_id (Código de desembolso)
- payment_date (Fecha de pago)
- currency (Moneda)
- cuenta_remitente (Cuenta Remitente) - optional

**New grouping logic:**
- customer_external_id (Identificación del cliente)
- payment_date (Fecha de pago)
- currency (Moneda)
- cuenta_remitente (Cuenta Remitente) - optional
- exchangerate (Tasa de cambio de FK/en línea)

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/payment_template_service.py` - Contains the `_generate_payment_ref()` method that needs to be updated to:
  - Accept `customer_external_id` instead of `invoice_core_id`
  - Accept `exchangerate` as a new parameter
  - Update the docstring to reflect the new grouping logic
  - Also needs updates in two calling locations:
    - `convert_to_netsuite_template()` (~lines 241-254) - Extract and pass the new parameters
    - `_process_row()` (~lines 378-386) - Extract and pass the new parameters

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Reference file for column mappings:
  - `customer_external_id` maps to "Identificación del cliente" (required column)
  - `exchangerate` maps to "Tasa de cambio de FK/en línea" (optional column)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_generate_payment_ref()` Method Signature
- In `backend/src/core/servicios/payment_template_service.py`, locate `_generate_payment_ref()` method (~line 632)
- Change parameter `invoice_core_id: str` to `customer_external_id: str`
- Add new parameter `exchangerate: Optional[float]` (or `Optional[str]`)
- Update the docstring to reflect the new grouping logic:
  - Replace "Código de desembolso (invoice_core_id)" with "Identificación del cliente (customer_external_id)"
  - Add "Tasa de cambio (exchangerate)" to the list

### Step 2: Update `_generate_payment_ref()` Method Body
- Update the components list to use `customer_external_id` instead of `invoice_core_id` (~line 665-669)
- Add `exchangerate` to the components list (format as string, handle None/empty)
- Update debug logging to reflect the new parameters (~line 680-684)

### Step 3: Update `convert_to_netsuite_template()` Caller
- In `convert_to_netsuite_template()` method (~lines 241-254):
- Change extraction from `invoice_core_id` to `customer_external_id`:
  ```python
  customer_external_id = get_row_value("customer_external_id", required_columns) or ""
  ```
- Add extraction of `exchangerate` from optional columns:
  ```python
  exchangerate_raw = get_row_value("exchangerate", optional_columns)
  ```
- Update the `_generate_payment_ref()` call to pass the new parameters:
  ```python
  payment_ref = self._generate_payment_ref(
      customer_external_id,
      payment_date_raw,
      currency,
      cuenta_remitente,
      exchangerate_raw
  )
  ```

### Step 4: Update `_process_row()` Caller
- In `_process_row()` method (~lines 378-386):
- The `customer_external_id` is already extracted at line 347
- The `exchangerate_raw` is already extracted at line 367
- Update the `_generate_payment_ref()` call to use `customer_external_id` instead of `invoice_core_id`:
  ```python
  payment_ref = self._generate_payment_ref(
      customer_external_id,
      payment_date_raw,
      currency,
      cuenta_remitente,
      exchangerate_raw
  )
  ```

### Step 5: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Verify backend Python import check passes
- Verify backend tests pass
- Verify frontend build passes

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && source venv/bin/activate && python -c "import src.core.servicios.payment_template_service; print('Import OK')"` - Verify Python syntax
- `cd backend && source venv/bin/activate && python -m pytest` - Run backend tests to validate with zero regressions
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- **Column Mappings (both countries):**
  - `customer_external_id` → "Identificación del cliente" (required column)
  - `exchangerate` → "Tasa de cambio de FK/en línea" (optional column)

- **Exchange Rate Handling:**
  - The exchange rate may be None/empty for some payments
  - When included in the grouping key, format as string to ensure consistent matching
  - Consider rounding to avoid floating-point precision issues (e.g., round to 4 decimal places)

- **New payment_ref format:**
  ```
  {customer_external_id}|{payment_date_YYYYMMDD}|{currency}|{cuenta_remitente}|{exchangerate}
  ```
  For online payments without cuenta_remitente:
  ```
  {customer_external_id}|{payment_date_YYYYMMDD}|{currency}|{exchangerate}
  ```

- **Business Impact:**
  - Payments will now be grouped by customer instead of disbursement code
  - Different exchange rates will create separate payment groups
  - This affects how spread and comision_banco values are assigned (first row of each group)
