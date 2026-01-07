# Feature Prompt: Instruccion de Mandato - Full Implementation

## Template Analysis

### Template File
- **Path:** `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- **Contract Type Enum:** `pl_co_mandato_im` (already exists in `ContractType`)

> **Scope:** This implementation covers **non-DIAN creditors only** (requiring Bank Certificate PDF). DIAN payments (`pl_co_dian_mandato_im`) will be implemented separately with a dedicated template.

### Document Structure

The template consists of a single table with 7 rows and 2 columns (content duplicated in both columns):

| Row | Content |
|-----|---------|
| 0 | Header: Fecha de Instruccion de Mandato, Numero de Desembolso |
| 1 | Introduction paragraph with contract date references |
| 2 | Section title: "Acto(s) para el(los) cual(es)..." |
| 3 | Transfer description + **NESTED TABLE** for Creditor Information |
| 4 | Section title: "Terminos generales de la Instruccion de Mandato" |
| 5 | Legal terms and declarations |
| 6 | Signature block with representative name and ID |

### Placeholders Identified

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `[Fecha actual]` | Current date | System Generated |
| `[Numero de cotizacion de desembolso]` | Disbursement quote number | Cotizacion PDF |
| `[dia de firma contrato mandato]` | Day of contract signing | Cotizacion PDF |
| `[mes de firma contrato mandato]` | Month of contract signing | Cotizacion PDF |
| `[ano de firma contrato mandato]` | Year of contract signing | Cotizacion PDF |
| `[monto a transferir en letras]` | Amount in words (Spanish) | Derived |
| `[monto a transferir en numeros]` | Amount in numbers | Cotizacion PDF |
| `[Nombre del representante legal del Cliente]` | Legal representative name | Database/Cotizacion |
| `[numero ID representante legal]` | Legal representative ID | Database/Cotizacion |

### Nested Table Structure (Creditor Information)

Located in Row 3, Cell 0 of the main table:

| Column 0 | Column 1 | Column 2 | Column 3 | Column 4 |
|----------|----------|----------|----------|----------|
| Razon social | NIT (si aplica) | Banco | Tipo de Cuenta | Numero de Cuenta |
| `[...]` | `[...]` | `[...]` | `[Ahorros \| Corriente]` | `[...]` |
| `[...]` | `[...]` | (empty) | (empty) | (empty) |
| `[...]` | `[...]` | (empty) | (empty) | (empty) |

**Note:** Template supports up to 3 creditors.

---

## Example File Analysis

### Cotizacion PDF (Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf)

**Extracted Data Points:**

| Field | Value in Example | Location in PDF |
|-------|------------------|-----------------|
| Numero de Cotizacion | CO:900436389:1:2:DOM | Page 1, Header table |
| Fecha de Cotizacion | 10 de noviembre de 2025 | Page 1, Header table |
| Fecha de Contrato de Credito | 6 de noviembre de 2025 | Page 1, First paragraph |
| Monto de Desembolso | COP 739,860 | Page 1, Conditions table |
| Representante Legal | Cesar Jose Castillo Soto | Page 2, Signature block |
| Tipo ID Representante | C.E. | Page 2, Signature block |
| Numero ID Representante | 814674 | Page 2, Signature block |

**Anexo I Table (Page 3):**

| Acreedor | No. Instrumento | Monto (COP) |
|----------|-----------------|-------------|
| Entidad de pago de Impuestos | 1003887257 | 407,001.00 |
| Entidad de pago de Impuestos | 1003887254 | 290,000.00 |
| Entidad de pago de Impuestos | 1003887815 | 42,859.00 |
| **TOTAL** | | **739,860.00** |

### Bank Certificate PDF (certificado bancario.pdf)

**Extracted Data Points:**

| Field | Value in Example | Location in PDF |
|-------|------------------|-----------------|
| Company Name | CONSULADUANA & LOGISTICA SAS | Header paragraph |
| NIT | 901599856 | Header paragraph |
| Bank | BANCOLOMBIA | Document title/logo |
| Account Type | CUENTA DE AHORROS | Product table |
| Account Number | 77500002334 | Product table |
| Account Status | ACTIVA | Product table |
| Certificate Date | Martes, 9 de julio de 2024 | Header |

---

## Feature Prompt for `/feature` Command

### Overview

**Task:** Implement the "Instruccion de Mandato" (Mandate Instruction) document generation feature for the Paga Local Colombia workflow.

**Current State:**
- `ContractType.PL_CO_MANDATO_IM` enum value exists in `legal_dtos.py` (line 30)
- No handler implemented in `DocumentService.generate_contract_document()`
- `CotizacionParserService` exists and can be reused
- No Bank Certificate parser exists

**Goal:** Enable users to generate Instruccion de Mandato documents for non-DIAN creditors by uploading a Cotizacion PDF and Bank Certificate PDF(s).

> **Note:** Bank Certificate PDF is REQUIRED for this implementation. DIAN payments will be handled separately.

---

### Backend Requirements

#### 1. Create Bank Certificate Parser Service

**File:** `backend/src/core/servicios/bank_certificate_parser_service.py`

```python
"""
Bank Certificate Parser Service - Extracts creditor bank information
"""
from dataclasses import dataclass
from typing import Optional
import fitz  # PyMuPDF
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class BankAccountInfo:
    """Bank account information extracted from certificate"""
    razon_social: str
    nit: str
    banco: str
    tipo_cuenta: str  # "Ahorros" or "Corriente"
    numero_cuenta: str

