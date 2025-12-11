# Feature: Colombia Payment Conversion - Spread Separate Line for Capital-Only Pago en Línea

## Feature Description
Modify the Colombia Historial de Pagos to Aplicación de Pagos conversion to handle a special case: when a payment is made via "Pago en Línea" and the entire payment goes only to capital (capital amount equals total payment amount), the spread amount must be output as a separate line with `concept_type` = `SPREAD` instead of being included in the Spread FK/PA columns. The separate SPREAD line should have blank `account` and `araccount` fields.

## User Story
As a Tesorería department user
I want spread amounts for capital-only online payments to appear as separate output lines
So that NetSuite can properly process and reconcile the spread revenue separately from the main payment application

## Problem Statement
Currently, when processing "Pago en Línea" payments in Colombia, the spread value is calculated and placed in the `Spread FK` or `Spread PA` columns of the first output row. However, when a payment goes **entirely to capital** (no other concepts like COSTOS_FIJOS, INTERESES, etc.), the spread amount needs to be recorded as a separate transaction line in NetSuite rather than as an additional column value. This is required for proper financial reconciliation in specific online payment scenarios where only capital is being paid.

## Solution Statement
Modify the `_process_row` method in `PaymentTemplateService` to:
1. Detect when the payment method is "Pago en Línea" AND the only non-zero concept is CAPITAL
2. In this case, instead of populating Spread FK/PA columns, create an additional output row with:
   - `concept_type` = "SPREAD"
   - `payment_amount` = calculated spread amount (spread_value × total_pagado_usd)
   - `currency` = "COP" (spread is always in COP for Colombia)
   - `account` = blank/None
   - `araccount` = blank/None
   - Same values for: `customer_external_id`, `invoice_core_id`, `payment_date`, `payment_ref`, `exchangerate`
3. The Spread FK/PA columns should remain empty (None) for all rows in this scenario

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Uses existing `require_roles(['tesoreria'])` dependency
- Frontend Protection: Existing route protection - no changes needed

## Relevant Files
Use these files to implement the feature:

- `backend/src/core/servicios/payment_template_service.py` - Main service that processes rows and generates output. Contains `_process_row` method that needs modification to detect capital-only payments and generate separate SPREAD line.
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Contains column mappings and OUTPUT_TEMPLATE_COLUMNS. May need to add "SPREAD" as a recognized concept type.
- `backend/src/interface/tesoreria_dtos.py` - DTOs for tesoreria module. May need to update ConceptType if it's typed.
- `frontend/src/types/tesoreria.ts` - Frontend types including ConceptType. Should add "SPREAD" as valid concept.
- `.claude/commands/test_e2e.md` - E2E test runner instructions for understanding test patterns.
- `.claude/commands/e2e/test_login.md` - Reference for E2E test file format.
- `.claude/commands/e2e/test_payment_template_converter.md` - Existing payment converter test that can be referenced.

### New Files
- `.claude/commands/e2e/test_colombia_spread_separate_line.md` - E2E test file to validate the new spread separate line behavior

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
| Cliente | Yes | String | Not empty |
| Identificación del cliente | Yes | String | Not empty |
| Código de desembolso | Yes | String | Not empty |
| Código de recaudo | Yes | String | Not empty |
| Fecha de pago | Yes | Date | Valid date |
| Moneda | Yes | String | COP/USD |
| Capital | Yes | Numeric | >= 0 |
| Banco remitente | Yes | String | Not empty |
| Médio de pago | No | String | "Pago en línea", "Manual", etc. |
| Tasa de cambio de FK/en línea | No | Numeric | Exchange rate |
| Spread | No | Numeric | Spread rate value |
| Total pagado [USD] | No | Numeric | Total in USD |
| NT | No | String | "NT" for Operaciones Cedidas |

**Output Excel Structure (updated):**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| customer_external_id | Identificación del cliente | Direct copy |
| invoice_core_id | Código de desembolso | Direct copy |
| concept_type | Derived | "CAPITAL", "COSTOS_FIJOS", "INTERESES", "MORATORIOS", "SEGUROS", **"SPREAD"** (NEW) |
| payment_date | Fecha de pago | Format dd/mm/yyyy |
| payment_amount | Concept value or spread calc | Round to 2 decimals |
| currency | Moneda or "COP" for SPREAD | Direct or fixed "COP" |
| payment_ref | Generated | customer + date + currency + cuenta |
| account | Cuenta Remitente lookup | **Blank for SPREAD** |
| araccount | AR account lookup | **Blank for SPREAD** |
| exchangerate | Tasa de cambio | Direct copy |
| comision_banco | Referencia bancaria | Parsed numeric (first row only) |
| Spread PA | Spread × Total USD | **Blank when separate SPREAD line** |
| Spread FK | Spread × Total USD | **Blank when separate SPREAD line** |
| Spread Supra | N/A | Always blank |

