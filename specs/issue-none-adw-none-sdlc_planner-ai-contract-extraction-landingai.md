# Feature: AI-Powered Contract Data Extraction with LandingAI ADE

## Feature Description
Implement AI-powered contract data extraction using LandingAI's Agentic Document Extraction (ADE) API for scanned contracts and image-based PDFs. This feature extends the existing standard regex-based contract extraction with an AI alternative that can process scanned/image-based documents where text extraction fails.

The feature adds a new API endpoint for AI extraction, updates the frontend FKContractUpload component to offer both extraction methods, and provides visual feedback during the longer AI processing time (30-60 seconds).

## User Story
As an **alianzas** team member
I want to extract contract data from scanned PDF contracts using AI
So that I can process image-based documents that standard text extraction cannot handle

## Problem Statement
The current contract extraction service (`ContractExtractorService`) uses regex patterns on extracted text from PDFs and DOCX files. However, when PDFs are scanned/image-based (no selectable text), the extraction fails with 0% confidence. Users currently have no automated option for these documents and must enter data manually.

## Solution Statement
Implement a new `LandingAIContractParserService` following the existing `LandingAIRUTParserService` pattern to:
1. Parse scanned PDFs to markdown using LandingAI ADE Parse API
2. Extract structured contract data using LandingAI ADE Extract API with a custom schema
3. Expose this through a new API endpoint `/api/alianzas/brokers/extract-contract-ai`
4. Update the frontend to allow users to choose between standard and AI extraction methods
5. Provide progress feedback during the 30-60 second AI processing time

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Use existing `require_alianzas_role` dependency from `rbac_dependencies.py`
- Frontend Protection: Component is within the Alianzas module which is already protected by `RoleProtectedRoute`

## Relevant Files
Use these files to implement the feature:

**Backend - Reference Pattern:**
- `backend/src/core/servicios/landingai_rut_parser_service.py` - Follow this exact pattern for the new contract parser service
- `backend/src/config/settings.py` - LandingAI settings already exist (LANDINGAI_API_KEY, LANDINGAI_PARSE_ENDPOINT, LANDINGAI_EXTRACT_ENDPOINT)

**Backend - Files to Modify:**
- `backend/src/adapter/rest/alianzas_routes.py` - Add new `/brokers/extract-contract-ai` endpoint
- `backend/src/interface/alianzas_dtos.py` - `BrokerContractData` and `ExtractionMethod` already defined, no changes needed

**Frontend - Files to Modify:**
- `frontend/src/components/alianzas/FKContractUpload.tsx` - Add AI extraction option with radio buttons and progress indicator
- `frontend/src/services/alianzasService.ts` - Add `extractContractAI` function

**Frontend - Reference Files:**
- `frontend/src/types/alianzas.ts` - Types already include `ExtractionMethod` and `BrokerContractData`, may need `AIExtractionStatus` type

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `backend/src/core/servicios/landingai_contract_parser_service.py` - AI contract parser service using LandingAI ADE
- `.claude/commands/e2e/test_ai_contract_extraction.md` - E2E test for AI contract extraction flow

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)
Repository methods and access patterns used:

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A - No repository needed | N/A | N/A | Service calls external LandingAI API |

The service directly calls LandingAI APIs and returns a Pydantic model. No database interaction required.

### F. External API Contract (Integration only)
LandingAI ADE API integration:

| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `https://api.va.landing.ai/v1/ade/parse` | POST | Bearer Token (LANDINGAI_API_KEY) | multipart/form-data with `document` file | JSON: `{ "markdown": "...", "chunks": [...] }` |
| `https://api.va.landing.ai/v1/ade/extract` | POST | Bearer Token (LANDINGAI_API_KEY) | form-data with `schema` (JSON) + `markdown` | JSON: `{ "extraction": {...}, "metadata": {...} }` (200 or 206 for partial) |

**Extraction Schema:**
```python
BROKER_CONTRACT_EXTRACTION_SCHEMA = {
    'type': 'object',
    'properties': {
        'nombre_broker': {
            'type': 'string',
            'description': 'Nombre o razón social del broker/aliado comercial que aparece en el contrato'
        },
        'porcentaje_comision_apertura': {
            'type': 'number',
            'description': 'Porcentaje de la comisión de apertura que corresponde al broker (ej: 60 para 60%, 80 para 80%). Buscar frases como "Bono equivalente al X%" o "X% de la comisión de apertura"'
        },
        'porcentaje_comision_operativa': {
            'type': 'number',
            'description': 'Porcentaje sobre operaciones/desembolsos mensuales (ej: 0.10 para 0.10%, 0.15 para 0.15%). Buscar frases como "comisión operativa" o "por cada desembolso"'
        },
        'fecha_contrato': {
            'type': 'string',
            'description': 'Fecha de firma del contrato en formato DD/MM/YYYY'
        },
        'vigencia_meses': {
            'type': 'integer',
            'description': 'Vigencia del contrato en meses (ej: 12, 24)'
        },
        'rfc_broker': {
            'type': 'string',
            'description': 'RFC del broker para facturación (formato: XXXX######XXX)'
        },
        'cuenta_bancaria': {
            'type': 'string',
            'description': 'Número de cuenta CLABE para depósitos (18 dígitos)'
        },
        'banco': {
            'type': 'string',
            'description': 'Nombre de la institución bancaria'
        }
    },
    'required': [
        'porcentaje_comision_apertura',
        'porcentaje_comision_operativa'
    ]
}
```