class BankCertificateParserService:
    """Service for parsing bank certificate PDFs"""

    def parse_bancolombia(self, pdf_bytes: bytes) -> BankAccountInfo:
        """Parse Bancolombia bank certificate"""
        # Implementation...

    def parse_bbva(self, pdf_bytes: bytes) -> BankAccountInfo:
        """Parse BBVA bank certificate"""
        # Implementation...

    def parse_certificate(self, pdf_bytes: bytes) -> BankAccountInfo:
        """Auto-detect bank and parse certificate"""
        # Detect bank from content/logo
        # Route to appropriate parser
```

**Key Extraction Patterns for Bancolombia:**
```python
# Company name
COMPANY_PATTERN = r'informar que\s+(.+?)\s+identificado'

# NIT
NIT_PATTERN = r'NIT\s+(\d+)'

# Account type
ACCOUNT_TYPE_PATTERN = r'(CUENTA DE AHORROS|CUENTA CORRIENTE)'

# Account number (10+ digits in product table)
ACCOUNT_NUMBER_PATTERN = r'\b(\d{10,})\b'
```

#### 2. Create DTOs for Instruccion de Mandato

**File:** `backend/src/interface/legal_dtos.py` (add to existing file)

```python
class AcreedorGastosNacionales(BaseModel):
    """Creditor information for Instruccion de Mandato"""
    razon_social: str = Field(..., min_length=1, max_length=255)
    nit: Optional[str] = Field(None, max_length=20)
    banco: str = Field(..., min_length=1, max_length=100)
    tipo_cuenta: str = Field(..., pattern=r'^(Ahorros|Corriente|PCE)$')
    numero_cuenta: str = Field(..., min_length=1, max_length=50)

class InstruccionMandatoRequest(BaseModel):
    """Request to generate Instruccion de Mandato"""
    client_nit: str = Field(..., min_length=5, max_length=20)
    numero_cotizacion_desembolso: str = Field(...)
    fecha_contrato_mandato: str = Field(..., description="ISO format date")
    monto: Decimal = Field(..., gt=0)
    acreedores: list[AcreedorGastosNacionales] = Field(..., min_items=1, max_items=3)
```

#### 3. Add Document Generation Handler

**File:** `backend/src/core/servicios/document_service.py` (modify existing file)

Add routing in `generate_contract_document()`:
```python
elif contract_type == 'pl_co_mandato_im':
    return self.generate_instruccion_mandato_document(contract_data)
```

Add new method:
```python
def generate_instruccion_mandato_document(
    self,
    contract_data: Dict[str, Any],
    template_name: str = "FK COL - Fin. COP - Mandato (IM).docx"
) -> bytes:
    """
    Generate Instruccion de Mandato document from template and data

    Args:
        contract_data: Dictionary containing:
            - numero_cotizacion_desembolso
            - fecha_contrato_mandato (ISO format)
            - monto
            - acreedores (list of creditor dicts)
            - Client data (representante_legal, cedula_representante)

    Returns:
        bytes: Generated DOCX file content
    """
    # 1. Load template
    # 2. Prepare replacements using _prepare_instruccion_mandato_replacements()
    # 3. Replace main document placeholders
    # 4. Populate nested creditor table using _populate_acreedores_table()
    # 5. Return bytes
