# Bug: False positive on NIT check when using certificado de existencia from Cámara de Comercio Bogotá

## Bug Description
When running cross-check validation, the system incorrectly interprets a NIT like `9018546872` (extracted from Certificado de Existencia) as different from `901854687-2` (from RUT or financial statements). The system displays the alert: "NITs base diferentes: 901854687, 9018546872".

The root issue is that in Certificados de Existencia y Representación Legal from Cámara de Comercio Bogotá, NITs are often displayed as `901854687 2` (base + space + check digit). When AI extraction processes this, it concatenates to `9018546872`, losing the semantic separation between base NIT and check digit.

**Expected behavior**: NITs `901854687-2`, `901854687 2`, and `9018546872` should all be recognized as the same NIT (base: `901854687`, check digit: `2`).

**Actual behavior**: `9018546872` is treated as a 10-digit base NIT with no check digit, causing a false positive "NITs base diferentes" alert.

## Problem Statement
The `normalize_nit()` function in `normalization_service.py` only recognizes check digits when they are explicitly separated by a dash or space (`[-\s](\d)$`). When a 10-digit NIT string is provided without a separator (e.g., `9018546872`), the function treats the entire string as the base NIT instead of recognizing that Colombian NITs are always 9 base digits + 1 check digit.

## Solution Statement
Enhance the `normalize_nit()` function to handle the case where a 10-digit NIT is provided without a separator. In this case, automatically infer that the last digit is the check digit, since Colombian NITs are structurally 9 base digits + 1 verification digit.

The fix should:
1. First attempt to find an explicit separator (dash or space)
2. If no separator found AND the NIT has exactly 10 digits, treat the last digit as the check digit
3. Preserve backward compatibility for all existing formats

## Steps to Reproduce
1. Create a risk assessment with multiple documents
2. Upload a RUT document with NIT `901854687-2`
3. Upload a Certificado de Existencia where the NIT is extracted as `9018546872` (no separator)
4. Run cross-validation
5. Observe the false positive alert: "ALERTA CRÍTICA: NITs base diferentes: 901854687, 9018546872"

## Root Cause Analysis
The `normalize_nit()` function in `backend/src/core/servicios/risk/normalization_service.py` uses this regex pattern:

```python
check_digit_match = re.search(r'[-\s](\d)$', cleaned)
```

This pattern only matches when there's an explicit separator (dash or space) before the final digit. For input `9018546872`:
- The regex `[-\s](\d)$` does NOT match (no separator)
- `check_digit` is set to `None`
- The entire `9018546872` becomes the base NIT (10 digits)

For input `901854687-2`:
- The regex matches: separator=`-`, check digit=`2`
- `check_digit` = `2`
- Base NIT = `901854687` (9 digits)

The comparison then fails because `901854687` != `9018546872`.

Colombian NITs are always structured as 9 base digits + 1 check digit. When we receive a 10-digit number without separator, we should infer this structure.

## Affected Layer
- [x] Backend: core/servicios (business logic)

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/risk/normalization_service.py` - Contains the `normalize_nit()` function that needs to be updated to handle 10-digit NITs without separators
- `backend/tests/test_cross_validation_improvements.py` - Contains existing NIT validation tests; add new tests for this edge case
- `backend/src/core/servicios/risk/cross_validation_service.py` - Uses the normalization service for NIT comparison; no changes needed but useful for understanding context

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update the `normalize_nit()` function in `normalization_service.py`

- Read `backend/src/core/servicios/risk/normalization_service.py` to understand the current implementation
- Modify the `normalize_nit()` function to handle the 10-digit case:
  - After checking for explicit separator, if no separator is found:
    - Count the digits in the cleaned NIT
    - If exactly 10 digits, treat the last digit as the check digit
  - Update the docstring to document this new behavior
- Preserve backward compatibility for all existing formats:
  - `830.027.231-3` → base=`830027231`, check=`3`
  - `830027231 3` → base=`830027231`, check=`3`
  - `830027231-3` → base=`830027231`, check=`3`
  - `8300272313` → base=`830027231`, check=`3` (NEW: 10 digits, no separator)
  - `830027231` → base=`830027231`, check=`None` (9 digits, no check digit)

### 2. Add unit tests for the new NIT normalization behavior

- Read `backend/tests/test_cross_validation_improvements.py` to understand the test structure
- Add a new test class or extend existing tests for the 10-digit NIT case:
  - Test `test_nit_10_digits_no_separator_extracts_check_digit`: Verify `9018546872` → base=`901854687`, check=`2`
  - Test `test_nit_10_digits_no_separator_matches_with_separator`: Verify `9018546872` matches `901854687-2`
  - Test `test_nit_9_digits_no_check_digit`: Verify `830027231` → base=`830027231`, check=`None` (unchanged behavior)
  - Test `test_cross_validation_10_digit_nit_no_discrepancy`: Integration test with cross-validation service

### 3. Run Validation Commands

- Run `cd backend && python -m pytest tests/test_cross_validation_improvements.py -v` to verify all NIT tests pass
- Run `cd backend && python -m pytest` to verify no regressions in other tests
- Run `cd backend && ruff check src/` to verify linting passes

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

Before fix (to confirm bug exists):
```bash
cd backend && python -c "
from src.core.servicios.risk.normalization_service import NormalizationService
ns = NormalizationService()
# Current buggy behavior
print('Before fix:')
print(f'901854687-2 -> {ns.normalize_nit(\"901854687-2\")}')  # Should be ('901854687', '2')
print(f'9018546872 -> {ns.normalize_nit(\"9018546872\")}')    # Buggy: ('9018546872', None)
print()
print('are_nits_equivalent:', ns.are_nits_equivalent('901854687-2', '9018546872'))  # Should be (True, ...) but is (False, ...)
"
```

After fix (to confirm bug is resolved):
```bash
cd backend && python -c "
from src.core.servicios.risk.normalization_service import NormalizationService
ns = NormalizationService()
print('After fix:')
print(f'901854687-2 -> {ns.normalize_nit(\"901854687-2\")}')  # ('901854687', '2')
print(f'9018546872 -> {ns.normalize_nit(\"9018546872\")}')    # Fixed: ('901854687', '2')
print(f'830027231 -> {ns.normalize_nit(\"830027231\")}')      # ('830027231', None) - unchanged
print()
print('are_nits_equivalent:', ns.are_nits_equivalent('901854687-2', '9018546872'))  # (True, 'NITs equivalentes', None)
"
```

Full validation:
- `cd backend && python -m pytest tests/test_cross_validation_improvements.py -v` - Run cross-validation tests including new NIT cases
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting (no frontend changes, but good practice)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check (no frontend changes, but good practice)
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- Colombian NITs are always 9 base digits + 1 verification digit (dígito de verificación)
- The check digit is calculated using modulo 11 algorithm from the base digits
- This fix only infers the check digit for exactly 10-digit inputs; 9-digit inputs remain unchanged (no check digit assumed)
- The Certificado de Existencia documents from Cámara de Comercio Bogotá show NITs with a space like "901854687 2" which AI extraction may concatenate to "9018546872"
- This is a minimal, surgical fix that only affects the `normalize_nit()` function
