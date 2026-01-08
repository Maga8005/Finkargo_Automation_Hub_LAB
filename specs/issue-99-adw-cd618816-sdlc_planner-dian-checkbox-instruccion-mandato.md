# Feature: DIAN Checkbox for Instruccion de Mandato with Auto-Wording

## Feature Description
This feature enhances the Instruccion de Mandato document generation to support mixed creditor types (DIAN and non-DIAN) within a single document. Currently, there are two separate forms - one for DIAN payments and one for generic creditors with bank certificates. When a payment has BOTH types, users must manually combine documents.

The enhancement adds a per-creditor "Es DIAN" checkbox that:
- Auto-populates predefined DIAN wording when checked
- Disables bank certificate upload for DIAN creditors
- Defaults account type to "PSE" for DIAN transfers
- Auto-detects DIAN creditors based on name patterns
- Generates a single unified document with all creditors

## User Story
As an Operations team member (operations role)
I want to mark individual creditors as DIAN payments in a single Instruccion de Mandato form
So that I can generate a unified document for mixed DIAN and non-DIAN creditors without manual document merging

## Problem Statement
Currently, the Paga Local Colombia workflow has two separate document types:
1. **Mandato (IM)** - Generic creditors requiring bank certificate uploads
2. **DIAN Mandato (IM)** - DIAN-specific payments with predefined wording

When a quotation contains both DIAN payments (tributos/impuestos) and regular creditors (freight agents, customs brokers), users must:
1. Generate separate documents for each type
2. Manually combine or process them separately
3. Risk inconsistencies between documents

Additionally, there's a bug where the account type shows "PC" instead of "PSE" for DIAN transfers.

## Solution Statement
Unify the two forms into a single enhanced form with:
1. Per-creditor "Es DIAN" checkbox in the creditors table
2. Conditional UI - DIAN creditors don't need bank certificates; non-DIAN do
3. Auto-wording injection for DIAN creditors
4. Auto-detection of DIAN creditors from parsed quotation data
5. Single document generation with appropriate wording per creditor type
6. Fix account type to properly show "PSE" for DIAN transfers

## Access Control
- Required Role(s): `operations`, `admin`, `mesa_control`
- Backend Protection: Uses existing `require_paga_local_role` dependency from `rbac_dependencies.py`
- Frontend Protection: Already protected via parent route `OperationsPagaLocalColombia`

## Relevant Files
Use these files to implement the feature:

