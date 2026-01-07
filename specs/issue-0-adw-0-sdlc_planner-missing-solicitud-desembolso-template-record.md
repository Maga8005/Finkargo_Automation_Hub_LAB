# Bug: Missing Database Template Record for Solicitud de Desembolso

## Bug Description
When attempting to generate a Solicitud de Desembolso document in the Paga Local Colombia Operations workflow, after successfully selecting a customer and uploading the Cotización PDF, the document generation fails with the error:

**Error message**: "Error al generar solicitud: No active contract template found for type: pl_co_solicitud_desembolso"

**Expected behavior**: The system should generate a Solicitud de Desembolso (PLSD) contract and submit it to the Legal review queue.

**Actual behavior**: The contract generation fails at the template lookup step because there is no record in the `contract_templates` database table for the contract type `pl_co_solicitud_desembolso`.

## Problem Statement
The Solicitud de Desembolso feature implementation is incomplete. While the:
- Word template file exists: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
- Contract type enum is defined: `PL_CO_SOLICITUD_DESEMBOLSO = "pl_co_solicitud_desembolso"` in `legal_dtos.py`
- Contract ID prefix is configured (PLSD) in database functions
- Document generation method exists: `generate_solicitud_desembolso_document()` in `document_service.py`
- Frontend form and API endpoints are complete

**The missing piece**: There is no record in the `contract_templates` table for `pl_co_solicitud_desembolso`. The `ContractService.generate_contract()` method requires an active template record (line 74-76 in `contract_service.py`) and fails when none is found.

## Solution Statement
Create a SQL migration to insert an active template record for `pl_co_solicitud_desembolso` into the `contract_templates` table. This follows the established pattern used for other Paga Local contract types (e.g., `migration_add_paga_local_sin_aval_templates.sql`).

The migration will:
1. Insert a new record with `contract_type = 'pl_co_solicitud_desembolso'`
2. Set `template_content` to the template filename: `'FK COL - Fin. COP - Solicitud de Desembolso.docx'`
3. Set `active = true` to make it the active template
4. Use `ON CONFLICT DO NOTHING` for idempotency

## Steps to Reproduce
1. Login as an Operations user (or Admin)
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click on the "Solicitud de Desembolso" tab
4. Search for and select a client (e.g., NIT: 901234567)
5. Upload a valid Cotización PDF file
6. Click "Extraer Datos" to extract data from the PDF
7. Verify extracted data populates the form
8. Click "Solicitar Documento" button
9. **Observe error**: "Error al generar solicitud: No active contract template found for type: pl_co_solicitud_desembolso"

## Root Cause Analysis
The error originates in `backend/src/core/servicios/contract_service.py` at lines 74-76:

```python
# 2. Get active template for contract type
template = await self.template_repo.get_active_template(contract_type)
if not template:
    raise ValueError(f"No active contract template found for type: {contract_type}")
```

The `template_repo.get_active_template()` method queries the `contract_templates` table for a record where:
- `contract_type = 'pl_co_solicitud_desembolso'`
- `active = True`

No such record exists because the database migration for this contract type was never created. The implementation of the Solicitud de Desembolso feature added:
- Frontend components (`FKSolicitudDesembolsoRequest.tsx`)
- API endpoints (`operations_routes.py`)
- Document generation logic (`document_service.py`)
- Contract ID prefix configuration (database function)

But omitted the crucial step of inserting the template record in the database.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [x] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

Note: While the root cause is missing database data (not code), the fix is a database migration, which falls under the repositorio/data access layer.

## Relevant Files
Use these files to fix the bug:

- `backend/database/migration_add_paga_local_sin_aval_templates.sql` - Reference pattern for inserting template records. Shows the exact SQL structure needed for `contract_templates` table inserts.
- `backend/src/core/servicios/contract_service.py:74-76` - Where the error is raised. Confirms the `contract_type` value that needs a matching template record.
- `backend/src/repositorio/template_repository.py:20-36` - Shows `get_active_template()` method that queries the `contract_templates` table.
- `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx` - The template file that needs to be referenced in the database record.
- `.claude/commands/test_e2e.md` - Read to understand how to create an E2E test file.
- `.claude/commands/e2e/test_login.md` - Example E2E test structure to follow.

