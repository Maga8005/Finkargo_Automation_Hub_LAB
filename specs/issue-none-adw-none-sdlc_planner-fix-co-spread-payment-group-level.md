# Feature: Fix Colombia Spread Calculation - Use Aggregated Total Pagado USD at Payment Group Level

## Feature Description
Fix the spread calculation in the Colombia payment template conversion to use the **aggregated `Total Pagado [USD]`** across all rows in a payment group, instead of the row-level value. Currently, each row calculates spread using only its own `Total Pagado [USD]` value, which causes incorrect spread amounts when a single payment spans multiple rows.

**This spec extends the existing group-level decision logic** (already implemented via `_collect_payment_group_info()`) to also use the aggregated USD total for spread amount calculation.

## User Story
As a Treasury (Tesorería) department user processing Colombia payments
I want the spread calculation to use the SUM of `Total Pagado [USD]` across ALL rows in the payment group
So that the spread amount reflects the total payment value, not individual row values

## Problem Statement
**Current (INCORRECT) Behavior:**
Each row calculates spread independently using its own `Total Pagado [USD]`:
```
Payment Group "ABC|20241204|COP|60100001091|4350.5000":
  Row 1: Total Pagado USD = 50, CAPITAL = 200
  Row 2: Total Pagado USD = 500, INTERESES = 150, COSTOS_FIJOS = 50

  Current (WRONG):
  - Spread for Row 1 = spread_rate × 50 (only Row 1's USD)
  - Spread for Row 2 = spread_rate × 500 (only Row 2's USD)
  - Result: Spread calculated separately per row!

  Expected (CORRECT):
  - Aggregated Total Pagado USD = 550 (50 + 500)
  - Spread = spread_rate × 550 (calculated ONCE using aggregated total)
  - Applied to ONE row (first non-CAPITAL concept row in INTERESES row)
```

**Root Cause:**
The `_collect_payment_group_info()` method already aggregates `total_pagado_usd` at the group level (lines 1249-1254), but the `_process_row()` method still uses the row-level `total_pagado_usd` variable (extracted at lines 492-498) for spread calculation (lines 624-626).

## Solution Statement
The fix requires modifying `_process_row()` to use `group_info["total_pagado_usd"]` (the aggregated total) instead of the row-level `total_pagado_usd` for spread calculation:

1. **Use aggregated total for spread columns** (lines 624-626):
   - Change: `spread_rate × total_pagado_usd` → `spread_rate × group_info["total_pagado_usd"]`

2. **Use aggregated total for separate SPREAD line** (lines 570-575):
   - Change: `spread_value × total_pagado_usd` → `spread_value × group_info["total_pagado_usd"]`

3. **Track spread assignment** to ensure spread is only calculated/assigned ONCE per payment group:
   - Add check: if `group_info["spread_assigned"]` is True, skip spread assignment
   - After assigning spread, set `group_info["spread_assigned"] = True`

**Note:** The `_collect_payment_group_info()` method already aggregates `total_pagado_usd` and tracks `spread_assigned` (initialized to False at line 1244). We just need to use these values in `_process_row()`.

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Existing RBAC via `require_roles(['tesoreria', 'admin'])` on tesoreria routes
- Frontend Protection: Existing route protection on `/tesoreria/*` routes

## Relevant Files
Use these files to implement the feature:

- **`backend/src/core/servicios/payment_template_service.py`**: Main service file where the fix must be implemented. Contains:
  - `convert_to_netsuite_template()` - needs pre-processing phase
  - `_process_row()` - needs to receive and use group context
  - `_is_capital_only_pago_en_linea()` - needs to be renamed/updated for group-level evaluation
  - `_get_spread_target_index()` - may need updates for group-level spread placement

