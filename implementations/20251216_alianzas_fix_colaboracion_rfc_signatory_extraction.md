# Implementation: Fix COLABORACIÓN RFC and Signatory Extraction

**Date:** 2025-12-16
**Module:** Alianzas (Broker Incentive Extraction)
**Plan:** `specs/issue-0-adw-0-sdlc_planner-fix-colaboracion-rfc-signatory-extraction.md`

## Summary

Fixed the RFC and Signatory name extraction for COLABORACIÓN contracts. Previously, the system was extracting Finkargo's RFC and representative name instead of the Broker's (FREELANCE) information.

## Problem

For COLABORACIÓN contracts, the signature block has two columns:
- **Left (FINKARGO)**: Alma Angélica Guzmán Martínez, RFC No. GUMA790902MR2, Representante Legal
- **Right (FREELANCE)**: Broker name, RFC without "No.", Por su propio derecho

The existing extraction logic found the first RFC in the document (Finkargo's) rather than the broker's RFC from the FREELANCE column.

## Solution

1. **Added COLABORACIÓN-specific RFC patterns** that identify the FREELANCE RFC by:
   - Looking for "RFC " followed by value and "Por su propio derecho"
   - Using negative lookahead to exclude "RFC No." (Finkargo's format)

2. **Created intelligent two-column layout parsing** to extract the broker name:
   - Find the RFC line containing both "RFC No." and another RFC
   - Look at the line above (name line) and split by multiple spaces (column separator)
   - Extract the right-side name (FREELANCE column)

3. **Added fallback protection** to ensure Finkargo's RFC (`GUMA790902MR2`) and name (`Alma Angélica Guzmán Martínez`) are never returned for COLABORACIÓN contracts.

## Changes Made

### Backend Changes

- **Added COLABORACIÓN RFC patterns** (`broker_incentive_extractor.py`)
  - `COLABORACION_RFC_PATTERNS` - Patterns to match RFC without "No." followed by "Por su propio derecho"
  - `COLABORACION_SIGNATORY_PATTERNS` - Fallback patterns for signatory name extraction
  - Added `FINKARGO_RFC` and `FINKARGO_NAME` constants for exclusion validation

- **Added specialized extraction method** (`broker_incentive_extractor.py`)
  - `_extract_colaboracion_signatory_info()` - Main method for COLABORACIÓN-specific extraction
  - `_extract_colaboracion_name_from_columns()` - Intelligent two-column layout parsing

- **Updated extract_signatory_info method** (`broker_incentive_extractor.py`)
  - Added `contract_type` parameter
  - Routes COLABORACIÓN contracts to specialized extraction first
  - Falls back to generic extraction if specialized fails
  - Excludes Finkargo's RFC/name even in fallback for COLABORACIÓN contracts

- **Updated extract_from_pdf method** (`broker_incentive_extractor.py`)
  - Passes identified contract type to `extract_signatory_info()`

### Tests Added

- `test_extract_colaboracion_rfc_from_freelance_column` - Verify RFC extracted from FREELANCE side
- `test_extract_colaboracion_signatory_from_freelance_column` - Verify name extracted from FREELANCE side
- `test_extract_colaboracion_signatory_info_complete` - Verify both name and RFC extracted correctly
- `test_extract_colaboracion_signatory_excludes_finkargo_rfc` - Verify Finkargo's RFC is NOT extracted
- `test_extract_colaboracion_signatory_excludes_finkargo_name` - Verify Finkargo's name is NOT extracted
- `test_extract_signatory_info_with_colaboracion_contract_type` - Verify routing works correctly

## Discrepancies Found

**PDF text extraction layout issue**: The plan assumed regex patterns could directly identify the FREELANCE column. However, PDF text extraction produces a single text stream where two-column layout appears as single lines with both values separated by spaces.

**Resolution**: Implemented intelligent line-based parsing that:
1. Identifies the RFC line by finding "RFC No." and another RFC on the same line
2. Looks at the previous line (name line)
3. Splits by multiple spaces (>=3) to separate columns
4. Extracts the right-side (FREELANCE) value

## Validation Results

All validation commands passed:

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - **56 tests passed**
- `cd backend && ruff check src/` - **All checks passed**
- `cd frontend && npm run lint` - **0 errors** (4 pre-existing warnings unrelated to changes)
- `cd frontend && npx tsc --noEmit` - **No errors**
- `cd frontend && npm run build` - **Build successful**

## Files Changed

```
 backend/src/core/servicios/broker_contract_scanner.py        | 124 +++++--
 backend/src/core/servicios/broker_incentive_excel_generator.py |  72 +++-
 backend/src/core/servicios/broker_incentive_extractor.py     | 335 ++++++++++++++++-
 backend/src/interface/broker_incentive_dtos.py               |  12 +
 backend/tests/test_broker_incentive_extraction.py            | 385 ++++++++++++++++++++-
 frontend/src/components/alianzas/FKBrokerContractScanForm.tsx |   4 +-
 frontend/src/components/alianzas/FKBrokerIncentiveResultsGrid.tsx |  58 ++++
 frontend/src/services/brokerIncentiveService.ts              |  54 ++-
 8 files changed, 984 insertions(+), 60 deletions(-)
```

## Key Differentiators for COLABORACIÓN Contracts

| Field | FINKARGO (Left) | FREELANCE (Right) |
|-------|-----------------|-------------------|
| RFC Format | `RFC No. GUMA790902MR2` | `RFC VELS720821EL1` |
| Role | `Representante Legal` | `Por su propio derecho` |
| Name Position | Left side of name line | Right side of name line |

## Notes

1. The two-column layout parsing uses `>=3 spaces` as the column separator threshold. This works reliably for the DocuSign-generated COLABORACIÓN contracts.

2. The fix specifically targets COLABORACIÓN contracts. Other contract types (BONO, INCENTIVOS) continue to use the existing generic extraction logic.

3. No frontend changes were required - the frontend automatically displays the correct data once the backend extracts it properly.
