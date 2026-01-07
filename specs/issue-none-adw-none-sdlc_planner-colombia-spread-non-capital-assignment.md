# Feature: Colombia Payment Conversion - Spread Assignment to Non-Capital Concepts

## Feature Description
Modify the Colombia Historial de Pagos to Aplicación de Pagos conversion so that when a source row has multiple concepts (CAPITAL plus other concepts like COSTOS_FIJOS, INTERESES, etc.), the spread values (Spread FK/Spread PA) are assigned to the first non-CAPITAL concept line rather than to the CAPITAL line. Currently, spread is assigned to the first output row regardless of concept type (which is often CAPITAL). This change ensures spread values are properly associated with revenue-generating concepts rather than principal repayment.

## User Story
As a Tesorería department user
I want spread values to be assigned to non-CAPITAL concept lines when multiple concepts exist
So that NetSuite correctly associates spread revenue with the appropriate concept type for accurate financial reporting

## Problem Statement
Currently, when processing a Colombia payment with multiple concepts (e.g., CAPITAL + COSTOS_FIJOS + INTERESES), the spread value is assigned to the first output row, which is typically CAPITAL due to dictionary ordering. This is incorrect because:
1. Spread represents revenue from the payment processing, not principal repayment
2. NetSuite reporting requires spread to be associated with fee/interest concepts, not capital
3. The current behavior can cause reconciliation issues in financial reporting

## Solution Statement
Modify the `_process_row` method in `PaymentTemplateService` to:
1. When multiple concepts exist (not capital-only), find the first non-CAPITAL concept row to assign spread values
2. Keep the existing behavior for capital-only scenarios (separate SPREAD line for Pago en Línea)
3. Ensure spread is never assigned to CAPITAL rows when other concepts exist
4. The logic should identify which output row index corresponds to a non-CAPITAL concept and assign spread there

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Uses existing `require_roles(['tesoreria'])` dependency
- Frontend Protection: Existing route protection - no changes needed

## Relevant Files
Use these files to implement the feature:

- `backend/src/core/servicios/payment_template_service.py` - Main service containing `_process_row` method. The loop that generates output rows currently uses `idx == 0` to determine spread assignment. This needs to change to assign spread to first non-CAPITAL concept.
- `backend/tests/test_payment_template_service.py` - Existing unit tests for the service. Need to add/update tests for the new spread assignment logic.
- `.claude/commands/test_e2e.md` - E2E test runner instructions.
- `.claude/commands/e2e/test_colombia_spread_separate_line.md` - Existing E2E test for spread separate line that may need updates.

### New Files
- `.claude/commands/e2e/test_colombia_spread_non_capital.md` - E2E test file to validate spread is assigned to non-CAPITAL concepts

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (existing - no changes):**
| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| Capital | Yes | Numeric | >= 0 |
| 4x1000 | No | Numeric | Cost column |
| Fondo de garantías | No | Numeric | Cost column |
| Intereses Corrientes | No | Numeric | Interest column |
| Spread | No | Numeric | Spread rate value |
| Total pagado [USD] | No | Numeric | Total in USD |
| NT | No | String | "NT" for Operaciones Cedidas |

**Output Excel Structure (existing - logic change only):**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| concept_type | Derived | "CAPITAL", "COSTOS_FIJOS", "INTERESES", etc. |
| Spread PA | Spread × Total USD | **Assigned to first non-CAPITAL row** (changed) |
| Spread FK | Spread × Total USD | **Assigned to first non-CAPITAL row** (changed) |

**Data Transformation Rules (updated):**
- When multiple concepts exist: Spread goes to first non-CAPITAL concept row
- When only CAPITAL exists (Pago en Línea): Separate SPREAD row created (existing behavior)
- When only CAPITAL exists (Manual): Spread goes to CAPITAL row (no other option)

**Catalog Dependencies:**
- [x] AR account mappings documented (existing, no changes)
- [x] Country-specific variations identified (Colombia only, México unchanged)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A - No repository changes | N/A | N/A | Service-only logic change |

