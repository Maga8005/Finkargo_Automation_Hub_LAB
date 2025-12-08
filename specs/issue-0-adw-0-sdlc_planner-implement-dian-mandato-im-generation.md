# Feature: DIAN Mandato (IM) Contract Generation

## Feature Description

Implement the DIAN Mandato (IM) contract generation feature for the Paga Local Colombia workflow. This feature enables operations users to generate "Template DIAN - Mandato (IM)" documents for DIAN (Dirección de Impuestos y Aduanas Nacionales) payments. Unlike the regular Mandato (IM) which requires Bank Certificate PDFs for each creditor, the DIAN Mandato uses only the Cotización PDF plus client data from the database. No creditor bank information is needed since DIAN payments use static government payment information.

The DIAN Mandato (IM) is a simplified version of the regular Mandato (IM) that:
- Uses a different template: `FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx`
- Requires only Cotización PDF upload (no Bank Certificate PDFs)
- Uses client data from the database (no additional creditor bank info needed)
- Generates documents with contract ID prefix `PLDI` (Paga Local DIAN)

## User Story

As an **operations team member**
I want to generate DIAN Mandato (IM) documents by uploading a Cotización PDF
So that I can quickly authorize Finkargo to make payments to DIAN on behalf of clients without the need to collect bank certificates for tax authority payments

## Problem Statement

Currently, the Finkargo Automation Hub has a placeholder tab for "Template DIAN - Mandato (IM)" in the Paga Local Colombia section, but it displays a generic contract request form that doesn't work. Users need a specialized form similar to the regular Mandato (IM) that:

1. Extracts data from Cotización PDFs (quote number, date, amount)
2. Uses client information from the database
3. Does NOT require Bank Certificate PDFs (DIAN uses static payment info)
4. Generates documents using the DIAN-specific template

The existing regular Mandato (IM) workflow is too complex for DIAN payments because it requires uploading Bank Certificate PDFs that don't apply to government tax payments.

## Solution Statement

Implement a simplified DIAN Mandato (IM) generation workflow:

1. **Create a new frontend form component** (`FKDIANMandatoForm.tsx`) that:
   - Allows client search by NIT
   - Accepts Cotización PDF upload and extraction
   - Shows extracted data (quote number, date, amount) for review
   - Does NOT show Bank Certificate upload sections
   - Generates the document with one click

2. **Add backend API endpoint** for DIAN Mandato generation that:
   - Reuses the existing Cotización parser
   - Uses the DIAN-specific template
   - Populates placeholders from client data + Cotización data

3. **Extend document service** to handle `pl_co_dian_mandato_im` contract type

4. **Create database migration** to add template record for the DIAN Mandato template

## Access Control

- **Required Role(s):** `admin`, `operations`
- **Backend Protection:** Use `require_operations_role` from `rbac_dependencies.py`
- **Frontend Protection:** Already protected by `RoleProtectedRoute` on the Paga Local Colombia page

## Relevant Files

Use these files to implement the feature:

**Backend - API Routes:**
- `backend/src/adapter/rest/operations_routes.py` (lines 506-747) - Existing Mandato IM endpoints to reference; add new DIAN endpoint
- `backend/src/adapter/rest/rbac_dependencies.py` - RBAC dependency for role protection

**Backend - Business Logic:**
- `backend/src/core/servicios/document_service.py` (lines 932-1182) - Existing `generate_instruccion_mandato_document()` to create similar method for DIAN
- `backend/src/core/servicios/cotizacion_parser_service.py` - Reuse for parsing Cotización PDFs
- `backend/src/core/servicios/contract_service.py` - Main contract generation orchestration

**Backend - DTOs:**
- `backend/src/interface/legal_dtos.py` (lines 378-465) - Existing DTOs, need to add `DIANMandatoRequest`

**Backend - Repository:**
- `backend/src/repositorio/contract_repository.py` - Contract CRUD operations
- `backend/src/repositorio/template_repository.py` - Template lookup

**Backend - Template:**
- `backend/templates/FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx` - The DIAN template file

**Frontend - Services:**
- `frontend/src/services/operationsService.ts` - Add new service methods for DIAN Mandato

**Frontend - Types:**
- `frontend/src/types/legal.ts` - Add `DIANMandatoRequest` interface

