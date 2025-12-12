# Bug: Manual COP Spread Not Aggregating Across Payment Group

## Bug Description
When calculating spread for Manual COP payments in Colombia, the system calculates spread using only the individual row's `Total pagado [USD]` instead of aggregating the USD amounts across all rows in the same payment group (payment_ref). This results in incorrect spread values when a payment group has multiple input rows.

**Symptoms:**
- First row in a payment group gets spread calculated only for its own `Total pagado [USD]`
- Second and subsequent rows in the same payment group get no spread assignment (correctly), but their USD amounts are not included in the first row's spread calculation
- Output shows partial spread instead of the full group-level spread

**Expected behavior:**
- For Manual COP payments, the spread formula `(Tasa Fincargo - TRM) × Total Pagado USD` should use the SUM of `Total pagado [USD]` across ALL rows in the payment group

**Actual behavior:**
- The formula only uses the first row's `Total pagado [USD]`, ignoring other rows in the group

## Problem Statement
The `_calculate_manual_cop_spread()` method is called with individual row's `total_pagado_usd` instead of the group-aggregated `total_pagado_usd` that is already collected in `payment_group_info`.

## Solution Statement
Use `group_info["total_pagado_usd"]` (the pre-calculated group total) instead of the individual row's `total_pagado_usd` when calling `_calculate_manual_cop_spread()`. This aligns the Manual COP spread calculation with the existing non-Manual spread calculation which already correctly uses `group_total_usd`.

## Steps to Reproduce
1. Upload test file: `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251211 CASOS RECOMPRAS.xlsx`
2. Convert to Colombia payment template
3. Check output row for CAPITAL INVESTMENTS (payment_ref `901055873|20251204|60100001091|3850.0000`)
4. **Input has 2 rows:** Row 0 with USD=246682.4675, Row 1 with USD=3317.5325 (total = 250000)
5. **Bug:** Output shows Spread FK = 17070426.75 (calculated only from row 0)
6. **Expected:** Spread FK should be calculated using combined USD = 250000

## Root Cause Analysis
In `payment_template_service.py` at lines 617-621, the manual COP spread calculation uses the individual row's `total_pagado_usd`:

```python
manual_spread = self._calculate_manual_cop_spread(
    tasa_fincargo=original_exchangerate,
    tasa_trm=tasa_trm,
    total_pagado_usd=total_pagado_usd  # BUG: Uses individual row's total
)
```

However, the `group_info["total_pagado_usd"]` already contains the aggregated sum across the payment group (calculated in `_collect_payment_group_info()`). This aggregated value is correctly used for non-Manual spread calculations (lines 691-694), but not for Manual COP spread.

Additionally, the Manual COP spread should only be calculated once per payment group (on the first row), similar to how non-Manual spread is handled.

