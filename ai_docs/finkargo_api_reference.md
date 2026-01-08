# Finkargo Automation Hub - API Reference

## Base URLs

| Environment | URL |
|-------------|-----|
| Development | `http://localhost:8000/api` |
| Production | `https://finkargo-automation-hub.onrender.com/api` |

## Authentication

All protected endpoints require a JWT Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

Tokens are obtained through Supabase Auth and automatically managed by the frontend.

---

## Health & Utility Endpoints

### GET /api/health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "app": "Finkargo Automation Hub",
  "version": "1.0.0"
}
```

### GET /api/debug/cors
Debug CORS configuration.

**Response:**
```json
{
  "cors_origins_raw": "[\"http://localhost:5173\"]",
  "cors_origins_parsed": ["http://localhost:5173"],
  "cors_origins_type": "<class 'list'>",
  "note": "This endpoint helps debug CORS configuration issues"
}
```

### GET /api/departments
Get list of Finkargo departments.

**Response:**
```json
{
  "departments": [
    {"id": "operations", "name": "Operaciones", "icon": "Settings"},
    {"id": "legal", "name": "Legal", "icon": "Gavel"},
    {"id": "finance", "name": "Finanzas", "icon": "AttachMoney"}
  ]
}
```

---

## Authentication Endpoints (`/api/auth`)

### POST /api/auth/login
Authenticate user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "user": { "id": "uuid", "email": "user@example.com" },
  "session": { "access_token": "jwt...", "expires_at": 1234567890 }
}
```

### POST /api/auth/register
Register new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "user_type": "funcionario",
  "role": "user"
}
```

### GET /api/auth/me
Get current user profile.

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "legal",
  "user_type": "funcionario",
  "is_active": true
}
```

---

## Legal Endpoints (`/api/legal`)

**Required Role:** `legal` or `admin`

### Client Management

#### GET /api/legal/clients/search
Search clients by NIT or name.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| query | string | General search term |
| nit | string | Client NIT (tax ID) |
| nombre | string | Company name |
| is_active | boolean | Filter by active status |

**Response:**
```json
[
  {
    "id": "uuid",
    "nit": "900123456-1",
    "nombre_importador": "EMPRESA S.A.S.",
    "representante_legal": "Juan Pérez",
    "cedula_representante": "1234567890",
    "ciudad_domicilio": "Bogotá",
    "cupo_plataforma": 50000000,
    "is_active": true
  }
]
```

#### GET /api/legal/clients/{nit}
Get client by NIT.

**Response:** Same as search result object.

#### POST /api/legal/clients
Create new client.

**Request:**
```json
{
  "nit": "900123456-1",
  "nombre_importador": "EMPRESA S.A.S.",
  "representante_legal": "Juan Pérez",
  "cedula_representante": "1234567890",
  "ciudad_domicilio": "Bogotá",
  "cupo_plataforma": 50000000
}
```

#### PUT /api/legal/clients/{client_id}
Update client.

#### POST /api/legal/clients/import
Bulk import clients from CSV/Excel.

**Request:** `multipart/form-data` with `file` field.

**Response:**
```json
{
  "total_processed": 100,
  "successful": 95,
  "failed": 5,
  "errors": ["Row 3: Invalid NIT format", "Row 7: Missing required field"],
  "import_id": "uuid"
}
```

### Contract Management

#### GET /api/legal/contracts/stats
Get contract statistics.

**Response:**
```json
{
  "total_generated": 150,
  "pending_review": 12,
  "approved": 130,
  "rejected": 8,
  "generated_today": 5,
  "generated_this_week": 25,
  "generated_this_month": 75
}
```

#### GET /api/legal/contracts/pending-review
Get contracts pending legal review.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| contract_type | string | Filter by type: `activos`, `otrosi`, `inventario_bodega` |

**Response:**
```json
[
  {
    "id": "uuid",
    "contract_id": "ACT-2025-033",
    "contract_type": "activos",
    "client_nit": "900123456-1",
    "status": "under_review",
    "generated_by": "user-uuid",
    "created_at": "2025-01-15T10:30:00Z",
    "data_snapshot": {
      "nombre_importador": "EMPRESA S.A.S.",
      "cupo_plataforma": 50000000
    }
  }
]
```

#### GET /api/legal/contracts
Get contract history with filters.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status |
| client_nit | string | Filter by client NIT |
| date_from | datetime | Start date filter |
| date_to | datetime | End date filter |
| limit | int | Results per page (default: 50) |
| offset | int | Pagination offset |

#### GET /api/legal/contracts/{contract_id}
Get contract details by ID (UUID or business ID like ACT-2025-033).

#### GET /api/legal/contracts/{contract_id}/preview
Get populated contract content for preview.

**Response:**
```json
{
  "content": "CONTRATO DE COMPRAVENTA DE CARTERA..."
}
```

#### POST /api/legal/contracts/{contract_id}/review
Review contract (approve or reject).

**Request:**
```json
{
  "action": "approve",  // or "reject"
  "notes": "Optional review notes"
}
```

**Response:**
```json
{
  "id": "uuid",
  "contract_id": "ACT-2025-033",
  "status": "approved",
  "reviewed_by": "reviewer-uuid",
  "reviewed_at": "2025-01-15T14:00:00Z",
  "review_notes": "Approved without changes",
  "approved_document_url": "https://supabase.co/storage/..."
}
```

