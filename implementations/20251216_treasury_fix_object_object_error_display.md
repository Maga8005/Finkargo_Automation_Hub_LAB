# Implementation Report: Fix [object Object] Error Display in Directory Scanner

**Date:** 2025-12-16
**Module:** Treasury / Directory Scanner
**Issue:** Bug - Error messages displaying as `[object Object]` instead of human-readable text

## Summary

Fixed the bug where error messages in the Directory Scanner page were displayed as `[object Object]` instead of human-readable text. The issue occurred when FastAPI returned structured error objects (like validation error arrays) that were not properly stringified before being displayed to users.

## Work Completed

- **Created `extractErrorMessage` utility function** in `frontend/src/utils/errorUtils.ts`:
  - Handles null/undefined errors gracefully
  - Extracts messages from string errors directly
  - Handles axios error structure with `response.data.detail`
  - Formats FastAPI validation error arrays into readable strings
  - Handles timeout errors with specific Spanish message
  - Handles network errors with specific Spanish message
  - Handles objects with `message` or `msg` properties
  - Falls back to JSON stringification for unknown object types
  - Uses safe try/catch for circular reference protection

- **Added `isTimeoutError` helper function** to detect axios timeout errors

- **Updated `directoryScannerService.ts`**:
  - Added import for `extractErrorMessage`
  - Replaced manual error extraction in `scanLocalDirectory`, `listInventoryFiles`, and `downloadInventoryFile`
  - Changed error types from `any` to `unknown` for better type safety
  - Added type assertions for axios error logging

- **Updated `FKDirectoryScanForm.tsx`**:
  - Added import for `extractErrorMessage`
  - Updated catch block to use `extractErrorMessage` instead of `err.message`
  - Changed error type from `any` to `unknown`

- **Updated `DirectoryScannerPage.tsx`**:
  - Added import for `extractErrorMessage`
  - Updated catch block to use `extractErrorMessage` for snackbar messages
  - Changed error type from `any` to `unknown`

- **Created E2E test file** `.claude/commands/e2e/test_directory_scanner_error_display.md`:
  - Tests that error messages are human-readable
  - Verifies error messages do NOT contain `[object Object]`
  - Includes steps to trigger and validate error display

## Discrepancies Found

1. **Plan specified creating new file** `frontend/src/utils/errorUtils.ts` but it already existed with `formatApiError` and other utilities. **Resolution:** Added new `extractErrorMessage` and `isTimeoutError` functions to the existing file.

2. **Pre-existing build errors** in `FKComisionesTable.tsx` and `FKPagosTable.tsx` related to MUI DataGrid localization. **Resolution:** These are unrelated to this bug fix and existed before the changes.

3. **Backend timeout was already updated** in a previous change from 10 minutes to 60 minutes. The plan mentioned this but it was already done.

## Files Changed

```
 backend/src/interface/directory_scanner_dtos.py    |   6 +-
 frontend/src/components/treasury/FKDirectoryScanForm.tsx    |   5 +-
 frontend/src/pages/treasury/DirectoryScannerPage.tsx    |   7 +-
 frontend/src/services/directoryScannerService.ts   |  58 ++++-----
 frontend/src/utils/errorUtils.ts                   | 130 +++++++++++++++++++++
 5 files changed, 165 insertions(+), 41 deletions(-)
```

## New Files Created

- `.claude/commands/e2e/test_directory_scanner_error_display.md` - E2E test for error display validation

## Validation Results

- **TypeScript type check**: Passed (`npx tsc --noEmit` - no errors)
- **ESLint**: Modified files pass with no errors (pre-existing warnings in other files)
- **Frontend build**: Pre-existing errors in unrelated files (`FKComisionesTable.tsx`, `FKPagosTable.tsx`)

## Technical Details

### Error Message Extraction Logic

The new `extractErrorMessage` function follows this priority:

1. Return fallback if error is null/undefined
2. Return string directly if error is already a string
3. Check for timeout errors and return Spanish message
4. Extract from axios `error.response.data.detail`:
   - If array: format as validation errors with field names
   - If string: use directly or translate
   - If object: extract `message` or `msg` property, or stringify
5. Handle Error instances with message property
6. Handle plain objects with `message` or `msg` properties
7. Last resort: JSON.stringify the error
8. Final fallback: return default Spanish error message

### Error Types Supported

- String errors
- Error instances
- Axios errors with `response.data.detail`
- FastAPI validation errors (arrays)
- Timeout errors (`ECONNABORTED`)
- Network errors
- Objects with `message`/`msg` properties
- Unknown object types (stringified)

## Notes

- The `extractErrorMessage` utility is designed for reuse across the application
- All error messages default to Spanish for user-facing display
- The utility includes protection against circular references in JSON.stringify
- Pre-existing build errors in MUI DataGrid components should be addressed separately
