# Feature: Instruccion de Mandato (Mandate Instruction) Document Generation

## Feature Description

Implement the "Instruccion de Mandato" (Mandate Instruction) document generation feature for the Paga Local Colombia workflow. This feature enables legal and operations users to generate mandate instruction documents by uploading a Cotización PDF and optionally Bank Certificate PDFs. The system extracts data from these documents, validates them, and generates a properly formatted Instruccion de Mandato document that authorizes Finkargo to transfer funds to National Expense Creditors on behalf of clients.

The feature includes:
- Bank Certificate PDF parsing service to extract creditor bank account information
- Cotización PDF parsing (reusing existing service) to extract disbursement details
- Document generation service to populate the Instruccion de Mandato template
- API endpoints for PDF parsing and document generation
- Frontend form with multi-step wizard for file upload and data review
- Support for multiple creditors (up to 3 per document)
- DIAN static values configuration for tax authority payments

**Scope:** This implementation handles non-DIAN creditors only (contract type `pl_co_mandato_im`). DIAN-specific payments will be implemented separately with contract type `pl_co_dian_mandato_im`.

## User Story

As a **legal team member or operations specialist**
I want to upload Cotización and Bank Certificate PDFs to generate Instruccion de Mandato documents
So that I can quickly authorize Finkargo to transfer funds to creditors with accurate bank information extracted automatically

## Problem Statement

Currently, the Finkargo Automation Hub supports various contract types but lacks support for generating Instruccion de Mandato documents, which are essential for the Paga Local Colombia disbursement workflow. Users need to:

1. Manually extract creditor bank account information from Bank Certificate PDFs
2. Manually extract disbursement details from Cotización PDFs
3. Manually fill in mandate instruction documents
4. Risk data entry errors that could cause payment failures

This manual process is time-consuming, error-prone, and blocks the Mesa de Control team from releasing disbursements until bank certificates are processed.

## Solution Statement

Automate the Instruccion de Mandato document generation by:

1. **Creating a Bank Certificate Parser Service** that extracts creditor information (company name, NIT, bank, account type, account number) from Bancolombia and BBVA certificate PDFs using regex patterns and text extraction
2. **Reusing the existing Cotización Parser Service** to extract disbursement details (numero_cotizacion, fecha_contrato, monto_total, creditor list)
3. **Extending the Document Service** to populate the Instruccion de Mandato template with extracted data, including dynamic creditor table population
4. **Building API endpoints** for PDF parsing and document generation with proper error handling and validation
5. **Creating a multi-step frontend form** that guides users through: uploading PDFs → reviewing extracted data → generating document
6. **Supporting multiple creditors** (up to 3) with automatic DIAN detection and manual entry fallback

This solution reduces document preparation time from 30+ minutes to under 5 minutes, eliminates data entry errors, and integrates seamlessly with the existing Paga Local workflow.

## Access Control

- **Required Role(s):** `admin`, `legal`, `operations`
- **Backend Protection:** Use `require_roles(['admin', 'legal', 'operations'])` RBAC dependency for all endpoints
- **Frontend Protection:**
  ```typescript
  <RoleProtectedRoute allowedRoles={['admin', 'legal', 'operations']}>
    <InstruccionMandatoPage />
  </RoleProtectedRoute>
  ```

**Rationale:** Legal team generates contracts, Operations team requests disbursements, and Admins need full access for troubleshooting.

## Relevant Files

### Backend Files (Existing)

- **`backend/src/interface/legal_dtos.py`** (lines 11-32, 50+)
  - Contains `ContractType` enum with `PL_CO_MANDATO_IM = "pl_co_mandato_im"` (line 30) - already exists
  - Will add new DTOs: `AcreedorGastosNacionales`, `InstruccionMandatoRequest`, `BankCertificateData`

- **`backend/src/core/servicios/document_service.py`** (1518+ lines)
  - Main document generation service with routing logic (lines 68-90)
  - Will add `generate_instruccion_mandato_document()` method
  - Will add helper methods: `_prepare_instruccion_mandato_replacements()`, `_populate_acreedores_table()`
  - Existing helper: `_number_to_words_spanish()` (line 755+) - reuse for monto en letras

- **`backend/src/core/servicios/cotizacion_parser_service.py`** (490 lines)
  - Existing parser for Cotización PDFs - will reuse for extracting numero_cotizacion, fecha_contrato_credito, monto_total, anexo_items
  - Reference pattern for building Bank Certificate parser

- **`backend/src/adapter/rest/legal_routes.py`** or **`operations_routes.py`**
  - Will add 3 new endpoints: parse-cotizacion, parse-bank-certificate, generate endpoints
  - Follows existing file upload patterns (lines 168-230 in operations_routes.py)

- **`backend/src/adapter/rest/rbac_dependencies.py`**
  - Contains `require_roles()` dependency for authorization

- **`backend/templates/FK COL - Fin. COP - Mandato (IM).docx`**
  - Template file exists - contains placeholders for main document and nested creditor table

### Frontend Files (Existing)

- **`frontend/src/types/legal.ts`** (193 lines)
  - Contains existing types: `CotizacionData`, `AnexoItem`, `SolicitudDesembolsoRequest`
  - Will add: `AcreedorGastosNacionales`, `InstruccionMandatoRequest`, `InstruccionMandatoFormData`, `BankCertificateData`
  - Contract type union already includes `'pl_co_mandato_im'` (line 123)

- **`frontend/src/services/legalService.ts`** or **`operationsService.ts`**
  - Will add service methods: `parseCotizacionForMandato()`, `parseBankCertificate()`, `generateInstruccionMandato()`

- **`frontend/src/App.tsx`**
  - Will add route for Instruccion de Mandato page with role protection

