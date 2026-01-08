# Bug: 400 Error When Generating K° Crédito (Aval PJ) Contract

## Bug Description
When a user attempts to generate a K° Crédito (Aval PJ) contract from the Paga Local Colombia > Contratos Cuenta Cliente > Aval Persona Jurídica section, the system returns a 400 error with the message "Request failed with status code 400". The contract generation fails before document creation because the system cannot find an active template record in the database for the `pl_co_credito_aval_pj` contract type.

**Expected behavior:** The contract should be generated successfully and sent for legal review.

**Actual behavior:** 400 error is returned, contract is not generated.

## Problem Statement
The `contract_service.py` requires an active template record in the `contract_templates` database table for each contract type before it can generate contracts. While the document generation code was added to `document_service.py`, the corresponding database template record and contract ID prefix were never created for `pl_co_credito_aval_pj`.

## Solution Statement
Create a database migration to:
1. Insert an active template record for `pl_co_credito_aval_pj` in the `contract_templates` table
2. Add the contract ID prefix for `pl_co_credito_aval_pj` to the `contract_id_sequence` table (if needed)

This follows the exact pattern used for the `pl_co_credito_no_aval` contract type in `migration_add_paga_local_sin_aval_templates.sql`.

## Steps to Reproduce
1. Login to the Finkargo Automation Hub
2. Navigate to Operations > Paga Local Colombia
3. Go to "Contratos Cuenta Cliente" tab
4. Click on "Aval Persona Jurídica" subtab
5. Click "Solicitar" on the "K° Crédito (Aval PJ)" card
6. Search for a client by NIT
7. Select a client and click "Solicitar K° Crédito (Aval PJ)"
8. **Result:** Error message "Request failed with status code 400"

## Root Cause Analysis
The contract generation flow in `contract_service.py` (line 72-74) requires an active template record:
```python
template = await self.template_repo.get_active_template(contract_type)
if not template:
    raise ValueError(f"No active contract template found for type: {contract_type}")
```

When a user requests a `pl_co_credito_aval_pj` contract:
1. The frontend sends `contract_type: "pl_co_credito_aval_pj"` to `/api/operations/contracts/generate`
2. The backend validates the contract type enum (passes)
3. The backend queries `contract_templates` for an active template with `contract_type = 'pl_co_credito_aval_pj'`
4. No record exists → `ValueError` is raised → HTTP 400 response

The document generation method `generate_paga_local_credito_aval_pj_document()` was added to `document_service.py`, but the prerequisite database record was never created.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`backend/database/migration_add_paga_local_sin_aval_templates.sql`** - Reference for how to create template records. Follow this exact pattern.
- **`backend/database/migration_add_paga_local_contract_id_prefixes.sql`** - Reference for how contract ID prefixes are added for Paga Local contract types.
- **`backend/src/core/servicios/contract_service.py`** (lines 72-74) - Location where the template lookup fails.
- **`backend/src/repositorio/template_repository.py`** (lines 20-36) - Shows the query structure for template lookup.

### New Files
- **`backend/database/migration_add_paga_local_aval_pj_template.sql`** - New migration file to add the template record for `pl_co_credito_aval_pj`.

## Step by Step Tasks

### Step 1: Review Existing Migration for Reference
- Read `backend/database/migration_add_paga_local_sin_aval_templates.sql` to understand the exact SQL structure needed
- Read `backend/database/migration_add_paga_local_contract_id_prefixes.sql` to understand if contract ID prefix is needed

### Step 2: Create Database Migration File
- Create new file: `backend/database/migration_add_paga_local_aval_pj_template.sql`
- Add INSERT statement for `pl_co_credito_aval_pj` template record with:
  - `contract_type`: `'pl_co_credito_aval_pj'`
  - `version`: `'1.0.0'`
  - `template_content`: `'FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx'`
  - `active`: `true`
- Add verification SELECT statement
- Use `ON CONFLICT DO NOTHING` for idempotency

### Step 3: Apply Migration to Database
- Execute the migration SQL in Supabase SQL Editor
- Verify the record was created by querying `contract_templates` table

### Step 4: Test Contract Generation
- Restart backend server to clear any caches
- Attempt to generate a K° Crédito (Aval PJ) contract
- Verify the contract is created successfully with status "under_review"

### Step 5: Run Validation Commands
- Execute all validation commands to ensure no regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd /c/Users/Usuario/Finkargo_Automation_Hub/backend && python -c "from src.core.servicios.document_service import DocumentService; print('Import successful')"` - Verify DocumentService imports without errors
- `cd /c/Users/Usuario/Finkargo_Automation_Hub/frontend && npx tsc --noEmit` - Run TypeScript type check

## Notes
- This is a database-only fix. No code changes are required.
- The same pattern will need to be repeated for `pl_co_credito_aval_pn` (Aval PN template) to enable that contract type.
- The migration should be idempotent using `ON CONFLICT DO NOTHING` to avoid errors if run multiple times.
- After applying the migration, the contract ID prefix may need to be added to the `contract_id_prefixes` table if it's used for sequential ID generation (e.g., "PLCAPJ-2025-001").
