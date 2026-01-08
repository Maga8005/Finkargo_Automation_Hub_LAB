# Feature: Alianzas E2E Integration Tests

## Feature Description
Create a comprehensive end-to-end (E2E) test suite for the Alianzas (Partnerships) module and ensure all components are properly integrated. This includes a unified E2E test file that covers the complete workflow from broker creation to payment approval, unit tests for commission calculations, test fixtures with sample data, and validation of navigation and role protection.

## User Story
As a QA engineer/developer
I want comprehensive E2E tests and integration validation for the Alianzas module
So that I can ensure all broker management, commission calculation, export, and approval workflows function correctly end-to-end

## Problem Statement
The Alianzas module has individual E2E tests for specific features (broker CRUD, commission calculation, contract extraction, etc.), but lacks:
1. A unified E2E test that covers the **complete workflow** from broker creation through payment approval
2. Unit tests for commission calculation business logic
3. Reusable test fixtures with sample data
4. Comprehensive integration validation checklist

## Solution Statement
Create:
1. **Unified E2E Test File**: `.claude/commands/e2e/test_alianzas_comisiones.md` - A comprehensive test covering all four major flows (Broker CRUD, Contract Extraction, Commission Calculation, Export/Approval)
2. **Test Fixtures**: `backend/tests/fixtures/alianzas_test_data.py` - Sample data for testing with expected calculation results
3. **Unit Tests**: `backend/tests/test_alianzas_service.py` - Unit tests for commission calculation business logic
4. **Integration Checklist**: Validation commands and acceptance criteria for full module verification

## Access Control
- Required Role(s): `alianzas` or `admin`
- Backend Protection: Uses `require_roles(['alianzas', 'admin'])` from `rbac_dependencies.py`
- Frontend Protection: Routes protected via `RoleProtectedRoute` component for `/alianzas/*` paths

## Relevant Files
Use these files to implement the feature:

**E2E Test Framework:**
- `.claude/commands/test_e2e.md` - E2E test runner documentation and format
- `.claude/commands/e2e/test_login.md` - Example of basic E2E test format
- `.claude/commands/e2e/test_broker_crud.md` - Existing broker CRUD test (reference)
- `.claude/commands/e2e/test_broker_commission_calculation.md` - Existing commission calculation test (reference)
- `.claude/commands/e2e/test_broker_contract_extraction.md` - Existing contract extraction test (reference)
- `.claude/commands/e2e/test_commission_export_approval.md` - Existing export/approval test (reference)

**Backend Services (for unit tests):**
- `backend/src/core/servicios/comision_service.py` - Commission calculation business logic
- `backend/src/core/servicios/broker_service.py` - Broker management service
- `backend/src/core/servicios/banxico_service.py` - Exchange rate service
- `backend/src/interface/alianzas_dtos.py` - DTOs for validation

**Frontend Pages (for E2E navigation):**
- `frontend/src/pages/alianzas/BrokersPage.tsx` - Broker management page
- `frontend/src/pages/alianzas/ComisionesCalculo.tsx` - Commission calculation page
- `frontend/src/pages/alianzas/PagosHistorial.tsx` - Payment history page
- `frontend/src/components/ui/FKSidebar.tsx` - Sidebar navigation with Alianzas menu

**Types and Services:**
- `frontend/src/types/alianzas.ts` - TypeScript type definitions
- `frontend/src/services/alianzasService.ts` - Frontend API service

**Existing Test Files:**
- `backend/tests/test_comision_service.py` - May need to be created/extended
- `backend/tests/test_banxico_service.py` - May need to be created/extended

