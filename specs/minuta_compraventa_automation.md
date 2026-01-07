# Feature: Minuta Compraventa Contract Automation

## Feature Description

Automate the generation of "Minuta Compraventa" (Sales Contract) documents for real estate transactions in Bolivia. This contract type requires extracting data from three PDF source documents (Cédula de Identidad, Folio Real Departamento, Folio Real Parqueo) and combining them with user-provided form data (pricing, dates, tax information) to populate a Word template and generate the final contract document.

This is a new contract type in the existing Legal Contract Automation system, following the established patterns from Activos, Otrosí, and Inventario Bodega contracts, but with a unique multi-PDF extraction workflow rather than client database lookup.

## User Story

As an Operations team member
I want to upload property and buyer documents and fill in additional details
So that I can automatically generate a Minuta Compraventa contract without manual data entry

## Problem Statement

Currently, generating Minuta Compraventa contracts requires manual extraction of data from multiple PDF documents (ID cards, property registrations) and manual entry into a Word template. This process is error-prone, time-consuming (15-30 minutes per contract), and requires understanding of where each piece of information should be placed in the template.

## Solution Statement

Create an automated workflow that:
1. Accepts three PDF uploads (Cédula de Identidad, Folio Real Departamento, Folio Real Parqueo)
2. Extracts structured data from each PDF using PyMuPDF text extraction with regex patterns
3. Presents a form for user to input additional data (pricing, dates, tax year)
4. Combines extracted and user-provided data to populate the Word template
5. Generates the final contract document for legal review
6. Follows the existing contract review and approval workflow

## Relevant Files

Use these files to implement the feature:

### Backend Files (Existing - Modify)

- `backend/src/interface/legal_dtos.py` - Add new contract type enum value `MINUTA_COMPRAVENTA` and DTOs for minuta-specific data (BuyerData, PropertyData, MinutaFormData)
- `backend/src/core/servicios/document_service.py` - Add `generate_minuta_compraventa_document()` method and `_prepare_minuta_replacements()` helper
- `backend/src/adapter/rest/operations_routes.py` - Update `/contracts/generate` endpoint to handle minuta_compraventa type with multiple file uploads
- `backend/src/repositorio/contract_repository.py` - Update `generate_contract_id()` to support "MIN" prefix for minuta contracts

### Backend Files (New)

- `backend/src/core/servicios/minuta_parser_service.py` - New service for parsing Bolivian ID cards (Cédula) and Folio Real property documents
- `backend/database/migration_add_minuta_compraventa_support.sql` - Database migration for new contract type

### Frontend Files (Existing - Modify)

- `frontend/src/pages/operations/OperationsDashboard.tsx` - Add new tab for Minuta Compraventa
- `frontend/src/services/operationsService.ts` - Add `requestMinutaCompraventaGeneration()` method
- `frontend/src/types/legal.ts` - Add TypeScript types for minuta data structures
- `frontend/src/components/forms/FKApprovedContracts.tsx` - Add purple badge for minuta_compraventa type
- `frontend/src/components/forms/FKReviewQueue.tsx` - Add purple badge for minuta_compraventa type

### Frontend Files (New)

- `frontend/src/components/forms/FKMinutaCompraventaRequest.tsx` - New form component with multi-file upload and form fields

### Template Files

- `backend/templates/Minuta Compraventa GT.docx` - Copy from `Example FIles for Reqs/` to backend templates directory (needs placeholder conversion)

### New Files

#### Backend
- `backend/src/core/servicios/minuta_parser_service.py` - PDF parsing service for Bolivian documents
- `backend/database/migration_add_minuta_compraventa_support.sql` - Database migration

#### Frontend
- `frontend/src/components/forms/FKMinutaCompraventaRequest.tsx` - Main request form component

## Implementation Plan

### Phase 1: Foundation

1. **Analyze PDF Document Structures**: Study the three source PDF types to identify extraction patterns:
   - Cédula de Identidad: Extract nombre completo, número de cédula, domicilio, zona, ciudad
   - Folio Real Departamento: Extract matrícula, superficie, ubicación, piso/planta, gravámenes
   - Folio Real Parqueo: Extract matrícula, superficie, nivel, gravámenes

2. **Convert Template Placeholders**: The current template uses underscore placeholders (`_____`) instead of bracket placeholders (`[placeholder]`). Need to update the template to use bracket placeholders that the DocumentService can process.

3. **Database Setup**: Create migration to add minuta_compraventa contract type and MIN-YYYY-NNN ID sequence.

