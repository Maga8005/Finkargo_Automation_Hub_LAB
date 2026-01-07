# Feature: Solicitud de Desembolso Document Generation with Cotización PDF Upload

## Feature Description
This feature implements complete Solicitud de Desembolso (Disbursement Request) document generation for Paga Local Colombia operations. The feature enables Operations users to:
1. Upload Cotización (quote) PDF documents from HubSpot
2. Automatically extract key financial and legal data from the uploaded PDF
3. Review and edit extracted data in an interactive form with dynamic Anexo I table
4. Generate the official Solicitud de Desembolso Word document with all placeholders populated
5. Submit to Legal department's review queue for approval

This feature is critical for Paga Local Colombia's financing workflow, allowing quick and accurate generation of disbursement request documents while reducing manual data entry errors and processing time.

## User Story
As an Operations team member handling Paga Local Colombia financing
I want to upload a Cotización PDF, extract its data automatically, and generate a Solicitud de Desembolso document
So that I can quickly submit accurate disbursement requests to Legal for approval without manual data entry errors

## Problem Statement
Currently, the Solicitud de Desembolso contract type (`pl_co_solicitud_desembolso`) exists in the system with its template and UI tab, but uses a generic form that requires manual data entry. Operations team members must:
- Manually transcribe data from Cotización PDFs received from HubSpot
- Enter complex Anexo I table data (creditors, instrument numbers, amounts) line by line
- Calculate totals manually
- Risk data entry errors that delay Legal approval
- Spend excessive time on repetitive data entry tasks

This creates bottlenecks in the financing workflow and increases the likelihood of errors in critical financial documents.

## Solution Statement
Implement a specialized form component (`FKSolicitudDesembolsoRequest`) that:
- Provides a file upload zone for Cotización PDF documents
- Extracts structured data using a new `CotizacionParserService` (PyMuPDF-based, similar to existing `RutParserService`)
- Pre-populates form fields with extracted data (editable for corrections)
- Provides a dynamic Anexo I table with add/remove row functionality and automatic total calculation
- Combines extracted data with client database information
- Generates the Word document using a specialized handler in `DocumentService`
- Integrates seamlessly with the existing Legal review queue workflow

This solution follows existing patterns (Inventario Bodega PDF upload) and maintains Clean Architecture principles while adding new capabilities for dynamic table generation and user-editable extracted data.

## Access Control
- Required Role(s): `operations`, `admin`
- Backend Protection: Use `require_operations_role` from `rbac_dependencies.py` for all new endpoints
- Frontend Protection: No additional protection needed - Operations dashboard already protected with `RoleProtectedRoute allowedRoles={['admin', 'operations']}`

## Relevant Files
Use these files to implement the feature:

**Backend - Services Layer (Business Logic):**
- `backend/src/core/servicios/rut_parser_service.py` - Reference pattern for PDF parsing with PyMuPDF (multi-strategy extraction, normalization, validation). Use as blueprint for `cotizacion_parser_service.py`
- `backend/src/core/servicios/contract_service.py` - Contract generation orchestration. Review how Inventario Bodega integrates custodian data (lines 105-116) to understand data snapshot merging pattern
- `backend/src/core/servicios/document_service.py` - Document generation routing and template population. Need to add `generate_solicitud_desembolso_document()` handler with Anexo I table population logic

**Backend - API Layer (REST Controllers):**
- `backend/src/adapter/rest/operations_routes.py` - Operations endpoints. Review Inventario Bodega endpoint (lines 62-161) for PDF upload pattern with `UploadFile`, file validation, and parser service integration. Add two new endpoints: parse-cotizacion and generate-solicitud-desembolso

**Backend - DTOs (Data Transfer Objects):**
- `backend/src/interface/legal_dtos.py` - Contains `CustodianData` (lines 121-137) and contract DTOs. Add `AnexoItem`, `SolicitudDesembolsoRequest`, and `CotizacionData` models following existing patterns

**Backend - RBAC (Role-Based Access Control):**
- `backend/src/adapter/rest/rbac_dependencies.py` - Contains `require_operations_role` dependency to protect new endpoints

**Frontend - Form Components:**
- `frontend/src/components/forms/FKInventarioRequest.tsx` - Reference pattern for PDF upload, file validation, extraction flow, and service integration. Blueprint for new `FKSolicitudDesembolsoRequest.tsx`
- `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx` - Parent component with tabs. Currently uses generic form for Solicitud Desembolso (tab 2). Replace with specialized component

**Frontend - Services (API Layer):**
- `frontend/src/services/operationsService.ts` - API service methods. Review `requestInventarioBodegaGeneration` (lines 133-153) for FormData upload pattern. Add `parseCotizacionPdf` and `generateSolicitudDesembolso` methods

**Frontend - Types:**
- `frontend/src/types/legal.ts` - TypeScript type definitions. Add `AnexoItem`, `CotizacionData`, and `SolicitudDesembolsoRequest` interfaces

**Frontend - API Clients:**
- `frontend/src/api/clients/apiClient.ts` - Axios client with auth interceptors. Already configured for multipart form uploads

**Backend - Template:**
- `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx` - Word template with placeholders. Contains Anexo I table structure requiring dynamic row population

**Documentation:**
- `docs/20251207_FEATURE_PROMPT_SOLICITUD_DESEMBOLSO_IMPLEMENTATION.md` - Detailed feature specification with PDF analysis, data flow diagram, placeholder mapping, and acceptance criteria
- `CLAUDE.md` - Project architecture guidance, Clean Architecture principles, component naming conventions (FK prefix), and deployment configuration

**Testing Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner pattern using Playwright MCP server
- `.claude/commands/e2e/test_login.md` - Example E2E test structure with user story, test steps, success criteria
- `.claude/commands/e2e/test_contract_request.md` - Contract request E2E test pattern relevant for this feature

