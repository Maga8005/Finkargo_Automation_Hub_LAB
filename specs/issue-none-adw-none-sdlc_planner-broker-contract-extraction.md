# Feature: Broker Contract Data Extraction

## Feature Description
Implement a standard contract data extraction system using regex patterns for DOCX and PDF files with selectable text. This feature allows Alianzas users to upload broker contracts and automatically extract key commercial terms like commission percentages, bank information, and contract dates, reducing manual data entry and improving accuracy.

## User Story
As an **alianzas** user
I want to upload a broker contract (PDF or DOCX) and have it automatically extract the commercial terms
So that I can quickly populate broker information without manual data entry and reduce transcription errors

## Problem Statement
Currently, when onboarding new brokers, users must manually read through contracts and type each field into the broker form. This process is:
- Time-consuming (each contract can take 10-15 minutes to process)
- Error-prone (typos in percentages or bank account numbers)
- Inconsistent (different users may interpret fields differently)

## Solution Statement
Implement a regex-based text extraction service that:
1. Extracts text from DOCX and PDF documents
2. Uses pattern matching to identify key contract fields (commission rates, bank info, dates)
3. Supports multiple contract versions (Marzo 2024 and current templates)
4. Returns structured data that pre-populates the broker form
5. Allows users to review and correct extracted values before saving
6. Suggests AI extraction as a fallback when pattern matching fails

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Use existing `require_alianzas_role` dependency from `rbac_dependencies.py`
- Frontend Protection: Component is used within Alianzas pages already protected by `RoleProtectedRoute`

## Relevant Files
Use these files to implement the feature:

**Backend - Existing Files:**
- `backend/src/adapter/rest/alianzas_routes.py` - Add new `/brokers/extract-contract` endpoint
- `backend/src/interface/alianzas_dtos.py` - Add `BrokerContractData` DTO for extraction response
- `backend/src/core/servicios/broker_service.py` - Reference for service patterns
- `backend/src/core/servicios/document_service.py` - Reference for DOCX handling patterns (uses python-docx)
- `backend/src/adapter/rest/rbac_dependencies.py` - Use existing `require_alianzas_role`
- `backend/requirements.txt` - Already has `python-docx`, `PyMuPDF` for PDF text extraction

**Frontend - Existing Files:**
- `frontend/src/components/alianzas/FKBrokerForm.tsx` - Integrate contract upload section
- `frontend/src/services/alianzasService.ts` - Add `extractContract` API method
- `frontend/src/types/alianzas.ts` - Add `BrokerContractData` TypeScript interface
- `frontend/src/components/forms/FKExcelUploader.tsx` - Reference for upload component pattern (drag & drop)

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `backend/src/core/servicios/contract_extractor_service.py` - Contract text extraction service with regex patterns
- `frontend/src/components/alianzas/FKContractUpload.tsx` - Contract file upload component with preview
- `.claude/commands/e2e/test_broker_contract_extraction.md` - E2E test for contract extraction feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature extracts FROM documents, not generates them.

### B. Excel Column Mapping (Excel Processing only)
N/A

### C. File Format Specification (Import/Export only)

| Format | Max Size | Required Structure | Validation Rules |
|--------|----------|-------------------|------------------|
| DOCX | 10MB | Any text content | Must have readable text |
| PDF | 10MB | Selectable text (not scanned) | Must have extractable text |

**Extraction Patterns (Two Contract Versions):**

**Version Marzo 2024:**
| Pattern | Description | Example Match |
|---------|-------------|---------------|
| `Bono equivalente al (\d+)%` | Opening commission | "Bono equivalente al 60%" → 60 |
| `(\d+\.?\d*)%.*operativa` | Operational commission | "0.10% operativa" → 0.10 |

**Current Version:**
| Pattern | Description | Example Match |
|---------|-------------|---------------|
| `(\d+)% de la comisión de apertura` | Opening commission | "60% de la comisión de apertura" → 60 |
| `(\d+\.?\d*)%.*por operación` | Operational commission | "0.10% por operación" → 0.10 |

