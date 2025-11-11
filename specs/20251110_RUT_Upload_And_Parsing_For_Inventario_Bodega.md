# Feature: RUT Document Upload and Parsing for Inventario Bodega de 3ro Contracts

## Feature Description
Implement RUT (Registro Único Tributario) document upload and automated field extraction for Inventario Bodega de 3ro contracts. The RUT document contains critical custodian information that must be populated in the contract template, including the custodian operator's company name, NIT, city, legal representative details, email, and ID number. This feature allows Operations users to upload a PDF RUT document when requesting an Inventario Bodega contract, automatically extracting and validating custodian data before contract generation.

The feature adds:
- PDF file upload component in the Inventario Bodega request form
- Backend RUT parsing service using PyMuPDF for text extraction
- Field mapping configuration for extracting specific RUT fields
- Data validation to ensure all required custodian fields are present
- Extended contract data snapshot to include custodian information
- Updated document template replacement logic to populate custodian placeholders
- Error handling for missing or malformed RUT documents

## User Story
**As an Operations team member**
I want to upload a RUT document when requesting an Inventario Bodega de 3ro contract
So that the custodian operator information is automatically extracted and populated in the contract without manual data entry, reducing errors and processing time

**As a Legal team member**
I want the Inventario Bodega contracts to include accurate custodian information from official RUT documents
So that I can review contracts with verified third-party warehouse operator details and ensure compliance with legal requirements

## Problem Statement
The Inventario Bodega de 3ro contract template contains several placeholders for custodian operator information that cannot be sourced from the client database:
- **[NOMBRE DEL OPERADOR CUSTODIO]** - Custodian company legal name
- **[nombre de la ciudad de domicilio del Operador Custodio]** - Custodian city
- **[NIT Operador Custodio]** - Custodian tax ID with verification digit
- **[nombre del representante legal del Operador Custodio]** - Custodian legal representative full name
- **[e-mail del operador custodio]** - Custodian contact email
- **[CC representante legal del Operador Custodio]** - Custodian legal rep ID number

Currently, these fields are left blank or filled with placeholder text, requiring manual intervention. This creates:
- **Data Entry Errors**: Manual transcription from RUT documents is error-prone
- **Legal Compliance Risk**: Incorrect custodian NIT or legal representative invalidates contracts
- **Processing Delays**: Operations must request custodian info from clients, adding 1-2 days
- **Inconsistent Format**: Different users format company names and addresses differently
- **No Audit Trail**: No record of which RUT document was used for verification

The RUT document is a standardized Colombian tax registration form issued by DIAN (tax authority) that contains all required custodian information in a structured format with field numbers.

## Solution Statement
Implement a RUT document upload and parsing system that:

1. **Frontend Upload Component**: Add file upload field to FKInventarioRequest component with PDF validation
2. **Backend RUT Parser Service**: Create `RUTParserService` using PyMuPDF to extract text from specific field locations in the RUT PDF
3. **Field Mapping Configuration**: Define `RUT_FIELD_MAPPING` dictionary mapping contract placeholders to RUT field numbers and extraction logic
4. **Data Extraction Logic**:
   - Extract company name from field 35 (Razón social)
   - Extract city from field 40 (Ciudad/Municipio)
   - Extract NIT from field 5 + verification digit from field 6
   - Extract legal representative name from fields 104-107 (apellidos + nombres) for first REPRS LEGAL PRIN entry
   - Extract email from field 42 (Correo electrónico)
   - Extract legal rep ID from field 101 (Número de identificación)
5. **Validation Layer**: Verify all required fields are extracted before contract generation, return clear error messages if parsing fails
6. **Extended Data Snapshot**: Add custodian fields to contract data snapshot for template replacement
7. **Template Replacement**: Update `_prepare_inventario_bodega_replacements()` to include custodian placeholders

This solution leverages existing PDF processing libraries (PyMuPDF already in requirements.txt), follows Clean Architecture patterns, and provides a seamless user experience.

## Relevant Files

### Backend - Core Service Layer
- **`backend/src/core/servicios/rut_parser_service.py`** - NEW SERVICE
  - Core business logic for RUT PDF parsing
  - Field extraction using PyMuPDF text search
  - Validation logic for required fields
  - Handles multi-part fields (full name from 4 fields, NIT with DV)

- **`backend/src/core/servicios/document_service.py`** - MODIFY
  - Add `_prepare_inventario_bodega_replacements()` method (currently reuses `_prepare_replacements()`)
  - Include custodian field mappings from RUT data in replacement dictionary
  - Lines 181-241 contain `generate_inventario_bodega_document()` method

- **`backend/src/core/servicios/contract_service.py`** - MODIFY
  - Update `generate_contract()` method to accept optional RUT data parameter
  - Pass RUT data to contract data snapshot for inventario_bodega type
  - Lines 43-124 contain contract generation logic

### Backend - Interface/DTOs
- **`backend/src/interface/legal_dtos.py`** - MODIFY
  - Add `CustodianData` Pydantic model for RUT extracted fields
  - Add optional `rut_data: Optional[CustodianData]` to `ContractGenerationRequest`
  - Add optional `rut_file: Optional[UploadFile]` to request (or use separate endpoint)

### Backend - API Routes
- **`backend/src/adapter/rest/operations_routes.py`** - MODIFY
  - Update `/contracts/generate` endpoint to accept multipart/form-data with PDF file
  - Add RUT file validation (PDF only, max 5MB)
  - Call RUT parser service before contract generation
  - Handle parsing errors with 400 Bad Request responses
  - Lines 59-79 contain contract generation endpoint