### New Files
- `backend/src/core/servicios/cotizacion_parser_service.py` - PDF parsing service for Cotización documents. Extract numero_cotizacion, fechas, representante legal info, and Anexo I table items using PyMuPDF
- `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx` - Specialized form component with PDF upload, data extraction, editable fields, dynamic Anexo table, and validation
- `.claude/commands/e2e/test_solicitud_desembolso_request.md` - E2E test validating complete workflow from PDF upload to document submission

## Implementation Plan

### Phase 1: Foundation (Backend DTOs and Service Infrastructure)
**Goal**: Establish data models and service layer foundation for PDF parsing and document generation

1. **Create Backend DTOs** (`legal_dtos.py`):
   - Define `AnexoItem` model: acreedor (str), numero_instrumento (str), monto (Decimal)
   - Define `CotizacionData` model: extracted PDF fields with Optional typing for nullable fields
   - Define `SolicitudDesembolsoRequest` model: request payload with validation rules
   - Add Pydantic validators for: monto > 0, dias_plazo range (30-180), anexo_items non-empty list

2. **Create Cotización Parser Service** (`cotizacion_parser_service.py`):
   - Implement `CotizacionParserService` class following `RutParserService` pattern
   - Create multi-strategy extraction methods for each field:
     - `_extract_numero_cotizacion()` - Pattern: "CO:{NIT}:{sequence}:{type}:DOM"
     - `_extract_fecha_cotizacion()` - Spanish date parsing (e.g., "10 de noviembre de 2025")
     - `_extract_fecha_contrato_credito()` - Same date parsing logic
     - `_extract_representante_legal()` - Full name from structured sections
     - `_extract_anexo_table()` - Table extraction with headers, rows, and total calculation
   - Add text normalization utilities (whitespace cleanup, accent handling)
   - Implement comprehensive error handling with descriptive exceptions
   - Add logging for debugging extraction issues

3. **Write Unit Tests for Parser Service**:
   - Create `backend/tests/test_cotizacion_parser_service.py`
   - Test successful extraction with valid PDF
   - Test handling of missing/malformed data
   - Test date parsing edge cases (different Spanish formats)
   - Test Anexo table extraction with various row counts
   - Test calculation accuracy for monto_total

### Phase 2: Core Implementation (Backend API and Frontend Components)

4. **Add Operations API Endpoints** (`operations_routes.py`):
   - Implement `POST /api/operations/contracts/solicitud-desembolso/parse-cotizacion`:
     - Accept `UploadFile` with PDF validation (content_type, max size 5MB)
     - Call `CotizacionParserService.parse_cotizacion()`
     - Return `CotizacionData` DTO
     - Handle parsing errors with HTTP 422 status
   - Implement `POST /api/operations/contracts/solicitud-desembolso/generate`:
     - Accept `SolicitudDesembolsoRequest` DTO
     - Validate client exists using `client_repository`
     - Create contract record with status `under_review`
     - Generate contract ID with PLSD prefix
     - Store data snapshot with client + solicitud data
     - Return `ContractGenerationResponse`
   - Protect both endpoints with `require_operations_role` dependency
   - Add comprehensive error handling and logging

5. **Add Document Service Handler** (`document_service.py`):
   - Add routing case in `generate_contract_document()`:
     ```python
     elif contract_type == 'pl_co_solicitud_desembolso':
         return self.generate_solicitud_desembolso_document(contract_data)
     ```
   - Implement `generate_solicitud_desembolso_document()` method:
     - Load template: "FK COL - Fin. COP - Solicitud de Desembolso.docx"
     - Call `_prepare_solicitud_desembolso_replacements()`
     - Populate Anexo I table dynamically using python-docx table API
     - Replace all text placeholders
     - Return document bytes
   - Implement `_prepare_solicitud_desembolso_replacements()` helper:
     - Map data fields to template placeholders
     - Generate consecutivo: `CO:{NIT}:1:D:M:DOM`
     - Format dates in Spanish (e.g., "6 de noviembre de 2025")
     - Format currency amounts with Colombian peso format
   - Implement `_populate_anexo_table()` helper:
     - Find Anexo I table in document
     - Clone table row template
     - Iterate anexo_items and populate rows
     - Add total row at bottom
     - Format currency values consistently

6. **Create Frontend TypeScript Types** (`legal.ts`):
   - Define `AnexoItem` interface matching backend DTO
   - Define `CotizacionData` interface with camelCase naming
   - Define `SolicitudDesembolsoRequest` interface for API payload
   - Add JSDoc comments explaining each field's purpose

7. **Add Frontend Service Methods** (`operationsService.ts`):
   - Implement `parseCotizacionPdf(file: File): Promise<CotizacionData>`:
     - Create FormData, append file
     - POST to `/operations/contracts/solicitud-desembolso/parse-cotizacion`
     - Set headers: 'Content-Type': 'multipart/form-data'
     - Handle errors with user-friendly messages
   - Implement `generateSolicitudDesembolso(request: SolicitudDesembolsoRequest): Promise<ContractGeneration>`:
     - POST to `/operations/contracts/solicitud-desembolso/generate`
     - Return contract generation response
     - Handle validation errors

8. **Create Specialized Form Component** (`FKSolicitudDesembolsoRequest.tsx`):
   - **Structure**: Use Material-UI Card layout with 5 sections
   - **Section 1 - Client Search**:
     - Reuse existing client search pattern from `FKInventarioRequest`
     - TextField for NIT search
     - Display selected client info (nombre, NIT, ciudad)
   - **Section 2 - Cotización Upload**:
     - File input with accept="application/pdf"
     - Validate file type and size (max 5MB)
     - "Extraer Datos" button to trigger parsing
     - Loading state during extraction
     - Error display if parsing fails
   - **Section 3 - Extracted Data (Editable)**:
     - TextField: Número de Cotización de Desembolso (required)
     - DatePicker: Fecha del Contrato de Crédito (required)
     - TextField: Días de Plazo (number, default 120, range 30-180)
     - Read-only: Monto Total (auto-calculated from Anexo items)
   - **Section 4 - Anexo I Table (Dynamic)**:
     - DataGrid or Table component with columns: Acreedor, No. Instrumento, Monto
     - Add row button (IconButton with AddIcon)
     - Remove row button per row (IconButton with DeleteIcon)
     - Input fields in each cell (TextField)
     - Auto-calculate and display total at bottom
     - Pre-populate from extracted data
   - **Section 5 - Preview & Submit**:
     - Summary of all data (read-only preview)
     - Submit button: "Solicitar Documento"
     - Success/error feedback (Snackbar)
   - **State Management**:
     - Use react-hook-form for form state
     - useState for: cotizacionFile, extractedData, isExtracting, anexoItems
     - useEffect to calculate montoTotal when anexoItems change
   - **Validation**:
     - Client selected (required)
     - Cotización uploaded and extracted (required)
     - Numero cotización non-empty
     - Fecha contrato valid date
     - Dias plazo in range 30-180
     - At least one anexo item
     - All anexo items have valid amounts > 0

