# Feature: Broker CRUD Management for Alianzas Module

## Feature Description
Implement full CRUD (Create, Read, Update, Delete) operations for broker management in the Alianzas (Partnerships) module. This includes backend repository, service layer, API endpoints, and a complete frontend UI with DataGrid listing, search, filters, and form components. The feature enables the Alianzas team to manage broker partners, their commission rates, contract information, and hierarchical relationships (master broker / sub-broker).

## User Story
As an **alianzas team member** (or admin)
I want to manage broker partners through a complete CRUD interface
So that I can maintain broker information, commission rates, contract details, and master/sub-broker relationships

## Problem Statement
The Alianzas department needs to manage broker partnerships but currently has no UI or API to create, view, update, or deactivate brokers. The database schema exists (`brokers` table from `migration_create_alianzas_tables.sql`), but there is no application layer to interact with it. This prevents the team from efficiently managing partner relationships and commission structures.

## Solution Statement
Implement a complete CRUD system following the established codebase patterns:
1. **Backend**: Repository → Service → Routes layers with proper DTOs
2. **Frontend**: TypeScript types, service layer, list page with DataGrid, and form component
3. **Navigation**: Add Alianzas section to sidebar and protected routes
4. **Access Control**: Role-based protection for alianzas and admin users

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: `require_roles(['alianzas'])` from `rbac_dependencies.py` (admin bypass enabled by default)
- Frontend Protection: `<RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>`

## Relevant Files
Use these files to implement the feature:

**Backend - Reference patterns:**
- `backend/src/adapter/rest/alianzas_routes.py` - Existing routes file to extend (currently only has health check)
- `backend/src/adapter/rest/rbac_dependencies.py` - Role-based access control patterns (`require_roles`, `require_alianzas_role`)
- `backend/src/adapter/rest/legal_routes.py` - Reference for CRUD route patterns
- `backend/src/repositorio/contract_repository.py` - Reference for repository patterns
- `backend/src/core/servicios/contract_service.py` - Reference for service layer patterns
- `backend/src/interface/legal_dtos.py` - Reference for DTO patterns with enums and Pydantic models
- `backend/src/config/supabase_config.py` - Supabase client configuration
- `backend/main.py` - Router registration and departments endpoint (needs alianzas department added)

**Frontend - Reference patterns:**
- `frontend/src/services/legalService.ts` - Reference for API service patterns
- `frontend/src/types/index.ts` - Core types file (UserRole already includes 'alianzas')
- `frontend/src/types/legal.ts` - Reference for module-specific types
- `frontend/src/components/forms/FKContractRequest.tsx` - Reference for FK-prefixed form components with react-hook-form
- `frontend/src/pages/legal/LegalDashboard.tsx` - Reference for page component patterns
- `frontend/src/components/ui/FKSidebar.tsx` - Sidebar navigation (needs alianzas access check)
- `frontend/src/App.tsx` - Route definitions (needs alianzas routes)
- `frontend/src/api/clients/apiClient.ts` - Axios client for API calls

**Database:**
- `backend/database/migration_create_alianzas_tables.sql` - Already exists with `brokers` table schema

