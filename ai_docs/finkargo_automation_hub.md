# Finkargo Automation Hub - Application Documentation

## Overview

Finkargo Automation Hub is an enterprise automation platform for Finkargo's business operations in Colombian logistics. It's a monorepo containing a React frontend and FastAPI backend that automates:

- **Legal Contract Generation** - Automated contract creation and approval workflows
- **Operations Workflows** - Contract requests and document management
- **Financial Reporting** - Mexico invoicing automation with Google Drive integration

### Production URLs
- **Frontend**: https://finkargo-automation-hub.vercel.app/
- **Backend API**: https://finkargo-automation-hub.onrender.com/api
- **API Docs**: https://finkargo-automation-hub.onrender.com/docs

---

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React + TypeScript + Vite | React 19.1, Vite 7.1 |
| **UI Library** | Material-UI (MUI) | 7.3.4 |
| **State Management** | React Context API | - |
| **Forms** | react-hook-form | 7.64.0 |
| **Backend** | FastAPI + Python | Python 3.11.9, FastAPI 0.104.1+ |
| **Database** | PostgreSQL (Supabase) | - |
| **Authentication** | Supabase Auth (JWT) | - |
| **Storage** | Supabase Storage | - |
| **Frontend Hosting** | Vercel | - |
| **Backend Hosting** | Render | - |

---

## Architecture

### Clean Architecture Pattern

The application follows Clean Architecture with strict layer separation:

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  pages/ → components/ → services/ → api/                       │
│   (UI)    (Reusable)    (Logic)    (HTTP)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│  adapter/rest/ → core/servicios/ → repositorio/ → database     │
│  (Controllers)   (Business Logic)  (Data Access)               │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
Finkargo_Automation_Hub/
├── frontend/                    # React application
│   └── src/
│       ├── api/clients/         # Axios HTTP clients
│       ├── components/          # UI components (FK-prefixed)
│       │   ├── forms/           # Form components
│       │   ├── ui/              # Layout components
│       │   └── declaraciones/   # Module-specific
│       ├── contexts/            # React Context providers
│       ├── hooks/               # Custom React hooks
│       ├── pages/               # Route pages
│       │   ├── legal/           # Legal module
│       │   ├── operations/      # Operations module
│       │   └── finance/         # Finance module
│       ├── services/            # API service layer
│       ├── types/               # TypeScript types
│       └── theme/               # MUI theme
├── backend/                     # FastAPI application
│   └── src/
│       ├── adapter/rest/        # API routes
│       ├── core/servicios/      # Business logic
│       ├── repositorio/         # Data access
│       ├── interface/           # DTOs
│       ├── config/              # Configuration
│       └── models/              # SQLAlchemy models
├── scripts/                     # Development scripts
├── specs/                       # Feature specifications
└── implementations/             # Implementation notes
```

---

## Authentication System

### Flow Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  LoginPage   │────►│ Supabase Auth│────►│ AuthContext  │
│              │     │   (JWT)      │     │   Provider   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                           ┌──────────────────────────────┐
                           │  user_profiles table fetch   │
                           │  (role, permissions)         │
                           └──────────────────────────────┘
```

### Authentication Context (`frontend/src/contexts/AuthContext.tsx`)

The AuthContext provides global authentication state:

```typescript
interface AuthContextType {
  user: SupabaseUser | null;        // Supabase auth user
  session: Session | null;           // JWT session
  userProfile: UserProfile | null;   // Extended profile from DB
  loading: boolean;                  // Auth loading state
  isTransitioning: boolean;          // Login transition state
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (...) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
  revalidateSession: () => Promise<boolean>;
}
```

**Key Features:**
- Profile caching (5-minute TTL) for fast authentication
- Automatic session revalidation every 5 minutes
- Window focus session validation
- Token refresh handling

### Route Protection

Two components protect routes:

1. **ProtectedRoute** - Requires authentication only
2. **RoleProtectedRoute** - Requires specific role(s)

```typescript
// Authentication only
<ProtectedRoute>
  <HomePage />
</ProtectedRoute>

// Role-based access
<RoleProtectedRoute allowedRoles={[UserRole.LEGAL]}>
  <LegalDashboard />
</RoleProtectedRoute>
```

### User Roles

| Role | Description | Access |
|------|-------------|--------|
| `admin` | Full system access | All modules |
| `legal` | Legal department | Contract review/approval |
| `operations` | Operations team | Contract requests, approved downloads |
| `commercial` | Sales operations | Limited access |
| `analyst` | Data analysis | Read-only access |
| `mesa_control` | Control desk | Specific workflows |
| `manager` | Department supervision | Department-wide access |
| `user` | Basic authenticated | Limited access |
| `cliente` | External client | Client dashboard only |

### Backend RBAC (`backend/src/adapter/rest/rbac_dependencies.py`)

```python
# Pre-configured role dependencies
require_legal_role = require_roles(['legal'])           # Legal or Admin
require_operations_role = require_roles(['operations']) # Operations or Admin
require_admin_role = require_roles(['admin'], allow_admin=False)  # Admin only

# Usage in routes
@router.post("/contracts/generate")
async def generate_contract(
    current_user: dict = Depends(require_operations_role)
):
    # Only operations team or admins can access
    pass
```

