# Bug: PA Classification Excel Download Not Generated

## Bug Description
When running the PA Report classification workflow, the classification appears to complete successfully (the record is saved in Historial with status 'classified'), but when attempting to download the classified Excel file, no file is generated. The user sees a 404 error or the download simply doesn't work.

**Expected behavior:** After classification completes, clicking "Descargar Archivo Clasificado" should download an Excel file with all the classified PA data including the 8 output columns (PA, Categoria, Subcategoria, Clasificacion, Nexo, Comprobacion Saldos, Cuenta Homologacion, Nombre Homologacion).

**Actual behavior:** Classification appears to succeed (UI shows success message, Historial shows record with 'classified' status), but download returns 404 error "Archivo no encontrado o sesión inválida".

## Problem Statement
The classified data is stored in an in-memory dictionary (`_processing_sessions`) but the Excel file is not persisted. When the download is requested, one of the following occurs:
1. The in-memory session data is lost (server restart between classification and download)
2. The `classified_df` DataFrame is None or empty
3. Excel generation fails silently and returns None

The system lacks proper error handling and does not persist the classified data or generated Excel file, making downloads unreliable.

## Solution Statement
1. Add comprehensive error logging in `get_classified_excel` to identify exactly why None is returned
2. Persist the classified Excel file to Supabase Storage during classification
3. Store the file URL in `pa_processing_history` for reliable download
4. Update download endpoint to retrieve file from storage if in-memory session is lost
5. Add proper error messages to help diagnose failures

## Steps to Reproduce
1. Login as a finance user
2. Navigate to Finance > Reporte PA
3. Upload the PA account catalog (e.g., `Catálogo de Cuenta.xlsx`)
4. Upload a movements CSV file (e.g., `MovimientoDetallado NOV_25.csv`)
5. Run Step 1: Cleanup - verify success
6. Run Step 2: Classification - verify success message appears
7. Click "Descargar Archivo Clasificado" button
8. Observe: Download fails with 404 error or no file is generated
9. Check Historial tab: Record shows status 'classified' but no file available

## Root Cause Analysis
The root cause is a **lack of persistence for classified Excel files**. The current implementation:

1. **In-memory only storage** (`pa_report_service.py` lines 35, 482):
   ```python
   _processing_sessions: Dict[str, Dict] = {}
   session["classified_df"] = classified_df  # Stored in volatile memory
   ```

2. **Excel generation on-demand** (`pa_report_service.py` lines 544-570):
   ```python
   async def get_classified_excel(self, session_id: str) -> Optional[bytes]:
       session = _processing_sessions.get(session_id)
       if not session or session.get("classified_df") is None:
           return None  # Returns None silently if session lost
   ```

3. **No file persistence**: The database stores session metadata and stats, but not the actual Excel file or a URL to it. The `pa_processing_history` table has no column for storing the generated file.

4. **Silent failures**: When `get_classified_excel` returns None, the route returns 404 but there's no logging to indicate WHY it failed.

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

**Primary files to modify:**
- `backend/src/core/servicios/pa_report_service.py` - Main service handling classification and Excel generation. Need to add file persistence and better error handling.
- `backend/src/adapter/rest/pa_routes.py` - API routes for download endpoints. Need to improve error handling and add fallback to storage retrieval.
- `backend/src/repositorio/pa_rules_repository.py` - Repository for PA operations. Need to add methods for storing/retrieving file URLs.

**Reference files:**
- `backend/src/interface/pa_dtos.py` - DTOs for PA operations. May need to add classified_file_url field.
- `backend/database/migration_pa_classification.sql` - Check current schema, may need to add column for file URL.
- `frontend/src/pages/finance/ReportePA.tsx` - Frontend page to verify download flow is correctly handling errors.
- `frontend/src/services/financeServicePA.ts` - Frontend service to verify API calls.
- `app_docs/feature-b13fe784-pa-csv-semicolon-delimiter.md` - Reference documentation for PA feature.
- `app_docs/feature-550a54d1-pa-report-classification.md` - Reference documentation for PA classification feature.

### New Files
- `backend/database/migration_add_pa_file_storage.sql` - Migration to add classified_file_url and cleaned_file_url columns to pa_processing_history

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Debug Logging for Diagnosis
Add comprehensive logging to `get_classified_excel` method to identify exactly why None is returned:

