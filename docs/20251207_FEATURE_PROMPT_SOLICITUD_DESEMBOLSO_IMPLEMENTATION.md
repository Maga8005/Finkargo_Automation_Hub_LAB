# Feature Prompt: Solicitud de Desembolso - Full Implementation

> **Purpose**: Complete implementation prompt for the `/feature` command to build the Solicitud de Desembolso document generation feature.

---

## Template Analysis

### Template Location
`backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`

### Placeholders Identified

| Placeholder | Description | Source |
|-------------|-------------|--------|
| `[Número de cotización de desembolso]` | Quote number (appears 2x) | Cotización PDF / User Input |
| `[día] de [mes] de 202[X]` | Request date | System (Current Date) |
| `CO:NIT:1:D:M:DOM` | Credit contract consecutive | Derived Formula |
| `[día de firma del contrato de crédito]` | Contract sign day | Cotización PDF / User Input |
| `[mes de firma del contrato de crédito]` | Contract sign month | Cotización PDF / User Input |
| `[año de firma del contrato de crédito]` | Contract sign year | Cotización PDF / User Input |
| `[monto]` | Disbursement amount (appears 2x) | Cotización PDF / User Input |
| `[número de días de plazo]` | Payment term days | Cotización PDF / User Input |

### Anexo I Table Structure

| Column | Description |
|--------|-------------|
| Acreedor del Gasto Nacional de Importación | Creditor name/type |
| No. de Instrumento de Pago | Payment instrument number |
| Monto del Instrumento de Pago (COP) | Amount per instrument |
| **TOTAL** | Sum of all amounts |

---

## Cotización PDF Analysis

### Example File
`Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`

### Extracted Data Points

| Field | Value in Example | Location in PDF |
|-------|------------------|-----------------|
| Fecha de Cotización | `10 de noviembre de 2025` | Page 1, header section |
| Número de Cotización | `CO:900436389:1:2:DOM` | Page 1, header section |
| Fecha Contrato de Crédito | `6 de noviembre de 2025` | Page 1, body text |
| Representante Legal | `Cesar Jose Castillo Soto` | Page 2 |
| Tipo ID Representante | `C.E.` | Page 2 |
| Número ID Representante | `814674` | Page 2 |
| Anexo Table | 3 rows with Entidad de pago de Impuestos | Page 3 |

### Anexo Table Example (Page 3)

| Acreedor | No. Instrumento | Monto (COP) |
|----------|-----------------|-------------|
| Entidad de pago de Impuestos | 1003887257 | $407,001.00 |
| Entidad de pago de Impuestos | 1003887254 | $290,000.00 |
| Entidad de pago de Impuestos | 1003887815 | $42,859.00 |
| **TOTAL** | | **$739,860.00** |

---

## Feature Prompt for `/feature` Command

```
Feature: Implement Solicitud de Desembolso Document Generation with Cotización PDF Upload

## Overview
Implement complete Solicitud de Desembolso document generation for Paga Local Colombia. This feature requires a specialized form that:
1. Allows PDF upload of the Cotización document from HubSpot
2. Extracts key fields from the uploaded Cotización PDF
3. Combines extracted data with client database information
4. Generates the Solicitud de Desembolso Word document with all placeholders filled
5. Sends to Legal review queue

## Current State
- Contract type `pl_co_solicitud_desembolso` exists with prefix `PLSD-`
- Template exists: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
- UI tab exists in `FKPagaLocalCODocumentosOperacion.tsx` using generic form
- No specialized form or PDF extraction logic exists

## Requirements

### 1. Backend: Cotización PDF Parser Service
Create `backend/src/core/servicios/cotizacion_parser_service.py`:

```python
class CotizacionParserService:
    """Extract data from Cotización PDF documents"""

    def parse_cotizacion(self, pdf_bytes: bytes) -> CotizacionData:
        """
        Extract fields from Cotización PDF:
        - numero_cotizacion: str (e.g., "CO:900436389:1:2:DOM")
        - fecha_cotizacion: date
        - fecha_contrato_credito: date
        - representante_legal: str
        - tipo_id_representante: str (CC, CE, etc.)
        - numero_id_representante: str
        - anexo_items: List[AnexoItem] with:
            - acreedor: str
            - numero_instrumento: str
            - monto: Decimal
        - monto_total: Decimal (sum of anexo items)
        """
```

PDF parsing approach:
- Use PyMuPDF (fitz) to extract text
- Page 1: Extract numero_cotizacion, fecha_cotizacion, fecha_contrato_credito
- Page 2: Extract representante_legal data
- Page 3: Parse Anexo table rows

### 2. Backend: Extended DTOs
Update `backend/src/interface/legal_dtos.py`:

```python
class AnexoItem(BaseModel):
    """Single row in Anexo I table"""
    acreedor: str
    numero_instrumento: str
    monto: Decimal