### Phase 2: Core Implementation

1. **Backend PDF Parser Service**: Create `MinutaParserService` class with methods:
   - `parse_cedula_pdf()` - Extract buyer data from Bolivian ID card
   - `parse_folio_real_pdf()` - Extract property data from Folio Real documents

2. **Backend DTOs**: Add new Pydantic models:
   - `BuyerData` - Extracted from Cédula
   - `PropertyData` - Extracted from Folio Real (both Departamento and Parqueo)
   - `MinutaFormData` - User-provided data (prices, dates, tax year)
   - `MinutaContractRequest` - Combined request with all data sources

3. **Document Service**: Add `generate_minuta_compraventa_document()` with specific placeholder mappings for this contract type.

4. **Frontend Form Component**: Create `FKMinutaCompraventaRequest.tsx` with:
   - Three file upload zones (Cédula, Departamento, Parqueo PDFs)
   - Form fields for price, price breakdown, date, tax year
   - Preview of extracted data before submission

### Phase 3: Integration

1. **Operations Routes**: Extend the existing `/contracts/generate` endpoint to:
   - Accept `contract_type: 'minuta_compraventa'`
   - Handle three file uploads (`cedula_file`, `departamento_file`, `parqueo_file`)
   - Parse all three PDFs and combine with form data
   - Generate contract with appropriate ID (MIN-2025-XXX)

2. **Frontend Integration**:
   - Add new tab to Operations Dashboard
   - Add badge color (purple/secondary) for minuta_compraventa type
   - Update operations service with new API method

3. **Review Workflow**: The generated contract will follow the existing legal review workflow (under_review → approved/rejected).

## Step by Step Tasks

### Step 1: Prepare Template File
- Copy `Example FIles for Reqs/Minuta Compraventa GT.docx` to `backend/templates/`
- Convert underscore placeholders to bracket placeholders matching the field mapping document
- Placeholders to create:
  - `[NOMBRE_COMPRADOR]` - Full name from Cédula
  - `[CI_COMPRADOR]` - ID number from Cédula
  - `[DOMICILIO_COMPRADOR]` - Address from Cédula
  - `[ZONA_COMPRADOR]` - Zone from Cédula
  - `[CIUDAD_COMPRADOR]` - City from Cédula
  - `[PRECIO_TOTAL]` - Total price (form input)
  - `[PRECIO_LETRAS]` - Price in words (generated)
  - `[PRECIO_DEPTO]` - Department price (form input)
  - `[PRECIO_PARQUEO]` - Parking price (form input)
  - `[MATRICULA_DEPTO]` - From Folio Real Departamento
  - `[SUPERFICIE_DEPTO]` - From Folio Real Departamento
  - `[PISO_DEPTO]` - From Folio Real Departamento
  - `[NUMERO_DEPTO]` - From Folio Real Departamento
  - `[MATRICULA_PARQUEO]` - From Folio Real Parqueo
  - `[SUPERFICIE_PARQUEO]` - From Folio Real Parqueo
  - `[NIVEL_PARQUEO]` - From Folio Real Parqueo
  - `[NUMERO_PARQUEO]` - From Folio Real Parqueo
  - `[GESTION_IMPBI_PAGADO]` - Tax year paid (form input)
  - `[GESTION_IMPBI_COMPRADOR]` - Tax year for buyer (form input)
  - `[DIA_FIRMA]` - Day of signature (form input)
  - `[MES_FIRMA]` - Month of signature (form input)
  - `[ANIO_FIRMA]` - Year of signature (form input)

### Step 2: Create Database Migration
- Create `backend/database/migration_add_minuta_compraventa_support.sql`:
  - Insert template record for minuta_compraventa
  - Update `generate_contract_id()` function to add MIN prefix
  - Initialize sequence for minuta_compraventa in contract_id_sequence table

### Step 3: Create Backend DTOs
- Update `backend/src/interface/legal_dtos.py`:
  - Add `MINUTA_COMPRAVENTA = "minuta_compraventa"` to ContractType enum
  - Add `BuyerData` model for Cédula extracted data
  - Add `PropertyData` model for Folio Real extracted data
  - Add `MinutaFormData` model for user-provided form fields
  - Add `MinutaDataSnapshot` model that combines all data sources

