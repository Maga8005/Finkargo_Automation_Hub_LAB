# Bug: Fraud Risk Module Bug Fixes

## Bug Description
The fraud risk module has three distinct bugs that need to be fixed:

1. **File Size Limit for Certificado de Existencia**: The current file size limit is 10MB, but users need to upload files up to 50MB.

2. **Missing Domain DNS/Age Check in External Contacts**: The "Contactos Externos Individuales" functionality already has domain validation via DNS check and WHOIS age lookup implemented in the backend service, but it's not being surfaced properly in the UI or there may be inconsistencies in how results are displayed.

3. **EmailChainDiscrepancy Validation Error**: When using the email thread functionality with text upload, the app extracts email addresses for domain check but throws a Pydantic validation error:
   ```
   1 validation error for EmailChainDiscrepancy document_value
   Input should be a valid string [type=string_type, input_value=['830116134', '9'], input_type=list]
   ```
   The error shows that `document_value` is receiving a list `['830116134', '9']` instead of a string.

## Problem Statement
1. Users cannot upload Certificado de Existencia documents larger than 10MB, limiting their ability to complete risk evaluations.
2. Domain existence and age validation needs to be properly exposed for external contact email validation.
3. The NIT normalization function returns a tuple `(base_digits, check_digit)` but the code that consumes it treats it as a string, causing Pydantic validation errors when building EmailChainDiscrepancy objects.

## Solution Statement
1. Increase the `certificado_existencia` file size limit from 10MB to 50MB in both frontend and backend.
2. Verify domain DNS/age check is working for external contacts and ensure it's properly displayed in the UI.
3. Fix the `_get_document_data` method in `email_chain_service.py` to properly handle the tuple returned by `normalize_nit()` by joining the base and check digit into a single string.

## Steps to Reproduce

### Bug 1: File Size Limit
1. Navigate to Risk Dashboard
2. Open or create a risk evaluation
3. Attempt to upload a Certificado de Existencia PDF larger than 10MB
4. Error: "File too large. Maximum: 10MB"

### Bug 2: Domain DNS Check (to verify current state)
1. Navigate to Risk Dashboard
2. Open a risk evaluation
3. Go to "Contactos Externos" tab
4. Add an external contact with a corporate email
5. Click "Validar"
6. Verify that domain existence and age information is displayed

### Bug 3: EmailChainDiscrepancy Error
1. Navigate to Risk Dashboard
2. Open a risk evaluation with documents containing NITs
3. Go to "Contacto Externo" tab, "Cadenas de Email" section
4. Paste email text containing a NIT (e.g., "NIT: 830.116.134-9")
5. Upload the email chain
6. Click "Validar" to validate the email chain
7. Error: Pydantic validation error about document_value being a list

## Root Cause Analysis

### Bug 1: File Size Limit
The limit is hardcoded in two places:
- `frontend/src/types/risk.ts` line 448-453: `max_size_mb: 10`
- Backend `risk_routes.py` reads the limit from the frontend config via `get_document_type_info()`

### Bug 2: Domain DNS Check
After investigation, the domain DNS and age check IS already implemented in `external_contact_service.py` (lines 149-167, 201). The service performs:
- DNS existence check via `domain_validator.check_domain_existence(domain)`
- WHOIS age lookup via `domain_validator.get_domain_age(domain)`
- Results are included in `EmailValidationResult` model with fields:
  - `domain_exists`
  - `domain_age_days`
  - `domain_creation_date`
  - `domain_registrar`
  - `age_lookup_status`

This may just need UI verification or there could be a display issue.

### Bug 3: EmailChainDiscrepancy Error
In `backend/src/core/servicios/risk/email_chain_service.py`, the `_get_document_data` method at lines 333-339:

```python
for field in ['nit', 'nit_empresa', 'numero_identificacion']:
    value = extracted.get(field)
    if value:
        normalized = self.normalization_service.normalize_nit(str(value))
        if normalized and normalized not in doc_data['nits']:
            doc_data['nits'].append(normalized)
```

The `normalize_nit()` function in `normalization_service.py` returns a **tuple** `(base_digits, check_digit)`, not a string. When this tuple is appended to `doc_data['nits']` and later used in `_validate_nit_mention()` to build an `EmailChainDiscrepancy`, it's passed to `document_value` which expects a string, causing the Pydantic validation error.

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [x] Backend: adapter/rest (API routes) - for file size validation
- [x] Frontend: types
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services

## Relevant Files
Use these files to fix the bug:

### Bug 1 (File Size Limit)
- `frontend/src/types/risk.ts` (line 448-453) - Contains `DOCUMENT_TYPE_CONFIG` with `certificado_existencia.max_size_mb: 10` that needs to be changed to 50
- `backend/src/adapter/rest/risk_routes.py` (lines 920-927) - Backend validation reads from document config; verify it uses the same limit

### Bug 2 (Domain DNS Check) - Verification Only
- `backend/src/core/servicios/risk/external_contact_service.py` - Already has DNS and age check implemented; verify it works
- `backend/src/core/servicios/risk/domain_validation_service.py` - Contains the actual DNS/WHOIS logic
- `frontend/src/components/risk/FKExternalContactTab.tsx` - Frontend component displaying validation results; verify domain info is shown
- `frontend/src/types/risk.ts` - Contains `EmailValidationResult` interface with domain fields

