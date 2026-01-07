# Feature: Broker Commission Calculation Logic

## Feature Description
Implement the core commission calculation logic for brokers including apertura (opening) and operativa (operational) commission types. This service calculates broker commissions based on client credit lines, payment percentages, and monthly operations, with automatic USD to MXN conversion using Banxico exchange rates.

## User Story
As an alianzas team member,
I want to calculate broker commissions automatically based on business rules,
So that I can accurately determine how much to pay each broker for referrals and ongoing operations.

## Problem Statement
The alianzas team currently lacks an automated system to calculate broker commissions. Manual calculations are error-prone, time-consuming, and don't integrate with exchange rate data. The team needs a system that:
1. Calculates apertura commissions based on credit line and client payment percentage
2. Calculates operativa commissions based on monthly operation disbursements
3. Converts amounts to MXN using official Banxico exchange rates
4. Enforces business rules (e.g., minimum 50% client payment for apertura)
5. Persists calculated commissions for approval workflow

## Solution Statement
Create a ComisionService that:
1. Retrieves broker commission percentages from the database
2. Applies business formulas for apertura and operativa commission types
3. Integrates with BanxicoService for USD/MXN conversion
4. Validates business rules before calculation
5. Provides preview (calculate without saving) and batch calculation endpoints
6. Stores calculated commissions in broker_comisiones table for approval workflow

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: `require_alianzas_role` from `rbac_dependencies.py` (already defined)
- Frontend Protection: Not applicable (backend-only feature, no UI in this implementation)

## Relevant Files
Use these files to implement the feature:

**Backend - Existing Files to Modify:**
- `backend/src/interface/alianzas_dtos.py` - Add commission DTOs (TipoComision enum, EstadoComision enum, ComisionCalculada, ComisionInput)
- `backend/src/adapter/rest/alianzas_routes.py` - Add commission calculation endpoints

**Backend - Existing Files to Reference (Read Only):**
- `backend/src/repositorio/broker_repository.py` - Reference for repository patterns, especially `get_by_id` which returns `dict`
- `backend/src/core/servicios/broker_service.py` - Reference for service layer patterns and how to use broker_repo
- `backend/src/core/servicios/banxico_service.py` - Reference for `get_tipo_cambio(fecha: date) -> Decimal` method
- `backend/database/migration_create_alianzas_tables.sql` - Reference for `broker_comisiones` table schema (already exists)

### New Files
- `backend/src/core/servicios/comision_service.py` - Core business logic for commission calculations
- `backend/src/repositorio/comision_repository.py` - Data access layer for broker_comisiones table
- `backend/tests/test_comision_service.py` - Unit tests for commission calculation logic
- `.claude/commands/e2e/test_broker_commission_calculation.md` - E2E test specification (API-focused)

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this feature does not involve document generation.

### B. Excel Column Mapping (Excel Processing only)
Not applicable - this feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)
Not applicable - this feature does not involve file import/export.

### D. Data Contract Verification (ALL features)
Document return types and access patterns for repository methods used:

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `broker_repo.get_by_id(broker_id)` | `dict | None` | `broker['porcentaje_apertura']` | `Decimal(broker['porcentaje_apertura'] or 0)` |
| `banxico_service.get_tipo_cambio(fecha)` | `Decimal` | Direct | `await self.banxico.get_tipo_cambio(fecha_corte)` |
| `comision_repo.create(data)` | `dict` | `result['id']` | Returns created record |
| `comision_repo.get_by_periodo(mes, anio)` | `List[dict]` | `item['monto_broker_mxn']` | List of commission records |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs (or will be added) - TipoComision, EstadoComision
- [ ] Template file exists in `backend/templates/` (if applicable) - Not applicable
- [x] Database records exist (or migration created) - `broker_comisiones` table exists in `migration_create_alianzas_tables.sql`
- [x] Country-specific data handled (CO vs MX) - This is MX-specific (Banxico integration)

**Database Table Reference (`broker_comisiones`):**
```sql
CREATE TABLE broker_comisiones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broker_id UUID NOT NULL REFERENCES brokers(id),
    periodo_mes INTEGER NOT NULL CHECK (periodo_mes BETWEEN 1 AND 12),
    periodo_anio INTEGER NOT NULL CHECK (periodo_anio >= 2020),
    cliente_nombre VARCHAR(255),
    cliente_nit VARCHAR(50),
    tipo_comision VARCHAR(20) NOT NULL CHECK (tipo_comision IN ('apertura', 'operativa')),
    linea_credito DECIMAL(15,2),
    porcentaje_comision_cliente DECIMAL(5,2),
    monto_comision_cliente DECIMAL(15,2),
    porcentaje_broker DECIMAL(5,3),
    monto_broker_usd DECIMAL(15,2),
    operaciones_mes DECIMAL(15,2),
    tipo_cambio DECIMAL(10,4),
    monto_broker_mxn DECIMAL(15,2),
    cliente_pago_pct DECIMAL(5,2),
    estado VARCHAR(20) NOT NULL DEFAULT 'calculado',
    notas TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);
```