**Frontend:**
- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx` - Parent page containing the tabs; no changes needed
- `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx` - Tab container for Documentos Operación; minor UI text updates may be needed
- `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` - **PRIMARY CHANGE**: Add DIAN checkbox, conditional bank cert upload, auto-wording
- `frontend/src/components/forms/FKDIANMandatoForm.tsx` - Can be deprecated/removed after merging functionality into FKInstruccionMandatoForm
- `frontend/src/types/legal.ts` - Add `es_dian` field to `AcreedorGastosNacionales` type
- `frontend/src/services/operationsService.ts` - May need to update request types

**Backend:**
- `backend/src/adapter/rest/operations_routes.py` - Update `generate_instruccion_mandato` to handle mixed creditors
- `backend/src/interface/legal_dtos.py` - Add `es_dian` field to `AcreedorGastosNacionales` model
- `backend/src/core/servicios/document_service.py` - Update `_populate_acreedores_table` to handle DIAN wording
- `backend/src/core/servicios/cotizacion_parser_service.py` - Add DIAN auto-detection in `_extract_anexo_table`
- `backend/src/core/servicios/bank_certificate_parser_service.py` - No changes needed

**Template:**
- `backend/templates/FK COL - Fin. COP - Mandato (IM).docx` - Verify creditor table can accommodate DIAN wording

**Testing:**
- `.claude/commands/test_e2e.md` - Reference for E2E test format
- `.claude/commands/e2e/test_login.md` - Reference for E2E test structure

### New Files
- `.claude/commands/e2e/test_dian_checkbox_instruccion_mandato.md` - E2E test for the unified DIAN checkbox feature

## Pre-Implementation Verification

### Feature Category
- [x] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
The Mandato (IM) template (`FK COL - Fin. COP - Mandato (IM).docx`) has these placeholders:

| Placeholder | Data Source | Format | Notes |
|-------------|-------------|--------|-------|
| [Fecha actual] | datetime.utcnow() | "DD de MONTH de YYYY" | Current date in Spanish |
| [Número de cotización de desembolso] | data.numero_cotizacion_desembolso | String | Quote number |
| [día de firma contrato mandato] | data.fecha_contrato_mandato | Integer (day) | Day component |
| [mes de firma contrato mandato] | data.fecha_contrato_mandato | String (month name) | Spanish month name |
| [año de firma contrato mandato] | data.fecha_contrato_mandato | Integer (year) | Full year |
| [monto a transferir en letras] | data.monto | Spanish words + "PESOS" | Amount in words |
| [monto a transferir en números] | data.monto | "$X,XXX,XXX" | Formatted currency |
| [Nombre del representante legal del Cliente] | data.representante_legal | String | Client rep name |
| [número ID representante legal] | data.cedula_representante | String | Client rep ID |

**Creditor Table (nested table):**
- Located at: Table 0 → Row 3 → Cell 0 → Nested Table
- Row 0: Header row
- Rows 1-3: Data rows for creditors with placeholders for: Razón Social, NIT, Banco, Tipo Cuenta, Número Cuenta

**DIAN Auto-Wording Constant:**
```python
DIAN_WORDING = "Transferencia electronica PSE a favor de la DIAN"
DIAN_KEYWORDS = ["DIAN", "Direccion de Impuestos", "Aduanas Nacionales", "Entidad de pago de Impuestos"]
```

### B. Excel Column Mapping (Excel Processing only)
N/A - Not an Excel processing feature.

### C. File Format Specification (Import/Export only)
N/A - Not a file import/export feature.

### D. Data Contract Verification (ALL features)
Document return types and access patterns for repository methods used:

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| client_repo.get_by_nit() | dict | data['field'] | client['nit'] |
| contract_repo.create() | dict | data['field'] | contract['id'] |

**Updated Request/Response DTOs:**

```python
# AcreedorGastosNacionales (updated)
class AcreedorGastosNacionales(BaseModel):
    razon_social: str
    nit: Optional[str] = None  # Optional for DIAN
    banco: str  # "DIAN" or actual bank name
    tipo_cuenta: str  # "PSE" for DIAN, or "Ahorros"/"Corriente"
    numero_cuenta: str  # "N/A" for DIAN, or actual account number
    es_dian: bool = False  # NEW: Flag to indicate DIAN payment
