# Contract Generation System Overview

## Purpose

This document provides a comprehensive overview of the Finkargo Automation Hub's Legal Contract Automation system. Use this as a reference when defining requirements for new contract types to automate.

---

## Executive Summary

The Legal Contract Automation system eliminates manual contract creation by:

1. **Pulling client data** from a database (imported via CSV/Excel)
2. **Populating Word templates** with placeholder replacement
3. **Generating PDFs** via LibreOffice conversion
4. **Managing a review workflow** (Legal approves/rejects)
5. **Storing approved documents** in Supabase Storage for download

**Problem Solved:** Legal team was manually creating 3-15 contracts per day, spending 15+ minutes per contract copying data from the platform into Word templates. This system reduces contract generation to under 1 minute.

---

## Architecture

### Clean Architecture Layers

```
Frontend (React 19 / TypeScript 5):
├── Pages (OperationsDashboard, LegalDashboard)
├── Components (FKContractRequest, FKOtrosiRequest, FKInventarioRequest, FKReviewQueue)
├── Services (legalService, operationsService)
└── API Clients (axios with auth interceptors)

Backend (FastAPI / Python 3.11):
├── Adapter/REST (legal_routes.py, operations_routes.py)
├── Core/Servicios (contract_service.py, document_service.py)
├── Repositorio (contract_repository.py, client_repository.py, template_repository.py)
└── Interface/DTOs (legal_dtos.py)
```

### Key Files

| Layer | File | Purpose |
|-------|------|---------|
| Backend Routes | `backend/src/adapter/rest/legal_routes.py` | API endpoints for contract operations |
| Backend Service | `backend/src/core/servicios/contract_service.py` | Business logic orchestration |
| Backend Service | `backend/src/core/servicios/document_service.py` | Word template population & PDF conversion |
| Backend DTOs | `backend/src/interface/legal_dtos.py` | Data transfer objects and enums |
| Backend Repository | `backend/src/repositorio/contract_repository.py` | Database operations |
| Frontend Component | `frontend/src/components/forms/FKContractRequest.tsx` | Activos contract request form |
| Frontend Component | `frontend/src/components/forms/FKOtrosiRequest.tsx` | Otrosi contract request form |
| Frontend Component | `frontend/src/components/forms/FKInventarioRequest.tsx` | Inventario Bodega request form |
| Frontend Service | `frontend/src/services/operationsService.ts` | API client for operations |

---

## Contract Types Currently Supported

| Type | Contract ID Format | Template File | Color Badge | Description |
|------|-------------------|---------------|-------------|-------------|
| **Activos** | ACT-2025-XXX | FK COL - GM - Activos.docx | Blue (info) | Asset guarantee contracts |
| **Otrosi No. 1** | OTRO-2025-XXX | FK COL - K Marco - Otrosi No. 1.docx | Orange (warning) | Contract amendments |
| **Inventario Bodega** | INV-2025-XXX | FK COL - GM - Inventario Bodega de 3ro.docx | Green (success) | Third-party warehouse inventory |

---

## Data Model

### Client Data (Core Fields)

These fields are stored in the `clients` table and retrieved when generating any contract:

```python
# Required fields
nit: str                          # Colombian tax ID (e.g., "900123456-1")
nombre_importador: str            # Company legal name
representante_legal: str          # Legal representative full name
cedula_representante: str         # Legal rep ID number
ciudad_domicilio: str             # City of domicile
cupo_plataforma: Decimal          # Credit limit from platform

# Optional fields (enhance contract completeness)
direccion_comercial: str          # Commercial address
tipo_identificacion_representante: str  # ID type (CC, CE, Pasaporte)
nombre_contrato_marco: str        # Framework contract name
kam_nombre: str                   # Key Account Manager name
kam_email: str                    # KAM email
destinatario_nombre: str          # Recipient name for notifications
destinatario_email: str           # Recipient email
```

### Contract Generation Record

Each generated contract creates a record in `contract_generations`:

```python
id: UUID                          # Database UUID
contract_id: str                  # Business ID (e.g., ACT-2025-042)
contract_type: str                # "activos", "otrosi", "inventario_bodega"
client_nit: str                   # Reference to client
client_id: UUID                   # Foreign key to clients table
status: str                       # "under_review", "approved", "rejected"
generated_by: UUID                # User who requested
generated_at: datetime            # Timestamp
template_id: UUID                 # Template version used
template_version: str             # Semantic version (e.g., "1.0.0")
data_snapshot: JSON               # Snapshot of all data at generation time
reviewed_by: UUID                 # Legal reviewer (nullable)
reviewed_at: datetime             # Review timestamp (nullable)
review_notes: str                 # Rejection reason or comments (nullable)
pdf_url: str                      # Storage URL for generated PDF
approved_document_url: str        # Supabase Storage URL for approved PDF
```

### Additional Data (Contract-Type Specific)

**Custodian Data (Inventario Bodega only):**

Extracted from RUT PDF document uploaded by Operations:

```python
nombre_operador_custodio: str                          # Custodian company name
ciudad_domicilio_custodio: str                         # Custodian city
nit_operador_custodio: str                             # Custodian tax ID
nombre_representante_legal_custodio: str               # Custodian legal rep name
email_operador_custodio: str                           # Custodian email
cc_representante_legal_custodio: str                   # Custodian legal rep ID
tipo_identificacion_representante_legal_custodio: str  # ID type (CC, CE, etc.)
```

---

## Template Placeholder System

### How It Works

Word templates (.docx) contain bracketed placeholders like `[NOMBRE DEL CLIENTE]`. The `DocumentService` loads the template, replaces all placeholders with actual data, and saves the populated document.

### Standard Placeholders (All Contract Types)

**Client Information:**
```
[NOMBRE DEL CLIENTE]                    → nombre_importador (company name)
[NIT]                                   → nit (tax ID)
[Nombre del representante legal]        → representante_legal
[nombre del representante legal]        → representante_legal (lowercase variant)
[tipo de identificacion]                → tipo_identificacion_representante (CC, CE)
[identificacion RL]                     → cedula_representante
[nombre de la ciudad]                   → ciudad_domicilio
[Domicilio en que el Importador...]     → direccion_comercial or ciudad_domicilio
```

**Financial Information:**
```
[valor Cupo de Operaciones en numeros]  → Formatted currency (e.g., "$50.000.000")
[valor Cupo de Operaciones en letras]   → Number in Spanish words
[valor en numeros]                      → Same as above (alternate placeholder)
[valor en letras]                       → Same as above (alternate placeholder)
```

**Contract Metadata:**
```
[nombre del contrato marco]             → nombre_contrato_marco
[sic]                                   → contract_id (e.g., ACT-2025-042)
```

**Contact Information:**
```
[nombre del KAM]                        → kam_nombre
[KAM e-mail]                            → kam_email
[nombre del destinatario]               → destinatario_nombre
[destinatario e-mail]                   → destinatario_email
```

**Date Placeholders:**
```
[dia]                                   → Day number (e.g., "15")
[mes]                                   → Month name in Spanish (e.g., "noviembre")
[•]                                     → Last digit of year (for "202[•]" format)
```

### Contract-Type Specific Placeholders

**Inventario Bodega (Custodian Information):**
```
[NOMBRE DEL OPERADOR CUSTODIO]                              → nombre_operador_custodio
[nombre de la ciudad de domicilio del Operador Custodio]    → ciudad_domicilio_custodio
[NIT Operador Custodio]                                     → nit_operador_custodio
[nombre del representante legal del Operador Custodio]      → nombre_representante_legal_custodio
[e-mail del operador custodio]                              → email_operador_custodio
[CC representante legal del Operador Custodio]              → cc_representante_legal_custodio
[id RL del Operador Custodio]                               → cc_representante_legal_custodio
[tipo de id RL Operador Custodio]                           → tipo_identificacion_representante_legal_custodio
```

