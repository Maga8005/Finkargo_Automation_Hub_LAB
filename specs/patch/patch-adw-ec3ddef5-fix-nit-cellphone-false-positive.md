# Patch: Fix NIT vs Cellphone False Positive Detection

## Metadata
adw_id: `ec3ddef5`
review_change_request: `Fix email chain validation false positive where Colombian cellphone numbers are incorrectly detected as NITs and compared against the actual NIT, raising false fraud alerts.`

## Issue Summary
**Original Spec:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md
**Issue:** The email chain NIT extraction pattern matches Colombian cellphone numbers (e.g., `3174305472`) because they are 10 digits. When the validation compares this "NIT mention" against the actual NIT (`830116134-9`), it raises a false positive CRITICAL alert saying the NITs don't match.

**Solution:** Add cellphone number filtering to the NIT extraction logic. Colombian cellphone numbers have a distinct format (10 digits starting with `31`, `32`, `30`, `35`, or `36`) that can be easily differentiated from NITs (6-10 digits followed by check digit).

## Root Cause Analysis

1. **NIT Pattern** in `email_chain_parser_service.py`:
   ```python
   NIT_PATTERN = r'\b(\d{3}\.?\d{3}\.?\d{3}[-\s]?\d|\d{9}[-\s]?\d)\b'
   ```
   This matches: `XXX.XXX.XXX-X` or `XXXXXXXXX-X`

2. **Cellphone Pattern**: `3174305472` is 10 digits, which matches the pattern as 9 base digits + 1 "check digit"

3. **Colombian Cellphone Format**:
   - 10 digits total
   - Starts with `3` followed by `0`, `1`, `2`, `5`, or `6` (mobile prefixes: 310-319, 320-329, 300-309, 350-359, 360-369)
   - Sometimes prefixed with country code: `+57` or `57`

4. **Colombian NIT Format**:
   - 6 to 10 base digits (typically 9 for companies)
   - Followed by a check digit after `-` separator
   - Does NOT start with `3` followed by typical mobile prefixes

## Files to Modify

1. `backend/src/core/servicios/risk/email_chain_parser_service.py` - Add cellphone filtering to NIT extraction

## Implementation Steps

### Step 1: Add Colombian Cellphone Pattern and Filter Logic

In `email_chain_parser_service.py`, add a helper method to detect Colombian cellphone numbers and filter them out from NIT matches.

**Add cellphone detection pattern after the NIT_PATTERN constant (around line 46):**
```python
# Colombian cellphone pattern: 10 digits starting with 3 (mobile prefixes 30x, 31x, 32x, 35x, 36x)
# May have country code prefix: +57 or 57
COLOMBIAN_CELLPHONE_PATTERN = r'(?:\+?57\s*)?(?:3[0-26-9]\d{8})\b'
```

**Add helper method after `is_free_email_provider` method (around line 684):**
```python
def is_colombian_cellphone(self, number: str) -> bool:
    """
    Check if a number string is a Colombian cellphone number.

    Colombian cellphones:
    - 10 digits total
    - Start with 3 followed by 0, 1, 2, 5, or 6 (mobile prefixes)
    - May have +57 or 57 country code prefix

    Args:
        number: Normalized number string (digits only)

    Returns:
        bool: True if matches Colombian cellphone pattern
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'[^\d]', '', number)

    # Check for country code prefix and remove it
    if digits_only.startswith('57') and len(digits_only) == 12:
        digits_only = digits_only[2:]

    # Must be exactly 10 digits
    if len(digits_only) != 10:
        return False

    # Must start with 3 followed by mobile prefix (0, 1, 2, 5, 6)
    # Mobile prefixes: 300-309, 310-319, 320-329, 350-359, 360-369
    if digits_only[0] == '3' and digits_only[1] in '01256':
        return True

    return False
```

### Step 2: Update NIT Extraction to Filter Cellphones

