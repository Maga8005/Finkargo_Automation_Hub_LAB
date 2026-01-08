# Fraud Risk Module Bug Fixes

**ADW ID:** ec3ddef5
**Date:** 2025-12-25
**Specification:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md

## Overview

This release addresses five bugs in the fraud risk module: increased file size limits for Certificado de Existencia uploads, fixed NIT normalization causing validation errors, added Colombian cellphone filtering to prevent false positives, corrected domain validation source logic, and ensured domain validation status always displays.

## What Was Built

- Increased Certificado de Existencia file size limit from 10MB to 50MB
- Fixed NIT normalization tuple-to-string conversion in email chain validation
- Added Colombian cellphone number detection to filter false positive NIT matches
- Fixed RUT domain as authoritative source for typosquatting validation
- Added INFO severity level for positive domain validation status display
- Fixed external contact domain validation field mapping

## Technical Implementation

### Files Modified

- `frontend/src/types/risk.ts`: Increased `certificado_existencia.max_size_mb` from 10 to 50; added `info` to `DiscrepancySeverity` type; added `info_count` to `EmailChainValidationResult`
- `backend/src/core/servicios/risk/email_chain_service.py`: Fixed tuple unpacking from `normalize_nit()` in `_get_document_data()` and `_validate_nit_mention()`; added INFO-level domain validation results
- `backend/src/core/servicios/risk/email_chain_parser_service.py`: Added `is_colombian_cellphone()` method and filtering in NIT extraction
- `backend/src/core/servicios/risk/cross_validation_service.py`: Removed company-name-derived domain from typosquatting check; RUT email domain is now authoritative
- `frontend/src/components/risk/FKCrossValidationResults.tsx`: Fixed field mapping for external contact domain validation display

### Key Changes

- **NIT Normalization Fix**: The `normalize_nit()` function returns a tuple `(base_digits, check_digit)`. Code now properly unpacks and formats as `"base-check"` string before storing in discrepancy objects.

- **Cellphone Filtering**: New `is_colombian_cellphone()` method detects 10-digit numbers starting with mobile prefixes (30x, 31x, 32x, 35x, 36x) to prevent them from being incorrectly flagged as NIT mentions.

- **Domain Validation Source**: Cross-validation now uses only the RUT email domain as the authoritative source. Previously, deriving domains from company names caused false positives (e.g., "company.com" flagged when RUT has "company.com.co").

- **INFO Severity Level**: Domain validation now returns INFO-level discrepancies for verified domains instead of returning `None`, ensuring positive validation status is always displayed.

- **Discrepancy Count Logic**: `total_discrepancies` now excludes INFO-level items, counting only actual issues (critical/high/medium/low).

## How to Use

1. **Upload Large Documents**: Navigate to Risk Evaluation, upload Certificado de Existencia files up to 50MB without size errors.

2. **Email Chain Validation**: Upload email chains containing NIT mentions. The system now correctly validates without Pydantic errors about list vs string types.

3. **Cellphone Filtering**: NITs in emails that match Colombian cellphone patterns (e.g., 3001234567) are automatically filtered out and not flagged as discrepancies.

4. **Domain Validation**: Cross-validation shows domain verification status for external contacts. Verified domains display as INFO-level positive indicators.

## Configuration

No new environment variables required. File size limit is configured in `DOCUMENT_TYPE_CONFIG`:

```typescript
certificado_existencia: {
  max_size_mb: 50,  // Previously 10
}
```

## Testing

### Validation Commands

```bash
# Backend
cd backend && ruff check src/
cd backend && python -m pytest

# Frontend
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

### Manual Verification

1. Upload a 30MB PDF as Certificado de Existencia - should succeed
2. Upload email chain with NIT like "830.116.134-9" - should validate without errors
3. Upload email mentioning cellphone "3001234567" - should not be flagged as NIT
4. Check external contact validation shows domain age/existence info

### E2E Test

```bash
# Run E2E test for fraud risk module fixes
/test_e2e test_fraud_risk_module_fixes
```

## Notes

- The NIT normalization fix resolves the Pydantic validation error: `Input should be a valid string [type=string_type, input_value=['830116134', '9'], input_type=list]`

- Colombian cellphone detection covers mobile prefixes: 300-309, 310-319, 320-329, 350-359, 360-369

- RUT email domain is considered authoritative because it comes from an official government document (DIAN registration)

- INFO-level discrepancies have green styling (`#E0F7E6` background, `#2CA14D` text) to indicate positive verification