---

## Contract Generation Workflow

### End-to-End Flow

```
1. Operations User                    2. System                           3. Legal User
   │                                     │                                   │
   ├─► Search client by NIT/name         │                                   │
   │   ◄── Display client data ──────────┤                                   │
   │                                     │                                   │
   ├─► Select contract type              │                                   │
   ├─► (Optional) Upload RUT file        │                                   │
   ├─► Click "Request Contract"          │                                   │
   │                                     │                                   │
   │   ──── API: POST /generate ────────►│                                   │
   │                                     ├─► Validate client exists          │
   │                                     ├─► Get active template             │
   │                                     ├─► Generate contract ID            │
   │                                     ├─► Create data snapshot            │
   │                                     ├─► Save record (status: under_review)
   │   ◄── Return contract details ──────┤                                   │
   │                                     │                                   │
   │   ✓ Success: "Contract ID: ACT-2025-042"                                │
   │                                     │                                   │
   │                                     │   ◄── View pending queue ─────────┤
   │                                     │                                   │
   │                                     │   ──── Download DOCX/PDF ────────►│
   │                                     │   ◄── Review document ────────────┤
   │                                     │                                   │
   │                                     │   ◄── Approve/Reject ─────────────┤
   │                                     │                                   │
   │                                     ├─► On Approve:                     │
   │                                     │   ├─► Generate DOCX               │
   │                                     │   ├─► Convert to PDF (LibreOffice)│
   │                                     │   ├─► Upload to Supabase Storage  │
   │                                     │   └─► Update status: approved     │
   │                                     │                                   │
   │   ◄── View approved contracts ──────┤                                   │
   ├─► Download approved PDF             │                                   │
   └─► Send to client via DocuSign       │                                   │
```

### Contract Statuses

| Status | Description | Next Actions |
|--------|-------------|--------------|
| `under_review` | Contract generated, awaiting Legal review | Approve or Reject |
| `approved` | Legal approved, PDF available for download | Download, send to client |
| `rejected` | Legal rejected with notes | Re-request with corrections |

---

## API Endpoints

### Operations Endpoints

```http
POST /api/operations/contracts/generate
Content-Type: application/json (or multipart/form-data for file uploads)

Request Body:
{
  "client_nit": "900123456-1",
  "contract_type": "activos"  // or "otrosi", "inventario_bodega"
}

Response: ContractGenerationResponse
{
  "id": "uuid",
  "contract_id": "ACT-2025-042",
  "contract_type": "activos",
  "client_nit": "900123456-1",
  "status": "under_review",
  "generated_at": "2025-11-26T10:30:00Z",
  "data_snapshot": { ... }
}
```

```http
GET /api/operations/contracts/approved
Query Params: ?contract_type=activos&sort_by=reviewed_at&sort_order=desc

Response: List[ContractGenerationDetail]
```

### Legal Endpoints

```http
GET /api/legal/contracts/pending-review
Query Params: ?contract_type=activos

Response: List[ContractGenerationDetail]
```

```http
POST /api/legal/contracts/{contract_id}/review
Content-Type: application/json

Request Body:
{
  "action": "approve",  // or "reject"
  "notes": "Optional review comments"
}

Response: ContractReviewResponse
```

```http
GET /api/legal/contracts/{contract_id}/download/pdf
Response: StreamingResponse (application/pdf)

GET /api/legal/contracts/{contract_id}/download/docx
Response: StreamingResponse (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
```

---

## Key Services Implementation

### ContractService (contract_service.py)

Orchestrates the contract generation process:

```python
async def generate_contract(request: ContractGenerationRequest, user_id: str) -> Dict:
    # 1. Fetch client data by NIT
    client = await self.client_repo.get_by_nit(request.client_nit)

    # 2. Get active template for contract type
    template = await self.template_repo.get_active_template(contract_type)

    # 3. Generate sequential contract ID (ACT-2025-042)
    contract_id = await self.contract_repo.generate_contract_id(contract_type)

    # 4. Create data snapshot (immutable record of data at generation time)
    data_snapshot = {
        'nit': client['nit'],
        'nombre_importador': client['nombre_importador'],
        'contract_id': contract_id,
        'generation_date': datetime.utcnow().strftime('%Y-%m-%d'),
        # ... all other fields
    }

    # 5. Save contract record with status "under_review"
    contract = await self.contract_repo.create(contract_data)

    return contract
```

### DocumentService (document_service.py)

Handles Word template population and PDF conversion:

```python
def generate_contract_document(contract_data: Dict, template_name: str) -> bytes:
    # 1. Route to appropriate method based on contract type
    if contract_type == 'otrosi':
        return self.generate_otrosi_document(contract_data)
    elif contract_type == 'inventario_bodega':
        return self.generate_inventario_bodega_document(contract_data)
    else:
        return self.generate_activos_document(contract_data)

def generate_activos_document(contract_data: Dict, template_name: str) -> bytes:
    # 1. Load Word template
    doc = Document(template_path)

    # 2. Prepare replacements dictionary
    replacements = self._prepare_replacements(contract_data)

    # 3. Replace placeholders in paragraphs and tables
    for para in doc.paragraphs:
        self._replace_in_paragraph(para, replacements)

    # 4. Save to bytes and return
    return content

def convert_to_pdf(docx_bytes: bytes) -> bytes:
    # Uses LibreOffice headless mode for conversion
    # Works on Windows, Linux, and Mac
    cmd = [soffice_path, '--headless', '--convert-to', 'pdf', ...]
    subprocess.run(cmd)
    return pdf_bytes
```

---

## Adding a New Contract Type

### Checklist

To add a new contract type (e.g., "garantia_mercancia"), complete these steps:

#### 1. Database Migration

Create `backend/database/migration_add_[type]_support.sql`:

```sql
-- Step 1: Insert template record
INSERT INTO contract_templates (contract_type, version, template_content, active, notes)
VALUES ('garantia_mercancia', '1.0.0', 'FK COL - GM - Garantia Mercancia.docx', true, 'Description');

-- Step 2: Update generate_contract_id() function
CREATE OR REPLACE FUNCTION generate_contract_id(p_contract_type VARCHAR DEFAULT 'activos')
RETURNS VARCHAR AS $$
BEGIN
    IF p_contract_type = 'otrosi' THEN
        prefix := 'OTRO';
    ELSIF p_contract_type = 'inventario_bodega' THEN
        prefix := 'INV';
    ELSIF p_contract_type = 'garantia_mercancia' THEN  -- NEW
        prefix := 'GM';
    ELSE
        prefix := 'ACT';
    END IF;
    -- ... rest of function
END;
$$ LANGUAGE plpgsql;

-- Step 3: Initialize sequence
INSERT INTO contract_id_sequence (year, contract_type, last_sequence)
VALUES (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'garantia_mercancia', 0)
ON CONFLICT (year, contract_type) DO NOTHING;
```

#### 2. Backend Changes

**Add enum value** in `backend/src/interface/legal_dtos.py`:

```python
class ContractType(str, Enum):
    ACTIVOS = "activos"
    OTROSI = "otrosi"
    INVENTARIO_BODEGA = "inventario_bodega"
    GARANTIA_MERCANCIA = "garantia_mercancia"  # NEW
```

**Add generation method** (if unique placeholders) in `backend/src/core/servicios/document_service.py`:

```python
def generate_contract_document(self, contract_data: Dict, template_name: str) -> bytes:
    contract_type = contract_data.get('contract_type', 'activos')

    if contract_type == 'garantia_mercancia':  # NEW
        return self.generate_garantia_mercancia_document(contract_data)
    # ... existing types

def generate_garantia_mercancia_document(self, contract_data: Dict) -> bytes:
    template_path = self.template_dir / "FK COL - GM - Garantia Mercancia.docx"
    # ... template loading and replacement logic
```

#### 3. Frontend Changes

