# Feature: LandingAI-Powered RUT Document Extraction for Inventario Bodega

## Feature Description
The Inventario Bodega contract workflow currently extracts custodian information from RUT (Registro Único Tributario) PDF documents using PyMuPDF text extraction. However, some RUT PDFs are scanned images rather than text-based PDFs, causing the current extraction to fail.

This feature adds an optional LandingAI-powered extraction mode that users can enable via a checkbox when:
1. The RUT PDF is an image-based scan (no selectable text)
2. The regular text-based extraction fails or produces incorrect results

LandingAI's ADE (Agentic Document Extraction) API uses AI to extract structured data from document images, making it more robust for scanned documents at the cost of processing time (30-60 seconds).

## User Story
As an Operations team member
I want to optionally use AI-powered extraction for image-based RUT documents
So that I can successfully process Inventario Bodega contracts even when RUT PDFs are scanned images

## Problem Statement
RUT documents from DIAN (Colombian tax authority) can be:
1. **Text-based PDFs**: Generated digitally with selectable text → Current extraction works
2. **Image-based PDFs**: Scanned documents where text is embedded as images → Current extraction fails

When operations users upload image-based RUT PDFs, the current `RUTParserService` cannot extract the required custodian fields, blocking contract generation.

## Solution Statement
Add a checkbox option in the `FKInventarioRequest` form that allows users to enable "AI-powered extraction" (LandingAI). When enabled:
1. The RUT PDF is sent to LandingAI's ADE Parse API to convert to markdown
2. The markdown is sent to LandingAI's ADE Extract API with a RUT-specific JSON schema
3. The extracted structured data is mapped to the existing `CustodianData` model
4. The contract generation proceeds as normal with the AI-extracted data

A tooltip informs users that AI extraction is more robust but takes longer (30-60 seconds).

## Access Control
- Required Role(s): `operations`, `admin`
- Backend Protection: `require_operations_role` dependency (already in place)
- Frontend Protection: Protected by existing `RoleProtectedRoute` for operations pages

## Relevant Files
Use these files to implement the feature:

**Backend - Core Services:**
- `backend/src/core/servicios/rut_parser_service.py` - Current RUT text extraction (add LandingAI integration here)
- `backend/src/config/settings.py` - Add LandingAI API configuration

**Backend - API Routes:**
- `backend/src/adapter/rest/operations_routes.py` - Add `use_ai_extraction` form parameter to contract generation endpoint

**Backend - DTOs:**
- `backend/src/interface/legal_dtos.py` - Contains `CustodianData` model (no changes needed)

**Backend - Reference:**
- `docs/20251127_landingai_ade_integration_guide.md` - LandingAI API documentation

**Frontend - Forms:**
- `frontend/src/components/forms/FKInventarioRequest.tsx` - Add AI extraction checkbox with tooltip

**Frontend - Services:**
- `frontend/src/services/operationsService.ts` - Add `use_ai_extraction` parameter to API call

**Testing:**
- `.claude/commands/e2e/test_login.md` - E2E test reference pattern
- `.claude/commands/test_e2e.md` - E2E test runner documentation

### New Files
- `backend/src/core/servicios/landingai_rut_parser_service.py` - LandingAI-based RUT extraction service
- `.claude/commands/e2e/test_inventario_bodega_ai_extraction.md` - E2E test for AI extraction feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| RUTParserService.parse_rut_pdf() | CustodianData (Pydantic) | data.field_name | `custodian_data.nombre_operador_custodio` |
| LandingAIRUTParserService.parse_rut_pdf() | CustodianData (Pydantic) | data.field_name | Same as above |

### F. External API Contract (LandingAI ADE)

**ADE Parse API:**
| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `https://api.va.landing.ai/v1/ade/parse` | POST | Bearer Token | multipart/form-data (document file) | JSON `{ "markdown": "...", "chunks": [...] }` |

**ADE Extract API:**
| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `https://api.va.landing.ai/v1/ade/extract` | POST | Bearer Token | form-data (schema, markdown) | JSON `{ "extraction": {...} }` |

**RUT Extraction Schema (for LandingAI):**
```json
{
  "type": "object",
  "properties": {
    "nombre_operador_custodio": {
      "type": "string",
      "description": "Company legal name (Razón social) - field 35"
    },
    "ciudad_domicilio_custodio": {
      "type": "string",
      "description": "City/Municipality where company is located - field 40"
    },
    "nit_operador_custodio": {
      "type": "string",
      "description": "Tax ID with verification digit (NIT-DV format: 900989925-7) - fields 5 and 6"
    },
    "email_operador_custodio": {
      "type": "string",
      "description": "Company contact email - field 42"
    },
    "nombre_representante_legal_custodio": {
      "type": "string",
      "description": "Legal representative full name (first + last names) - fields 104-107"
    },
    "cc_representante_legal_custodio": {
      "type": "string",
      "description": "Legal representative ID number (cédula) - field 101"
    },
    "tipo_identificacion_representante_legal_custodio": {
      "type": "string",
      "description": "Legal representative ID type (CC, CE, Pasaporte) - field 100"
    }
  },
  "required": [
    "nombre_operador_custodio",
    "nit_operador_custodio",
    "nombre_representante_legal_custodio",
    "cc_representante_legal_custodio"
  ]
}
```