- **`frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`** (280+ lines)
  - Reference pattern for multi-section form with PDF upload and data extraction

### New Files

#### Backend

- **`backend/src/core/servicios/bank_certificate_parser_service.py`**
  - New PDF parser service to extract bank account information from Bancolombia and BBVA certificates
  - Pattern: Similar to `cotizacion_parser_service.py` with bank-specific extraction strategies

- **`backend/src/core/servicios/constants.py`**
  - Constants file for DIAN creditor static values
  - Contains `DIAN_CREDITOR_INFO` dict and `DIAN_KEYWORDS` list

- **`backend/tests/test_bank_certificate_parser_service.py`**
  - Unit tests for bank certificate parser
  - Test cases: valid certificates, invalid PDFs, missing fields, multi-format support

#### Frontend

- **`frontend/src/components/forms/FKInstruccionMandatoForm.tsx`**
  - Main form component with multi-step wizard (Client Search → PDF Upload → Data Review → Generate)
  - Handles Cotización upload, Bank Certificate upload, creditor management, document generation

- **`frontend/src/components/ui/FKAcreedorCard.tsx`**
  - Reusable card component to display/edit single creditor information
  - Shows: razon_social, NIT, banco, tipo_cuenta, numero_cuenta
  - Supports edit mode and read-only mode

- **`frontend/src/pages/legal/InstruccionMandatoPage.tsx`**
  - Page component that renders FKInstruccionMandatoForm
  - Handles navigation after successful generation

- **`.claude/commands/e2e/test_instruccion_mandato_generation.md`**
  - E2E test to validate the complete workflow from PDF upload to document generation

## Pre-Implementation Verification

### Feature Category

- [x] **Document Generation** (contracts, PDFs) → Complete sections A, D, E
- [x] **Data Import/Export** (CSV, ZIP) → Complete sections C, D (for PDF imports)
- [ ] Excel Processing (treasury, finance) → N/A
- [ ] API Integration (external services) → N/A
- [ ] Reporting (queries, history) → N/A
- [ ] CRUD Operations (basic data management) → N/A

### A. Template Placeholder Inventory (Document Generation)

Based on the data sources document (`docs/20251207_INSTRUCCION_MANDATO_DATA_SOURCES.md`), the template contains the following placeholders:

| Placeholder | Data Source | Format | Notes |
|-------------|-------------|--------|-------|
| `[Fecha actual]` | System.now() | "DD de MONTH de YYYY" | Current generation date in Spanish |
| `[Numero de cotizacion de desembolso]` | Cotizacion PDF | String | Format: CO:900436389:1:2:DOM |
| `[dia de firma contrato mandato]` | Cotizacion PDF (fecha_contrato_credito) | Integer | Day number (e.g., 6) |
| `[mes de firma contrato mandato]` | Cotizacion PDF (fecha_contrato_credito) | String | Spanish month name (e.g., "noviembre") |
| `[ano de firma contrato mandato]` | Cotizacion PDF (fecha_contrato_credito) | Integer | 4-digit year (e.g., 2025) |
| `[monto a transferir en letras]` | Derived from monto_total | String | Spanish words (e.g., "SETECIENTOS TREINTA Y NUEVE MIL...") |
| `[monto a transferir en numeros]` | Cotizacion PDF (monto_total) | String | Formatted number (e.g., "$739,860") |
| `[Nombre del representante legal del Cliente]` | Database (clients.representante_legal) | String | Legal representative full name |
| `[numero ID representante legal]` | Database (clients.cedula_representante) | String | ID number (e.g., "1234567890") |

**Nested Table Placeholders (Creditor Information Table):**

The template contains a nested table (Table 0 → Row 3 → Cell 0 → Nested Table) with 3 data rows for creditors. Each row has:

| Column | Placeholder | Data Source | Format |
|--------|-------------|-------------|--------|
| Razon social | `[...]` | Bank Certificate PDF or DIAN constant | String (company name) |
| NIT (si aplica) | `[...]` | Bank Certificate PDF or DIAN constant | String (e.g., "901599856" or "800.197.268-4") |
| Banco | `[...]` | Bank Certificate PDF or DIAN constant | String (e.g., "BANCOLOMBIA" or "PSE/Recaudo Electronico") |
| Tipo de Cuenta | `[Ahorros \| Corriente]` | Bank Certificate PDF or DIAN constant | String (e.g., "CUENTA DE AHORROS", "CUENTA CORRIENTE", "PCE") |
| Numero de Cuenta | `[...]` | Bank Certificate PDF or DIAN constant | String (account number or "N/A - Pago Electronico") |

**DIAN Static Values (for future implementation):**
- Razon Social: "DIAN - Direccion de Impuestos y Aduanas Nacionales"
- NIT: "800.197.268-4"
- Banco: "PSE/Recaudo Electronico"
- Tipo de Cuenta: "PCE"
- Numero de Cuenta: "N/A - Pago Electronico"

### B. Excel Column Mapping (Excel Processing)

**N/A** - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export)

#### Cotización PDF (Input)

| Format | Max Size | Required Content | Validation Rules |
|--------|----------|------------------|------------------|
| PDF | 5MB | Numero de cotizacion, Fecha contrato credito, Anexo I table with creditors | Must be valid PDF, must contain extractable text |

**Expected Fields:**
- Numero de cotizacion (Format: CO:XXXXXXXXX:X:X:XXX)
- Fecha del contrato de credito (Format: "6 de noviembre de 2025")
- Anexo I table with columns: Acreedor, No. Instrumento, Monto

#### Bank Certificate PDF (Input)

