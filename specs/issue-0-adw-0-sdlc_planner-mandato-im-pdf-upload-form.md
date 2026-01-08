# Feature: Mandato (IM) PDF Upload Form - Paga Local Colombia

## Feature Description

Add Cotización and Certificado Bancario (Bank Certificate) PDF upload functionality to the Mandato (IM) document generation form in the Paga Local Colombia workflow. Currently, the Mandato (IM) tab uses a generic contract request form (`FKPagaLocalCOContractRequest`) that only allows client selection without PDF upload or data extraction. This feature creates a specialized form (`FKInstruccionMandatoForm`) similar to the existing `FKSolicitudDesembolsoRequest` component that enables:

1. Client search and selection
2. Cotización PDF upload with automatic data extraction
3. Certificado Bancario (Bank Certificate) PDF upload for creditor bank account information
4. Review and edit extracted data before document generation
5. Support for multiple creditors (up to 3 per document)

The backend services and API endpoints for parsing PDFs and generating the Instrucción de Mandato document already exist. This feature focuses solely on the **frontend implementation** to connect to those existing backend endpoints.

## User Story

As an **operations team member or legal specialist** handling Paga Local Colombia workflows
I want to upload Cotización and Certificado Bancario PDFs when generating Mandato (IM) documents
So that I can automatically extract creditor bank account information and generate accurate mandate instruction documents without manual data entry

## Problem Statement

The Mandato (IM) tab in Paga Local Colombia currently uses a generic form (`FKPagaLocalCOContractRequest`) that:
1. Only allows client selection (no PDF upload)
2. Does not extract data from Cotización PDFs
3. Does not support uploading Certificado Bancario for creditor bank information
4. Requires manual entry of all creditor data

This is inconsistent with the Solicitud de Desembolso tab which has a specialized form with PDF upload and data extraction capabilities. Users expect the same functionality for Mandato (IM) documents.

## Solution Statement

Create a new specialized frontend component `FKInstruccionMandatoForm.tsx` that:

1. **Reuses the existing pattern** from `FKSolicitudDesembolsoRequest.tsx` for client search, PDF upload, and data extraction
2. **Connects to existing backend endpoints** in `operationsService.ts`:
   - `parseCotizacionForMandato()` - extracts data from Cotización PDF
   - `parseBankCertificate()` - extracts creditor info from Bank Certificate PDF
   - `generateInstruccionMandato()` - generates the document
3. **Adds creditor management UI** for adding/editing up to 3 creditors with their bank account details
4. **Integrates into the existing tab structure** by replacing the generic form in `FKPagaLocalCODocumentosOperacion.tsx`

The backend implementation is already complete - this is purely a frontend feature to enable the existing backend functionality.

## Access Control

- **Required Role(s):** `admin`, `legal`, `operations`
- **Backend Protection:** Already implemented with `require_roles(['admin', 'legal', 'operations'])` on existing endpoints
- **Frontend Protection:** Already configured in `FKPagaLocalCODocumentosOperacion.tsx` - no additional protection needed

## Relevant Files

### Existing Backend Files (No Changes Needed)

- **`backend/src/adapter/rest/operations_routes.py`** - Contains the endpoints:
  - `POST /contracts/instruccion-mandato/parse-cotizacion`
  - `POST /contracts/instruccion-mandato/parse-bank-certificate`
  - `POST /contracts/instruccion-mandato/generate`
- **`backend/src/core/servicios/cotizacion_parser_service.py`** - Parses Cotización PDFs
- **`backend/src/core/servicios/bank_certificate_parser_service.py`** - Parses Bank Certificate PDFs
- **`backend/src/core/servicios/document_service.py`** - Generates Instrucción de Mandato documents

### Existing Frontend Files (Reference/Modify)

- **`frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`** (563 lines)
  - Reference pattern for PDF upload, data extraction, client search, and dynamic table
  - Blueprint for the new `FKInstruccionMandatoForm.tsx` component

- **`frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`** (145 lines)
  - Parent component with tabs for Mandato (IM), Solicitud Desembolso, DIAN Mandato
  - Currently uses generic `FKPagaLocalCOContractRequest` for Mandato (IM) tab
  - **Will modify**: Replace generic form with new `FKInstruccionMandatoForm` for `pl_co_mandato_im` type

