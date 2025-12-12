# Bug: Colombia Spread Logic Creates Separate SPREAD Row for Multi-Currency Payment Groups

## Bug Description

When processing Colombia "Pago en línea" payments with multiple source rows that have the same exchange rate but different currencies (USD and COP), the system incorrectly treats them as separate payment groups. This causes:

1. A separate SPREAD row to be created for USD-only rows (when they only contain CAPITAL)
2. The COP row with non-CAPITAL concepts (e.g., MORATORIOS) gets spread in the column instead of receiving the full payment group spread

**Actual behavior:**
- Row with USD/CAPITAL creates a separate SPREAD line (27523.05 COP)
- Row with COP/MORATORIOS gets spread in "Spread PA" column (76.95)

**Expected behavior:**
- Since all rows belong to the same payment (same customer, date, exchange rate), they should be grouped together
- The group has concepts {CAPITAL, MORATORIOS}, so spread should go to the MORATORIOS row's Spread column
- No separate SPREAD line should be created
- The spread amount (27523.05 + 76.95 = ~27600) should appear in the Spread PA column of the MORATORIOS row

## Problem Statement

The `_generate_payment_ref()` method includes `currency` in the payment grouping key, causing rows with USD and COP currencies (but same exchange rate) to be treated as separate payment groups. This breaks the group-level logic that determines whether to create a separate SPREAD line vs adding spread to a column.

## Solution Statement

Modify the `_generate_payment_ref()` method to NOT include currency in the payment group key when the exchange rate is the same. Payments with the same customer, date, cuenta_remitente, and exchange rate belong to the same payment group regardless of the currency of individual line items.

Additionally, ensure the spread calculation accumulates spread from ALL rows in the payment group (not just the first row's spread value).

## Steps to Reproduce

1. Upload the source file: `Example FIles for Reqs/20251112 PRUEBA CARDIOFIT STORE SAS.xlsx`
2. The file contains 3 rows:
   - Row 0: USD, Capital=200, Spread=50, exchangerate=3934.46
   - Row 1: USD, Capital=550.46, Spread=50, exchangerate=3930.13
   - Row 2: COP, Moratorios=1.539, Spread=50, exchangerate=3930.13
3. Process through Colombia payment template conversion
4. Observe the output file `Aplicacion_Pagos_CO (26).xlsx`:
   - Row 3: SPREAD 27523.05 COP (incorrectly created as separate line)
   - Row 4: MORATORIOS 1.54 COP with Spread PA=76.95 (should have ~27600 instead)

## Root Cause Analysis

The bug originates in the `_generate_payment_ref()` method at line 940-1006 in `payment_template_service.py`:

```python
def _generate_payment_ref(
    self,
    customer_external_id: str,
    payment_date_raw: Optional[str],
    currency: str,  # <-- Currency is included in grouping
    cuenta_remitente: Optional[str],
    exchangerate: Optional[str] = None
) -> str:
    # ...
    components = [
        customer_external_id or "",
        date_key,
        currency.upper() if currency else "COP"  # <-- BUG: Currency differentiates groups
    ]
```

This causes:
- Row 1 (USD): payment_ref = `901260586|20251209|USD|0|3930.1331`
- Row 2 (COP): payment_ref = `901260586|20251209|COP|0|3930.1331`

These are treated as DIFFERENT payment groups, when they should be the SAME group.

The `_is_capital_only_pago_en_linea_for_group()` method then incorrectly determines that the USD group only has CAPITAL, triggering a separate SPREAD line.

**Secondary issue:** The spread amount calculation uses `total_pagado_usd * spread_value`, but this is calculated per-row rather than aggregating the spread across all rows in the true payment group.

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

- `backend/src/core/servicios/payment_template_service.py` - Contains the buggy `_generate_payment_ref()` method (line 940-1006), `_collect_payment_group_info()` (line 1305-1436), and `_process_row()` (line 371-802). The fix needs to:
  1. Remove currency from payment_ref generation (line 976-984)
  2. Ensure spread calculation aggregates correctly across multi-currency rows

- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains column mappings and optional columns definition. May need to verify no changes needed.

- `backend/tests/test_payment_template_service.py` - Add/update tests to cover multi-currency payment group scenarios.

### New Files

- `.claude/commands/e2e/test_co_spread_payment_group_level.md` - E2E test file to validate the fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand the Current Payment Grouping Logic

- Read `backend/src/core/servicios/payment_template_service.py` focusing on:
  - `_generate_payment_ref()` method (lines 940-1006)
  - `_collect_payment_group_info()` method (lines 1305-1436)
  - `_process_row()` method (lines 371-802)
- Verify the bug by tracing through how rows with same exchange rate but different currencies get different payment_refs

### 2. Modify `_generate_payment_ref()` to Remove Currency from Grouping Key

- Edit `backend/src/core/servicios/payment_template_service.py`
- In `_generate_payment_ref()` method (around line 976-984):
  - Remove `currency` from the `components` list that builds the payment_ref
  - The grouping should be based on: customer_external_id + date + cuenta_remitente + exchangerate
  - Currency should NOT differentiate payment groups when exchangerate is the same
- Update the docstring to reflect this change

### 3. Update `_collect_payment_group_info()` to Correctly Aggregate Multi-Currency Groups

- In `_collect_payment_group_info()` method, verify that:
  - Concepts from both USD and COP rows are correctly aggregated into the group's `concepts` set
  - `total_pagado_usd` correctly sums across all rows regardless of currency
- The method should already handle this correctly once payment_ref no longer includes currency

### 4. Verify Spread Calculation Logic in `_process_row()`

- In `_process_row()` method, verify that:
  - `should_create_separate_spread_line` uses group-level concepts (not row-level)
  - When group has mixed concepts (CAPITAL + non-CAPITAL), spread goes to column not separate line
  - The spread amount calculation uses the correct formula

### 5. Update Unit Tests

- Edit `backend/tests/test_payment_template_service.py`
- Add a test case for multi-currency payment groups:
  - Test input: 2+ rows with same exchange rate but different currencies (USD, COP)
  - Expected: All rows grouped together, no separate SPREAD line if non-CAPITAL concepts exist
  - Verify spread goes to the non-CAPITAL concept row's Spread column

### 6. Create E2E Test File

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/test_e2e.md` to understand E2E test format
- Create `.claude/commands/e2e/test_co_spread_payment_group_level.md` that:
  - Uploads the test file `Example FIles for Reqs/20251112 PRUEBA CARDIOFIT STORE SAS.xlsx`
  - Processes it through Colombia payment template conversion
  - Validates:
    - No separate SPREAD line for rows 1-2 (same exchange rate group)
    - MORATORIOS row has correct spread amount (~27600) in Spread PA column
    - Row 0 (different exchange rate) still correctly gets separate SPREAD line

### 7. Run Validation Commands

- Execute all validation commands to ensure the fix works and no regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

Before fix - verify bug exists:
```bash
# Process the test file and examine output
cd backend && source venv/bin/activate && python -c "
import asyncio
from src.core.servicios.payment_template_service import payment_template_service
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

async def test():
    # Read test file
    with open('../Example FIles for Reqs/20251112 PRUEBA CARDIOFIT STORE SAS.xlsx', 'rb') as f:
        content = f.read()

    # Create mock upload file
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value=content)

    # Convert
    output_bytes, stats = await payment_template_service.convert_to_netsuite_template(mock_file, 'colombia')

    # Read output
    import pandas as pd
    output_df = pd.read_excel(BytesIO(output_bytes))
    print('=== OUTPUT ===')
    print(output_df.to_string())
    print()
    print('=== CONCEPT TYPES ===')
    print(output_df['concept_type'].value_counts())
    print()
    print('=== SPREAD LINES ===')
    spread_rows = output_df[output_df['concept_type'] == 'SPREAD']
    print(f'Number of SPREAD rows: {len(spread_rows)}')
    print(spread_rows[['customer_external_id', 'payment_amount', 'payment_ref']].to_string())