### Phase 3: Integration and Testing

9. **Integrate Form into Operations Dashboard** (`FKPagaLocalCODocumentosOperacion.tsx`):
   - Import `FKSolicitudDesembolsoRequest` component
   - Replace generic `FKPagaLocalCOContractRequest` in tab 2 with `<FKSolicitudDesembolsoRequest />`
   - Remove contract type prop (hardcoded to `pl_co_solicitud_desembolso` in specialized component)
   - Verify tab label: "Solicitud de Desembolso"

10. **Create E2E Test File** (`.claude/commands/e2e/test_solicitud_desembolso_request.md`):
    - Follow structure from `test_contract_request.md` and `test_login.md`
    - **User Story**: Operations user uploading Cotización PDF and generating Solicitud de Desembolso
    - **Prerequisites**: Operations user logged in, test Cotización PDF available, test client exists
    - **Test Steps**:
      1. Login as operations user
      2. Navigate to `/operations/contratos-paga-local-colombia`
      3. Click "Solicitud de Desembolso" tab
      4. Screenshot: Empty form
      5. Search and select test client by NIT
      6. Upload test Cotización PDF
      7. Click "Extraer Datos" button
      8. Verify extracted data appears in form fields
      9. Screenshot: Form with extracted data
      10. Edit anexo table (add/remove rows)
      11. Verify monto total auto-calculates
      12. Screenshot: Complete form ready for submission
      13. Click "Solicitar Documento"
      14. Verify success message
      15. Navigate to Legal review queue
      16. Verify new PLSD contract appears with status "under_review"
      17. Screenshot: Contract in review queue
    - **Success Criteria**:
      - PDF upload and extraction work without errors
      - All form fields are editable
      - Anexo table add/remove functionality works
      - Total calculation is accurate
      - Document submission succeeds
      - Contract appears in Legal queue with correct status and ID format (PLSD-2025-XXX)

11. **Backend Integration Testing**:
    - Create `backend/tests/test_solicitud_desembolso_integration.py`
    - Test complete flow: parse PDF → generate contract → verify database record
    - Test API endpoints with FastAPI TestClient
    - Verify contract ID generation with PLSD prefix
    - Verify data snapshot structure in database
    - Test error scenarios: invalid PDF, missing client, invalid data

12. **Manual Testing Checklist**:
    - Test with real Cotización PDF from `Example FIles for Reqs/` directory
    - Verify all placeholders in generated Word document are populated correctly
    - Verify Anexo I table in document matches form input exactly
    - Test Legal approval workflow (approve contract, verify PDF generation)
    - Test downloading approved document from Contratos Aprobados tab
    - Verify edge cases: empty Anexo table (should error), negative amounts (should error)

## Step by Step Tasks

### Task 1: Create Backend DTOs for Solicitud de Desembolso
- Open `backend/src/interface/legal_dtos.py`
- Add `AnexoItem` Pydantic model with fields: acreedor (str), numero_instrumento (str), monto (Decimal)
- Add validator to `AnexoItem`: monto must be > 0
- Add `CotizacionData` Pydantic model with fields from PDF extraction (numero_cotizacion, fecha_cotizacion, fecha_contrato_credito, representante_legal, tipo_id_representante, numero_id_representante, anexo_items, monto_total)
- Add `SolicitudDesembolsoRequest` Pydantic model with fields: client_nit (str), numero_cotizacion_desembolso (str), fecha_contrato_credito (date), monto (Decimal), dias_plazo (int, default 120), anexo_items (List[AnexoItem])
- Add validators: client_nit non-empty, monto > 0, dias_plazo range 30-180, anexo_items non-empty list
- Run backend linting: `cd backend && ruff check src/`

### Task 2: Implement Cotización PDF Parser Service
- Create `backend/src/core/servicios/cotizacion_parser_service.py`
- Import PyMuPDF (fitz), re, logging, Decimal, date from datetime
- Create `CotizacionParserService` class with `parse_cotizacion(pdf_bytes: bytes) -> CotizacionData` method
- Implement text extraction: open PDF with fitz, extract text from each page
- Implement `_extract_numero_cotizacion()`: regex pattern for "CO:{digits}:{digits}:{digits}:DOM"
- Implement `_extract_fecha_cotizacion()`: Spanish date parsing with regex (e.g., "10 de noviembre de 2025")
- Implement `_extract_fecha_contrato_credito()`: same date parsing logic
- Implement `_extract_representante_legal()`: search for name patterns on page 2
- Implement `_extract_tipo_id_representante()`: search for "C.C.", "C.E.", "NIT" patterns
- Implement `_extract_numero_id_representante()`: extract ID number near tipo_id
- Implement `_extract_anexo_table()`: parse table structure on page 3, extract rows with acreedor, numero_instrumento, monto
- Calculate monto_total by summing all anexo item amounts
- Add comprehensive logging for each extraction step
- Handle extraction failures gracefully with Optional fields
- Raise descriptive exceptions for critical missing data

### Task 3: Write Unit Tests for Cotización Parser
- Create `backend/tests/test_cotizacion_parser_service.py`
- Create test fixture with sample Cotización PDF bytes (use `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`)
- Test `parse_cotizacion()` returns valid `CotizacionData` with all fields populated
- Test date parsing with various Spanish formats
- Test Anexo table extraction with 1, 3, 5 rows
- Test monto_total calculation accuracy
- Test handling of missing optional fields (representante_legal, etc.)
- Run tests: `cd backend && python -m pytest tests/test_cotizacion_parser_service.py -v`

