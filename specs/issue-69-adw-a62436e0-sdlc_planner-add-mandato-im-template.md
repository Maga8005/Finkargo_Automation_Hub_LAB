# Bug: Missing contract_templates database record for pl_co_mandato_im

## Bug Description
When attempting to generate an Instrucción de Mandato document for a Paga Local Colombia operation, the system returns the error: `"Error al generar documento: Error generating contract: No active contract template found for type: pl_co_mandato_im"`. The form workflow completes successfully (client selection, Cotización PDF upload, bank certificate extraction, creditor information), but the backend fails to generate the document because it cannot find a template record in the database.

**Expected behavior:** The Instrucción de Mandato document should be generated successfully and placed in the Legal review queue with a contract ID like `PLMI-2025-001`.

**Actual behavior:** The API returns a 500 error with the message "No active contract template found for type: pl_co_mandato_im".

## Problem Statement
The `contract_service.py` method `generate_contract()` requires an active template record in the `contract_templates` database table to generate any contract. While the Word template file exists (`FK COL - Fin. COP - Mandato (IM).docx`) and the document generation code is implemented in `document_service.py`, there is no database migration that inserts a record for `pl_co_mandato_im` into the `contract_templates` table.

## Solution Statement
Create a new SQL migration file that inserts a template record for `pl_co_mandato_im` into the `contract_templates` table, following the same pattern as `migration_add_solicitud_desembolso_template.sql`. The template record must:
1. Set `contract_type` to `'pl_co_mandato_im'`
2. Set `template_content` to `'FK COL - Fin. COP - Mandato (IM).docx'` (the existing template file name)
3. Set `active` to `true`
4. Set `version` to `'1.0.0'`

## Steps to Reproduce
1. Login as an operations user
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click the "Documentos Operación" tab
4. Click the "Mandato (IM)" subtab
5. Search and select a client (e.g., NIT: 900436389)
6. Upload a Cotización PDF
7. Click "Extraer Datos del PDF"
8. Add at least one creditor with bank information (Razón Social, Banco, Tipo de Cuenta, Número de Cuenta)
9. Click "Generar Instrucción de Mandato"
10. Observe error: "Error al generar documento: Error generating contract: No active contract template found for type: pl_co_mandato_im"

## Root Cause Analysis
The `ContractService.generate_contract()` method in `backend/src/core/servicios/contract_service.py` (lines 74-76) performs a database lookup for an active template:

```python
# 2. Get active template for contract type
template = await self.template_repo.get_active_template(contract_type)
if not template:
    raise ValueError(f"No active contract template found for type: {contract_type}")
```

The `template_repo.get_active_template()` method queries the `contract_templates` table:

```python
response = self.db.table('contract_templates')\
    .select('*')\
    .eq('contract_type', contract_type)\
    .eq('active', True)\
    .execute()
```

For `pl_co_mandato_im`, there is no INSERT statement in any migration file. By contrast, the similar `pl_co_solicitud_desembolso` type has its own migration (`migration_add_solicitud_desembolso_template.sql`) that inserts its template record.

