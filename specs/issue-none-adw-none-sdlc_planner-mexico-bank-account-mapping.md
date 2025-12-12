# Chore: Add Mexico Bank Account Mapping for Payment Export

## Chore Description
Add bank account mappings for Mexico in the payment export functionality. The `account` field in the output template needs to be populated based on the `Cuenta Remitente` source field. Currently, Mexico bank account mapping is not implemented (there's a comment "México mapping not yet implemented" in the code).

The mappings to add are:
| NetSuite Account ID | Cuenta Remitente |
|---------------------|------------------|
| 2322 | 0123270165 |
| 2320 | 0123375153 |
| 2111 | 0118970882 |
| 2110 | 669555222 |

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (lines 48-69, 306-328) - Contains the Colombia bank account mapping dictionary (`COLOMBIA_BANK_ACCOUNT_MAPPING`) and the `get_bank_account_id()` helper function. This is where we need to:
  1. Add a new `MEXICO_BANK_ACCOUNT_MAPPING` dictionary following the same pattern as Colombia
  2. Update the `get_bank_account_id()` function to look up Mexico mappings

- **`backend/src/core/servicios/payment_template_service.py`** (line 417) - Uses `get_bank_account_id()` to populate the `account` field. No changes needed here as it already passes the country parameter.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Add Mexico Bank Account Mapping Dictionary
- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- After the `MEXICO_AR_ACCOUNTS` dictionary (around line 88), add a new section for Mexico bank account mappings
- Create `MEXICO_BANK_ACCOUNT_MAPPING: Dict[str, int]` with the following mappings:
  ```python
  # =============================================================================
  # MÉXICO BANK ACCOUNT MAPPINGS (Cuenta Remitente -> NetSuite Internal ID)
  # =============================================================================

  # Maps bank account numbers (Cuenta Remitente) to NetSuite internal account IDs
  # Used to populate the 'account' field in the output template for México
  MEXICO_BANK_ACCOUNT_MAPPING: Dict[str, int] = {
      "0123270165": 2322,
      "0123375153": 2320,
      "0118970882": 2111,
      "669555222": 2110,
  }
  ```

### Task 2: Update get_bank_account_id Function to Support Mexico
- In the same file, locate the `get_bank_account_id()` function (around line 306)
- Replace the comment "# México mapping not yet implemented" with actual México lookup logic:
  ```python
  elif country_lower == "mexico":
      # Normalize the account number by stripping whitespace
      normalized = str(cuenta_remitente).strip()
      return MEXICO_BANK_ACCOUNT_MAPPING.get(normalized)
  ```

### Task 3: Run Validation Commands
Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id, MEXICO_BANK_ACCOUNT_MAPPING; print('Mexico mappings:', MEXICO_BANK_ACCOUNT_MAPPING); print('Test 0123270165:', get_bank_account_id('0123270165', 'mexico')); print('Test 669555222:', get_bank_account_id('669555222', 'mexico'))"` - Verify Mexico bank account mappings work correctly
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Colombia still works:', get_bank_account_id('60100001091', 'colombia'))"` - Verify Colombia mappings still work (regression test)
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- The mapping is from `Cuenta Remitente` (bank account number from source file) → NetSuite Internal Account ID
- The dictionary key is the bank account number (string), and the value is the NetSuite ID (integer)
- Account numbers should be stored as strings to preserve leading zeros (e.g., "0123270165")
- The existing Colombia implementation normalizes the account number by stripping whitespace - Mexico should follow the same pattern
- No frontend changes are required as the `account` field is already included in the output template