```

Add helper methods:
```python
def _prepare_instruccion_mandato_replacements(self, data: Dict[str, Any]) -> Dict[str, str]:
    """Prepare placeholder replacements for Instruccion de Mandato"""
    # Use existing _number_to_words_spanish() for monto en letras
    # Parse fecha_contrato_mandato for day/month/year components

def _populate_acreedores_table(self, doc: Document, acreedores: list) -> None:
    """Populate the nested creditor information table"""
    # Navigate to Table 0 -> Row 3 -> Cell 0 -> Nested Table
    # Fill rows 1-3 with creditor data (row 0 is header)
```

#### 4. Add API Endpoints

**File:** `backend/src/adapter/rest/legal_routes.py` (modify existing file)

```python
@router.post("/contracts/instruccion-mandato/generate")
async def generate_instruccion_mandato(
    request: InstruccionMandatoRequest,
    current_user: dict = Depends(require_roles(['admin', 'legal']))
) -> ContractGenerationResponse:
    """Generate Instruccion de Mandato document"""
    # Implementation...

@router.post("/contracts/instruccion-mandato/parse-cotizacion")
async def parse_cotizacion_for_mandato(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(['admin', 'legal']))
) -> dict:
    """Parse Cotizacion PDF to extract data for Instruccion de Mandato"""
    # Reuse CotizacionParserService
    # Return extracted data for frontend to populate form

@router.post("/contracts/instruccion-mandato/parse-bank-certificate")
async def parse_bank_certificate(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles(['admin', 'legal']))
) -> AcreedorGastosNacionales:
    """Parse Bank Certificate PDF to extract creditor information"""
    # Use new BankCertificateParserService
```

---

### Frontend Requirements

#### 1. Create Types

**File:** `frontend/src/types/legal.ts` (add to existing file)

```typescript
export interface AcreedorGastosNacionales {
  razon_social: string;
  nit?: string;
  banco: string;
  tipo_cuenta: 'Ahorros' | 'Corriente';  // PCE removed - DIAN handled separately
  numero_cuenta: string;
}

export interface InstruccionMandatoRequest {
  client_nit: string;
  numero_cotizacion_desembolso: string;
  fecha_contrato_mandato: string;
  monto: number;
  acreedores: AcreedorGastosNacionales[];  // At least 1 required
}

export interface InstruccionMandatoFormData {
  cotizacionFile: File | null;
  bankCertificateFiles: File[];  // Required - at least 1 for each creditor
  manualAcreedores: AcreedorGastosNacionales[];
}
```

#### 2. Create Form Component

**File:** `frontend/src/components/forms/FKInstruccionMandatoForm.tsx`

**Component Requirements:**
1. **Step 1 - Upload Cotizacion:** File upload for Cotizacion PDF
   - Parse on upload to extract numero_cotizacion, fecha_contrato, monto
   - Display extracted data for user confirmation

2. **Step 2 - Upload Bank Certificate(s):** File upload for Bank Certificate PDF(s)
   - Parse each certificate to extract creditor bank information
   - Display extracted data for each creditor
   - Support adding multiple creditors (up to 3)
   - Manual entry fallback for creditor data

3. **Step 3 - Review & Generate:**
   - Display all extracted/entered data
   - Client information from search
   - Validate at least 1 creditor with bank info
   - Generate button to create document

**Key UI Elements:**
- `<FKFileUpload>` for PDF uploads (Cotizacion + Bank Certificates)
- `<FKAcreedorCard>` for displaying/editing creditor info
- Add/Remove creditor buttons (max 3, min 1)

#### 3. Add Service Methods

**File:** `frontend/src/services/legalService.ts` (modify existing file)

```typescript
export const legalService = {
  // ... existing methods

  parseCotizacionForMandato: async (file: File): Promise<CotizacionData> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/legal/contracts/instruccion-mandato/parse-cotizacion', formData);
    return response.data;
  },

  parseBankCertificate: async (file: File): Promise<AcreedorGastosNacionales> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/legal/contracts/instruccion-mandato/parse-bank-certificate', formData);
    return response.data;
  },

  generateInstruccionMandato: async (request: InstruccionMandatoRequest): Promise<ContractGenerationResponse> => {
    const response = await apiClient.post('/legal/contracts/instruccion-mandato/generate', request);
    return response.data;
  },
};
```

#### 4. Add Page/Route

**File:** `frontend/src/pages/legal/InstruccionMandatoPage.tsx`

- Import and render `<FKInstruccionMandatoForm>`
- Handle success/error states
- Navigate to review queue after generation

**File:** `frontend/src/App.tsx` (modify routing)

```tsx
<Route path="/legal/instruccion-mandato" element={
  <RoleProtectedRoute allowedRoles={['admin', 'legal']}>
    <InstruccionMandatoPage />
  </RoleProtectedRoute>
} />
```

---

> **Note:** DIAN Static Values Configuration is out of scope for this implementation. DIAN payments (`pl_co_dian_mandato_im`) will be implemented separately with a dedicated template and constants.

---

## Data Flow Diagram

```
+-------------------+                    +----------------------+
|   Frontend Form   |                    |      Backend API     |
+-------------------+                    +----------------------+
         |                                        |
         | 1. Upload Cotizacion PDF               |
         |--------------------------------------->|
         |                                        |
         |    Parse with CotizacionParserService  |
         |<---------------------------------------|
         |    Return: numero, fecha, monto        |
         |                                        |
         | 2. Upload Bank Certificate(s) [REQ]    |
         |--------------------------------------->|
         |                                        |
         |    Parse with BankCertParserService    |
         |<---------------------------------------|
         |    Return: bank account info           |
         |                                        |
         | 3. Submit generation request           |
         |--------------------------------------->|
         |                                        |
         |    DocumentService.generate_instruccion|
         |    _mandato_document()                 |
         |                                        |
         |    - Fill placeholders                 |
         |    - Populate creditor table           |
         |    - Generate DOCX                     |
         |<---------------------------------------|
         |    Return: contract_id, docx_url       |
         |                                        |