### Document Downloads

#### GET /api/legal/contracts/{contract_id}/download/docx
Download contract as Word document.

**Response:** Binary DOCX file with `Content-Disposition: attachment`.

#### GET /api/legal/contracts/{contract_id}/download/pdf
Download contract as PDF.

**Response:** Binary PDF file with `Content-Disposition: attachment`.

### Templates

#### GET /api/legal/templates/active
Get active contract template.

**Response:**
```json
{
  "id": "uuid",
  "version": "2.0",
  "template_content": "CONTRATO DE..."
}
```

---

## Operations Endpoints (`/api/operations`)

**Required Role:** `operations` or `admin`

### Contract Generation

#### POST /api/operations/contracts/generate
Request new contract generation.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client_nit | string | Yes | Client NIT |
| contract_type | string | Yes | `activos`, `otrosi`, or `inventario_bodega` |
| rut_file | file | Only for `inventario_bodega` | RUT PDF document |

**Response:**
```json
{
  "id": "uuid",
  "contract_id": "ACT-2025-034",
  "contract_type": "activos",
  "client_nit": "900123456-1",
  "status": "under_review",
  "generated_by": "user-uuid",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### GET /api/operations/contracts/approved
Get approved contracts for download.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| contract_type | string | Filter by type |
| sort_by | string | Sort field (contract_id, reviewed_at, etc.) |
| sort_order | string | `asc` or `desc` |
| client_name | string | Filter by name (partial match) |
| client_nit | string | Filter by NIT (partial match) |
| date_from | string | Filter by approval date >= |
| date_to | string | Filter by approval date <= |
| cupo_min | float | Filter by credit limit >= |
| cupo_max | float | Filter by credit limit <= |

**Response:**
```json
[
  {
    "id": "uuid",
    "contract_id": "ACT-2025-033",
    "contract_type": "activos",
    "client_nit": "900123456-1",
    "status": "approved",
    "reviewed_at": "2025-01-15T14:00:00Z",
    "approved_document_url": "https://supabase.co/storage/...",
    "data_snapshot": {
      "nombre_importador": "EMPRESA S.A.S.",
      "cupo_plataforma": 50000000
    }
  }
]
```

#### GET /api/operations/contracts/{contract_id}
Get contract details.

#### GET /api/operations/contracts/{contract_id}/download/pdf
Download approved contract PDF from storage.

---

## Finance Endpoints (`/api/finance`)

**Required Role:** Any authenticated user

### Excel Processing

#### POST /api/finance/upload-excel
Upload and validate master Excel file.

**Request:** `multipart/form-data` with Excel file.

**Required Columns:**
- UUID
- CODIGO DE OPERACIÓN
- Conceptos
- Fecha emision
- RFC receptor
- Razon receptor
- SubTotal
- IVA Trasladado
- IVA Exento
- Total

**Response:**
```json
{
  "session_id": "uuid",
  "valid": true,
  "data": [
    {
      "uuid": "ABC123...",
      "codigo_operacion": "OP-001",
      "conceptos": "Servicio de flete",
      "fecha_emision": "2025-01-15",
      "rfc_receptor": "XAXX010101000",
      "razon_receptor": "EMPRESA S.A.",
      "subtotal": 10000.00,
      "iva_trasladado": 1600.00,
      "iva_exento": 0.00,
      "total": 11600.00
    }
  ],
  "errors": [],
  "drive_sync_stats": {
    "new": 5,
    "updated": 2,
    "unchanged": 93
  }
}
```

### Invoice Search

#### POST /api/finance/search
Search invoices in session.

**Request:**
```json
{
  "session_id": "uuid",
  "search_type": "codigo_operacion",  // or "rfc", "fecha"
  "codigo_operacion": "OP-001",       // when search_type = "codigo_operacion"
  "rfc": "XAXX010101000",             // when search_type = "rfc"
  "fecha_inicio": "2025-01-01",       // optional date range
  "fecha_fin": "2025-01-31"           // optional date range
}
```

**Response:**
```json
{
  "results": [...],
  "total_found": 15,
  "total_amount": 175000.00
}
```

### Session Management

#### GET /api/finance/session/{session_id}/stats
Get session statistics.

**Response:**
```json
{
  "session_id": "uuid",
  "total_records": 100,
  "total_amount": 1500000.00,
  "total_subtotal": 1293103.45,
  "total_iva": 206896.55,
  "unique_rfcs": 25,
  "unique_operaciones": 40
}
```

#### DELETE /api/finance/session/{session_id}
Clear session data from cache.

### ZIP Generation

#### POST /api/finance/generate-zip
Generate ZIP package with PDFs, XMLs, and Excel report.

**Request:**
```json
{
  "session_id": "uuid",
  "uuids": ["uuid1", "uuid2"],  // specific invoices
  "search_criteria": {},         // or use search criteria
  "metadata": {
    "codigo_operacion": "OP-001"
  }
}
```

**Response:** Binary ZIP file with:
- `PDFs/` folder with PDF files
- `XMLs/` folder with XML files
- Excel report with invoice details

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

---

## Rate Limiting

Currently no rate limiting is implemented. Plan for future implementation.

---

## Pagination

Endpoints supporting pagination use:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | int | 50 | Results per page |
| offset | int | 0 | Starting position |

Example:
```
GET /api/legal/contracts?limit=20&offset=40
```