| Format | Max Size | Required Content | Validation Rules |
|--------|----------|------------------|------------------|
| PDF | 5MB | Company name, NIT, Bank name, Account type, Account number | Must be valid PDF, must contain extractable text, must match Bancolombia or BBVA format |

**Expected Fields:**
- Company Name (Razon Social)
- NIT (Tax ID)
- Bank Name (BANCOLOMBIA, BBVA, etc.)
- Account Type (CUENTA DE AHORROS, CUENTA CORRIENTE)
- Account Number (10+ digit number)

**Bancolombia Format:**
```
BANCOLOMBIA S.A. se permite informar que [COMPANY_NAME] identificado(a) con
NIT [NIT], a la fecha de expedicion...

| Producto | No. Producto | Fecha Apertura | Estado |
| CUENTA DE AHORROS | 77500002334 | 2022/06/03 | ACTIVA |
```

**Extraction Regex Patterns:**
- Company Name: `informar que (.+?) identificado`
- NIT: `NIT (\d+)`
- Bank: Extract from header/logo or document title
- Account Type: `(CUENTA DE AHORROS|CUENTA CORRIENTE)`
- Account Number: `\d{10,}` in the product table

### D. Data Contract Verification (ALL features)

#### Repository Return Types

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `client_repository.get_by_nit(nit)` | dict | `data['nit']`, `data['representante_legal']` | Use dict bracket notation |
| `contract_repository.create_contract(...)` | dict | `data['id']`, `data['contract_id']` | Use dict bracket notation |
| `template_repository.get_active_template(contract_type)` | dict | `data['id']`, `data['template_content']` | Use dict bracket notation |

**Note:** All repository methods in this project return `dict` objects (from Supabase queries), NOT SQLAlchemy model objects. Always use bracket notation `data['field']`, never dot notation `data.field`.

### E. Database Dependencies Checklist (Document/CRUD)

- [x] **Contract type enum exists** in `legal_dtos.py`: `PL_CO_MANDATO_IM = "pl_co_mandato_im"` (line 30)
- [x] **Template file exists** in `backend/templates/`: `FK COL - Fin. COP - Mandato (IM).docx`
- [ ] **Database migration needed:** No - contract type and template table structure already support this type
- [ ] **Contract ID prefix exists:** No new prefix needed - will use existing "ACT-YYYY-NNN" format
- [x] **Country-specific handling:** Yes - Colombia-specific (CO), uses COP currency and Spanish text

**Database Records Verification:**
- Template record must exist in `contract_templates` table with `contract_type='pl_co_mandato_im'`, `active=true`
- If template record doesn't exist, create it via SQL insert or admin interface

### F. External API Contract (Integration)

**N/A** - This feature does not integrate with external APIs.

### G. Query Specification (Reporting)

**N/A** - This feature does not involve custom reporting queries beyond standard contract history.

### Interface Mapping (Frontend ↔ Backend)

**Important:** This project uses **snake_case** consistently across frontend and backend to match API responses. Do NOT use camelCase in frontend TypeScript.

#### Cotización Data Mapping

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| numero_cotizacion | numero_cotizacion | string | Quote number |
| fecha_cotizacion | fecha_cotizacion | string (optional) | ISO date |
| fecha_contrato_credito | fecha_contrato_credito | string (optional) | ISO date |
| representante_legal | representante_legal | string (optional) | Legal rep name |
| tipo_id_representante | tipo_id_representante | string (optional) | ID type (C.C., C.E.) |
| numero_id_representante | numero_id_representante | string (optional) | ID number |
| anexo_items | anexo_items | AnexoItem[] | Array of creditor items |
| monto_total | monto_total | number (Decimal) | Total amount |

#### Bank Certificate Data Mapping

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| razon_social | razon_social | string | Company name |
| nit | nit | string | Tax ID |
| banco | banco | string | Bank name |
| tipo_cuenta | tipo_cuenta | 'Ahorros' \| 'Corriente' \| 'PCE' | Account type |
| numero_cuenta | numero_cuenta | string | Account number |

#### Acreedor (Creditor) Data Mapping

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| razon_social | razon_social | string | Company name |
| nit | nit | string (optional) | Tax ID (optional for DIAN) |
| banco | banco | string | Bank name |
| tipo_cuenta | tipo_cuenta | 'Ahorros' \| 'Corriente' \| 'PCE' | Account type |
| numero_cuenta | numero_cuenta | string | Account number |

#### Instruccion de Mandato Request Mapping

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| client_nit | client_nit | string | Client tax ID |
| numero_cotizacion_desembolso | numero_cotizacion_desembolso | string | Quote number |
| fecha_contrato_mandato | fecha_contrato_mandato | string | ISO date format |
| monto | monto | number | Amount (will be Decimal on backend) |
| acreedores | acreedores | AcreedorGastosNacionales[] | Array of creditors (max 3) |

## Implementation Plan

### Phase 1: Foundation (Backend DTOs and Constants)

**Goal:** Define data structures and constants needed for the feature.

1. **Add DTOs to `legal_dtos.py`:**
   - `BankCertificateData` - parsed bank certificate fields
   - `AcreedorGastosNacionales` - creditor information for mandate
   - `InstruccionMandatoRequest` - API request for document generation

2. **Create `constants.py`:**
   - `DIAN_CREDITOR_INFO` dict with static values
   - `DIAN_KEYWORDS` list for detecting DIAN creditors

3. **Create Bank Certificate Parser Service:**
   - `BankCertificateParserService` class in `bank_certificate_parser_service.py`
   - Implement Bancolombia parsing with regex patterns
   - Implement BBVA parsing (bonus)
   - Auto-detect bank and route to appropriate parser