class SolicitudDesembolsoRequest(BaseModel):
    """Request for Solicitud de Desembolso generation"""
    client_nit: str
    # From Cotización (user input or PDF extraction)
    numero_cotizacion_desembolso: str
    fecha_contrato_credito: date
    monto: Decimal
    dias_plazo: int = 120
    # Anexo items
    anexo_items: List[AnexoItem]
    # Optional: uploaded cotizacion PDF for reference
    cotizacion_pdf_base64: Optional[str] = None

class CotizacionData(BaseModel):
    """Extracted data from Cotización PDF"""
    numero_cotizacion: str
    fecha_cotizacion: date
    fecha_contrato_credito: date
    representante_legal: Optional[str]
    tipo_id_representante: Optional[str]
    numero_id_representante: Optional[str]
    anexo_items: List[AnexoItem]
    monto_total: Decimal
```

### 3. Backend: Document Service Handler
Add to `backend/src/core/servicios/document_service.py`:

```python
def generate_solicitud_desembolso_document(self, contract_data: Dict[str, Any]) -> bytes:
    """Generate Solicitud de Desembolso from template"""
    template_name = "FK COL - Fin. COP - Solicitud de Desembolso.docx"

    # Prepare replacements
    replacements = self._prepare_solicitud_desembolso_replacements(contract_data)

    # Load and populate template
    # Handle Anexo I table population

def _prepare_solicitud_desembolso_replacements(self, data: Dict) -> Dict[str, str]:
    """Map data to template placeholders"""
    return {
        '[Número de cotización de desembolso]': data['numero_cotizacion_desembolso'],
        '[día]': str(datetime.now().day),
        '[mes]': self._get_spanish_month(datetime.now().month),
        '202[X]': str(datetime.now().year),
        'CO:NIT:1:D:M:DOM': self._generate_consecutivo(data['nit']),
        '[día de firma del contrato de crédito]': str(data['fecha_contrato_credito'].day),
        '[mes de firma del contrato de crédito]': self._get_spanish_month(data['fecha_contrato_credito'].month),
        '[año de firma del contrato de crédito]': str(data['fecha_contrato_credito'].year),
        '[monto]': self._format_currency(data['monto']),
        '[número de días de plazo]': str(data['dias_plazo']),
    }

def _generate_consecutivo(self, nit: str) -> str:
    """Generate credit contract consecutive: CO:{NIT}:1:D:M:DOM"""
    return f"CO:{nit}:1:D:M:DOM"
```

### 4. Backend: API Endpoint
Add to `backend/src/adapter/rest/operations_routes.py`:

```python
@router.post("/contracts/solicitud-desembolso/parse-cotizacion")
async def parse_cotizacion_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_operations_role)
) -> CotizacionData:
    """Parse uploaded Cotización PDF and return extracted data"""

@router.post("/contracts/solicitud-desembolso/generate")
async def generate_solicitud_desembolso(
    request: SolicitudDesembolsoRequest,
    current_user: dict = Depends(require_operations_role)
) -> ContractGenerationResponse:
    """Generate Solicitud de Desembolso document"""
```

### 5. Frontend: Specialized Form Component
Create `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`:

**Form Sections:**

1. **Client Search Section** (existing pattern)
   - Search by NIT or name
   - Display selected client info

2. **Cotización Upload Section** (NEW)
   - PDF file upload dropzone
   - "Extraer Datos" button to parse PDF
   - Show extraction status/results

3. **Cotización Data Section** (editable after extraction)
   - Número de Cotización de Desembolso (text, required)
   - Fecha del Contrato de Crédito (date picker, required)
   - Monto Total (currency, required, auto-calculated)
   - Días de Plazo (number, default 120)

4. **Anexo I Table Section** (dynamic rows)
   - Add/remove row buttons
   - Columns: Acreedor, No. Instrumento, Monto
   - Auto-sum total at bottom
   - Pre-populated from PDF extraction

5. **Preview & Submit Section**
   - Show all data before submission
   - "Solicitar Documento" button

**State Management:**
```typescript
interface SolicitudDesembolsoFormState {
  // Client
  selectedClient: Client | null;

  // Cotización extraction
  cotizacionFile: File | null;
  extractedData: CotizacionData | null;
  isExtracting: boolean;

  // Form fields (editable)
  numeroCotizacion: string;
  fechaContrato: Date | null;
  diasPlazo: number;
  anexoItems: AnexoItem[];