**Data Transformation Rules:**
- Standard behavior (multiple concepts): 1:N row expansion (one row per non-zero concept), spread in Spread FK/PA column
- **Capital-only Pago en Línea** (NEW): 1:(1+1) row expansion - one CAPITAL row + one separate SPREAD row
- Detection logic: `medio_pago` contains "pago en l" (case-insensitive) AND only CAPITAL has non-zero value

**Catalog Dependencies:**
- [x] AR account mappings documented (existing, no changes needed for SPREAD - it uses blank)
- [x] Country-specific variations identified (Colombia only, México unchanged)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A - No repository changes | N/A | N/A | Service-only changes |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| concept_type | concept_type | string | Add "SPREAD" as valid value |

## Implementation Plan

### Phase 1: Foundation
- Add "SPREAD" to concept type definitions in both frontend and backend
- No database changes required (output is file-based, not persisted)

### Phase 2: Core Implementation
- Modify `_process_row` in `PaymentTemplateService` to:
  1. Detect capital-only Pago en Línea payments
  2. Generate separate SPREAD output row when condition is met
  3. Ensure Spread FK/PA columns are blank when separate line is generated
- Add helper method `_is_capital_only_pago_en_linea()` for clean detection logic
- Add method `_create_spread_output_row()` to generate the separate SPREAD line

### Phase 3: Integration
- No routing or navigation changes needed
- No frontend component changes needed (output format is same Excel structure)
- Create E2E test to validate the new behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Frontend Type Definitions
- Edit `frontend/src/types/tesoreria.ts`
- Add `'SPREAD'` to the `ConceptType` union type
- This allows the frontend to recognize SPREAD as a valid concept type if validation is added later

### Step 2: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for test format
- Create `.claude/commands/e2e/test_colombia_spread_separate_line.md`
- Define test steps that:
  1. Login as tesoreria user
  2. Navigate to Colombia payment converter
  3. Upload a test Excel file with a capital-only Pago en Línea payment
  4. Download the converted file
  5. Verify the output contains a separate SPREAD row with blank account/araccount
  6. Verify the CAPITAL row has no Spread FK/PA values

### Step 3: Add Helper Method for Detection
- Edit `backend/src/core/servicios/payment_template_service.py`
- Add a new private method `_is_capital_only_pago_en_linea()`:
  ```python
  def _is_capital_only_pago_en_linea(
      self,
      medio_pago: Optional[str],
      processed_concepts: Dict[str, float]
  ) -> bool:
      """
      Check if this is a capital-only Pago en Línea payment.

      Returns True if:
      1. Payment method is "Pago en línea" (case-insensitive)
      2. CAPITAL is the only non-zero concept
      """
      # Check payment method
      if not medio_pago or "pago en l" not in medio_pago.lower():
          return False

      # Check if only CAPITAL has a non-zero value
      non_zero_concepts = [k for k, v in processed_concepts.items() if abs(v) > 0.001]
      return non_zero_concepts == ["CAPITAL"]
  ```

### Step 4: Add Method to Create SPREAD Output Row
- Continue editing `backend/src/core/servicios/payment_template_service.py`
- Add a new private method `_create_spread_output_row()`:
  ```python
  def _create_spread_output_row(
      self,
      customer_external_id: str,
      invoice_core_id: str,
      payment_date: str,
      payment_ref: str,
      exchangerate: Optional[float],
      spread_amount: float
  ) -> Dict:
      """
      Create a separate SPREAD output row for capital-only Pago en Línea payments.

      The SPREAD row has blank account and araccount fields.
      """
      return {
          "customer_external_id": customer_external_id,
          "invoice_core_id": invoice_core_id,
          "concept_type": "SPREAD",
          "payment_date": payment_date,
          "payment_amount": round(spread_amount, 2),
          "currency": "COP",  # Spread is always in COP for Colombia
          "payment_ref": payment_ref,
          "account": None,  # Blank for SPREAD
          "araccount": None,  # Blank for SPREAD
          "exchangerate": exchangerate,
          "comision_banco": None,
          "Spread PA": None,
          "Spread FK": None,
          "Spread Supra": None,
      }
  ```