**Error Handling Strategy:**
- HTTP 200: Full success, use extraction data directly
- HTTP 206: Partial success, data is usable but check for null fields
- HTTP 4xx/5xx: Log error, raise ValueError with descriptive message
- Timeout (120s): Raise timeout error, suggest retry

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| use_ai_extraction | use_ai_extraction | boolean | New form field, defaults to false |
| rut_file | rut_file | File (PDF) | Existing field, no changes |

## Implementation Plan

### Phase 1: Foundation
1. Add LandingAI API configuration to backend settings
2. Create the LandingAI RUT parser service with proper schema
3. Add `use_ai_extraction` parameter to operations routes

### Phase 2: Core Implementation
1. Implement LandingAI Parse + Extract flow in new service
2. Update operations endpoint to conditionally use AI or text extraction
3. Add checkbox with tooltip to frontend form
4. Update frontend service to pass new parameter

### Phase 3: Integration
1. Test with sample image-based RUT PDFs
2. Verify fallback behavior when API fails
3. Ensure existing text-based extraction still works by default

## Step by Step Tasks

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` to understand E2E test runner format
- Read `.claude/commands/e2e/test_login.md` for test file structure reference
- Create `.claude/commands/e2e/test_inventario_bodega_ai_extraction.md` with:
  - User story for AI extraction feature
  - Test steps for enabling checkbox and submitting form
  - Verification of loading state during AI processing
  - Success criteria including longer processing time

### Step 2: Add LandingAI Configuration to Backend Settings
- Edit `backend/src/config/settings.py`
- Add environment variables:
  ```python
  LANDINGAI_API_KEY: str = ""
  LANDINGAI_PARSE_ENDPOINT: str = "https://api.va.landing.ai/v1/ade/parse"
  LANDINGAI_EXTRACT_ENDPOINT: str = "https://api.va.landing.ai/v1/ade/extract"
  ```

### Step 3: Create LandingAI RUT Parser Service
- Create `backend/src/core/servicios/landingai_rut_parser_service.py`
- Import `CustodianData` from `src.interface.legal_dtos`
- Define RUT_EXTRACTION_SCHEMA constant with all 7 custodian fields
- Implement `LandingAIRUTParserService` class with:
  - `__init__(self)` - load settings, configure API endpoints
  - `parse_rut_pdf(self, pdf_bytes: bytes) -> CustodianData` - main extraction method
  - `_call_parse_api(self, pdf_bytes: bytes) -> str` - call ADE Parse, return markdown
  - `_call_extract_api(self, markdown: str) -> dict` - call ADE Extract with schema
  - `_map_to_custodian_data(self, extraction: dict) -> CustodianData` - map to Pydantic model
  - `_validate_extraction(self, data: dict) -> bool` - check required fields present
- Handle HTTP 200 and 206 responses appropriately
- Set timeout to 120 seconds for API calls
- Add comprehensive logging for debugging

### Step 4: Update Operations Routes
- Edit `backend/src/adapter/rest/operations_routes.py`
- Add `use_ai_extraction: Optional[bool] = Form(False)` parameter to `request_contract_generation`
- Import `LandingAIRUTParserService` from new service
- Update RUT parsing logic:
  ```python
  if contract_type_enum == ContractType.INVENTARIO_BODEGA:
      if use_ai_extraction:
          logger.info("Using LandingAI for RUT extraction (user requested)")
          parser = LandingAIRUTParserService()
      else:
          parser = RUTParserService()
      custodian_data = parser.parse_rut_pdf(rut_bytes)
  ```
- Add error handling for LandingAI-specific errors

### Step 5: Update Frontend Form Component
- Edit `frontend/src/components/forms/FKInventarioRequest.tsx`
- Add imports for Checkbox, FormControlLabel, Tooltip from MUI
- Add state: `const [useAiExtraction, setUseAiExtraction] = useState(false);`
- Add checkbox after RUT file upload section:
  ```tsx
  <Tooltip title="Usa inteligencia artificial para extraer datos de documentos escaneados. Más robusto pero toma más tiempo (30-60 segundos).">
    <FormControlLabel
      control={
        <Checkbox
          checked={useAiExtraction}
          onChange={(e) => setUseAiExtraction(e.target.checked)}
        />
      }
      label="Usar extracción AI (para PDFs escaneados)"
    />
  </Tooltip>
  ```
- Pass `useAiExtraction` to service call
- Show loading indicator with "Extrayendo datos con AI..." message when AI extraction is enabled

### Step 6: Update Frontend Operations Service
- Edit `frontend/src/services/operationsService.ts`
- Update `requestInventarioBodegaGeneration` signature:
  ```typescript
  async requestInventarioBodegaGeneration(
    clientNit: string,
    rutFile: File,
    useAiExtraction: boolean = false
  ): Promise<ContractGeneration>
  ```
- Add to FormData:
  ```typescript
  formData.append('use_ai_extraction', useAiExtraction.toString());
  ```

### Step 7: Update Frontend Component to Use New Service Signature
- Edit `frontend/src/components/forms/FKInventarioRequest.tsx`
- Update `handleRequestContract` to pass `useAiExtraction`:
  ```typescript
  const contract = await operationsService.requestInventarioBodegaGeneration(
    selectedClient.nit,
    rutFile,
    useAiExtraction
  );
  ```

### Step 8: Add Dependencies to Requirements
- Edit `backend/requirements.txt`
- Add `requests>=2.31.0` if not already present (for LandingAI API calls)

### Step 9: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Testing Strategy

### Unit Tests
- `test_landingai_rut_parser_service.py`:
  - Test `_map_to_custodian_data` with valid extraction dict
  - Test `_validate_extraction` with missing required fields
  - Test HTTP 206 partial success handling
  - Mock API responses for parse and extract endpoints

### Edge Cases
1. **LandingAI API unavailable**: Should raise ValueError with clear message
2. **Partial extraction (HTTP 206)**: Should still succeed if required fields present
3. **Timeout**: Should raise timeout error after 120 seconds
4. **Invalid API key**: Should raise auth error with helpful message
5. **Empty/corrupted PDF**: Should raise ValueError explaining the issue
6. **Very large PDF (>5MB)**: Already validated at upload, but API should handle gracefully
7. **Non-RUT document**: Extraction will likely fail validation, raise descriptive error

## Acceptance Criteria
1. ✅ Checkbox appears in FKInventarioRequest form after RUT file upload section
2. ✅ Tooltip explains AI extraction is for scanned PDFs and takes 30-60 seconds
3. ✅ When checkbox is unchecked (default), existing text extraction is used
4. ✅ When checkbox is checked, LandingAI extraction is used
5. ✅ Loading state shows "Extrayendo datos con AI..." when AI extraction is in progress
6. ✅ Successful AI extraction populates contract with custodian data
7. ✅ API errors show descriptive error messages to user
8. ✅ Existing text-based extraction continues to work unchanged
9. ✅ Backend properly validates `use_ai_extraction` as boolean
10. ✅ Environment variable `LANDINGAI_API_KEY` is required for AI extraction to work

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend validation
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend production build
cd frontend && npm run build

# E2E test (after starting dev servers)
# Read .claude/commands/test_e2e.md
# Execute .claude/commands/e2e/test_inventario_bodega_ai_extraction.md
```