### Task 4: Add Backend API Endpoints for Solicitud de Desembolso
- Open `backend/src/adapter/rest/operations_routes.py`
- Import `CotizacionParserService`, `SolicitudDesembolsoRequest`, `CotizacionData` from appropriate modules
- Add endpoint `POST /contracts/solicitud-desembolso/parse-cotizacion`:
  - Parameter: `file: UploadFile = File(...)`
  - Dependency: `current_user: dict = Depends(require_operations_role)`
  - Validate file: content_type == 'application/pdf', size <= 5MB
  - Read file bytes: `pdf_bytes = await file.read()`
  - Instantiate `CotizacionParserService` and call `parse_cotizacion(pdf_bytes)`
  - Return `CotizacionData` DTO
  - Handle parsing exceptions with HTTP 422 and descriptive error message
- Add endpoint `POST /contracts/solicitud-desembolso/generate`:
  - Parameter: `request: SolicitudDesembolsoRequest`
  - Dependency: `current_user: dict = Depends(require_operations_role)`
  - Validate client exists by NIT using `client_repository.get_by_nit()`
  - Call `contract_service.generate_contract()` with contract_type `pl_co_solicitud_desembolso`
  - Build data snapshot combining client data + solicitud data
  - Return contract generation response with contract ID, status, created timestamp
- Add comprehensive error handling and logging for both endpoints
- Run backend linting: `cd backend && ruff check src/`

### Task 5: Implement Document Service Handler for Solicitud de Desembolso
- Open `backend/src/core/servicios/document_service.py`
- In `generate_contract_document()` method, add routing case:
  ```python
  elif contract_type == 'pl_co_solicitud_desembolso':
      return self.generate_solicitud_desembolso_document(contract_data)
  ```
- Implement `generate_solicitud_desembolso_document(contract_data: Dict[str, Any]) -> bytes`:
  - Get template path: "FK COL - Fin. COP - Solicitud de Desembolso.docx"
  - Load template with python-docx: `Document(template_path)`
  - Call `_prepare_solicitud_desembolso_replacements(contract_data)` to get placeholder mapping
  - Replace all text placeholders in paragraphs and tables
  - Call `_populate_anexo_table(document, contract_data['anexo_items'])` to fill Anexo I table
  - Save document to BytesIO buffer
  - Return bytes
- Implement `_prepare_solicitud_desembolso_replacements(data: Dict) -> Dict[str, str]`:
  - Map all template placeholders to data values
  - Generate consecutivo: `f"CO:{data['nit']}:1:D:M:DOM"`
  - Format dates in Spanish using `_get_spanish_month()` helper
  - Format currency amounts with Colombian peso format
  - Return dictionary of placeholder → value mappings
- Implement `_populate_anexo_table(document: Document, anexo_items: List[Dict])`:
  - Find Anexo I table in document by searching for header text
  - Get table row template (assume row 2 is template)
  - For each anexo item: clone row, populate cells with acreedor, numero_instrumento, formatted monto
  - Add total row at end with sum of all amounts
  - Format all currency values consistently
- Run backend linting: `cd backend && ruff check src/`

### Task 6: Create Frontend TypeScript Types
- Open `frontend/src/types/legal.ts`
- Add `AnexoItem` interface:
  ```typescript
  export interface AnexoItem {
    acreedor: string;
    numeroInstrumento: string;
    monto: number;
  }
  ```
- Add `CotizacionData` interface:
  ```typescript
  export interface CotizacionData {
    numeroCotizacion: string;
    fechaCotizacion: string;
    fechaContratCredito: string;
    representanteLegal?: string;
    tipoIdRepresentante?: string;
    numeroIdRepresentante?: string;
    anexoItems: AnexoItem[];
    montoTotal: number;
  }
  ```
- Add `SolicitudDesembolsoRequest` interface:
  ```typescript
  export interface SolicitudDesembolsoRequest {
    client_nit: string;
    numero_cotizacion_desembolso: string;
    fecha_contrato_credito: string; // ISO date string
    monto: number;
    dias_plazo: number;
    anexo_items: AnexoItem[];
  }
  ```
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`

### Task 7: Add Frontend Service Methods for Solicitud de Desembolso
- Open `frontend/src/services/operationsService.ts`
- Import types: `AnexoItem`, `CotizacionData`, `SolicitudDesembolsoRequest` from '@/types/legal'
- Implement `parseCotizacionPdf(file: File): Promise<CotizacionData>`:
  - Create FormData: `const formData = new FormData()`
  - Append file: `formData.append('file', file)`
  - POST to `/operations/contracts/solicitud-desembolso/parse-cotizacion` with formData
  - Set headers: `'Content-Type': 'multipart/form-data'`
  - Return response.data as `CotizacionData`
  - Wrap in try-catch with user-friendly error message
- Implement `generateSolicitudDesembolso(request: SolicitudDesembolsoRequest): Promise<ContractGeneration>`:
  - POST to `/operations/contracts/solicitud-desembolso/generate` with request payload
  - Return response.data
  - Handle validation errors (422) with field-specific messages
- Run frontend linting: `cd frontend && npm run lint`

### Task 8: Create Specialized Form Component for Solicitud de Desembolso
- Create `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`
- Import dependencies: React, useState, useEffect, react-hook-form, Material-UI components, operationsService, types
- Define component state interfaces:
  - `selectedClient: Client | null`
  - `cotizacionFile: File | null`
  - `extractedData: CotizacionData | null`
  - `isExtracting: boolean`
  - `anexoItems: AnexoItem[]`
- Initialize react-hook-form with default values
- **Section 1: Client Search**:
  - TextField for NIT search with debounced search
  - Display selected client info (Card with Typography)
  - Reset button to clear selection
- **Section 2: Cotización Upload**:
  - Hidden file input with ref
  - Button to trigger file selection
  - Display selected filename
  - File validation: PDF only, max 5MB
  - "Extraer Datos" Button with loading state
  - Call `operationsService.parseCotizacionPdf(cotizacionFile)` on click
  - Store extracted data in state
  - Display error if extraction fails (Alert component)
- **Section 3: Extracted Data Fields (Editable)**:
  - TextField: Número de Cotización (pre-filled from extractedData, required)
  - DatePicker: Fecha del Contrato de Crédito (pre-filled, required)
  - TextField: Días de Plazo (number input, default 120, validation: 30-180)
  - Typography: Monto Total (read-only, formatted currency, auto-calculated from anexoItems)
- **Section 4: Anexo I Table (Dynamic)**:
  - Table with columns: Acreedor, No. Instrumento, Monto, Actions
  - Each row: TextField inputs for editable cells, IconButton for delete
  - Button: "Agregar Fila" (adds empty row to anexoItems state)
  - Pre-populate rows from extractedData.anexoItems
  - Calculate total in useEffect when anexoItems change
- **Section 5: Preview & Submit**:
  - Card with summary: client name, numero cotizacion, fecha contrato, dias plazo, monto total, anexo count
  - Button: "Solicitar Documento" (primary color, large size)
  - Disable if form invalid or missing required data
  - On submit: call `operationsService.generateSolicitudDesembolso(payload)`
  - Show success Snackbar on success
  - Show error Alert on failure
- **Validation Logic**:
  - Client must be selected
  - Cotización must be uploaded and extracted
  - Numero cotización non-empty string
  - Fecha contrato valid date
  - Dias plazo number in range 30-180
  - At least one anexo item
  - All anexo items must have: non-empty acreedor, non-empty numero_instrumento, monto > 0
- Export component with FK prefix: `export const FKSolicitudDesembolsoRequest: React.FC = () => { ... }`
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`
- Run frontend linting: `cd frontend && npm run lint`