---

## Module Documentation

### 1. Legal Module

**Purpose:** Review and approve contracts generated by Operations.

**Route:** `/department/legal`

**Access:** `legal` role or `admin`

#### Components

| Component | File | Description |
|-----------|------|-------------|
| LegalDashboard | `pages/legal/LegalDashboard.tsx` | Main dashboard with tabs |
| FKReviewQueue | `components/forms/FKReviewQueue.tsx` | Contract review queue |
| FKClientDataImport | `components/forms/FKClientDataImport.tsx` | CSV/Excel import |

#### API Endpoints (`/api/legal`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/clients/search` | Search clients by NIT/name |
| GET | `/clients/{nit}` | Get client by NIT |
| POST | `/clients/import` | Bulk import from CSV/Excel |
| GET | `/contracts/stats` | Contract statistics |
| GET | `/contracts/pending-review` | Contracts awaiting review |
| GET | `/contracts/{id}` | Contract details |
| POST | `/contracts/{id}/review` | Approve/reject contract |
| GET | `/contracts/{id}/download/docx` | Download as DOCX |
| GET | `/contracts/{id}/download/pdf` | Download as PDF |

#### Contract Review Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Pending   │────►│   Review    │────►│  Approved   │
│   Review    │     │   Queue     │     │  or Reject  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Generate   │
                    │  PDF & Save │
                    └─────────────┘
```

---

### 2. Operations Module

**Purpose:** Request contracts and download approved documents.

**Routes:**
- `/operations/contratos-colombia` - Colombia contracts
- `/operations/contratos-mexico` - Mexico contracts

**Access:** `operations` role or `admin`

#### Components

| Component | File | Description |
|-----------|------|-------------|
| OperationsContractsColombia | `pages/operations/OperationsContractsColombia.tsx` | Main dashboard |
| FKContractRequest | `components/forms/FKContractRequest.tsx` | Request Activos contract |
| FKOtrosiRequest | `components/forms/FKOtrosiRequest.tsx` | Request Otrosí contract |
| FKInventarioRequest | `components/forms/FKInventarioRequest.tsx` | Request Inventario Bodega |
| FKApprovedContracts | `components/forms/FKApprovedContracts.tsx` | View/download approved |

#### Contract Types

| Type | Description | Template |
|------|-------------|----------|
| `activos` | Asset financing contract | FK COL - GM - Activos.docx |
| `otrosi` | Amendment to master contract | FK COL - K Marco - Otrosí No. 1.docx |
| `inventario_bodega` | Third-party warehouse inventory | FK COL - GM - Inventario Bodega de 3ro.docx |

#### API Endpoints (`/api/operations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contracts/generate` | Request new contract |
| GET | `/contracts/approved` | List approved contracts |
| GET | `/contracts/{id}` | Contract details |
| GET | `/contracts/{id}/download/pdf` | Download approved PDF |

#### Contract Generation Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Operations    │────►│   Create        │────►│   Legal         │
│   Requests      │     │   UNDER_REVIEW  │     │   Reviews       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
         ┌──────────────────────────────────────────────┤
         ▼                                              ▼
┌─────────────────┐                           ┌─────────────────┐
│   REJECTED      │                           │   APPROVED      │
│   (with notes)  │                           │   + PDF saved   │
└─────────────────┘                           └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   Operations    │
                                              │   Downloads     │
                                              └─────────────────┘
```

---

### 3. Finance Module

**Purpose:** Mexico invoicing automation with Excel processing and Google Drive integration.

**Routes:**
- `/finance/reporteria-automatica-co` - Colombia reporting
- `/finance/reporteria-automatica-mx` - Mexico invoicing

**Access:** Authenticated users

#### Components

| Component | File | Description |
|-----------|------|-------------|
| ReporteriaAutomaticaMX | `pages/finance/ReporteriaAutomaticaMX.tsx` | Main dashboard |
| FKExcelUploader | `components/forms/FKExcelUploader.tsx` | Excel file upload |

#### API Endpoints (`/api/finance`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-excel` | Upload and validate Excel |
| POST | `/search` | Search invoices in session |
| GET | `/session/{id}/stats` | Session statistics |
| DELETE | `/session/{id}` | Clear session data |
| POST | `/generate-zip` | Generate ZIP with PDFs/XMLs |

#### Mexico Invoicing Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Upload        │────►│   Validate &    │────►│   Sync with     │
│   Excel File    │     │   Parse         │     │   Google Drive  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Download      │◄────│   Generate      │◄────│   Search &      │
│   ZIP Package   │     │   ZIP Bundle    │     │   Filter        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### Excel Required Columns

| Column | Description |
|--------|-------------|
| UUID | Invoice unique identifier |
| CODIGO DE OPERACIÓN | Operation code |
| Conceptos | Invoice concepts |
| Fecha emision | Issue date |
| RFC receptor | Recipient RFC |
| Razon receptor | Recipient business name |
| SubTotal | Subtotal amount |
| IVA Trasladado | Transferred VAT |
| IVA Exento | Exempt VAT |
| Total | Total amount |