**Additional Patterns:**
| Pattern | Field | Example Match |
|---------|-------|---------------|
| `(?:firmado\|fecha).*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})` | Contract date | "firmado 15/03/2024" → 15/03/2024 |
| `vigencia.*?(\d+)\s*meses` | Duration months | "vigencia de 12 meses" → 12 |
| `R\.?F\.?C\.?[:\s]*([A-Z]{3,4}\d{6}[A-Z0-9]{3})` | RFC (tax ID) | "R.F.C.: ABC123456XY1" → ABC123456XY1 |
| `CLABE[:\s]*(\d{18})` | Bank account CLABE | "CLABE: 012345678901234567" → 012345678901234567 |
| `(?:banco\|institución)[:\s]*([A-Za-z\s]+)` | Bank name | "banco: BBVA" → BBVA |

### D. Data Contract Verification (ALL features)

| Repository/Service Method | Return Type | Access Pattern | Example |
|--------------------------|-------------|----------------|---------|
| ContractExtractorService.extract_from_docx() | BrokerContractData | DTO object | result.porcentaje_comision_apertura |
| ContractExtractorService.extract_from_pdf() | BrokerContractData | DTO object | result.extraction_confidence |
| ContractExtractorService._extract_with_patterns() | BrokerContractData | DTO object | Internal method |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] No new database tables needed
- [x] No new enums needed
- [x] No template files needed
- [x] This feature only processes uploaded files and returns extracted data

### F. External API Contract (Integration only)
N/A - No external APIs used

### G. Query Specification (Reporting only)
N/A

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| nombre_broker | nombre_broker | string \| null | Extracted broker name |
| porcentaje_comision_apertura | porcentaje_comision_apertura | number \| null | Opening commission % |
| porcentaje_comision_operativa | porcentaje_comision_operativa | number \| null | Operational commission % |
| fecha_contrato | fecha_contrato | string \| null | ISO date format |
| vigencia_meses | vigencia_meses | number \| null | Duration in months |
| rfc_broker | rfc_broker | string \| null | Mexican tax ID |
| cuenta_bancaria | cuenta_bancaria | string \| null | CLABE account number |
| banco | banco | string \| null | Bank name |
| extraction_method | extraction_method | 'standard' \| 'ai' | Which method was used |
| extraction_confidence | extraction_confidence | number \| null | 0-1 confidence score |
| raw_text_preview | raw_text_preview | string \| null | First 500 chars for debug |

## Implementation Plan

### Phase 1: Foundation
- Add `BrokerContractData` DTO to `alianzas_dtos.py`
- Add `BrokerContractData` TypeScript interface to `alianzas.ts`
- Create `contract_extractor_service.py` with regex patterns

### Phase 2: Core Implementation
- Implement DOCX text extraction using python-docx
- Implement PDF text extraction using PyMuPDF (fitz)
- Implement regex pattern matching for both contract versions
- Add API endpoint `/brokers/extract-contract` to alianzas_routes.py
- Add `extractContract` method to alianzasService.ts
- Create `FKContractUpload.tsx` component with drag & drop

### Phase 3: Integration
- Integrate `FKContractUpload` into `FKBrokerForm.tsx`
- Add form field population from extracted data
- Add extraction confidence indicator
- Implement error handling with AI extraction suggestion

## Step by Step Tasks

### Step 1: Add Backend DTO
Add `BrokerContractData` Pydantic model to `backend/src/interface/alianzas_dtos.py`:
- Include all extraction fields (nombre_broker, porcentaje_comision_apertura, etc.)
- Add extraction_method and extraction_confidence fields
- Add raw_text_preview for debugging
- Use Optional types with None defaults

### Step 2: Create Contract Extractor Service
Create `backend/src/core/servicios/contract_extractor_service.py`:
- Define regex patterns for both contract versions (Marzo 2024 and Current)
- Implement `extract_from_docx(file_bytes)` using python-docx
- Implement `extract_from_pdf(file_bytes)` using PyMuPDF (fitz)
- Implement `_extract_with_patterns(text)` for regex extraction
- Calculate confidence score based on fields found
- Include proper logging and error handling

### Step 3: Add API Endpoint
Add endpoint to `backend/src/adapter/rest/alianzas_routes.py`:
- `POST /api/alianzas/brokers/extract-contract`
- Accept `UploadFile` parameter for contract file
- Validate file type (PDF, DOCX only) and size (<10MB)
- Call ContractExtractorService based on file extension
- Return `BrokerContractData` response
- Handle errors with clear messages

