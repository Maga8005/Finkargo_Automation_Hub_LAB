# Finkargo Automation Hub - File Structure Reference

This document provides a detailed map of the codebase structure for quick navigation.

---

## Frontend Structure (`frontend/src/`)

### Entry Points

| File | Purpose |
|------|---------|
| `main.tsx` | React app entry point |
| `App.tsx` | Root component with routing |
| `App.css` | Global styles |
| `index.css` | Root CSS variables |

### API Layer (`api/`)

```
api/
└── clients/
    └── apiClient.ts          # Axios instance with interceptors
```

**Key Features:**
- Base URL from environment variable
- JWT token injection
- Error handling interceptors

### Components (`components/`)

```
components/
├── forms/                     # Business form components (FK-prefixed)
│   ├── FKClientDataImport.tsx    # CSV/Excel client import
│   ├── FKContractRequest.tsx     # Activos contract request
│   ├── FKOtrosiRequest.tsx       # Otrosí contract request
│   ├── FKInventarioRequest.tsx   # Inventario Bodega request
│   ├── FKReviewQueue.tsx         # Legal review queue
│   ├── FKApprovedContracts.tsx   # Approved contracts list
│   ├── FKContractGenerator.tsx   # Contract generation form
│   └── FKExcelUploader.tsx       # Finance Excel uploader
│
├── ui/                        # Layout components
│   ├── FKMainLayout.tsx          # Main app layout with Outlet
│   ├── FKSidebar.tsx             # Navigation sidebar
│   ├── FKSidebarWithCollapse.tsx # Collapsible sidebar
│   ├── FKTopNavbar.tsx           # Top navigation bar
│   └── FKUserMenu.tsx            # User dropdown menu
│
├── declaraciones/             # Matching results module
│   ├── FKConfidenceDistributionChart.tsx
│   ├── FKManualMatchOverrideForm.tsx
│   ├── FKMatchDetailModal.tsx
│   ├── FKMatchDetailsTable.tsx
│   ├── FKMatchingStatisticsCard.tsx
│   └── FKUnmatchedRecordsView.tsx
│
├── ProtectedRoute.tsx         # Auth-required wrapper
└── RoleProtectedRoute.tsx     # Role-required wrapper
```

### Contexts (`contexts/`)

```
contexts/
├── AuthContext.tsx            # Authentication state provider
└── ThemeContext.tsx           # Theme (light/dark) provider
```

### Hooks (`hooks/`)

```
hooks/
├── useAuth.ts                 # Access AuthContext
└── useThemeMode.ts            # Access ThemeContext
```

### Pages (`pages/`)

```
pages/
├── HomePage.tsx               # Landing/dashboard page
├── LoginPage.tsx              # Authentication page
├── DepartmentPage.tsx         # Generic department page
├── ClientDashboard.tsx        # External client view
│
├── legal/
│   └── LegalDashboard.tsx     # Legal department dashboard
│
├── operations/
│   ├── OperationsDashboard.tsx           # Operations home
│   ├── OperationsContractsColombia.tsx   # Colombia contracts
│   └── OperationsContractsMexico.tsx     # Mexico contracts
│
├── finance/
│   ├── ReporteriaAutomaticaCO.tsx        # Colombia reporting
│   └── ReporteriaAutomaticaMX.tsx        # Mexico invoicing
│
├── fiscal/
│   └── FiscalModulePage.tsx              # Fiscal module
│
└── declaraciones/
    └── MatchingResultsDashboardPage.tsx  # Matching dashboard
```

### Services (`services/`)

```
services/
├── supabase.ts                # Supabase client setup
├── legalService.ts            # Legal API calls
├── operationsService.ts       # Operations API calls
├── financeService.ts          # Finance API calls
├── departmentService.ts       # Department API calls
└── matchingResultsService.ts  # Matching results API
```

### Types (`types/`)

```
types/
├── index.ts                   # Core types (User, Auth, etc.)
├── legal.ts                   # Legal-specific types
├── finance.ts                 # Finance-specific types
├── matching_results_types.ts  # Matching types
└── theme.ts                   # Theme types
```

### Theme (`theme/`)

```
theme/
├── theme.ts                   # Main MUI theme (light)
└── darkTheme.ts               # Dark mode theme
```

---

## Backend Structure (`backend/src/`)

### Entry Point

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app initialization, routes, CORS |

### Adapter Layer (`adapter/rest/`)

```
adapter/rest/
├── __init__.py
├── auth_routes.py             # Authentication endpoints
├── legal_routes.py            # Legal contract endpoints
├── operations_routes.py       # Operations endpoints
├── finance_routes.py          # Finance/invoicing endpoints
├── dependencies.py            # Auth dependencies
└── rbac_dependencies.py       # Role-based access control
```

### Core Services (`core/servicios/`)

```
core/servicios/
├── __init__.py
├── contract_service.py        # Contract business logic
├── document_service.py        # DOCX/PDF generation
├── csv_template_mapper.py     # CSV column mapping
├── rut_parser_service.py      # RUT PDF parsing
├── excel_validation_service.py # Finance Excel validation
├── excel_merge_service.py     # Excel data merging
├── excel_report_service.py    # Excel report generation
├── invoice_search_service.py  # Invoice search logic
├── zip_generator_service.py   # ZIP package creation
└── google_drive_service.py    # Google Drive integration
```

### Interface/DTOs (`interface/`)