```

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - `ContractType.PL_CO_MANDATO_IM` exists
- [x] Template file exists in `backend/templates/` - `FK COL - Fin. COP - Mandato (IM).docx`
- [x] Database records exist - Template record in `contract_templates` table
- [x] Country-specific data handled - Colombia only (CO)

### F. External API Contract (Integration only)
N/A - No external API integration.

### G. Query Specification (Reporting only)
N/A - Not a reporting feature.

### Interface Mapping (Frontend ↔ Backend)
Map frontend TypeScript fields to backend Pydantic fields:

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| razon_social | razon_social | string | Creditor company name |
| nit | nit | string? | Optional for DIAN creditors |
| banco | banco | string | "DIAN" for DIAN payments |
| tipo_cuenta | tipo_cuenta | string | "PSE" for DIAN, "Ahorros"/"Corriente" for others |
| numero_cuenta | numero_cuenta | string | "N/A" for DIAN |
| es_dian | es_dian | boolean | NEW: true = DIAN payment |

## Implementation Plan
### Phase 1: Foundation
1. Update DTOs to add `es_dian` field
2. Update TypeScript types to match
3. Add DIAN constants to backend service

### Phase 2: Core Implementation
1. Modify `FKInstruccionMandatoForm` to add DIAN checkbox per creditor
2. Update cotizacion parser to auto-detect DIAN creditors
3. Update document service to handle DIAN wording in creditor table
4. Fix account type bug (PC → PSE)

### Phase 3: Integration
1. Update form validation for conditional bank cert requirement
2. Update UI to disable/hide bank cert upload for DIAN creditors
3. Create E2E test for the unified form

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Update Backend DTOs
- Open `backend/src/interface/legal_dtos.py`
- Add `es_dian: bool = False` field to `AcreedorGastosNacionales` model
- Update validator to ensure `tipo_cuenta` accepts "PSE" as valid option (already exists but verify)
- Ensure NIT validation allows empty/None for DIAN creditors

### Task 2: Add DIAN Constants to Document Service
- Open `backend/src/core/servicios/document_service.py`
- Add constants at top of file:
  ```python
  # DIAN Payment Constants
  DIAN_WORDING = "Transferencia electronica PSE a favor de la DIAN"
  DIAN_KEYWORDS = ["DIAN", "Direccion de Impuestos", "Aduanas Nacionales", "Entidad de pago de Impuestos"]
  ```

### Task 3: Update Creditor Table Population
- In `document_service.py`, modify `_populate_acreedores_table` method
- For creditors with `es_dian=True`:
  - Set razon_social cell to `DIAN_WORDING`
  - Set nit cell to "N/A" or empty
  - Set banco cell to "DIAN"
  - Set tipo_cuenta cell to "PSE"
  - Set numero_cuenta cell to "N/A"
- For non-DIAN creditors, use existing logic

### Task 4: Update Cotizacion Parser for DIAN Auto-Detection
- Open `backend/src/core/servicios/cotizacion_parser_service.py`
- After extracting each anexo item, check if `acreedor` contains any DIAN keywords
- Add helper method `_is_dian_creditor(acreedor_name: str) -> bool`
- Update `AnexoItem` return to include suggested `es_dian` flag
- NOTE: `AnexoItem` is in `legal_dtos.py` - may need to add `es_dian` field there too

### Task 5: Update AnexoItem DTO (if needed)
- Open `backend/src/interface/legal_dtos.py`
- Add optional `es_dian: bool = False` to `AnexoItem` model if parser needs to return this

### Task 6: Update Frontend TypeScript Types
- Open `frontend/src/types/legal.ts`
- Add `es_dian?: boolean` to `AcreedorGastosNacionales` interface
- Add `es_dian?: boolean` to `AnexoItem` interface (if auto-detection is used)

### Task 7: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for reference
- Create `.claude/commands/e2e/test_dian_checkbox_instruccion_mandato.md`
- Test steps should cover:
  1. Login with operations role
  2. Navigate to Paga Local Colombia > Documentos Operación > Mandato (IM)
  3. Search and select a client
  4. Upload a Cotización PDF (use test file if available)
  5. Verify DIAN checkbox appears for each creditor
  6. Check DIAN checkbox for first creditor
  7. Verify auto-wording appears in preview
  8. Verify bank certificate upload is disabled for DIAN creditor
  9. Add a non-DIAN creditor
  10. Upload bank certificate for non-DIAN creditor
  11. Submit and verify success

### Task 8: Update FKInstruccionMandatoForm Component
- Open `frontend/src/components/forms/FKInstruccionMandatoForm.tsx`
- Add state for `es_dian` per creditor (update `AcreedorGastosNacionales` array state)
- Add DIAN checkbox to each creditor row in the form
- When checkbox is checked:
  - Auto-fill: `razon_social = "Transferencia electronica PSE a favor de la DIAN"`
  - Auto-fill: `banco = "DIAN"`
  - Auto-fill: `tipo_cuenta = "PSE"`
  - Auto-fill: `numero_cuenta = "N/A"`
  - Disable bank certificate upload section for that creditor
  - Disable manual editing of razon_social, banco, tipo_cuenta, numero_cuenta
- When checkbox is unchecked:
  - Enable all fields
  - Enable bank certificate upload
  - Clear auto-filled values
- Add auto-detection: when `cotizacionData.anexo_items` is populated, check each `acreedor` for DIAN keywords and pre-check the checkbox

### Task 9: Add DIAN Detection Helper to Frontend
- In `FKInstruccionMandatoForm.tsx`, add helper function:
  ```typescript
  const DIAN_KEYWORDS = ['DIAN', 'Direccion de Impuestos', 'Aduanas Nacionales', 'Entidad de pago de Impuestos'];

  const isDianCreditor = (acreedorName: string): boolean => {
    const nameLower = acreedorName.toLowerCase();
    return DIAN_KEYWORDS.some(keyword => nameLower.includes(keyword.toLowerCase()));
  };
  ```
- Use this in `handleExtractCotizacion` to auto-check DIAN checkbox

### Task 10: Update Form Validation
- In `FKInstruccionMandatoForm.tsx`, modify `validateAcreedores` function
- For DIAN creditors (`es_dian = true`):
  - Skip bank certificate validation
  - Skip banco, tipo_cuenta, numero_cuenta manual validation (auto-filled)
- For non-DIAN creditors:
  - Require bank certificate upload
  - Require all bank account fields

### Task 11: Update Creditor Row UI
- In `FKInstruccionMandatoForm.tsx`, modify the creditor card rendering
- Add Checkbox component with label "Es DIAN"
- Position checkbox at top of creditor card
- Add conditional rendering:
  - If `es_dian`: Show read-only DIAN info card, hide bank cert upload
  - If not `es_dian`: Show editable fields and bank cert upload

### Task 12: Fix Account Type Bug
- In `document_service.py`, verify `tipo_cuenta` mapping in `_populate_acreedores_table`
- For DIAN creditors, explicitly set to "PSE" (not "PC")
- Check if there's any normalization in the validator that might change "PSE"

### Task 13: Update Operations Service (if needed)
- Open `frontend/src/services/operationsService.ts`
- Ensure `InstruccionMandatoRequest` type matches updated DTO
- No endpoint changes needed - same endpoint handles both

### Task 14: Consider Deprecating FKDIANMandatoForm
- The DIAN-only form (`FKDIANMandatoForm.tsx`) may be redundant after this feature
- Options:
  1. Keep it for simple DIAN-only cases (less UI complexity)
  2. Remove it and always use the unified form
- Decision: Keep for now, but update tab description to note unified form can handle DIAN too

### Task 15: Update Tab Description (Optional UX Enhancement)
- In `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`
- Update `DOCUMENT_CONFIGS` for Mandato (IM) to mention it now supports mixed DIAN/non-DIAN

### Task 16: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Run E2E test to verify feature works end-to-end

## Testing Strategy
### Unit Tests
- Add pytest tests for `_is_dian_creditor` helper in cotizacion parser
- Add pytest tests for DIAN creditor handling in `_populate_acreedores_table`
- Test that `AcreedorGastosNacionales` validator accepts `es_dian` field

### Edge Cases
- Single DIAN creditor only (should work like old DIAN form)
- Single non-DIAN creditor only (should work like old generic form)
- Mixed: 1 DIAN + 1 non-DIAN creditor
- Mixed: 2 DIAN + 1 non-DIAN creditor
- Maximum creditors: 3 creditors with mixed types
- Auto-detection edge cases:
  - "DIAN" in name → detected
  - "Entidad de pago de Impuestos" → detected
  - Random freight company → NOT detected
  - False positive prevention: "GUARDIAN" should NOT be detected as DIAN

## Acceptance Criteria
1. [ ] Each creditor row has "Es DIAN" checkbox visible
2. [ ] Checking DIAN auto-fills predefined wording ("Transferencia electronica PSE a favor de la DIAN")
3. [ ] Checking DIAN disables bank certificate upload for that row
4. [ ] Checking DIAN auto-fills: banco="DIAN", tipo_cuenta="PSE", numero_cuenta="N/A"
5. [ ] Unchecked rows require bank certificate upload
6. [ ] Multiple mixed creditors (DIAN + non-DIAN) can be added to single document
7. [ ] Account type correctly shows "PSE" for DIAN (not "PC")
8. [ ] DIAN auto-detection works based on creditor name patterns
9. [ ] Generated document contains correct wording for each creditor type
10. [ ] User can manually override auto-detection (uncheck DIAN checkbox)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/ -v` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_dian_checkbox_instruccion_mandato.md` to validate this functionality works

## Notes
### DIAN Wording Constant
The exact wording to use for DIAN payments:
```
"Transferencia electronica PSE a favor de la DIAN"
```

### DIAN Keywords for Auto-Detection
```python
DIAN_KEYWORDS = ["DIAN", "Direccion de Impuestos", "Aduanas Nacionales", "Entidad de pago de Impuestos"]
```

### Account Type Values
- For DIAN transfers: `"PSE"`
- For bank transfers: `"Ahorros"` or `"Corriente"`

### Migration from Separate Forms
After this feature is complete, the workflow becomes:
1. User uploads Cotización PDF
2. System extracts creditors and auto-detects DIAN ones
3. User reviews and adjusts DIAN checkboxes if needed
4. For non-DIAN creditors, user uploads bank certificates
5. Single document is generated with appropriate content for each creditor type

### Future Considerations
- Consider adding visual indicator (icon/badge) for DIAN-detected creditors
- Consider adding bulk "Mark all as DIAN" / "Mark none as DIAN" actions
- Consider migrating users away from `FKDIANMandatoForm` completely after sufficient validation

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no DB changes)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Document Generation:**
- [x] ALL template placeholders extracted and documented
- [x] Placeholder mapping table complete with data sources
- [x] Database records verified (template, enum, prefix)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) - CO only

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