### Interface Mapping (Frontend ↔ Backend)

No interface changes required - this is purely a backend business logic change in how output rows are generated.

## Implementation Plan

### Phase 1: Foundation
- No database or interface changes needed
- Update existing unit tests to reflect new expected behavior

### Phase 2: Core Implementation
- Modify `_process_row` method to:
  1. First pass: identify which concept types exist and their order
  2. Determine the index of the first non-CAPITAL concept
  3. Assign spread values to that index instead of always index 0
- Add helper method `_get_spread_target_index()` for clean logic

### Phase 3: Integration
- No routing or navigation changes needed
- Update E2E tests to validate new behavior
- Ensure existing tests pass with updated expectations

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for test format
- Create `.claude/commands/e2e/test_colombia_spread_non_capital.md`
- Define test steps that:
  1. Login as tesoreria user
  2. Navigate to Colombia payment converter
  3. Upload a test Excel file with CAPITAL + other concepts
  4. Download the converted file
  5. Verify spread is on a non-CAPITAL row
  6. Verify CAPITAL row has no spread values

### Step 2: Add Helper Method to Determine Spread Target Index
- Edit `backend/src/core/servicios/payment_template_service.py`
- Add a new private method `_get_spread_target_index()`:
  ```python
  def _get_spread_target_index(
      self,
      processed_concepts: Dict[str, float],
      country: str
  ) -> int:
      """
      Determine which output row index should receive spread values.

      For Colombia:
      - If multiple concepts exist, return index of first non-CAPITAL concept
      - If only CAPITAL exists, return 0 (will be handled separately)

      Args:
          processed_concepts: Dictionary of concept_type -> amount
          country: Country code

      Returns:
          Index of the row that should receive spread values
      """
      if country.lower() != "colombia":
          return 0  # México uses standard behavior

      # Get list of non-zero concepts in order
      non_zero_concepts = [k for k, v in processed_concepts.items() if abs(v) > 0.001]

      # Find first non-CAPITAL concept
      for idx, concept in enumerate(non_zero_concepts):
          if concept != "CAPITAL":
              return idx

      # If only CAPITAL exists, return 0
      return 0
  ```

### Step 3: Modify _process_row to Use New Spread Assignment Logic
- Continue editing `backend/src/core/servicios/payment_template_service.py`
- Before the output row generation loop, call `_get_spread_target_index()`
- Replace the `idx == 0` check with `idx == spread_target_index`
- Update the logic:
  ```python
  # Determine which row should get spread values (first non-CAPITAL for Colombia)
  spread_target_index = self._get_spread_target_index(processed_concepts, country)

  # Generate output rows for non-zero concepts
  for idx, (concept_type, amount) in enumerate(processed_concepts.items()):
      if abs(amount) > 0.001:
          # ... existing AR account logic ...

          # Spread goes to spread_target_index, not always idx == 0
          is_spread_target = (idx == spread_target_index)

          row_comision_banco = comision_banco if idx == 0 else None

          if should_create_separate_spread_line:
              row_spread_pa = None
              row_spread_fk = None
          else:
              row_spread_pa = round(spread_pa * total_pagado_usd, 2) if is_spread_target and spread_pa is not None and total_pagado_usd is not None else None
              row_spread_fk = round(spread_fk * total_pagado_usd, 2) if is_spread_target and spread_fk is not None and total_pagado_usd is not None else None
          row_spread_supra = spread_supra if is_spread_target else None
  ```

### Step 4: Update Existing Unit Tests
- Edit `backend/tests/test_payment_template_service.py`
- Update `test_multi_concept_pago_en_linea_no_spread_row` to verify:
  - Spread FK is on COSTOS_FIJOS row, NOT on CAPITAL row
- Add new test `test_spread_assigned_to_non_capital_concept`:
  - Input: CAPITAL + COSTOS_FIJOS + INTERESES
  - Expected: Spread on first non-CAPITAL (COSTOS_FIJOS), not on CAPITAL
