# Bug: EmailChainValidationStatus Enum Case Mismatch

## Bug Description
When navigating to the Riesgos module's "Contacto Externo" (External Communication) section, users receive a CORS error in the browser console. The actual underlying issue is a 500 Internal Server Error caused by an `AttributeError` in the backend. The browser shows a CORS error because FastAPI fails to return proper CORS headers when an unhandled exception occurs before the response is generated.

**Error Message:**
```
AttributeError: type object 'EmailChainValidationStatus' has no attribute 'pending'
```

**Browser Symptom:**
```
Access to XMLHttpRequest at 'http://localhost:8003/api/risk/evaluations/{uuid}/email-chains-with-validations'
from origin 'http://localhost:5175' has been blocked by CORS policy
```

## Problem Statement
The `EmailChainValidationStatus` enum is defined with uppercase member names (`PENDING`, `VALIDATED`, `SUSPICIOUS`, `CRITICAL`) in `src/interface/risk_dtos.py`, but the code in `risk_routes.py` at lines 2623-2624 incorrectly attempts to access lowercase member names (`pending`, `validated`), causing an `AttributeError`.

## Solution Statement
Fix the enum member references in `risk_routes.py` to use the correct uppercase member names (`EmailChainValidationStatus.PENDING` and `EmailChainValidationStatus.VALIDATED`) instead of the incorrect lowercase versions.

## Steps to Reproduce
1. Start the backend and frontend servers locally
2. Log in to the application
3. Navigate to the Riesgos module
4. Open any risk evaluation
5. Click on the "Contacto Externo" tab
6. Observe the CORS error in the browser console and the 500 Internal Server Error in the backend logs

## Root Cause Analysis
The `EmailChainValidationStatus` enum is defined in `src/interface/risk_dtos.py` as:

```python
class EmailChainValidationStatus(str, Enum):
    """Status of email chain validation"""
    PENDING = "pending"
    VALIDATED = "validated"
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"
```

However, in `src/adapter/rest/risk_routes.py` at lines 2623-2624, the code incorrectly references:
- `EmailChainValidationStatus.pending` (should be `EmailChainValidationStatus.PENDING`)
- `EmailChainValidationStatus.validated` (should be `EmailChainValidationStatus.VALIDATED`)

This is a simple typo where the enum values (lowercase) were used instead of the enum member names (uppercase). This bug was likely introduced during the implementation of the external communication validation feature (ADW 584b6bdd).

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`backend/src/adapter/rest/risk_routes.py`** (lines 2623-2624): Contains the incorrect enum member references that need to be fixed
- **`backend/src/interface/risk_dtos.py`** (line 611-616): Contains the enum definition - reference to verify correct member names

### Reference Files (no changes needed)
- **`backend/src/core/servicios/risk/email_chain_service.py`**: Shows correct usage of the enum with uppercase member names (CRITICAL, SUSPICIOUS, VALIDATED)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Enum Member References in risk_routes.py

- Open `backend/src/adapter/rest/risk_routes.py`
- Locate line 2623-2624 in the `get_email_chains_with_validations` function
- Change `EmailChainValidationStatus.pending` to `EmailChainValidationStatus.PENDING`
- Change `EmailChainValidationStatus.validated` to `EmailChainValidationStatus.VALIDATED`

**Before:**
```python
pending_count=sum(1 for c in chains_with_validations if c.validation_status == EmailChainValidationStatus.pending),
validated_count=sum(1 for c in chains_with_validations if c.validation_status == EmailChainValidationStatus.validated),
```

**After:**
```python
pending_count=sum(1 for c in chains_with_validations if c.validation_status == EmailChainValidationStatus.PENDING),
validated_count=sum(1 for c in chains_with_validations if c.validation_status == EmailChainValidationStatus.VALIDATED),
```

### Step 2: Verify No Other Incorrect References Exist

- Search the entire backend codebase for lowercase enum references: `EmailChainValidationStatus.pending`, `EmailChainValidationStatus.validated`, `EmailChainValidationStatus.suspicious`, `EmailChainValidationStatus.critical`
- Ensure all references use uppercase member names

### Step 3: Run Validation Commands

- Execute all validation commands listed below to ensure the fix works and causes no regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Reproduce the bug (before fix)
```bash
# Start the backend server and hit the failing endpoint
curl -X GET "http://localhost:8003/api/risk/evaluations/ab868d98-2eb3-4a4a-adee-aaed9e1cfa44/email-chains-with-validations" -H "Content-Type: application/json"
# Expected: 500 Internal Server Error with AttributeError
```

### Verify the fix (after fix)
```bash
# Start the backend server and hit the endpoint
curl -X GET "http://localhost:8003/api/risk/evaluations/ab868d98-2eb3-4a4a-adee-aaed9e1cfa44/email-chains-with-validations" -H "Content-Type: application/json"
# Expected: 200 OK or 404 Not Found (if evaluation doesn't exist), NOT 500
```

### Search for any remaining incorrect enum references
```bash
cd backend && grep -rn "EmailChainValidationStatus\.\(pending\|validated\|suspicious\|critical\)" src/
# Expected: No matches (all should use uppercase PENDING, VALIDATED, etc.)
```

### Run standard validation suite
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

- This is a simple one-line fix (two enum references on adjacent lines)
- The CORS error is a red herring - the actual issue is the backend 500 error. When FastAPI raises an unhandled exception, it doesn't add CORS headers to the error response, which causes the browser to report a CORS error instead of showing the actual 500 error
- The fix is surgical and minimal - only changing the case of two enum member names
- Similar usage of this enum in `email_chain_service.py` already uses the correct uppercase format