**Create request component** `frontend/src/components/forms/FKGarantiaMercanciaRequest.tsx`:
- Copy from existing component (e.g., `FKOtrosiRequest.tsx`)
- Update component name, icons, colors, button text, API method

**Add API method** in `frontend/src/services/operationsService.ts`:

```typescript
async requestGarantiaMercanciaGeneration(clientNit: string): Promise<ContractGeneration> {
  const request: ContractGenerationRequest = {
    client_nit: clientNit,
    contract_type: 'garantia_mercancia',
  };
  const response = await apiClient.post<ContractGeneration>(
    `${BASE_URL}/contracts/generate`,
    request
  );
  return response.data;
}
```

**Update badge helpers** in `FKReviewQueue.tsx` and `FKApprovedContracts.tsx`:

```typescript
const getContractTypeBadge = (contractType: string) => {
  if (contractType === 'garantia_mercancia') {  // NEW
    return { label: 'Garantia Mercancia', color: 'secondary' as const };
  }
  // ... existing types
};
```

**Add tab** to Operations Dashboard:

```tsx
<Tab label="Solicitar Garantia Mercancia" icon={<SecurityIcon />} iconPosition="start" />

<TabPanel value={currentTab} index={X}>
  <FKGarantiaMercanciaRequest />
</TabPanel>
```

#### 4. Template File

Add Word template to `backend/templates/`:
- File name must match `template_content` in database
- Use standard placeholder format: `[placeholder name]`
- Test all placeholders are correctly formatted

---

## Requirements Template for New Contract Types

When defining requirements for a new contract, provide:

### 1. Contract Identification

```
Contract Name: [Full name in Spanish]
Contract ID Prefix: [3-4 character prefix, e.g., "GM"]
Template File Name: [e.g., "FK COL - GM - Garantia Mercancia.docx"]
Badge Color: [info/warning/success/secondary/error]
```

### 2. Data Requirements

```
Required Client Fields:
- [ ] nit
- [ ] nombre_importador
- [ ] representante_legal
- [ ] cedula_representante
- [ ] ciudad_domicilio
- [ ] cupo_plataforma

Additional Data Needed:
- [ ] [Field name]: [Description] - [Source: user input / file upload / API]
```

### 3. Template Placeholders

```
Standard Placeholders Used:
- [NOMBRE DEL CLIENTE]
- [NIT]
- [etc...]

New Placeholders Required:
- [NEW PLACEHOLDER]: Maps to [data field]
```

### 4. Workflow Requirements

```
- [ ] Requires file upload? [Yes/No - describe file type]
- [ ] Requires additional user input? [Yes/No - describe fields]
- [ ] Special validation rules? [Describe]
- [ ] Different review process? [Describe]
```

### 5. User Interface

```
Tab Position: [After which existing tab?]
Icon: [MUI icon name]
Primary Color: [info/warning/success/etc.]
Spanish Labels:
  - Tab Label: "[...]"
  - Button Label: "[...]"
  - Success Message: "[...]"
```

---

## Reference Implementation

For a complete example of adding a new contract type, see:

- **Spec**: `specs/20251110_inventario_bodega_3ro_contract_type.md`
- **Implementation**: `implementations/20251110_inventario_bodega_contract_type_implementation.md`

These documents show the full process including RUT file upload and parsing for additional data extraction.

---

## Technical Constraints

### File Handling
- PDF generation requires LibreOffice installed on server
- Maximum file upload size: 5MB
- Supported upload formats: PDF only (for RUT parsing)

### Database
- Contract ID sequences are per-year, per-type (reset January 1st)
- Data snapshots are immutable JSON (audit trail)
- All tables have Row Level Security (RLS) enabled

### Performance
- Contract generation: 500-800ms
- PDF conversion: 2-4 seconds
- RUT parsing (if applicable): 200-400ms

---

**Document Version**: 1.0
**Created**: November 26, 2025
**Author**: Claude Code
**Purpose**: Reference for new contract type automation requirements
