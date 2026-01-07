# Chore: Complete Treasury Account Field Mapping for Colombia

## Chore Description
In the treasury module, the Colombia functionality is not generating a value for the `account` field in the output Excel file (`Aplicacion_Pagos_Co`). All rows show blank values for this field.

The `account` field should be populated from the upload file using the `Cuenta Remitente` column, mapped to internal NetSuite account IDs according to this mapping:

| CTA (Source - Cuenta Remitente) | ID Interno (Destination - account) |
|--------------------------------|-----------------------------------|
| 60100001091 | 230 |
| 60100005374 | 2346 |
| 42861435 | 231 |
| 60100004638 | 1439 |
| 2600000313 | 2439 |
| 1250001972 | 232 |
| 36449096 | 235 |
| 3644-6725 | 236 |
| 709396827 | 2441 |
| 3304261649 | 1493 |
| 5089889016 | 239 |
| 3304296965 | 1492 |
| 9562345678749720 | 2418 |
| 8482979559 | 2498 |

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains all payment-related catalogs and mappings for Colombia and México. This is where the new account number to internal ID mapping dictionary should be added, along with a lookup function.

- `backend/src/core/servicios/payment_template_service.py` - Contains the `PaymentTemplateService` class that converts Historial de Pagos files to NetSuite templates. The `_process_row` method (line 290-452) currently sets `account` to `None` (line 443). This needs to be updated to use the new account lookup function.

- `backend/src/interface/tesoreria_dtos.py` - Contains DTOs for the treasury module. May need review to ensure the `account` field type is appropriate.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Colombia Bank Account Mapping to Catalogs

In `backend/src/core/servicios/catalogs/payment_catalogs.py`:

- Add a new dictionary `COLOMBIA_BANK_ACCOUNT_MAPPING` that maps bank account numbers (strings) to their NetSuite internal IDs (integers)
- Include all 14 mappings from the provided table
- Account numbers should be stored as strings to handle variations (e.g., "3644-6725" with hyphen)
- Add a helper function `get_bank_account_id(cuenta_remitente: str, country: str) -> Optional[int]` that:
  - Normalizes the input by stripping whitespace
  - Looks up the account in the mapping dictionary
  - Returns the internal ID or None if not found
  - Only applies to Colombia (returns None for other countries for now)

### Step 2: Update Payment Template Service to Use Account Mapping

In `backend/src/core/servicios/payment_template_service.py`:

- Import the new `get_bank_account_id` function from `payment_catalogs`
- In the `_process_row` method, add logic to:
  - Extract the `cuenta_remitente` value using the existing `get_value` helper function
  - Call `get_bank_account_id(cuenta_remitente, country)` to get the internal account ID
  - Pass this value to the output row instead of `None` for the `account` field

### Step 3: Update Output Row Generation

In the `_process_row` method around line 435-450:

- Before generating output rows, get the account ID:
  ```python
  cuenta_remitente = get_value("cuenta_remitente", optional_columns)
  account_id = get_bank_account_id(cuenta_remitente, country) if cuenta_remitente else None
  ```
- Update the output row dictionary to use `account_id` instead of `None`:
  ```python
  "account": account_id,
  ```

### Step 4: Run Validation Commands

Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- The `cuenta_remitente` column is already defined in `COLOMBIA_OPTIONAL_COLUMNS` as `"Cuenta Remitente"`, so the column mapping infrastructure is already in place.
- The account numbers in the mapping should be stored as strings because some may contain non-numeric characters (e.g., "3644-6725" with a hyphen).
- When looking up account numbers, consider normalizing by removing common variations (whitespace, leading zeros if applicable).
- This mapping is specific to Colombia. México may need its own mapping in the future, but for now the function should gracefully return None for non-Colombia countries.
- The `account` field in the output corresponds to column H in the NetSuite template (position 8 in `OUTPUT_TEMPLATE_COLUMNS`).
