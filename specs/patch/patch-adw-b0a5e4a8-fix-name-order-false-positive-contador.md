# Patch: Fix contador/revisor fiscal name order false positive

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `The app is raising a false positive when checking for signatories vs revisor fiscal or contador, when the order of names and last names is inverted in one document relative to the other. For example, in this case for Global Imports Latam SAS, Lais Milena Lobo is the same person as Lobo Barros Lais Milena. The issue is the revisor fiscal and the contador show up in the RUT first with last names then with names, while other documents may show them first with names and then last names.`

## Issue Summary
**Original Spec:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md
**Issue:** The `_names_match` method in `cross_validation_service.py` fails to match names when name parts differ between documents (e.g., "Lais Milena Lobo" vs "Lobo Barros Lais Milena"). The current token-based comparison requires exact token matches, but Colombian documents often show partial names in different orders - RUT shows "LASTNAME1 LASTNAME2 FIRSTNAME1 FIRSTNAME2" while financial statements may show "FIRSTNAME1 FIRSTNAME2 LASTNAME1" (without LASTNAME2).
**Solution:** Enhance the `_names_match` method to use a token overlap percentage check instead of exact token match. If one name's tokens are a significant subset of the other's tokens (e.g., 75% overlap), consider it a match. This handles cases where one document has partial names.

## Files to Modify

- `backend/src/core/servicios/risk/cross_validation_service.py`: Enhance `_names_match()` method to handle partial name matches with token overlap
- `backend/tests/test_fraud_detection_service.py`: Add test case for partial name order matching

## Implementation Steps

### Step 1: Enhance `_names_match` method in cross_validation_service.py
- Modify the token comparison logic (lines 1297-1302) to use token overlap instead of exact match
- Instead of `if tokens1 == tokens2:`, calculate the overlap percentage between the two token sets
- If the overlap is >= 75% of the smaller token set, return True (match)
- This handles cases like:
  - "LAIS MILENA LOBO" (3 tokens) vs "LOBO BARROS LAIS MILENA" (4 tokens)
  - Common tokens: {LAIS, MILENA, LOBO} = 3 tokens
  - Overlap = 3/3 (100% of smaller set) = match

Implementation:
```python
# In _names_match method, after exact token match check:
# Check for partial token overlap (handles name variations between documents)
common_tokens = tokens1 & tokens2
min_tokens = min(len(tokens1), len(tokens2))
if min_tokens > 0:
    overlap_ratio = len(common_tokens) / min_tokens
    if overlap_ratio >= 0.75:  # 75% of smaller set must match
        return True
```

### Step 2: Add unit test for partial name matching
- Add test case to `test_fraud_detection_service.py` covering the scenario:
  - RUT contador/revisor: "LOBO BARROS LAIS MILENA"
  - Financial statement signatory: "LAIS MILENA LOBO"
  - Expected: Match (INFO severity, not HIGH)

## Validation

Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && python -m py_compile src/main.py` - Validate Python syntax
2. `cd backend && ./venv/bin/ruff check src/` - Validate code quality
3. `cd backend && python -m pytest tests/test_fraud_detection_service.py -v --tb=short` - Run fraud detection tests
4. `cd backend && python -m pytest -v --tb=short` - Run all backend tests
5. `cd frontend && npx tsc --noEmit` - Verify no TypeScript regressions

## Patch Scope
**Lines of code to change:** ~15
**Risk level:** low
**Testing required:** Unit tests for partial name matching in contador/revisor fiscal validation