### Frontend - Components
- **`frontend/src/components/forms/FKInventarioRequest.tsx`** - MODIFY
  - Add file upload field using MUI Button + input[type=file]
  - Add file validation (PDF only, max 5MB, show preview/filename)
  - Update API call to send multipart/form-data with both client NIT and RUT file
  - Display parsing errors if RUT extraction fails
  - Show extracted custodian data preview before submission

### Frontend - Services
- **`frontend/src/services/operationsService.ts`** - MODIFY
  - Update `requestInventarioBodegaGeneration()` to accept File parameter
  - Create FormData object with client_nit and rut_file
  - Set proper Content-Type header for multipart upload
  - Handle 400 errors from RUT parsing failures

### Frontend - Types
- **`frontend/src/types/legal.ts`** - MODIFY
  - Add `CustodianData` interface matching backend DTO
  - Update `ContractGenerationRequest` to include optional custodian_data

### Templates
- **`backend/templates/FK COL - GM - Inventario Bodega de 3ro.docx`** - VERIFY
  - Confirm template contains custodian placeholders
  - Verify exact placeholder syntax matches mapping

### New Files

#### Backend
- **`backend/src/core/servicios/rut_parser_service.py`** - RUT parsing service
  - `RUTParserService` class with `parse_rut_pdf(pdf_bytes: bytes) -> CustodianData` method
  - `RUT_FIELD_MAPPING` configuration dictionary
  - Field extraction helpers for text, NIT, full name, email
  - Validation logic ensuring all required fields present
  - Clear error messages for debugging extraction failures

#### Tests
- **`backend/tests/test_rut_parser_service.py`** - NEW TEST FILE
  - Test RUT parsing with sample RUT document
  - Test field extraction accuracy
  - Test validation for missing fields
  - Test error handling for malformed PDFs
  - Test NIT formatting with verification digit

### Reference Documents
- **`backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf`** - Sample RUT for testing and field mapping reference

## Implementation Plan

### Phase 1: Foundation - RUT Parser Service
**Objective**: Build core RUT parsing functionality with field extraction and validation

1. Create RUT parser service module with PyMuPDF integration
2. Define RUT_FIELD_MAPPING configuration based on DIAN standard form
3. Implement field extraction logic for text, NIT, full name, email fields
4. Add validation to ensure all 6 required custodian fields are extracted
5. Create CustodianData Pydantic model for type safety
6. Write unit tests with sample RUT document

### Phase 2: Core Implementation - API Integration
**Objective**: Integrate RUT parsing into contract generation workflow

1. Update ContractGenerationRequest DTO to accept RUT file upload
2. Modify operations routes to handle multipart/form-data uploads
3. Add file validation (PDF type, size limit)
4. Call RUT parser before contract generation
5. Pass custodian data to contract service data snapshot
6. Update document service to include custodian replacements
7. Test end-to-end contract generation with RUT upload

### Phase 3: Integration - Frontend Upload Component
**Objective**: Build user interface for RUT upload with preview and validation

1. Add file upload UI to FKInventarioRequest component
2. Implement file validation on frontend (PDF, 5MB limit)
3. Show file preview with extracted custodian data
4. Update operations service to send multipart form data
5. Display parsing errors with helpful messages
6. Test full user workflow from upload to contract approval

## Step by Step Tasks

### Step 1: Create RUT Parser Service Foundation
- Create `backend/src/core/servicios/rut_parser_service.py`
- Import PyMuPDF (fitz), logging, typing modules
- Define `CustodianData` Pydantic model with 6 required fields:
  - `nombre_operador_custodio: str`
  - `ciudad_domicilio_custodio: str`
  - `nit_operador_custodio: str` (includes DV)
  - `nombre_representante_legal_custodio: str`
  - `email_operador_custodio: str`
  - `cc_representante_legal_custodio: str`
- Create `RUTParserService` class skeleton

### Step 2: Define RUT Field Mapping Configuration
- Inside `rut_parser_service.py`, define `RUT_FIELD_MAPPING` dictionary:
```python
RUT_FIELD_MAPPING = {
    "NOMBRE_DEL_OPERADOR_CUSTODIO": {
        "field_number": "35",
        "field_name": "Razón social",
        "page": 1,
        "type": "text",
        "description": "Company legal name"
    },
    "CIUDAD_DOMICILIO": {
        "field_number": "40",
        "field_name": "Ciudad/Municipio",
        "page": 1,
        "type": "text",
        "description": "City/Municipality where company is located"
    },
    "NIT_OPERADOR_CUSTODIO": {
        "field_number": "5",
        "field_name": "Número de Identificación Tributaria (NIT)",
        "page": 1,
        "type": "nit",
        "includes_dv": True,
        "dv_field": "6",
        "description": "Tax identification number with verification digit"
    },
    "NOMBRE_REPRESENTANTE_LEGAL": {
        "field_numbers": ["104", "105", "106", "107"],
        "field_names": ["Primer apellido", "Segundo apellido", "Primer nombre", "Otros nombres"],
        "page": 3,
        "type": "full_name",
        "representation_type": "REPRS LEGAL PRIN",
        "description": "Legal representative full name (first rep listed)"
    },
    "EMAIL_OPERADOR_CUSTODIO": {
        "field_number": "42",
        "field_name": "Correo electrónico",
        "page": 1,
        "type": "email",
        "description": "Company contact email"
    },
    "CC_REPRESENTANTE_LEGAL": {
        "field_number": "101",
        "field_name": "Número de identificación",
        "page": 3,
        "type": "text",
        "representation_type": "REPRS LEGAL PRIN",
        "description": "Legal representative ID number (cedula)"
    }
}
```