### Bug 3 (EmailChainDiscrepancy Error)
- `backend/src/core/servicios/risk/email_chain_service.py` (lines 333-339, 609-674) - Contains `_get_document_data` and `_validate_nit_mention` methods that handle NIT normalization incorrectly
- `backend/src/core/servicios/risk/normalization_service.py` (lines 137-178) - Contains `normalize_nit()` function that returns `Tuple[str, Optional[str]]`
- `backend/src/interface/risk_dtos.py` (lines 641-649) - Contains `EmailChainDiscrepancy` model with `document_value: Optional[str]`

### E2E Test Reference Files
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/e2e_onhold/test_login.md` - Example E2E test format
- `.claude/commands/e2e/e2e_onhold/test_email_chain_validation.md` - Related email chain E2E test

### New Files
- `.claude/commands/e2e/test_fraud_risk_module_fixes.md` - New E2E test file to validate all three bug fixes

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix File Size Limit for Certificado de Existencia

1. Read `frontend/src/types/risk.ts` and locate the `DOCUMENT_TYPE_CONFIG` object
2. Change `certificado_existencia.max_size_mb` from `10` to `50`
3. Verify backend uses this config or has its own limit that needs updating
4. Read `backend/src/adapter/rest/risk_routes.py` to verify it reads from document config

### Step 2: Verify Domain DNS Check for External Contacts

1. Read `backend/src/core/servicios/risk/external_contact_service.py` to confirm DNS/age check implementation
2. Read `frontend/src/components/risk/FKExternalContactTab.tsx` to verify domain info is displayed in UI
3. Read `frontend/src/types/risk.ts` to verify `EmailValidationResult` interface includes domain fields
4. If UI is not showing domain info, add it to the component

### Step 3: Fix EmailChainDiscrepancy Validation Error

1. Read `backend/src/core/servicios/risk/normalization_service.py` and understand `normalize_nit()` return type
2. Read `backend/src/core/servicios/risk/email_chain_service.py` and locate:
   - `_get_document_data()` method (around line 333)
   - `_validate_nit_mention()` method (around line 609)
3. Fix `_get_document_data()` to convert the tuple to a string:
   ```python
   for field in ['nit', 'nit_empresa', 'numero_identificacion']:
       value = extracted.get(field)
       if value:
           base, check = self.normalization_service.normalize_nit(str(value))
           # Join base and check digit into a single string
           if base:
               normalized = f"{base}-{check}" if check else base
               if normalized not in doc_data['nits']:
                   doc_data['nits'].append(normalized)
   ```
4. Also fix `_validate_nit_mention()` to properly handle the normalization:
   ```python
   # Normalize the mentioned NIT
   base, check = self.normalization_service.normalize_nit(nit)
   normalized_mention = f"{base}-{check}" if check else base
   ```
5. Additionally, fix where `known_nits` from `client_snapshot` is normalized (around line 629):
   ```python
   if client_nit:
       base, check = self.normalization_service.normalize_nit(str(client_nit))
       normalized_client_nit = f"{base}-{check}" if check else base
       if normalized_client_nit and normalized_client_nit not in known_nits:
           known_nits.append(normalized_client_nit)
   ```

### Step 4: Create E2E Test File

1. Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/e2e_onhold/test_email_chain_validation.md` to understand E2E test format
2. Create `.claude/commands/e2e/test_fraud_risk_module_fixes.md` with tests for:
   - Uploading a large (>10MB, <50MB) Certificado de Existencia file
   - Verifying domain existence and age info is displayed for external contacts
   - Uploading an email chain with NIT mentions and validating without errors

### Step 5: Run Validation Commands

Execute all validation commands to ensure bug fixes work correctly with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Backend Validation
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd backend && python -c "from src.core.servicios.risk.email_chain_service import EmailChainService; from src.core.servicios.risk.normalization_service import NormalizationService; ns = NormalizationService(); print(ns.normalize_nit('830.116.134-9'))"` - Verify NIT normalization output format

### Frontend Validation
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

### Manual Verification Steps
1. Start the application locally (`./scripts/start.sh`)
2. **Test Bug 1**: Navigate to risk evaluation, upload a 30MB PDF as Certificado de Existencia - should succeed
3. **Test Bug 2**: Add an external contact with corporate email, validate, verify domain age/existence info shows
4. **Test Bug 3**: Upload email chain text with NIT mentions, validate - should complete without Pydantic errors

### E2E Test Validation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_fraud_risk_module_fixes.md` to validate all three bug fixes

## Notes

1. The `normalize_nit()` function returns a tuple for flexibility in comparing base vs check digits separately. The fix should join them back into a standard NIT format string when storing in `doc_data['nits']`.

2. For the external contact domain validation, the implementation already exists in the backend. If the UI is not showing the information, the fix is a frontend display issue, not a backend implementation issue.

3. The file size limit change only affects Certificado de Existencia. Other document types retain their current limits (RUT: 5MB, Cédula: 5MB, etc.).

4. The Pydantic error shows `['830116134', '9']` which appears to be Python's string representation of a tuple being interpreted as a list. This confirms the root cause is the tuple being passed where a string is expected.