4. **Add Unit Tests:**
   - `test_bank_certificate_parser_service.py`
   - Test valid certificate parsing
   - Test invalid PDF handling
   - Test missing field scenarios

### Phase 2: Core Implementation (Document Generation and API)

**Goal:** Implement document generation logic and expose API endpoints.

1. **Extend Document Service:**
   - Add routing case for `pl_co_mandato_im` in `generate_contract_document()`
   - Implement `generate_instruccion_mandato_document()` method
   - Implement `_prepare_instruccion_mandato_replacements()` helper
   - Implement `_populate_acreedores_table()` helper to fill nested table

2. **Add API Endpoints (in `legal_routes.py` or `operations_routes.py`):**
   - `POST /api/legal/contracts/instruccion-mandato/parse-cotizacion` - Parse Cotización PDF
   - `POST /api/legal/contracts/instruccion-mandato/parse-bank-certificate` - Parse Bank Certificate PDF
   - `POST /api/legal/contracts/instruccion-mandato/generate` - Generate document
   - All endpoints require `admin`, `legal`, or `operations` role

3. **Add Integration Tests:**
   - Test Cotización parsing endpoint
   - Test Bank Certificate parsing endpoint
   - Test document generation endpoint
   - Test error handling (invalid PDFs, missing fields)

### Phase 3: Frontend Integration

**Goal:** Build user interface for PDF upload and document generation.

1. **Add TypeScript Types:**
   - Add types to `frontend/src/types/legal.ts`: `BankCertificateData`, `AcreedorGastosNacionales`, `InstruccionMandatoRequest`, `InstruccionMandatoFormData`

2. **Add Service Methods:**
   - Add methods to `frontend/src/services/legalService.ts` or `operationsService.ts`
   - `parseCotizacionForMandato()`, `parseBankCertificate()`, `generateInstruccionMandato()`

3. **Create UI Components:**
   - `FKAcreedorCard.tsx` - Display/edit single creditor information
   - `FKInstruccionMandatoForm.tsx` - Main multi-step form component
   - `InstruccionMandatoPage.tsx` - Page wrapper component

4. **Add Routing:**
   - Add route to `App.tsx` with `RoleProtectedRoute`
   - Add navigation link to Paga Local menu (if not already present)

5. **Create E2E Test:**
   - Create `.claude/commands/e2e/test_instruccion_mandato_generation.md`
   - Test complete workflow: login → upload Cotización → upload Bank Cert → generate document

## Step by Step Tasks

### Task 1: Add Backend DTOs and Enums

**Files:** `backend/src/interface/legal_dtos.py`

- Read the existing `legal_dtos.py` file to understand the structure
- Add `BankCertificateData` DTO with fields: `numero_certificado`, `banco`, `fecha_emision`, `razon_social`, `nit`, `tipo_cuenta`, `numero_cuenta`
- Add `AcreedorGastosNacionales` DTO with fields: `razon_social`, `nit` (optional), `banco`, `tipo_cuenta`, `numero_cuenta`
- Add validators to ensure required fields are not empty
- Add `InstruccionMandatoRequest` DTO with fields: `client_nit`, `numero_cotizacion_desembolso`, `fecha_contrato_mandato`, `monto`, `acreedores` (list, min 1, max 3)
- Run backend linting: `cd backend && ruff check src/interface/legal_dtos.py`

### Task 2: Create Constants File for DIAN Values

**Files:** `backend/src/core/servicios/constants.py` (new file)

- Create new file `backend/src/core/servicios/constants.py`
- Define `DIAN_CREDITOR_INFO` dict with keys: `razon_social`, `nit`, `banco`, `tipo_cuenta`, `numero_cuenta`
- Define `DIAN_KEYWORDS` list with lowercase keywords: `['dian', 'entidad de pago de impuestos', 'tributo', 'aduanero', 'impuesto']`
- Add docstrings explaining these constants are for DIAN detection
- Run backend linting: `cd backend && ruff check src/core/servicios/constants.py`

### Task 3: Create Bank Certificate Parser Service

**Files:** `backend/src/core/servicios/bank_certificate_parser_service.py` (new file)

- Create new file following the pattern from `cotizacion_parser_service.py`
- Implement `BankCertificateParserService` class with methods:
  - `parse_bank_certificate(pdf_bytes: bytes) -> BankCertificateData` - main entry point
  - `_extract_razon_social(text: str) -> str` - extract company name using regex `r'informar que\s+(.+?)\s+identificado'`
  - `_extract_nit(text: str) -> str` - extract NIT using regex `r'NIT\s+(\d+)'`
  - `_extract_banco(text: str) -> str` - extract bank name from header (look for "BANCOLOMBIA", "BBVA")
  - `_extract_tipo_cuenta(text: str) -> str` - extract account type using regex `r'(CUENTA DE AHORROS|CUENTA CORRIENTE)'`
  - `_extract_numero_cuenta(text: str) -> str` - extract account number using regex `r'\b(\d{10,})\b'`
- Use PyMuPDF (`fitz`) for PDF reading
- Add comprehensive logging (debug, info, warning levels)
- Raise `ValueError` with descriptive messages for parsing failures
- Handle missing optional fields gracefully
- Run backend linting: `cd backend && ruff check src/core/servicios/bank_certificate_parser_service.py`

### Task 4: Add Unit Tests for Bank Certificate Parser

**Files:** `backend/tests/test_bank_certificate_parser_service.py` (new file)

- Create pytest test file
- Add test fixtures for sample PDF content
- Add test cases:
  - `test_parse_valid_bancolombia_certificate()` - valid Bancolombia PDF
  - `test_parse_invalid_pdf_raises_error()` - invalid PDF content
  - `test_parse_missing_critical_field_raises_error()` - PDF missing NIT
  - `test_parse_with_optional_fields_missing()` - optional fields handle gracefully