### Task 9: Integrate Form into Paga Local CO Operations Dashboard
- Open `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`
- Import new component: `import { FKSolicitudDesembolsoRequest } from './FKSolicitudDesembolsoRequest';`
- Locate tab 2 (Solicitud de Desembolso tab)
- Replace existing `<FKPagaLocalCOContractRequest contractType="pl_co_solicitud_desembolso" ... />` with `<FKSolicitudDesembolsoRequest />`
- Remove unnecessary props (contractType, contractLabel, description - now hardcoded in specialized component)
- Verify tab label is "Solicitud de Desembolso"
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`
- Run frontend linting: `cd frontend && npm run lint`

### Task 10: Create E2E Test File for Solicitud de Desembolso Workflow
- Create `.claude/commands/e2e/test_solicitud_desembolso_request.md`
- Follow structure from `test_contract_request.md` and `test_login.md`
- Write sections: User Story, Prerequisites, Test Steps, Success Criteria
- **User Story**: "As an Operations team member, I want to upload a Cotización PDF and generate a Solicitud de Desembolso document, so that Legal can review and approve it"
- **Prerequisites**:
  - User logged in with `operations` role
  - Backend and frontend servers running
  - Test client exists in database (NIT: 900436389)
  - Test Cotización PDF available: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
- **Test Steps** (17 steps):
  1. Login as operations user
  2. Navigate to `/operations/contratos-paga-local-colombia`
  3. Click "Solicitud de Desembolso" tab (tab 2)
  4. Take screenshot: Empty Solicitud de Desembolso form
  5. Search for client by NIT: 900436389
  6. Verify client appears in search results
  7. Select client
  8. Verify client info displays
  9. Click file upload button
  10. Upload test Cotización PDF
  11. Verify filename displays
  12. Click "Extraer Datos" button
  13. Wait for extraction to complete (loading state)
  14. Verify extracted data populates form fields (numero cotizacion, fecha contrato, anexo table)
  15. Take screenshot: Form with extracted data
  16. Edit dias_plazo field to 90
  17. Add one row to Anexo table manually
  18. Verify monto total recalculates correctly
  19. Take screenshot: Complete form ready for submission
  20. Click "Solicitar Documento" button
  21. Wait for submission to complete
  22. Verify success message appears (Snackbar or Alert)
  23. Navigate to `/department/legal` (Legal dashboard)
  24. Navigate to review queue tab
  25. Verify new contract with ID format PLSD-2025-XXX appears
  26. Verify contract status is "under_review"
  27. Verify contract details match submitted data (client NIT, numero cotizacion)
  28. Take screenshot: Contract in Legal review queue
- **Success Criteria**:
  - Solicitud de Desembolso form loads without errors
  - PDF upload accepts only PDF files and validates size
  - Data extraction completes successfully and populates fields
  - All form fields are editable
  - Anexo table add/remove row functionality works
  - Monto total auto-calculates accurately
  - Form validation prevents invalid submission
  - Contract is created with correct ID format (PLSD-2025-XXX)
  - Contract appears in Legal review queue with status "under_review"
  - 4 screenshots captured: empty form, extracted data, complete form, review queue

### Task 11: Run Backend Integration Tests
- Create `backend/tests/test_solicitud_desembolso_integration.py`
- Import FastAPI TestClient, pytest, services, repositories
- Create test fixtures: test_client (TestClient), test_db (database session), test_user (operations role), test_pdf (Cotización PDF bytes)
- Test `parse_cotizacion_pdf` endpoint:
  - POST PDF file to `/api/operations/contracts/solicitud-desembolso/parse-cotizacion`
  - Assert response status 200
  - Assert CotizacionData structure is correct
  - Assert extracted fields are non-empty
- Test `generate_solicitud_desembolso` endpoint:
  - POST valid SolicitudDesembolsoRequest to `/api/operations/contracts/solicitud-desembolso/generate`
  - Assert response status 200
  - Assert contract ID format: PLSD-YYYY-XXX
  - Assert contract status: "under_review"
  - Query database to verify contract record exists
  - Verify data snapshot structure
- Test error scenarios:
  - Invalid file type (non-PDF) → expect 422
  - File too large (>5MB) → expect 422
  - Missing client NIT → expect 404
  - Invalid dias_plazo (out of range) → expect 422
  - Empty anexo_items → expect 422
- Run tests: `cd backend && python -m pytest tests/test_solicitud_desembolso_integration.py -v`

### Task 12: Manual Testing and Validation
- Start development servers:
  - Backend: `cd backend && python -m uvicorn main:app --reload`
  - Frontend: `cd frontend && npm run dev`
- Login as operations user
- Navigate to Paga Local Colombia contracts → Solicitud de Desembolso tab
- **Test 1: PDF Upload and Extraction**:
  - Upload `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
  - Click "Extraer Datos"
  - Verify extracted data: numero_cotizacion (CO:900436389:1:2:DOM), fecha_contrato_credito (Nov 6, 2025), anexo_items (3 rows)
  - Verify monto_total calculation: $739,860.00