### Step 5: Modify _process_row for Capital-Only Detection
- Continue editing `backend/src/core/servicios/payment_template_service.py`
- Modify the `_process_row` method to:
  1. After processing concepts, check if this is capital-only Pago en Línea
  2. If yes, calculate spread amount and create separate SPREAD row
  3. If yes, ensure Spread FK/PA columns are NOT populated on the CAPITAL row
  4. The logic should be added after `processed_concepts = self._process_concepts(...)` and before generating output rows

**Key changes to `_process_row`:**
- After calling `_process_concepts()`, call `_is_capital_only_pago_en_linea(medio_pago, processed_concepts)`
- Create a flag `should_create_separate_spread_line` based on this check
- Calculate `spread_amount = spread_value * total_pagado_usd` if condition is met
- When generating output rows:
  - If `should_create_separate_spread_line` is True:
    - Do NOT set `row_spread_pa` or `row_spread_fk` on the CAPITAL row
    - After generating the CAPITAL row, call `_create_spread_output_row()` and append it
  - Otherwise, keep existing behavior (spread in columns)

### Step 6: Update Logging for New Behavior
- Add debug logging when separate SPREAD line is created:
  ```python
  if should_create_separate_spread_line:
      logger.debug(
          f"Creating separate SPREAD line for capital-only Pago en línea: "
          f"customer={customer_external_id}, spread_amount={spread_amount}"
      )
  ```

### Step 7: Write Unit Tests
- Create or update test file `backend/tests/test_payment_template_service.py`
- Add test cases for:
  1. `test_capital_only_pago_en_linea_creates_spread_line` - Verify separate SPREAD row is created
  2. `test_capital_only_pago_en_linea_no_spread_columns` - Verify Spread FK/PA are blank on CAPITAL row
  3. `test_multiple_concepts_pago_en_linea_no_spread_line` - Verify standard behavior when multiple concepts exist
  4. `test_capital_only_manual_payment_no_spread_line` - Verify manual payments keep standard behavior

### Step 8: Run Backend Tests
- Run `cd backend && python -m pytest tests/test_payment_template_service.py -v`
- Ensure all tests pass including new test cases

### Step 9: Run Full Validation Suite
- Execute validation commands to ensure no regressions

## Testing Strategy

### Unit Tests
- Test `_is_capital_only_pago_en_linea()` with various inputs:
  - Pago en línea with only CAPITAL → True
  - Pago en línea with CAPITAL + INTERESES → False
  - Manual payment with only CAPITAL → False
  - Pago en línea with zero CAPITAL → False
- Test `_create_spread_output_row()` output format
- Test full `_process_row()` output for capital-only scenario

### Edge Cases
- Capital = 0 (edge case, should not create SPREAD line)
- Spread value = 0 (should not create SPREAD line even if capital-only)
- Total pagado USD = 0 (spread amount would be 0, handle gracefully)
- NT flag present with capital-only (should use Spread PA, not Spread FK - verify in separate line)
- Multiple source rows with same payment_ref grouping, one capital-only and one not
- Pago en línea spelling variations: "Pago en Línea", "pago en linea", "PAGO EN LÍNEA"

## Acceptance Criteria
1. When a Colombia payment has `Médio de pago` = "Pago en línea" AND only CAPITAL has a non-zero value:
   - A separate output row with `concept_type` = "SPREAD" is created
   - The SPREAD row has `account` = blank and `araccount` = blank
   - The SPREAD row has `payment_amount` = spread_value × total_pagado_usd (rounded to 2 decimals)
   - The SPREAD row has `currency` = "COP"
   - The CAPITAL row has `Spread PA` = blank and `Spread FK` = blank
2. When a Colombia payment has multiple non-zero concepts, standard behavior is maintained (spread in columns)
3. When a Colombia payment is NOT "Pago en línea", standard behavior is maintained regardless of concept count
4. México conversion is not affected by this change
5. All existing unit tests continue to pass
6. E2E test validates the new behavior with real file upload/download

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/ -v` - Run all backend tests
- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run payment template specific tests
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_colombia_spread_separate_line.md` E2E test to validate this functionality works

## Notes
- This feature is Colombia-specific. México does not have this requirement.
- The "SPREAD" concept type is only used for output; it's not a column in the source Excel file.
- The spread calculation `spread_value × total_pagado_usd` is already being done in the current code for the column values; we're just outputting it differently.
- The exchange rate adjustment for Pago en línea (subtracting spread from rate) should still occur on the CAPITAL row.
- Future consideration: If more countries need similar logic, consider making this behavior configurable per country in the catalogs.

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
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
