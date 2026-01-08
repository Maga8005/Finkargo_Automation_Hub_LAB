# Feature: Paga Local Contratos marco - Sin Aval Template Implementation

## Feature Description
Implement Word template processing for the two "Sin Aval" (No Guarantee) contract types in the Paga Local Colombia module. These contracts (`pl_co_credito_no_aval` and `pl_co_mandato_no_aval`) currently have UI components but lack backend document generation functionality. The implementation will enable automatic population of Word templates with client data from the database, following the same pattern as the working "Contrato de Activos" implementation.

The templates are already placed in the `backend/templates/` directory:
- **K° Crédito (No Aval)**: `FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`
- **K° Mandato**: `FK COL paga local - Fin. COP - K° Mandato.docx`

## User Story
As an Operations team member
I want to generate "Sin Aval" contracts for Paga Local Colombia clients
So that Legal can review pre-filled contract documents and approve them for client delivery

## Problem Statement
The Paga Local Colombia "Sin Aval" contract types were added to the UI as part of the module implementation (issue tracked in `specs/chore-paga-local-contracts-section.md` and `implementations/20251202_operations_paga_local_colombia.md`), but the backend document generation service does not yet support these contract types. When Operations users request these contracts, the system cannot populate the Word templates with client data, preventing contract generation and approval workflows.

## Solution Statement
Extend the `DocumentService` class to support the two "Sin Aval" contract types by:
1. Adding template mapping logic to route these contract types to appropriate generation methods
2. Creating dedicated generation methods that load the Word templates and replace bracketed placeholders (e.g., `[NOMBRE DEL CLIENTE]`) with actual client data
3. Inserting template records in the database to enable template versioning and tracking
4. Following the existing pattern established for Activos, Otrosí, and Inventario Bodega contracts

## Access Control
- **Required Role(s)**: `operations` (to request contracts), `legal` (to review and approve)
- **Backend Protection**: Uses existing RBAC pattern with `require_roles(['operations', 'legal', 'admin'])` in operations routes
- **Frontend Protection**: Already implemented - routes protected by `ProtectedRoute` component, components use `RoleProtectedRoute` for operations/legal access

## Relevant Files
Use these files to implement the feature:

### Backend Files

**Document Generation Service:**
- `backend/src/core/servicios/document_service.py` (lines 34-58) - Main routing logic in `generate_contract_document()` method that dispatches to contract-type-specific methods. Add routing for `pl_co_credito_no_aval` and `pl_co_mandato_no_aval`.
- `backend/src/core/servicios/document_service.py` (lines 60-114) - Reference implementation in `generate_activos_document()` showing template loading, placeholder replacement, and DOCX generation pattern to follow.
- `backend/src/core/servicios/document_service.py` (lines 337-430) - Helper method `_prepare_replacements()` that creates the placeholder-to-value mapping from contract data. May need extension for Paga Local specific fields.

**Contract Service:**
- `backend/src/core/servicios/contract_service.py` (lines 41-136) - Orchestrates contract generation flow: validates client, fetches template, generates contract ID, creates data snapshot. No changes needed but important context.

**DTOs and Types:**
- `backend/src/interface/legal_dtos.py` (lines 25-27) - Already contains `PL_CO_CREDITO_NO_AVAL` and `PL_CO_MANDATO_NO_AVAL` enum values in `ContractType`.

**Database:**
- `backend/database/combined_schema.sql` (lines 29-51) - `contract_templates` table schema showing version, contract_type, template_content (filename), and active flag.

### Template Files

**Word Templates:**
- `backend/templates/FK COL paga local - Fin. COP - K° Crédito (No Aval).docx` - Template for credit contract without guarantee
- `backend/templates/FK COL paga local - Fin. COP - K° Mandato.docx` - Template for mandate contract without guarantee

### Reference Documentation

**System Overview:**
- `specs/contract_generation_system_overview.md` (lines 132-194) - Documents standard placeholder system used across all contract types (e.g., `[NOMBRE DEL CLIENTE]`, `[NIT]`, `[valor Cupo de Operaciones en numeros]`)
- `specs/contract_generation_system_overview.md` (lines 386-499) - Step-by-step guide for adding new contract types, showing database migrations, DTO updates, service changes, and frontend integration.

**Implementation References:**
- `implementations/20251110_inventario_bodega_contract_type_implementation.md` - Complete example of adding a new contract type with custom placeholders
- `implementations/20251106_Otrosi_Contract_Type_Implementation.md` - Another reference implementation showing the full pattern

