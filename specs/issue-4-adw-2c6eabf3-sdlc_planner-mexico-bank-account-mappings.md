# Feature: Mexico Bank Account Mappings for Aplicacion de Pagos

## Feature Description
Add new bank account mappings for Mexico in the Treasury (Tesoreria) payment export functionality. When processing the "Historial de Pagos" file for Mexico, the system needs to map specific `Cuenta Remitente` (sender bank account) values to their corresponding NetSuite internal account codes. This feature extends the existing bank account mapping functionality by adding two new mappings:
- Account `012180001189708826` maps to code `2111`
- Account `738250227` maps to code `2519`

## User Story
As a Treasury department (Tesoreria) user
I want the system to correctly map Mexico bank account numbers to NetSuite codes in the Aplicacion de Pagos output
So that payments are automatically assigned to the correct NetSuite accounts without manual intervention

## Problem Statement
The Mexico payment export functionality currently has limited bank account mappings. When treasury users upload a Historial de Pagos file with bank account `012180001189708826` or `738250227` in the "Cuenta Remitente" column, the `account` field in the output remains empty because these mappings don't exist. This requires manual data entry in NetSuite, increasing workload and potential for errors.

## Solution Statement
Extend the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary in `payment_catalogs.py` to include the two new bank account mappings. The existing `get_bank_account_id()` function already handles Mexico lookups, so only the dictionary needs to be updated. This follows the established pattern for adding bank account mappings.

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Existing RBAC on `/api/tesoreria/*` endpoints
- Frontend Protection: Existing route protection on `/tesoreria/*` pages

## Relevant Files
Use these files to implement the feature:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (lines 92-109) - Contains the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary that needs to be updated with the new mappings. This is the only file that requires modification.
- **`backend/src/core/servicios/payment_template_service.py`** (line 669) - Uses `get_bank_account_id()` to populate the `account` field. No changes needed, but useful to understand how mappings are used.
- **`backend/tests/test_payment_template_service.py`** - Existing test file for payment template service. New test cases should be added here.
- **`implementations/20251209_tesoreria_mexico_bank_account_mapping.md`** - Previous implementation reference showing the pattern for adding Mexico bank account mappings.
- **`.claude/commands/test_e2e.md`** - E2E test runner documentation.
- **`.claude/commands/e2e/test_login.md`** - Example E2E test file format.
- **`.claude/commands/e2e/test_payment_template_converter.md`** - Existing payment template E2E test for reference.

### New Files
- **`.claude/commands/e2e/test_mexico_bank_account_mappings.md`** - E2E test file to validate the new bank account mappings work correctly in the Mexico payment conversion flow.

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing only)
This feature involves Excel processing for the payment template conversion.

**Source Excel Structure:**
| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| Cuenta Remitente | No (optional) | String/Number | Not empty for mapping |

**Output Excel Structure:**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| account | Cuenta Remitente | Lookup in MEXICO_BANK_ACCOUNT_MAPPING |

**Catalog Dependencies:**
- [x] AR account mappings documented (existing MEXICO_BANK_ACCOUNT_MAPPING)
- [x] Country-specific variations identified (CO vs MX) - This only affects MX

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| get_bank_account_id() | Optional[int] | Function call | get_bank_account_id('738250227', 'mexico') |

The function signature:
```python
def get_bank_account_id(cuenta_remitente: Optional[str], country: str) -> Optional[int]
```

### Interface Mapping (Frontend ↔ Backend)
No frontend changes required. The `account` field is already included in the output template and will be automatically populated with the correct NetSuite ID.

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| N/A | account | int | Output field in converted Excel |

## Implementation Plan
### Phase 1: Foundation
- No database changes required
- No new DTOs or interfaces needed
- Update only the mapping dictionary

### Phase 2: Core Implementation
- Add new entries to `MEXICO_BANK_ACCOUNT_MAPPING` dictionary
- Handle potential leading zero variations (Excel may strip leading zeros from numeric values)
- Add unit tests for the new mappings

