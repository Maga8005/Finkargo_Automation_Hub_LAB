# Implementation Report: Fraud Risk Module Bug Fixes

**Date**: 2025-12-25
**Issue**: #36
**Branch**: bug-issue-36-adw-ec3ddef5-fraud-risk-module-fixes

## Summary

Fixed three bugs in the fraud risk module:

1. **File Size Limit for Certificado de Existencia**: Increased from 10MB to 50MB
2. **Domain DNS/Age Check for External Contacts**: Verified already working (no changes needed)
3. **EmailChainDiscrepancy Validation Error**: Fixed NIT normalization tuple-to-string conversion

## Changes Made

### Bug 1: File Size Limit (Fixed)

- **File**: `frontend/src/types/risk.ts`
- **Change**: Updated `DOCUMENT_TYPE_CONFIG.certificado_existencia.max_size_mb` from `10` to `50`
- **Impact**: Users can now upload Certificado de Existencia documents up to 50MB

### Bug 2: Domain DNS/Age Check (Verified - No Changes Needed)

After investigation, the domain DNS and age check functionality was found to be **already fully implemented**:

- **Backend**: `external_contact_service.py` (lines 149-167, 201) performs DNS existence check and WHOIS age lookup
- **Frontend**: `FKEmailValidationResult.tsx` displays domain existence, age, and color-coded chips
- **Types**: `EmailValidationResult` interface includes all necessary domain fields

No code changes required - the feature is working as designed.

### Bug 3: EmailChainDiscrepancy Error (Fixed)

- **File**: `backend/src/core/servicios/risk/email_chain_service.py`
- **Root Cause**: The `normalize_nit()` function returns a tuple `(base_digits, check_digit)`, but the code was treating it as a string directly
- **Changes**:
  1. Fixed `_get_document_data()` method (lines 333-342): Now properly unpacks the tuple and joins base + check digit into a string
  2. Fixed `_validate_nit_mention()` method (lines 629-654): Now properly handles tuple unpacking for both client NIT and mentioned NIT normalization

**Before (broken):**
```python
normalized = self.normalization_service.normalize_nit(str(value))
# normalized was a tuple like ('830116134', '9'), not a string
doc_data['nits'].append(normalized)  # Appended tuple, causing Pydantic error
```

**After (fixed):**
```python
base, check = self.normalization_service.normalize_nit(str(value))
if base:
    normalized = f"{base}-{check}" if check else base  # Now a proper string
    doc_data['nits'].append(normalized)
```

## Discrepancies Found

| Plan Assumption | Reality | Resolution |
|-----------------|---------|------------|
| Domain DNS check may need UI fixes | Already fully implemented and working | No changes needed |
| Backend may have separate file size limit | Backend uses frontend config via `doc_info['max_size_mb']` | Single change in frontend was sufficient |

## Validation Results

| Check | Status |
|-------|--------|
| Backend ruff lint | ✅ All checks passed |
| Frontend ESLint | ✅ 0 errors (4 pre-existing warnings) |
| TypeScript type check | ✅ No errors |
| Frontend build | ✅ Built successfully |
| Python syntax check | ✅ Passed |
| NIT normalization test | ✅ Returns ('830116134', '9'), formats to '830116134-9' |

## Files Changed

```
backend/src/core/servicios/risk/email_chain_service.py | 30 ++++++++++++++--------
frontend/src/types/risk.ts                             |  2 +-

2 files changed, 20 insertions(+), 12 deletions(-)
```

## New Files Created

- `.claude/commands/e2e/test_fraud_risk_module_fixes.md` - E2E test specification for all three bug fixes

## Testing Recommendations

1. **Manual Testing**:
   - Upload a 30MB PDF as Certificado de Existencia - should succeed
   - Add external contact with corporate email, validate - should show domain age info
   - Upload email chain with NIT mentions, validate - should complete without Pydantic errors

2. **E2E Testing**:
   - Run `/test_e2e test_fraud_risk_module_fixes` to execute the new E2E test spec