asyncio.run(test())
"
```

After fix - verify bug is resolved:
```bash
# Same test - should show:
# - 1 SPREAD row (for exchange rate 3934.46 group) instead of 2
# - MORATORIOS row should have Spread PA ~27600
cd backend && source venv/bin/activate && python -c "
import asyncio
from src.core.servicios.payment_template_service import payment_template_service
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

async def test():
    with open('../Example FIles for Reqs/20251112 PRUEBA CARDIOFIT STORE SAS.xlsx', 'rb') as f:
        content = f.read()

    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value=content)

    output_bytes, stats = await payment_template_service.convert_to_netsuite_template(mock_file, 'colombia')

    import pandas as pd
    output_df = pd.read_excel(BytesIO(output_bytes))

    # Verify only 1 SPREAD row (for the 3934.46 exchange rate group which is CAPITAL-only)
    spread_rows = output_df[output_df['concept_type'] == 'SPREAD']
    assert len(spread_rows) == 1, f'Expected 1 SPREAD row, got {len(spread_rows)}'

    # Verify MORATORIOS row has spread in column (not separate line)
    moratorios_rows = output_df[output_df['concept_type'] == 'MORATORIOS']
    assert len(moratorios_rows) == 1, f'Expected 1 MORATORIOS row, got {len(moratorios_rows)}'

    mora_spread_pa = moratorios_rows['Spread PA'].iloc[0]
    # Expected: (550.461 + 1.539) * 50 = 27600 (approximately)
    assert mora_spread_pa is not None and mora_spread_pa > 27000, f'Expected Spread PA ~27600, got {mora_spread_pa}'

    print('SUCCESS: Bug is fixed!')
    print(f'- SPREAD rows: {len(spread_rows)} (expected 1)')
    print(f'- MORATORIOS Spread PA: {mora_spread_pa} (expected ~27600)')
    print()
    print('=== FULL OUTPUT ===')
    print(output_df.to_string())

asyncio.run(test())
"
```

Standard validation:
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

E2E validation:
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_co_spread_payment_group_level.md` test file to validate this functionality works

## Notes

1. **Business Context**: The payment grouping is critical for NetSuite integration. Payments must be grouped correctly so that:
   - Spread amounts are applied to the correct AR accounts
   - The payment reference allows NetSuite to match payments correctly

2. **Edge Cases to Consider**:
   - Different exchange rates should still create separate groups (Row 0 with 3934.46 vs Rows 1-2 with 3930.13)
   - Manual payments (non-Pago en línea) have different spread calculation logic - ensure this is not affected
   - México payments don't have the same spread column logic - ensure no regression

3. **Testing Data**: The test file `Example FIles for Reqs/20251112 PRUEBA CARDIOFIT STORE SAS.xlsx` contains the exact scenario to validate the fix.

4. **Calculation Verification**:
   - Row 1: Capital=550.461 USD, Spread=50
   - Row 2: Moratorios=1.539 USD equivalent, Spread=50
   - Group total USD = 550.461 + 1.539 = 552.0
   - Expected spread = 552.0 * 50 = 27600 COP (should go to Spread PA column on MORATORIOS row)