### F. External API Contract (Integration only)
Banxico API is already integrated via `BanxicoService`:

| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| Internal: `banxico_service.get_tipo_cambio(fecha)` | async | Bmx-Token header (env) | `date` object | `Decimal` |

### G. Query Specification (Reporting only)
Not applicable for initial implementation. Future reporting can use:

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| `periodo_mes` | int (1-12) | Yes | - |
| `periodo_anio` | int | Yes | - |
| `broker_id` | UUID | No | All brokers |

### Interface Mapping (Frontend ↔ Backend)
Backend-only feature. DTO field naming:

| DTO Field | DB Field | Type | Notes |
|-----------|----------|------|-------|
| `broker_id` | `broker_id` | UUID | Required |
| `tipo_comision` | `tipo_comision` | TipoComision enum | 'apertura' or 'operativa' |
| `cliente_nombre` | `cliente_nombre` | str | Client company name |
| `cliente_nit` | `cliente_nit` | str | Client tax ID |
| `linea_credito` | `linea_credito` | Decimal | For apertura only |
| `porcentaje_comision_cliente` | `porcentaje_comision_cliente` | Decimal | For apertura only |
| `cliente_pago_pct` | `cliente_pago_pct` | Decimal | % client has paid (0-100) |
| `operaciones_mes` | `operaciones_mes` | Decimal | For operativa only |
| `monto_broker_usd` | `monto_broker_usd` | Decimal | Calculated USD amount |
| `monto_broker_mxn` | `monto_broker_mxn` | Decimal | Calculated MXN amount |
| `tipo_cambio` | `tipo_cambio` | Decimal | Exchange rate used |
| `estado` | `estado` | EstadoComision enum | 'calculado', 'aprobado', 'pagado' |

## Implementation Plan
### Phase 1: Foundation
- Add commission-related DTOs to `alianzas_dtos.py`
- Create `ComisionRepository` for database operations on `broker_comisiones` table
- Create unit tests for repository

### Phase 2: Core Implementation
- Create `ComisionService` with business logic
- Implement `calcular_comision_apertura` method
- Implement `calcular_comision_operativa` method
- Implement `guardar_comisiones` method
- Create unit tests for service

### Phase 3: Integration
- Add API endpoints to `alianzas_routes.py`
- Add dependency injection for ComisionService
- Create E2E test specification
- Run validation commands

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Commission DTOs to alianzas_dtos.py
- Add `TipoComision` enum with values: `APERTURA = 'apertura'`, `OPERATIVA = 'operativa'`
- Add `EstadoComision` enum with values: `CALCULADO = 'calculado'`, `APROBADO = 'aprobado'`, `PAGADO = 'pagado'`
- Add `ComisionCalculada` Pydantic model with all calculation result fields
- Add `ComisionInput` Pydantic model for API request validation
- Add `ComisionListResponse` model for paginated responses

### Step 2: Create ComisionRepository
- Create `backend/src/repositorio/comision_repository.py`
- Implement `__init__(self, supabase_client: Client)`
- Implement `async def create(self, data: dict) -> dict`
- Implement `async def get_by_periodo(self, mes: int, anio: int) -> List[dict]`
- Implement `async def get_by_broker(self, broker_id: str, mes: int, anio: int) -> List[dict]`
- Implement `async def update_estado(self, comision_id: str, estado: str) -> dict`
- Implement `async def get_resumen_por_broker(self, mes: int, anio: int) -> List[dict]` with aggregation

### Step 3: Create ComisionService
- Create `backend/src/core/servicios/comision_service.py`
- Implement `__init__` with `broker_repo`, `comision_repo`, and `banxico_service` dependencies
- Implement `async def calcular_comision_apertura(...)` method with business rules:
  - Validate cliente_pago_pct >= 50%
  - Retrieve broker with `porcentaje_apertura`
  - Calculate: `monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / 100)`
  - Calculate: `monto_broker_usd = monto_comision_cliente * (porcentaje_broker / 100) * (cliente_pago_pct / 100)`
  - Get exchange rate from Banxico
  - Calculate: `monto_broker_mxn = monto_broker_usd * tipo_cambio`
  - Return `ComisionCalculada` model
- Implement `async def calcular_comision_operativa(...)` method:
  - Retrieve broker with `porcentaje_operativa`
  - Calculate: `monto_broker_usd = operaciones_mes * (porcentaje_operativa / 100)`
  - Get exchange rate from Banxico
  - Calculate: `monto_broker_mxn = monto_broker_usd * tipo_cambio`
  - Return `ComisionCalculada` model
- Implement `async def guardar_comisiones(...)` method to persist calculated commissions