- Run tests: `cd backend && python -m pytest tests/test_bank_certificate_parser_service.py -v`

### Task 5: Extend Document Service for Instruccion de Mandato

**Files:** `backend/src/core/servicios/document_service.py`

- Read the existing `document_service.py` file (lines 68-90 for routing logic)
- In `generate_contract_document()`, add routing case:
  ```python
  elif contract_type == 'pl_co_mandato_im':
      return self.generate_instruccion_mandato_document(contract_data)
  ```
- Implement `generate_instruccion_mandato_document(contract_data: Dict[str, Any], template_name: str = "FK COL - Fin. COP - Mandato (IM).docx") -> bytes`:
  - Load template from `self.template_dir / template_name`
  - Call `_prepare_instruccion_mandato_replacements(contract_data)` to get replacement dict
  - Replace placeholders in paragraphs using `_replace_in_paragraph()` (existing method)
  - Replace placeholders in table cells
  - Call `_populate_acreedores_table(doc, acreedores)` to fill nested table
  - Save document to temp file, read bytes, delete temp file, return bytes
- Implement `_prepare_instruccion_mandato_replacements(data: Dict[str, Any]) -> Dict[str, str]`:
  - Extract data_snapshot from `data.get('data_snapshot', {})`
  - Parse `fecha_contrato_mandato` to get day, month, year components
  - Convert monto to Spanish words using `_number_to_words_spanish()` (existing method at line 755+)
  - Return dict mapping placeholders to values (see Placeholder Inventory section)
- Implement `_populate_acreedores_table(doc: Document, acreedores: list) -> None`:
  - Navigate to nested table: `doc.tables[0].rows[3].cells[0].tables[0]`
  - Iterate over acreedores (max 3)
  - Fill each row (rows 1-3) with creditor data (row 0 is header)
  - Replace `[...]` placeholders in each cell
- Run backend linting: `cd backend && ruff check src/core/servicios/document_service.py`

### Task 6: Add API Endpoints for Instruccion de Mandato

**Files:** `backend/src/adapter/rest/legal_routes.py` or `operations_routes.py`

- Decide which router to use (legal or operations) - recommend `operations_routes.py` since it's disbursement-related
- Import new DTOs and services
- Add endpoint `POST /contracts/instruccion-mandato/parse-cotizacion`:
  - Accept `UploadFile` parameter
  - Validate file type (PDF only) and size (max 5MB)
  - Use existing `CotizacionParserService` to parse
  - Return `CotizacionData` DTO
  - Require roles: `['admin', 'legal', 'operations']`
- Add endpoint `POST /contracts/instruccion-mandato/parse-bank-certificate`:
  - Accept `UploadFile` parameter
  - Validate file type (PDF only) and size (max 5MB)
  - Use new `BankCertificateParserService` to parse
  - Return `BankCertificateData` DTO
  - Require roles: `['admin', 'legal', 'operations']`
- Add endpoint `POST /contracts/instruccion-mandato/generate`:
  - Accept `InstruccionMandatoRequest` body
  - Validate client exists using `client_repository.get_by_nit()`
  - Call `ContractService.generate_contract()` with contract type `pl_co_mandato_im`
  - Return `ContractGenerationResponse` DTO
  - Require roles: `['admin', 'legal', 'operations']`
- Run backend linting: `cd backend && ruff check src/adapter/rest/`

### Task 7: Add Backend Integration Tests

**Files:** `backend/tests/` (existing test files or new files)

- Add integration tests for Instruccion de Mandato endpoints:
  - Test parse-cotizacion endpoint with valid PDF
  - Test parse-bank-certificate endpoint with valid PDF
  - Test generate endpoint with valid request
  - Test error handling (invalid PDFs, missing client, validation errors)
- Run tests: `cd backend && python -m pytest tests/ -v -k instruccion_mandato`

### Task 8: Add Frontend TypeScript Types

**Files:** `frontend/src/types/legal.ts`

- Read existing `legal.ts` file to understand structure
- Add `BankCertificateData` interface matching backend DTO
- Add `AcreedorGastosNacionales` interface matching backend DTO
- Add `InstruccionMandatoRequest` interface matching backend DTO
- Add `InstruccionMandatoFormData` interface for form state (includes `cotizacionFile`, `bankCertificateFiles`, `isDianOnly`, `manualAcreedores`)
- Verify contract type union already includes `'pl_co_mandato_im'` (line 123)
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`

### Task 9: Add Frontend Service Methods

**Files:** `frontend/src/services/legalService.ts` or `operationsService.ts`

- Decide which service to use (recommend `operationsService.ts` for consistency with Solicitud de Desembolso)
- Add method `parseCotizacionForMandato(file: File): Promise<CotizacionData>`:
  - Create FormData, append file
  - POST to `/operations/contracts/instruccion-mandato/parse-cotizacion`
  - Return parsed data
- Add method `parseBankCertificate(file: File): Promise<BankCertificateData>`:
  - Create FormData, append file
  - POST to `/operations/contracts/instruccion-mandato/parse-bank-certificate`
  - Return parsed data
- Add method `generateInstruccionMandato(request: InstruccionMandatoRequest): Promise<ContractGenerationResponse>`:
  - POST to `/operations/contracts/instruccion-mandato/generate`
  - Return contract generation response
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`

### Task 10: Create FKAcreedorCard Component

**Files:** `frontend/src/components/ui/FKAcreedorCard.tsx` (new file)

