# Implementation Report: Use RUT Email Domain as Official Source

## Date
2025-12-25

## ADW ID
`ec3ddef5`

## Summary
Fixed typosquatting detection to use the RUT email domain as the authoritative source instead of deriving an expected `.com` domain from the company name.

## Problem
The fraud risk module was incorrectly flagging "TLD variation" alerts when a company's RUT document had an email domain like `petroworks.com.co`, but the system derived `petroworks.com` as the expected domain from the company name. This created false positives because the RUT document IS the official government source - the domain in it should be considered legitimate, not suspicious.

## Solution
Removed the `company_name` parameter from the `check_domain_typosquatting` call in `_validate_email_domain`. The RUT email domain is now treated as authoritative. Typosquatting detection only flags domains that are similar to known large company domains (like `azelis.com`, `basf.com`, etc.) but not company-name-derived domains.

## Changes Made

- **backend/src/core/servicios/risk/cross_validation_service.py** (lines 695-707)
  - Removed unused `company_name` variable assignment
  - Added explanatory comments about why company name derivation is skipped
  - Removed `company_name` parameter from `check_domain_typosquatting()` call

## Files Changed
```
backend/src/core/servicios/risk/cross_validation_service.py | 14 ++++++++------
1 file changed, 8 insertions(+), 6 deletions(-)
```

## Discrepancies Between Plan and Reality
None - the plan accurately described the issue and solution.

## Validation Results
All validation commands passed:

1. **Python Syntax Check** - Passed
2. **Backend Linting (ruff)** - All checks passed
3. **Typosquatting Service Tests** - 33/33 passed
4. **Cross Validation Tests** - 25/25 passed
5. **All Backend Tests** - 472/472 passed

## Test Coverage
Existing tests continue to verify:
- Typosquatting detection for actual typosquatting cases (e.g., `acelis.com.co` vs `azelis.com`)
- Free email provider flagging
- Legitimate corporate domains not being flagged
- TLD variation detection for known large company domains

## Risk Assessment
- **Risk Level:** Low
- **Impact:** Reduces false positive TLD variation alerts for companies with country-specific domains
- **Backward Compatibility:** Full - no API changes, only internal logic fix