```

---

## Acceptance Criteria

### Backend
- [ ] `BankCertificateParserService` correctly extracts data from Bancolombia certificates
- [ ] `BankCertificateParserService` handles BBVA certificates (bonus)
- [ ] `generate_instruccion_mandato_document()` fills all placeholders correctly
- [ ] Nested creditor table populated with 1-3 creditors
- [ ] Amount displayed in both numbers and words (Spanish)
- [ ] API endpoints return proper error messages for invalid files
- [ ] Validation: Reject requests without at least 1 creditor with bank info

### Frontend
- [ ] Form successfully parses and displays Cotizacion data
- [ ] Bank Certificate upload and parsing works (required step)
- [ ] Multiple creditors can be added/removed (max 3, min 1)
- [ ] Form validation prevents submission without Bank Certificate
- [ ] Generated document downloads correctly

### Integration
- [ ] End-to-end flow: Upload Cotizacion -> Upload Bank Certificate(s) -> Add Creditors -> Generate -> Download
- [ ] Generated document matches expected format from template

---

## Files to Create

| File | Description |
|------|-------------|
| `backend/src/core/servicios/bank_certificate_parser_service.py` | Bank certificate PDF parser |
| `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` | Main form component |
| `frontend/src/components/ui/FKAcreedorCard.tsx` | Creditor info display card |
| `frontend/src/pages/legal/InstruccionMandatoPage.tsx` | Page component |

## Files to Modify

| File | Changes |
|------|---------|
| `backend/src/interface/legal_dtos.py` | Add `AcreedorGastosNacionales`, `InstruccionMandatoRequest` DTOs |
| `backend/src/core/servicios/document_service.py` | Add `generate_instruccion_mandato_document()` and helper methods |
| `backend/src/adapter/rest/legal_routes.py` | Add 3 new endpoints |
| `frontend/src/types/legal.ts` | Add TypeScript interfaces |
| `frontend/src/services/legalService.ts` | Add service methods |
| `frontend/src/App.tsx` | Add route for Instruccion de Mandato page |

---

## References

- **Data Sources Document:** `docs/20251207_INSTRUCCION_MANDATO_DATA_SOURCES.md`
- **Transcript:** `docs/20251207A TRANSCRIPT INSTRUCCION DE MANDATO.txt`
- **Template:** `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- **Example Cotizacion:** `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
- **Example Bank Certificate:** `Example FIles for Reqs/certificado bancario.pdf`
- **Contract Type:** `pl_co_mandato_im` (line 30 in `legal_dtos.py`)
- **Existing Parser Pattern:** `backend/src/core/servicios/cotizacion_parser_service.py`
- **Existing Document Service:** `backend/src/core/servicios/document_service.py`
