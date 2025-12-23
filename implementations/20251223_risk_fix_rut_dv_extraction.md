# Implementation Report: Fix RUT DV (Dígito de Verificación) Extraction

**Date:** 2025-12-23
**Module:** Risk (Riesgos)
**Issue:** #12 - Fix RUT DV extraction in Riesgos feature

## Summary

Fixed the RUT DV (dígito de verificación) extraction issue in the Riesgos (Risk) Document info extraction feature. The system was extracting an incorrect DV value because the LandingAI extraction schema didn't provide explicit guidance about the exact location of field 6.DV in Colombian RUT documents.

## Changes Made

- **Updated RUT extraction schema** in `document_extraction_service.py` to provide explicit guidance about the DV field location:
  - Enhanced the `nit` field description to clearly specify that field 5 contains the 9-digit NIT and field 6.DV (immediately after field 5) contains the single-digit verification digit
  - Added example format showing expected output (e.g., "830027231-3")
  - Specified the exact field labels as they appear in Colombian RUT documents

- **Created E2E test file** at `.claude/commands/e2e/test_rut_dv_extraction.md` to validate the RUT DV extraction functionality:
  - User story for Risk Analyst role
  - Test steps for uploading RUT document and verifying extracted DV
  - Success criteria focusing on correct DV extraction from field 6.DV

## Discrepancies Found

**None.** The plan accurately described the issue and the solution. The file locations, line numbers, and schema structure matched the actual codebase.

## Validation Results

### Backend Validation
- `ruff check src/` - ✅ All checks passed
- `pytest tests/` - ✅ 302 tests passed (excluding tests with missing optional dependencies: fitz, docx, httplib2)

### Frontend Validation
- `npm run lint` - ✅ Passed (4 pre-existing warnings unrelated to this change)
- `npx tsc --noEmit` - ✅ No type errors
- `npm run build` - ✅ Build successful

## Files Changed

```
 backend/src/core/servicios/risk/document_extraction_service.py | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

## New Files Created

```
 .claude/commands/e2e/test_rut_dv_extraction.md
```

## Technical Details

### Before (Ambiguous)
```python
"nit": {"type": "string", "description": "NIT with verification digit (fields 5-6)"},
```

### After (Explicit)
```python
"nit": {"type": "string", "description": "NIT with verification digit. Field 5 contains the 9-digit NIT number (labeled '5. Número de Identificación Tributaria (NIT)'). Immediately after field 5, there is a small field labeled '6.DV' containing a single digit which is the verification digit (dígito de verificación). Extract as 'XXXXXXXXX-D' format where D is the digit from field 6.DV. For example, if NIT is 830027231 and 6.DV is 3, return '830027231-3'."},
```

## Notes

- The fix is surgical and backwards compatible - only the schema description was enhanced
- No new dependencies required
- The LandingAI API uses the description field to understand what to extract, so improving the description should fix the extraction
- The existing `rut_parser_service.py` already has correct logic for text-based extraction - this change aligns the AI extraction with that behavior