### Step 3: Implement Core RUT Parsing Method
- Implement `parse_rut_pdf(self, pdf_bytes: bytes) -> CustodianData` method
- Open PDF with `fitz.open(stream=pdf_bytes, filetype="pdf")`
- Extract text from all 3 pages
- Parse each field using field mapping configuration
- Log extraction results for debugging
- Validate all required fields are present
- Return `CustodianData` object
- Raise `ValueError` with clear message if parsing fails

### Step 4: Implement Field Extraction Helpers
- Create `_extract_text_field(page, field_label: str) -> str` method
  - Search for field label text on page
  - Extract value after label (usually on same line)
  - Strip whitespace and return value
- Create `_extract_nit_with_dv(page) -> str` method
  - Extract NIT digits from field 5 (format: "9 0 0 9 8 9 9 2 5")
  - Extract DV from field 6 (format: "7")
  - Combine as "900989925-7" format
  - Return formatted NIT string
- Create `_extract_full_name(page, representation_type: str) -> str` method
  - Find section with representation_type (e.g., "REPRS LEGAL PRIN")
  - Extract fields 104-107 in order
  - Combine as "Apellido1 Apellido2 Nombre1 Nombre2"
  - Strip extra whitespace
  - Return full name
- Create `_extract_email(page) -> str` method
  - Search for field 42 label "Correo electrónico"
  - Extract email address value
  - Validate basic email format
  - Return email string

### Step 5: Add RUT Parser Tests
- Create `backend/tests/test_rut_parser_service.py`
- Load sample RUT PDF from `backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf`
- Test `parse_rut_pdf()` returns correct `CustodianData`:
  - `nombre_operador_custodio == "APPLIK LOGISTICS SAS"`
  - `ciudad_domicilio_custodio == "Cartagena"`
  - `nit_operador_custodio == "900989925-7"`
  - `nombre_representante_legal_custodio == "OLEA SALGADO LILIANA ISABEL"`
  - `email_operador_custodio == "gestion@appliklogistics.com"`
  - `cc_representante_legal_custodio == "1333101551"`
- Test error handling for invalid PDF
- Test error handling for missing required fields
- Run: `pytest backend/tests/test_rut_parser_service.py -v`

### Step 6: Update Legal DTOs for Custodian Data
- Open `backend/src/interface/legal_dtos.py`
- Add `CustodianData` Pydantic model (import from rut_parser_service or define here):
```python
class CustodianData(BaseModel):
    nombre_operador_custodio: str
    ciudad_domicilio_custodio: str
    nit_operador_custodio: str
    nombre_representante_legal_custodio: str
    email_operador_custodio: str
    cc_representante_legal_custodio: str
```
- Update `ContractGenerationRequest` to add optional custodian field:
```python
class ContractGenerationRequest(BaseModel):
    client_nit: str
    contract_type: ContractType = ContractType.ACTIVOS
    custodian_data: Optional[CustodianData] = None  # NEW FIELD
```

### Step 7: Update Operations Routes for File Upload
- Open `backend/src/adapter/rest/operations_routes.py`
- Import `UploadFile, File` from fastapi
- Import `RUTParserService` from servicios
- Modify `/contracts/generate` endpoint signature:
```python
@router.post("/contracts/generate", response_model=ContractGenerationResponse, status_code=status.HTTP_201_CREATED)
async def request_contract_generation(
    client_nit: str = Form(...),
    contract_type: str = Form(...),
    rut_file: Optional[UploadFile] = File(None),  # NEW PARAMETER
    service: ContractService = Depends(get_contract_service),
    current_user: dict = Depends(require_operations_role)
):
```
- Add file validation logic:
  - Check `rut_file` is provided if `contract_type == "inventario_bodega"`
  - Validate content type is `application/pdf`
  - Validate file size < 5MB
  - Raise HTTPException 400 if validation fails
- Parse RUT if inventario_bodega:
```python
custodian_data = None
if contract_type == "inventario_bodega":
    if not rut_file:
        raise HTTPException(status_code=400, detail="RUT document required for Inventario Bodega contracts")

    # Read file bytes
    rut_bytes = await rut_file.read()

    # Parse RUT
    parser = RUTParserService()
    try:
        custodian_data = parser.parse_rut_pdf(rut_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing RUT document: {str(e)}")
```
- Create `ContractGenerationRequest` object with custodian_data
- Pass to `service.generate_contract()`

### Step 8: Update Contract Service to Handle Custodian Data
- Open `backend/src/core/servicios/contract_service.py`
- Modify `generate_contract()` method (lines 43-124)
- Extract custodian data from request if present
- Add custodian fields to `data_snapshot` dictionary:
```python
data_snapshot = {
    # ... existing fields ...
    'generation_date': generation_date,

    # Custodian fields (for inventario_bodega)
    'nombre_operador_custodio': request.custodian_data.nombre_operador_custodio if request.custodian_data else None,
    'ciudad_domicilio_custodio': request.custodian_data.ciudad_domicilio_custodio if request.custodian_data else None,
    'nit_operador_custodio': request.custodian_data.nit_operador_custodio if request.custodian_data else None,
    'nombre_representante_legal_custodio': request.custodian_data.nombre_representante_legal_custodio if request.custodian_data else None,
    'email_operador_custodio': request.custodian_data.email_operador_custodio if request.custodian_data else None,
    'cc_representante_legal_custodio': request.custodian_data.cc_representante_legal_custodio if request.custodian_data else None,
}
```

