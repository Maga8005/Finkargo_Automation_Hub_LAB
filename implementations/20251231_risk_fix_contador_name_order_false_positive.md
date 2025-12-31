# Implementation Report: Fix Contador/Revisor Fiscal Name Order False Positive

**Date:** 2025-12-31
**ADW ID:** b0a5e4a8
**Patch Spec:** specs/patch/patch-adw-b0a5e4a8-fix-name-order-false-positive-contador.md

## Summary

Fixed a false positive in the contador/revisor fiscal validation where names with different orders and partial token overlap were incorrectly flagged as mismatches.

## Problem

The `_names_match` method in `cross_validation_service.py` was failing to match names when:
- RUT shows names in Colombian format: `LASTNAME1 LASTNAME2 FIRSTNAME1 FIRSTNAME2` (e.g., "LOBO BARROS LAIS MILENA")
- Financial statements show partial names: `FIRSTNAME1 FIRSTNAME2 LASTNAME1` (e.g., "LAIS MILENA LOBO")

The existing token comparison required exact token matches, which failed when one document had partial names (missing second lastname).

## Solution

Enhanced the `_names_match` method to calculate token overlap percentage:
- Compute common tokens between the two name sets
- If 75% or more of the smaller token set matches, consider it a match
- This handles partial name variations while still rejecting completely different names

## Changes Made

- **backend/src/core/servicios/risk/cross_validation_service.py** (lines 1304-1312):
  - Added token overlap calculation after exact token match check
  - Uses 75% threshold of smaller token set for match determination

- **backend/tests/test_fraud_detection_service.py**:
  - Added `test_contador_revisor_fiscal_partial_name_match` test case
  - Validates the Global Imports Latam SAS scenario (LOBO BARROS LAIS MILENA vs LAIS MILENA LOBO)

## Validation

All validation commands passed:

1. `python -m py_compile main.py` - Python syntax valid
2. `ruff check src/` - All checks passed
3. `pytest tests/test_fraud_detection_service.py -v` - 36 tests passed
4. `pytest -v` - 510 tests passed
5. `npx tsc --noEmit` - No TypeScript regressions

## Discrepancies Found

None. The plan accurately described the existing implementation and required changes.

## Files Changed

```
backend/src/core/servicios/risk/cross_validation_service.py | 10 +++++
backend/tests/test_fraud_detection_service.py              | 49 ++++++++++++++++++++++
2 files changed, 59 insertions(+)
```

## Test Case Details

The new test validates:
- RUT contador name: "LOBO BARROS LAIS MILENA" (4 tokens)
- Financial statement signatory: "LAIS MILENA LOBO" (3 tokens)
- Common tokens: {LOBO, LAIS, MILENA} = 3 tokens
- Overlap ratio: 3/3 = 100% of smaller set
- Expected result: Match (is_discrepancy = False)