```
interface/
├── __init__.py
├── auth_dtos.py               # Authentication DTOs
├── legal_dtos.py              # Legal contract DTOs
└── finance_dtos.py            # Finance/invoicing DTOs
```

### Repositories (`repositorio/`)

```
repositorio/
├── __init__.py
├── client_repository.py       # Client data access
├── contract_repository.py     # Contract data access
└── template_repository.py     # Template data access
```

### Configuration (`config/`)

```
config/
├── __init__.py
├── settings.py                # Pydantic settings
└── supabase_config.py         # Supabase client setup
```

### Models (`models/`)

```
models/
├── __init__.py
└── legal_models.py            # SQLAlchemy models (minimal use)
```

---

## Database (`backend/database/`)

### Schema & Migrations

```
database/
├── README.md                  # Database setup guide
├── __init__.py
├── schema.sql                 # Base schema
├── combined_schema.sql        # Full schema reference
│
└── Migrations (apply in order):
    ├── migration_create_user_profiles.sql
    ├── migration_add_legal_operations_roles.sql
    ├── migration_add_user_type.sql
    ├── migration_add_contract_fields.sql
    ├── migration_add_otrosi_support.sql
    ├── migration_add_otrosi_support_CORRECTED.sql
    ├── migration_add_otrosi_support_FIXED.sql
    ├── migration_add_inventario_bodega_support.sql
    ├── migration_add_approved_document_url.sql
    ├── migration_allow_null_audit_fields.sql
    ├── migration_fix_user_profiles_rls.sql
    ├── migration_create_legal_user.sql
    └── migration_create_operations_user.sql
```

---

## Templates (`backend/templates/`)

Contract document templates:

```
templates/
├── FK COL - GM - Activos.docx           # Activos contract
├── FK COL - GM - Activos.pdf            # Reference PDF
├── FK COL - K Marco - Otrosí No. 1.docx # Otrosí contract
├── FK COL - GM - Inventario Bodega de 3ro.docx # Inventario
└── plantilla_importacion_clientes.csv   # Client import template
```

---

## Scripts (`scripts/`)

Development helper scripts:

```
scripts/
├── README.md                  # Script documentation
├── QUICK_START.md            # Quick start guide
├── start-dev.sh              # Start both servers (Unix)
├── start-dev.bat             # Start both servers (Windows)
└── stop-dev.sh               # Stop servers
```

---

## Specifications (`specs/`)

Feature specifications:

```
specs/
├── contract_generation_system_overview.md
├── contratos-aprobados-filtering.md
├── contratos-aprobados-sorting.md
├── dark_mode_implementation.md
├── minuta_compraventa_automation.md
├── fix_rut_parser_gamalog_format.md
└── Various bug fix and feature specs...
```

---

## Implementation Notes (`implementations/`)

Post-implementation documentation:

```
implementations/
├── 20251106_Legal_CORS_500_Error_Client_Search_Fix.md
├── 20251106_Otrosi_Contract_Type_Implementation.md
├── 20251110_RUT_Upload_Parsing_Implementation.md
├── 20251110_inventario_bodega_contract_type_implementation.md
└── Various implementation docs...
```

---

## Claude Code Commands (`.claude/commands/`)

Custom slash commands for development:

```
.claude/commands/
├── bug.md                     # Bug fix workflow
├── chore.md                   # Maintenance task
├── classify_issue.md          # Issue classification
├── commit.md                  # Git commit helper
├── feature.md                 # Feature implementation
├── find_plan_file.md          # Find planning files
├── generate_branch_name.md    # Branch naming
├── implement.md               # Implementation workflow
├── install.md                 # Installation helper
├── prime.md                   # Codebase priming
├── pull_request.md            # PR creation
├── start.md                   # Start development
└── tools.md                   # Available tools
```

---

## Configuration Files

### Frontend

| File | Purpose |
|------|---------|
| `frontend/package.json` | Dependencies and scripts |
| `frontend/vite.config.ts` | Vite bundler config |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/tsconfig.app.json` | App-specific TS config |
| `frontend/tsconfig.node.json` | Node TS config |
| `frontend/eslint.config.js` | ESLint rules |
| `frontend/vercel.json` | Vercel deployment config |
| `frontend/.env.example` | Environment template |

### Backend

| File | Purpose |
|------|---------|
| `backend/requirements.txt` | Python dependencies |
| `backend/runtime.txt` | Python version |
| `backend/Dockerfile` | Docker config |
| `backend/render-build.sh` | Render build script |
| `backend/.env.example` | Environment template |

---

## Key File Locations Quick Reference

### Need to add a new route?
- Frontend: `frontend/src/App.tsx`
- Backend: `backend/main.py` (include router)

### Need to add a new API endpoint?
- Create/modify: `backend/src/adapter/rest/{module}_routes.py`
- Add DTOs: `backend/src/interface/{module}_dtos.py`

### Need to add business logic?
- Backend: `backend/src/core/servicios/{service}_service.py`

### Need to add data access?
- Backend: `backend/src/repositorio/{entity}_repository.py`

### Need to add a new form component?
- Frontend: `frontend/src/components/forms/FK{Name}.tsx`

### Need to add a new page?
- Frontend: `frontend/src/pages/{module}/{PageName}.tsx`
- Update routing in `App.tsx`

### Need to add TypeScript types?
- Frontend: `frontend/src/types/{module}.ts` or `index.ts`

### Need to add a database migration?
- Backend: `backend/database/migration_{description}.sql`

### Need to add a contract template?
- Backend: `backend/templates/{template_name}.docx`