## Affected Layer
- [x] Backend: core/servicios (business logic)

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/payment_template_service.py` - Contains the `_process_row()` method where manual COP spread is calculated (lines 617-621). The fix involves using `group_info["total_pagado_usd"]` instead of individual `total_pagado_usd`.
- `backend/tests/test_payment_template_service.py` - Add tests for manual COP spread group aggregation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Read and understand the current manual COP spread logic

- Read `backend/src/core/servicios/payment_template_service.py` lines 588-656 (Manual COP spread handling section)
- Confirm the bug: `total_pagado_usd` is the individual row's value, not the group aggregate
- Note that `group_info["total_pagado_usd"]` is available and contains the correct aggregate

### 2. Fix the manual COP spread calculation to use group total

- Edit `backend/src/core/servicios/payment_template_service.py`
- Around line 617-621, modify to use group total:

  **Before:**
  ```python
  manual_spread = self._calculate_manual_cop_spread(
      tasa_fincargo=original_exchangerate,
      tasa_trm=tasa_trm,
      total_pagado_usd=total_pagado_usd
  )
  ```

  **After:**
  ```python
  # Use group total USD for aggregated spread calculation
  group_total_usd_for_spread = group_info["total_pagado_usd"] if group_info else total_pagado_usd
  manual_spread = self._calculate_manual_cop_spread(
      tasa_fincargo=original_exchangerate,
      tasa_trm=tasa_trm,
      total_pagado_usd=group_total_usd_for_spread
  )
  ```

### 3. Update logging to show group total used

- Update the manual COP spread INFO log (around line 635-640) to include `group_total_usd_for_spread` for clarity:
  ```python
  logger.info(
      f"Manual COP spread calculated: customer={customer_external_id}, "
      f"tasa_fincargo={original_exchangerate}, tasa_trm={tasa_trm}, "
      f"row_total_usd={total_pagado_usd}, group_total_usd={group_total_usd_for_spread}, "
      f"is_nt={is_nt_spread}, is_recomprada={is_recomprada}, "
      f"spread_pa={spread_pa}, spread_fk={spread_fk}"
  )
  ```

### 4. Add unit tests for manual COP spread group aggregation

- Edit `backend/tests/test_payment_template_service.py`
- Add new test class `TestManualCOPSpreadGroupAggregation` with tests:
  - `test_manual_cop_spread_uses_group_total_usd` - Verify spread is calculated using aggregated group total
  - `test_manual_cop_spread_single_row_group` - Verify single-row groups work correctly
  - `test_manual_cop_spread_assigned_only_once_per_group` - Verify spread only assigned to first eligible row

### 5. Run validation commands

- Execute all validation commands to ensure the fix works with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

Test the specific scenario with the example file:
```bash
cd backend && source venv/bin/activate && python -c "
import pandas as pd
from src.core.servicios.payment_template_service import PaymentTemplateService

# Load the test file
input_df = pd.read_excel('/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251211 CASOS RECOMPRAS.xlsx')
print('Input rows for CAPITAL INVESTMENTS:')
cap_inv = input_df[input_df['Cliente'].str.contains('CAPITAL INVESTMENTS', na=False)]
print(cap_inv[['Cliente', 'Total pagado [USD]', 'Moneda', 'Tasa de cambio de FK/en línea']].to_string())
print(f'Total USD for group: {cap_inv[\"Total pagado [USD]\"].sum()}')
print()

# The service is async, so we need to use asyncio
import asyncio
import io

async def test():
    service = PaymentTemplateService()

    # Create a mock UploadFile
    class MockUploadFile:
        def __init__(self, df):
            self.buffer = io.BytesIO()
            df.to_excel(self.buffer, index=False)
            self.buffer.seek(0)
            self.filename = 'test.xlsx'

        async def read(self):
            return self.buffer.getvalue()

    upload = MockUploadFile(input_df)
    result = await service.convert_historial(upload, 'colombia')

    # Parse the output
    output_df = pd.read_excel(io.BytesIO(result.file_bytes))
    print('Output for 901055873 (CAPITAL INVESTMENTS):')
    cap_output = output_df[output_df['customer_external_id'] == 901055873]
    print(cap_output[['customer_external_id', 'concept_type', 'payment_amount', 'Spread FK', 'Spread PA']].to_string())

    # Verify: Spread should be calculated using group total (250000 USD)
    # If TRM is ~4437, then spread = (4437 - 3850) * 250000 = 146,750,000
    spread_fk = cap_output['Spread FK'].dropna().sum()
    print(f'\\nTotal Spread FK for group: {spread_fk}')
    print('Expected: ~146,750,000 (using group total 250000 USD)')

asyncio.run(test())
"
```

- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- The `group_info["total_pagado_usd"]` is already correctly calculated in `_collect_payment_group_info()` at lines 1400-1405
- This fix aligns Manual COP spread calculation with the existing non-Manual spread calculation which already uses `group_total_usd` (line 692)
- The `spread_already_assigned` check (line 750) already prevents duplicate spread assignment across rows in a group
- The formula for Manual COP spread is: `(Tasa Fincargo - TRM) × Total Pagado USD (GROUP)`