**Paga Local Module:**
- `specs/chore-paga-local-contracts-section.md` - Original spec defining all 9 Paga Local Colombia contract types
- `implementations/20251202_operations_paga_local_colombia.md` - Implementation report showing UI/frontend work completed

### Frontend Files (Context Only - No Changes Needed)
- `frontend/src/components/forms/FKPagaLocalCOCuentaCliente.tsx` (lines 88-104) - Shows the "Sin Aval" subtab configuration with the two contract type buttons already implemented
- `frontend/src/components/forms/FKPagaLocalCOContractRequest.tsx` - Reusable request form that calls the operations service, already supports these contract types
- `frontend/src/services/operationsService.ts` - Service layer that calls backend API, already configured for these types

### Testing Reference
- `.claude/commands/test_e2e.md` - E2E test runner pattern using Playwright
- `.claude/commands/e2e/test_login.md` - Example E2E test file structure
- `.claude/commands/e2e/test_contract_request.md` - Contract request workflow test pattern

### New Files
- `backend/database/migration_add_paga_local_sin_aval_templates.sql` - Database migration to insert template records for the two contract types
- `.claude/commands/e2e/test_paga_local_sin_aval_contracts.md` - E2E test specification to validate the complete workflow

## Implementation Plan

### Phase 1: Foundation
**Database Preparation:**
- Create database migration file to insert template records into `contract_templates` table for both contract types
- Set contract_type values: `pl_co_credito_no_aval` and `pl_co_mandato_no_aval`
- Set template_content to exact template filenames: `FK COL paga local - Fin. COP - K° Crédito (No Aval).docx` and `FK COL paga local - Fin. COP - K° Mandato.docx`
- Set version to `1.0.0` and active to `true`
- Execute migration in Supabase SQL Editor

**Template Analysis:**
- Open both Word templates and identify all bracketed placeholders (e.g., `[NOMBRE DEL CLIENTE]`, `[NIT]`)
- Document any Paga Local specific placeholders that differ from standard Activos placeholders
- Verify placeholders match fields available in client data snapshot

### Phase 2: Core Implementation
**Document Service Enhancement:**
- Update `generate_contract_document()` routing logic to handle `pl_co_credito_no_aval` and `pl_co_mandato_no_aval`
- Create two new generation methods:
  - `generate_paga_local_credito_no_aval_document()` - For credit contract
  - `generate_paga_local_mandato_no_aval_document()` - For mandate contract
- Each method follows the pattern: load template → prepare replacements → replace in paragraphs → replace in tables → return DOCX bytes
- Reuse `_prepare_replacements()` helper if placeholders are standard, or create `_prepare_paga_local_no_aval_replacements()` if custom placeholders are needed
- Add comprehensive logging for debugging

**Template Placeholder Mapping:**
- Map client database fields to template placeholders:
  - `[NOMBRE DEL CLIENTE]` → `nombre_importador`
  - `[NIT]` → `nit`
  - `[Nombre del representante legal]` → `representante_legal`
  - `[identificacion RL]` → `cedula_representante`
  - `[nombre de la ciudad]` → `ciudad_domicilio`
  - `[valor Cupo de Operaciones en numeros]` → formatted `cupo_plataforma`
  - `[valor Cupo de Operaciones en letras]` → number-to-words conversion
  - `[sic]` → `contract_id`
  - Date placeholders: `[dia]`, `[mes]`, `[•]` (year last digit)
  - Contact info: `[nombre del KAM]`, `[KAM e-mail]`, `[nombre del destinatario]`, `[destinatario e-mail]`

### Phase 3: Integration
**Testing and Validation:**
- Test document generation with sample client data
- Verify all placeholders are replaced correctly
- Ensure DOCX files open without corruption
- Test PDF conversion using LibreOffice
- Validate storage upload to Supabase Storage

**End-to-End Validation:**
- Create E2E test specification
- Test complete workflow: login → navigate → search client → request contract → verify under_review status
- Verify Legal can download DOCX/PDF and approve
- Verify approved PDF appears in Operations approved contracts list

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze Template Placeholders
- Open the two Word template files in `backend/templates/`:
  - `FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`
  - `FK COL paga local - Fin. COP - K° Mandato.docx`