## Notes

### New Dependencies
- **Backend**: `requests>=2.31.0` (should already be available via httpx, but add explicitly for LandingAI calls)

### Environment Variables Required for Production
```bash
LANDINGAI_API_KEY=your_api_key_here
```

### Cost Considerations
- LandingAI ADE charges per document processed (~$0.30-$4.00/doc depending on size)
- Only enabled when user explicitly checks the AI extraction checkbox
- Default behavior (unchecked) uses free text extraction

### Future Enhancements
1. **Automatic fallback**: If text extraction fails, automatically retry with AI extraction
2. **Confidence scores**: Display extraction confidence to user
3. **Caching**: Cache extraction results to avoid re-processing same documents

### RUT Field Mapping Reference
| Field # | Field Name | CustodianData Field |
|---------|------------|---------------------|
| 35 | Razón social | nombre_operador_custodio |
| 40 | Ciudad/Municipio | ciudad_domicilio_custodio |
| 5+6 | NIT + DV | nit_operador_custodio |
| 42 | Correo electrónico | email_operador_custodio |
| 104-107 | Representante Legal names | nombre_representante_legal_custodio |
| 101 | Número de identificación | cc_representante_legal_custodio |
| 100 | Tipo de documento | tipo_identificacion_representante_legal_custodio |

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (API Integration)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - no schema changes)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**API Integration:**
- [x] External API contract documented (ADE Parse and Extract endpoints)
- [x] Auth method specified (Bearer token)
- [x] Error/retry strategy defined (timeout, HTTP status handling)

### Consistency (ALL features)
- [x] Data types match between frontend and backend (boolean use_ai_extraction)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods (CustodianData is Pydantic model)
- [x] Country-specific variations handled (N/A - Colombia only feature)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
