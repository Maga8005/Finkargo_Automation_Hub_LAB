# E2E Test: Declaration Upload Session Error Handling

Test that 404 session errors show clear user feedback and allow recovery.

## User Story

As a Finkargo treasury user
I want to see a clear error message when my session expires
So that I can recover by re-uploading the Historial de Pagos file

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with admin or tesoreria role
- Test files:
  - Historial de Pagos Excel file
  - Declaration Inventory Excel file (`20251215 Diveco Test.xlsx`)

## Test Scenarios

### Scenario 1: Session Expires During Declaration Upload

This scenario tests what happens when the user tries to upload a declaration file but the session has expired (e.g., server restart, 30+ minute timeout).

#### Test Steps

1. Navigate to http://localhost:5173
2. Login with admin or tesoreria role user
3. Navigate to `/treasury/declaration-matching`
4. Upload a valid Historial de Pagos Excel file
5. **Verify** file parses successfully and session ID is created
6. **SIMULATE SESSION LOSS**: Restart the backend server OR wait 30+ minutes
7. Attempt to upload declaration inventory file
8. **Verify** error message appears: "La sesion ha expirado o el servidor fue reiniciado. Por favor, vuelva a cargar el archivo de Historial de Pagos para continuar."
9. **Verify** workflow resets to Step 1 (both upload sections reset)
10. **Verify** user can re-upload Historial file to start fresh
11. Take screenshot of error state

### Scenario 2: No Session When Uploading Declarations

This scenario tests the validation that prevents uploading declarations without first uploading Historial.

#### Test Steps

1. Navigate to http://localhost:5173
2. Login with admin or tesoreria role user
3. Navigate to `/treasury/declaration-matching`
4. **Verify** Declaration Inventory upload section shows "Primero suba el archivo de Historial de Pagos"
5. **Verify** Declaration Inventory upload is disabled until Historial is uploaded

### Scenario 3: Session Error During Execute Matching

This scenario tests error handling during the matching execution step.

#### Test Steps

1. Navigate to http://localhost:5173
2. Login with admin or tesoreria role user
3. Navigate to `/treasury/declaration-matching`
4. Upload Historial de Pagos file
5. Upload Declaration Inventory file
6. Proceed to Step 2 (Configure Parameters)
7. **SIMULATE SESSION LOSS**: Restart the backend server
8. Click "Ejecutar Coincidencias"
9. **Verify** error message appears about session expiration
10. **Verify** workflow resets to Step 1
11. Take screenshot of error state

### Scenario 4: Recovery After Session Error

This scenario tests that users can successfully recover after a session error.

#### Test Steps

1. Trigger a session error (any of the above scenarios)
2. **Verify** error message is displayed
3. **Verify** upload sections are reset
4. Upload Historial de Pagos file again
5. **Verify** new session is created
6. Upload Declaration Inventory file
7. **Verify** upload succeeds
8. Proceed through the complete workflow
9. **Verify** download works successfully
10. Take screenshot of successful completion

## Success Criteria

- [ ] 404 errors from session expiration show clear Spanish error message
- [ ] Error message explains how to recover (re-upload Historial)
- [ ] Workflow resets to Step 1 when session error occurs
- [ ] All state is cleared (sessionId, uploadResponse, declarationsResponse, matchingResponse)
- [ ] User can successfully restart the workflow after error
- [ ] No JavaScript errors in console during error handling
- [ ] Declaration upload is properly guarded against missing session

## Error Messages Expected

| Scenario | Expected Error Message |
|----------|----------------------|
| 404 Session Error | "La sesion ha expirado o el servidor fue reiniciado. Por favor, vuelva a cargar el archivo de Historial de Pagos para continuar." |
| No Session | "No hay sesion activa. Por favor, primero suba el archivo de Historial de Pagos." |

## Screenshot Locations

1. After session error occurs showing error message
2. After workflow resets to Step 1
3. After successful recovery and completion

## Notes

- Session timeout is 30 minutes (configured in backend)
- Sessions are stored in-memory, so server restart clears all sessions
- The fix focuses on graceful degradation - when sessions are lost, users get clear feedback and can easily recover