- Document all bracketed placeholders found (e.g., `[NOMBRE DEL CLIENTE]`, `[NIT]`)
- Compare with standard placeholders listed in `specs/contract_generation_system_overview.md` (lines 139-180)
- Identify any Paga Local specific placeholders that are not standard
- Determine if we can reuse `_prepare_replacements()` or need a custom method

### Step 2: Create Database Migration
- Create `backend/database/migration_add_paga_local_sin_aval_templates.sql`
- Write SQL INSERT statements for both contract types into `contract_templates` table:
  - contract_type: `pl_co_credito_no_aval`, version: `1.0.0`, template_content: `FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`, active: `true`
  - contract_type: `pl_co_mandato_no_aval`, version: `1.0.0`, template_content: `FK COL paga local - Fin. COP - K° Mandato.docx`, active: `true`
- Add descriptive notes explaining each template's purpose
- Document migration in file header with creation date and purpose

### Step 3: Update DocumentService Routing Logic
- Edit `backend/src/core/servicios/document_service.py`
- In the `generate_contract_document()` method (around line 49-56), add routing for the two new contract types:
  ```python
  elif contract_type == 'pl_co_credito_no_aval':
      return self.generate_paga_local_credito_no_aval_document(contract_data)
  elif contract_type == 'pl_co_mandato_no_aval':
      return self.generate_paga_local_mandato_no_aval_document(contract_data)
  ```
- Add this after the existing `inventario_bodega` check and before the `else` clause

### Step 4: Implement K° Crédito (No Aval) Generation Method
- Add new method `generate_paga_local_credito_no_aval_document()` to `DocumentService`
- Follow the exact pattern from `generate_activos_document()` (lines 60-114):
  - Define template_name parameter with default: `"FK COL paga local - Fin. COP - K° Crédito (No Aval).docx"`
  - Load template using `Document(str(template_path))`
  - Call `_prepare_replacements()` or custom replacement method
  - Iterate through paragraphs and call `_replace_in_paragraph()`
  - Iterate through tables and replace in all cell paragraphs
  - Save to temporary file and return bytes
- Add comprehensive logging at each step
- Add docstring explaining purpose, args, returns, and raises

### Step 5: Implement K° Mandato (No Aval) Generation Method
- Add new method `generate_paga_local_mandato_no_aval_document()` to `DocumentService`
- Follow the same pattern as K° Crédito method:
  - Define template_name parameter with default: `"FK COL paga local - Fin. COP - K° Mandato.docx"`
  - Use identical implementation pattern as K° Crédito
  - Ensure proper error handling for missing template
- Add comprehensive logging
- Add docstring

### Step 6: Test Custom Replacement Logic (If Needed)
- If templates have Paga Local specific placeholders identified in Step 1:
  - Create `_prepare_paga_local_no_aval_replacements()` helper method
  - Extend the standard replacements dictionary with custom mappings
  - Update both generation methods to call this helper instead of `_prepare_replacements()`
- Otherwise, confirm that `_prepare_replacements()` handles all placeholders correctly

### Step 7: Execute Database Migration
- Open Supabase SQL Editor at the project dashboard
- Execute the migration file created in Step 2
- Verify both template records are inserted:
  ```sql
  SELECT id, contract_type, version, template_content, active, created_at
  FROM contract_templates
  WHERE contract_type IN ('pl_co_credito_no_aval', 'pl_co_mandato_no_aval')
  ORDER BY contract_type;
  ```
- Confirm both records show `active = true` and correct filenames

### Step 8: Manual Test Document Generation
- Use the backend Python interpreter or create a test script
- Load a sample client from the database
- Call the contract service to generate a contract with `contract_type='pl_co_credito_no_aval'`
- Verify DOCX file is generated without errors
- Open DOCX in Microsoft Word or LibreOffice to verify:
  - All placeholders are replaced
  - No `[...]` brackets remain
  - Formatting is preserved
  - Document opens without corruption
- Repeat for `contract_type='pl_co_mandato_no_aval'`

### Step 9: Test PDF Conversion
- For each generated DOCX, test PDF conversion:
  - Call `document_service.convert_to_pdf(docx_bytes)`
  - Verify PDF is generated without errors
  - Open PDF to confirm formatting and content
- Ensure LibreOffice is installed and accessible by the backend
- Verify PDF conversion completes in reasonable time (< 5 seconds)

