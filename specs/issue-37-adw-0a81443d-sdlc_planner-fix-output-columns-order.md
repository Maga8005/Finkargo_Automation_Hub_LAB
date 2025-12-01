# Bug: Tesorería - Output File Missing Columns and Incorrect Column Order

## Bug Description

The Tesorería "Plantillas para Cargar NetSuite" feature for both Colombia and México is generating output files with three critical issues:

1. **Missing columns**: 5 required columns are not present in the output (`account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`)
2. **Incorrect column order**: The 10 existing columns are not in the correct order as specified in the template definition
3. **Extra column**: There's a `memo` column that shouldn't be in the output

**Current Output (WRONG)**: 10 columns
```
payment_date, customer_external_id, payment_ref, invoice_core_id, concept_type,
payment_amount, currency, exchangerate, araccount, memo
```

**Expected Output (CORRECT)**: 14 columns
```
customer_external_id, invoice_core_id, concept_type, payment_date, payment_amount,
currency, payment_ref, account, araccount, exchangerate, comision_banco,
Spread PA, Spread FK, Spread Supra
```

## Problem Statement

The `OUTPUT_TEMPLATE_COLUMNS` constant in `payment_catalogs.py` defines only 10 columns in the wrong order, and the `_process_row()` method in `payment_template_service.py` doesn't generate values for the 5 missing columns. This causes the output Excel files to have incorrect structure and missing data required by NetSuite.

## Solution Statement

Update the output template column definition to include all 14 required columns in the correct order, and modify the `_process_row()` method to calculate and populate the 5 missing columns:
- `account`: Lookup bank account internal ID from catalog (placeholder/empty for now)
- `comision_banco`: Extract from "Referencia bancaria" for México (first line per payment group only)
- `Spread PA`: Calculate for manual payments: (Exchange rate - BanRep rate) × Total paid USD
- `Spread FK`: Calculate for online payments: Total paid × Spread Finkargo rate
- `Spread Supra`: Calculate for Supra payments: Total paid × Spread Finkargo rate

## Steps to Reproduce

1. Navigate to Tesorería → Plantillas para Cargar NetSuite → Colombia (or México)
2. Upload a valid "Historial de Pagos" Excel file
3. Click "Convertir" button
4. Download the generated Excel file
5. Open the file and examine columns
6. **Observe**:
   - Only 10 columns exist instead of 14
   - Column order doesn't match template specification
   - `memo` column exists but shouldn't
   - Missing: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`

## Root Cause Analysis

The root cause is in two locations:

1. **`backend/src/core/servicios/catalogs/payment_catalogs.py:157-168`**: The `OUTPUT_TEMPLATE_COLUMNS` list only defines 10 columns and includes `memo` which shouldn't be there. It's missing the 5 required columns.

2. **`backend/src/core/servicios/payment_template_service.py:341-352`**: The `_process_row()` method only creates output dictionaries with the 10 existing columns. It doesn't:
   - Look up `account` from bank catalogs
   - Extract `comision_banco` from "Referencia bancaria" (México only)
   - Calculate the three Spread columns based on payment method and exchange rates
   - Ensure only ONE row per payment group gets the spread and commission values

## Affected Layer

- [x] Backend: core/servicios (business logic)
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files

Use these files to fix the bug:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (Lines 157-168)
  - Contains the `OUTPUT_TEMPLATE_COLUMNS` constant that defines the output column order
  - MUST be updated to include all 14 columns in the correct order
  - Remove `memo` column, add `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`

- **`backend/src/core/servicios/payment_template_service.py`** (Lines 266-354)
  - The `_process_row()` method generates output row dictionaries
  - Currently only populates 10 fields
  - MUST be enhanced to:
    - Add `account` field (placeholder/empty for now - bank catalog lookup to be implemented later)
    - Add `comision_banco` field (extract from source for México, empty for Colombia)
    - Add `Spread PA`, `Spread FK`, `Spread Supra` fields (calculated based on payment method)
  - Lines 180-264: The `convert_to_netsuite_template()` method orchestrates the conversion
    - May need enhancement to track payment groups for proper spread/commission distribution
  - Lines 341-352: Output dictionary construction needs all 14 fields

- **`backend/src/core/servicios/payment_template_service.py`** (Line 242)
  - The DataFrame construction uses `OUTPUT_TEMPLATE_COLUMNS` to define column order
  - Once the constant is updated, this will automatically use the correct column order

- **`backend/src/interface/tesoreria_dtos.py`** (Lines 167-194)
  - The `OutputTemplateRow` Pydantic model defines the output schema
  - Currently only has 10 fields
  - MUST be updated to include the 5 missing fields for type safety

- **Reference file**: `Example FIles for Reqs/FIN_ Definicion Template para Aplicación de pagos.xlsx`
  - Sheet: "Hoja 1", Row 1 (index 0) - Colombia column definitions
  - Sheet: "Hoja 1", Row 2 (index 1) - México descriptions
  - This file contains the authoritative column order and business rules

### New Files

No new files need to be created - all changes are modifications to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Update OUTPUT_TEMPLATE_COLUMNS constant with correct column order

- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Locate the `OUTPUT_TEMPLATE_COLUMNS` list (lines 157-168)
- Replace the entire list with the correct 14 columns in the correct order:
  ```python
  OUTPUT_TEMPLATE_COLUMNS = [
      "customer_external_id",
      "invoice_core_id",
      "concept_type",
      "payment_date",
      "payment_amount",
      "currency",
      "payment_ref",
      "account",
      "araccount",
      "exchangerate",
      "comision_banco",
      "Spread PA",
      "Spread FK",
      "Spread Supra",
  ]
  ```
- Remove the `memo` column
- Add the 5 missing columns: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`
- Ensure the order matches the template specification exactly

