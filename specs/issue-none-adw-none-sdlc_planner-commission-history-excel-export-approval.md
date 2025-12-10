# Feature: Commission History View, Excel Export, and Approval Workflow

## Feature Description
Implement a comprehensive commission management workflow for the Alianzas module that includes:
1. Commission history view with filters and pagination
2. Excel export functionality with detailed and summary sheets
3. Commission approval workflow that creates payment records for brokers
4. Payment history tracking with status management

This feature extends the existing commission calculation system to support the full lifecycle from calculation to payment, enabling the Alianzas team to efficiently manage broker payouts.

## User Story
As an Alianzas department user
I want to view commission history, export to Excel, and approve commissions for payment
So that I can manage the complete broker payment lifecycle with proper documentation and audit trail

## Problem Statement
The current system allows calculating and saving commissions but lacks:
- A way to view historical commission data with filters
- Excel export for reporting and external review
- Formal approval workflow to transition commissions to payments
- Payment tracking and history management

## Solution Statement
Extend the Alianzas module with:
1. **Pago Repository**: Database access layer for broker payments (`broker_pagos` table)
2. **Excel Export Service**: Generate multi-sheet Excel reports with commission details, broker summaries, and metadata
3. **Approval Service**: Bulk approve commissions and create corresponding payment records
4. **New API Endpoints**: CRUD operations for commissions list, export, approval, and payment management
5. **Pagos History Page**: New frontend page to view payment history with filters
6. **UI Enhancements**: Add export and approval buttons to existing ComisionesCalculo page

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Use existing `require_alianzas_role` dependency from `rbac_dependencies.py`
- Frontend Protection: Use `RoleProtectedRoute` with `allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}`

## Relevant Files
Use these files to implement the feature:

**Backend - Existing Files to Modify:**
- `backend/src/adapter/rest/alianzas_routes.py` - Add new endpoints for commissions list, export, approval, and payment CRUD
- `backend/src/core/servicios/comision_service.py` - Add approval logic to create payment records
- `backend/src/interface/alianzas_dtos.py` - Add DTOs for payments and approval responses

**Backend - Reference Files:**
- `backend/src/repositorio/comision_repository.py` - Pattern for new pago_repository
- `backend/src/core/servicios/excel_report_service.py` - Pattern for Excel generation with openpyxl
- `backend/database/migration_create_alianzas_tables.sql` - Contains `broker_pagos` table schema (already exists)

**Frontend - Existing Files to Modify:**
- `frontend/src/pages/alianzas/ComisionesCalculo.tsx` - Add export and approval buttons with functionality
- `frontend/src/services/alianzasService.ts` - Add new API methods
- `frontend/src/types/alianzas.ts` - Add payment types and enums
- `frontend/src/App.tsx` - Add new route for payments history

**Frontend - Reference Files:**
- `frontend/src/components/alianzas/FKComisionesTable.tsx` - Pattern for data table components
- `frontend/src/components/alianzas/FKResumenBrokers.tsx` - Pattern for summary components

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - E2E test format example

### New Files
| File Path | Purpose |
|-----------|---------|
| `backend/src/repositorio/pago_repository.py` | Database operations for broker_pagos table |
| `backend/src/core/servicios/comision_excel_service.py` | Excel export generation with openpyxl |
| `frontend/src/pages/alianzas/PagosHistorial.tsx` | Payment history page with filters and table |
| `frontend/src/components/alianzas/FKPagosTable.tsx` | DataGrid component for payment records |
| `.claude/commands/e2e/test_commission_export_approval.md` | E2E test for export and approval workflow |

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs)
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [x] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature does not involve Word document generation.

### B. Excel Column Mapping (Excel Processing)

**Output Excel Structure - Sheet 1: "Detalle"**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| Cliente | comision.cliente_nombre | Direct |
| NIT | comision.cliente_nit | Direct |
| Broker | comision.broker_nombre (via join) | Direct |
| Tipo | comision.tipo_comision | Map: apertura→Apertura, operativa→Operativa |
| Línea Crédito | comision.linea_credito | Currency format USD |
| % Comisión Cliente | comision.porcentaje_comision_cliente | Percentage format |
| Monto Comisión | comision.monto_comision_cliente | Currency format USD |
| % Broker | comision.porcentaje_broker | Percentage format |
| Operaciones Mes | comision.operaciones_mes | Currency format USD |
| Monto USD | comision.monto_broker_usd | Currency format USD |
| T/C | comision.tipo_cambio | Decimal 4 places |
| Monto MXN | comision.monto_broker_mxn | Currency format MXN |
| % Pago Cliente | comision.cliente_pago_pct | Percentage format |
| Estado | comision.estado | Map: calculado→Calculado, aprobado→Aprobado, pagado→Pagado |