- **`frontend/src/services/operationsService.ts`** (291 lines)
  - **Already has** the service methods:
    - `parseCotizacionForMandato(file: File)` (line 244)
    - `parseBankCertificate(file: File)` (line 263)
    - `generateInstruccionMandato(request)` (line 282)
  - No changes needed

- **`frontend/src/types/legal.ts`** (229 lines)
  - **Already has** the types:
    - `BankCertificateData` (line 195)
    - `AcreedorGastosNacionales` (line 205)
    - `InstruccionMandatoRequest` (line 213)
    - `InstruccionMandatoFormData` (line 221)
  - No changes needed

### New Files

- **`frontend/src/components/forms/FKInstruccionMandatoForm.tsx`**
  - New specialized form component for Mandato (IM) document generation
  - Includes: client search, Cotización upload, Bank Certificate upload, creditor management, document generation

- **`.claude/commands/e2e/test_instruccion_mandato_form.md`**
  - E2E test file to validate the complete Mandato (IM) form workflow
  - Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand test format

## Implementation Plan

### Phase 1: Foundation

**Goal:** Understand the existing patterns and ensure types are ready

1. **Verify existing types** in `frontend/src/types/legal.ts`:
   - Confirm `BankCertificateData`, `AcreedorGastosNacionales`, `InstruccionMandatoRequest`, `InstruccionMandatoFormData` exist
   - Confirm `CotizacionData` type is exported (used for Cotización parsing)

2. **Verify existing services** in `frontend/src/services/operationsService.ts`:
   - Confirm `parseCotizacionForMandato()`, `parseBankCertificate()`, `generateInstruccionMandato()` exist

### Phase 2: Core Implementation

**Goal:** Create the specialized form component

1. **Create `FKInstruccionMandatoForm.tsx`**:
   - Follow the pattern from `FKSolicitudDesembolsoRequest.tsx`
   - Section 1: Client Search (identical to Solicitud Desembolso)
   - Section 2: Cotización PDF Upload (use `parseCotizacionForMandato()`)
   - Section 3: Extracted Data Display (numero_cotizacion, fecha_contrato, monto)
   - Section 4: Creditor Management:
     - For each creditor from anexo_items:
       - Upload Bank Certificate PDF
       - Parse and display extracted bank account data
       - Allow manual editing of extracted data
     - Add/remove creditors (max 3)
   - Section 5: Review & Generate (call `generateInstruccionMandato()`)

### Phase 3: Integration

**Goal:** Wire up the component and test

1. **Update `FKPagaLocalCODocumentosOperacion.tsx`**:
   - Import `FKInstruccionMandatoForm`
   - Replace generic form for `pl_co_mandato_im` with `<FKInstruccionMandatoForm />`

2. **Create E2E test file** to validate the workflow

3. **Run validation commands** to ensure zero regressions

## Step by Step Tasks

### Task 1: Verify Existing Backend APIs Work

- Start development servers: `./scripts/start-dev.sh`
- Use browser dev tools or curl to test endpoints:
  - `POST /api/operations/contracts/instruccion-mandato/parse-cotizacion`
  - `POST /api/operations/contracts/instruccion-mandato/parse-bank-certificate`
  - `POST /api/operations/contracts/instruccion-mandato/generate`
- Verify endpoints return expected data structures
- Document any issues found

### Task 2: Verify Frontend Types and Services

- Read `frontend/src/types/legal.ts` to confirm types exist:
  - `BankCertificateData`
  - `AcreedorGastosNacionales`
  - `InstruccionMandatoRequest`
  - `InstruccionMandatoFormData`
  - `CotizacionData`
- Read `frontend/src/services/operationsService.ts` to confirm service methods exist:
  - `parseCotizacionForMandato()`
  - `parseBankCertificate()`
  - `generateInstruccionMandato()`
- Run TypeScript check: `cd frontend && npx tsc --noEmit`

### Task 3: Create FKInstruccionMandatoForm Component

- Create `frontend/src/components/forms/FKInstruccionMandatoForm.tsx`
- Use `FKSolicitudDesembolsoRequest.tsx` as the reference pattern
- Implement component structure with state management:

```typescript
// State variables needed:
- selectedClient: Client | null
- searchQuery: string, searching: boolean
- cotizacionFile: File | null
- cotizacionData: CotizacionData | null
- extracting: boolean
- acreedores: AcreedorGastosNacionales[]
- bankCertFiles: Map<number, File> (index -> file)
- requesting: boolean
- requestedContract: ContractGeneration | null
- error: string | null
```

