# Chore: Add [NIT] Placeholder Support to Solicitud de Desembolso Template

## Chore Description
The Solicitud de Desembolso Word template has been updated to include a `[NIT]` placeholder that should display the client's NIT (tax identification number). The backend `_prepare_solicitud_desembolso_replacements` method needs to be updated to include this placeholder in its replacement dictionary so that the NIT is properly populated in the generated document.

Currently:
- The data snapshot already contains the `nit` field (extracted from client data in `operations_routes.py` line 278)
- Other document generation methods (`_prepare_replacements`, `_prepare_otrosi_replacements`) already support `[NIT]` placeholder
- The `_prepare_solicitud_desembolso_replacements` method does NOT include `[NIT]` in its replacements dictionary

The fix is straightforward: add the `[NIT]` placeholder to the replacements dictionary in `_prepare_solicitud_desembolso_replacements`.

## Relevant Files
Use these files to resolve the chore:

- `backend/src/core/servicios/document_service.py` - Contains the `_prepare_solicitud_desembolso_replacements` method (lines 1234-1302) that needs to be updated to include the `[NIT]` placeholder. This is the only file that needs modification.

**Reference files (no changes needed):**
- `backend/src/adapter/rest/operations_routes.py` - Shows that `nit` is already included in the data snapshot (line 278: `"nit": client['nit']`)
- `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx` - The Word template that contains the `[NIT]` placeholder (binary file, cannot read directly)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update the _prepare_solicitud_desembolso_replacements Method

- Open `backend/src/core/servicios/document_service.py`
- Locate the `_prepare_solicitud_desembolso_replacements` method (starts at line 1234)
- Find the `replacements` dictionary (starts at line 1278)
- Add the `[NIT]` placeholder to the replacements dictionary
- The NIT value is available in `data.get('nit', '')` since it's already in the data snapshot

**Code change:**
Add this line to the `replacements` dictionary (around line 1300, before the closing brace):

```python
# Client identification
'[NIT]': data.get('nit', ''),
```

### Step 2: Update the Method Docstring

- Update the docstring at lines 1238-1243 to include `[NIT]` in the list of template placeholders
- Add `- [NIT]` to the list of supported placeholders

### Step 3: Run Validation Commands

- Execute all validation commands to ensure the change works correctly and introduces no regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- This is a minimal change that only affects one method in one file
- The NIT data is already available in the data snapshot (confirmed in `operations_routes.py` line 278)
- The pattern follows existing implementations in `_prepare_replacements` (line 651) and `_prepare_otrosi_replacements` (line 727)
- No frontend changes are required since the NIT is already being sent as part of the client data
- No database changes are required
- After deployment, any newly generated Solicitud de Desembolso documents will have the NIT placeholder properly populated