- **`backend/tests/test_payment_template_service.py`**: Existing unit tests that need new test cases for payment group-level scenarios. Must add tests for:
  - Multi-row payment groups with mixed concepts
  - Single-row payment groups (existing behavior)
  - Spread placement across multiple rows

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`**: Reference for understanding column mappings and concept columns.

- **`.claude/commands/test_e2e.md`** and **`.claude/commands/e2e/test_login.md`**: Reference for E2E test format.

### New Files
- **`.claude/commands/e2e/test_co_spread_payment_group_level.md`**: E2E test to validate the payment group-level spread logic works correctly

## Pre-Implementation Verification

### Feature Category
- [x] Excel Processing (treasury, finance) → Complete sections B, D

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (Colombia Historial de Pagos):**
| Column Name (exact) | Required | Data Type | Notes |
|--------------------|----------|-----------|-------|
| Identificación del cliente | Yes | String | Customer NIT |
| Código de desembolso | Yes | String | Invoice/loan code |
| Fecha de pago | Yes | Date | Payment date |
| Moneda | Yes | String | COP/USD |
| Capital | No | Float | Capital amount |
| 4x1000 | No | Float | Tax component |
| Fondo de garantías | No | Float | Cost component |
| IVA Fondo de garantías | No | Float | Cost component |
| Intereses Corrientes | No | Float | Interest |
| Médio de pago | No | String | "Pago en línea" / "Manual" |
| Spread | No | Float | Spread rate |
| Total pagado [USD] | No | Float | USD amount for spread calculation |
| NT | No | String | NT flag for spread routing |
| Tasa de cambio de FK/en línea | No | Float | Exchange rate |
| Cuenta Remitente | No | String | Bank account (for grouping) |

**Output Template Structure:**
| Column Name | Source/Calculation | Notes |
|-------------|-------------------|-------|
| customer_external_id | Identificación del cliente | Direct copy |
| invoice_core_id | Código de desembolso | Direct copy |
| concept_type | Derived from concept columns | CAPITAL, INTERESES, COSTOS_FIJOS, SPREAD |
| payment_date | Fecha de pago | Formatted to dd/mm/yyyy |
| payment_amount | Concept value | Rounded to 2 decimals |
| currency | Moneda | COP/USD |
| payment_ref | Generated | Customer + Date + Currency + Account + Rate |
| account | Bank account ID | From catalog |
| araccount | AR account | From catalog based on concept |
| exchangerate | Tasa de cambio | May be adjusted or cleared |
| Spread PA | spread * total_pagado_usd | If NT column contains "NT" |
| Spread FK | spread * total_pagado_usd | If NT column does NOT contain "NT" |

**Catalog Dependencies:**
- [x] AR account mappings documented (via `get_ar_account()` in payment_catalogs.py)
- [x] Country-specific variations identified (Colombia vs México)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A | N/A | N/A | No repository changes needed |

**Note**: This is a pure service-layer logic fix. No repository or database changes required.

### Interface Mapping (Frontend ↔ Backend)
No frontend changes required - this is a backend business logic fix. The API contract remains unchanged.

## Implementation Plan

### Phase 1: Analysis (Already Complete)
The infrastructure for group-level processing already exists:
- `_collect_payment_group_info()` method (lines 1161-1293) already:
  - Aggregates `total_pagado_usd` across rows in the same payment group
  - Tracks `spread_assigned` flag (initialized to False)
  - Collects all concepts in the group
- `_process_row()` already receives `group_info` parameter (added in previous implementation)

### Phase 2: Core Fix - Use Aggregated Total
Modify `_process_row()` to use `group_info["total_pagado_usd"]` instead of row-level value:
1. Replace row-level `total_pagado_usd` with group-level value in spread column calculation
2. Replace row-level `total_pagado_usd` with group-level value in separate SPREAD line calculation
3. Check and update `spread_assigned` flag to prevent duplicate spread assignment

### Phase 3: Testing
- Add unit tests for multi-row payment groups with different `Total Pagado [USD]` values
- Verify spread is calculated ONCE using aggregated total
- Verify spread is assigned to only ONE row per group

## Step by Step Tasks

### Step 1: Add Unit Tests for Aggregated Total Pagado USD
Create new test cases in `backend/tests/test_payment_template_service.py`:
- `test_spread_uses_aggregated_total_pagado_usd_from_group`: Two-row payment group with different `Total Pagado [USD]` values (e.g., 50 and 500), verify spread = rate × 550 (not rate × 50 or rate × 500)
- `test_spread_assigned_only_once_per_group`: Multi-row group, verify spread appears on ONLY ONE output row
- `test_spread_assignment_tracking_prevents_duplicates`: Verify `group_info["spread_assigned"]` flag works correctly

### Step 2: Create E2E Test File
Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for format reference, then create/update `.claude/commands/e2e/test_co_spread_payment_group_level.md` with:
- Test case verifying spread amount uses aggregated `Total Pagado [USD]`
- Verification that spread appears on only one row per payment group

### Step 3: Modify `_process_row()` - Use Aggregated Total for Spread Columns
Update lines 624-626 in `payment_template_service.py`:
```python
# BEFORE:
row_spread_pa = round(spread_pa * total_pagado_usd, 2) if is_spread_target and spread_pa is not None and total_pagado_usd is not None else None
row_spread_fk = round(spread_fk * total_pagado_usd, 2) if is_spread_target and spread_fk is not None and total_pagado_usd is not None else None