In the `_extract_mentions_from_body` method (around line 634), add filtering after NIT matches are found:

**Before (current code):**
```python
# Extract NITs
nit_matches = re.findall(self.NIT_PATTERN, body)
for nit in nit_matches:
    # Normalize NIT format
    normalized = re.sub(r'[.\s]', '', nit)
    if normalized not in mentions['nits']:
        mentions['nits'].append(normalized)
```

**After (with cellphone filtering):**
```python
# Extract NITs
nit_matches = re.findall(self.NIT_PATTERN, body)
for nit in nit_matches:
    # Normalize NIT format (remove dots and spaces)
    normalized = re.sub(r'[.\s]', '', nit)

    # Filter out Colombian cellphone numbers (10 digits starting with 3)
    # Cellphones look like NITs but have distinct patterns
    if self.is_colombian_cellphone(normalized):
        logger.debug(f"Filtered cellphone number from NIT matches: {normalized}")
        continue

    if normalized not in mentions['nits']:
        mentions['nits'].append(normalized)
```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Backend Linting**
   ```bash
   cd backend && ./venv/bin/ruff check src/core/servicios/risk/email_chain_parser_service.py
   ```

2. **Python Syntax Check**
   ```bash
   cd backend && python -c "from src.core.servicios.risk.email_chain_parser_service import EmailChainParserService; print('Import OK')"
   ```

3. **Unit Test - Verify Cellphone Filtering**
   ```bash
   cd backend && python -c "
from src.core.servicios.risk.email_chain_parser_service import EmailChainParserService
parser = EmailChainParserService()

# Test cellphone detection
assert parser.is_colombian_cellphone('3174305472') == True, 'Should detect 317 prefix'
assert parser.is_colombian_cellphone('3001234567') == True, 'Should detect 300 prefix'
assert parser.is_colombian_cellphone('3154567890') == True, 'Should detect 315 prefix'
assert parser.is_colombian_cellphone('573174305472') == True, 'Should detect with 57 prefix'

# Test NIT patterns (should NOT be filtered as cellphones)
assert parser.is_colombian_cellphone('830116134') == False, '9-digit NIT should not match'
assert parser.is_colombian_cellphone('8301161349') == False, 'NIT starting with 8 should not match'
assert parser.is_colombian_cellphone('1234567890') == False, '10-digit not starting with 3 should not match'
assert parser.is_colombian_cellphone('3741234567') == False, '374 is not a valid mobile prefix'

print('All cellphone detection tests passed!')
"
   ```

4. **Integration Test - Verify NIT Extraction Filtering**
   ```bash
   cd backend && python -c "
from src.core.servicios.risk.email_chain_parser_service import EmailChainParserService
parser = EmailChainParserService()

# Test that cellphone is filtered from NIT extraction
body_with_cellphone = '''
Contacto: 3174305472
NIT: 830.116.134-9
Empresa: Petroworks S.A.S
'''
result = parser.parse_raw_text(body_with_cellphone)
mentions = result['mentions']
print(f'Extracted NITs: {mentions[\"nits\"]}')

# Verify cellphone is NOT in NITs
assert '3174305472' not in mentions['nits'], 'Cellphone should be filtered from NITs'
assert '317430547-2' not in mentions['nits'], 'Cellphone with check digit should be filtered'

# Verify actual NIT IS extracted
assert any('830116134' in nit for nit in mentions['nits']), 'Real NIT should be extracted'

print('NIT extraction filtering test passed!')
"
   ```

5. **Run All Backend Tests**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

6. **Frontend Linting** (ensure no impact)
   ```bash
   cd frontend && npm run lint
   ```

7. **Frontend TypeScript Check** (ensure no impact)
   ```bash
   cd frontend && npx tsc --noEmit
   ```

## Patch Scope
**Lines of code to change:** ~25
**Risk level:** low
**Testing required:** Unit tests for cellphone detection, integration test for NIT extraction filtering