### Step 4: Create Minuta Parser Service
- Create `backend/src/core/servicios/minuta_parser_service.py`:
  - `MinutaParserService` class
  - `parse_cedula_pdf(pdf_bytes: bytes) -> BuyerData` method:
    - Extract from image-based Bolivian ID card (may need OCR consideration)
    - Fields: nombre completo, número CI, domicilio, zona, ciudad
  - `parse_folio_real_pdf(pdf_bytes: bytes, property_type: str) -> PropertyData` method:
    - Extract from Folio Real document (text-based PDF)
    - Fields: matrícula, superficie, ubicación, nivel/piso, gravámenes

### Step 5: Update Document Service
- Add to `backend/src/core/servicios/document_service.py`:
  - `generate_minuta_compraventa_document()` method
  - `_prepare_minuta_replacements()` helper method
  - Map all placeholder values from buyer data, property data, and form data

### Step 6: Update Operations Routes
- Modify `backend/src/adapter/rest/operations_routes.py`:
  - Update `/contracts/generate` endpoint signature to accept optional files:
    - `cedula_file: Optional[UploadFile]`
    - `departamento_file: Optional[UploadFile]`
    - `parqueo_file: Optional[UploadFile]`
  - Add form fields for minuta-specific data:
    - `precio_total: Optional[str]`
    - `precio_departamento: Optional[str]`
    - `precio_parqueo: Optional[str]`
    - `gestion_impbi_pagado: Optional[str]`
    - `gestion_impbi_comprador: Optional[str]`
    - `dia_firma: Optional[str]`
    - `mes_firma: Optional[str]`
    - `anio_firma: Optional[str]`
  - Add logic to handle minuta_compraventa contract type

### Step 7: Create Frontend Types
- Update `frontend/src/types/legal.ts`:
  - Add `minuta_compraventa` to ContractGenerationRequest contract_type
  - Add `BuyerData` interface
  - Add `PropertyData` interface
  - Add `MinutaFormData` interface
  - Add `MinutaContractRequest` interface

### Step 8: Update Operations Service
- Add to `frontend/src/services/operationsService.ts`:
  - `requestMinutaCompraventaGeneration()` method that:
    - Accepts three PDF files
    - Accepts form data object
    - Creates FormData with all files and fields
    - Posts to `/operations/contracts/generate`

### Step 9: Create FKMinutaCompraventaRequest Component
- Create `frontend/src/components/forms/FKMinutaCompraventaRequest.tsx`:
  - File upload section with three zones:
    - Cédula de Identidad (required)
    - Folio Real Departamento (required)
    - Folio Real Parqueo (required)
  - Form section with fields:
    - Precio Total (currency input)
    - Precio Departamento (currency input)
    - Precio Parqueo (currency input)
    - Gestión IMPBI Pagado (year selector)
    - Gestión IMPBI Comprador (year selector)
    - Fecha de Firma (date picker)
  - Preview section showing extracted data (optional enhancement)
  - Submit button with loading state
  - Success/error alerts

### Step 10: Update Operations Dashboard
- Update `frontend/src/pages/operations/OperationsDashboard.tsx`:
  - Import `FKMinutaCompraventaRequest` component
  - Import `HomeWork` or `Gavel` icon for tab
  - Add new Tab: "Solicitar Minuta Compraventa"
  - Add new TabPanel with info card (purple theme) and form component
  - Update tab indices for existing "Contratos Aprobados" tab

### Step 11: Update Badge Helpers
- Update `frontend/src/components/forms/FKReviewQueue.tsx`:
  - Add case for `minuta_compraventa` in `getContractTypeBadge()`
  - Return `{ label: 'Minuta Compraventa', color: 'secondary' }`
- Update `frontend/src/components/forms/FKApprovedContracts.tsx`:
  - Add same badge case for `minuta_compraventa`

### Step 12: Run Tests and Validate
- Run backend pytest tests
- Run frontend TypeScript compilation
- Run frontend lint
- Manual end-to-end testing with sample PDFs

## Testing Strategy

### Unit Tests

**Backend Tests:**
- Test `MinutaParserService.parse_cedula_pdf()` with sample Cédula PDF
- Test `MinutaParserService.parse_folio_real_pdf()` with sample Departamento PDF
- Test `MinutaParserService.parse_folio_real_pdf()` with sample Parqueo PDF
- Test `DocumentService.generate_minuta_compraventa_document()` with mock data
- Test `_prepare_minuta_replacements()` with complete data snapshot
- Test contract ID generation returns MIN-YYYY-NNN format