### Step 4: Add API Endpoints to alianzas_routes.py
- Add dependency injection function `get_comision_repository()`
- Add dependency injection function `get_comision_service()`
- Add `POST /api/alianzas/comisiones/calcular` endpoint for single commission preview
- Add `POST /api/alianzas/comisiones/calcular-lote` endpoint for batch calculation with optional save
- Add `GET /api/alianzas/comisiones/{periodo_anio}/{periodo_mes}` endpoint to list commissions by period
- Add `GET /api/alianzas/comisiones/broker/{broker_id}` endpoint to list commissions by broker
- Add `PATCH /api/alianzas/comisiones/{comision_id}/estado` endpoint to update commission status

### Step 5: Create Unit Tests
- Create `backend/tests/test_comision_service.py`
- Test `calcular_comision_apertura` with valid inputs
- Test `calcular_comision_apertura` raises ValueError when cliente_pago_pct < 50
- Test `calcular_comision_apertura` raises ValueError when broker not found
- Test `calcular_comision_operativa` with valid inputs
- Test `calcular_comision_operativa` raises ValueError when broker not found
- Test USD to MXN conversion with mock Banxico service
- Test `guardar_comisiones` persists all commissions correctly

### Step 6: Create E2E Test Specification
- Create `.claude/commands/e2e/test_broker_commission_calculation.md`
- Read `.claude/commands/test_e2e.md` for format reference
- Read `.claude/commands/e2e/test_login.md` for login pattern
- Define test steps for API-based commission calculation
- Include test cases for apertura and operativa commission types
- Include test case for batch calculation
- Include validation of Banxico exchange rate integration

### Step 7: Run Validation Commands
- Run backend tests with pytest
- Run backend linting with ruff
- Run TypeScript type check (no frontend changes, but verify no regressions)
- Run frontend build to validate production compilation

## Testing Strategy
### Unit Tests
- **ComisionService Tests:**
  - `test_calcular_apertura_success` - Valid apertura calculation
  - `test_calcular_apertura_min_payment_validation` - Rejects < 50% payment
  - `test_calcular_apertura_broker_not_found` - Raises ValueError
  - `test_calcular_operativa_success` - Valid operativa calculation
  - `test_calcular_operativa_broker_not_found` - Raises ValueError
  - `test_currency_conversion` - Verifies USD to MXN conversion
  - `test_guardar_comisiones_batch` - Saves multiple commissions

### Edge Cases
- Broker with `porcentaje_apertura = 0` or `None`
- Broker with `porcentaje_operativa = 0` or `None`
- Client payment percentage exactly at 50% boundary
- Very large credit lines (test Decimal precision)
- Weekend/holiday date where Banxico has no rate (fallback logic)
- Batch calculation with mixed apertura and operativa commissions

## Acceptance Criteria
- [ ] Can calculate apertura commission with correct formula: `monto_comision_cliente * porcentaje_broker / 100 * cliente_pago_pct / 100`
- [ ] Can calculate operativa commission with correct formula: `operaciones_mes * porcentaje_operativa / 100`
- [ ] Validates minimum 50% client payment for apertura commissions
- [ ] Converts USD to MXN using Banxico FIX exchange rate
- [ ] Can save calculated commissions to `broker_comisiones` database table
- [ ] Batch calculation works for multiple clients in single request
- [ ] Preview mode calculates without persisting to database
- [ ] All unit tests pass
- [ ] API endpoints return appropriate HTTP status codes (200, 400, 404, 500)
- [ ] Commission amounts use Decimal precision (not float rounding errors)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run backend unit tests
cd backend && python -m pytest tests/test_comision_service.py -v

# Run all backend tests
cd backend && python -m pytest

# Run backend linting
cd backend && ruff check src/

# Run frontend linting (verify no regressions)
cd frontend && npm run lint

# Run TypeScript type check (verify no regressions)
cd frontend && npx tsc --noEmit

# Run frontend build (verify production compilation)
cd frontend && npm run build
```

Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_commission_calculation.md` to validate API functionality.

## Notes
- **Decimal Precision:** Use Python's `Decimal` type throughout calculations to avoid floating-point rounding errors in financial calculations.
- **Banxico Rate Caching:** The BanxicoService already implements in-memory caching. No additional caching needed.
- **No New Dependencies:** This feature uses existing dependencies (pydantic, supabase, decimal, httpx).
- **Future Enhancements:**
  - UI for commission calculation (separate feature)
  - Commission approval workflow with notifications
  - Payment scheduling integration
  - Bulk import from Excel

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (table already exists)
- [x] E2E test file task included (Step 6)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Repository patterns match existing code (`broker_repository.py`)
- [x] Service layer follows existing patterns (`broker_service.py`)
- [x] DTO validation rules defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend (backend-only feature)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (MX-only with Banxico)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers API endpoints
