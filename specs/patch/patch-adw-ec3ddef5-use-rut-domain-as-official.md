# Patch: Use RUT Email Domain as Official Source

## Metadata
adw_id: `ec3ddef5`
review_change_request: `The RUT document is one of the two official documents obtained from government entities in the current workflow. The domain obtained from the notifications email listed in the RUT should be taken as a source against which to compare. The system is raising an alert expecting the domain to be petroworks.com, but the RUT document is showing that the official domain is petroworks.com.co. The logic is incorrectly assuming the correct domain should be .com instead of the official domain from the RUT.`

## Issue Summary
**Original Spec:** N/A (Fraud Risk Module)
**Issue:** The `_derive_domain_from_company` method in `typosquatting_service.py` derives an expected domain by taking the company name and appending `.com` (e.g., "PETROWORKS" → "petroworks.com"). This creates false positives when the actual official domain from the RUT is a different TLD like `.com.co`. The RUT document should be the authoritative source for the company's official domain, not an assumption of `.com`.
**Solution:** Modify the typosquatting detection logic to prioritize the domain extracted from the RUT document as the authoritative "known domain" instead of deriving an expected `.com` domain from the company name. When a domain is extracted from official documents (RUT, Certificado de Existencia), it should be used as the expected domain, and only fall back to deriving a domain when no official domain is available.

## Files to Modify

1. `backend/src/core/servicios/risk/typosquatting_service.py` - Modify `_derive_domain_from_company` to return `None` when not needed (preventing false `.com` assumptions)
2. `backend/src/core/servicios/risk/cross_validation_service.py` - Update `_validate_email_domain` to use the RUT-extracted domain as the official reference instead of relying on company name derivation

## Implementation Steps

### Step 1: Update `_validate_email_domain` in `cross_validation_service.py` to prioritize RUT domain
- In the `_validate_email_domain` method (line 670-787), the current logic passes `company_name` to `check_domain_typosquatting` which derives a `.com` domain
- Modify the logic to:
  1. Extract the domain from the RUT's email field first (this is already done on line 691)
  2. Use this RUT-extracted domain as the "known official domain" for the company
  3. Only call `check_domain_typosquatting` with `known_domains` populated from actual document extractions, NOT from company name derivation
  4. Remove or skip passing `company_name` to `check_domain_typosquatting` since the RUT domain is the authoritative source

### Step 2: Update `_validate_email_domain` method signature and logic
- The method should recognize that when the email domain from the RUT matches what we're checking, there's no discrepancy
- If the RUT has email `info@petroworks.com.co`, then `petroworks.com.co` IS the official domain
- Only flag typosquatting when the domain being validated differs from the RUT's official domain
- Adjust the code so the `known_domains` list is populated from official document domains, not derived from company name

### Step 3: Update `check_domain_typosquatting` call to not pass `company_name`
- In `_validate_email_domain` around lines 700-705, the current code passes `company_name=company_name` which causes derivation of `.com` domains
- Remove the `company_name` parameter from the call since we should use the actual document-extracted domains
- The `known_domains` parameter already includes domains extracted from documents via `self.typosquatting.DEFAULT_KNOWN_DOMAINS`
- The fix is to NOT derive a domain from company name when we already have official document domains

### Step 4: Verify the fix logic
- When processing the RUT document:
  - If RUT has email `info@petroworks.com.co`, the domain is `petroworks.com.co`
  - This domain should be added to the known/official domains list
  - Any subsequent validation against this domain should recognize it as legitimate
  - Only flag typosquatting if someone uses a similar but different domain (e.g., `petrworks.com.co` with typo)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check**
   ```bash
   cd backend && python -m py_compile src/core/servicios/risk/cross_validation_service.py
   ```

2. **Backend Linting**
   ```bash
   cd backend && ./venv/bin/ruff check src/core/servicios/risk/
   ```

3. **Backend Tests - Typosquatting Service**
   ```bash
   cd backend && python -m pytest tests/test_typosquatting_service.py -v --tb=short
   ```

4. **Backend Tests - Cross Validation**
   ```bash
   cd backend && python -m pytest tests/test_cross_validation_improvements.py -v --tb=short
   ```

5. **All Backend Tests**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

## Patch Scope
**Lines of code to change:** ~10-15 lines
**Risk level:** Low - targeted change to domain derivation logic without affecting other fraud detection rules
**Testing required:** Run existing typosquatting and cross-validation tests to verify the fix works correctly without breaking other detection logic. Specifically verify that:
- Domains extracted from RUT are treated as official/legitimate
- Typosquatting detection still works for actual typosquatting cases (e.g., `petrworks.com.co` vs `petroworks.com.co`)
- TLD variation warnings are not raised when the domain matches the RUT document