**Frontend - Components:**
- `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx` (lines 131-141) - Parent component with DIAN tab
- `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` - Reference for building simplified DIAN form

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_instruccion_mandato_form.md` - Reference for creating DIAN Mandato E2E test

### New Files

| File Path | Purpose |
|-----------|---------|
| `frontend/src/components/forms/FKDIANMandatoForm.tsx` | Simplified form for DIAN Mandato (IM) - no bank cert upload |
| `backend/database/migration_add_dian_mandato_im_template.sql` | SQL migration to add template record to `contract_templates` table |
| `.claude/commands/e2e/test_dian_mandato_im_form.md` | E2E test for DIAN Mandato (IM) workflow |

## Pre-Implementation Verification

### Feature Category
- [x] **Document Generation** (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → N/A
- [ ] Data Import/Export (CSV, ZIP) → N/A
- [ ] API Integration (external services) → N/A
- [ ] Reporting (queries, history) → N/A
- [ ] CRUD Operations (basic data management) → N/A

### A. Template Placeholder Inventory (Document Generation)

**Template file:** `backend/templates/FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx`

Extracted placeholders (9 total):

| Placeholder | Data Source | Format | Notes |
|-------------|-------------|--------|-------|
| `[Fecha actual]` | System `datetime.utcnow()` | "DD de MONTH de YYYY" | Spanish month name (e.g., "7 de diciembre de 2025") |
| `[Número de cotización de desembolso]` | Cotización PDF `numero_cotizacion` | String | Format: CO:900436389:1:2:DOM |
| `[día de firma contrato mandato]` | Cotización PDF `fecha_contrato_credito` | Integer | Day number (e.g., "6") |
| `[mes de firma contrato mandato]` | Cotización PDF `fecha_contrato_credito` | String | Spanish month name (e.g., "noviembre") |
| `[año de firma contrato mandato]` | Cotización PDF `fecha_contrato_credito` | Integer | 4-digit year (e.g., "2025") |
| `[monto a transferir en letras]` | Cotización PDF `monto_total` | String | Spanish words uppercase (e.g., "SETECIENTOS TREINTA Y NUEVE MIL PESOS") |
| `[monto a transferir en números]` | Cotización PDF `monto_total` | String | Formatted currency (e.g., "$739,860") |
| `[Nombre del representante legal del Cliente]` | Database `clients.representante_legal` | String | Full name |
| `[número ID representante legal]` | Database `clients.cedula_representante` | String | ID number |

**Key difference from regular Mandato (IM):** No nested creditor table placeholders (`[•]`, `[Ahorros | Corriente]`). The DIAN template is simpler.

### B. Excel Column Mapping (Excel Processing only)
N/A - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)
**Cotización PDF Input:**

| Format | Max Size | Required Content | Validation Rules |
|--------|----------|------------------|------------------|
| PDF | 5MB | Numero de cotizacion, Fecha contrato credito, Monto total | Must be valid PDF with extractable text |

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `client_repo.get_by_nit(nit)` | dict | `data['nit']`, `data['representante_legal']` | Use bracket notation |
| `contract_repo.create_contract(...)` | dict | `data['id']`, `data['contract_id']` | Use bracket notation |
| `template_repo.get_active_template(contract_type)` | dict | `data['id']`, `data['template_content']` | Use bracket notation |

### E. Database Dependencies Checklist (Document/CRUD)
- [x] **Contract type enum exists** in `legal_dtos.py`: `PL_CO_DIAN_MANDATO_IM = "pl_co_dian_mandato_im"` (line 32)
- [x] **Template file exists** in `backend/templates/`: `FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx`
- [x] **Contract ID prefix exists** in `generate_contract_id()`: `PLDI` (migration already applied)
- [ ] **Database template record**: NEEDS MIGRATION - no record in `contract_templates` for `pl_co_dian_mandato_im`
- [x] **Country-specific handling:** Colombia-specific (CO), uses COP currency and Spanish text

### F. External API Contract (Integration only)
N/A - No external API integration.

### G. Query Specification (Reporting only)
N/A - No reporting queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `client_nit` | `client_nit` | string | Client tax ID |
| `numero_cotizacion_desembolso` | `numero_cotizacion_desembolso` | string | Quote number from Cotización PDF |
| `fecha_contrato_mandato` | `fecha_contrato_mandato` | string | ISO date format (YYYY-MM-DD) |
| `monto` | `monto` | number | Total amount from Cotización PDF |

**Note:** Unlike regular `InstruccionMandatoRequest`, DIAN Mandato does NOT have `acreedores` array.

## Implementation Plan

### Phase 1: Foundation (Backend DTOs and Database Migration)
1. Add `DIANMandatoRequest` DTO to `legal_dtos.py`
2. Create database migration to add template record
3. Verify template file exists and is readable

### Phase 2: Core Implementation (Backend Document Generation)
1. Add routing case in `document_service.py` for `pl_co_dian_mandato_im`
2. Create `generate_dian_mandato_document()` method (simplified, no creditor table)
3. Add API endpoint `POST /api/operations/contracts/dian-mandato/generate`
4. Add Cotización parse endpoint (can reuse existing or create dedicated)

### Phase 3: Frontend Integration
1. Create `FKDIANMandatoForm.tsx` component (simplified form)
2. Add service methods to `operationsService.ts`
3. Update `FKPagaLocalCODocumentosOperacion.tsx` to use new form for DIAN tab

### Phase 4: Testing and Validation
1. Create E2E test file
2. Run all validation commands
3. Manual testing

## Step by Step Tasks

### Task 1: Add DIANMandatoRequest DTO

**Files:** `backend/src/interface/legal_dtos.py`

1. Read the existing `legal_dtos.py` file (already done in pre-implementation)
2. Add `DIANMandatoRequest` class after line 465:
   ```python
   class DIANMandatoRequest(BaseModel):
       """Request to generate DIAN Mandato (IM) contract - simplified, no creditors"""
       client_nit: str = Field(..., min_length=5, max_length=20, description="Client NIT")
       numero_cotizacion_desembolso: str = Field(..., min_length=1, max_length=100, description="Disbursement quote number")
       fecha_contrato_mandato: str = Field(..., description="Mandate contract date (ISO format)")
       monto: Decimal = Field(..., gt=0, description="Total amount to transfer in COP")

       @validator('client_nit')
       def validate_client_nit(cls, v):
           """Validate NIT is not empty"""
           if not v or not v.strip():
               raise ValueError('client_nit cannot be empty')
           return v.strip()

       @validator('monto')
       def validate_monto(cls, v):
           """Validate that monto is positive"""
           if v <= 0:
               raise ValueError('monto must be greater than 0')
           return v
   ```
3. Run backend linting: `cd backend && ruff check src/interface/legal_dtos.py`

### Task 2: Create Database Migration for Template Record

**Files:** `backend/database/migration_add_dian_mandato_im_template.sql` (new file)

1. Create new migration file with content:
   ```sql
   /*
    * Migration: Add DIAN Mandato (IM) Contract Template
    * Created: 2025-12-07
    * Author: SDLC Agent
    *
    * Purpose:
    * Adds the contract template record for DIAN Mandato (IM) (PLDI) documents
    * in the Paga Local Colombia module.
    *
    * The Word template file already exists at:
    * backend/templates/FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx
    */

   -- Insert template record for DIAN Mandato (IM)
   INSERT INTO contract_templates (
       contract_type,
       version,
       template_content,
       active,
       created_at
   ) VALUES (
       'pl_co_dian_mandato_im',
       '1.0.0',
       'FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx',
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
   WHERE contract_type = 'pl_co_dian_mandato_im';
   ```
2. Document that this migration must be run manually in Supabase SQL Editor

### Task 3: Extend Document Service for DIAN Mandato

**Files:** `backend/src/core/servicios/document_service.py`

1. Add routing case for `pl_co_dian_mandato_im` in `generate_contract_document()` method (around line 103):
   ```python
   elif contract_type == 'pl_co_dian_mandato_im':
       return self.generate_dian_mandato_document(contract_data)
   ```

2. Add `generate_dian_mandato_document()` method after `generate_instruccion_mandato_document()`:
   ```python
   def generate_dian_mandato_document(
       self,
       contract_data: Dict[str, Any],
       template_name: str = "FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx"
   ) -> bytes:
       """
       Generate DIAN Mandato (IM) contract document from template and data

       This is a simplified version of Instruccion de Mandato - no creditor table.
       Uses same placeholders but doesn't have nested creditor table.

       Args:
           contract_data: Dictionary containing contract data with data_snapshot including:
               - Client data (representante_legal, cedula_representante)
               - numero_cotizacion_desembolso
               - fecha_contrato_mandato
               - monto

       Returns:
           bytes: Generated DOCX file content
       """
       template_path = self.template_dir / template_name

       if not template_path.exists():
           raise FileNotFoundError(f"Template not found: {template_path}")

       logger.info(f"Loading DIAN Mandato (IM) template from: {template_path}")

       # Load template
       doc = Document(str(template_path))

       # Extract data from data_snapshot
       data = contract_data.get('data_snapshot', contract_data)
       logger.debug(f"Data snapshot keys: {list(data.keys())}")

       # Reuse the same replacements function as regular Mandato (IM)
       replacements = self._prepare_instruccion_mandato_replacements(data)
       logger.info(f"Prepared {len(replacements)} placeholder replacements")

       # Replace placeholders in paragraphs
       para_replacements = 0
       for paragraph in doc.paragraphs:
           for placeholder, value in replacements.items():
               if placeholder in paragraph.text:
                   paragraph.text = paragraph.text.replace(placeholder, str(value))
                   para_replacements += 1

       # Replace placeholders in tables
       table_replacements = 0
       for table in doc.tables:
           for row in table.rows:
               for cell in row.cells:
                   for paragraph in cell.paragraphs:
                       for placeholder, value in replacements.items():
                           if placeholder in paragraph.text:
                               paragraph.text = paragraph.text.replace(placeholder, str(value))
                               table_replacements += 1

       logger.info(f"Replacements made: {para_replacements} in paragraphs, {table_replacements} in tables")

       # NOTE: No creditor table population needed for DIAN template

       # Save to bytes
       import io
       file_stream = io.BytesIO()
       doc.save(file_stream)
       file_stream.seek(0)

       logger.info(f"Generated DIAN Mandato (IM) document for contract {data.get('contract_id', 'unknown')}")
       return file_stream.read()
   ```

3. Run backend linting: `cd backend && ruff check src/core/servicios/document_service.py`

### Task 4: Add API Endpoint for DIAN Mandato Generation

**Files:** `backend/src/adapter/rest/operations_routes.py`

1. Add import for new DTO at top of file (around line 30):
   ```python
   from src.interface.legal_dtos import (
       # ... existing imports ...
       DIANMandatoRequest,
   )
   ```

2. Add new endpoint after the existing `generate_instruccion_mandato` endpoint (after line 747):
   ```python
   # ==================== DIAN Mandato (IM) Endpoints ====================

   @router.post("/contracts/dian-mandato/parse-cotizacion", response_model=CotizacionData)
   async def parse_cotizacion_for_dian_mandato(
       file: UploadFile = File(..., description="Cotización PDF document"),
       current_user: dict = Depends(require_operations_role)
   ):
       """
       Parse Cotización PDF for DIAN Mandato (IM) (Operations role or Admin required)

       This endpoint reuses the same Cotización parser as Instrucción de Mandato.
       Returns extracted data for form pre-population.
       """
       import logging
       logger = logging.getLogger(__name__)

       logger.info(f"Cotización PDF parse request for DIAN Mandato - File: {file.filename}, User: {current_user.get('email', current_user.get('id'))}")

       try:
           # Validate file type
           if file.content_type != 'application/pdf':
               raise HTTPException(
                   status_code=400,
                   detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed"
               )

           # Validate file size (5MB limit)
           pdf_bytes = await file.read()
           if len(pdf_bytes) > 5 * 1024 * 1024:
               raise HTTPException(
                   status_code=400,
                   detail="PDF file size exceeds 5MB limit"
               )

           # Parse Cotización document
           logger.info(f"Parsing Cotización document: {file.filename}")
           parser = CotizacionParserService()

           try:
               cotizacion_data = parser.parse_cotizacion(pdf_bytes)
               logger.info(f"Cotización parsed successfully - Quote: {cotizacion_data.numero_cotizacion}")
               return cotizacion_data
           except ValueError as e:
               logger.error(f"Cotización parsing failed: {e}")
               raise HTTPException(
                   status_code=422,
                   detail=f"Error parsing Cotización document: {str(e)}"
               )
           except Exception as e:
               logger.error(f"Unexpected error parsing Cotización: {e}", exc_info=True)
               raise HTTPException(
                   status_code=422,
                   detail=f"Failed to parse Cotización document: {str(e)}"
               )
       except HTTPException:
           raise
       except Exception as e:
           logger.error(f"Error processing Cotización PDF: {e}", exc_info=True)
           raise HTTPException(status_code=500, detail=str(e))


   @router.post("/contracts/dian-mandato/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
   async def generate_dian_mandato(
       request: DIANMandatoRequest,
       service: ContractService = Depends(get_contract_service),
       client_repo: ClientRepository = Depends(get_client_repo),
       current_user: dict = Depends(require_operations_role)
   ):
       """
       Generate DIAN Mandato (IM) contract (Operations role or Admin required)

       This is a simplified Mandato for DIAN payments - no creditors required.

       The request must include:
       - client_nit: Client NIT for database lookup
       - numero_cotizacion_desembolso: Quote number
       - fecha_contrato_mandato: Mandate contract date (ISO format)
       - monto: Total amount

       Returns the created contract with ID format: PLDI-YYYY-XXX
       """
       import logging
       logger = logging.getLogger(__name__)

       logger.info(f"DIAN Mandato generation request - NIT: {request.client_nit}, Quote: {request.numero_cotizacion_desembolso}, User: {current_user.get('email', current_user.get('id'))}")

       try:
           # Get user_id from authenticated user
           user_id = current_user['id']

           # Validate client exists
           client = await client_repo.get_by_nit(request.client_nit)
           if not client:
               logger.error(f"Client not found with NIT: {request.client_nit}")
               raise HTTPException(
                   status_code=404,
                   detail=f"Client with NIT {request.client_nit} not found"
               )

           # Build data snapshot combining client data + DIAN mandato data
           from decimal import Decimal
           cupo = client.get('cupo_plataforma')

           data_snapshot = {
               # Client data (client is a dict from repository)
               "nit": client['nit'],
               "nombre_importador": client['nombre_importador'],
               "representante_legal": client['representante_legal'],
               "cedula_representante": client['cedula_representante'],
               "ciudad_domicilio": client['ciudad_domicilio'],
               "cupo_plataforma": float(cupo) if cupo is not None and isinstance(cupo, (Decimal, int, float, str)) else cupo,
               "direccion_comercial": client.get('direccion_comercial'),
               "tipo_identificacion_representante": client.get('tipo_identificacion_representante'),
               # DIAN Mandato specific data
               "numero_cotizacion_desembolso": request.numero_cotizacion_desembolso,
               "fecha_contrato_mandato": request.fecha_contrato_mandato,
               "monto": float(request.monto),
               # No acreedores for DIAN
           }

           logger.info(f"Prepared data snapshot for DIAN Mandato")

           # Create contract generation request
           contract_request = ContractGenerationRequest(
               client_nit=request.client_nit,
               contract_type=ContractType.PL_CO_DIAN_MANDATO_IM,
               custodian_data=None
           )

           # Generate contract with custom data snapshot
           contract = await service.generate_contract(
               request=contract_request,
               user_id=user_id,
               custom_data_snapshot=data_snapshot
           )

           contract_id = contract.get('contract_id', 'unknown')
           logger.info(f"Generated DIAN Mandato contract: {contract_id}")

           # Return response
           return ContractGenerationResponse(
               id=contract['id'],
               contract_id=contract['contract_id'],
               contract_type=contract['contract_type'],
               client_nit=contract['client_nit'],
               status=contract['status'],
               generated_at=contract['generated_at'],
               pdf_url=contract.get('pdf_url'),
               approved_document_url=contract.get('approved_document_url'),
               data_snapshot=contract['data_snapshot']
           )

       except HTTPException:
           raise
       except Exception as e:
           logger.error(f"Error generating DIAN Mandato: {e}", exc_info=True)
           raise HTTPException(status_code=500, detail=f"Error generating contract: {str(e)}")
   ```

3. Run backend linting: `cd backend && ruff check src/adapter/rest/operations_routes.py`

### Task 5: Add Frontend TypeScript Types

**Files:** `frontend/src/types/legal.ts`

1. Add `DIANMandatoRequest` interface after `InstruccionMandatoFormData` (after line 228):
   ```typescript
   // DIAN Mandato (IM) Types - Simplified, no creditors
   export interface DIANMandatoRequest {
     client_nit: string;
     numero_cotizacion_desembolso: string;
     fecha_contrato_mandato: string; // ISO date string
     monto: number;
   }
   ```

2. Run TypeScript type check: `cd frontend && npx tsc --noEmit`

### Task 6: Add Frontend Service Methods

**Files:** `frontend/src/services/operationsService.ts`

1. Import the new type at top (around line 12):
   ```typescript
   import type {
     // ... existing imports ...
     DIANMandatoRequest,
   } from '../types/legal';
   ```

2. Add service methods after `generateInstruccionMandato()` (after line 290):
   ```typescript
   /**
    * Parse Cotización PDF and extract data for DIAN Mandato (IM)
    */
   async parseCotizacionForDIANMandato(file: File): Promise<CotizacionData> {
     const formData = new FormData();
     formData.append('file', file);

     const response = await apiClient.post<CotizacionData>(
       `${BASE_URL}/contracts/dian-mandato/parse-cotizacion`,
       formData,
       {
         headers: {
           'Content-Type': 'multipart/form-data',
         },
       }
     );
     return response.data;
   },

   /**
    * Generate DIAN Mandato (IM) contract - simplified, no creditors
    */
   async generateDIANMandato(
     request: DIANMandatoRequest
   ): Promise<ContractGeneration> {
     const response = await apiClient.post<ContractGeneration>(
       `${BASE_URL}/contracts/dian-mandato/generate`,
       request
     );
     return response.data;
   },
   ```

3. Run frontend linting: `cd frontend && npm run lint`

### Task 7: Create FKDIANMandatoForm Component

**Files:** `frontend/src/components/forms/FKDIANMandatoForm.tsx` (new file)

Create a simplified form component based on `FKInstruccionMandatoForm.tsx` but WITHOUT the creditor/bank certificate sections:

1. Create new file with content implementing:
   - Section 1: Client Search (same as regular Mandato IM)
   - Section 2: Cotización PDF Upload (same as regular Mandato IM)
   - Section 3: Extracted Data Review (numero_cotizacion, fecha, monto)
   - Section 4: Generate Document button (no creditor section)
2. Remove all Bank Certificate handling code
3. Remove all `acreedores` state and logic
4. Call `operationsService.generateDIANMandato()` instead
5. Run frontend linting: `cd frontend && npm run lint`

### Task 8: Update Parent Component to Use DIAN Form

**Files:** `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`

1. Add import for new form (around line 22):
   ```typescript
   import FKDIANMandatoForm from './FKDIANMandatoForm';
   ```

2. Update the rendering logic (around lines 131-141) to use DIAN form for third tab:
   ```typescript
   {config.type === 'pl_co_solicitud_desembolso' ? (
     <FKSolicitudDesembolsoRequest />
   ) : config.type === 'pl_co_mandato_im' ? (
     <FKInstruccionMandatoForm />
   ) : config.type === 'pl_co_dian_mandato_im' ? (
     <FKDIANMandatoForm />
   ) : (
     <FKPagaLocalCOContractRequest
       contractType={config.type}
       contractLabel={config.label}
     />
   )}
   ```

3. Run frontend linting: `cd frontend && npm run lint`

### Task 9: Create E2E Test File

**Files:** `.claude/commands/e2e/test_dian_mandato_im_form.md` (new file)

1. Read `.claude/commands/test_e2e.md` for test runner instructions
2. Read `.claude/commands/e2e/test_instruccion_mandato_form.md` for reference
3. Create E2E test file with:
   - User Story for DIAN Mandato workflow
   - Test steps for: login → navigate → client search → cotización upload → generate
   - NO bank certificate upload steps (key difference)
   - Success criteria verification
   - Screenshots at each step

### Task 10: Run Validation Commands

Execute all validation commands to ensure zero regressions:

1. `cd backend && python -m pytest` - Run backend tests
2. `cd backend && ruff check src/` - Run backend linting
3. `cd frontend && npm run lint` - Run frontend linting
4. `cd frontend && npx tsc --noEmit` - Run TypeScript type check
5. `cd frontend && npm run build` - Run frontend build

## Testing Strategy

### Unit Tests
- Test `generate_dian_mandato_document()` produces valid DOCX
- Test all placeholder replacements
- Test API endpoint validation for `DIANMandatoRequest`
- Test client not found returns 404

### Edge Cases
1. **Invalid PDF file type** → Should return 400 error
2. **PDF exceeds 5MB** → Should return 400 error
3. **Cotización parsing fails** → Should return 422 error
4. **Client NIT not found** → Should return 404 error
5. **Empty monto** → Should return 400 validation error
6. **Invalid date format** → Should return 400 validation error
7. **Template file missing** → Should return 500 error with helpful message

## Acceptance Criteria

### Backend
- [ ] `DIANMandatoRequest` DTO created with validation
- [ ] `generate_dian_mandato_document()` fills all 9 placeholders correctly
- [ ] No creditor table population (DIAN template has no creditor table)
- [ ] API endpoint `POST /api/operations/contracts/dian-mandato/generate` works
- [ ] API endpoint `POST /api/operations/contracts/dian-mandato/parse-cotizacion` works
- [ ] Contract ID generated with `PLDI-` prefix
- [ ] Database migration file created for template record
- [ ] All backend linting passes

### Frontend
- [ ] `FKDIANMandatoForm` component created (no bank cert sections)
- [ ] Form successfully parses Cotización PDF
- [ ] Form displays extracted data for review
- [ ] Generate button calls correct API endpoint
- [ ] Success message shows contract ID with `PLDI-` prefix
- [ ] Form can be reset for new document
- [ ] All frontend linting passes
- [ ] TypeScript compiles without errors
- [ ] Frontend builds successfully

### Integration
- [ ] E2E test passes with all screenshots captured
- [ ] Generated DOCX document opens without errors
- [ ] All placeholders replaced (no `[...]` remaining)
- [ ] Date components match input date
- [ ] Amount displays in both numbers and words

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions:

1. **Run Backend Tests:**
   ```bash
   cd backend && source venv/bin/activate && python -m pytest
   ```
   Expected: All tests pass

2. **Run Backend Linting:**
   ```bash
   cd backend && source venv/bin/activate && ruff check src/
   ```
   Expected: No linting errors

3. **Run Frontend Linting:**
   ```bash
   cd frontend && npm run lint
   ```
   Expected: No linting errors

4. **Run TypeScript Type Check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```
   Expected: No type errors

5. **Run Frontend Build:**
   ```bash
   cd frontend && npm run build
   ```
   Expected: Build succeeds, output in `dist/`

6. **Run E2E Test:**
   - Read `.claude/commands/test_e2e.md`
   - Read and execute `.claude/commands/e2e/test_dian_mandato_im_form.md`
   - Expected: Test passes with all screenshots captured

7. **Manual Verification:**
   - Run database migration in Supabase SQL Editor
   - Generate a test DIAN Mandato document
   - Verify all placeholders replaced
   - Verify contract ID starts with `PLDI-`

## Notes

### Database Migration

The migration file `backend/database/migration_add_dian_mandato_im_template.sql` must be run manually in Supabase SQL Editor before testing the feature:

1. Go to Supabase Dashboard → SQL Editor
2. Paste the migration SQL
3. Execute
4. Verify the record exists with: `SELECT * FROM contract_templates WHERE contract_type = 'pl_co_dian_mandato_im';`

### Dependencies

**No new dependencies required.** This feature reuses existing:
- python-docx for Word document manipulation
- PyMuPDF (fitz) for PDF parsing
- FastAPI for API endpoints
- React/MUI for frontend components

### Key Differences from Regular Mandato (IM)

| Aspect | Regular Mandato (IM) | DIAN Mandato (IM) |
|--------|---------------------|-------------------|
| Contract Type | `pl_co_mandato_im` | `pl_co_dian_mandato_im` |
| Contract ID Prefix | `PLMI-` | `PLDI-` |
| Template | `FK COL - Fin. COP - Mandato (IM).docx` | `FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx` |
| Bank Certificate | Required (1-3 per document) | NOT required |
| Creditor Table | Populated with bank info | No creditor table |
| API Endpoint | `/contracts/instruccion-mandato/generate` | `/contracts/dian-mandato/generate` |
| Request DTO | `InstruccionMandatoRequest` (has acreedores) | `DIANMandatoRequest` (no acreedores) |

### Future Enhancements

1. **Auto-detect DIAN in regular Mandato form**: If a creditor is detected as DIAN in the regular Mandato (IM) form, suggest using the DIAN Mandato form instead.

2. **Batch DIAN payments**: Support generating multiple DIAN Mandato documents at once.

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (Document Generation)
- [x] All new files listed in "New Files" section (3 files)
- [x] All database migrations identified and tasks created (Task 2)
- [x] E2E test file task included (Task 9)
- [x] All external dependencies listed in Notes (None required)

### Category-Specific Completeness

**Document Generation:**
- [x] ALL template placeholders extracted and documented (9 placeholders)
- [x] Placeholder mapping table complete with data sources
- [x] Database records verified (template file exists, enum exists, prefix exists, migration needed)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (Colombia, COP, Spanish)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