### New Files
1. `.claude/commands/e2e/test_alianzas_comisiones.md` - Comprehensive E2E test covering all workflows
2. `backend/tests/fixtures/alianzas_test_data.py` - Test fixtures with sample data
3. `backend/tests/test_alianzas_service.py` - Unit tests for commission calculations

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
| broker_repo.create() | dict | data['id'] | Broker UUID returned |
| broker_repo.get_by_id() | dict | data['porcentaje_apertura'] | Commission rate |
| comision_repo.create() | dict | data['monto_broker_usd'] | Calculated amount |
| comision_repo.get_by_periodo() | list[dict] | item['broker_id'] | Period commissions |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (`TipoBroker`, `TipoComision`, `EstadoComision`, `EstadoPago`)
- [x] Database tables exist (`brokers`, `comisiones`, `pagos`)
- [x] Migration applied: `migration_create_alianzas_tables.sql`
- [x] Banxico API token configured for exchange rates

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| broker.nombre | broker.nombre | string | Broker name |
| broker.tipo_broker | broker.tipo_broker | enum | master_broker/independiente/aliado_logistico/consultoria |
| broker.porcentaje_apertura | broker.porcentaje_apertura | Decimal | Opening commission % |
| broker.porcentaje_operativa | broker.porcentaje_operativa | Decimal | Operations commission % |
| comision.linea_credito | linea_credito | Decimal | Credit line in USD |
| comision.porcentaje_comision_cliente | porcentaje_comision_cliente | Decimal | Client commission % |
| comision.cliente_pago_pct | cliente_pago_pct | Decimal | Client payment % (min 50%) |
| comision.operaciones_mes | operaciones_mes | Decimal | Monthly operations in USD |
| comision.monto_broker_usd | monto_broker_usd | Decimal | Broker commission in USD |
| comision.monto_broker_mxn | monto_broker_mxn | Decimal | Broker commission in MXN |

## Implementation Plan

### Phase 1: Foundation - Test Fixtures
Create reusable test fixtures with sample broker and commission data including expected calculation results.

### Phase 2: Unit Tests
Create unit tests for commission calculation business logic covering:
- Apertura commission formula
- Operativa commission formula
- Edge cases (0% commission, 50% client payment)
- Validation errors

### Phase 3: E2E Integration Test
Create comprehensive E2E test file covering the complete workflow:
1. Broker CRUD Flow
2. Contract Extraction Flow
3. Commission Calculation Flow
4. Export and Approval Flow

## Step by Step Tasks

### Step 1: Create Test Fixtures File
Create `backend/tests/fixtures/alianzas_test_data.py` with sample data:

- Define `SAMPLE_BROKER` dictionary with all broker fields
- Define `SAMPLE_COMISION_APERTURA` with expected calculation results
- Define `SAMPLE_COMISION_OPERATIVA` with expected calculation results
- Include calculation formulas in comments for reference
- Add edge case test data (0% commission, minimum 50% payment)

### Step 2: Create Unit Tests for Commission Service
Create `backend/tests/test_alianzas_service.py`:

- Test apertura commission calculation with known inputs
- Test operativa commission calculation with known inputs
- Test edge case: 0% commission rate
- Test edge case: exactly 50% client payment (minimum allowed)
- Test validation error: client payment < 50%
- Test Excel generation structure (if applicable)
- Use pytest fixtures for broker mock data

### Step 3: Create Comprehensive E2E Test File
Create `.claude/commands/e2e/test_alianzas_comisiones.md`:

**Test Scenario 1: Broker CRUD Flow**
- Navigate to Alianzas > Brokers
- Create new broker with all fields
- Verify broker appears in list
- Edit broker (change porcentaje_apertura)
- Verify changes saved
- Screenshot: broker list with new entry

**Test Scenario 2: Contract Extraction Flow**
- Navigate to broker edit form
- Upload sample contract
- Select "Extracción Estándar"
- Verify fields populated
- Screenshot: form with extracted data

**Test Scenario 3: Commission Calculation Flow**
- Navigate to Alianzas > Cálculo Mensual
- Select current month/year
- Verify exchange rate loaded
- Add apertura commission with specific values
- Verify calculation preview
- Add operativa commission
- Verify calculation
- Screenshot: commissions table
- Screenshot: resumen por broker

**Test Scenario 4: Export and Approval Flow**
- Click "Exportar Excel"
- Verify download starts
- Click "Aprobar Comisiones"
- Confirm in dialog
- Verify success message
- Navigate to Historial de Pagos
- Verify payment record created
- Screenshot: payment history

### Step 4: Ensure fixtures directory exists
Create `backend/tests/fixtures/__init__.py` if it doesn't exist.

