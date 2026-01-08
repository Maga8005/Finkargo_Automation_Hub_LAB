# Chore: Fix Exchange Rate Column Mapping

## Chore Description
The exchange rate field (`exchangerate`) is returning blank in the generated Excel file (`Aplicacion_Pagos_Co`). The value should be populated from the `Tasa de cambio de FK/en línea` column in the uploaded Historial de Pagos file.

The issue is a mismatch between the expected column name in the code and the actual column name in the uploaded files:
- **Current mapping**: `"Tasa de cambio FK/en línea"` (missing "de")
- **Actual column name**: `"Tasa de cambio de FK/en línea"` (with "de")

This mismatch causes the column lookup to fail, resulting in `None` values for the exchange rate.

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains the column mappings for Colombia and México. Line 109 defines the `exchangerate` mapping that needs to be corrected. This is where the fix needs to be applied.

- `backend/src/core/servicios/payment_template_service.py` - Contains the `PaymentTemplateService` that processes the Excel files. Lines 349-356 extract the exchange rate using the `get_value` helper function with the column mapping from `optional_columns`. This code is correct and doesn't need changes.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Colombia Exchange Rate Column Mapping

In `backend/src/core/servicios/catalogs/payment_catalogs.py`:

- Change line 109 from:
  ```python
  "exchangerate": "Tasa de cambio FK/en línea",
  ```
  To:
  ```python
  "exchangerate": "Tasa de cambio de FK/en línea",
  ```

Note: Adding the word "de" between "cambio" and "FK" to match the actual column name in the uploaded files.

### Step 2: Update México Exchange Rate Column Mapping (if applicable)

In `backend/src/core/servicios/catalogs/payment_catalogs.py`:

- Check line 157 for the México optional columns
- If the same column name is used for México, update it from:
  ```python
  "exchangerate": "Tasa de cambio FK/en línea",
  ```
  To:
  ```python
  "exchangerate": "Tasa de cambio de FK/en línea",
  ```

### Step 3: Run Validation Commands

Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- The column name mismatch is a simple typo: "cambio FK" vs "cambio de FK"
- The column lookup in `payment_template_service.py` normalizes column names to lowercase and strips whitespace, but it cannot handle mismatched column names
- Both Colombia and México optional columns should be checked and updated if they have the same issue
- No changes are needed to the `payment_template_service.py` file - the logic there is correct, it's just receiving the wrong column name to search for