---

## Backend Services

### ContractService (`backend/src/core/servicios/contract_service.py`)

Core business logic for contract operations:

```python
class ContractService:
    async def generate_contract(request, user_id) -> Dict
    async def review_contract(contract_id, action, reviewer_id, notes) -> Dict
    async def get_contract_details(contract_id) -> Optional[Dict]
    async def get_pending_reviews(contract_type) -> list
    async def get_approved_contracts(contract_type) -> list
    async def get_contract_stats() -> Dict[str, int]
    async def populate_template(contract_id) -> str
    async def generate_contract_document(contract_id) -> bytes  # DOCX
    async def generate_contract_pdf(contract_id) -> bytes       # PDF
```

### DocumentService (`backend/src/core/servicios/document_service.py`)

Document generation and PDF conversion:

```python
class DocumentService:
    def generate_contract_document(contract_data) -> bytes  # DOCX generation
    def convert_to_pdf(docx_bytes) -> bytes                 # PDF conversion
    def upload_to_storage(pdf_bytes, contract_id) -> str    # Supabase upload
```

### RUTParserService (`backend/src/core/servicios/rut_parser_service.py`)

Parses Colombian RUT (tax ID) PDFs to extract custodian information for Inventario Bodega contracts.

### CSVTemplateMapper (`backend/src/core/servicios/csv_template_mapper.py`)

Maps CSV/Excel columns to database fields, supporting multiple template formats.

---

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `auth.users` | Supabase built-in authentication |
| `user_profiles` | Extended user data with roles |
| `clients` | Imported client data (NIT, company info) |
| `contract_templates` | Versioned contract templates |
| `contract_generations` | Contract audit trail |
| `contract_id_sequence` | Sequential ID generator |
| `data_imports` | CSV/Excel import history |

### Contract ID Format

```
{TYPE}-{YEAR}-{SEQUENCE}

Examples:
- ACT-2025-001  (Activos)
- OTR-2025-015  (Otrosí)
- INV-2025-003  (Inventario Bodega)
```

### Contract Statuses

| Status | Description |
|--------|-------------|
| `under_review` | Awaiting legal review |
| `approved` | Approved by legal |
| `rejected` | Rejected with notes |
| `generated` | Legacy status |

---

## Frontend Services

### API Client (`frontend/src/api/clients/apiClient.ts`)

Axios instance with:
- Base URL configuration
- JWT token injection via interceptors
- Error handling

### Service Layer

| Service | File | Description |
|---------|------|-------------|
| legalService | `services/legalService.ts` | Legal contract operations |
| operationsService | `services/operationsService.ts` | Operations contract requests |
| financeService | `services/financeService.ts` | Finance/invoicing operations |
| supabase | `services/supabase.ts` | Supabase client instance |

---

## Development Commands

### Frontend

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Dev server (http://localhost:5173)
npm run build        # Production build
npm run lint         # Lint code
npm run preview      # Preview production build
```

### Backend

```bash
cd backend
python -m venv venv                    # Create virtual environment
source venv/bin/activate               # Activate (Mac/Linux)
pip install -r requirements.txt        # Install dependencies
python -m uvicorn main:app --reload    # Dev server (http://localhost:8000)
```

### Quick Start Scripts

```bash
# Start both servers
./scripts/start-dev.sh

# Stop servers
./scripts/stop-dev.sh
```

---

## Environment Variables

### Frontend (.env)

```bash
VITE_SUPABASE_URL=https://[project-id].supabase.co
VITE_SUPABASE_ANON_KEY=[anon-key]
VITE_API_URL=http://localhost:8000/api
```

### Backend (.env)

```bash
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=[anon-key]
SUPABASE_SERVICE_KEY=[service-key]
PYTHON_VERSION=3.11.9  # Critical for Render
CORS_ORIGINS=["http://localhost:5173"]  # Must be JSON array!
```

---

## Code Conventions

### Naming

- **Components**: FK prefix for business components (e.g., `FKContractRequest.tsx`)
- **Files**: PascalCase for components, camelCase for utilities
- **Types**: 100% TypeScript, no `any` types

### Architecture Rules

1. **Frontend**: pages → components → services → api
2. **Backend**: adapter/rest → core/servicios → repositorio
3. **Forms**: Always use react-hook-form with MUI
4. **State**: Context API for global, useState for local

---

## Common Workflows

### Adding a New Contract Type

1. Add template DOCX to `backend/templates/`
2. Create database migration for new type
3. Update `ContractType` enum in DTOs
4. Add frontend form component
5. Update Operations dashboard tabs

### Adding a New Role

1. Update `UserRole` enum in `frontend/src/types/index.ts`
2. Add role to database enum
3. Create RBAC dependency in `rbac_dependencies.py`
4. Add `RoleProtectedRoute` for new routes

### Debugging API Issues

1. Check browser Network tab for request/response
2. View backend logs for errors
3. Use `/api/debug/cors` endpoint for CORS issues
4. Check Swagger UI at `/docs` for API testing
