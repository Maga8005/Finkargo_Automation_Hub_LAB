# Bug: Otrosí Contract Generation 422 Unprocessable Content Error

## Bug Description
When attempting to generate an Otrosí No. 1 contract through the Operations department interface (`FKOtrosiRequest.tsx`), the API request fails with a 422 (Unprocessable Content) HTTP status code. Additionally, a React rendering error occurs when the error response is displayed: "Objects are not valid as a React child (found: object with keys {type, loc, msg, input})".

**Symptoms:**
1. Backend returns 422 status code when requesting Otrosí contract generation
2. Console shows "Request error: AxiosError" from FKOtrosiRequest.tsx:77
3. React crashes with "Objects are not valid as a React child" error when trying to display the error
4. User cannot generate Otrosí contracts

**Additional Issue Found During Testing:**
5. After fixing the 422 error, a 500 Internal Server Error occurred: "'dict' object has no attribute 'contract_id'"
6. This was caused by logging code assuming the contract response was an object instead of a dict

**Expected Behavior:**
- API should accept the request and create a contract in UNDER_REVIEW status
- Any validation errors should be displayed in a user-friendly format in Spanish
- The application should not crash when displaying error messages

**Actual Behavior:**
- Backend rejects the request with 422 status
- Frontend crashes when attempting to render the Pydantic validation error object
- Error message is not user-friendly

## Problem Statement
There are multiple issues affecting contract generation:

1. **Content-Type Mismatch**: The frontend `operationsService.requestOtrosiGeneration()` sends JSON (`application/json`), but the backend endpoint `/api/operations/contracts/generate` expects `multipart/form-data` with Form parameters (`client_nit`, `contract_type`, `rut_file`).

2. **Error Display Bug**: The error handling code at line 76 in `FKOtrosiRequest.tsx` attempts to display `err.response?.data?.detail`, which for Pydantic validation errors is an array of error objects (with `type`, `loc`, `msg`, `input` keys). React cannot render these objects directly, causing the application to crash.

3. **Logging Type Error**: The backend logging code at line 148 assumes `contract` is an object with `.contract_id` attribute, but the service returns a dict with `['contract_id']` key, causing AttributeError and 500 Internal Server Error.

## Solution Statement
Fix the content-type mismatch, improve error handling, and resolve logging issues:

1. **Update `operationsService.requestOtrosiGeneration()`**: Change from sending JSON to sending `multipart/form-data` using FormData, matching the backend's expected format for all contract types (Inventario Bodega already uses FormData).

2. **Add proper error formatting**: Create a utility function to parse Pydantic validation errors and format them as user-friendly Spanish messages that can be displayed in the Alert component.

3. **Add defensive error handling**: Ensure the error display code handles various error response formats (string, array, object) without crashing React.

4. **Fix backend logging type handling**: Update logging code to handle both dict and object response types using `hasattr()` check and safe dict access with `.get()` method.

## Steps to Reproduce
1. Navigate to Operations dashboard
2. Go to "Solicitar Otrosí No. 1" section
3. Search for a client by NIT or name
4. Select a client from search results
5. Click "Solicitar Otrosí No. 1" button
6. Observe 422 error in console and React crash

## Root Cause Analysis
The root cause is a **content-type mismatch** between frontend and backend:

**Backend Expectation** (`backend/src/adapter/rest/operations_routes.py:62-67`):
```python
@router.post("/contracts/generate", response_model=ContractGenerationResponse)
async def request_contract_generation(
    client_nit: str = Form(..., description="Client NIT"),
    contract_type: str = Form(..., description="Contract type"),
    rut_file: Optional[UploadFile] = File(None),
    ...
)
```
The endpoint uses `Form(...)` parameters, which requires `multipart/form-data`.

**Frontend Implementation** (`frontend/src/services/operationsService.ts:41-52`):
```typescript
async requestOtrosiGeneration(clientNit: string): Promise<ContractGeneration> {
  const request: ContractGenerationRequest = {
    client_nit: clientNit,
    contract_type: 'otrosi',
  };
  const response = await apiClient.post<ContractGeneration>(
    `${BASE_URL}/contracts/generate`,
    request  // ← Sends JSON, not FormData
  );
  return response.data;
}
```
This sends `application/json`, causing FastAPI to reject the request with 422.