  // Calculated
  montoTotal: number;
}
```

### 6. Frontend: Type Definitions
Add to `frontend/src/types/legal.ts`:

```typescript
export interface AnexoItem {
  acreedor: string;
  numeroInstrumento: string;
  monto: number;
}

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

export interface SolicitudDesembolsoRequest {
  client_nit: string;
  numero_cotizacion_desembolso: string;
  fecha_contrato_credito: string;
  monto: number;
  dias_plazo: number;
  anexo_items: AnexoItem[];
}
```

### 7. Frontend: Service Layer
Add to `frontend/src/services/operationsService.ts`:

```typescript
async parseCotizacionPdf(file: File): Promise<CotizacionData> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/operations/contracts/solicitud-desembolso/parse-cotizacion', formData);
  return response.data;
}

async generateSolicitudDesembolso(request: SolicitudDesembolsoRequest): Promise<ContractGeneration> {
  const response = await apiClient.post('/operations/contracts/solicitud-desembolso/generate', request);
  return response.data;
}
```

### 8. Integration
Update `FKPagaLocalCODocumentosOperacion.tsx`:
- Replace generic `FKPagaLocalCOContractRequest` with `FKSolicitudDesembolsoRequest` for the Solicitud Desembolso tab

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Search & Select Client (NIT)                                │
│  2. Upload Cotización PDF                                       │
│  3. Click "Extraer Datos"                                       │
│  4. Review/Edit extracted data                                  │
│  5. Click "Solicitar Documento"                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                                 │
├─────────────────────────────────────────────────────────────────┤
│  FROM CLIENT DATABASE:          │  FROM COTIZACIÓN PDF:         │
│  - NIT                          │  - Número de cotización       │
│  - Nombre importador            │  - Fecha contrato crédito     │
│  - Representante legal          │  - Anexo I table items        │
│  - Cédula representante         │  - Monto total (calculated)   │
│  - Ciudad domicilio             │                               │
├─────────────────────────────────────────────────────────────────┤
│  SYSTEM GENERATED:              │  USER INPUT:                  │
│  - Fecha solicitud (today)      │  - Días de plazo (default 120)│
│  - Consecutivo contrato         │  - Edits to extracted data    │
│    (CO:{NIT}:1:D:M:DOM)         │                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TEMPLATE POPULATION                             │
├─────────────────────────────────────────────────────────────────┤
│  Template: FK COL - Fin. COP - Solicitud de Desembolso.docx     │
│                                                                  │
│  Placeholders filled:                                            │
│  - [Número de cotización de desembolso] → numeroCotizacion      │
│  - [día] de [mes] de 202[X] → Current date                      │
│  - CO:NIT:1:D:M:DOM → Generated consecutivo                     │
│  - [fecha firma contrato] → From cotización                     │
│  - [monto] → Total from anexo items                             │
│  - [días plazo] → User input or default 120                     │
│  - Anexo I Table → Dynamic rows from anexo_items                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LEGAL REVIEW QUEUE                             │
├─────────────────────────────────────────────────────────────────┤
│  Status: under_review                                            │
│  Contract ID: PLSD-2025-001                                      │
│  Awaiting Legal approval                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Acceptance Criteria

1. ✅ User can upload Cotización PDF and extract data automatically
2. ✅ Extracted data is editable before submission
3. ✅ Anexo I table supports dynamic rows (add/remove)
4. ✅ Monto total auto-calculates from Anexo items
5. ✅ Generated document has all placeholders correctly filled
6. ✅ Anexo I table in document matches user input
7. ✅ Document is sent to Legal review queue with status `under_review`
8. ✅ Legal can approve/reject using existing workflow
9. ✅ Approved PDF downloadable from Contratos Aprobados tab

## Files to Create/Modify

### New Files
- `backend/src/core/servicios/cotizacion_parser_service.py`
- `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`

### Modified Files
- `backend/src/interface/legal_dtos.py` - Add new DTOs
- `backend/src/adapter/rest/operations_routes.py` - Add endpoints
- `backend/src/core/servicios/document_service.py` - Add handler
- `frontend/src/types/legal.ts` - Add types
- `frontend/src/services/operationsService.ts` - Add service methods
- `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx` - Use new component
```

---

## References

- Template: `backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`
- Example Cotización: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`
- Data Sources: `docs/20251207_SOLICITUD_DESEMBOLSO_DATA_SOURCES.md`
- Transcript: `docs/20251207 TRANSCRIPT SOLICITUD DE DESEMBOLSO.txt`
- Contract Type: `pl_co_solicitud_desembolso`
- ID Prefix: `PLSD-`