- **Test 2: Form Editing**:
  - Edit numero cotizacion field
  - Change fecha_contrato_credito date
  - Add new anexo row manually
  - Remove one anexo row
  - Verify monto_total recalculates correctly
- **Test 3: Form Validation**:
  - Clear required fields, verify submit button disabled
  - Enter invalid dias_plazo (e.g., 200), verify error message
  - Remove all anexo items, verify error message
- **Test 4: Document Generation**:
  - Fill form completely
  - Click "Solicitar Documento"
  - Verify success message
  - Check network tab: verify API call to `/generate` endpoint succeeded
- **Test 5: Legal Review Queue**:
  - Switch to Legal user (or navigate to Legal dashboard)
  - Open review queue
  - Verify new PLSD-2025-XXX contract appears
  - Verify contract details: client name, contract type, status "under_review", timestamp
- **Test 6: Document Approval**:
  - Approve the contract
  - Verify document generation (DOCX → PDF conversion)
  - Download approved PDF
  - Open PDF and verify: all placeholders replaced, Anexo I table matches input, correct formatting
- **Test 7: Approved Contracts Download**:
  - Navigate to Operations → Paga Local Colombia → Contratos Aprobados tab
  - Verify approved PLSD contract appears in list
  - Download PDF
  - Verify PDF is identical to Legal-approved version

### Task 13: Execute E2E Test and Capture Screenshots
- Read `.claude/commands/test_e2e.md` to understand E2E test execution
- Read `.claude/commands/e2e/test_solicitud_desembolso_request.md` (created in Task 10)
- Execute E2E test using Playwright MCP server:
  - Run: `/test_e2e f5fb4293 e2e_test_runner_0 .claude/commands/e2e/test_solicitud_desembolso_request.md http://localhost:5173`
  - Ensure backend and frontend servers are running
  - Ensure test user credentials are configured
  - Ensure test Cotización PDF exists in specified path
- Verify all test steps execute successfully
- Verify 4 screenshots are captured and saved to: `/Users/danielrestrepo/Finkargo_Automation_Hub/agents/f5fb4293/e2e_test_runner_0/img/solicitud_desembolso/`
- If any test step fails, debug and fix issue, then re-run test
- Verify E2E test JSON output shows `"status": "passed"`

### Task 14: Run All Validation Commands
- Execute validation commands in order:
  - `cd backend && python -m pytest` - Run all backend tests (must pass with zero failures)
  - `cd backend && ruff check src/` - Run backend linting (must show zero errors)
  - `cd frontend && npm run lint` - Run frontend linting (must pass ESLint rules)
  - `cd frontend && npx tsc --noEmit` - Run TypeScript type checking (must show zero errors)
  - `cd frontend && npm run build` - Run production build (must complete successfully without errors)
- If any validation fails, fix the issues and re-run
- Document any warnings or non-critical issues in implementation notes

## Testing Strategy

### Unit Tests

**Backend Unit Tests:**
1. **CotizacionParserService Tests** (`test_cotizacion_parser_service.py`):
   - Test successful extraction with valid PDF
   - Test each extraction method individually:
     - `_extract_numero_cotizacion()` with various formats
     - `_extract_fecha_cotizacion()` with different Spanish date formats
     - `_extract_fecha_contrato_credito()` with edge cases
     - `_extract_representante_legal()` with multiple name formats
     - `_extract_anexo_table()` with 0, 1, 3, 5 rows
   - Test monto_total calculation accuracy with Decimal precision
   - Test handling of missing optional fields (should return None)
   - Test handling of malformed PDF (should raise descriptive exception)

2. **DocumentService Tests** (add to existing `test_document_service.py`):
   - Test `generate_solicitud_desembolso_document()` with valid data
   - Test `_prepare_solicitud_desembolso_replacements()` placeholder mapping
   - Test `_populate_anexo_table()` with various row counts
   - Test date formatting in Spanish
   - Test currency formatting (Colombian pesos)
   - Test consecutivo generation format

**Frontend Unit Tests (Future Enhancement):**
- Component testing with React Testing Library (not configured yet, mentioned in CLAUDE.md)
- Test FKSolicitudDesembolsoRequest component:
  - File upload validation
  - Form field validation
  - Anexo table add/remove functionality
  - Monto total calculation
  - Form submission

### Integration Tests

**Backend Integration Tests** (`test_solicitud_desembolso_integration.py`):
1. Test complete flow: parse PDF → generate contract → verify database
2. Test API endpoints with FastAPI TestClient:
   - POST `/parse-cotizacion` with valid PDF → 200 response with CotizacionData
   - POST `/parse-cotizacion` with invalid file → 422 error
   - POST `/generate` with valid request → 200 response with ContractGeneration
   - POST `/generate` with missing client → 404 error
   - POST `/generate` with invalid data → 422 error
3. Test RBAC: unauthorized user (non-operations role) → 403 error
4. Test contract ID generation: verify PLSD-YYYY-XXX format and sequence
5. Test data snapshot: verify structure contains client + solicitud data

**E2E Tests** (Playwright):
- Test complete user workflow from login to document approval
- Validate UI interactions: PDF upload, data extraction, form editing, submission
- Verify integration with Legal review queue
- Capture screenshots at key steps for visual regression testing