**Secondary Issue**: The Pydantic validation error structure (`{type, loc, msg, input}`) cannot be rendered directly in React JSX, causing the rendering crash.

## Relevant Files
Use these files to fix the bug:

### Frontend Files
- **`frontend/src/services/operationsService.ts`** (lines 41-52)
  - Contains `requestOtrosiGeneration()` that needs to be fixed to send FormData instead of JSON
  - Also contains `requestContractGeneration()` (lines 16-24) which has the same issue

- **`frontend/src/components/forms/FKOtrosiRequest.tsx`** (lines 59-81)
  - Contains error handling logic that needs improvement to format Pydantic validation errors
  - Line 76 displays error without proper formatting

- **`frontend/src/utils/errorUtils.ts`** (NEW FILE)
  - Will contain utility function to format API validation errors into user-friendly Spanish messages

### Backend Files (for reference/testing)
- **`backend/src/adapter/rest/operations_routes.py`** (lines 61-151)
  - Backend endpoint that expects multipart/form-data
  - Used to verify the fix works correctly

- **`backend/src/interface/legal_dtos.py`** (lines 122-133)
  - Contains `ContractGenerationRequest` DTO with validation rules
  - Helps understand validation error structure

### New Files
- **`frontend/src/utils/errorUtils.ts`**
  - Utility to format Pydantic validation errors into Spanish user messages

## Step by Step Tasks

### Step 1: Create Error Formatting Utility
Create a new utility file to handle API validation errors and format them for user display.

- Create `frontend/src/utils/errorUtils.ts`
- Add function `formatApiError(error: any): string` that:
  - Handles Pydantic validation error arrays (FastAPI 422 responses)
  - Handles simple string error messages
  - Handles unknown error formats with fallback message
  - Returns Spanish user-friendly messages
- Export the utility function

### Step 2: Fix `requestOtrosiGeneration()` Method
Update the Otrosí-specific method to use FormData instead of JSON.

- Open `frontend/src/services/operationsService.ts`
- Modify `requestOtrosiGeneration()` (lines 41-52):
  - Create FormData instance
  - Append `client_nit` and `contract_type` as form fields
  - Set proper Content-Type header (`multipart/form-data`)
  - Keep the same return type and error handling

### Step 3: Fix Generic `requestContractGeneration()` Method
Update the generic contract generation method to use FormData (used by other components).

- In `frontend/src/services/operationsService.ts`
- Modify `requestContractGeneration()` (lines 16-24):
  - Create FormData instance
  - Append `client_nit` and `contract_type` from request object
  - Set proper Content-Type header
  - Maintain backward compatibility with existing callers

### Step 4: Improve Error Handling in `FKOtrosiRequest.tsx`
Update the component to use the new error formatting utility.

- Open `frontend/src/components/forms/FKOtrosiRequest.tsx`
- Import `formatApiError` utility
- Update error handling in `handleRequestContract()` (line 76):
  - Replace direct error detail access with `formatApiError(err)`
  - Remove console.error or keep for debugging purposes
  - Ensure error state is always a string

### Step 5: Add Logging to Backend Endpoint
Add structured logging to help debug future issues with contract generation.

- Open `backend/src/adapter/rest/operations_routes.py`
- Add logging at the start of `request_contract_generation()` to log:
  - Incoming request parameters (client_nit, contract_type)
  - Content-Type header received
  - User information
- Add logging for validation errors before raising HTTPException
- Use INFO level for normal flow, ERROR level for exceptions

### Step 5.1: Fix Logging Type Handling (Discovered During Testing)
Fix AttributeError in logging code that assumes contract is an object.

- Open `backend/src/adapter/rest/operations_routes.py`
- Locate the logging line after `service.generate_contract()` (line 148)
- Update to handle both dict and object response types:
  - Use `hasattr(contract, 'contract_id')` to check if it's an object
  - Use `contract.get('contract_id', 'unknown')` as fallback for dict
  - This prevents "'dict' object has no attribute 'contract_id'" error

**Fix Code:**
```python
# Handle both dict and object response types
contract_id = contract.contract_id if hasattr(contract, 'contract_id') else contract.get('contract_id', 'unknown')
logger.info(f"Contract generated successfully - Contract ID: {contract_id}, NIT: {client_nit}, Type: {contract_type}")
```

### Step 6: Manual Testing
Manually test the fix through the UI to ensure it works correctly.