**Output Excel Structure - Sheet 2: "Resumen por Broker"**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| Broker | resumen.broker_nombre | Direct |
| Total Apertura USD | resumen.total_apertura_usd | Currency format USD |
| Total Apertura MXN | resumen.total_apertura_mxn | Currency format MXN |
| Total Operativa USD | resumen.total_operativa_usd | Currency format USD |
| Total Operativa MXN | resumen.total_operativa_mxn | Currency format MXN |
| Total USD | resumen.total_usd | Currency format USD |
| Total MXN | resumen.total_mxn | Currency format MXN |
| # Comisiones | resumen.num_comisiones | Integer |

**Output Excel Structure - Sheet 3: "Información"**
| Row | Content |
|-----|---------|
| Período | {mes_nombre} {anio} |
| Tipo de Cambio | {tipo_cambio} MXN/USD |
| Fecha TC | {fecha_tipo_cambio} |
| Generado | {datetime.now()} |
| Total Comisiones | {count} |
| Total USD | {sum} |
| Total MXN | {sum} |

**Catalog Dependencies:**
- [x] No external catalog mappings required
- [x] Uses existing EstadoComision and TipoComision enums

### C. File Format Specification (Import/Export only)
N/A - This feature only exports Excel files (no import).

### D. Data Contract Verification

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `comision_repo.get_by_periodo()` | `List[dict]` | `record['field']` | `record['broker_id']` |
| `comision_repo.get_resumen_por_broker()` | `List[dict]` | `record['field']` | `record['broker_nombre']` |
| `comision_repo.update_estado()` | `Optional[dict]` | `record['field']` | `record['estado']` |
| `pago_repo.create()` | `dict` | `record['field']` | `record['id']` |
| `pago_repo.get_by_periodo()` | `List[dict]` | `record['field']` | `record['total_usd']` |
| `pago_repo.get_historial()` | `List[dict]` | `record['field']` | `record['estado']` |
| `pago_repo.update_estado()` | `Optional[dict]` | `record['field']` | `record['fecha_pago']` |

### E. Database Dependencies Checklist
- [x] `broker_pagos` table already exists in `migration_create_alianzas_tables.sql`
- [x] Payment states enum: `pendiente`, `programado`, `pagado` (defined in migration)
- [x] Commission states enum: `calculado`, `aprobado`, `pagado` (defined in migration and DTOs)
- [x] RLS policies already configured for alianzas role
- [x] Foreign keys to brokers table already established

### F. External API Contract (Integration only)
N/A - This feature does not integrate with external APIs.

### G. Query Specification (Reporting)

**Commission List Query:**
| Filter | Type | Required | Default |
|--------|------|----------|---------|
| periodo_mes | int (1-12) | Yes | - |
| periodo_anio | int (>=2020) | Yes | - |
| broker_id | UUID | No | None |
| estado | string | No | None |
| tipo_comision | string | No | None |

**Payment History Query:**
| Filter | Type | Required | Default |
|--------|------|----------|---------|
| broker_id | UUID | No | None |
| estado | string | No | None |
| limit | int | No | 50 |
| offset | int | No | 0 |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| broker_id | broker_id | string (UUID) | snake_case in both |
| periodo_mes | periodo_mes | number | snake_case in both |
| periodo_anio | periodo_anio | number | snake_case in both |
| total_usd | total_usd | number | snake_case in both |
| total_mxn | total_mxn | number | snake_case in both |
| tipo_cambio | tipo_cambio | number | snake_case in both |
| fecha_programada | fecha_programada | string (ISO date) | snake_case in both |
| fecha_pago | fecha_pago | string (ISO date) | snake_case in both |
| estado | estado | string (enum) | snake_case in both |
| comprobante_url | comprobante_url | string | snake_case in both |
| factura_broker_url | factura_broker_url | string | snake_case in both |

## Implementation Plan

