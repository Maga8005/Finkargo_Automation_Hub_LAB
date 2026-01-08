# PA Report Upload CORS/413 Error Fix

**Date:** 2025-12-30
**Module:** Finance (PA Report)
**Specification:** specs/issue-na-adw-na-sdlc_planner-fix-pa-upload-file-size-cors.md

## Summary

Fixed the PA Report file upload feature that was failing with a misleading CORS error when uploading files larger than 10MB. The actual root cause was a file size limit configuration mismatch and missing CORS headers on 413 error responses.

## Changes Made

### Backend Changes

1. **Updated `backend/main.py`** - Modified `RequestSizeLimitMiddleware` to include CORS headers in 413 responses
   - Added `Access-Control-Allow-Origin` header with the request's origin
   - Added `Access-Control-Allow-Credentials: true` header
   - Updated docstring to explain the CORS header requirement

2. **Updated `backend/.env`** - Changed `MAX_UPLOAD_SIZE` from `10485760` (10MB) to `52428800` (50MB)

### Frontend Changes

1. **Updated `frontend/src/services/financeServicePA.ts`** - Improved 413 error detection
   - Added axios import for proper error type checking
   - Added `axios.isAxiosError()` check to detect HTTP 413 status code
   - Extracts error detail from server response when available
   - Falls back to default "file too large" message

## Discrepancies Found

1. **Plan stated `settings.py` needed updating** - The `MAX_UPLOAD_SIZE` in `settings.py` was already correctly set to `52428800` (50MB). The actual issue was the `.env` file overriding it with `10485760` (10MB).

## Root Cause Analysis

The bug manifested as a CORS error in the browser, but the actual root cause was:

1. **File size limit override in .env**: The `.env` file had `MAX_UPLOAD_SIZE=10485760` (10MB), overriding the default 50MB in `settings.py`

2. **Missing CORS headers on 413 response**: The `RequestSizeLimitMiddleware` runs before `CORSMiddleware` in the request chain (due to Starlette middleware order). When it returned a 413 response early, the response never passed through CORS middleware, causing browsers to report a CORS error instead of the actual 413 error.

3. **Frontend error masking**: The frontend's error handler was only checking for "413" in error messages, not the actual HTTP status code from axios responses.

## Files Changed

```
 backend/main.py                           | 10 ++++++++++
 frontend/src/services/financeServicePA.ts | 21 ++++++++++++++++++++-
 backend/.env                              |  1 (not tracked - local config)
 2 files changed (tracked), 30 insertions(+), 1 deletion(-)
```

## Validation

- Backend linting: Passed (existing warnings not related to these changes)
- Frontend linting: Passed (only pre-existing warnings)
- TypeScript type check: Passed
- Frontend build: Passed
- Backend restarted with new configuration

## Testing

After these changes:
1. Files up to 50MB should upload successfully
2. Files over 50MB will show a proper "file too large" error message (not a CORS error)
3. The error message from the server is displayed to the user when available