- **Section 1: Client Search**:
  - TextField for NIT/name search
  - Search button with loading state
  - Search results list
  - Selected client display

- **Section 2: Cotización Upload**:
  - File input (PDF only, max 5MB)
  - "Extraer Datos" button
  - Display extracted data after parsing:
    - numero_cotizacion
    - fecha_contrato_credito
    - monto_total
    - anexo_items (list of creditors)

- **Section 3: Extracted Cotización Data (Editable)**:
  - TextField: Número de Cotización de Desembolso (editable)
  - TextField: Fecha del Contrato de Mandato (date input, editable)
  - TextField: Monto Total (read-only, from anexo_items sum)

- **Section 4: Creditor Bank Account Information**:
  - For each creditor from cotizacionData.anexo_items (or manual entry):
    - Card showing: Acreedor name, monto
    - File input for Bank Certificate PDF
    - "Extraer Datos del Certificado" button
    - Display/edit extracted bank info:
      - razon_social
      - nit
      - banco
      - tipo_cuenta (Ahorros/Corriente/PCE)
      - numero_cuenta
  - Button: "Agregar Acreedor Manual" (if < 3 creditors)
  - Button to remove creditor

- **Section 5: Generate Document**:
  - Summary of all data
  - "Generar Instrucción de Mandato" button
  - Success message after generation

- Implement handlers:
  - `handleClientSearch()`
  - `handleCotizacionUpload()`
  - `handleExtractCotizacion()`
  - `handleBankCertUpload(index: number)`
  - `handleExtractBankCert(index: number)`
  - `handleAcreedorChange(index: number, field: keyof AcreedorGastosNacionales, value: string)`
  - `handleAddAcreedor()`
  - `handleRemoveAcreedor(index: number)`
  - `handleGenerate()`
  - `handleReset()`

- Run linting: `cd frontend && npm run lint`
- Run TypeScript check: `cd frontend && npx tsc --noEmit`

### Task 4: Integrate Form into Paga Local CO Operations Tab

- Open `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`
- Import the new component:
  ```typescript
  import FKInstruccionMandatoForm from './FKInstruccionMandatoForm';
  ```
- Modify the tab rendering logic (around line 103-138):
  - Add condition for `pl_co_mandato_im` to use `FKInstruccionMandatoForm`
  - Keep generic form for `pl_co_dian_mandato_im` (future implementation)

  ```typescript
  {config.type === 'pl_co_solicitud_desembolso' ? (
    <FKSolicitudDesembolsoRequest />
  ) : config.type === 'pl_co_mandato_im' ? (
    <FKInstruccionMandatoForm />
  ) : (
    <FKPagaLocalCOContractRequest
      contractType={config.type}
      contractLabel={config.label}
    />
  )}
  ```

- Run linting: `cd frontend && npm run lint`
- Run TypeScript check: `cd frontend && npx tsc --noEmit`

### Task 5: Create E2E Test File

- Create `.claude/commands/e2e/test_instruccion_mandato_form.md`
- Follow the structure from `test_login.md` and existing E2E tests
- **User Story**: Operations/Legal user uploading Cotización and Bank Certificate PDFs to generate Mandato (IM)
- **Prerequisites**:
  - Backend and frontend servers running
  - User logged in with operations/legal role
  - Test client exists (NIT: 900436389)
  - Test PDFs available:
    - `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
    - `Example FIles for Reqs/certificado bancario.pdf`
- **Test Steps**:
  1. Login as operations user
  2. Navigate to `/operations/contratos-paga-local-colombia`
  3. Click "Documentos de Operación" tab
  4. Click "Mandato (IM)" subtab
  5. Screenshot: Empty Mandato (IM) form
  6. Search for client by NIT: 900436389
  7. Select client from results
  8. Upload Cotización PDF
  9. Click "Extraer Datos del PDF"
  10. Screenshot: Form with extracted Cotización data
  11. Verify extracted data displayed (numero_cotizacion, fecha, monto, creditors)
  12. For first creditor: Upload Bank Certificate PDF
  13. Click "Extraer Datos del Certificado"
  14. Screenshot: Form with extracted bank certificate data
  15. Verify creditor bank info displayed
  16. Review all data in summary section
  17. Click "Generar Instrucción de Mandato"
  18. Screenshot: Success message with contract ID
  19. Verify contract ID format: starts with ACT-YYYY-
- **Success Criteria**:
  - Form loads and displays all sections
  - PDF upload accepts only PDF files
  - Cotización extraction populates form fields
  - Bank Certificate extraction populates creditor info
  - Document generation succeeds
  - Contract appears in review queue

### Task 6: Run Validation Commands

Execute every command to validate the feature works correctly with zero regressions:

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

### Task 7: Execute E2E Test

- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_instruccion_mandato_form.md`
- Verify all test steps pass
- Capture screenshots at specified points
- Document any failures and fix issues

