# Bug: [object Object] Error Display in Directory Scanner

## Bug Description
When running the directory scan extraction process, error messages are displayed as `[object Object]` instead of a human-readable error message. This occurs in the Directory Scanner page when the scan operation fails due to various reasons (validation errors, server errors, timeouts, etc.).

**Symptoms:**
- Error alert shows `[object Object]` text
- User cannot understand what went wrong
- No actionable information provided

**Expected Behavior:**
- Error messages should display human-readable text explaining the error
- Validation errors should show specific field issues
- Server errors should show descriptive messages

**Actual Behavior:**
- Error alert displays `[object Object]` literal string

## Problem Statement
The frontend error handling code assumes error messages are always strings, but FastAPI can return structured error objects (e.g., validation errors as arrays). When these objects are passed to `new Error()` or displayed directly, JavaScript converts them to `[object Object]`.

## Solution Statement
Create a robust error message extraction utility that:
1. Handles string error messages directly
2. Extracts message from FastAPI validation error arrays
3. Stringifies any remaining object types with meaningful formatting
4. Apply this utility consistently across all error handling in the directory scanner flow

## Steps to Reproduce
1. Navigate to http://localhost:5173
2. Go to Treasury > Escaneo de Directorios
3. Enter an invalid directory path or trigger any backend error
4. Click "Escanear Directorio"
5. Observe the error alert showing `[object Object]`

## Root Cause Analysis
The root cause is in the error handling chain:

1. **Backend** (`directory_scanner.py`): Returns proper `HTTPException` with string `detail`
2. **FastAPI Framework**: Returns JSON `{"detail": "message"}` for HTTPException, but validation errors return `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`
3. **Frontend Service** (`directoryScannerService.ts` lines 126-131):
   ```javascript
   const errorMessage =
     error.response?.data?.detail ||  // Could be an array/object!
     error.message ||
     'Failed to scan directory';
   throw new Error(errorMessage);  // new Error(object) = "[object Object]"
   ```
4. **Form Component** (`FKDirectoryScanForm.tsx` line 120):
   ```javascript
   setError(err.message || 'Error al escanear directorio');
   ```
5. **Page Component** (`DirectoryScannerPage.tsx` line 57):
   ```javascript
   setSnackbarMessage(error.message || 'Error al escanear directorio');
   ```

When `error.response?.data?.detail` is an object or array, `new Error(object)` produces an Error with message `[object Object]`.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [x] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `frontend/src/services/directoryScannerService.ts` - Contains the `scanLocalDirectory` function where the error is first caught and re-thrown. Lines 118-132 handle errors but don't properly stringify object errors.
- `frontend/src/components/treasury/FKDirectoryScanForm.tsx` - Contains the form component that displays the error alert. Line 120 catches errors and sets state without proper type handling.
- `frontend/src/pages/treasury/DirectoryScannerPage.tsx` - Contains the page component that also displays snackbar errors. Line 57 has the same pattern.

### New Files
- `frontend/src/utils/errorUtils.ts` - New utility file containing the `extractErrorMessage` function for consistent error message extraction.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Error Utility Function
- Create a new file `frontend/src/utils/errorUtils.ts`
- Implement `extractErrorMessage(error: unknown): string` function that:
  - Returns the string directly if `error` is a string
  - Extracts `error.message` if error is an Error instance
  - Handles axios error structure: `error.response?.data?.detail`
  - If `detail` is an array (FastAPI validation errors), extract and join the `msg` fields
  - If `detail` is an object with a `message` or `msg` field, use that
  - If `detail` is a string, use it directly
  - Fallback to `JSON.stringify(error)` for any remaining object types
  - Final fallback to a generic error message

### Step 2: Update Directory Scanner Service
- Open `frontend/src/services/directoryScannerService.ts`
- Import the `extractErrorMessage` utility
- Replace lines 126-131 error handling:
  ```javascript
  // Before
  const errorMessage =
    error.response?.data?.detail ||
    error.message ||
    'Failed to scan directory';
  throw new Error(errorMessage);

  // After
  const errorMessage = extractErrorMessage(error);
  throw new Error(errorMessage);
  ```

### Step 3: Update Directory Scan Form Component
- Open `frontend/src/components/treasury/FKDirectoryScanForm.tsx`
- Import the `extractErrorMessage` utility
- Update line 120 error handling:
  ```javascript
  // Before
  setError(err.message || 'Error al escanear directorio');

  // After
  setError(extractErrorMessage(err));
  ```

### Step 4: Update Directory Scanner Page
- Open `frontend/src/pages/treasury/DirectoryScannerPage.tsx`
- Import the `extractErrorMessage` utility
- Update line 57 error handling:
  ```javascript
  // Before
  setSnackbarMessage(error.message || 'Error al escanear directorio');

  // After
  setSnackbarMessage(extractErrorMessage(error));
  ```

### Step 5: Create E2E Test for Error Display
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` as examples
- Create a new E2E test file `.claude/commands/e2e/test_directory_scanner_error_display.md` that:
  1. Navigates to the Directory Scanner page
  2. Enters an invalid/non-existent directory path
  3. Clicks "Escanear Directorio"
  4. Verifies the error message displayed is NOT `[object Object]`
  5. Verifies the error message contains human-readable text
  6. Takes screenshots of the error state

### Step 6: Run Validation Commands
- Execute all validation commands to ensure the bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Verify frontend TypeScript compiles without errors
cd frontend && npx tsc --noEmit

# Run frontend linting
cd frontend && npm run lint

# Build frontend for production
cd frontend && npm run build

# Run backend linting
cd backend && ruff check src/

# Run backend tests
cd backend && python -m pytest
```

**Manual Validation:**
1. Start both frontend and backend servers
2. Navigate to http://localhost:5173
3. Go to Treasury > Escaneo de Directorios
4. Enter a non-existent directory path (e.g., `C:/NonExistent/Path`)
5. Click "Escanear Directorio"
6. **Verify** the error message is human-readable (NOT `[object Object]`)
7. **Verify** the error explains what went wrong

**E2E Test Validation:**
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_directory_scanner_error_display.md` to validate error display works correctly

## Notes
- The `extractErrorMessage` utility should be designed for reuse across the application
- Consider adding TypeScript overloads for better type safety
- The utility should handle edge cases like:
  - Null/undefined errors
  - Circular reference objects (use try/catch on JSON.stringify)
  - Very long error messages (consider truncation)
- FastAPI validation errors follow this structure:
  ```json
  {
    "detail": [
      {"loc": ["body", "field_name"], "msg": "error message", "type": "value_error"}
    ]
  }
  ```
- Axios timeout errors have a different structure with `error.code = 'ECONNABORTED'`