# AFTER: Use group-level aggregated total
group_total_usd = group_info["total_pagado_usd"] if group_info else total_pagado_usd
row_spread_pa = round(spread_pa * group_total_usd, 2) if is_spread_target and spread_pa is not None and group_total_usd else None
row_spread_fk = round(spread_fk * group_total_usd, 2) if is_spread_target and spread_fk is not None and group_total_usd else None
```

### Step 4: Modify `_process_row()` - Use Aggregated Total for Separate SPREAD Line
Update lines 570-575 in `payment_template_service.py`:
```python
# BEFORE:
separate_spread_amount = None
if should_create_separate_spread_line and spread_value is not None and total_pagado_usd is not None:
    separate_spread_amount = spread_value * total_pagado_usd

# AFTER: Use group-level aggregated total
separate_spread_amount = None
group_total_usd_for_spread = group_info["total_pagado_usd"] if group_info else total_pagado_usd
if should_create_separate_spread_line and spread_value is not None and group_total_usd_for_spread:
    separate_spread_amount = spread_value * group_total_usd_for_spread
```

### Step 5: Add Spread Assignment Tracking
Add tracking to ensure spread is assigned only ONCE per payment group:
```python
# Before assigning spread to any row, check if already assigned
should_assign_spread = True
if group_info and group_info.get("spread_assigned"):
    should_assign_spread = False
    row_spread_pa = None
    row_spread_fk = None

# After assigning spread, mark as assigned
if (row_spread_pa is not None or row_spread_fk is not None) and group_info:
    group_info["spread_assigned"] = True
```

### Step 6: Update Logging for Spread Calculation
Add INFO-level logging to track the aggregated total being used:
```python
logger.info(
    f"Spread calculation using GROUP total: customer={customer_external_id}, "
    f"payment_ref='{payment_ref}', row_total_usd={total_pagado_usd}, "
    f"group_total_usd={group_total_usd}, spread_rate={spread_value}"
)
```

### Step 7: Run Unit Tests
Execute `cd backend && python -m pytest tests/test_payment_template_service.py -v` to verify all tests pass.

### Step 8: Run Full Validation
Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests - NEW for Aggregated Total
- **`test_spread_uses_aggregated_total_pagado_usd`**: Two-row group with Row 1 `Total Pagado [USD]=50`, Row 2 `Total Pagado [USD]=500`, spread_rate=10 → spread amount should be `10 × 550 = 5500`, NOT `10 × 50` or `10 × 500`
- **`test_spread_assigned_only_once_per_group`**: Multi-row group where both rows have non-CAPITAL concepts → spread should appear on ONLY the first non-CAPITAL row
- **`test_spread_assignment_flag_tracking`**: Verify `group_info["spread_assigned"]` is set to True after spread assignment

### Unit Tests - Existing (from previous implementation)
- **`test_group_with_capital_and_intereses_no_separate_spread`**: Two-row group, Row 1 CAPITAL, Row 2 INTERESES, Pago en línea → spread goes to INTERESES row columns
- **`test_group_with_all_capital_rows_creates_separate_spread`**: Two-row group, both CAPITAL-only, Pago en línea → creates separate SPREAD line
- **`test_single_row_capital_only_creates_separate_spread`**: Single row with CAPITAL-only, Pago en línea → creates separate SPREAD line (existing)
- **`test_group_with_capital_and_costos_fijos_no_separate_spread`**: Two-row group with mixed concepts → no separate SPREAD line
- **`test_manual_payment_group_never_creates_separate_spread`**: Manual payment regardless of concepts → spread in columns
- **`test_spread_placement_on_cop_non_capital_row`**: Verify spread goes to correct row in group

### Edge Cases
1. **Single-row group** - aggregated total equals row total (no change in behavior)
2. **Multi-row group with one row missing Total Pagado [USD]** - should still aggregate available values
3. **All rows have zero Total Pagado [USD]** - spread should be 0 or None
4. **Multi-row group where first row has no non-CAPITAL concepts** - spread goes to second row but uses aggregated total
5. **Group with only CAPITAL-only rows (Pago en línea)** - separate SPREAD line uses aggregated total

## Acceptance Criteria
1. **Aggregated Total**: Spread amount is calculated using the SUM of `Total Pagado [USD]` across ALL rows in the same payment group
2. **Single Assignment**: Spread is assigned to only ONE output row per payment group (the first non-CAPITAL concept row for column spread, or as a single SPREAD line for capital-only Pago en línea)
3. **Tracking Works**: The `group_info["spread_assigned"]` flag prevents duplicate spread assignment to subsequent rows
4. **Backward Compatible**: Single-row payment groups work identically to before (aggregated total = row total)
5. **Existing Behavior Preserved**: Payment groups where ALL rows have only CAPITAL and Pago en línea → separate SPREAD line using aggregated total
6. **Existing Behavior Preserved**: Payment groups with mixed concepts → spread goes to columns on first non-CAPITAL row using aggregated total
7. **México Unchanged**: México payments are unaffected (feature is Colombia-only)
8. **All Tests Pass**: All existing unit tests continue to pass, new tests for aggregation pass

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run payment template service tests
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting (no changes expected)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check (no changes expected)
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_co_spread_payment_group_level.md` to validate this functionality works E2E