### New Files
- `backend/database/migration_add_solicitud_desembolso_template.sql` - New migration to insert the template record
- `.claude/commands/e2e/test_solicitud_desembolso_generation.md` - E2E test file to validate the bug fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Create Database Migration for Template Record
- Create new file `backend/database/migration_add_solicitud_desembolso_template.sql`
- Use `migration_add_paga_local_sin_aval_templates.sql` as reference pattern
- Insert a record into `contract_templates` with:
  - `contract_type`: `'pl_co_solicitud_desembolso'`
  - `version`: `'1.0.0'`
  - `template_content`: `'FK COL - Fin. COP - Solicitud de Desembolso.docx'`
  - `active`: `true`
  - `created_at`: `NOW()`
- Use `ON CONFLICT (contract_type, version) DO NOTHING` for idempotency
- Add verification query at the end to confirm insertion

### Task 2: Apply Migration to Database
- Execute the migration SQL in Supabase SQL Editor:
  1. Open Supabase dashboard
  2. Navigate to SQL Editor
  3. Paste and run the migration SQL
  4. Verify the record was created with the verification query
- Alternatively, if using local development database, apply via CLI

### Task 3: Verify Fix via API Call
- Restart backend server to pick up any cached state: `cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Use curl or the frontend to test the flow:
  1. Login as Operations user
  2. Navigate to Solicitud de Desembolso form
  3. Select client, upload PDF, extract data
  4. Click "Solicitar Documento"
  5. Verify contract is created with PLSD-YYYY-XXX format
  6. Verify contract appears in Legal review queue

### Task 4: Create E2E Test File
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand E2E test structure
- Create `.claude/commands/e2e/test_solicitud_desembolso_generation.md` that validates:
  1. Login as operations user
  2. Navigate to Paga Local Colombia contracts
  3. Select "Solicitud de Desembolso" tab
  4. Search and select a test client
  5. Upload a test Cotización PDF
  6. Extract data from PDF
  7. Submit the form
  8. Verify success message appears (no error)
  9. Navigate to Legal review queue
  10. Verify PLSD contract appears with correct status
- Include screenshots at key steps to prove the bug is fixed

### Task 5: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Verify backend tests pass
- Verify frontend builds successfully
- If E2E test was created, read `.claude/commands/test_e2e.md` and execute the E2E test

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Verify template record exists in database (run in Supabase SQL Editor)
SELECT id, contract_type, version, template_content, active, created_at
FROM contract_templates
WHERE contract_type = 'pl_co_solicitud_desembolso';
# Expected: 1 row with active=true

# Run backend tests to validate bug fix with zero regressions
cd backend && python -m pytest

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

If E2E test was created:
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_solicitud_desembolso_generation.md` test file to validate this functionality works.

## Notes

### Migration SQL Reference
The migration SQL should look like this (following established pattern):

```sql
/*
 * Migration: Add Solicitud de Desembolso Contract Template
 * Created: 2025-12-07
 *
 * Purpose:
 * Adds the contract template record for Solicitud de Desembolso (PLSD) documents
 * in the Paga Local Colombia module.
 */

INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_solicitud_desembolso',
    '1.0.0',
    'FK COL - Fin. COP - Solicitud de Desembolso.docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;

-- Verify insertion
SELECT
    id,
    contract_type,
    version,
    template_content,
    active,
    created_at
FROM contract_templates
WHERE contract_type = 'pl_co_solicitud_desembolso';
```

### No Code Changes Required
This bug fix only requires a database migration. No backend or frontend code changes are needed - all the code logic is already implemented correctly. The missing piece is purely data in the `contract_templates` table.

### Production Deployment
After the migration is tested locally, it should be applied to the production Supabase database to fix the issue in production.
