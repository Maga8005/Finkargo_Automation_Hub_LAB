# Chore: Recompra Spread Column Routing Fix

## Chore Description

When processing Colombia payments, the spread column routing logic needs to account for the `Recomprado` flag. Currently, the logic only checks if the NT column contains "NT" to determine whether spread goes to `Spread PA` or `Spread FK`:

**Current logic:**
- NT contains "NT" → Spread PA (Patrimonio Autónomo)
- NT does NOT contain "NT" → Spread FK (Fincargo Colombia)

**Required logic:**
- NT contains "NT" AND Recomprado is False → Spread PA (Patrimonio Autónomo)
- NT contains "NT" AND Recomprado is True → Spread FK (Fincargo Colombia)
- NT does NOT contain "NT" → Spread FK (Fincargo Colombia)

The business reasoning is that when an operation is "recomprada" (repurchased), Fincargo Colombia takes back ownership from Patrimonio Autónomo, so the spread should go to Fincargo's column (Spread FK) instead of Patrimonio's column (Spread PA).

This is consistent with the AR account selection logic which already correctly handles recomprada operations (using Fincargo Colombia AR accounts instead of Patrimonio Autónomo accounts).

## Relevant Files

Use these files to resolve the chore:

- `backend/src/core/servicios/payment_template_service.py` - Contains the spread column routing logic (lines 556-581) that needs to be updated to check the `is_recomprada` flag
- `backend/tests/test_payment_template_service.py` - Add/update tests for recomprada spread routing
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Reference for column definitions (no changes needed)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Read and understand current spread routing logic

- Read `backend/src/core/servicios/payment_template_service.py` lines 556-581
- Confirm the current logic only checks `is_nt_spread` but NOT `is_recomprada`
- Note that `is_recomprada` is already parsed earlier in the method (around line 437-442)

### 2. Update spread column routing logic

- Edit `backend/src/core/servicios/payment_template_service.py`
- Modify the spread routing logic (around line 562-571) to include `is_recomprada` check:

  **Before:**
  ```python
  if is_nt_spread:
      spread_pa = spread_value
  else:
      spread_fk = spread_value
  ```

  **After:**
  ```python
  # Spread goes to Spread PA only if NT column contains "NT" AND NOT recomprada
  # If recomprada=True, spread goes to Spread FK (Fincargo Colombia takes back ownership)
  if is_nt_spread and not is_recomprada:
      spread_pa = spread_value
      logger.debug(f"Spread value {spread_value} -> Spread PA (NT column contains NT, not recomprada)")
  else:
      spread_fk = spread_value
      if is_recomprada and is_nt_spread:
          logger.debug(f"Spread value {spread_value} -> Spread FK (recomprada overrides NT)")
      else:
          logger.debug(f"Spread value {spread_value} -> Spread FK (NT column does not contain NT)")
  ```

### 3. Update the logging section for spread calculation

- Also update the INFO level logging (around line 574-581) to include `is_recomprada` in the log message for clarity

### 4. Update unit tests

- Edit `backend/tests/test_payment_template_service.py`
- Add tests in `TestRecompraARAccountSelection` class (or create new class `TestRecompraSpreadRouting`):
  - `test_nt_not_recomprada_spread_goes_to_pa` - NT populated, recomprada=False → Spread PA
  - `test_nt_recomprada_spread_goes_to_fk` - NT populated, recomprada=True → Spread FK
  - `test_no_nt_spread_goes_to_fk` - NT empty → Spread FK (regardless of recomprada)

### 5. Run validation commands

- Execute all validation commands to ensure the fix works with zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

Test the specific scenario:
```bash
cd backend && source venv/bin/activate && python -c "
from src.core.servicios.payment_template_service import PaymentTemplateService
import pandas as pd
from unittest.mock import patch

service = PaymentTemplateService()

# Get column mappings
from src.core.servicios.catalogs.payment_catalogs import (
    get_required_columns,
    get_concept_columns,
    get_optional_columns,
)

required_columns = get_required_columns('colombia')
concept_columns = get_concept_columns('colombia')
optional_columns = get_optional_columns('colombia')

# Test case: NT populated, Recomprada = True -> should go to Spread FK
row_data = {
    'Cliente': 'Test Client',
    'Identificación del cliente': '123456789',
    'Código de desembolso': 'CO:123:1:1:PAG',
    'Código de recaudo': 'REC-001',
    'Fecha de pago': '2025-12-01',
    'Moneda': 'COP',
    'Capital': 5000000.00,
    'Banco remitente': 'Test Bank',
    'Médio de pago': 'Manual',
    'Tasa de cambio de FK/en línea': 4200.00,
    'Spread': 10,
    'Total pagado [USD]': 1000.00,
    'NT': 'NT-12345',  # NT populated
    'Recomprado': 'Si',  # Recomprada = True
    '4x1000': 0,
    'Fondo de garantías': 0,
    'IVA Fondo de garantías': 0,
    'Seguro + IVA': 0,
    'Intereses Corrientes': 0,
    'Cuenta Remitente': '60100001091',
}

row = pd.Series(row_data)
df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
    mock_trm.get_trm_for_date.return_value = 4150.25

    result = service._process_row(
        row=row,
        country='colombia',
        required_columns=required_columns,
        concept_columns=concept_columns,
        optional_columns=optional_columns,
        df_columns_normalized=df_columns_normalized,
        is_first_row_in_group=True
    )

capital_row = result[0]
print(f'Spread PA: {capital_row.get(\"Spread PA\")}')
print(f'Spread FK: {capital_row.get(\"Spread FK\")}')

# Expected: Spread PA = None, Spread FK = 10000 (or calculated value)
assert capital_row.get('Spread PA') is None, f'Expected Spread PA to be None, got {capital_row.get(\"Spread PA\")}'
assert capital_row.get('Spread FK') is not None, f'Expected Spread FK to have value, got None'
print('SUCCESS: Recomprada routes spread to FK column')
"
```

- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- This change is consistent with the existing AR account selection logic which already handles recomprada correctly
- The spread routing logic is at lines 556-581 in `payment_template_service.py`
- The `is_recomprada` variable is already parsed and available in the `_process_row` method (lines 437-442)
- Manual COP spread calculation (lines 583+) also uses the same spread routing logic and should be updated consistently