## Testing Strategy

### Unit Tests

**Backend:**
- No new backend tests needed - backend is already implemented and tested

**Frontend:**
- No unit test framework configured yet (noted in project)
- Manual testing via E2E test covers the workflow

### Integration Tests

- E2E test validates complete flow from login to document generation
- Test PDF upload and parsing functionality
- Test form state management and validation
- Test API integration with backend endpoints

### Edge Cases

1. **Invalid PDFs:**
   - Non-PDF file selected → Should show error "Solo se permiten archivos PDF"
   - PDF > 5MB → Should show error "El archivo no debe superar 5MB"
   - PDF without expected content → Backend returns 422, show user-friendly error

2. **Missing Data:**
   - Cotización without numero_cotizacion → Should handle gracefully
   - Bank Certificate parsing failure → Allow manual entry fallback
   - Client not found → Show search error

3. **Creditor Management:**
   - 0 creditors → Should show validation error
   - More than 3 creditors → UI should prevent adding more
   - Missing bank info for creditor → Should validate before generation

4. **Form Validation:**
   - No client selected → Disable generate button
   - No Cotización uploaded → Disable generate button
   - Missing required creditor fields → Show validation errors

## Acceptance Criteria

- [ ] Mandato (IM) tab displays specialized form (not generic form)
- [ ] Client search works (search by NIT or name)
- [ ] Cotización PDF upload works (validation: PDF only, max 5MB)
- [ ] "Extraer Datos" button parses Cotización and populates form
- [ ] Extracted data is displayed and editable (numero_cotizacion, fecha)
- [ ] Creditor list displays from extracted anexo_items
- [ ] Bank Certificate PDF upload works for each creditor
- [ ] Bank Certificate extraction populates creditor bank info
- [ ] Creditor bank info is editable (razon_social, nit, banco, tipo_cuenta, numero_cuenta)
- [ ] Manual creditor add/remove works (max 3)
- [ ] Generate button calls `generateInstruccionMandato()` API
- [ ] Success message shows contract ID after generation
- [ ] Form can be reset for new document
- [ ] All frontend linting passes
- [ ] TypeScript type check passes
- [ ] Frontend build succeeds
- [ ] E2E test passes with screenshots

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_instruccion_mandato_form.md` to validate the complete workflow

## Notes

### Key Implementation Notes

1. **Backend is already complete** - This is purely a frontend feature. The backend endpoints, services, and document generation are fully implemented and tested.

2. **Follow existing patterns** - The `FKSolicitudDesembolsoRequest.tsx` component is the template to follow. It has all the patterns needed:
   - Client search with debounced input
   - PDF file upload with validation
   - Data extraction with loading states
   - Editable form fields
   - Dynamic table management
   - Form validation
   - API submission

3. **Types are already defined** - All TypeScript types needed are already in `frontend/src/types/legal.ts`:
   - `BankCertificateData`
   - `AcreedorGastosNacionales`
   - `InstruccionMandatoRequest`
   - `InstruccionMandatoFormData`
   - `CotizacionData`

4. **Services are already implemented** - All API methods exist in `frontend/src/services/operationsService.ts`:
   - `parseCotizacionForMandato()`
   - `parseBankCertificate()`
   - `generateInstruccionMandato()`

### Differences from Solicitud de Desembolso

| Feature | Solicitud Desembolso | Mandato (IM) |
|---------|---------------------|--------------|
| Cotización Upload | Yes | Yes |
| Bank Certificate Upload | No | Yes (per creditor) |
| Creditor Table | View-only anexo items | Editable with bank info |
| Generated Document | Solicitud de Desembolso | Instrucción de Mandato |

### Future Enhancement (Out of Scope)

The `pl_co_dian_mandato_im` (DIAN Mandato) contract type will need its own specialized form in the future, with DIAN static values pre-populated. This is out of scope for this feature.

### Component Naming

Follow the FK prefix convention:
- Component: `FKInstruccionMandatoForm`
- File: `FKInstruccionMandatoForm.tsx`