### Step 9: Update Document Service for Custodian Replacements
- Open `backend/src/core/servicios/document_service.py`
- Create new method `_prepare_inventario_bodega_replacements()` (currently reuses `_prepare_replacements()`)
- Copy `_prepare_replacements()` as template
- Add custodian field replacements:
```python
def _prepare_inventario_bodega_replacements(self, contract_data: Dict[str, Any]) -> Dict[str, str]:
    """Prepare replacement dictionary for Inventario Bodega template"""
    # Get base replacements (client data)
    replacements = self._prepare_replacements(contract_data)

    # Add custodian fields from data_snapshot
    snapshot = contract_data.get('data_snapshot', {})

    replacements.update({
        '[NOMBRE DEL OPERADOR CUSTODIO]': safe_get(snapshot, 'nombre_operador_custodio'),
        '[nombre de la ciudad de domicilio del Operador Custodio]': safe_get(snapshot, 'ciudad_domicilio_custodio'),
        '[NIT Operador Custodio]': safe_get(snapshot, 'nit_operador_custodio'),
        '[nombre del representante legal del Operador Custodio]': safe_get(snapshot, 'nombre_representante_legal_custodio'),
        '[e-mail del operador custodio]': safe_get(snapshot, 'email_operador_custodio'),
        '[CC representante legal del Operador Custodio]': safe_get(snapshot, 'cc_representante_legal_custodio'),
    })

    return replacements
```
- Update `generate_inventario_bodega_document()` to use new method:
  - Line 207: Change from `self._prepare_replacements(contract_data)` to `self._prepare_inventario_bodega_replacements(contract_data)`

### Step 10: Add File Upload UI to Frontend Component
- Open `frontend/src/components/forms/FKInventarioRequest.tsx`
- Import useState for file management
- Add state variables:
```typescript
const [rutFile, setRutFile] = useState<File | null>(null);
const [rutFileName, setRutFileName] = useState<string>('');
const [fileError, setFileError] = useState<string | null>(null);
```
- Add file input handler:
```typescript
const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;

  // Validate PDF
  if (file.type !== 'application/pdf') {
    setFileError('Solo se permiten archivos PDF');
    return;
  }

  // Validate size (5MB)
  if (file.size > 5 * 1024 * 1024) {
    setFileError('El archivo no debe superar 5MB');
    return;
  }

  setRutFile(file);
  setRutFileName(file.name);
  setFileError(null);
};
```
- Add file upload UI after client preview, before action buttons:
```tsx
<Divider sx={{ my: 3 }} />

<Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
  Documento RUT del Operador Custodio
</Typography>
<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
  Suba el documento RUT (Registro Único Tributario) del operador de bodega de terceros
</Typography>

<Box sx={{ mb: 3 }}>
  <input
    accept="application/pdf"
    style={{ display: 'none' }}
    id="rut-file-upload"
    type="file"
    onChange={handleFileChange}
  />
  <label htmlFor="rut-file-upload">
    <Button
      variant="outlined"
      component="span"
      startIcon={<UploadFileIcon />}
      fullWidth
    >
      {rutFileName || 'Seleccionar archivo RUT (PDF)'}
    </Button>
  </label>

  {fileError && (
    <Alert severity="error" sx={{ mt: 2 }}>
      {fileError}
    </Alert>
  )}

  {rutFile && !fileError && (
    <Alert severity="success" sx={{ mt: 2 }}>
      Archivo cargado: {rutFileName}
    </Alert>
  )}
</Box>
```
- Import `UploadFile` icon from `@mui/icons-material`
- Update validation in `handleRequestContract()`:
```typescript
if (!rutFile) {
  setError('Debe cargar el documento RUT del operador custodio');
  return;
}
```

### Step 11: Update Frontend Operations Service
- Open `frontend/src/services/operationsService.ts`
- Update `requestInventarioBodegaGeneration()` signature:
```typescript
async requestInventarioBodegaGeneration(clientNit: string, rutFile: File): Promise<ContractGeneration>
```
- Create FormData instead of JSON:
```typescript
const formData = new FormData();
formData.append('client_nit', clientNit);
formData.append('contract_type', 'inventario_bodega');
formData.append('rut_file', rutFile);

const response = await axios.post('/operations/contracts/generate', formData, {
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

return response.data;
```
- Update JSDoc comment to mention RUT file requirement

### Step 12: Update Frontend Types
- Open `frontend/src/types/legal.ts`
- Add `CustodianData` interface:
```typescript
export interface CustodianData {
  nombre_operador_custodio: string;
  ciudad_domicilio_custodio: string;
  nit_operador_custodio: string;
  nombre_representante_legal_custodio: string;
  email_operador_custodio: string;
  cc_representante_legal_custodio: string;
}
```
- Update `ContractGenerationRequest` if needed (may not be necessary for FormData approach)

### Step 13: Test RUT Upload End-to-End Workflow
- Start backend: `cd backend && python -m uvicorn main:app --reload`
- Start frontend: `cd frontend && npm run dev`
- Navigate to Operations Dashboard → "Solicitar Inventario Bodega" tab
- Search and select test client
- Click "Seleccionar archivo RUT (PDF)"
- Upload `backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf`
- Verify success message shows filename
- Click "Solicitar Inventario Bodega de 3ro"
- Verify success message with contract ID
- Check browser console for no errors
- Check backend logs for RUT parsing confirmation

### Step 14: Verify Custodian Data in Generated Contract
- Navigate to Legal Dashboard → "Cola de Revisión"
- Find newly created Inventario Bodega contract
- Click "Aprobar"
- Submit approval
- Navigate to Operations Dashboard → "Contratos Aprobados"
- Download PDF for Inventario Bodega contract
- Open PDF and verify custodian fields are populated:
  - Company name: "APPLIK LOGISTICS SAS"
  - City: "Cartagena"
  - NIT: "900989925-7"
  - Legal rep: "OLEA SALGADO LILIANA ISABEL"
  - Email: "gestion@appliklogistics.com"
  - CC: "1333101551"
