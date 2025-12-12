# Implementation: Colombia Recompra Spread Column Routing

**Date:** 2025-12-11
**Module:** Tesorería - Colombia Payment Template Conversion
**Author:** Claude Code

## Summary

Fixed the spread column routing logic to account for the `Recomprado` flag. When an operation is "recomprada" (repurchased), spread should go to `Spread FK` instead of `Spread PA`.

## Changes Made

### 1. Updated main spread routing logic (lines 556-576)
**File:** `backend/src/core/servicios/payment_template_service.py`

**Before:**
```python
if is_nt_spread:
    spread_pa = spread_value
else:
    spread_fk = spread_value
```

**After:**
```python
# Spread goes to PA only if NT and NOT recomprada
if is_nt_spread and not is_recomprada:
    spread_pa = spread_value
else:
    spread_fk = spread_value
```

### 2. Updated Manual COP spread routing logic (lines 623-640)
Applied the same `is_recomprada` check to manual COP payment spread routing.

### 3. Updated INFO logging
Added `is_recomprada` to the INFO level log messages for better debugging visibility.

### 4. Added unit tests
**File:** `backend/tests/test_payment_template_service.py`

Added new test class `TestRecompraSpreadRouting` with 3 tests:
- `test_nt_not_recomprada_spread_goes_to_pa` - NT + NOT recomprada → Spread PA
- `test_nt_recomprada_spread_goes_to_fk` - NT + recomprada → Spread FK
- `test_no_nt_spread_goes_to_fk` - No NT → Spread FK

## Business Logic

| NT Column | Recomprado | Spread Column |
|-----------|------------|---------------|
| Contains "NT" | False | Spread PA (Patrimonio Autónomo) |
| Contains "NT" | True | Spread FK (Fincargo Colombia) |
| Empty | Any | Spread FK (Fincargo Colombia) |

**Rationale:** When an operation is "recomprada", Fincargo Colombia takes back ownership from Patrimonio Autónomo. The spread should therefore go to Fincargo's column (Spread FK) instead of Patrimonio's column (Spread PA).

## Test Results

All 81 tests pass with zero regressions:
- 3 new recompra spread routing tests
- 78 existing tests unchanged

## Discrepancies from Plan

**None.** The implementation followed the plan exactly.

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 23 lines changed
backend/tests/test_payment_template_service.py        | 197 lines added
```

## Validation

- ✅ `pytest tests/test_payment_template_service.py` - 81 tests passed
- ✅ `ruff check src/core/servicios/payment_template_service.py` - All checks passed