**Frontend Tests:**
- Test `FKMinutaCompraventaRequest` component renders correctly
- Test file upload validation (PDF type, size limits)
- Test form validation (required fields)
- Test `requestMinutaCompraventaGeneration()` constructs correct FormData

### Integration Tests

**API Endpoint Tests:**
- Test POST `/operations/contracts/generate` with contract_type=minuta_compraventa
- Test file upload handling with three PDF files
- Test form data parsing
- Test error responses for missing files
- Test error responses for invalid file types
- Test contract creation in database
- Test generated contract ID format

**End-to-End Tests:**
- Navigate to Operations Dashboard
- Click Minuta Compraventa tab
- Upload three sample PDFs
- Fill form fields
- Submit request
- Verify success message with contract ID
- Navigate to Legal Review Queue
- Verify contract appears with purple badge
- Approve contract
- Navigate to Approved Contracts
- Download PDF and verify content

### Edge Cases

- Missing required PDF files
- Invalid PDF format (corrupted file)
- PDF with unreadable/extractable text (scanned image without OCR)
- Large PDF files (>10MB)
- Form fields with special characters
- Very large price values (formatting)
- Year values outside valid range
- Network timeout during file upload
- Concurrent requests for same contract
- Template file missing from backend

## Acceptance Criteria

1. **Tab Visibility**: New "Solicitar Minuta Compraventa" tab appears in Operations Dashboard between "Solicitar Inventario Bodega" and "Contratos Aprobados"
2. **File Upload**: Users can upload three PDF files (Cédula, Departamento, Parqueo) with validation
3. **Form Completion**: Users can fill in pricing, date, and tax year information
4. **Contract Generation**: System generates contract with ID format MIN-YYYY-NNN
5. **Data Extraction**: Buyer and property data is correctly extracted from uploaded PDFs
6. **Template Population**: Generated DOCX contains all extracted and form data in correct positions
7. **Review Workflow**: Generated contracts appear in Legal Review Queue with purple badge
8. **Approval Process**: Legal can approve/reject contracts following existing workflow
9. **PDF Download**: Approved contracts can be downloaded as PDF
10. **Error Handling**: Clear error messages for invalid uploads or extraction failures

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `cd /Users/danielrestrepo/Finkargo_Automation_Hub/backend && source venv/bin/activate && python -m pytest tests/ -v` - Run backend tests
- `cd /Users/danielrestrepo/Finkargo_Automation_Hub/frontend && npm run build` - Build frontend to verify TypeScript compilation
- `cd /Users/danielrestrepo/Finkargo_Automation_Hub/frontend && npm run lint` - Run frontend linting
- `cd /Users/danielrestrepo/Finkargo_Automation_Hub && ./scripts/start-dev.sh` - Start development servers
- Manual testing: Upload sample PDFs and verify contract generation

## Notes

### PDF Extraction Challenges

The Bolivian Cédula de Identidad PDF appears to be an image-based document (photo of ID card). This may require:
1. **OCR Integration**: Consider using pytesseract or similar OCR library for text extraction
2. **Alternative Approach**: The MRZ (Machine Readable Zone) at the bottom of the ID contains structured data that can be parsed with regex
3. **Manual Entry Fallback**: If OCR is unreliable, provide form fields for manual entry with PDF preview

The Folio Real documents appear to be text-based PDFs, which should be extractable with PyMuPDF's standard text extraction.

### Template Conversion

The current template uses underscore placeholders (`_____`) which is non-standard. The implementation should:
1. Create a copy of the template with bracket placeholders
2. Store converted template in `backend/templates/Minuta Compraventa GT.docx`
3. Keep original in `Example FIles for Reqs/` for reference

### Color Theme

Following the established pattern:
- Activos: Blue (info)
- Otrosí: Orange (warning)
- Inventario Bodega: Green (success)
- **Minuta Compraventa: Purple (secondary)** - New

### Data Storage

Unlike other contract types that pull from the `clients` table, Minuta Compraventa:
- Does NOT use the clients table
- Stores all data in `data_snapshot` JSON field
- Includes buyer data, both property data, and form data
- No client_id foreign key (nullable for this type)

### Future Enhancements

1. **Data Preview**: Show extracted data before submission for user verification
2. **OCR Improvements**: Integrate cloud OCR service for better ID card extraction
3. **Bulk Generation**: Support multiple contracts from Excel upload
4. **Template Variants**: Support different Minuta templates for different cities/notaries
5. **Digital Signatures**: Integration with DocuSign or similar for electronic signing