- Create functional component that accepts props: `acreedor: AcreedorGastosNacionales`, `onEdit?: (acreedor: AcreedorGastosNacionales) => void`, `onRemove?: () => void`, `readOnly?: boolean`
- Display creditor information in MUI Card:
  - Razon Social (TextField if editable, Typography if read-only)
  - NIT (TextField if editable, Typography if read-only)
  - Banco (TextField if editable, Typography if read-only)
  - Tipo de Cuenta (Select if editable with options: Ahorros, Corriente, PCE)
  - Numero de Cuenta (TextField if editable, Typography if read-only)
- Show Edit and Remove buttons if not read-only
- Use Finkargo color palette and styling
- Export component as `export const FKAcreedorCard`
- Run linting: `cd frontend && npm run lint`

### Task 11: Create FKInstruccionMandatoForm Component

**Files:** `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` (new file)

- Create functional component following pattern from `FKSolicitudDesembolsoRequest.tsx`
- Implement multi-section form with state management:
  - Section 1: Client Search (search by NIT, display client info)
  - Section 2: Upload Cotización PDF (file upload, parse button, display extracted data)
  - Section 3: Creditor Information (DIAN detection, Bank Certificate upload for non-DIAN, manual entry fallback)
  - Section 4: Review & Generate (display all data, generate button)
- Use `useState` hooks for:
  - `selectedClient` - Client | null
  - `cotizacionFile` - File | null
  - `cotizacionData` - CotizacionData | null
  - `acreedores` - AcreedorGastosNacionales[] (max 3)
  - `bankCertFiles` - File[] (for multiple uploads)
  - `error` - string | null
  - `requesting` - boolean
  - `extracting` - boolean
- Implement handlers:
  - `handleClientSearch()` - search client by NIT
  - `handleCotizacionUpload()` - upload and parse Cotización PDF
  - `handleBankCertUpload()` - upload and parse Bank Certificate PDF
  - `handleAddAcreedor()` - add creditor to list (max 3)
  - `handleRemoveAcreedor(index)` - remove creditor from list
  - `handleGenerate()` - validate form and call generation API
- Use MUI components: Card, TextField, Button, Alert, CircularProgress
- Export component as `export const FKInstruccionMandatoForm`
- Run linting: `cd frontend && npm run lint`

### Task 12: Create InstruccionMandatoPage Component

**Files:** `frontend/src/pages/legal/InstruccionMandatoPage.tsx` (new file)

- Create functional component that renders `FKInstruccionMandatoForm`
- Wrap form in `FKMainLayout` (existing layout component)
- Add page title: "Instrucción de Mandato - Paga Local Colombia"
- Handle navigation after successful generation (redirect to contract history or review queue)
- Export component as `export default InstruccionMandatoPage`
- Run linting: `cd frontend && npm run lint`

### Task 13: Add Frontend Routing

**Files:** `frontend/src/App.tsx`

- Read existing `App.tsx` to find Paga Local routes section
- Add route for Instruccion de Mandato:
  ```tsx
  <Route path="/legal/instruccion-mandato" element={
    <RoleProtectedRoute allowedRoles={['admin', 'legal', 'operations']}>
      <InstruccionMandatoPage />
    </RoleProtectedRoute>
  } />
  ```
- Add import for `InstruccionMandatoPage` component
- Verify route is accessible at `http://localhost:5173/legal/instruccion-mandato`
- Run linting: `cd frontend && npm run lint`

### Task 14: Create E2E Test File

**Files:** `.claude/commands/e2e/test_instruccion_mandato_generation.md` (new file)

- Create E2E test file following pattern from `test_solicitud_desembolso_pdf_upload.md`
- Define User Story: "As an operations/legal user, I want to upload Cotización and Bank Certificate PDFs to generate Instruccion de Mandato documents"
- Define Prerequisites: logged in as operations/legal user, test PDFs available
- Define Test Steps:
  1. Login as operations user
  2. Navigate to Instruccion de Mandato page (`/legal/instruccion-mandato`)
  3. Search for client by NIT
  4. Upload Cotización PDF (`Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`)
  5. Verify extracted data displayed (numero_cotizacion, fecha_contrato, monto_total)
  6. Upload Bank Certificate PDF (`Example FIles for Reqs/certificado bancario.pdf`)
  7. Verify extracted creditor information displayed
  8. Review all data and click Generate button
  9. Verify document generation succeeds (contract ID shown, download link available)
  10. Take screenshots at each step
- Define Success Criteria: All steps complete without errors, document generated successfully
- Define Screenshot locations using pattern: `agents/<adw_id>/test_e2e/img/instruccion_mandato/*.png`

### Task 15: Run E2E Test to Validate Feature

**Instructions:** Execute the E2E test to validate the complete workflow

- Read `.claude/commands/test_e2e.md` to understand test execution
- Read `.claude/commands/e2e/test_instruccion_mandato_generation.md` (created in Task 14)
- Execute the E2E test following the test runner instructions
- Ensure backend and frontend servers are running (`scripts/start-dev.sh`)
- Capture screenshots at each step
- Verify all success criteria are met
- If test fails, document failures and fix issues before proceeding

### Task 16: Run Validation Commands

**Instructions:** Run all validation commands to ensure zero regressions

- Run backend tests: `cd backend && python -m pytest`
- Run backend linting: `cd backend && ruff check src/`
- Run frontend linting: `cd frontend && npm run lint`
- Run TypeScript type check: `cd frontend && npx tsc --noEmit`
- Run frontend build: `cd frontend && npm run build`
- Verify all commands execute without errors
- If any errors occur, fix them before marking feature complete

## Testing Strategy

### Unit Tests

**Backend:**
- `test_bank_certificate_parser_service.py` - Test bank certificate parsing with various formats and edge cases
- Test extraction methods individually (`_extract_razon_social`, `_extract_nit`, etc.)
- Test invalid PDF handling (corrupted files, wrong format, empty files)
- Test missing required fields (should raise ValueError)
- Test optional fields handling (should not raise error if missing)