### Step 5: Run Validation Commands
Execute all validation commands to verify zero regressions.

## Testing Strategy

### Unit Tests
- `test_apertura_commission_calculation`: Verify formula `linea_credito * (porcentaje_comision_cliente/100) * (porcentaje_broker/100) * (cliente_pago_pct/100)`
- `test_operativa_commission_calculation`: Verify formula `operaciones_mes * (porcentaje_operativa/100)`
- `test_minimum_payment_validation`: Verify 400 error when cliente_pago_pct < 50
- `test_zero_commission_rate`: Verify calculation handles 0% gracefully
- `test_exchange_rate_conversion`: Verify USD to MXN conversion using tipo_cambio

### Edge Cases
- Broker with 0% apertura/operativa commission
- Client payment exactly at 50% threshold
- Client payment at 49% (should fail validation)
- Very large credit line amounts (overflow check)
- Exchange rate unavailable (fallback behavior)
- Missing optional fields in commission request

## Acceptance Criteria
- [ ] Test fixtures file created with sample data (`backend/tests/fixtures/alianzas_test_data.py`)
- [ ] Unit tests created for commission calculations (`backend/tests/test_alianzas_service.py`)
- [ ] Comprehensive E2E test file created (`.claude/commands/e2e/test_alianzas_comisiones.md`)
- [ ] All unit tests pass: `cd backend && python -m pytest tests/test_alianzas_service.py -v`
- [ ] Backend linting passes: `cd backend && ruff check src/`
- [ ] Frontend TypeScript check passes: `cd frontend && npx tsc --noEmit`
- [ ] Frontend build succeeds: `cd frontend && npm run build`
- [ ] Navigation to /alianzas routes works for alianzas/admin roles
- [ ] Non-alianzas users cannot access /alianzas routes
- [ ] Commission calculations match expected formulas

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# 1. Run the new alianzas unit tests
cd backend && python -m pytest tests/test_alianzas_service.py -v

# 2. Run all backend tests
cd backend && python -m pytest

# 3. Run backend linting
cd backend && ruff check src/

# 4. Run frontend linting
cd frontend && npm run lint

# 5. Run frontend TypeScript type check
cd frontend && npx tsc --noEmit

# 6. Run frontend build
cd frontend && npm run build

# 7. E2E test (manual with Playwright MCP)
# Read .claude/commands/test_e2e.md, then execute .claude/commands/e2e/test_alianzas_comisiones.md
```

## Notes

### Commission Calculation Formulas
**Apertura Commission:**
```
monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / 100)
monto_broker_usd = monto_comision_cliente * (porcentaje_broker_apertura / 100) * (cliente_pago_pct / 100)
monto_broker_mxn = monto_broker_usd * tipo_cambio
```

**Operativa Commission:**
```
monto_broker_usd = operaciones_mes * (porcentaje_operativa / 100)
monto_broker_mxn = monto_broker_usd * tipo_cambio
```

### Business Rules
- `cliente_pago_pct` must be >= 50% for apertura commissions
- Exchange rate fetched from Banxico SIE API (SF43718)
- Falls back to previous business day if rate not available
- Approval creates aggregated payment records per broker

### Existing E2E Tests
The Alianzas module already has individual E2E tests:
- `test_broker_crud.md` - Broker CRUD operations
- `test_broker_contract_extraction.md` - Contract extraction (regex)
- `test_ai_contract_extraction.md` - AI-powered extraction
- `test_banxico_exchange_rate.md` - Exchange rate integration
- `test_broker_commission_calculation.md` - Commission calculation API
- `test_commission_export_approval.md` - Export and approval workflow

The new `test_alianzas_comisiones.md` provides a **unified workflow test** that validates the complete end-to-end user journey.

### Dependencies
- pytest (already in requirements.txt)
- ruff (for linting)
- Playwright MCP (for E2E execution)

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - tables exist)
- [x] E2E test file task included
- [x] All external dependencies listed in Notes

### Category-Specific Completeness (CRUD Operations)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for repository methods
- [x] Business rules documented (50% minimum payment, formulas)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