### Phase 3: Integration
- Create E2E test to validate the feature
- Run all validation commands

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Read `.claude/commands/e2e/test_payment_template_converter.md` for payment-specific testing patterns
- Create `.claude/commands/e2e/test_mexico_bank_account_mappings.md` with test steps to:
  1. Login as tesoreria user
  2. Navigate to Mexico payment converter
  3. Upload test file with the new bank accounts
  4. Verify the output contains the correct account codes (2111, 2519)

### Task 2: Update Mexico Bank Account Mapping Dictionary
- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Locate the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary (around lines 92-109)
- Add the two new mappings:
  ```python
  # New mappings for issue #4
  "012180001189708826": 2111,
  "738250227": 2519,
  ```
- IMPORTANT: Also add variants without leading zeros for Excel compatibility:
  ```python
  "12180001189708826": 2111,  # Without leading zero (Excel integer format)
  ```

### Task 3: Add Unit Tests for New Mappings
- Open `backend/tests/test_payment_template_service.py`
- Add test cases to verify:
  ```python
  def test_mexico_bank_account_mapping_012180001189708826():
      """Test new bank account mapping 012180001189708826 -> 2111"""
      assert get_bank_account_id("012180001189708826", "mexico") == 2111

  def test_mexico_bank_account_mapping_738250227():
      """Test new bank account mapping 738250227 -> 2519"""
      assert get_bank_account_id("738250227", "mexico") == 2519

  def test_mexico_bank_account_mapping_without_leading_zero():
      """Test bank account lookup works without leading zero (Excel integer)"""
      assert get_bank_account_id("12180001189708826", "mexico") == 2111
  ```

### Task 4: Run Validation Commands
Execute all validation commands to verify implementation with zero regressions.

## Testing Strategy
### Unit Tests
- Test `get_bank_account_id()` with new account numbers for Mexico
- Test with leading zero and without leading zero variants
- Regression test: verify existing Mexico mappings still work
- Regression test: verify Colombia mappings still work

### Edge Cases
- Account number with leading zeros (string format from Excel text cells)
- Account number without leading zeros (integer format from Excel)
- Account number not in mapping (should return None)
- Whitespace around account number (should be trimmed)

## Acceptance Criteria
- [ ] `get_bank_account_id("012180001189708826", "mexico")` returns `2111`
- [ ] `get_bank_account_id("738250227", "mexico")` returns `2519`
- [ ] `get_bank_account_id("12180001189708826", "mexico")` returns `2111` (no leading zero variant)
- [ ] Existing Mexico bank account mappings continue to work
- [ ] Existing Colombia bank account mappings continue to work
- [ ] All unit tests pass
- [ ] Backend linting passes
- [ ] E2E test file created

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id, MEXICO_BANK_ACCOUNT_MAPPING; print('All Mexico mappings:', MEXICO_BANK_ACCOUNT_MAPPING)"` - Display all Mexico bank account mappings
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Test 012180001189708826:', get_bank_account_id('012180001189708826', 'mexico'))"` - Verify new mapping 1
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Test 738250227:', get_bank_account_id('738250227', 'mexico'))"` - Verify new mapping 2
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Test no leading zero:', get_bank_account_id('12180001189708826', 'mexico'))"` - Verify no-leading-zero variant
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Existing MX mapping 0123270165:', get_bank_account_id('0123270165', 'mexico'))"` - Regression test existing Mexico mapping
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Colombia still works:', get_bank_account_id('60100001091', 'colombia'))"` - Regression test Colombia mapping
- `cd backend && python -m pytest tests/test_payment_template_service.py -v` - Run payment template service tests
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_mexico_bank_account_mappings.md` to validate this functionality works

## Notes
- This feature follows the exact same pattern as the previous Mexico bank account mapping implementation (see `implementations/20251209_tesoreria_mexico_bank_account_mapping.md`)
- Account numbers must be stored as strings to preserve leading zeros
- Excel may store account numbers as integers (stripping leading zeros), so both variants should be mapped
- No frontend changes are required since the `account` field is already included in the output template
- The account number `012180001189708826` has a leading zero that may be stripped by Excel when stored as a number
- No new dependencies required

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
- [x] Data transformation rules specified (1:1 mapping lookup)
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