### Step 10: Create E2E Test Specification
- Create `.claude/commands/e2e/test_paga_local_sin_aval_contracts.md`
- Follow the format from `.claude/commands/e2e/test_contract_request.md`
- Define test steps:
  1. Login as operations user
  2. Navigate to `/operations/paga-local-colombia`
  3. Click "Contratos Cuenta Cliente" tab
  4. Click "Sin Aval" subtab
  5. Click "K° Crédito (No Aval)" contract card
  6. Search for client by NIT (use test client: 900123456)
  7. Select client and submit contract request
  8. Verify success message and contract in pending queue
  9. Repeat for "K° Mandato No Aval"
- Define success criteria: contract IDs generated, status is "under_review", no errors
- Specify 6 screenshots to capture the workflow

### Step 11: Run Backend Tests and Linting
- Execute validation commands to catch any regressions:
  ```bash
  cd backend && python -m pytest
  cd backend && ruff check src/
  ```
- Fix any test failures or linting errors
- Ensure zero regressions in existing functionality

### Step 12: Run Frontend Validation
- Execute frontend validation commands:
  ```bash
  cd frontend && npm run lint
  cd frontend && npx tsc --noEmit
  cd frontend && npm run build
  ```
- Confirm no TypeScript errors
- Confirm production build succeeds
- Fix any issues discovered

### Step 13: Execute E2E Test (Final Validation)
- Read `.claude/commands/test_e2e.md` to understand the E2E test runner
- Execute the E2E test created in Step 10:
  - Ensure backend and frontend servers are running
  - Run the test using Playwright browser automation
  - Verify all test steps pass
  - Confirm screenshots are captured
- If test fails, debug and fix issues, then re-run
- Document test results with pass/fail status

## Testing Strategy

### Unit Tests
**Backend Document Service Tests:**
- Test `generate_paga_local_credito_no_aval_document()` with mock contract data
- Test `generate_paga_local_mandato_no_aval_document()` with mock contract data
- Test template loading with missing template file (should raise `FileNotFoundError`)
- Test placeholder replacement completeness (no brackets remain)
- Test DOCX byte generation (valid file format)

**Backend Integration Tests:**
- Test full contract generation flow for both types via `ContractService`
- Test template fetching from database by contract_type
- Test data snapshot creation with all required fields
- Test PDF conversion pipeline

### Edge Cases
**Missing or Invalid Data:**
- Test with client missing optional fields (direccion_comercial, KAM info) - should not break, use empty strings or defaults
- Test with negative cupo_plataforma (incomplete records) - should format correctly or show placeholder
- Test with very long client names (>100 chars) - should not break template formatting

**Template Issues:**
- Test with corrupted template file - should raise clear error
- Test with template containing unrecognized placeholders - should leave unchanged
- Test with template in different Word format (.doc vs .docx) - should handle or fail gracefully

**Database Issues:**
- Test contract generation when no active template exists - should raise `ValueError`
- Test with multiple active templates for same contract_type - should use most recent

**PDF Conversion:**
- Test PDF conversion when LibreOffice is not installed - should raise clear error with installation instructions
- Test PDF conversion timeout (very large documents) - should complete or fail gracefully

## Acceptance Criteria
- [ ] Both template records exist in `contract_templates` table with `active=true`
- [ ] `DocumentService` routes `pl_co_credito_no_aval` and `pl_co_mandato_no_aval` to dedicated generation methods
- [ ] Both generation methods successfully load templates from `backend/templates/`
- [ ] All bracketed placeholders in templates are replaced with actual client data
- [ ] Generated DOCX files open in Microsoft Word/LibreOffice without errors
- [ ] DOCX to PDF conversion works for both contract types
- [ ] Operations users can request both contract types via UI
- [ ] Contracts are created with status "under_review"
- [ ] Legal users can download DOCX/PDF for review
- [ ] Legal users can approve contracts, generating final PDFs
- [ ] Approved PDFs appear in Operations "Contratos Aprobados" tab
- [ ] E2E test passes with 100% success rate
- [ ] Backend tests pass with zero regressions
- [ ] Frontend build succeeds with no errors
- [ ] All placeholders documented and mapped correctly

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

### Database Validation
```bash
# Execute in Supabase SQL Editor
SELECT id, contract_type, version, template_content, active, created_at
FROM contract_templates
WHERE contract_type IN ('pl_co_credito_no_aval', 'pl_co_mandato_no_aval')
ORDER BY contract_type;
```
**Expected:** 2 rows returned, both with `active = true` and correct template filenames