**Error Handling Strategy:**
| Error | HTTP Code | User Message |
|-------|-----------|--------------|
| Timeout (>120s) | 504 | "La extracción está tomando demasiado tiempo. Intente de nuevo." |
| Invalid API Key | 401 | "API key no válida. Contacte al administrador." |
| Rate Limit | 429 | "Límite de peticiones excedido. Intente en unos minutos." |
| Partial Success | 206 | Return data with warning, allow manual completion |
| Missing Required Fields | 200 | Return partial data with lower confidence score |

### Interface Mapping (Frontend ↔ Backend)
Map frontend TypeScript fields to backend Pydantic fields:

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| nombre_broker | nombre_broker | string \| null | Extracted broker name |
| porcentaje_comision_apertura | porcentaje_comision_apertura | number \| null | 0-100 percentage |
| porcentaje_comision_operativa | porcentaje_comision_operativa | number \| null | 0-100 percentage |
| fecha_contrato | fecha_contrato | string \| null | ISO date format |
| vigencia_meses | vigencia_meses | number \| null | Months |
| rfc_broker | rfc_broker | string \| null | Mexican RFC |
| cuenta_bancaria | cuenta_bancaria | string \| null | CLABE 18 digits |
| banco | banco | string \| null | Bank name |
| extraction_method | extraction_method | 'standard' \| 'ai' | Method used |
| extraction_confidence | extraction_confidence | number \| null | 0-1 confidence |
| raw_text_preview | raw_text_preview | string \| null | Debug preview |

All fields use **snake_case** consistently between frontend and backend.

## Implementation Plan

### Phase 1: Foundation
1. Create `LandingAIContractParserService` following `LandingAIRUTParserService` pattern
2. Implement the extraction schema and API calling logic
3. Handle HTTP 206 partial success responses

### Phase 2: Core Implementation
1. Add new API endpoint `/brokers/extract-contract-ai` in `alianzas_routes.py`
2. Add dependency injection for the new service
3. Update frontend types for AI extraction status
4. Add `extractContractAI` service function with extended timeout
5. Update `FKContractUpload` component with extraction method selection

