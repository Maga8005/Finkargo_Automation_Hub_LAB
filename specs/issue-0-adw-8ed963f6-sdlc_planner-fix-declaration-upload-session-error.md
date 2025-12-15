# Bug: 404 Error When Uploading Declaration Inventory

## Bug Description

When uploading a declaration inventory Excel file to the Treasury Declaration Matching workflow, users receive a 404 error. The error occurs when trying to upload the file `20251215 Diveco Test.xlsx` to the "Inventario de Declaraciones" section.

**Symptoms:**
- User attempts to upload declaration inventory file
- Backend returns HTTP 404 status code
- Error message in Spanish: "Sesión no encontrada o expirada" (Session not found or expired)
- Upload appears to fail silently without clear user feedback

**Expected behavior:**
- User uploads declaration inventory file
- File is parsed and declarations are loaded
- User can proceed with matching workflow

**Actual behavior:**
- 404 error returned
- User cannot proceed with the workflow

## Problem Statement

The 404 error occurs because the session_id used for the declaration upload request references a session that no longer exists in the backend's in-memory session storage. This happens when:

1. **Server restart**: The backend was restarted (common during development with --reload flag), clearing all in-memory sessions
2. **Session expiration**: The session expired after 30 minutes of inactivity
3. **Session never created**: The user attempted to upload declarations without first uploading the Historial de Pagos file

The root issue is that the backend uses in-memory session storage (`_sessions` dict) which is volatile. Combined with poor error handling in the frontend, users don't get clear feedback about what went wrong.

## Solution Statement

1. **Improve frontend error handling** to detect session-related errors and provide clear user feedback
2. **Add session validation** in the frontend before attempting declaration upload
3. **Show session status** to help users understand when they need to re-upload files
4. **Provide clear recovery path** when session is lost

This is a minimal fix focused on user experience - we're NOT adding persistent session storage (that would be a larger architectural change).

## Steps to Reproduce

1. Navigate to `/treasury/declaration-matching`
2. Upload a valid Historial de Pagos Excel file
3. Wait for server restart (e.g., due to code change with --reload) OR wait 30+ minutes
4. Attempt to upload declaration inventory file `20251215 Diveco Test.xlsx`
5. Observe 404 error

Alternative reproduction:
1. Navigate to `/treasury/declaration-matching` with a stale sessionId from previous session
2. Attempt to upload declaration inventory file
3. Observe 404 error

## Root Cause Analysis

The backend endpoint at `treasury_matching_routes.py:224-246` validates the session_id:

```python
session = _get_session(session_id)
if not session:
    raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")
```

The `_sessions` dictionary is volatile in-memory storage (line 45):
```python
_sessions: Dict[str, Dict] = {}
SESSION_TIMEOUT_MINUTES = 30
```

When the server restarts or sessions expire, the frontend still holds the old `sessionId` in React state, leading to 404 errors when it tries to use it.

The frontend at `HistorialMatchingPage.tsx` doesn't handle this error gracefully - it shows a generic error without guiding the user to re-upload the Historial file.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [x] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files

Use these files to fix the bug:

- `frontend/src/pages/treasury/HistorialMatchingPage.tsx` - Main page component that manages session state and handles upload callbacks. Need to add error handling for 404 responses.
- `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx` - Upload component that shows file upload UI. May need to show session status.
- `frontend/src/services/treasuryMatchingService.ts` - API service layer. Reference for API calls.
- `backend/src/adapter/rest/treasury_matching_routes.py` - Backend route (reference only, no changes needed)

### New Files

1. `.claude/commands/e2e/test_declaration_upload_session_error.md` - E2E test file to validate the bug fix works correctly

## Step by Step Tasks

### Step 1: Add Session Validation Before Declaration Upload

- Open `frontend/src/pages/treasury/HistorialMatchingPage.tsx`
- In the `handleDeclarationsUpload` function (around line 107), add explicit validation before attempting upload
- If `sessionId` is null or empty, show an error message asking user to first upload Historial file
- Log the sessionId being used for debugging

### Step 2: Add Error Handling for 404 Session Errors

- In `handleDeclarationsUpload` function, wrap the API call in try-catch
- Check if error response status is 404
- If 404, show a specific error message: "La sesión ha expirado. Por favor, vuelva a cargar el archivo de Historial de Pagos."
- Reset the session state to force re-upload of Historial file
- Add similar error handling to `handleExecuteMatching`, `handleManualOverride`, `handleClearMatch`, and `handleDownload`

### Step 3: Add Session Status Indicator

- In `FKHistorialMatchingUploader.tsx`, add a visual indicator when session is active
- Show session expiration warning after 25 minutes (5 minutes before timeout)
- This helps users understand their session state

### Step 4: Reset Workflow on Session Loss

- In `HistorialMatchingPage.tsx`, create a `resetSession` function that clears:
  - `sessionId`
  - `uploadResponse`
  - `declarationsResponse`
  - `matchingResults`
- Call this function when a 404 session error is detected
- This forces the user to start fresh from Step 1

### Step 5: Create E2E Test File

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_declaration_historial_matching.md` for format
- Create `.claude/commands/e2e/test_declaration_upload_session_error.md`
- Test scenario: Verify that 404 session errors show clear user feedback
- Test scenario: Verify that session loss triggers workflow reset
- Test scenario: Verify user can recover by re-uploading Historial file

### Step 6: Run Validation Commands

- Execute all validation commands to ensure zero regressions

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

```bash
# Frontend validation
cd frontend && npm run lint  # Run frontend linting
cd frontend && npx tsc --noEmit  # Run TypeScript type check
cd frontend && npm run build  # Run frontend build

# Backend validation (no backend changes, but verify it still works)
cd backend && ruff check src/  # Run backend linting

# Manual testing
# 1. Open http://localhost:5173/treasury/declaration-matching
# 2. Upload Historial file
# 3. Restart backend server (simulate session loss)
# 4. Attempt to upload declaration file
# 5. Verify clear error message appears
# 6. Verify workflow resets to allow re-upload of Historial
```

Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_declaration_upload_session_error.md` test file to validate this functionality works.

## Notes

### Why Not Persist Sessions?

Persisting sessions to a database would be a more robust solution but requires:
- Database schema changes
- Additional complexity in session management
- Transaction handling for concurrent access
- Session cleanup jobs

For this bug fix, we focus on **graceful degradation** - when sessions are lost, users get clear feedback and can easily recover.

### Session Timeout

The current timeout is 30 minutes (`SESSION_TIMEOUT_MINUTES = 30`). Users should be warned before timeout to avoid data loss.

### In-Memory Session Design Decision

The in-memory session storage was a deliberate design choice for simplicity during initial development. A future enhancement could use Redis or database-backed sessions for production deployments with multiple server instances.

### Error Message Translations

The 404 response message from backend is in Spanish: "Sesión no encontrada o expirada". The frontend should display a user-friendly message in Spanish as well, with clear recovery instructions.
