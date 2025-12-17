# Bug: Broker Incentives Extraction 404 Not Found Error

## Bug Description
When attempting to scan a directory for broker contracts using the "Extracción Incentivos" feature in the Alianzas module, the user receives a "Not Found" error. The backend logs reveal that the request is being sent to `/api/api/alianzas/broker-contracts/scan` instead of the correct path `/api/alianzas/broker-contracts/scan`, resulting in a 404 Not Found response.

**Symptoms:**
- UI displays "Not Found" error alert
- Backend returns HTTP 404 status code
- Feature is completely non-functional

**Expected Behavior:**
- Directory scan should execute successfully
- Results should display in the data grid
- Excel export should be available

**Actual Behavior:**
- Request fails with 404 Not Found
- URL path has duplicate `/api/` prefix

## Problem Statement
The frontend `brokerIncentiveService.ts` defines `BASE_PATH = '/api/alianzas/broker-contracts'`, but the `apiClient` already has a base URL of `http://localhost:8000/api`. This causes a double `/api/` prefix in the final request URL, resulting in `/api/api/alianzas/broker-contracts/scan` which doesn't match any backend route.

## Solution Statement
Remove the `/api` prefix from `BASE_PATH` in `brokerIncentiveService.ts`. The path should be `/alianzas/broker-contracts` since `apiClient` already includes `/api` in its base URL.

## Steps to Reproduce
1. Log in to the application with alianzas or admin role
2. Navigate to Alianzas > Extracción Incentivos
3. Enter a valid directory path (e.g., `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024`)
4. Check "Incluir Subcarpetas"
5. Click "Escanear Directorio"
6. Observe "Not Found" error displayed in UI

## Root Cause Analysis
The root cause is an inconsistent URL path construction between the service and the API client:

1. **apiClient.ts** (line 11): `baseURL = 'http://localhost:8000/api'` - includes `/api`
2. **brokerIncentiveService.ts** (line 13): `BASE_PATH = '/api/alianzas/broker-contracts'` - also includes `/api`
3. When combined: `http://localhost:8000/api` + `/api/alianzas/broker-contracts/scan` = `/api/api/alianzas/broker-contracts/scan`

The backend route is correctly defined at `/api/alianzas/broker-contracts/scan` (alianzas_routes.py line 1563-1564), but the frontend is sending requests to a non-existent double-prefixed path.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [x] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`frontend/src/services/brokerIncentiveService.ts`** (line 13): Contains the incorrect `BASE_PATH` with duplicate `/api` prefix. This is the file that needs to be modified.
- **`frontend/src/api/clients/apiClient.ts`** (line 11): Reference file to understand that baseURL already includes `/api`.
- **`backend/src/adapter/rest/alianzas_routes.py`** (lines 1563-1564): Reference file confirming the correct backend route is `/api/alianzas/broker-contracts/scan`.

### New Files
- `.claude/commands/e2e/test_broker_incentive_extraction.md`: E2E test to validate the fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix the BASE_PATH in brokerIncentiveService.ts
- Open `frontend/src/services/brokerIncentiveService.ts`
- Change line 13 from:
  ```typescript
  const BASE_PATH = '/api/alianzas/broker-contracts';
  ```
  to:
  ```typescript
  const BASE_PATH = '/alianzas/broker-contracts';
  ```
- This removes the duplicate `/api` prefix since `apiClient` already has `/api` in its base URL

### Step 2: Verify the fix compiles without TypeScript errors
- Run `cd frontend && npx tsc --noEmit` to ensure no type errors
- Run `cd frontend && npm run lint` to ensure no linting issues

### Step 3: Create E2E test file
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_broker_contract_extraction.md` to understand E2E test format
- Create `.claude/commands/e2e/test_broker_incentive_extraction.md` with steps to:
  1. Navigate to http://localhost:5173/
  2. Log in with alianzas/admin credentials
  3. Navigate to Alianzas > Extracción Incentivos
  4. Enter directory path `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024`
  5. Check "Incluir Subcarpetas"
  6. Click "Escanear Directorio"
  7. Verify no "Not Found" error appears
  8. Verify results display in data grid or appropriate message
  9. Take screenshot to prove functionality works

### Step 4: Run validation commands
- Execute all validation commands listed below to confirm the fix works with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_incentive_extraction.md` to validate this functionality works

## Notes
- This is a minimal one-line fix that addresses the root cause
- The pattern of including `/api` in service BASE_PATH is inconsistent with other services in the codebase - consider auditing other services for similar issues
- The backend route definition is correct and does not need modification
- After fixing, the correct URL will be: `http://localhost:8000/api/alianzas/broker-contracts/scan`