### Phase 3: Integration
1. Add progress indicator for AI extraction steps
2. Implement fallback suggestion (suggest AI when standard fails)
3. Create E2E test for the AI extraction flow
4. Test error handling and timeout scenarios

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_ai_contract_extraction.md` with test steps for:
  - Navigate to broker management page
  - Login as alianzas user
  - Create new broker
  - Upload a scanned PDF contract
  - Select AI extraction method
  - Verify progress indicator appears with steps
  - Verify extracted data appears in preview
  - Apply extracted data to form
  - Capture screenshots at each step

### Step 2: Create LandingAI Contract Parser Service
- Create `backend/src/core/servicios/landingai_contract_parser_service.py`
- Follow the exact pattern from `landingai_rut_parser_service.py`
- Define `BROKER_CONTRACT_EXTRACTION_SCHEMA` constant with all fields
- Implement `LandingAIContractParserService` class with:
  - `__init__` loading settings from `get_settings()`
  - `parse_contract_pdf(pdf_bytes: bytes) -> BrokerContractData` main method
  - `_call_parse_api(pdf_bytes: bytes) -> str` for ADE Parse
  - `_call_extract_api(markdown: str) -> dict` for ADE Extract
  - `_validate_extraction(extraction: dict) -> bool` for required fields
  - `_map_to_contract_data(extraction: dict) -> BrokerContractData` for mapping
- Handle HTTP 206 partial success like the RUT parser
- Set `extraction_method = ExtractionMethod.AI` in returned data

### Step 3: Add API Endpoint in alianzas_routes.py
- Import the new `LandingAIContractParserService`
- Add dependency injection function `get_landingai_contract_parser`
- Add new endpoint:
  ```python
  @router.post('/brokers/extract-contract-ai', response_model=BrokerContractData)
  async def extract_contract_ai(
      contract_file: UploadFile = File(..., description='Contrato PDF del broker'),
      current_user: dict = Depends(require_alianzas_role),
      parser: LandingAIContractParserService = Depends(get_landingai_contract_parser)
  ) -> BrokerContractData:
  ```
- Validate file type (PDF only for AI extraction)
- Validate file size (max 10MB)
- Call `parser.parse_contract_pdf(await contract_file.read())`
- Handle ValueError exceptions with appropriate HTTP status codes

### Step 4: Update Frontend Types
- Update `frontend/src/types/alianzas.ts`
- Add `AIExtractionStatus` type:
  ```typescript
  export type AIExtractionStatus = 'idle' | 'uploading' | 'parsing' | 'extracting' | 'complete' | 'error';
  ```
- Add `AI_EXTRACTION_STATUS_LABELS` for display text

### Step 5: Update Frontend Service
- Update `frontend/src/services/alianzasService.ts`
- Add `extractContractAI` function:
  ```typescript
  extractContractAI: async (file: File): Promise<BrokerContractData> => {
    const formData = new FormData();
    formData.append('contract_file', file);

    const response = await apiClient.post<BrokerContractData>(
      '/alianzas/brokers/extract-contract-ai',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000  // 2 minutes for AI processing
      }
    );
    return response.data;
  }
  ```

### Step 6: Update FKContractUpload Component
- Update `frontend/src/components/alianzas/FKContractUpload.tsx`
- Add state for extraction method: `const [extractionMethod, setExtractionMethod] = useState<'standard' | 'ai'>('standard');`
- Add state for AI status: `const [aiStatus, setAiStatus] = useState<AIExtractionStatus>('idle');`
- Add RadioGroup for extraction method selection:
  - "Estándar" option (default)
  - "IA (para escaneados)" option with warning helper text
- Update `handleExtract` to use the selected method:
  - If 'standard': use existing `alianzasService.extractContract`
  - If 'ai': use new `alianzasService.extractContractAI` with progress updates
- Add progress stepper for AI extraction showing:
  1. "Subiendo documento..." (uploading)
  2. "Convirtiendo a texto (IA)..." (parsing)
  3. "Extrayendo datos (IA)..." (extracting)
  4. "Completado" (complete)
- Show extraction method chip in results ('Método: IA' or 'Método: Estándar')
- When standard extraction returns 0% confidence, suggest AI extraction

### Step 7: Add Error Handling
- Handle LandingAI-specific errors in the frontend:
  - Timeout: "La extracción IA está tomando demasiado tiempo. Intente de nuevo."
  - 401: "API key de IA no válida. Contacte al administrador."
  - 429: "Límite de peticiones de IA excedido. Intente en unos minutos."
  - Partial (206): Show warning banner and allow manual completion
- Disable form controls during AI extraction
- Show appropriate loading states

### Step 8: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Test `LandingAIContractParserService._map_to_contract_data()` with various extraction results
- Test `_validate_extraction()` with missing required fields
- Test timeout handling and error mapping
- Mock LandingAI API responses for unit tests

### Edge Cases
- PDF with no extractable data returns empty BrokerContractData with low confidence
- API timeout after 120 seconds raises appropriate error
- Partial success (HTTP 206) returns data with warning
- Invalid API key returns user-friendly error
- Rate limiting returns retry message
- Very large PDF (near 10MB limit) processes correctly
- Non-PDF file uploaded to AI endpoint returns 400 error

## Acceptance Criteria
- [ ] Can extract data from scanned PDF contracts using AI
- [ ] Progress indicator shows extraction steps during AI processing
- [ ] Extraction takes 30-60 seconds (within 120s timeout)
- [ ] Handles LandingAI errors gracefully with user-friendly messages
- [ ] Partial results (HTTP 206) handled with user notification
- [ ] AI-extracted data can be reviewed and edited before applying
- [ ] Extraction method shown in results ('ai' vs 'standard')
- [ ] When standard extraction fails (0% confidence), AI is suggested
- [ ] Form is disabled during extraction process
- [ ] Backend returns appropriate HTTP status codes for errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. **Backend Tests:**
```bash
cd backend && python -m pytest
```

2. **Backend Linting:**
```bash
cd backend && ruff check src/
```

3. **Frontend Linting:**
```bash
cd frontend && npm run lint
```

4. **TypeScript Type Check:**
```bash
cd frontend && npx tsc --noEmit
```

5. **Frontend Build:**
```bash
cd frontend && npm run build
```

6. **E2E Test (after implementation):**
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_ai_contract_extraction.md` to validate the AI extraction flow

7. **Manual API Test:**
```bash
# Test AI extraction endpoint with a PDF file
curl -X POST "http://localhost:8000/api/alianzas/brokers/extract-contract-ai" \
  -H "Authorization: Bearer <token>" \
  -F "contract_file=@test_contract.pdf"
```

## Notes

### Dependencies
- No new pip packages required - `httpx` is already used by `landingai_rut_parser_service.py`
- No new npm packages required

### Configuration
- `LANDINGAI_API_KEY` environment variable must be set for AI extraction to work
- API endpoints are already configured in `settings.py`

### Performance Considerations
- AI extraction takes 30-60 seconds, much slower than standard extraction
- Progress indicator is essential for user experience
- 120-second timeout is configured to handle slow responses

### Future Enhancements
- Add retry logic for transient failures
- Cache extraction results for the same document
- Add batch extraction for multiple contracts
- Support additional document formats (images)

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no database changes)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**API Integration:**
- [x] External API contract documented
- [x] Auth method specified (Bearer token)
- [x] Error/retry strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods (N/A)
- [x] Country-specific variations handled (CO vs MX) - Not applicable, Mexico RFC format used

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
