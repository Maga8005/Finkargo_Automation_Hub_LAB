# Implementation Report: Check All Signatories for Contador/Revisor Fiscal Validation

**Date:** 2025-12-31
**ADW ID:** `b0a5e4a8`
**Module:** Risk / Fraud Detection
**Type:** Patch

## Summary

Fixed false positive alerts in contador/revisor fiscal validation by updating the logic to check ALL signatories in financial statements instead of just the first one.

## Problem

The validation logic was only checking a single signatory (either `auditor_name` or `signatory_name`) against registered contador/revisor fiscal. Financial statements often have multiple signatories (e.g., Representante Legal AND Contador), but the system only validated the first one found. This caused false positives in cases like Multivalsas where the Contador was the second signatory.

## Solution

1. **Added `signatories` array field to extraction schemas** - Both `FINANCIAL_STATEMENT_CURRENT` and `FINANCIAL_STATEMENT_PRIOR` schemas now support extracting all signatories with their names, IDs, and roles.

2. **Updated validation logic to check all signatories** - The `_validate_contador_revisor_fiscal()` method now:
   - Builds a list of all signatories from the new `signatories` array AND legacy single fields (backwards compatibility)
   - Checks if ANY signatory matches the registered contador/revisor fiscal
   - Only flags HIGH severity alert if NONE of the signatories match

## Files Modified

- `backend/src/core/servicios/risk/document_extraction_service.py` - Added `signatories` array to financial statement schemas
- `backend/src/core/servicios/risk/cross_validation_service.py` - Updated validation logic to check all signatories
- `backend/tests/test_fraud_detection_service.py` - Updated test assertions to match new message format

## Changes Summary

```
.../servicios/risk/cross_validation_service.py     | 258 ++++++++++-----------
.../servicios/risk/document_extraction_service.py  |  30 ++-
backend/tests/test_fraud_detection_service.py      |   6 +-
3 files changed, 155 insertions(+), 139 deletions(-)
```

## Discrepancies Found and Resolved

1. **Test assertion updates required** - Two test cases (`test_contador_revisor_fiscal_name_mismatch` and `test_contador_revisor_fiscal_not_found_critical`) had assertions checking for specific phrases in the description message. The new message format uses plural "Firmantes" and "Ningún firmante" instead of singular forms. Updated the test assertions to match the new message patterns.

## Key Implementation Details

### New Extraction Schema Field

```python
"signatories": {
    "type": ["array", "null"],
    "description": "List of all signatories who signed the financial statement",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "id": {"type": ["string", "null"]},
            "role": {"type": ["string", "null"]}
        },
        "required": ["name"]
    }
}
```

### New Validation Logic

1. Builds `signatories_to_check` list from:
   - `signatories` array (new schema)
   - `signatory_name` field (legacy)
   - `auditor_name` field (legacy)

2. Loops through all signatories to find a match:
   - If any matches contador/revisor fiscal → SUCCESS
   - If name matches but ID differs → MEDIUM severity (ID discrepancy)
   - If none match → HIGH severity alert

3. Updated `values_found` to include `all_signatories` for transparency in UI

## Validation Results

- Backend syntax check: PASSED
- Backend linting (ruff): All checks passed
- Backend tests: 509 passed (including 35 fraud detection tests)
- Frontend linting: 4 warnings (pre-existing, unrelated)
- Frontend type check: PASSED
- Frontend build: PASSED

## Testing Notes

The patch should be tested with financial statements that have multiple signatories (like the Multivalsas case with Representante Legal + Contador) to verify the fix works correctly.
