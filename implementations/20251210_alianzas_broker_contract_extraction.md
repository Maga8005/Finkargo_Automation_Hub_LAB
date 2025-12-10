# Implementation Report: Broker Contract Data Extraction

**Date:** 2025-12-10
**Feature:** Broker Contract Data Extraction
**Module:** Alianzas

## Summary

Implemented a contract data extraction system for broker contracts using regex patterns. The feature allows Alianzas users to upload broker contracts (PDF or DOCX) and automatically extract key commercial terms like commission percentages, bank information, and contract dates.

## Work Completed

### Backend

- **Added `BrokerContractData` DTO** (`backend/src/interface/alianzas_dtos.py`)
  - Added `ExtractionMethod` enum (`standard`, `ai`)
  - Added `BrokerContractData` Pydantic model with all extraction fields
  - Fields: `nombre_broker`, `porcentaje_comision_apertura`, `porcentaje_comision_operativa`, `fecha_contrato`, `vigencia_meses`, `rfc_broker`, `cuenta_bancaria`, `banco`, `extraction_confidence`, `raw_text_preview`

- **Created `ContractExtractorService`** (`backend/src/core/servicios/contract_extractor_service.py`)
  - Regex patterns for both contract versions (Marzo 2024 and Current)
  - `extract_from_docx()` - Extract text from DOCX using python-docx
  - `extract_from_pdf()` - Extract text from PDF using PyMuPDF (fitz)
  - `_extract_with_patterns()` - Apply regex patterns to extract fields
  - Confidence score calculation based on fields found
  - Date parsing for both numeric (DD/MM/YYYY) and Spanish formats

- **Added API endpoint** (`backend/src/adapter/rest/alianzas_routes.py`)
  - `POST /api/alianzas/brokers/extract-contract`
  - File upload validation (PDF, DOCX only, 10MB max)
  - Returns `BrokerContractData` with extracted fields and confidence

### Frontend

- **Added TypeScript types** (`frontend/src/types/alianzas.ts`)
  - `ExtractionMethod` type and constants
  - `BrokerContractData` interface

- **Added service method** (`frontend/src/services/alianzasService.ts`)
  - `extractContract(file: File)` - Uploads file and returns extracted data

- **Created `FKContractUpload` component** (`frontend/src/components/alianzas/FKContractUpload.tsx`)
  - Drag & drop file upload zone
  - File type and size validation
  - Loading state during extraction
  - Preview card with editable extracted fields
  - Confidence indicator (color-coded chip)
  - "Aplicar al Formulario" button

- **Integrated with `FKBrokerForm`** (`frontend/src/components/alianzas/FKBrokerForm.tsx`)
  - Added collapsible "Importar desde Contrato" accordion section
  - Maps extracted data to form fields
  - Snackbar notifications for success/error
  - Only shown when creating new broker (not editing)

### E2E Test

- **Created E2E test file** (`.claude/commands/e2e/test_broker_contract_extraction.md`)
  - Tests login with alianzas role
  - Tests navigation to broker management
  - Tests file upload validation
  - Tests extraction and form population

## Files Changed

| File | Change Type | Lines |
|------|-------------|-------|
| `backend/src/interface/alianzas_dtos.py` | Modified | +40 |
| `backend/src/core/servicios/contract_extractor_service.py` | Created | +392 |
| `backend/src/adapter/rest/alianzas_routes.py` | Modified | +91 |
| `frontend/src/types/alianzas.ts` | Modified | +29 |
| `frontend/src/services/alianzasService.ts` | Modified | +22 |
| `frontend/src/components/alianzas/FKContractUpload.tsx` | Created | +534 |
| `frontend/src/components/alianzas/FKBrokerForm.tsx` | Modified | +60 |
| `.claude/commands/e2e/test_broker_contract_extraction.md` | Created | +120 |

**Total:** ~1,288 lines added/modified

## Discrepancies Found

None. The plan was accurate and all assumptions were correct:
- Existing files were found at the expected locations
- No new database tables needed
- PyMuPDF (fitz) and python-docx were already in requirements.txt
- Field naming conventions matched (snake_case in both frontend and backend)

## Validation Results

- **Frontend Linting:** Passed (no errors)
- **TypeScript Check:** Passed (no errors)
- **Frontend Build:** Passed (build successful)
- **Backend Imports:** Passed (all imports successful)
- **Backend Server:** Running without errors

## Acceptance Criteria Status

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

## Notes

- AI extraction is mentioned in UI but disabled (marked as "próximamente")
- The extraction uses case-insensitive regex patterns for flexibility
- Confidence is calculated as `(fields_found / total_fields)` where total_fields = 8
- Raw text preview (first 500 chars) is included for debugging
