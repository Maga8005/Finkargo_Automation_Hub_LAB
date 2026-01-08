# Implementation: Add [NIT] Placeholder to Solicitud de Desembolso Template

## Date
2025-12-07

## Summary
Added support for the `[NIT]` placeholder in the Solicitud de Desembolso document generation. The template was updated to include this placeholder, and the backend now populates it with the client's tax identification number.

## Changes Made

- **Updated `_prepare_solicitud_desembolso_replacements` method** in `document_service.py`:
  - Added `'[NIT]': data.get('nit', '')` to the replacements dictionary (line 1284)
  - Updated method docstring to document the `[NIT]` placeholder (line 1240)

## Files Changed

| File | Lines Changed | Description |
|------|---------------|-------------|
| `backend/src/core/servicios/document_service.py` | +4 lines | Added `[NIT]` placeholder support |

## Validation Results

All validation commands passed:

- `cd backend && python -m pytest` - **27/27 tests passed**
- `cd backend && ruff check src/` - **All checks passed**
- `cd frontend && npm run lint` - **Passed**
- `cd frontend && npx tsc --noEmit` - **Passed**
- `cd frontend && npm run build` - **Built successfully**

## Technical Details

The NIT data was already available in the data snapshot (set in `operations_routes.py` line 278: `"nit": client['nit']`). The fix was simply adding the placeholder mapping to the `_prepare_solicitud_desembolso_replacements` method, following the same pattern used in other methods like `_prepare_replacements` (line 651) and `_prepare_otrosi_replacements` (line 727).

## Related Files

- Plan: `specs/issue-0-adw-0-sdlc_planner-add-nit-placeholder-solicitud-desembolso.md`
- Template: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