- Start backend server: `cd backend && python main.py`
- Start frontend dev server: `cd frontend && npm run dev`
- Navigate to Operations dashboard → "Solicitar Otrosí No. 1"
- Test the following scenarios:
  1. **Happy path**: Search for a valid client and request Otrosí contract
     - Should create contract in UNDER_REVIEW status
     - Should show success message
  2. **Invalid NIT**: Search for non-existent client
     - Should show appropriate error in Spanish
     - Should NOT crash React
  3. **Network error**: Disconnect from backend
     - Should show connection error in Spanish
     - Should NOT crash React
  4. **Empty search**: Try requesting without selecting a client
     - Should show validation error
     - Should NOT crash React

### Step 7: Verify Backend Logs
Check that the new logging provides useful debugging information.

- Review backend console output during manual testing
- Verify that incoming requests are logged with:
  - Client NIT
  - Contract type
  - Content-Type header
- Verify that any validation errors are logged before being sent to frontend
- Ensure no sensitive information (tokens, passwords) is logged

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Backend Validation
- `cd backend && python -m pytest tests/ -v` - Run all backend tests (if tests exist)
- `cd backend && python main.py` - Start backend server and verify no startup errors

### Frontend Validation
- `cd frontend && npm run type-check` - Verify TypeScript types are correct
- `cd frontend && npm run build` - Verify production build succeeds
- `cd frontend && npm run dev` - Start dev server for manual testing

### Manual End-to-End Validation
After starting both backend and frontend:
1. Navigate to `http://localhost:5173` (or configured port)
2. Login with Operations role credentials
3. Go to "Solicitar Otrosí No. 1" section
4. Search for test client (e.g., "900123456-1")
5. Select client and click "Solicitar Otrosí No. 1"
6. Verify:
   - ✅ No 422 error in console
   - ✅ No React rendering crash
   - ✅ Success message appears in Spanish
   - ✅ Contract is created with UNDER_REVIEW status
7. Test error scenarios:
   - Invalid NIT → Shows user-friendly error
   - Empty selection → Shows validation error
   - Both should NOT crash React

### Verify No Regressions
- Test Inventario Bodega contract generation (already uses FormData)
  - Should still work correctly with RUT upload
- Test other Operations features:
  - Get approved contracts list
  - Download approved contract PDFs
- Verify no TypeScript compilation errors
- Verify no console errors or warnings during normal operation

## Notes

### Technical Context
- **FastAPI Form vs JSON**: FastAPI distinguishes between `Form()` parameters (requires `multipart/form-data`) and Pydantic models (requires `application/json`). The backend uses `Form()` to support optional file uploads in the same endpoint.

- **Why Not Change Backend**: Changing the backend to accept JSON would require creating separate endpoints for file uploads vs non-file requests, increasing complexity. It's simpler to standardize on FormData for all contract generation requests.

- **Pydantic Validation Errors**: When FastAPI/Pydantic validation fails, the error response has this structure:
  ```json
  {
    "detail": [
      {
        "type": "missing",
        "loc": ["body", "client_nit"],
        "msg": "Field required",
        "input": null
      }
    ]
  }
  ```
  This cannot be rendered directly in React JSX.

- **Dict vs Object Response Types**: The `ContractService.generate_contract()` method returns a Pydantic model that gets serialized to a dict by FastAPI's response model. When logging, we must handle both types safely using `hasattr()` checks and dict `.get()` methods to prevent AttributeError exceptions that would cause 500 errors.

### Error Message Translations (Spanish)
For the error formatting utility, use these translations:
- "Field required" → "Campo requerido"
- "Invalid value" → "Valor inválido"
- "Client not found" → "Cliente no encontrado"
- "Invalid contract type" → "Tipo de contrato inválido"
- Default → "Error al solicitar el contrato. Por favor intente nuevamente."

### Future Improvements
- Consider adding automated E2E tests for contract generation flow
- Add error boundary component to gracefully handle unexpected React errors
- Consider standardizing all API requests to use proper error formatting
- Add request/response logging middleware for better debugging

### Related Files (Not Modified)
- `frontend/src/api/clients/apiClient.ts` - Axios client configuration (no changes needed)
- `backend/src/core/servicios/contract_service.py` - Business logic (no changes needed)
- `frontend/src/types/legal.ts` - Type definitions (no changes needed, already correct)