**E2E Testing:**
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_login.md` - Reference for E2E test file format

### New Files
Create these files to implement the feature:

**Backend:**
- `backend/src/interface/alianzas_dtos.py` - DTOs for broker (BrokerCreate, BrokerUpdate, BrokerResponse, BrokerSearchRequest, enums)
- `backend/src/repositorio/broker_repository.py` - Repository for broker database operations
- `backend/src/core/servicios/broker_service.py` - Business logic service for broker operations

**Frontend:**
- `frontend/src/types/alianzas.ts` - TypeScript types for broker (Broker, BrokerFormData, enums)
- `frontend/src/services/alianzasService.ts` - API service for broker endpoints
- `frontend/src/pages/alianzas/BrokersPage.tsx` - Main page with broker list and management
- `frontend/src/components/alianzas/FKBrokerForm.tsx` - Reusable form component for create/edit

**E2E Test:**
- `.claude/commands/e2e/test_broker_crud.md` - E2E test for broker management workflow

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| broker_repo.get_by_id() | dict | data['id'] | `broker['nombre']` |
| broker_repo.create() | dict | data['id'] | `result['id']` |
| broker_repo.update() | dict | data['nombre'] | `updated['estado']` |
| broker_repo.delete() | bool | - | Returns True/False |
| broker_repo.search() | List[dict] | data[0]['id'] | `brokers[0]['nombre']` |
| broker_repo.list_all() | List[dict] | data[0]['id'] | `brokers[0]['tipo_broker']` |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (will be added in alianzas_dtos.py):
  - `TipoBroker`: master_broker, independiente, aliado_logistico, consultoria
  - `EstadoBroker`: activo, inactivo, pendiente
- [x] Database table exists: `brokers` table in `migration_create_alianzas_tables.sql`
- [x] RLS policies exist for alianzas role (in migration file)
- [x] Indexes exist for common queries (in migration file)
- [x] Country-specific: N/A (Mexico-focused, no CO variation needed)

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| id | id | string (UUID) | Primary key |
| nombre | nombre | string | Required, max 255 chars |
| tipo_broker | tipo_broker | TipoBroker | Enum: master_broker, independiente, aliado_logistico, consultoria |
| master_broker_id | master_broker_id | string (UUID) | Optional, self-referencing FK |
| porcentaje_apertura | porcentaje_apertura | number | Decimal(5,2), 0-100 |
| porcentaje_operativa | porcentaje_operativa | number | Decimal(5,3), 0-100 |
| cuenta_bancaria | cuenta_bancaria | string | Optional, max 50 chars |
| banco | banco | string | Optional, max 100 chars |
| rfc | rfc | string | Optional, Mexican tax ID, max 20 chars |
| fecha_contrato | fecha_contrato | string (date) | ISO format YYYY-MM-DD |
| vigencia_contrato | vigencia_contrato | string (date) | ISO format YYYY-MM-DD |
| estado | estado | EstadoBroker | Enum: activo, inactivo, pendiente |
| link_expediente | link_expediente | string | Optional URL |
| notas | notas | string | Optional text |
| created_at | created_at | string (datetime) | ISO format |
| updated_at | updated_at | string (datetime) | ISO format |
| created_by | created_by | string (UUID) | User who created |

## Implementation Plan

### Phase 1: Foundation (Backend DTOs and Repository)
- Create DTOs with Pydantic models and enums
- Implement repository layer with Supabase operations
- Ensure proper type coercion for Decimal fields

### Phase 2: Core Implementation (Service and Routes)
- Create service layer with business logic validation
- Implement API endpoints in alianzas_routes.py
- Add comprehensive error handling

### Phase 3: Frontend Implementation
- Create TypeScript types mirroring backend DTOs
- Implement API service layer
- Create list page with search/filter functionality
- Create form component for create/edit operations

### Phase 4: Integration
- Add Alianzas to departments endpoint in main.py
- Update sidebar navigation with alianzas access check
- Add protected routes in App.tsx
- Create E2E test file

## Step by Step Tasks

### Task 1: Create Backend DTOs
- Read `backend/src/interface/legal_dtos.py` for reference patterns
- Create `backend/src/interface/alianzas_dtos.py` with:
  - `TipoBroker` enum (master_broker, independiente, aliado_logistico, consultoria)
  - `EstadoBroker` enum (activo, inactivo, pendiente)
  - `BrokerBase` model with all fields and validators
  - `BrokerCreate` model (extends BrokerBase)
  - `BrokerUpdate` model (all fields optional)
  - `BrokerResponse` model (includes id, created_at, updated_at)
  - `BrokerSearchRequest` model (nombre, tipo_broker, estado filters)

### Task 2: Create Broker Repository
- Read `backend/src/repositorio/contract_repository.py` for reference patterns
- Create `backend/src/repositorio/broker_repository.py` with methods:
  - `__init__(self, supabase_client)` - Initialize with Supabase client
  - `async get_all(self, filters: dict = None) -> List[dict]` - List with optional filters
  - `async get_by_id(self, broker_id: str) -> Optional[dict]` - Get single broker
  - `async create(self, data: BrokerCreate, user_id: str) -> dict` - Create new broker
  - `async update(self, broker_id: str, data: BrokerUpdate) -> Optional[dict]` - Update broker
  - `async delete(self, broker_id: str) -> bool` - Soft delete (set estado='inactivo')
  - `async search(self, params: BrokerSearchRequest) -> List[dict]` - Search by nombre, tipo, estado
  - `async list_by_master_broker(self, master_broker_id: str) -> List[dict]` - Get sub-brokers

### Task 3: Create Broker Service
- Read `backend/src/core/servicios/contract_service.py` for reference patterns
- Create `backend/src/core/servicios/broker_service.py` with:
  - `__init__(self, broker_repo)` - Initialize with repository
  - `async create_broker(data, user_id)` - Validate master_broker relationship, create
  - `async update_broker(broker_id, data)` - Verify exists, validate, update
  - `async get_broker(broker_id)` - Get or raise ValueError
  - `async search_brokers(params)` - Delegate to repository
  - `async list_brokers(active_only=True)` - List all or active only
  - `async get_sub_brokers(master_broker_id)` - Get sub-brokers under master
  - Business rules:
    - master_broker_id must reference a broker with tipo_broker='master_broker'
    - Only certain tipos can have a master_broker_id (independiente, aliado_logistico)

### Task 4: Implement API Endpoints
- Read `backend/src/adapter/rest/alianzas_routes.py` (existing file)
- Extend with broker CRUD endpoints:
  - `POST /api/alianzas/brokers` - Create broker (requires alianzas role)
  - `GET /api/alianzas/brokers` - List brokers with filters (requires alianzas role)
  - `GET /api/alianzas/brokers/{broker_id}` - Get broker by ID (requires alianzas role)
  - `PUT /api/alianzas/brokers/{broker_id}` - Update broker (requires alianzas role)
  - `DELETE /api/alianzas/brokers/{broker_id}` - Soft delete broker (requires alianzas role)
  - `GET /api/alianzas/brokers/search` - Search by query (optional, can merge with list)
  - `GET /api/alianzas/brokers/{broker_id}/sub-brokers` - Get sub-brokers under master
- Add dependency injection functions for repository and service
- Use `require_roles(['alianzas'])` for all endpoints (admin bypass is default)

### Task 5: Create Frontend Types
- Read `frontend/src/types/legal.ts` for reference patterns
- Create `frontend/src/types/alianzas.ts` with:
  - `TipoBroker` union type: 'master_broker' | 'independiente' | 'aliado_logistico' | 'consultoria'
  - `EstadoBroker` union type: 'activo' | 'inactivo' | 'pendiente'
  - `Broker` interface (all fields from BrokerResponse)
  - `BrokerCreateRequest` interface (matches BrokerCreate)
  - `BrokerUpdateRequest` interface (all optional)
  - `BrokerSearchParams` interface (nombre, tipo_broker, estado)
  - `BrokerWithSubBrokers` interface (extends Broker with sub_brokers array)

### Task 6: Create Frontend Service
- Read `frontend/src/services/legalService.ts` for reference patterns
- Create `frontend/src/services/alianzasService.ts` with:
  - `getBrokers(params?: BrokerSearchParams): Promise<Broker[]>` - List/search brokers
  - `getBrokerById(id: string): Promise<Broker>` - Get single broker
  - `createBroker(data: BrokerCreateRequest): Promise<Broker>` - Create broker
  - `updateBroker(id: string, data: BrokerUpdateRequest): Promise<Broker>` - Update broker
  - `deleteBroker(id: string): Promise<void>` - Delete (soft delete)
  - `getBrokerWithSubBrokers(id: string): Promise<BrokerWithSubBrokers>` - Get with sub-brokers

### Task 7: Create Broker Form Component
- Read `frontend/src/components/forms/FKContractRequest.tsx` for reference patterns
- Create `frontend/src/components/alianzas/FKBrokerForm.tsx` with:
  - Props: `broker?: Broker`, `onSuccess: (broker: Broker) => void`, `onCancel: () => void`, `masterBrokerOptions?: Broker[]`
  - Use react-hook-form with Controller for Select fields
  - Fields:
    - nombre (TextField, required)
    - tipo_broker (Select with TipoBroker options)
    - master_broker_id (Select, only show for non-master tipos)
    - porcentaje_apertura (TextField number, InputAdornment with %)
    - porcentaje_operativa (TextField number, InputAdornment with %)
    - cuenta_bancaria (TextField)
    - banco (TextField)
    - rfc (TextField)
    - fecha_contrato (TextField type="date")
    - vigencia_contrato (TextField type="date")
    - estado (Select with EstadoBroker options)
    - link_expediente (TextField)
    - notas (TextField multiline)
  - Submit handler calls create or update based on broker prop
  - Loading state with CircularProgress
  - Error/success alerts

### Task 8: Create Brokers Page
- Read `frontend/src/pages/legal/LegalDashboard.tsx` for reference patterns
- Create `frontend/src/pages/alianzas/BrokersPage.tsx` with:
  - State: brokers, loading, error, success, filters, selectedBroker, formDialogOpen, deleteDialogOpen
  - Search/filter bar with:
    - nombre TextField
    - tipo_broker Select
    - estado Select
    - Search button
    - "Nuevo Broker" button
  - Table or DataGrid displaying brokers with columns:
    - Nombre
    - Tipo (with human-readable labels)
    - Estado (Chip with color coding)
    - % Apertura
    - % Operativa
    - Banco
    - Actions (Edit, Delete icons)
  - Dialog for FKBrokerForm (create/edit)
  - Confirmation dialog for delete
  - Load master brokers for form dropdown

### Task 9: Update Navigation and Routes
- Update `backend/main.py` `/api/departments` endpoint:
  - Add: `{"id": "alianzas", "name": "Alianzas", "icon": "People"}`
- Update `frontend/src/components/ui/FKSidebar.tsx`:
  - Add alianzas to `hasAccessToDepartment` function:
    ```typescript
    if (userRole === 'alianzas' && departmentId === 'alianzas') return true;
    ```
- Update `frontend/src/App.tsx`:
  - Import BrokersPage
  - Add route:
    ```typescript
    <Route
      path="alianzas/brokers"
      element={
        <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
          <BrokersPage />
        </RoleProtectedRoute>
      }
    />
    ```
  - Add department route for alianzas:
    ```typescript
    <Route
      path="department/alianzas"
      element={<Navigate to="/alianzas/brokers" replace />}
    />
    ```

### Task 10: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for reference
- Create `.claude/commands/e2e/test_broker_crud.md` with:
  - User Story: As an alianzas user, I want to manage brokers
  - Prerequisites: Backend/frontend running, alianzas test user
  - Test Steps:
    1. Navigate to application URL
    2. Login with alianzas role user
    3. Navigate to /alianzas/brokers
    4. Verify brokers page loads with DataGrid/Table
    5. Click "Nuevo Broker" button
    6. Fill form with test data
    7. Submit form
    8. Verify broker appears in list
    9. Click Edit on the broker
    10. Update a field
    11. Submit update
    12. Verify change reflected in list
    13. Click Delete on the broker
    14. Confirm deletion
    15. Verify broker removed (or marked inactive)
  - Success Criteria and screenshots

### Task 11: Run Validation Commands
Execute all validation commands to ensure zero regressions:
- `cd backend && python -m pytest` - Run backend tests
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_crud.md`