### Edge Cases

1. **PDF Parsing Edge Cases:**
   - Empty PDF (0 pages) → should error gracefully
   - PDF without expected structure (missing sections) → should handle with Optional fields
   - PDF with malformed dates (e.g., "32 de febrero") → should error with validation message
   - Anexo table with 0 rows → should return empty list (form validation catches this)
   - Anexo table with negative amounts → parser extracts as-is, DTO validation catches error
   - Very large PDF (>5MB) → endpoint validation rejects before parsing

2. **Form Validation Edge Cases:**
   - Client not selected → submit button disabled
   - Cotización not uploaded → submit button disabled
   - Dias plazo = 0 or negative → validation error
   - Dias plazo = 1000 (out of range) → validation error
   - Anexo table empty → validation error
   - Anexo item with monto = 0 → validation error
   - Anexo item with negative monto → validation error
   - Anexo item with empty acreedor or numero_instrumento → validation error

3. **Document Generation Edge Cases:**
   - Template file missing → should error with descriptive message
   - Template structure changed (Anexo table not found) → should error gracefully
   - Very long anexo table (100+ rows) → should handle without performance issues
   - Special characters in data (e.g., accents, symbols) → should preserve correctly in document

4. **Database Edge Cases:**
   - Client NIT not found → 404 error before generation
   - Duplicate submission (same numero_cotizacion) → allow (no uniqueness constraint)
   - Contract ID sequence collision → database sequence handles atomically

5. **Concurrency Edge Cases:**
   - Multiple users uploading simultaneously → each request independent, no race condition
   - Multiple contracts generated simultaneously → database sequence ensures unique IDs

## Acceptance Criteria

1. **PDF Upload and Extraction:**
   - ✅ User can select and upload a PDF file (max 5MB)
   - ✅ Only PDF files are accepted (MIME type validation)
   - ✅ "Extraer Datos" button triggers parsing with loading state
   - ✅ Extracted data from Cotización PDF populates form fields automatically
   - ✅ Extraction errors display user-friendly error messages (not stack traces)

2. **Form Functionality:**
   - ✅ All extracted fields are editable (user can correct errors)
   - ✅ Anexo I table supports dynamic add/remove rows
   - ✅ Monto total auto-calculates when anexo items change
   - ✅ Form validation prevents submission with invalid data
   - ✅ Submit button is disabled when form is invalid or incomplete

3. **Document Generation:**
   - ✅ Generated Word document has all placeholders correctly filled:
     - Número de cotización de desembolso
     - Fecha de solicitud (current date in Spanish)
     - Consecutivo contrato crédito (CO:{NIT}:1:D:M:DOM format)
     - Fecha de firma del contrato de crédito (Spanish format)
     - Monto (formatted as Colombian pesos)
     - Días de plazo
   - ✅ Anexo I table in document matches user input exactly (all rows present)
   - ✅ Anexo I table total row displays correct sum
   - ✅ All currency values formatted consistently (e.g., "$739,860.00 COP")

4. **Workflow Integration:**
   - ✅ Generated contract is sent to Legal review queue with status `under_review`
   - ✅ Contract ID follows format: `PLSD-2025-001` (year and sequence auto-generated)
   - ✅ Contract appears in Legal review queue with correct details (client, type, timestamp)
   - ✅ Legal can approve/reject using existing workflow (no changes needed)
   - ✅ Approved PDF is downloadable from Contratos Aprobados tab

5. **User Experience:**
   - ✅ Success message displays after successful submission
   - ✅ Error messages are descriptive and actionable (not technical jargon)
   - ✅ Loading states communicate progress during async operations (extraction, submission)
   - ✅ Form sections are clearly labeled and organized
   - ✅ Submit button label is clear: "Solicitar Documento"

6. **Data Integrity:**
   - ✅ Client data from database is correctly combined with solicitud data
   - ✅ Data snapshot in database preserves all input for audit trail
   - ✅ No data loss occurs during extraction or generation process
   - ✅ Special characters and accents are preserved in document

7. **Security and Access Control:**
   - ✅ Only users with `operations` or `admin` roles can access the form
   - ✅ API endpoints are protected with RBAC (require_operations_role)
   - ✅ File upload validates file type and size to prevent abuse
   - ✅ PDF parsing is sandboxed (no arbitrary code execution risk)

8. **Testing and Quality:**
   - ✅ Unit tests pass for CotizacionParserService with 80%+ coverage
   - ✅ Integration tests pass for API endpoints with all scenarios covered
   - ✅ E2E test validates complete workflow end-to-end with screenshots
   - ✅ Backend linting passes with zero errors
   - ✅ Frontend linting passes with zero errors
   - ✅ TypeScript type checking passes with zero errors
   - ✅ Production build completes successfully

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

**Backend Validation:**
```bash
# Run all backend tests (including new unit and integration tests)
cd backend && python -m pytest

# Run tests with coverage report for new files
cd backend && python -m pytest tests/test_cotizacion_parser_service.py tests/test_solicitud_desembolso_integration.py -v --cov=src/core/servicios/cotizacion_parser_service --cov=src/adapter/rest/operations_routes --cov-report=term-missing

# Run backend linting
cd backend && ruff check src/

# Check for unused imports and code quality issues
cd backend && ruff check src/ --select F,E,W,I
```

**Frontend Validation:**
```bash
# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check (must show zero errors)
cd frontend && npx tsc --noEmit

# Run production build (validates all imports and dependencies)
cd frontend && npm run build

# Verify build output exists
ls -lh frontend/dist/
```

**E2E Test Validation:**
```bash
# Start development servers in background
./scripts/start-dev.sh

# Wait for servers to be ready
sleep 10

# Execute E2E test for Solicitud de Desembolso workflow
# (Read test_e2e.md, then execute test_solicitud_desembolso_request.md)
# Expected: 4 screenshots captured, all test steps pass, status "passed"

# Stop development servers
./scripts/stop-dev.sh
```

