# Feature: Colombia Recompra AR Account Selection

## Feature Description
Add support for "recompra" (repurchased) operations in the Tesorería Colombia payment application module. When operations that were previously "cedidas" (assigned) to Patrimonio Autónomo are later "recompradas" (repurchased) by Fincargo Colombia, the AR account selection should revert to Fincargo Colombia accounts instead of Patrimonio accounts.

This ensures correct accounting treatment where repurchased operations are properly tracked under Fincargo Colombia's books rather than Patrimonio Autónomo's.

## User Story
As a **treasury operations user**
I want the payment template conversion to **recognize repurchased (recomprada) operations and use the correct AR accounts**
So that **repurchased operations use Fincargo Colombia AR accounts (302, 258, 1387) instead of Patrimonio Autónomo accounts (304, 259, 310, 1474)**

## Problem Statement
Currently, the payment template service determines AR accounts based solely on the NT column:
- NT has value → Patrimonio Autónomo AR accounts (304, 259, 310, 1474)
- NT is empty → Fincargo Colombia AR accounts (302, 258, 258, 1387)

This logic does not account for "recompra" scenarios where an operation was initially cedida (has NT value) but was later repurchased by Fincargo Colombia. In these cases, the AR accounts should revert to Fincargo Colombia accounts, but the current system still uses Patrimonio accounts because NT column remains populated.

## Solution Statement
Extend the AR account selection logic to consider both the NT flag AND the "Recomprado" column:
1. Add "recompra" column mapping to `COLOMBIA_OPTIONAL_COLUMNS`
2. Update `get_ar_account()` function to accept an `is_recomprada` parameter
3. Apply new logic: Use NT AR accounts ONLY when NT is populated AND operation is NOT recomprada
4. Extract the "Recomprado" value in `_process_row()` and pass it to AR account lookups

**Decision Matrix:**
| NT Column | Recomprado | AR Accounts Used |
|-----------|------------|------------------|
| Empty | N/A | Fincargo Colombia |
| Has Value | Not Recomprada | Patrimonio Autónomo |
| Has Value | Recomprada | Fincargo Colombia |

## Access Control
- Required Role(s): `admin`, `operations`, `mesa_control`
- Backend Protection: No changes required (existing endpoint protection applies)
- Frontend Protection: No changes required (backend-only feature)