### 2. Update OutputTemplateRow DTO to include missing fields

- Open `backend/src/interface/tesoreria_dtos.py`
- Locate the `OutputTemplateRow` Pydantic model (lines 167-194)
- Add the 5 missing fields with appropriate types and descriptions:
  - `account: Optional[str]` - Bank account internal ID (will be None for now)
  - `comision_banco: Optional[float]` - Bank commission (México only, first line per payment)
  - `spread_pa: Optional[float]` - PA Spread calculation (manual payments only)
  - `spread_fk: Optional[float]` - FK Spread calculation (online payments)
  - `spread_supra: Optional[float]` - Supra Spread calculation (Supra payments)
- Remove the `memo` field as it's not part of the specification
- Update the docstring to reflect the new fields and correct column count (14 columns)

### 3. Extract additional source column mappings for spread calculations

- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Add new entries to `COLOMBIA_OPTIONAL_COLUMNS` and create `MEXICO_OPTIONAL_COLUMNS`:
  - `medio_pago`: "Medio de pago" (payment method: Manual, Pago en línea, etc.)
  - `total_pagado_usd`: "Total pagado USD" (for spread calculations)
  - `referencia_bancaria`: "Referencia bancaria" (for comision_banco extraction)
  - `short_code`: "Short Code" or equivalent column to identify SUPRA vs PA
  - `cuenta_remitente`: "Cuenta Remitente" (for account lookup - future implementation)
- These will be used to extract values needed for the missing columns

### 4. Enhance _process_row() to populate the 5 missing columns

- Open `backend/src/core/servicios/payment_template_service.py`
- Locate the `_process_row()` method (lines 266-354)
- Add logic to extract the new source columns using the mappings from step 3:
  - Extract `medio_pago` (payment method)
  - Extract `total_pagado_usd`
  - Extract `referencia_bancaria` (México only)
  - Extract `short_code` or payment provider identifier
- Update the output row dictionary construction (lines 341-352) to include:
  - `"account": None` (placeholder for now - bank catalog lookup to be implemented later)
  - `"comision_banco": comision_value` (extract from referencia_bancaria for México, None for Colombia)
  - `"Spread PA": spread_pa_value` (calculated for manual payments)
  - `"Spread FK": spread_fk_value` (calculated for FK online payments)
  - `"Spread Supra": spread_supra_value` (calculated for Supra payments)
- Remove the `"memo": None` field

### 5. Implement comision_banco extraction logic for México

- In the `_process_row()` method, add logic to extract bank commission for México:
  - Check if `country == "mexico"`
  - If yes, extract value from "Referencia bancaria" column
  - Parse the numeric value (handle various formats: "$1,234.56", "1234.56", etc.)
  - Only populate this on the FIRST row of each payment group (same `payment_ref`)
  - For Colombia, always set to `None`
- Note: Determining "first row of payment group" requires tracking state across rows in `convert_to_netsuite_template()`

### 6. Implement spread calculation logic based on payment method

- In the `_process_row()` method, add spread calculation logic:
  - Extract `medio_pago` (payment method)
  - Extract `total_pagado_usd` (total paid in USD)
  - Extract `exchangerate` (already exists)
  - **For manual payments** (`medio_pago == "Manual"`):
    - Calculate `Spread PA = (exchangerate - tasa_banrep) * total_pagado_usd`
    - Note: `tasa_banrep` would need to come from NetSuite API or separate lookup (use placeholder 0 for now)
    - Set `Spread FK` and `Spread Supra` to `None`
  - **For online payments** (SUPRA or PA):
    - If provider is "SUPRA": Calculate `Spread Supra = total_pagado_usd * spread_rate`
    - If provider is "PA": Calculate `Spread FK = total_pagado_usd * spread_rate`
    - Note: `spread_rate` would need to come from configuration (use placeholder 0 for now)
    - Set the other spread columns to `None`
  - Only ONE row per payment group should have spread values (same `payment_ref`)
  - All values should be in local currency (COP or MXN)