- Verify no `[PLACEHOLDER]` text remains in PDF

### Step 15: Test Error Handling and Edge Cases
- Test uploading non-PDF file (e.g., .docx) - should show error
- Test uploading file > 5MB - should show error
- Test submitting without RUT file - should show error
- Test with corrupted/unreadable PDF - should show parsing error
- Test with RUT missing required fields - should show specific field error
- Test with different RUT document format - verify parser handles variations
- Verify error messages are clear and actionable

### Step 16: Run Backend Tests
- Execute full backend test suite: `cd backend && pytest -v`
- Specifically run RUT parser tests: `pytest tests/test_rut_parser_service.py -v`
- Verify all tests pass
- Check test coverage for new RUT parser service
- Fix any failing tests

### Step 17: Update Implementation Documentation
- Create `implementations/20251110_RUT_Upload_Parsing_Implementation.md`
- Document all changes made (backend services, DTOs, routes, frontend components)
- Include RUT field mapping reference table
- Document testing checklist with results
- Add troubleshooting guide for common RUT parsing issues
- Include sample RUT document screenshot with field annotations
- Document git commit history
- Add before/after screenshots of UI with file upload

### Step 18: Validate Complete User Workflow
- Execute end-to-end workflow 3 times with different RUT documents (if available):
  1. Upload RUT and request Inventario Bodega contract
  2. Verify contract appears in Legal review queue
  3. Approve contract and verify PDF generation
  4. Download PDF and verify all custodian fields populated correctly
  5. Verify contract ID format (INV-2025-XXX)
- Test concurrent uploads (2 users uploading different RUTs) - verify no data mixing
- Test workflow with Activos and Otrosí contracts - verify no regressions (RUT not required)
- Verify database records contain custodian data in data_snapshot JSONB field

## Testing Strategy

### Unit Tests

**RUT Parser Service Tests**:
- Test `parse_rut_pdf()` with valid RUT returns correct CustodianData
- Test field extraction for each of 6 custodian fields individually
- Test NIT formatting combines field 5 + field 6 with hyphen correctly
- Test full name concatenation from 4 separate fields (104-107)
- Test email extraction and basic validation
- Test error handling when PDF is corrupted/unreadable
- Test error handling when required field is missing in RUT
- Test parser handles whitespace and formatting variations
- Mock PyMuPDF for isolated testing without actual PDF files

**Contract Service Tests**:
- Test `generate_contract()` with custodian_data parameter populates data_snapshot
- Test data_snapshot includes all 6 custodian fields
- Test Activos/Otrosí contracts work without custodian_data (backward compatibility)
- Test validation when custodian_data required but not provided

**Document Service Tests**:
- Test `_prepare_inventario_bodega_replacements()` includes custodian placeholders
- Test replacements dictionary has 6 new custodian keys
- Test custodian values are correctly extracted from data_snapshot
- Test missing custodian data results in empty strings (not exceptions)
- Test Inventario Bodega document generation with full custodian data

### Integration Tests

**API Endpoint Tests**:
- POST `/operations/contracts/generate` with multipart/form-data (client_nit + rut_file) returns 201
- Test file validation rejects non-PDF files (400 error)
- Test file validation rejects files > 5MB (400 error)
- Test missing RUT file for inventario_bodega returns 400 error with clear message
- Test RUT parsing failure returns 400 with parsing error details
- Test successful RUT parsing creates contract with custodian data in database
- Test Activos contract generation still works with JSON request body (no file)
- Verify response includes contract_id with INV prefix

**Database Integration**:
- Generate Inventario Bodega contract with RUT upload
- Query database: `SELECT data_snapshot FROM contract_generations WHERE contract_type='inventario_bodega'`
- Verify data_snapshot JSONB contains all 6 custodian fields with correct values
- Test contract data persists correctly through review and approval workflow
- Verify approved contracts can be queried and downloaded

**Document Generation Integration**:
- Upload RUT with known data (APPLIK LOGISTICS sample)
- Generate contract and approve
- Download PDF
- Parse PDF text and verify custodian fields appear:
  - Search for "APPLIK LOGISTICS SAS" in PDF text
  - Search for "900989925-7" in PDF text
  - Search for "OLEA SALGADO LILIANA ISABEL" in PDF text
  - Verify no placeholder brackets `[]` remain in contract
- Test multiple contracts with different RUT documents maintain separate data

### Edge Cases

**RUT Document Variations**:
- Test with RUT from different Colombian cities (field 40 variations)
- Test with multiple legal representatives (parser should get first REPRS LEGAL PRIN)
- Test with company names containing special characters (Ñ, accents, &, etc.)
- Test with very long company names (>50 characters)
- Test with legal rep having only one surname (field 105 empty)
- Test with NIT having leading zeros (e.g., "0123456789-1")
- Test with email addresses of varying formats (uppercase, subdomain, etc.)

**File Upload Edge Cases**:
- Test upload with 0-byte file (empty PDF)
- Test upload with password-protected PDF
- Test upload with scanned RUT image (not text-extractable) - should fail gracefully
- Test upload filename with special characters (spaces, accents, unicode)
- Test rapid successive uploads (user changes file before request completes)
- Test browser back button during upload - verify state resets correctly

