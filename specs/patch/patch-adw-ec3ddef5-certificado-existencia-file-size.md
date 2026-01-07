# Patch: Increase Certificado de Existencia file size limit

## Metadata
adw_id: `ec3ddef5`
review_change_request: `When I try to upload the certificado de existencia found in this route 'c:\Users\guill\danke_apps\fkhub\lab-automation-hub-amplify\Example FIles for Reqs\PETROWORKS test\Camara de comercio Diciembre (1).pdf', the system generates an error message :8000/api/risk/evaluations/09ebc4a0-0c47-44f8-994b-b7e98d35c34f/documents:1 Failed to load resource: the server responded with a status of 400 (Bad Request)`

## Issue Summary
**Original Spec:** N/A (patch for file size mismatch)
**Issue:** The Certificado de Existencia (Camara de Comercio) document upload fails with 400 Bad Request because the file size (~14MB) exceeds the backend's 10MB limit. The frontend allows 50MB but the backend only allows 10MB, causing a mismatch that leads to user confusion.
**Solution:** Increase the backend's `max_size_mb` limit for `CERTIFICADO_EXISTENCIA` document type from 10MB to 50MB to match the frontend configuration.

## Files to Modify
Use these files to implement the patch:

1. `backend/src/core/servicios/risk/document_extraction_service.py` - Increase `max_size_mb` from 10 to 50 for `CERTIFICADO_EXISTENCIA`

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update backend file size limit for Certificado de Existencia
- Open `backend/src/core/servicios/risk/document_extraction_service.py`
- Locate the `get_document_type_info` method, specifically the `CERTIFICADO_EXISTENCIA` configuration (around line 479)
- Change `"max_size_mb": 10` to `"max_size_mb": 50`
- This aligns the backend limit with the frontend limit defined in `frontend/src/types/risk.ts` (line 451)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Backend Linting**
   ```bash
   cd backend && ruff check src/core/servicios/risk/document_extraction_service.py
   ```

2. **Backend Tests**
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

3. **Frontend Linting**
   ```bash
   cd frontend && npm run lint
   ```

4. **TypeScript Type Check**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend Build**
   ```bash
   cd frontend && npm run build
   ```

## Patch Scope
**Lines of code to change:** 1
**Risk level:** low
**Testing required:** Manual upload test with the 14MB Camara de Comercio PDF to verify the upload succeeds