### 7. Add payment grouping logic to convert_to_netsuite_template()

- In `convert_to_netsuite_template()` method (lines 180-264)
- Add tracking for payment groups (keyed by `payment_ref`) to ensure:
  - Only the FIRST row of each payment group gets `comision_banco` value
  - Only ONE row of each payment group gets spread values
- Modify the row processing loop to pass payment group context to `_process_row()`
- Options:
  - Track seen `payment_ref` values in a set
  - Pass a flag to `_process_row()` indicating if it's the first row of the group
  - Or handle post-processing after all rows are generated

### 8. Add helper method for parsing comision_banco from referencia_bancaria

- Create a new private method `_parse_comision_banco()` in `PaymentTemplateService`
- Input: raw string value from "Referencia bancaria" column
- Logic:
  - Handle various numeric formats: "$1,234.56", "1234.56", "1.234,56" (European format)
  - Extract numeric value using regex
  - Return float or None if parsing fails
- Use this method in the `comision_banco` extraction logic

### 9. Update column reordering in DataFrame construction

- Verify that line 242 in `payment_template_service.py` correctly uses `OUTPUT_TEMPLATE_COLUMNS`
- The current code: `output_df = pd.DataFrame(output_rows, columns=OUTPUT_TEMPLATE_COLUMNS)`
- This should automatically enforce the correct column order once the constant is updated
- Ensure the order matches exactly: `customer_external_id`, `invoice_core_id`, `concept_type`, `payment_date`, `payment_amount`, `currency`, `payment_ref`, `account`, `araccount`, `exchangerate`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`

### 10. Add logging for new column generation

- Add debug logging in `_process_row()` to track:
  - When `comision_banco` is extracted and its value
  - When spread calculations are performed and their values
  - When payment grouping logic determines first row vs subsequent rows
- This will help with debugging and validation

### 11. Run validation commands to verify bug fix

- Execute all commands in the "Validation Commands" section below
- Verify zero regressions in existing tests
- Confirm correct column count and order in output files

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

- **Manual Test**: Upload a test "Historial de Pagos" file for Colombia and México through the UI, download the output, and verify:
  - Output has exactly 14 columns
  - Columns are in the exact order specified
  - `memo` column is removed
  - New columns exist: `account`, `comision_banco`, `Spread PA`, `Spread FK`, `Spread Supra`
  - Values are populated where applicable (can be empty/None where business rules dictate)

- `cd backend && python -m pytest tests/` - Run all backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import OUTPUT_TEMPLATE_COLUMNS; print(f'Column count: {len(OUTPUT_TEMPLATE_COLUMNS)}'); print('Columns:', OUTPUT_TEMPLATE_COLUMNS); assert len(OUTPUT_TEMPLATE_COLUMNS) == 14, 'Should have 14 columns'; assert 'memo' not in OUTPUT_TEMPLATE_COLUMNS, 'Should not have memo'; assert 'account' in OUTPUT_TEMPLATE_COLUMNS, 'Should have account'"` - Verify OUTPUT_TEMPLATE_COLUMNS is correct
- `cd frontend && npm run lint` - Run frontend linting (no changes expected, but verify no breakage)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

### Future Enhancements (Out of Scope for This Bug Fix)

The following are mentioned in the bug report but should be implemented as separate features:

1. **Bank account lookup**: The `account` column should lookup the internal ID from "Catalogo CO" or "Catalogo MX" based on bank name/account number. For this bug fix, we'll leave it as `None` and implement the lookup in a separate task.

2. **BanRep exchange rate lookup**: The Spread PA calculation requires the "Tasa BanRep" (Banco de la República exchange rate) which is stored in NetSuite. For this bug fix, we'll use a placeholder value of 0, and implement the NetSuite integration separately.

3. **Spread rate configuration**: The Spread FK and Spread Supra calculations require the "Spread Finkargo rate" which may come from configuration or NetSuite. For this bug fix, we'll use placeholder values, and implement proper rate lookup separately.

4. **Payment provider identification**: Determining whether a payment is "SUPRA" vs "PA" requires parsing the payment method or a Short Code column. We'll need to verify the exact column name and logic with business users.

### Technical Debt

- Consider extracting spread calculation logic into a separate service class for better testability
- Consider creating a `PaymentGroup` class to encapsulate payment grouping logic
- Add comprehensive unit tests for the new calculation methods

### Business Rules to Clarify

- Confirm the exact column name for payment provider identification (SUPRA vs PA vs Manual)
- Confirm the exact column name for "Total pagado USD"
- Confirm the spread rate values or where to fetch them from
- Confirm bank catalog structure for the `account` lookup implementation
