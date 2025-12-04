# Bug: K° Crédito (No Aval) Contract Generation Returns 400 Error

## Bug Description
When attempting to generate a "K° Crédito (No Aval)" contract (`pl_co_credito_no_aval`) from the Operations Paga Local Colombia module, the backend returns a 400 Bad Request error with the message:

```
No active contract template found for type: pl_co_credito_no_aval
```

The UI workflow works correctly (client search, selection), but contract generation fails at the backend validation step.

**Expected behavior**: Contract should be generated successfully, creating a Word document populated with client data.

**Actual behavior**: 400 error returned, no contract generated.

## Problem Statement
The database is missing the contract template records for `pl_co_credito_no_aval` and `pl_co_mandato_no_aval` contract types. A migration file exists (`migration_add_paga_local_sin_aval_templates.sql`) but was never executed against the Supabase database.

## Solution Statement
Execute the existing migration SQL to insert the required template records into the `contract_templates` table. This is a database configuration issue, not a code bug - all backend code is already in place.

## Steps to Reproduce
1. Login as `admin@finkargo.com` or operations user
2. Navigate to `/operations/paga-local-colombia`
3. Select "Contratos Marco - Sin Aval" section
4. Click "K° Crédito (No Aval)" contract type
5. Search for a client (e.g., "test")
6. Select a client and click "Solicitar K° Crédito (No Aval)"
7. **Error**: 400 Bad Request - "No active contract template found for type: pl_co_credito_no_aval"

## Root Cause Analysis
The contract generation flow requires:
1. ✅ Client data exists in database
2. ✅ Contract type enum defined in `legal_dtos.py` (line 26: `PL_CO_CREDITO_NO_AVAL`)
3. ✅ Document generation code exists in `document_service.py` (lines 182-242)
4. ✅ Template file exists: `backend/templates/FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`
5. ❌ **MISSING**: Contract template record in `contract_templates` database table

The `ContractService.generate_contract()` method queries for an active template:
```python
template = await self.template_repo.get_active_template(contract_type)
if not template:
    raise ValueError(f"No active contract template found for type: {contract_type}")
```

Since no template record exists in the database for `pl_co_credito_no_aval`, this validation fails.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types
- [x] **Database**: contract_templates table (missing data)

## Relevant Files
Use these files to fix the bug:

- `backend/database/migration_add_paga_local_sin_aval_templates.sql` - **The migration file that needs to be executed**. Contains INSERT statements for both `pl_co_credito_no_aval` and `pl_co_mandato_no_aval` templates.

- `backend/src/core/servicios/contract_service.py` - Contains the validation logic that checks for active templates. **No code changes needed** - this file works correctly.

- `backend/src/repositorio/template_repository.py` - Repository that queries the `contract_templates` table. **No code changes needed**.

- `backend/templates/FK COL paga local - Fin. COP - K° Crédito (No Aval).docx` - The Word template file. **Already exists and ready**.

- `backend/templates/FK COL paga local - Fin. COP - K° Mandato.docx` - The K° Mandato template file. **Already exists and ready**.

### New Files
None - this is a database configuration issue, not a code issue.

## Step by Step Tasks

### Step 1: Verify Current Database State
- Connect to Supabase SQL Editor
- Run query to check if templates exist:
  ```sql
  SELECT contract_type, version, active, template_content
  FROM contract_templates
  WHERE contract_type LIKE 'pl_co_%'
  ORDER BY contract_type;
  ```
- Expected result: No rows returned for `pl_co_credito_no_aval` and `pl_co_mandato_no_aval`

### Step 2: Execute the Migration
- Open Supabase SQL Editor for the project
- Copy the contents of `backend/database/migration_add_paga_local_sin_aval_templates.sql`
- Execute the SQL statements
- Verify the INSERT was successful by checking the query output

### Step 3: Verify Template Records Created
- Run verification query:
  ```sql
  SELECT id, contract_type, version, template_content, active, created_at
  FROM contract_templates
  WHERE contract_type IN ('pl_co_credito_no_aval', 'pl_co_mandato_no_aval')
  ORDER BY contract_type;
  ```
- Expected: 2 rows returned with `active = true`

### Step 4: Update Error Message (Optional Improvement)
- File: `backend/src/adapter/rest/operations_routes.py` (line 94)
- Update the error message to dynamically list all valid contract types from the enum instead of hardcoded list
- Current: `"Must be one of: activos, otrosi, inventario_bodega"`
- Should be: Dynamic list from `ContractType` enum

### Step 5: Create E2E Test
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` for reference
- Create new E2E test file: `.claude/commands/e2e/test_paga_local_credito_no_aval.md`
- Test should validate:
  1. Login as operations/admin user
  2. Navigate to Paga Local Colombia page
  3. Select Sin Aval section
  4. Search for a client
  5. Select client and request K° Crédito (No Aval)
  6. Verify contract is generated successfully (no 400 error)
  7. Verify contract appears in pending review queue

### Step 6: Run Validation Commands

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Before fix (reproduce bug):**
```bash
# Call the API endpoint to verify 400 error
curl -X POST "http://localhost:8000/api/operations/contracts/generate" \
  -H "Authorization: Bearer <token>" \
  -F "client_nit=900123459-1" \
  -F "contract_type=pl_co_credito_no_aval"
# Expected: 400 error with "No active contract template found"
```

**After fix (verify success):**
```bash
# Same API call should now succeed
curl -X POST "http://localhost:8000/api/operations/contracts/generate" \
  -H "Authorization: Bearer <token>" \
  -F "client_nit=900123459-1" \
  -F "contract_type=pl_co_credito_no_aval"
# Expected: 201 Created with contract details
```

**Database verification:**
```sql
SELECT contract_type, version, active
FROM contract_templates
WHERE contract_type IN ('pl_co_credito_no_aval', 'pl_co_mandato_no_aval');
-- Expected: 2 rows with active = true
```

- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test `.claude/commands/e2e/test_paga_local_credito_no_aval.md` to validate this functionality works.

- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- This is primarily a **database configuration issue**, not a code bug
- The migration file already exists and is correct - it just needs to be executed
- Both K° Crédito (No Aval) and K° Mandato (No Aval) templates should be inserted together
- After fixing, the same pattern will work for `pl_co_mandato_no_aval` contract type
- Consider adding a startup check or migration script that validates required templates exist
- The template files in `backend/templates/` are already properly named to match the `template_content` field values in the migration