## Relevant Files
Use these files to implement the feature:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`**
  - Contains AR account mappings (`COLOMBIA_AR_ACCOUNTS`, `COLOMBIA_NT_AR_ACCOUNTS`)
  - Contains `COLOMBIA_OPTIONAL_COLUMNS` dictionary where "recompra" column needs to be added
  - Contains `get_ar_account()` function that needs `is_recomprada` parameter

- **`backend/src/core/servicios/payment_template_service.py`**
  - Contains `_process_row()` method where "Recomprado" value extraction happens
  - Contains the call to `get_ar_account()` that needs to pass `is_recomprada`
  - Contains `_collect_payment_group_info()` that may need updating for group-level recompra tracking

- **`backend/tests/test_payment_template_service.py`**
  - Contains existing tests for payment template service
  - New tests for recompra logic should follow existing patterns

- **`.claude/commands/test_e2e.md`** - Read to understand E2E test structure
- **`.claude/commands/e2e/test_login.md`** - Read for E2E test example patterns

### New Files
- **`backend/tests/test_recompra_ar_account.py`** - Unit tests specifically for recompra AR account selection logic

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure:**
| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| NT | No | String | Contains operation ID when cedida |
| Recomprado | No | String | "Si"/"Sí"/"Yes"/"True"/"1"/"Recomprada" for repurchased |

**Output Excel Structure (if applicable):**
The output structure is unchanged. The feature only affects AR account selection (araccount column value).

| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| araccount | Concept type + is_nt + is_recomprada | Lookup from AR account mappings |

**AR Account Mapping Decision:**
| Concept | Fincargo Colombia (Normal/Recomprada) | Patrimonio (NT, Not Recomprada) |
|---------|--------------------------------------|----------------------------------|
| CAPITAL | 302 | 304 |
| INTERESES | 258 | 259 |
| MORATORIOS | 258 | 259 |
| COSTOS_FIJOS | 258 | 310 |
| SEGUROS | 1387 | 1474 |

**Catalog Dependencies:**
- [x] AR account mappings documented - existing `COLOMBIA_AR_ACCOUNTS` and `COLOMBIA_NT_AR_ACCOUNTS`
- [x] Country-specific variations identified - This feature is Colombia-only

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `get_ar_account()` | `Optional[int]` | Direct return | `ar_account = get_ar_account("CAPITAL", "colombia", True, False)` |
| `get_optional_columns()` | `Dict[str, str]` | Dictionary access | `columns["recompra"]` |

### Interface Mapping (Frontend ↔ Backend)
This is a backend-only feature. No frontend changes are required.

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| N/A | is_recomprada | bool | Derived from "Recomprado" column in input Excel |

## Implementation Plan

### Phase 1: Foundation
1. Add "recompra" column mapping to `COLOMBIA_OPTIONAL_COLUMNS` in `payment_catalogs.py`
2. Update `get_ar_account()` function signature to accept `is_recomprada` parameter
3. Implement new AR account selection logic in `get_ar_account()`

### Phase 2: Core Implementation
1. Extract "Recomprado" value in `_process_row()` method
2. Implement helper function or logic to parse truthy values for recompra
3. Pass `is_recomprada` flag to all `get_ar_account()` calls in `_process_row()`
4. Update `_collect_payment_group_info()` if group-level recompra tracking is needed

### Phase 3: Integration
1. Add comprehensive unit tests for the new logic
2. Test with sample data covering all combinations (NT/no-NT, recomprada/not-recomprada)
3. Verify backward compatibility - existing behavior should not change for non-recomprada operations

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Recompra Column to Optional Columns

**File:** `backend/src/core/servicios/catalogs/payment_catalogs.py`

- Add "recompra" entry to `COLOMBIA_OPTIONAL_COLUMNS` dictionary:
  ```python
  "recompra": "Recomprado",  # Indicates if cedida operation was repurchased
  ```

### Step 2: Update get_ar_account() Function Signature

**File:** `backend/src/core/servicios/catalogs/payment_catalogs.py`

- Update `get_ar_account()` function to accept `is_recomprada` parameter:
  ```python
  def get_ar_account(concept_type: str, country: str, is_nt: bool = False, is_recomprada: bool = False) -> Optional[int]:
  ```
- Update docstring to document the new parameter
- Implement logic: Use NT accounts only when `is_nt=True AND is_recomprada=False`

### Step 3: Extract Recompra Value in _process_row()

**File:** `backend/src/core/servicios/payment_template_service.py`

- After the NT flag extraction (around line 432), add recompra value extraction:
  ```python
  # Check for Recompra flag (Colombia only)
  is_recomprada = False
  if country.lower() == "colombia":
      recompra_raw = get_value("recompra", optional_columns)
      if recompra_raw is not None:
          recompra_str = str(recompra_raw).strip().lower()
          is_recomprada = recompra_str in ['si', 'sí', 'yes', 'true', '1', 'recomprada']
  ```

### Step 4: Pass is_recomprada to get_ar_account() Calls

**File:** `backend/src/core/servicios/payment_template_service.py`

- Update the `get_ar_account()` call in `_process_row()` (around line 705):
  ```python
  ar_account = get_ar_account(concept_type, country, is_nt, is_recomprada)
  ```
- Also update the fallback call for COSTOS_FIJOS if needed

### Step 5: Add Logging for Recompra Decision

**File:** `backend/src/core/servicios/payment_template_service.py`

- Add INFO-level logging for recompra detection and AR account selection:
  ```python
  if is_recomprada:
      logger.info(
          f"Recompra detected: customer={customer_external_id}, "
          f"is_nt={is_nt}, is_recomprada={is_recomprada}, "
          f"ar_account will use Fincargo Colombia accounts"
      )
  ```

### Step 6: Update _collect_payment_group_info() for Recompra Tracking

**File:** `backend/src/core/servicios/payment_template_service.py`

- Add recompra extraction in the pre-processing phase if group-level recompra info is needed for future features

### Step 7: Create Unit Tests for Recompra Logic

**File:** `backend/tests/test_recompra_ar_account.py`

- Create new test file with the following test cases:
  1. `test_normal_operation_uses_fincargo_accounts` - NT empty → Fincargo accounts
  2. `test_cedida_not_recomprada_uses_patrimonio_accounts` - NT populated, not recomprada → Patrimonio accounts
  3. `test_cedida_recomprada_uses_fincargo_accounts` - NT populated, recomprada → Fincargo accounts
  4. `test_recompra_detection_various_truthy_values` - Test "Si", "Sí", "Yes", "True", "1", "Recomprada"
  5. `test_recompra_detection_falsy_values` - Test "No", "", None, "False"
  6. `test_all_concept_types_affected_by_recompra` - CAPITAL, INTERESES, MORATORIOS, COSTOS_FIJOS, SEGUROS

### Step 8: Add Integration Test with Full Row Processing

**File:** `backend/tests/test_payment_template_service.py`

- Add test class `TestRecompraARAccountSelection` with tests that verify end-to-end row processing with recompra flag

### Step 9: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests
1. **`get_ar_account()` function tests:**
   - Test all combinations: (is_nt=True/False) × (is_recomprada=True/False) × (concept_type variations)
   - Verify correct account IDs for each combination
   - Ensure Mexico is unaffected by recompra parameter

2. **Recompra value parsing tests:**
   - Test various truthy values: "Si", "Sí", "YES", "yes", "True", "true", "1", "Recomprada"
   - Test falsy values: "No", "NO", "", None, "False", "0"
   - Test whitespace handling

3. **Row processing tests:**
   - Full `_process_row()` with recompra flag
   - Verify output row has correct araccount value

### Edge Cases
1. **Empty recompra column** - Should default to not recomprada (existing NT behavior)
2. **Missing NT column with recompra value** - Should use Fincargo accounts (NT empty takes precedence)
3. **Case sensitivity** - "SI", "si", "Sí" should all be treated as recomprada
4. **Whitespace** - " Si " should be trimmed and recognized
5. **Unexpected values** - "Maybe", "N/A" should default to not recomprada
6. **Mexico operations** - Should be unaffected by recompra parameter

## Acceptance Criteria
1. ✅ When NT column is empty, Fincargo Colombia AR accounts (302, 258, 1387) are used regardless of Recomprado value
2. ✅ When NT column has a value AND Recomprado is empty/No, Patrimonio AR accounts (304, 259, 310, 1474) are used
3. ✅ When NT column has a value AND Recomprado indicates "yes", Fincargo Colombia AR accounts are used
4. ✅ Mexico operations are unaffected by this change
5. ✅ All existing tests pass (backward compatibility)
6. ✅ New tests cover all recompra scenarios
7. ✅ Logging captures recompra decisions for debugging

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run all backend tests
cd backend && python -m pytest

# Run specific recompra tests
cd backend && python -m pytest tests/test_recompra_ar_account.py -v

# Run payment template service tests
cd backend && python -m pytest tests/test_payment_template_service.py -v

# Run backend linting
cd backend && ruff check src/

# Run frontend linting (unchanged but verify no impact)
cd frontend && npm run lint

# Run TypeScript type check (unchanged but verify no impact)
cd frontend && npx tsc --noEmit

# Run frontend build (unchanged but verify no impact)
cd frontend && npm run build
```

## Notes

1. **Column name confirmation:** The feature spec indicates the column name is "Recomprado". This should be confirmed with the business team before final implementation. The column name is easily changeable in `COLOMBIA_OPTIONAL_COLUMNS`.

2. **Backward compatibility:** The `is_recomprada` parameter defaults to `False`, ensuring that existing behavior is preserved when:
   - The "Recomprado" column doesn't exist in the input file
   - The "Recomprado" column is empty

3. **Future extensibility:** The recompra flag could potentially affect other aspects of payment processing beyond AR accounts. The implementation should be designed to allow easy extension.

4. **Logging:** INFO-level logging is added for key decisions to aid in debugging and audit trails.

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no database changes)
- [ ] E2E test file task included (N/A - backend-only, no UI changes)
- [x] All external dependencies (npm/pip packages) listed in Notes (none required)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented (unchanged, only araccount value affected)
- [x] Data transformation rules specified (is_nt + is_recomprada → AR account lookup)
- [x] Catalog/lookup dependencies identified

### Consistency (ALL features)
- [x] Data types match between frontend and backend (N/A - backend only)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for repository methods
- [x] Country-specific variations handled (Colombia only feature)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [ ] E2E test covers happy path with screenshots (N/A - backend only)