**Manual Verification Checklist:**
1. ✅ Upload test Cotización PDF and verify extraction accuracy
2. ✅ Submit form and verify contract appears in Legal review queue with PLSD-2025-XXX ID
3. ✅ Approve contract in Legal dashboard
4. ✅ Download approved PDF and verify all placeholders are correctly populated
5. ✅ Verify Anexo I table in PDF matches submitted data exactly
6. ✅ Test edge cases: invalid file type, empty form submission, invalid dias_plazo

**API Endpoint Testing (Optional - using curl or Postman):**
```bash
# Test parse-cotizacion endpoint
curl -X POST http://localhost:8000/api/operations/contracts/solicitud-desembolso/parse-cotizacion \
  -H "Authorization: Bearer <token>" \
  -F "file=@path/to/test-cotizacion.pdf"

# Test generate endpoint
curl -X POST http://localhost:8000/api/operations/contracts/solicitud-desembolso/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_nit": "900436389",
    "numero_cotizacion_desembolso": "CO:900436389:1:2:DOM",
    "fecha_contrato_credito": "2025-11-06",
    "monto": 739860.00,
    "dias_plazo": 120,
    "anexo_items": [
      {"acreedor": "Entidad de pago de Impuestos", "numero_instrumento": "1003887257", "monto": 407001.00}
    ]
  }'
```

**Regression Testing:**
- ✅ Verify existing contract types still work (Activos, Otrosí, Inventario Bodega, Paga Local Crédito)
- ✅ Verify Legal review queue still displays all contract types correctly
- ✅ Verify approved contracts download functionality still works for all types

## Notes

### Technical Implementation Notes

1. **PyMuPDF Dependency:**
   - PyMuPDF (fitz) is already in `requirements.txt` (used by RutParserService)
   - Version: 1.23.0+ (compatible with Python 3.11.9)
   - No additional backend dependencies needed

2. **Date Parsing Strategy:**
   - Spanish month names: enero, febrero, marzo, abril, mayo, junio, julio, agosto, septiembre, octubre, noviembre, diciembre
   - Regex pattern: `(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})`
   - Convert month name to month number using dictionary lookup
   - Construct datetime object: `datetime(year, month, day)`

3. **Anexo Table Population:**
   - Use python-docx table API: `document.tables[index]`
   - Clone row template: `new_row = table.add_row()`
   - Populate cells: `new_row.cells[0].text = acreedor`
   - Preserve formatting from template (fonts, alignment, borders)

4. **Currency Formatting:**
   - Colombian peso format: `$###,###,###.## COP`
   - Use locale formatting or custom function
   - Ensure consistency across document (placeholders and table)

5. **Form State Management:**
   - Use react-hook-form for main form fields (numero_cotizacion, fecha_contrato, dias_plazo)
   - Use separate useState for anexoItems (dynamic array, easier to manipulate)
   - Sync anexoItems with form state on submit
   - Calculate montoTotal in useEffect whenever anexoItems change

6. **File Upload Security:**
   - Backend validates MIME type: `application/pdf`
   - Backend validates file size: max 5MB (5 * 1024 * 1024 bytes)
   - Frontend validates before upload for better UX
   - PyMuPDF sandboxes PDF parsing (no script execution)

### Future Enhancements (Out of Scope)

1. **OCR for Scanned PDFs:**
   - Current implementation assumes text-based PDFs
   - If clients provide scanned/image PDFs, add OCR preprocessing (Tesseract)

2. **Batch Processing:**
   - Allow upload of multiple Cotización PDFs
   - Generate multiple Solicitudes de Desembolso in one operation

3. **PDF Template Validation:**
   - Pre-validate uploaded PDF structure before parsing
   - Provide feedback if PDF doesn't match expected Cotización format

4. **Machine Learning Extraction:**
   - Replace regex-based extraction with ML model for more robust parsing
   - Train on corpus of Cotización PDFs for higher accuracy

5. **Anexo Table Import from Excel:**
   - Allow pasting Anexo data from Excel/CSV
   - Bulk import for large tables (50+ rows)

### Known Limitations

1. **PDF Format Dependency:**
   - Parser is tuned for specific Cotización PDF format from HubSpot
   - Changes to PDF template may require parser updates
   - Mitigation: Use multi-strategy extraction with fallbacks

2. **Date Format Assumptions:**
   - Assumes Spanish date format: "DD de MONTH de YYYY"
   - May fail with alternative formats (e.g., "DD/MM/YYYY")
   - Mitigation: Add multiple date parsing strategies

3. **No Duplicate Detection:**
   - System allows multiple contracts with same numero_cotizacion
   - No uniqueness constraint on this field
   - Rationale: Intentional - allows resubmissions and corrections

4. **Manual Anexo Table Editing:**
   - If extracted Anexo data is wrong, user must manually fix all rows
   - No row-level re-extraction
   - Mitigation: Clear UX for editing, validation prevents submission of invalid data

### Deployment Considerations

1. **Environment Variables:**
   - No new environment variables required
   - Uses existing Supabase and backend configuration

2. **Database Migration:**
   - No migration needed - contract type and prefix already configured
   - Verify `pl_co_solicitud_desembolso` exists in production database

3. **Template Deployment:**
   - Ensure template file is deployed: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
   - Verify file permissions (readable by backend process)

4. **Testing in Production:**
   - Test with real Cotización PDFs from HubSpot
   - Monitor extraction accuracy and adjust parser if needed
   - Collect feedback from Operations team on form UX

### Documentation and Training

1. **User Documentation:**
   - Create user guide for Operations team (screenshots, step-by-step)
   - Document common errors and troubleshooting steps
   - Provide examples of valid Cotización PDFs

2. **Developer Documentation:**
   - Add inline comments in CotizacionParserService explaining extraction logic
   - Document Anexo table population algorithm in DocumentService
   - Update CLAUDE.md with Solicitud de Desembolso implementation patterns

3. **Training:**
   - Conduct training session with Operations team
   - Demonstrate PDF upload, extraction, editing, and submission workflow
   - Collect feedback on usability and edge cases