## Notes

### Key Code Locations
1. **Group info collection (already aggregates total_pagado_usd):**
   - `payment_template_service.py` lines 1249-1254:
   ```python
   total_pagado_usd_raw = get_value(row, "total_pagado_usd", optional_columns)
   if total_pagado_usd_raw:
       try:
           payment_group_info[payment_ref]["total_pagado_usd"] += float(total_pagado_usd_raw)
       except (ValueError, TypeError):
           pass
   ```

2. **Spread column calculation (NEEDS FIX):**
   - `payment_template_service.py` lines 624-626:
   ```python
   row_spread_pa = round(spread_pa * total_pagado_usd, 2) if is_spread_target and spread_pa is not None and total_pagado_usd is not None else None
   row_spread_fk = round(spread_fk * total_pagado_usd, 2) if is_spread_target and spread_fk is not None and total_pagado_usd is not None else None
   ```
   **FIX**: Change `total_pagado_usd` to `group_info["total_pagado_usd"]`

3. **Separate SPREAD line calculation (NEEDS FIX):**
   - `payment_template_service.py` lines 570-575:
   ```python
   separate_spread_amount = None
   if should_create_separate_spread_line and spread_value is not None and total_pagado_usd is not None:
       separate_spread_amount = spread_value * total_pagado_usd
   ```
   **FIX**: Change `total_pagado_usd` to `group_info["total_pagado_usd"]`

### Implementation Notes
- **No database changes required** - this is a pure business logic fix in the service layer
- **No API contract changes** - input/output formats remain the same
- **No frontend changes required** - the backend fix is transparent to the frontend
- **Backward compatible** - single-row payment groups will work the same as before (aggregated total = row total)
- The `_collect_payment_group_info()` method already handles the aggregation; we just need to USE the aggregated value
- The `spread_assigned` flag is already initialized to False in `_collect_payment_group_info()` (line 1244) but is not being used - this fix will use it to prevent duplicate spread assignment

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section (E2E test file)
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (Step 2)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented
- [x] Data transformation rules specified (spread = rate × aggregated_total)
- [x] Catalog/lookup dependencies identified

### Consistency (ALL features)
- [x] Data types match between frontend and backend (no changes)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods (group_info["key"])
- [x] Country-specific variations handled (Colombia only - México unchanged)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
- [x] Specific line numbers identified for code changes (lines 570-575, 624-626)