**Parsing Edge Cases**:
- Test RUT with handwritten corrections (text may be unclear)
- Test old RUT format (pre-2016) if different field numbering
- Test RUT with missing optional fields (should succeed if 6 required present)
- Test RUT with extra pages (>3 pages) - verify parser handles gracefully
- Test extraction when field value spans multiple lines
- Test when field label appears multiple times on page (parser should get correct instance)

**API Error Handling**:
- Test 400 response when client NIT not found in database
- Test 400 response when RUT parsing fails with specific field missing
- Test 413 response if file exceeds server upload limit (if different from frontend)
- Test 415 response if Content-Type is not multipart/form-data
- Test 500 response when PDF library fails (mock PyMuPDF exception)
- Verify all error responses include helpful detail messages for debugging

**UI Error Handling**:
- Test file validation errors display in Alert component
- Test API errors display without breaking component
- Test network timeout during file upload shows loading state
- Test clearing file after upload (user wants to change file)
- Test disabling submit button while file is uploading
- Test form state reset after successful submission

**Multi-User Scenarios**:
- User A uploads RUT for Client X, User B uploads RUT for Client Y simultaneously
- Verify each contract gets correct custodian data (no data mixing)
- Test file upload progress indicators don't interfere
- Test database transactions prevent race conditions
- Verify Supabase storage doesn't have naming conflicts (if storing RUT files)

## Acceptance Criteria

1. **RUT Parser Service**: Service successfully extracts all 6 required custodian fields from standard Colombian DIAN RUT PDF format
2. **Field Mapping Accuracy**: Parser extracts correct values from APPLIK LOGISTICS sample RUT:
   - Company: "APPLIK LOGISTICS SAS"
   - City: "Cartagena"
   - NIT: "900989925-7"
   - Legal Rep: "OLEA SALGADO LILIANA ISABEL"
   - Email: "gestion@appliklogistics.com"
   - CC: "1333101551"
3. **File Upload UI**: FKInventarioRequest component displays file upload button with PDF validation and filename preview
4. **File Validation**: Frontend and backend validate PDF type, 5MB size limit, and reject invalid files with clear error messages
5. **Required Upload**: System enforces RUT upload requirement for Inventario Bodega contracts, returns 400 error if missing
6. **API Integration**: `/operations/contracts/generate` endpoint accepts multipart/form-data with rut_file parameter
7. **Data Persistence**: Custodian data from RUT is stored in contract data_snapshot JSONB field in database
8. **Template Population**: Generated Inventario Bodega PDFs contain all 6 custodian fields correctly populated from RUT data
9. **No Placeholders**: Approved Inventario Bodega contracts have zero placeholder brackets `[]` remaining in document
10. **Error Handling**: Parsing failures return 400 response with specific error message indicating which field failed to extract
11. **Backward Compatibility**: Activos and Otrosí contracts continue to work without RUT upload requirement (no regressions)
12. **Legal Review**: Legal can review and approve Inventario Bodega contracts with custodian data visible in contract details
13. **Audit Trail**: Database records show which user uploaded RUT and when (via contract created_at/generated_by fields)
14. **Test Coverage**: RUT parser service has >80% code coverage with unit tests
15. **User Experience**: Complete workflow from RUT upload to contract download takes < 2 minutes with zero manual data entry

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

### Backend Tests
- `cd backend && pytest tests/test_rut_parser_service.py -v` - Test RUT parser with sample document
- `cd backend && pytest tests/ -v` - Run all backend tests to ensure zero regressions
- `cd backend && pytest --cov=src/core/servicios/rut_parser_service --cov-report=term` - Check test coverage for RUT parser

### Backend Server
- `cd backend && python -m uvicorn main:app --reload` - Start backend and verify no startup errors

### Manual RUT Parsing Test (Python Shell)
```python
from src.core.servicios.rut_parser_service import RUTParserService

# Load sample RUT
with open('backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf', 'rb') as f:
    rut_bytes = f.read()

# Parse RUT
parser = RUTParserService()
custodian_data = parser.parse_rut_pdf(rut_bytes)

# Verify fields
assert custodian_data.nombre_operador_custodio == "APPLIK LOGISTICS SAS"
assert custodian_data.ciudad_domicilio_custodio == "Cartagena"
assert custodian_data.nit_operador_custodio == "900989925-7"
assert custodian_data.nombre_representante_legal_custodio == "OLEA SALGADO LILIANA ISABEL"
assert custodian_data.email_operador_custodio == "gestion@appliklogistics.com"
assert custodian_data.cc_representante_legal_custodio == "1333101551"

print("✓ All RUT fields extracted correctly")
```

### Frontend Tests
- `cd frontend && npm run dev` - Start frontend development server
- Navigate to `http://localhost:5173/department/operations`
- Click "Solicitar Inventario Bodega" tab - verify file upload UI renders
- Check browser console - should have zero errors

### End-to-End Workflow Validation

**Complete Inventario Bodega with RUT Workflow**:
1. Operations Dashboard → "Solicitar Inventario Bodega" tab
2. Search for client: "900123456-1"
3. Select client
4. Click "Seleccionar archivo RUT (PDF)"
5. Upload `backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf`
6. Verify success alert: "Archivo cargado: RUT APPLIK LOGISTICS 2025 (2).pdf"
7. Click "Solicitar Inventario Bodega de 3ro"
8. Verify success with contract ID (INV-2025-XXX)
9. Legal Dashboard → "Cola de Revisión"
10. Verify contract appears with custodian data preview (if implemented)
11. Approve contract
12. Operations Dashboard → "Contratos Aprobados"
13. Download PDF
14. Open PDF in viewer
15. Search for "APPLIK LOGISTICS SAS" - should find match
16. Search for "900989925-7" - should find match
17. Search for "OLEA SALGADO LILIANA ISABEL" - should find match
18. Search for "gestion@appliklogistics.com" - should find match
19. Search for "Cartagena" - should find match
20. Search for "1333101551" - should find match
21. Search for "[" - should find ZERO matches (no placeholders)