- Add new test `test_spread_on_capital_when_only_capital_manual`:
  - Input: Only CAPITAL, Manual payment (not Pago en línea)
  - Expected: Spread on CAPITAL (no other option)

### Step 5: Add Test for _get_spread_target_index Method
- Add unit tests for the new helper method:
  - `test_spread_target_index_returns_first_non_capital`
  - `test_spread_target_index_returns_zero_when_capital_only`
  - `test_spread_target_index_mexico_always_zero`

### Step 6: Run Unit Tests
- Run `cd backend && python -m pytest tests/test_payment_template_service.py -v`
- Ensure all tests pass including new and updated test cases

### Step 7: Run Full Validation Suite
- Execute all validation commands to ensure no regressions

## Testing Strategy

### Unit Tests
- Test `_get_spread_target_index()` with various concept combinations:
  - CAPITAL only → returns 0
  - CAPITAL + COSTOS_FIJOS → returns 1 (COSTOS_FIJOS index)
  - COSTOS_FIJOS + CAPITAL → returns 0 (COSTOS_FIJOS is first)
  - CAPITAL + INTERESES + COSTOS_FIJOS → returns 1 (first non-CAPITAL)
  - México with any concepts → returns 0 (standard behavior)
- Test full `_process_row()` output to verify spread assignment

### Edge Cases
- Only CAPITAL concept with Manual payment (spread should go to CAPITAL)
- Only CAPITAL concept with Pago en Línea (separate SPREAD line - existing behavior)
- Multiple non-CAPITAL concepts (spread goes to first one)
- CAPITAL with zero value but other concepts have values
- All concepts have zero values (no output rows)
- México payment (should use standard idx == 0 behavior)

## Acceptance Criteria
1. When a Colombia payment has CAPITAL plus other concepts:
   - Spread FK/PA is assigned to the first non-CAPITAL concept row
   - CAPITAL row has `Spread PA` = None and `Spread FK` = None
2. When a Colombia payment has only CAPITAL (Manual payment):
   - Spread FK/PA is assigned to CAPITAL row (no other option)
3. When a Colombia payment has only CAPITAL (Pago en Línea):
   - Separate SPREAD row is created (existing behavior unchanged)
4. México conversion is not affected by this change (uses idx == 0)
5. All existing unit tests continue to pass (with updated expectations)
6. comision_banco continues to go to first row (idx == 0), independent of spread

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run payment template specific tests
- `cd backend && python -m pytest tests/ -v` - Run all backend tests
- `cd backend && ruff check src/core/servicios/payment_template_service.py` - Run linting on modified file
- `cd frontend && npm run lint` - Run frontend linting (no changes expected)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check (no changes expected)
- `cd frontend && npm run build` - Run frontend build (no changes expected)
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_colombia_spread_non_capital.md` E2E test to validate this functionality works

## Notes
- This feature is Colombia-specific. México should continue to use the existing behavior (spread on first row).
- The `comision_banco` field should continue to be assigned to the first row (idx == 0), independent of spread assignment.
- Dictionary ordering in Python 3.7+ is guaranteed to be insertion order, so the concept order from `_process_concepts()` is deterministic.
- The order of concepts in `processed_concepts` is: CAPITAL, SEGUROS, COSTOS_FIJOS, INTERESES, MORATORIOS (based on how `_process_concepts` builds the dictionary).
- Future consideration: If the business requires spread to go to a specific concept type (e.g., always INTERESES if present), the `_get_spread_target_index` method can be extended with priority logic.

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no DB changes)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (N/A - none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented (if applicable)
- [x] Data transformation rules specified (1:1 or 1:N)
- [x] Catalog/lookup dependencies identified

### Consistency (ALL features)
- [x] Data types match between frontend and backend (N/A - backend only)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods (N/A)
- [x] Country-specific variations handled (CO vs MX) - Colombia only change

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