### Step 4: Add Frontend TypeScript Types
Add to `frontend/src/types/alianzas.ts`:
- `BrokerContractData` interface matching backend DTO
- `ExtractionMethod` type literal

### Step 5: Add Frontend Service Method
Add to `frontend/src/services/alianzasService.ts`:
- `extractContract(file: File)` method
- Use FormData for file upload
- Return typed `BrokerContractData` response

### Step 6: Create FKContractUpload Component
Create `frontend/src/components/alianzas/FKContractUpload.tsx`:
- Props: `onExtracted`, `onError`, `disabled`
- Drag & drop zone accepting .pdf and .docx
- Loading state during extraction
- Preview of extracted data in a card layout
- Editable fields to correct extraction errors
- Confidence indicator (progress bar or percentage)
- "Aplicar al Formulario" button
- "Usar Extracción IA" suggestion on failure

### Step 7: Integrate with FKBrokerForm
Update `frontend/src/components/alianzas/FKBrokerForm.tsx`:
- Add "Importar desde Contrato" collapsible section at the top
- Include `FKContractUpload` component
- Handle `onExtracted` callback to populate form fields
- Map extracted data to form field names:
  - `porcentaje_comision_apertura` → `porcentaje_apertura`
  - `porcentaje_comision_operativa` → `porcentaje_operativa`
  - `cuenta_bancaria` → `cuenta_bancaria`
  - `banco` → `banco`
  - `rfc_broker` → `rfc`
  - `fecha_contrato` → `fecha_contrato`
- Show toast/snackbar on successful extraction

### Step 8: Create E2E Test File
Create `.claude/commands/e2e/test_broker_contract_extraction.md`:
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for format
- Define test for contract upload and extraction
- Include login step (alianzas role)
- Navigate to broker management
- Upload sample contract file
- Verify extracted data appears
- Verify form fields are populated
- Capture screenshots at each step

### Step 9: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests
- Test `ContractExtractorService._extract_with_patterns()` with sample texts from both contract versions
- Test PDF text extraction with mock PyMuPDF
- Test DOCX text extraction with mock python-docx
- Test confidence calculation logic
- Test error handling for unsupported file types

### Edge Cases
- Empty PDF/DOCX files
- Scanned PDF with no selectable text (should return low confidence)
- Contract with missing fields (partial extraction)
- Very large files (>10MB rejection)
- Malformed files
- Contract with unusual number formats (e.g., "60,5%" vs "60.5%")
- Multiple matching patterns (should use first/best match)

## Acceptance Criteria
- [x] Can upload DOCX contract and extract commission percentages
- [x] Can upload PDF contract with text and extract data
- [x] Both contract versions (Marzo 2024, Actual) are recognized
- [x] Extracted data populates broker form
- [x] User can edit extracted values before saving
- [x] Clear error messages when extraction fails
- [x] Suggests AI extraction as alternative when standard fails
- [x] File size limit enforced (10MB)
- [x] Only PDF and DOCX files accepted
- [x] Confidence score displayed to user

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
   Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_contract_extraction.md` to validate this functionality works.

## Notes

### Dependencies
- **Backend**: No new pip packages needed. Already has:
  - `python-docx>=1.0.0` for DOCX text extraction
  - `PyMuPDF>=1.23.0` for PDF text extraction
- **Frontend**: No new npm packages needed. Using existing MUI components.

### Future Enhancements
- Add AI-powered extraction endpoint (`/extract-contract-ai`) for scanned documents
- Store extraction history for training/improvement
- Support additional contract formats (images, scanned PDFs via OCR)
- Add batch contract processing

### Pattern Matching Notes
- Patterns are case-insensitive for flexibility
- Multiple patterns per field allow version compatibility
- Confidence is calculated as: `(fields_found / total_fields) * 100`
- Raw text preview (first 500 chars) helps debug extraction issues

## Plan Quality Checklist

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified (none needed)
- [x] E2E test file task included (Step 8)
- [x] All external dependencies listed in Notes (none needed)

### Category-Specific Completeness
**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete (extraction patterns)
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for service methods

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