**Frontend:**
- No unit tests currently configured (mention in Notes for future consideration)

### Integration Tests

**Backend:**
- Test API endpoint `/contracts/instruccion-mandato/parse-cotizacion` with valid and invalid PDFs
- Test API endpoint `/contracts/instruccion-mandato/parse-bank-certificate` with valid and invalid PDFs
- Test API endpoint `/contracts/instruccion-mandato/generate` with valid and invalid requests
- Test document generation with 1, 2, and 3 creditors
- Test error responses (404 for client not found, 422 for parsing errors, 400 for validation errors)

### E2E Tests

**Browser Automation (Playwright):**
- Complete user workflow from login to document download
- PDF upload and parsing
- Form validation and error handling
- Multi-creditor scenarios
- DIAN detection (future enhancement)

### Edge Cases

1. **Invalid PDFs:**
   - Corrupted PDF files → Should return 422 error with descriptive message
   - Non-PDF files (images, Word docs) → Should return 400 error "Invalid file type"
   - Empty PDFs → Should return 422 error "PDF has no pages"

2. **Missing Data:**
   - Cotización PDF missing numero_cotizacion → Should return 422 error
   - Bank Certificate missing NIT → Should return 422 error
   - Client NIT not found in database → Should return 404 error

3. **Multiple Creditors:**
   - 0 creditors → Should return 400 validation error "min_items=1"
   - 4+ creditors → Should return 400 validation error "max_items=3"
   - Mix of DIAN and non-DIAN creditors → Should handle both types

4. **Date Parsing:**
   - Invalid fecha_contrato_mandato format → Should return 400 validation error
   - Date parsing from Spanish text ("6 de noviembre de 2025") → Should handle all months

5. **Amount Conversion:**
   - Monto = 0 → Should return 400 validation error "gt=0"
   - Very large amounts (billions) → Should convert to Spanish words correctly
   - Decimal amounts → Should handle properly (e.g., 739860.50)

6. **Template Handling:**
   - Template file not found → Should return 500 error with helpful message
   - Template placeholders mismatch → Should log warnings but continue
   - Nested table structure changed → Should raise error or handle gracefully

## Acceptance Criteria

### Backend

- [ ] `BankCertificateParserService` correctly extracts all fields from Bancolombia certificates
- [ ] `BankCertificateParserService` handles BBVA certificates (bonus feature)
- [ ] `generate_instruccion_mandato_document()` fills all main document placeholders correctly
- [ ] Nested creditor table populated with 1-3 creditors (dynamic rows)
- [ ] Amount displayed in both numbers (formatted with commas) and words (Spanish)
- [ ] Date components parsed correctly (day, month name, year) from fecha_contrato_credito
- [ ] API endpoints return proper error messages (400 for validation, 422 for parsing, 404 for not found)
- [ ] All backend unit tests pass (`pytest`)
- [ ] Backend linting passes (`ruff check src/`)

### Frontend

- [ ] Form successfully parses and displays Cotización data after upload
- [ ] Bank Certificate upload and parsing works without errors
- [ ] Multiple creditors can be added/removed (max 3 enforced)
- [ ] Form validation prevents submission with missing required fields
- [ ] Error messages display clearly for parsing failures or validation errors
- [ ] Generated document downloads correctly with proper filename
- [ ] All frontend linting passes (`npm run lint`)
- [ ] TypeScript type check passes (`npx tsc --noEmit`)
- [ ] Frontend build succeeds (`npm run build`)

### Integration

- [ ] End-to-end flow works: Login → Search Client → Upload Cotización → Upload Bank Cert → Generate → Download
- [ ] Generated DOCX document opens in Microsoft Word without errors
- [ ] Generated document matches expected format from template (manual inspection)
- [ ] All placeholders replaced (no `[...]` or `[PLACEHOLDER]` text remaining)
- [ ] Creditor table populated correctly (right number of rows, correct data in each cell)
- [ ] Amount in letters matches amount in numbers
- [ ] Date components match fecha_contrato_mandato input
- [ ] Client information (representante_legal, cedula) pulled from database correctly
- [ ] E2E test passes with all screenshots captured

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions:

1. **Run Backend Tests:**
   ```bash
   cd backend && python -m pytest
   ```
   Expected: All tests pass, including new `test_bank_certificate_parser_service.py` tests

2. **Run Backend Linting:**
   ```bash
   cd backend && ruff check src/
   ```
   Expected: No linting errors in new or modified files

3. **Run Frontend Linting:**
   ```bash
   cd frontend && npm run lint
   ```
   Expected: No linting errors in new or modified files