### Phase 1: Foundation
- Create `pago_repository.py` with CRUD operations for `broker_pagos` table
- Add payment DTOs to `alianzas_dtos.py` (PagoCreate, PagoResponse, PagoEstadoUpdate, etc.)
- Add payment types to frontend `alianzas.ts`

### Phase 2: Core Implementation
- Create `comision_excel_service.py` with openpyxl for Excel generation
- Add `aprobar_comisiones` method to `comision_service.py`
- Add new API endpoints to `alianzas_routes.py`:
  - GET `/comisiones` - List with filters
  - GET `/comisiones/export` - Excel export
  - POST `/comisiones/aprobar` - Approval workflow
  - GET `/pagos` - Payment history
  - PUT `/pagos/{id}/marcar-pagado` - Mark as paid
- Add service methods to `alianzasService.ts`

### Phase 3: Integration
- Create `PagosHistorial.tsx` page with filters and table
- Create `FKPagosTable.tsx` component with expandable rows
- Update `ComisionesCalculo.tsx` with export and approval buttons
- Add route in `App.tsx` for payments history
- Update sidebar navigation

## Step by Step Tasks

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md`
- Create `.claude/commands/e2e/test_commission_export_approval.md` with test steps for:
  - Navigate to ComisionesCalculo page
  - Add sample commissions
  - Click "Exportar Excel" button
  - Verify Excel download starts
  - Click "Aprobar Comisiones" button
  - Verify confirmation dialog
  - Confirm approval
  - Verify success message
  - Navigate to PagosHistorial page
  - Verify payment record appears

### Step 2: Create Pago Repository
- Create `backend/src/repositorio/pago_repository.py`
- Implement methods:
  - `create(data: dict) -> dict`
  - `get_by_id(pago_id: str) -> Optional[dict]`
  - `get_by_periodo(mes: int, anio: int) -> List[dict]`
  - `get_by_broker(broker_id: str) -> List[dict]`
  - `get_historial(filters: dict, limit: int, offset: int) -> List[dict]`
  - `update_estado(pago_id: str, estado: str, fecha_pago: date = None) -> Optional[dict]`
- Add `_serialize_for_db()` helper method following `comision_repository.py` pattern

### Step 3: Add Payment DTOs
- Add to `backend/src/interface/alianzas_dtos.py`:
  - `EstadoPago` enum: `pendiente`, `programado`, `pagado`
  - `PagoCreate` model
  - `PagoResponse` model
  - `PagoListResponse` model with pagination
  - `PagoEstadoUpdate` model
  - `ComisionAprobacionResponse` model (summary of approval action)

### Step 4: Create Excel Export Service
- Create `backend/src/core/servicios/comision_excel_service.py`
- Implement `ComisionExcelService` class with:
  - `generate_comisiones_excel(comisiones, resumen, periodo_mes, periodo_anio, tipo_cambio) -> BytesIO`
- Create 3 sheets: Detalle, Resumen por Broker, Información
- Apply styling: headers with bold font, currency formatting, borders
- Follow patterns from `excel_report_service.py`

### Step 5: Add Approval Logic to Comision Service
- Add to `backend/src/core/servicios/comision_service.py`:
  - `aprobar_comisiones(periodo_mes, periodo_anio, user_id) -> dict`
  - Logic:
    1. Fetch all 'calculado' commissions for period
    2. Update estado to 'aprobado'
    3. Aggregate by broker
    4. Create broker_pagos records (one per broker)
    5. Return summary with counts and totals

### Step 6: Add Backend API Endpoints
- Add to `backend/src/adapter/rest/alianzas_routes.py`:
  - `GET /comisiones` - List commissions with query params (periodo_mes, periodo_anio, broker_id, estado)
  - `GET /comisiones/export` - StreamingResponse with Excel file
  - `POST /comisiones/aprobar` - Approve and create payments
  - `GET /pagos` - List payments with pagination
  - `PUT /pagos/{pago_id}/marcar-pagado` - Update payment status

### Step 7: Add Frontend Types
- Add to `frontend/src/types/alianzas.ts`:
  - `EstadoPago` type and enum object
  - `ESTADO_PAGO_LABELS` and `ESTADO_PAGO_COLORS` mappings
  - `Pago` interface
  - `PagoListResponse` interface
  - `ComisionAprobacionResponse` interface

### Step 8: Add Frontend Service Methods
- Add to `frontend/src/services/alianzasService.ts`:
  - `getComisiones(params)` - Fetch commissions with filters
  - `exportComisionesExcel(periodoMes, periodoAnio)` - Download Excel file
  - `aprobarComisiones(periodoMes, periodoAnio)` - Approve commissions
  - `getPagos(params)` - Fetch payment history
  - `marcarPagado(pagoId, fechaPago, comprobanteUrl?)` - Update payment

### Step 9: Create FKPagosTable Component
- Create `frontend/src/components/alianzas/FKPagosTable.tsx`
- Features:
  - MUI DataGrid with payment records
  - Columns: Período, Broker, USD, MXN, T/C, Estado, Fecha Pago, Acciones
  - Status chips with colors (Pendiente=yellow, Programado=blue, Pagado=green)
  - Action buttons: Ver detalle, Marcar pagado
  - Row click to show commission breakdown (expandable detail panel)

### Step 10: Create PagosHistorial Page
- Create `frontend/src/pages/alianzas/PagosHistorial.tsx`
- Features:
  - Header with title "Historial de Pagos - Brokers"
  - Filter bar: Broker dropdown, Estado dropdown, Date range
  - FKPagosTable component
  - Pagination controls
  - "Marcar Pagado" dialog with fecha_pago date picker and comprobante_url input

### Step 11: Update ComisionesCalculo Page
- Modify `frontend/src/pages/alianzas/ComisionesCalculo.tsx`:
  - Update `handleExportExcel()` to call actual service and trigger download
  - Add `handleAprobarComisiones()` function
  - Add confirmation dialog for approval with summary
  - Show success message with approval summary after completion
  - Disable approval button if no saved commissions or already approved

### Step 12: Add Route and Navigation
- Add route in `frontend/src/App.tsx`:
  ```tsx
  <Route
    path="alianzas/pagos"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
        <PagosHistorial />
      </RoleProtectedRoute>
    }
  />
  ```
- Update sidebar navigation to include "Historial de Pagos" under Alianzas menu

### Step 13: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- `test_pago_repository.py`: Test CRUD operations for pago_repository
- `test_comision_excel_service.py`: Test Excel generation, verify sheets and data
- `test_comision_service_approval.py`: Test approval workflow and payment creation

### Edge Cases
- Approval with no commissions in period → Return empty response
- Approval of already-approved commissions → Skip or error
- Export with empty commission list → Generate Excel with headers only
- Mark paid without fecha_pago → Validation error
- Pagination with offset > total records → Return empty list

## Acceptance Criteria
- [x] Can view commission history by period with filters (broker, estado, tipo)
- [x] Can export commissions to Excel with proper formatting
- [x] Excel has 3 sheets: Detalle, Resumen por Broker, Información
- [x] Can approve commissions (changes estado from calculado to aprobado)
- [x] Approval creates broker_pagos records (one per broker for the period)
- [x] Can view payment history with filters and pagination
- [x] Can mark payments as completed with fecha_pago date
- [x] Status indicators show correct colors:
  - Commission: calculado=warning, aprobado=success, pagado=info
  - Payment: pendiente=warning, programado=info, pagado=success
- [x] All operations are protected by alianzas/admin role

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_commission_export_approval.md` to validate the full workflow works.

## Notes

### Dependencies
- `openpyxl` is already available in `backend/requirements.txt` (used by other Excel services)
- No new npm packages required for frontend

### Database
- `broker_pagos` table already exists in `migration_create_alianzas_tables.sql`
- No new migration needed

### Excel Styling Reference
Follow patterns from `backend/src/core/servicios/excel_report_service.py`:
- Use `PatternFill` for header backgrounds
- Use `Font(bold=True)` for headers
- Use `Border` for cell borders
- Set column widths with `column_dimensions`

### Future Considerations
- Add factura_broker_url support for broker invoice uploads
- Add fecha_programada for scheduled payment dates
- Add bulk payment processing (mark multiple as paid)
- Add PDF export option alongside Excel

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - table exists)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source data structure documented
- [x] Output Excel structure documented with all 3 sheets
- [x] Data transformation rules specified
- [x] No external catalog dependencies

**Reporting:**
- [x] Query filters and parameters documented
- [x] Pagination requirements specified

**CRUD Operations:**
- [x] Repository methods documented
- [x] DTOs specified

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path (Step 1)