The components that ARE working:
- Word template file exists: `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- Document generation method exists: `document_service.generate_instruccion_mandato_document()` (line 932)
- Contract ID prefix exists in database: `PLMI` for `pl_co_mandato_im` (from `migration_add_paga_local_contract_id_prefixes.sql`)
- Sequence record exists for year-based ID generation

The ONLY missing piece is the `contract_templates` database record.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types
- [x] Database: migration required

## Relevant Files
Use these files to fix the bug:

- **`backend/database/migration_add_solicitud_desembolso_template.sql`**
  - Reference file for the correct INSERT statement format
  - Shows the exact pattern for adding a template record to `contract_templates` table

- **`backend/src/core/servicios/contract_service.py`** (lines 74-76)
  - Shows where the template lookup happens and the error is raised
  - Confirms the exact error message format

- **`backend/src/repositorio/template_repository.py`** (lines 20-36)
  - Shows the `get_active_template()` method that queries the database
  - Confirms the table name and required columns

- **`backend/templates/FK COL - Fin. COP - Mandato (IM).docx`**
  - Verify this file exists (it does based on `ls` output)
  - The exact filename must match the `template_content` value in the INSERT

- **`.claude/commands/test_e2e.md`**
  - Read to understand E2E test format

- **`.claude/commands/e2e/test_login.md`**
  - Read to understand E2E test login procedure

- **`.claude/commands/e2e/test_instruccion_mandato_form.md`**
  - Existing E2E test file to validate the bug fix

### New Files
- **`backend/database/migration_add_instruccion_mandato_template.sql`** - New migration file to insert the template record

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Verify the Bug Exists

1. Start development servers: `./scripts/start-dev.sh`
2. Check backend logs while attempting to generate an Instrucción de Mandato
3. Confirm the error message matches: `No active contract template found for type: pl_co_mandato_im`
4. Verify the template file exists: `ls -la backend/templates/ | grep "Mandato (IM)"`

### Task 2: Verify Reference Migration Pattern

- Read `backend/database/migration_add_solicitud_desembolso_template.sql`
- Note the INSERT statement structure:
  ```sql
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
  ```

### Task 3: Create Migration File for pl_co_mandato_im

Create a new file `backend/database/migration_add_instruccion_mandato_template.sql` with:

```sql
/*
 * Migration: Add Instrucción de Mandato Contract Template
 * Created: 2025-12-07
 * Author: SDLC Agent
 *
 * Purpose:
 * Adds the contract template record for Instrucción de Mandato (PLMI) documents
 * in the Paga Local Colombia module.
 *
 * This fixes the bug where document generation fails with:
 * "No active contract template found for type: pl_co_mandato_im"
 *
 * The Word template file already exists at:
 * backend/templates/FK COL - Fin. COP - Mandato (IM).docx
 */

-- Insert template record for Instrucción de Mandato
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_im',
    '1.0.0',
    'FK COL - Fin. COP - Mandato (IM).docx',
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
WHERE contract_type = 'pl_co_mandato_im';
```

### Task 4: Apply the Migration to the Database

**Option A (Production/Staging via Supabase Dashboard):**
1. Open Supabase Dashboard → SQL Editor
2. Copy the migration SQL content
3. Execute the migration
4. Verify the record was created with the SELECT statement

**Option B (For local development with direct DB access):**
```bash
# If using psql client
psql $DATABASE_URL -f backend/database/migration_add_instruccion_mandato_template.sql
```

### Task 5: Restart Backend Server

After applying the migration:
```bash
# Stop and restart development servers
./scripts/stop-dev.sh
./scripts/start-dev.sh
```

### Task 6: Test the Fix Manually

1. Login as operations user (or use existing session)
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click "Documentos Operación" tab
4. Click "Mandato (IM)" subtab
5. Search and select a client (e.g., NIT: 900436389)
6. Upload a Cotización PDF
7. Click "Extraer Datos del PDF"
8. Fill in at least one creditor with:
   - Razón Social: Any company name
   - Banco: Any bank name
   - Tipo de Cuenta: Ahorros, Corriente, or PCE
   - Número de Cuenta: Any account number
9. Click "Generar Instrucción de Mandato"
10. Verify success message with contract ID format: `PLMI-2025-XXX`

### Task 7: Run Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && ruff check src/` - Run backend linting
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_instruccion_mandato_form.md` to validate the complete workflow end-to-end

## Notes

### Database Migration Required
This is a database-only fix. No code changes are needed because:
- The API endpoint is already implemented correctly (`operations_routes.py`)
- The document generation method exists (`document_service.generate_instruccion_mandato_document()`)
- The frontend form component works correctly (`FKInstruccionMandatoForm.tsx`)
- The contract ID prefix (PLMI) is already configured
- The only missing piece is the database record

### Similar Pattern
This follows the exact same fix pattern as `migration_add_solicitud_desembolso_template.sql` which fixed the identical issue for `pl_co_solicitud_desembolso`.

### No Code Changes Required
This bug fix is purely a database migration. After the migration is applied:
- No backend code needs to change
- No frontend code needs to change
- No tests need to be updated

### Post-Fix Verification
After applying the migration, verify the template record exists:
```sql
SELECT * FROM contract_templates WHERE contract_type = 'pl_co_mandato_im';
```

Expected result: One row with `active = true` and `template_content = 'FK COL - Fin. COP - Mandato (IM).docx'`
