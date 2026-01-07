# Feature: Connect K° Crédito (Aval PN) Template for Paga Local Colombia

## Feature Description
Connect the existing Word template `FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx` to the Paga Local Colombia contracts generation module. This follows the same implementation pattern used for the K° Crédito (Aval PJ) template, enabling Operations users to generate credit contracts with personal guarantor (Persona Natural) support.

## User Story
As an Operations team member
I want to generate K° Crédito (Aval PN) contracts from the Paga Local Colombia module
So that I can create credit contracts for clients who have a personal guarantor (Persona Natural)

## Problem Statement
The Paga Local Colombia module has the UI and contract type enum defined for `pl_co_credito_aval_pn`, but the backend document generation routing is not connected. When a user requests this contract type, the system falls through to the default Activos template instead of using the correct Aval PN template.

## Solution Statement
Follow the exact same implementation pattern as the K° Crédito (Aval PJ) template:
1. Add routing in `document_service.py` to handle `pl_co_credito_aval_pn` contract type
2. Create a new method `generate_paga_local_credito_aval_pn_document()` that loads the Aval PN template
3. Add database migration to register the template in `contract_templates` table

## Access Control
- Required Role(s): `operations`, `admin`
- Backend Protection: `require_operations_role` dependency (already in place for contract generation)
- Frontend Protection: Already configured - Paga Local Colombia page is role-protected

## Relevant Files
Use these files to implement the feature:

- `backend/src/core/servicios/document_service.py` - Main document generation service. Need to add routing for `pl_co_credito_aval_pn` and create new generation method.
- `backend/src/interface/legal_dtos.py` - Contains `ContractType` enum. Already has `PL_CO_CREDITO_AVAL_PN = "pl_co_credito_aval_pn"` defined.
- `backend/templates/FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx` - The template file (already exists).
- `frontend/src/components/forms/FKPagaLocalCOCuentaCliente.tsx` - Frontend component with Aval PN tab (already configured with `type: 'pl_co_credito_aval_pn'`).
- `backend/database/migration_add_paga_local_aval_pj_template.sql` - Reference for creating the new migration.

### New Files
- `backend/database/migration_add_paga_local_aval_pn_template.sql` - Database migration to register the Aval PN template
- `implementations/20251205_legal_connect_credito_aval_pn_template.md` - Implementation documentation

## Implementation Plan

### Phase 1: Foundation
- Create database migration for the `pl_co_credito_aval_pn` contract template record
- No changes needed to DTOs (enum already exists)

### Phase 2: Core Implementation
- Add routing case for `pl_co_credito_aval_pn` in `generate_contract_document()` method
- Create `generate_paga_local_credito_aval_pn_document()` method following the Aval PJ pattern
- Reuse `_prepare_paga_local_replacements()` for placeholder substitution

### Phase 3: Integration
- Apply database migration to Supabase
- Test end-to-end contract generation
- Verify correct template is used

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Database Migration
- Create `backend/database/migration_add_paga_local_aval_pn_template.sql`
- Insert template record with:
  - `contract_type`: `'pl_co_credito_aval_pn'`
  - `version`: `'1.0.0'`
  - `template_content`: `'FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx'`
  - `active`: `true`
- Use `ON CONFLICT DO NOTHING` for idempotency
- Include verification SELECT statement

### Step 2: Add Routing in DocumentService
- Open `backend/src/core/servicios/document_service.py`
- In `generate_contract_document()` method (around line 72-73), add new elif case:
  ```python
  elif contract_type == 'pl_co_credito_aval_pn':
      return self.generate_paga_local_credito_aval_pn_document(contract_data)
  ```
- Add this BEFORE the `else` clause (which defaults to activos)

### Step 3: Create Generation Method
- In `document_service.py`, add new method `generate_paga_local_credito_aval_pn_document()` after the existing `generate_paga_local_credito_aval_pj_document()` method
- Copy the structure from `generate_paga_local_credito_aval_pj_document()` and modify:
  - Template name: `"FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx"`
  - Log messages to reference "Aval PN" instead of "Aval PJ"
  - Error message for missing template
- Reuse `_prepare_paga_local_replacements()` for data mapping (same as Aval PJ)

### Step 4: Apply Database Migration
- Run the migration SQL in Supabase SQL Editor
- Verify the template record was created with:
  ```sql
  SELECT * FROM contract_templates WHERE contract_type = 'pl_co_credito_aval_pn';
  ```

### Step 5: Test Locally
- Start backend server: `cd backend && python -m uvicorn main:app --reload`
- Start frontend: `cd frontend && npm run dev`
- Navigate to Operations > Paga Local Colombia
- Go to "Contratos Cuenta Cliente" > "Aval Persona Natural" tab
- Click "K° Crédito (Aval PN)"
- Search for a test client and submit contract request
- Go to Legal dashboard, find the contract, download DOCX
- Verify the document uses the Aval PN template (not Activos)

### Step 6: Create Implementation Documentation
- Create `implementations/20251205_legal_connect_credito_aval_pn_template.md`
- Document the changes made, files modified, and testing results

### Step 7: Run Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
- Verify `generate_paga_local_credito_aval_pn_document()` loads the correct template
- Verify routing in `generate_contract_document()` correctly routes `pl_co_credito_aval_pn`

### Edge Cases
- Template file missing - should raise FileNotFoundError with descriptive message
- Contract type is NULL - should fall back to data_snapshot (already implemented)
- Template record missing in database - contract service should raise ValueError

## Acceptance Criteria
- [ ] Database migration creates `pl_co_credito_aval_pn` template record
- [ ] `generate_contract_document()` routes `pl_co_credito_aval_pn` to the new method
- [ ] `generate_paga_local_credito_aval_pn_document()` method exists and loads correct template
- [ ] Downloaded DOCX uses `FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx` template
- [ ] Backend logs show "Loading Paga Local Crédito (Aval PN) template"
- [ ] All validation commands pass without errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -c "from src.core.servicios.document_service import DocumentService; print('DocumentService imports OK')"` - Verify DocumentService can be imported after changes
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd frontend && npm run lint` - Run frontend linting (no frontend changes expected)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- The template file `FK COL paga local - Fin. COP - K° Crédito (Aval PN).docx` already exists in `backend/templates/`
- The `ContractType.PL_CO_CREDITO_AVAL_PN` enum value already exists in `legal_dtos.py`
- The frontend UI already has the "Aval Persona Natural" tab with contract type `pl_co_credito_aval_pn` configured
- This is a straightforward copy-paste-modify pattern from the Aval PJ implementation
- The `_prepare_paga_local_replacements()` helper method is reused for all Paga Local templates
- After this implementation, only the Mandato contracts (PJ, PN, No Aval) and Documentos Operación remain to be connected