### Backend Validation
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting (should show no new errors)

### Frontend Validation
- `cd frontend && npm run lint` - Run frontend linting (should show no errors)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check (should show no errors)
- `cd frontend && npm run build` - Run frontend build to validate production compilation (should succeed)

### End-to-End Test Validation
- Read `.claude/commands/test_e2e.md` to understand the E2E test runner
- Read and execute `.claude/commands/e2e/test_paga_local_sin_aval_contracts.md` to validate this functionality works end-to-end
- **Expected:** Test status is "passed", all screenshots captured, no errors

### Manual Smoke Test (Optional but Recommended)
1. Start backend: `cd backend && python -m uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Login as operations user at http://localhost:5173
4. Navigate to Operations → Paga Local Colombia
5. Click "Contratos Cuenta Cliente" → "Sin Aval"
6. Request "K° Crédito (No Aval)" for a test client
7. Verify success message and contract ID generated (format: varies by type)
8. Login as legal user
9. Navigate to Legal → Pending Review
10. Download DOCX for the new contract
11. Open in Word - verify all placeholders replaced
12. Approve the contract
13. Login back as operations user
14. Navigate to Paga Local Colombia → "Contratos Aprobados"
15. Verify approved contract appears with download link
16. Download and verify PDF

## Notes

### Template Filename Mapping
The database `template_content` field MUST exactly match the physical template filenames:
- Database: `FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`
- Filesystem: `backend/templates/FK COL paga local - Fin. COP - K° Crédito (No Aval).docx`

Any mismatch will cause `FileNotFoundError` during generation.

### Contract ID Sequence
These contract types will need entries in `contract_id_sequence` table. The `generate_contract_id()` database function should be extended to handle these types. Check existing migrations for patterns:
- Activos → ACT-YYYY-XXX
- Otrosí → OTRO-YYYY-XXX
- Inventario Bodega → INV-YYYY-XXX
- Paga Local contracts may use: PLCO-YYYY-XXX or similar

If contract ID generation fails, update the `generate_contract_id()` function in a separate migration.

### Placeholder Standardization
The Paga Local templates should use the same standard placeholders as Activos contracts to maximize code reuse. If any custom placeholders are discovered, document them here and create a custom replacement method.

Standard placeholders expected:
- `[NOMBRE DEL CLIENTE]` - Company legal name
- `[NIT]` - Tax ID
- `[Nombre del representante legal]` - Legal representative name
- `[identificacion RL]` - Legal rep ID number
- `[nombre de la ciudad]` - City of domicile
- `[valor Cupo de Operaciones en numeros]` - Credit limit (formatted currency)
- `[valor Cupo de Operaciones en letras]` - Credit limit (Spanish words)
- `[sic]` - Contract ID
- `[dia]`, `[mes]`, `[•]` - Date components

### Future Considerations
This implementation completes 2 of 9 Paga Local Colombia contract types. The remaining 7 types will need similar implementations:
- **Aval Persona Jurídica**: `pl_co_credito_aval_pj`, `pl_co_mandato_pj`
- **Aval Persona Natural**: `pl_co_credito_aval_pn`, `pl_co_mandato_pn`
- **Documentos Operación**: `pl_co_mandato_im`, `pl_co_solicitud_desembolso`, `pl_co_dian_mandato_im`

Consider extracting common logic into a shared Paga Local generation method to reduce code duplication.

### LibreOffice Dependency
PDF conversion requires LibreOffice installed on the server:
- **Development**: Install locally (macOS: `brew install libreoffice`, Linux: `apt-get install libreoffice`)
- **Production (Render)**: Add to `render.yaml` buildpack or install in build script

If LibreOffice is missing, PDF conversion will fail with clear error. Document this in deployment guides.

### Testing with Real Data
Before deploying to production:
1. Test with at least 3 real client records from production database
2. Verify all placeholders populate correctly
3. Have Legal team review sample generated contracts for accuracy
4. Confirm formatting matches expectations
5. Test DocuSign integration if applicable

### Performance Considerations
Document generation typically takes:
- DOCX generation: 200-500ms
- PDF conversion: 2-4 seconds
- Total per contract: ~3-5 seconds

Monitor generation times in production. If performance degrades, consider:
- Caching template objects
- Async/queue-based processing for bulk generation
- Pre-warming LibreOffice processes
