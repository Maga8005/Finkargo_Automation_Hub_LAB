# Implementation Report: DIAN Checkbox for Instruccion de Mandato

**Date:** 2025-12-12
**Module:** Operations / Paga Local Colombia
**Feature:** DIAN Checkbox with Auto-Wording for Instruccion de Mandato
**Issue:** #99

## Summary

Enhanced the Instruccion de Mandato document generation form to support mixed creditor types (DIAN and non-DIAN) within a single document. Previously, users had to use two separate forms - one for DIAN payments and one for generic creditors with bank certificates.

## Changes Made

### Backend Changes

1. **Updated DTOs** (`backend/src/interface/legal_dtos.py`)
   - Added `es_dian: bool = False` field to `AcreedorGastosNacionales` model
   - Allows creditors to be flagged as DIAN payments for conditional handling

2. **Added DIAN Constants** (`backend/src/core/servicios/document_service.py`)
   - Added `DIAN_WORDING` constant: "Transferencia electronica PSE a favor de la DIAN"
   - Added `DIAN_KEYWORDS` list for auto-detection patterns

3. **Updated Creditor Table Population** (`backend/src/core/servicios/document_service.py`)
   - Modified `_populate_acreedores_table` method to handle DIAN creditors
   - For DIAN creditors (`es_dian=True`):
     - Sets `razon_social` to DIAN_WORDING constant
     - Sets `nit` to "N/A"
     - Sets `banco` to "DIAN"
     - Sets `tipo_cuenta` to "PSE"
     - Sets `numero_cuenta` to "N/A"
   - Non-DIAN creditors use provided data as before

### Frontend Changes

1. **Updated TypeScript Types** (`frontend/src/types/legal.ts`)
   - Added `es_dian?: boolean` to `AcreedorGastosNacionales` interface

2. **Enhanced Form Component** (`frontend/src/components/forms/FKInstruccionMandatoForm.tsx`)
   - Added DIAN detection helper function `isDianCreditor()`
     - Uses word boundary matching for "DIAN" to prevent false positives (e.g., "GUARDIAN")
   - Added `handleDianToggle()` function for checkbox state management
   - Updated `handleExtractCotizacion()` to auto-detect DIAN creditors on PDF extraction
   - Updated `validateAcreedores()` to skip bank cert validation for DIAN creditors
   - Updated creditor card UI with:
     - "Es DIAN" checkbox at top of each creditor card
     - Visual indicator (DIAN chip/badge) when checked
     - Conditional rendering: read-only info for DIAN, editable fields for non-DIAN
     - Bank certificate upload hidden for DIAN creditors
     - Info alert explaining auto-filled DIAN data

3. **Created E2E Test** (`.claude/commands/e2e/test_dian_checkbox_instruccion_mandato.md`)
   - Comprehensive test covering DIAN checkbox functionality
   - Tests auto-detection, toggle behavior, mixed creditors, and document generation

## Acceptance Criteria Met

- [x] Each creditor row has "Es DIAN" checkbox visible
- [x] Checking DIAN auto-fills predefined wording
- [x] Checking DIAN disables bank certificate upload for that row
- [x] Checking DIAN auto-fills: banco="DIAN", tipo_cuenta="PSE", numero_cuenta="N/A"
- [x] Unchecked rows require bank certificate upload
- [x] Multiple mixed creditors (DIAN + non-DIAN) can be added to single document
- [x] Account type correctly shows "PSE" for DIAN (not "PC")
- [x] DIAN auto-detection works based on creditor name patterns
- [x] User can manually override auto-detection (toggle DIAN checkbox)

## Discrepancies Found and Resolved

None. The plan was accurate and no discrepancies were found during implementation:
- Template placeholders matched the documented format
- Data types aligned between frontend and backend
- Repository patterns used dict access as expected

## Validation Results

| Command | Result |
|---------|--------|
| `cd backend && pytest tests/ -v` | 227 tests passed |
| `cd backend && ruff check src/` | Pre-existing warnings only (not related to this feature) |
| `cd frontend && npm run lint` | 4 pre-existing warnings only |
| `cd frontend && npx tsc --noEmit` | Passed |
| `cd frontend && npm run build` | Build successful |

## Files Changed

```
backend/src/core/servicios/document_service.py     |  37 ++-
backend/src/interface/legal_dtos.py                |   1 +
frontend/src/components/forms/FKInstruccionMandatoForm.tsx  | 355 +++++++++++++-----
frontend/src/types/legal.ts                        |   1 +
4 files changed, 302 insertions(+), 92 deletions(-)
```

## New Files Created

- `.claude/commands/e2e/test_dian_checkbox_instruccion_mandato.md` - E2E test for the feature

## Testing Notes

- Backend tests pass without modification (field is optional with default)
- E2E test created for manual testing of the complete workflow
- The `isDianCreditor()` function uses word boundary regex to prevent false positives

## Future Considerations

- Consider adding visual indicator (icon/badge) for auto-detected DIAN creditors
- Consider adding bulk "Mark all as DIAN" action if common use case
- The separate `FKDIANMandatoForm` can be deprecated in the future once this unified form is validated in production