4. **Run TypeScript Type Check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```
   Expected: No type errors, all new types properly defined

5. **Run Frontend Build:**
   ```bash
   cd frontend && npm run build
   ```
   Expected: Build succeeds, no compilation errors, output in `dist/`

6. **Run E2E Test:**
   - Read `.claude/commands/test_e2e.md`
   - Read and execute `.claude/commands/e2e/test_instruccion_mandato_generation.md`
   - Expected: Test passes with status "passed", all screenshots captured, no errors

7. **Manual Document Verification:**
   - Generate a test Instruccion de Mandato document
   - Download and open in Microsoft Word
   - Verify all placeholders replaced
   - Verify creditor table populated correctly
   - Verify amounts match (numbers and letters)
   - Verify dates match fecha_contrato_mandato
   - Expected: Document looks professional, all data correct, no errors

## Notes

### Dependencies

**Backend (already in requirements.txt):**
- PyMuPDF (fitz) - PDF parsing
- python-docx - Word document manipulation
- FastAPI - API endpoints
- Pydantic - Data validation

**Frontend (already in package.json):**
- React 19.1.1
- Material-UI 7.3.4
- Axios 1.12.2
- react-hook-form 7.64.0

**No new dependencies required.**

### Future Enhancements

1. **DIAN Implementation (`pl_co_dian_mandato_im`):**
   - Create separate template for DIAN payments
   - Auto-populate DIAN static values from constants
   - Different UI flow (no Bank Certificate upload needed)
   - Estimated effort: 3-4 hours

2. **Multi-Bank Support:**
   - Add parsers for additional Colombian banks (Davivienda, Banco de Bogotá, etc.)
   - Create bank detection strategy based on logos/headers
   - Estimated effort: 2-3 hours per bank

3. **Batch Generation:**
   - Support generating multiple Instruccion de Mandato documents at once
   - ZIP file download with all documents
   - Estimated effort: 4-5 hours

4. **OCR Support:**
   - Handle scanned Bank Certificates (image-based PDFs)
   - Use Tesseract OCR or cloud OCR service
   - Estimated effort: 6-8 hours

### Known Limitations

1. **Bank Certificate Format Dependency:**
   - Parser is tuned for Bancolombia format
   - BBVA support is bonus feature (may require additional samples)
   - Other banks will require new parser implementations

2. **Text-Based PDFs Only:**
   - Current implementation does not support OCR for scanned documents
   - Bank Certificates must be native PDFs with extractable text

3. **Spanish Language Only:**
   - Amount-to-words conversion only supports Spanish
   - Date formatting only supports Spanish month names
   - No internationalization for other languages

4. **Template Structure Dependency:**
   - Nested table navigation assumes specific structure (Table 0 → Row 3 → Cell 0 → Nested Table)
   - If template structure changes, code must be updated

### Testing Accounts

**Operations Role:**
- Email: test-operations@finkargo.com
- Password: [configured in Supabase Auth]

**Legal Role:**
- Email: test-legal@finkargo.com
- Password: [configured in Supabase Auth]

**Admin Role:**
- Email: test-admin@finkargo.com
- Password: [configured in Supabase Auth]

### Reference Files

- **Template:** `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- **Data Sources Doc:** `docs/20251207_INSTRUCCION_MANDATO_DATA_SOURCES.md`
- **Transcript:** `docs/20251207A TRANSCRIPT INSTRUCCION DE MANDATO.txt`
- **Example Cotización:** `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
- **Example Bank Certificate:** `Example FIles for Reqs/certificado bancario.pdf`
- **Existing Parser Pattern:** `backend/src/core/servicios/cotizacion_parser_service.py`
- **Existing Document Service:** `backend/src/core/servicios/document_service.py`

### Architecture Notes

This feature follows Clean Architecture principles:
- **Adapter Layer** (`legal_routes.py` or `operations_routes.py`): HTTP endpoints, request/response handling
- **Core Layer** (`document_service.py`, `bank_certificate_parser_service.py`): Business logic, document generation, PDF parsing
- **Repository Layer** (existing repositories): Database access for clients, contracts
- **Interface Layer** (`legal_dtos.py`): Data Transfer Objects, validation

### Frontend State Management

- **Global State:** AuthContext (existing) for user authentication
- **Local State:** `useState` hooks in `FKInstruccionMandatoForm` for form data
- **No Redux:** Project uses Context API for global state, not Redux
- **No Global State Needed:** This feature is self-contained, no shared state beyond auth

### Error Handling Strategy

**Backend:**
- `ValueError` → 422 Unprocessable Entity (parsing errors)
- `ValidationError` (Pydantic) → 400 Bad Request (validation errors)
- `HTTPException(404)` → 404 Not Found (client not found)
- `Exception` → 500 Internal Server Error (unexpected errors)

**Frontend:**
- Catch errors from API calls and display user-friendly messages
- Use MUI `Alert` component for error display
- Log errors to console for debugging
- Provide retry mechanisms for transient failures

## Plan Quality Checklist

### General Completeness (ALL features)

- [x] Feature category identified in Pre-Implementation Verification (Document Generation + Data Import/Export)
- [x] All new files listed in "New Files" section (7 new files documented)
- [x] All database migrations identified and tasks created (No migrations needed - existing schema supports this)
- [x] E2E test file task included (Task 14 creates E2E test file)
- [x] All external dependencies listed in Notes (No new dependencies required)

### Category-Specific Completeness

**Document Generation:**
- [x] ALL template placeholders extracted and documented (9 main placeholders + 5 nested table columns per creditor)
- [x] Placeholder mapping table complete with data sources (See section A)
- [x] Database records verified (Contract type enum exists, template file exists, no new records needed)

**Data Import/Export:**
- [x] File format specifications documented (Cotización PDF and Bank Certificate PDF formats documented)
- [x] Field mapping table complete (See Interface Mapping section)
- [x] Error handling strategy defined (See Error Handling Strategy in Notes)

### Consistency (ALL features)

- [x] Data types match between frontend and backend (All use snake_case, types mapped in Interface Mapping section)
- [x] Field naming conventions use snake_case consistently (Explicit note in Interface Mapping section)
- [x] Access patterns (dict vs object) verified for repository methods (All repositories return dict - documented in section D)
- [x] Country-specific variations handled (Colombia-specific, COP currency, Spanish language - documented in section E)

### Testing

- [x] Validation commands test all new functionality (7 validation commands including E2E test)
- [x] Edge cases documented in Testing Strategy (6 edge case categories with 20+ specific scenarios)
- [x] E2E test covers happy path with screenshots (E2E test file creation in Task 14, execution in Task 15)