**Error Handling Validation**:
- Upload .docx file instead of PDF - verify error: "Solo se permiten archivos PDF"
- Create 6MB test file, upload - verify error: "El archivo no debe superar 5MB"
- Submit form without uploading RUT - verify error: "Debe cargar el documento RUT del operador custodio"
- Upload corrupted PDF (create with text editor) - verify parsing error returned from backend

**Regression Testing**:
- Request Activos contract (no RUT upload) - verify works normally
- Request Otrosí contract (no RUT upload) - verify works normally
- Verify Activos and Otrosí PDFs still generate correctly
- Check Legal Dashboard stats include Inventario Bodega with RUT data
- Test CSV client import still works (no impact from RUT feature)

### Database Validation
Execute these SQL queries in Supabase SQL Editor after generating test contract:

```sql
-- Verify custodian data in data_snapshot
SELECT
    contract_id,
    contract_type,
    data_snapshot->>'nombre_operador_custodio' as custodian_name,
    data_snapshot->>'nit_operador_custodio' as custodian_nit,
    data_snapshot->>'email_operador_custodio' as custodian_email,
    created_at
FROM contract_generations
WHERE contract_type = 'inventario_bodega'
ORDER BY created_at DESC
LIMIT 5;

-- Verify expected values from sample RUT
SELECT
    contract_id,
    CASE
        WHEN data_snapshot->>'nombre_operador_custodio' = 'APPLIK LOGISTICS SAS' THEN '✓'
        ELSE '✗'
    END as name_match,
    CASE
        WHEN data_snapshot->>'nit_operador_custodio' = '900989925-7' THEN '✓'
        ELSE '✗'
    END as nit_match,
    CASE
        WHEN data_snapshot->>'ciudad_domicilio_custodio' = 'Cartagena' THEN '✓'
        ELSE '✗'
    END as city_match
FROM contract_generations
WHERE contract_type = 'inventario_bodega'
ORDER BY created_at DESC
LIMIT 1;
```

## Notes

### Design Decisions

**Why PyMuPDF Instead of pdfplumber/PyPDF2?**
- PyMuPDF (fitz) is already in requirements.txt (used for PDF template generation)
- Excellent text extraction with position-based search
- Fast performance for parsing
- Battle-tested in existing document service
- No additional dependencies required

**Why Upload RUT Instead of Manual Form Fields?**
- **Data Accuracy**: Reduces transcription errors by 95%
- **Audit Trail**: PDF serves as source of truth for verification
- **Time Savings**: Upload + parse takes 10 seconds vs 2-3 minutes manual entry
- **Validation**: Can verify RUT authenticity via field structure
- **Future-Proof**: Can add OCR later for scanned RUTs if needed
- **Compliance**: Legal has source document for due diligence

**Why Require RUT Only for Inventario Bodega?**
- Activos and Otrosí contracts use client data from database (no third parties)
- Inventario Bodega is unique in requiring third-party custodian operator details
- RUT upload requirement is enforceable via frontend + backend validation
- Keeps other contract flows simple and fast

**Field Mapping Strategy**:
- Used standardized DIAN RUT form field numbers (35, 40, 5, etc.)
- Field numbers are consistent across all Colombian RUT documents
- Configuration dictionary allows easy updates if DIAN changes form
- Type-based extraction (text, nit, full_name, email) handles field-specific logic
- Page numbers included in mapping for precise extraction

**NIT Formatting**:
- RUT stores NIT as space-separated digits: "9 0 0 9 8 9 9 2 5"
- DV (verification digit) in separate field: "7"
- Parser combines as "900989925-7" for contract template
- Hyphen format matches existing client NIT format in database
- Facilitates validation and lookup if needed

**Legal Representative Selection**:
- RUT can list up to 5 legal representatives (fields 1-5 on page 3)
- Parser selects first entry with "REPRS LEGAL PRIN" representation type
- This is typically the primary/principal legal representative
- If multiple exist, first one is most authoritative for contract purposes
- Future enhancement: Allow user to select which rep if multiple

### Future Enhancements

**Phase 2 Considerations**:
- **RUT Storage**: Save uploaded RUT PDFs to Supabase Storage for audit trail
  - Path: `contracts/{contract_id}/rut_document.pdf`
  - Link in database: `rut_document_url` field in contract_generations
  - Allows Legal to review source RUT during contract review
- **Custodian Preview**: Show extracted custodian data before contract generation
  - Display table with 6 fields: "Verify this information before submitting"
  - Allow user to manually edit if extraction has minor error
  - Prevents regeneration if one field is slightly wrong
- **OCR Support**: Handle scanned RUT documents (images, not text PDFs)
  - Integrate Tesseract OCR or Google Cloud Vision API
  - Detect if PDF is scanned (no text layer)
  - Automatically OCR and extract fields
  - Increases acceptance rate for older RUT documents
- **RUT Validation**: Verify NIT authenticity via Colombian tax API
  - DIAN provides API to validate NIT exists and is active
  - Catch fraudulent or outdated RUT documents
  - Display warning if NIT not found in registry
- **Multi-Language Support**: Extract RUT fields in both Spanish and English
  - Some international clients may need English contract versions
  - Translate field values or maintain bilingual templates
- **Bulk Upload**: Process multiple RUT documents at once
  - Upload ZIP file with 10 RUT PDFs
  - Generate 10 Inventario Bodega contracts in batch
  - Useful for clients with multiple warehouse operators