## Testing Strategy

### Unit Tests
- `backend/tests/test_broker_repository.py`:
  - Test CRUD operations with mocked Supabase client
  - Test filter parameters passed correctly
  - Test soft delete updates estado
- `backend/tests/test_broker_service.py`:
  - Test master_broker_id validation
  - Test ValueError raised for not found
  - Test business rules enforcement

### Edge Cases
- Creating broker with non-existent master_broker_id → should fail
- Setting master_broker_id on a master_broker type → should fail or warn
- Deleting a master broker with sub-brokers → soft delete, sub-brokers retain reference
- Searching with empty filters → returns all active brokers
- Updating broker to inactive estado → same as delete
- RFC validation (optional, but if provided should match Mexican format)
- Percentage values outside 0-100 range → should fail validation

## Acceptance Criteria
- [ ] Can list all brokers with filtering by estado and tipo_broker
- [ ] Can create a new broker with all fields populated
- [ ] Can edit an existing broker's information
- [ ] Can soft-delete (deactivate) a broker
- [ ] Search works by nombre and RFC
- [ ] Master broker dropdown only shows brokers with tipo_broker='master_broker'
- [ ] Alianzas section appears in sidebar for alianzas/admin users
- [ ] Navigation to /alianzas/brokers works correctly
- [ ] Role protection works (non-alianzas/admin users cannot access)
- [ ] Form validation prevents invalid data submission
- [ ] Error messages display appropriately
- [ ] Success messages confirm operations completed
- [ ] E2E test passes with screenshots

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend validation
cd backend && python -m pytest
cd backend && ruff check src/

# Frontend validation
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

After all commands pass:
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_broker_crud.md` E2E test

## Notes
- The `alianzas` role already exists in `UserRole` enum in `frontend/src/types/index.ts`
- The `require_alianzas_role` dependency already exists in `rbac_dependencies.py`
- The `alianzas_routes.py` router is already registered in `main.py`
- The database migration `migration_create_alianzas_tables.sql` has the `brokers` table schema with RLS policies
- Ensure the database migration has been applied before testing
- The sidebar icon for Alianzas should use "People" which is already in the iconMap
- Consider future extensions: broker_comisiones and broker_pagos tables are already in the migration for commission tracking

## Plan Quality Checklist

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (CRUD Operations)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified (already exists)
- [x] E2E test file task included (Task 10)
- [x] All external dependencies listed in Notes (none required - all libraries already in project)

### Category-Specific Completeness (CRUD Operations)
- [x] Repository methods documented with return types
- [x] Service layer business rules specified
- [x] API endpoint routes defined
- [x] Frontend types mapped to backend DTOs

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (N/A - Mexico only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
