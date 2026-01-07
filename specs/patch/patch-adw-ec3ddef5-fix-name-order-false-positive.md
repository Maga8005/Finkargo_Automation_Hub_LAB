# Patch: Fix legal representative name order false positive

## Metadata
adw_id: `ec3ddef5`
review_change_request: `The logic is raising a false positive in the case that the name and last name are presented in different order between documents. For example, for Glatam, the Legal Representative name extracted from cédula was JOSE DAVID RAMOS DAZA, while in the certificado de existencia, the person shows up as RAMOS DAZA JOSE DAVID. This is the same person only that in the cédula they show up first names and then last names, while in the Certificado this person is listed first with last names and then names. Please adjust the logic so that this false positive is not raised.`

## Issue Summary
**Original Spec:** `app_docs/feature-ec3ddef5-fraud-risk-module-fixes.md`
**Issue:** The cross-validation service's `_names_match` method uses `SequenceMatcher` for fuzzy matching, which does not handle name reordering. When one document shows "JOSE DAVID RAMOS DAZA" (first names then last names) and another shows "RAMOS DAZA JOSE DAVID" (last names then first names), the current algorithm sees them as different names with low similarity score, causing a false positive discrepancy.
**Solution:** Enhance the `_names_match` method to check if two names contain the same set of name parts (tokens) regardless of order. If the tokenized names match exactly (same words, different order), treat them as matching. This handles the common Colombian document pattern where cédulas use "first + last" order while Certificado de Existencia uses "last + first" order.

## Files to Modify
Use these files to implement the patch:

1. `backend/src/core/servicios/risk/cross_validation_service.py` - Modify `_names_match` method to handle name reordering
2. `backend/tests/test_cross_validation_improvements.py` - Add test case for name order matching

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_names_match` method in cross_validation_service.py
- Modify the `_names_match` method (around line 1012-1019)
- Before the existing fuzzy matching logic, add a check that tokenizes both names and compares the token sets
- If the token sets are identical (same name parts, different order), return `True` immediately
- Fall back to existing `SequenceMatcher` fuzzy matching for cases where names have minor spelling variations

**Implementation logic:**
```python
def _names_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
    """Check if two names match with fuzzy matching and name order tolerance."""
    if not name1 or not name2:
        return False
    if name1 == name2:
        return True

    # NEW: Check for same name parts in different order
    # Handles: "JOSE DAVID RAMOS DAZA" vs "RAMOS DAZA JOSE DAVID"
    tokens1 = set(name1.split())
    tokens2 = set(name2.split())
    if tokens1 == tokens2:
        return True

    # Existing fuzzy matching for spelling variations
    similarity = SequenceMatcher(None, name1, name2).ratio()
    return similarity >= threshold
```

### Step 2: Add test case to test_cross_validation_improvements.py
- Add a new test case that verifies the name order matching works correctly
- Test cases should include:
  - "JOSE DAVID RAMOS DAZA" vs "RAMOS DAZA JOSE DAVID" (should match)
  - "MARIA FERNANDA LOPEZ GARCIA" vs "LOPEZ GARCIA MARIA FERNANDA" (should match)
  - "JOSE RAMOS" vs "DAVID RAMOS" (should NOT match - different name parts)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Backend linting:**
   ```bash
   cd backend && ./venv/bin/ruff check src/core/servicios/risk/cross_validation_service.py
   ```

2. **Backend pytest:**
   ```bash
   cd backend && python -m pytest tests/test_cross_validation_improvements.py -v --tb=short
   ```

3. **Full backend tests:**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

4. **Frontend TypeScript check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend build:**
   ```bash
   cd frontend && npm run build
   ```

## Patch Scope
**Lines of code to change:** ~15
**Risk level:** low
**Testing required:** Unit tests for name matching, integration tests for cross-validation