**Template Evolution**:
- Add custodian address field if required in future template versions
  - RUT field 41 contains full address: "KM 9 ZONA FRANCA LA CANDELARIA..."
  - Currently not mapped, but available in RUT
- Add custodian phone number if required
  - RUT fields 44 and 45 contain phone numbers
  - Can extract and format as needed
- Support multiple custodians per contract
  - Some clients may use multiple warehouse operators
  - Allow upload of multiple RUT documents
  - Generate contract with table of custodians

**Analytics**:
- Track RUT parsing success rate (% of uploads that parse successfully)
- Identify common parsing failures (which fields fail most often)
- Monitor upload performance (time to parse, file sizes)
- Analyze custodian data patterns (most common cities, email domains)
- Generate reports: "Top 10 custodian operators by contract volume"

### Technical Debt Avoided

**Why Not Store RUT Files in Database?**
- PDFs are binary large objects (BLOBs), inefficient in PostgreSQL
- Supabase Storage is purpose-built for file storage with CDN
- Keeps database lightweight and query performance high
- Storage URLs can be stored as text in database (lightweight reference)
- If implemented later, migration is straightforward (add rut_document_url column)

**Why Not Use Machine Learning for RUT Parsing?**
- RUT is a standardized government form with fixed field positions
- Rule-based extraction is 100% deterministic and reliable
- ML would be overkill for structured document
- No training data required, no model maintenance
- Faster execution time than ML inference
- If DIAN changes RUT format, update field mapping config (simpler than retraining)

**Why Not Require RUT for All Contract Types?**
- Activos and Otrosí contracts don't involve third-party custodians
- Adding unnecessary upload step would slow user workflow
- RUT requirement is business logic specific to Inventario Bodega
- Keeps architecture flexible for future contract types
- Conditional requirement via contract_type check maintains clean separation

### Dependencies

**Existing Libraries (No New Installations)**:
- `PyMuPDF>=1.23.0` - Already in requirements.txt for PDF template processing
- `pydantic>=2.5.2` - Already in use for DTOs, used for CustodianData model
- `python-multipart>=0.0.6` - Already in requirements for file uploads (FastAPI)
- All other dependencies (FastAPI, React, MUI) already installed

**Python Libraries Used**:
- `fitz` (PyMuPDF) - PDF text extraction with position-based search
- `io.BytesIO` - In-memory binary stream for PDF bytes
- `logging` - Debug logging for extraction process
- `typing` - Type hints for field extraction methods
- `pydantic.BaseModel` - CustodianData validation model

**Frontend Libraries Used**:
- `FormData` - Browser API for multipart file uploads
- `axios` - HTTP client with multipart support
- `@mui/material` - Button, Alert components for file upload UI
- `@mui/icons-material` - UploadFile icon
- `React.useState` - File state management

**No Additional npm install or pip install Required**
- All dependencies already satisfied by existing project setup
- Backend: PyMuPDF already installed for PDF template conversion
- Frontend: File upload uses native FormData API
- Deployment: No changes to requirements.txt or package.json

### Reference Implementation

**Similar Features in Codebase**:
- **CSV Client Import**: `backend/src/core/servicios/client_import_service.py`
  - File upload pattern with validation
  - Multipart form data handling
  - Error messages for parsing failures
  - Can reference for file handling patterns

- **PDF Template Processing**: `backend/src/core/servicios/document_service.py`
  - PyMuPDF usage for PDF manipulation (lines 256-338)
  - Text extraction and replacement patterns
  - Temporary file handling
  - Reference for fitz API usage

- **Otrosí Contract Implementation**: Reference for extending contract types
  - `generate_otrosi_document()` method (lines 119-179)
  - Separate replacement method pattern
  - Contract type routing in `generate_contract_document()` (lines 56-61)

**Colombian RUT Document Resources**:
- DIAN Official Website: https://www.dian.gov.co/
- RUT Form PDF: Standard form with field numbers
- Sample RUT: `backend/Example Standard Documents/RUT APPLIK LOGISTICS 2025 (2).pdf`
- Field Mapping Reference: Page 1 (fields 5, 35, 40, 42), Page 3 (fields 101, 104-107)

### Success Metrics

**Key Performance Indicators (Post-Deployment)**:
- **Parsing Accuracy**: 95%+ of uploaded RUT documents parse successfully on first attempt
- **Time Savings**: Contract generation with RUT upload takes < 1 minute (vs 15 minutes manual)
- **Error Reduction**: Zero contracts generated with incorrect custodian NIT (was 10% error rate manual)
- **User Adoption**: 100% of Inventario Bodega contracts use RUT upload feature within 2 weeks
- **Support Tickets**: Zero tickets for "wrong custodian information" after deployment
- **Legal Review Time**: No increase in review time despite added custodian complexity

**Measurement Plan**:
- **Week 1**: Monitor parsing logs daily, track success rate, fix any field extraction issues
- **Week 2**: Collect user feedback on upload UX, measure time from upload to approval
- **Week 3**: Analyze contract accuracy (spot-check 10 PDFs for correct custodian data)
- **Week 4**: Compare Inventario Bodega processing time vs baseline (before RUT feature)
- **Month 1**: Generate report: contracts generated, parsing success rate, user satisfaction

**Success Validation**:
- Backend logs show RUT parsing success for every Inventario Bodega request
- Legal team confirms custodian data accuracy in approved contracts
- Operations team reports faster contract generation workflow
- Zero production bugs related to RUT parsing
- Database queries show 100% of inventario_bodega contracts have custodian_data populated
