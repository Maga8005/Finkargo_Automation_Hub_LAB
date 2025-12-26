# Patch: Increase Certificado de Existencia File Size Limit

**Date:** 2025-12-25
**ADW ID:** ec3ddef5
**Type:** Patch

## Summary

Increased the backend file size limit for `CERTIFICADO_EXISTENCIA` (Camara de Comercio) document type from 10MB to 50MB to align with the frontend configuration and allow larger documents to be uploaded.

## Changes Made

- Updated `max_size_mb` from `10` to `50` for `CERTIFICADO_EXISTENCIA` in `DocumentExtractionService.get_document_type_info()` method

## File Modified

| File | Change |
|------|--------|
| `backend/src/core/servicios/risk/document_extraction_service.py` | Changed `max_size_mb: 10` to `max_size_mb: 50` (line 482) |

## Validation Results

| Check | Result |
|-------|--------|
| Backend Linting (ruff) | Passed |
| Frontend Linting (ESLint) | Passed (warnings only, pre-existing) |
| TypeScript Type Check | Passed |
| Frontend Build | Passed |

## Discrepancies

None found. The plan accurately described:
- The location of the file size configuration (line 479-484)
- The current value (10MB) and target value (50MB)
- The frontend configuration at `frontend/src/types/risk.ts` line 451 which already has 50MB

## Git Diff Statistics

```
backend/src/core/servicios/risk/document_extraction_service.py | 2 +-
1 file changed, 1 insertion(+), 1 deletion(-)
```

## Testing Notes

- Backend pytest was not available in the current environment
- Manual testing recommended: Upload a ~14MB Camara de Comercio PDF to verify the fix works in production