- In `pa_report_service.py`, update `get_classified_excel` method:
  - Log when session is not found in `_processing_sessions`
  - Log when `classified_df` is None
  - Log when Excel generation fails with the actual exception
  - Log the session_id being requested and available session_ids for debugging

### Step 2: Create Database Migration for File Storage
Create migration to add columns for storing file URLs:

- Create `backend/database/migration_add_pa_file_storage.sql`:
  - Add `classified_file_url` TEXT column to `pa_processing_history`
  - Add `cleaned_file_url` TEXT column to `pa_processing_history`
  - These will store URLs to files in Supabase Storage

### Step 3: Add File Storage Helper Method
Add method to upload Excel to Supabase Storage:

- In `pa_report_service.py`, add `_upload_excel_to_storage` method:
  - Takes Excel bytes, session_id, and file type (cleaned/classified)
  - Uploads to Supabase Storage bucket (e.g., 'pa-reports')
  - Returns the public URL or signed URL
  - Handle errors gracefully with logging

### Step 4: Update Classify Data to Persist Excel
Modify `classify_data` method to save Excel file:

- After classification completes (line 482), generate Excel immediately
- Upload to Supabase Storage using the new helper
- Store the URL in database via `update_processing_session`
- Update stats with file_url

### Step 5: Update Clean Data to Persist Excel
Modify `clean_data` method to save Excel file:

- After cleanup completes (line 353), generate Excel immediately
- Upload to Supabase Storage using the new helper
- Store the URL in database via `update_processing_session`

### Step 6: Update Download Endpoints for Fallback
Modify download methods to retrieve from storage if in-memory fails:

- In `get_classified_excel`:
  - First try to get from in-memory session
  - If not found, query database for the file URL
  - If URL exists, fetch from Supabase Storage
  - Return the bytes

- In `get_cleaned_excel`:
  - Same fallback logic as classified

### Step 7: Update Repository for File URL Operations
Add methods to repository for file URL storage/retrieval:

- In `pa_rules_repository.py`:
  - `update_processing_session` already handles updates, but verify it handles file URL fields
  - Add helper method `get_file_url(session_id, file_type)` to retrieve URL

### Step 8: Run Validation Commands
Execute every command in the Validation Commands section to validate the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Pre-fix verification (reproduce the bug):**
```bash
# Start the application locally
cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8003 &
cd frontend && npm run dev &

# Manually test:
# 1. Login as finance user
# 2. Navigate to Finance > Reporte PA
# 3. Upload catalog and movements file
# 4. Run cleanup and classification
# 5. Attempt download - verify it fails with 404
```

**Backend validation:**
- `cd backend && python -m pytest tests/test_pa_report_service.py -v` - Run PA report service tests
- `cd backend && python -m pytest` - Run all backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting

**Frontend validation:**
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

**Post-fix verification:**
```bash
# Manually test the full workflow:
# 1. Login as finance user
# 2. Navigate to Finance > Reporte PA
# 3. Upload catalog (e.g., Catálogo de Cuenta.xlsx)
# 4. Upload movements CSV (e.g., MovimientoDetallado NOV_25.csv)
# 5. Run Step 1: Cleanup
# 6. Verify cleanup succeeds and download works
# 7. Run Step 2: Classification
# 8. Verify classification succeeds
# 9. Click "Descargar Archivo Clasificado"
# 10. Verify Excel downloads with all 8 output columns populated
```

## Notes

1. **Supabase Storage Bucket**: Before deploying, ensure a 'pa-reports' bucket exists in Supabase Storage with appropriate RLS policies for authenticated users.

2. **File Cleanup**: Consider adding a cleanup job to delete old files from storage (e.g., files older than 30 days) to manage storage costs.

3. **In-memory Session Fallback**: The in-memory session storage is still useful for performance during the same session. The storage fallback is only used when the in-memory data is lost.

4. **Migration Order**: Apply the database migration before deploying the code changes to avoid errors accessing non-existent columns.

5. **Testing Large Files**: Test with large files (~50K records) to ensure Excel generation and upload work correctly for production-scale data.
