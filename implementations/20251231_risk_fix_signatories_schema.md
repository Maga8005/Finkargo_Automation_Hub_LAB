# Implementation Report: Fix LandingAI Signatories Schema Validation

## Summary

Fixed LandingAI ADE API schema validation error for the `signatories` field in financial statement extraction schemas. The API was rejecting requests with error:

> "Schema validation failed: Type list at root.signatories cannot contain 'object' or 'array'"

## Changes Made

- Changed `signatories` field type from `["array", "null"]` to `"array"` in:
  - `FINANCIAL_STATEMENT_CURRENT` schema (line 39)
  - `FINANCIAL_STATEMENT_PRIOR` schema (line 73)

This aligns with the working pattern used by other array fields (`shareholders`, `board_members`, `legal_representatives`) which use `"type": "array"` without the nullable type union.

## Files Changed

```
backend/src/core/servicios/risk/document_extraction_service.py | 4 ++--
1 file changed, 2 insertions(+), 2 deletions(-)
```

## Discrepancies Found

**None.** The plan was accurate:
- Line numbers matched the actual file
- The problematic `["array", "null"]` types were found exactly as specified
- The fix pattern matches other working array fields in the same file

## Validation Results

| Check | Status |
|-------|--------|
| Python Syntax | PASSED |
| Ruff Linting | PASSED (All checks passed!) |
| Unit Tests | PASSED (35/35 tests) |
| Import Validation | PASSED |
| Schema Type Verification | PASSED (`"array"` for both schemas) |

## Related

- **ADW ID:** b0a5e4a8
- **Patch Spec:** `specs/patch/patch-adw-b0a5e4a8-fix-signatories-schema.md`
- **Original Issue:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md
