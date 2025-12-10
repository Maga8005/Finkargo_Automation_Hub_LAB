# Feature: Alianzas Department Foundation - Database Schema and Role Configuration

## Feature Description
Create the foundational database schema and role configuration for the new Alianzas (Partnerships/Alliances) department module. This foundation includes three database tables for managing brokers, their commissions, and payments, along with the necessary role-based access control configuration and a basic API structure. This feature establishes the data layer that will support future broker commission management features.

## User Story
As an **admin or alianzas department user**
I want to have a database structure to store broker information, commissions, and payment records
So that I can manage broker partnerships and track commission calculations and payments

## Problem Statement
The Alianzas department needs a dedicated system to manage broker relationships and commission payments. Currently, there is no database infrastructure to support:
- Master broker and sub-broker hierarchies
- Commission calculations (apertura and operativa types)
- Payment tracking and scheduling
- Role-based access for alianzas staff

## Solution Statement
Create a complete database foundation consisting of:
1. Three interconnected tables (`brokers`, `broker_comisiones`, `broker_pagos`) with proper relationships and constraints
2. Row Level Security policies restricting write access to admin and alianzas roles
3. Performance indexes for common query patterns
4. A new `alianzas` role in both frontend and backend RBAC systems
5. A basic API router with health check endpoint

## Access Control
- Required Role(s): `admin`, `alianzas`
- Backend Protection: Use `require_roles(['alianzas'])` dependency (admin bypass enabled by default)
- Frontend Protection: Add `'alianzas'` to UserRole type for future UI components

## Relevant Files
Use these files to implement the feature:

**Backend - Role Configuration:**
- `backend/src/adapter/rest/rbac_dependencies.py` - Add `require_alianzas_role` dependency following `require_tesoreria_role` pattern (line 115)
- `backend/main.py` - Register new `alianzas_routes` router (lines 12, 56-60)

**Backend - New Routes:**
- Reference pattern: `backend/src/adapter/rest/tesoreria_routes.py` - Example of minimal route file with RBAC

**Database - Migrations:**
- Reference pattern: `backend/database/migration_add_finance_reports.sql` - Example of table creation with RLS and indexes
- Reference pattern: `backend/database/migration_add_tesoreria_role.sql` - Example of adding role to CHECK constraint
- Reference pattern: `backend/database/schema.sql` - Core schema patterns for UUID, timestamps, triggers

**Frontend - Types:**
- `frontend/src/types/index.ts` - Add `alianzas` to `UserRole` type (lines 70-81) and `UserRole` const (lines 82-93)

### New Files
- `backend/database/migration_create_alianzas_tables.sql` - Migration for brokers, broker_comisiones, broker_pagos tables
- `backend/database/migration_add_alianzas_role.sql` - Migration to add alianzas role to user_profiles CHECK constraint
- `backend/src/adapter/rest/alianzas_routes.py` - API routes for alianzas module

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature does not involve document generation.

### B. Excel Column Mapping (Excel Processing only)
N/A - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)
N/A - This feature does not involve file import/export.

### D. Data Contract Verification (ALL features)
This feature creates new database tables. The data contracts are defined as follows:

**Table: `brokers`**
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID | No | Primary key, auto-generated |
| nombre | VARCHAR(255) | No | Broker name |
| tipo_broker | VARCHAR(50) | No | Enum: master_broker, independiente, aliado_logistico, consultoria |
| master_broker_id | UUID | Yes | Self-referencing FK for hierarchies |
| porcentaje_apertura | DECIMAL(5,2) | Yes | e.g., 60.00 for 60% |
| porcentaje_operativa | DECIMAL(5,3) | Yes | e.g., 0.100 for 0.10% |
| cuenta_bancaria | VARCHAR(50) | Yes | Bank account number |
| banco | VARCHAR(100) | Yes | Bank name |
| rfc | VARCHAR(20) | Yes | Mexican tax ID |
| fecha_contrato | DATE | Yes | Contract start date |
| vigencia_contrato | DATE | Yes | Contract end date |
| estado | VARCHAR(20) | No | Default 'activo', enum: activo, inactivo, pendiente |
| link_expediente | TEXT | Yes | URL to document folder |
| notas | TEXT | Yes | Notes |
| created_at | TIMESTAMP | No | Auto-generated |
| updated_at | TIMESTAMP | No | Auto-updated via trigger |
| created_by | UUID | Yes | FK to auth.users |

**Table: `broker_comisiones`**
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID | No | Primary key |
| broker_id | UUID | No | FK to brokers |
| periodo_mes | INTEGER | No | Month 1-12 |
| periodo_anio | INTEGER | No | Year |
| cliente_nombre | VARCHAR(255) | Yes | Client name |
| cliente_nit | VARCHAR(50) | Yes | Client tax ID |
| tipo_comision | VARCHAR(20) | No | Enum: apertura, operativa |
| linea_credito | DECIMAL(15,2) | Yes | Credit line amount |
| porcentaje_comision_cliente | DECIMAL(5,2) | Yes | Client commission % |
| monto_comision_cliente | DECIMAL(15,2) | Yes | Client commission amount |
| porcentaje_broker | DECIMAL(5,3) | Yes | Broker commission % |
| monto_broker_usd | DECIMAL(15,2) | Yes | Broker amount in USD |
| operaciones_mes | DECIMAL(15,2) | Yes | Monthly operations total |
| tipo_cambio | DECIMAL(10,4) | Yes | Exchange rate |
| monto_broker_mxn | DECIMAL(15,2) | Yes | Broker amount in MXN |
| cliente_pago_pct | DECIMAL(5,2) | Yes | Client payment percentage |
| estado | VARCHAR(20) | No | Default 'calculado', enum: calculado, aprobado, pagado |
| notas | TEXT | Yes | Notes |
| created_at | TIMESTAMP | No | Auto-generated |
| created_by | UUID | Yes | FK to auth.users |

**Table: `broker_pagos`**
| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| id | UUID | No | Primary key |
| broker_id | UUID | No | FK to brokers |
| periodo_mes | INTEGER | No | Month 1-12 |
| periodo_anio | INTEGER | No | Year |
| total_usd | DECIMAL(15,2) | No | Total in USD |
| total_mxn | DECIMAL(15,2) | No | Total in MXN |
| tipo_cambio | DECIMAL(10,4) | No | Exchange rate |
| fecha_programada | DATE | Yes | Scheduled payment date |
| fecha_pago | DATE | Yes | Actual payment date |
| estado | VARCHAR(20) | No | Default 'pendiente', enum: pendiente, programado, pagado |
| comprobante_url | TEXT | Yes | Payment receipt URL |
| factura_broker_url | TEXT | Yes | Broker invoice URL |
| notas | TEXT | Yes | Notes |
| created_at | TIMESTAMP | No | Auto-generated |
| approved_by | UUID | Yes | FK to auth.users |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - N/A for this foundational feature (DTOs will be added in future)
- [x] Template file exists in `backend/templates/` - N/A
- [x] Database records exist (or migration created) - Migration will create tables
- [x] Country-specific data handled (CO vs MX) - Tables designed to support both, MXN currency columns included

### F. External API Contract (Integration only)
N/A - This feature does not involve external APIs.

### G. Query Specification (Reporting only)
N/A - Queries will be defined in future features. Indexes are created for anticipated query patterns.

### Interface Mapping (Frontend ↔ Backend)
For health endpoint only (future CRUD will need full mapping):

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| status | status | string | "healthy" |
| module | module | string | "alianzas" |

## Implementation Plan

### Phase 1: Foundation
1. Create database migration for the alianzas role addition to user_profiles
2. Create database migration for the three alianzas tables
3. Add `alianzas` role to frontend TypeScript types

### Phase 2: Core Implementation
1. Add `require_alianzas_role` dependency to rbac_dependencies.py
2. Create alianzas_routes.py with health endpoint
3. Register alianzas router in main.py

### Phase 3: Integration
1. Verify all migrations can be applied
2. Test health endpoint with role protection
3. Validate frontend type compilation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Add alianzas role to user_profiles CHECK constraint
Create the migration file to update the user_profiles table CHECK constraint to include the `alianzas` role.

- Create `backend/database/migration_add_alianzas_role.sql`
- Follow the pattern from `migration_add_tesoreria_role.sql`
- Drop existing constraint and recreate with alianzas added
- Include verification query to show existing roles

### Task 2: Create database migration for alianzas tables
Create the main migration file with all three tables, indexes, triggers, and RLS policies.

- Create `backend/database/migration_create_alianzas_tables.sql`
- Create `brokers` table with all specified columns
- Create `broker_comisiones` table with all specified columns
- Create `broker_pagos` table with all specified columns
- Add self-referencing FK on brokers for master_broker hierarchy
- Add FK constraints to auth.users where specified
- Create all 5 indexes specified in requirements
- Create updated_at trigger for brokers table
- Enable RLS on all three tables
- Create SELECT policy for authenticated users
- Create INSERT/UPDATE/DELETE policies checking for admin or alianzas role via user_profiles
- Add service_role full access policy
- Add table and column comments

### Task 3: Add alianzas role to frontend TypeScript types
Update the frontend types to include the new alianzas role.

- Edit `frontend/src/types/index.ts`
- Add `'alianzas'` to the `UserRole` type union (line ~80)
- Add `ALIANZAS: 'alianzas' as const` to the `UserRole` const object (line ~92)

### Task 4: Add require_alianzas_role to backend RBAC
Add the pre-configured alianzas role dependency to the RBAC module.

- Edit `backend/src/adapter/rest/rbac_dependencies.py`
- Add `require_alianzas_role = require_roles(['alianzas'])` following the tesoreria pattern (after line 115)

### Task 5: Create alianzas_routes.py
Create the basic API router for the alianzas module with health endpoint.

- Create `backend/src/adapter/rest/alianzas_routes.py`
- Import FastAPI router, logging, and rbac_dependencies
- Create router with prefix `/api/alianzas` and tags `["Alianzas - Partnerships"]`
- Create local `require_alianzas_role` using `require_roles(['alianzas'])`
- Implement `GET /health` endpoint that returns `{"status": "healthy", "module": "alianzas"}`
- Health endpoint should use the alianzas role dependency

### Task 6: Register alianzas router in main.py
Update the main application file to include the alianzas routes.

- Edit `backend/main.py`
- Add import for `alianzas_routes` in the imports section (line 12)
- Add `app.include_router(alianzas_routes.router)` after tesoreria_routes (line 61)

### Task 7: Run validation commands
Execute all validation commands to ensure the implementation is correct.

## Testing Strategy

### Unit Tests
For this foundational feature, the primary tests are:
1. Health endpoint returns 200 with correct payload
2. Health endpoint requires alianzas or admin role
3. TypeScript compilation succeeds with new role
4. Backend linting passes

### Edge Cases
1. User without alianzas role attempting to access health endpoint → 403
2. Admin user accessing health endpoint → 200 (admin bypass)
3. Inactive user with alianzas role → 403 (is_active check)

## Acceptance Criteria
- [ ] Migration file `migration_add_alianzas_role.sql` created with role CHECK constraint update
- [ ] Migration file `migration_create_alianzas_tables.sql` created with all three tables
- [ ] All three tables have proper constraints (PKs, FKs, CHECKs)
- [ ] Self-referencing FK on brokers.master_broker_id works correctly
- [ ] All 5 indexes created per specification
- [ ] RLS enabled on all three tables
- [ ] RLS policies allow SELECT for authenticated, INSERT/UPDATE/DELETE for admin/alianzas
- [ ] `alianzas` role added to frontend UserRole type and const
- [ ] `require_alianzas_role` dependency added to rbac_dependencies.py
- [ ] `alianzas_routes.py` created with `/api/alianzas/health` endpoint
- [ ] Router registered in main.py
- [ ] Health endpoint returns 200 OK with correct JSON structure
- [ ] Backend pytest passes
- [ ] Backend ruff linting passes
- [ ] Frontend TypeScript compilation passes
- [ ] Frontend build succeeds

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend validation
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend linting
cd frontend && npm run lint

# Frontend production build
cd frontend && npm run build

# Test health endpoint (requires running backend)
# After applying migrations and starting backend:
# curl -X GET http://localhost:8000/api/alianzas/health
```

## Notes

### Database Migration Application
The migration files must be applied in order:
1. First: `migration_add_alianzas_role.sql` - Updates CHECK constraint
2. Second: `migration_create_alianzas_tables.sql` - Creates tables with RLS

Apply migrations via Supabase SQL Editor or psql.

### RLS Policy Design
The RLS policies for write operations (INSERT, UPDATE, DELETE) need to check the user's role in the `user_profiles` table. The policy uses a subquery pattern:
```sql
CREATE POLICY "Admin and alianzas can insert brokers"
ON brokers FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM user_profiles
    WHERE user_profiles.id = auth.uid()
    AND user_profiles.role IN ('admin', 'alianzas')
    AND user_profiles.is_active = true
  )
);
```

### Future Considerations
- DTOs and interfaces will be created when CRUD operations are implemented
- Repository layer will be added for data access
- Service layer for business logic (commission calculations)
- Frontend components and pages for broker management UI

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (CRUD Operations)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature) - N/A, no UI in this feature
- [x] All external dependencies (npm/pip packages) listed in Notes - None required

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data contract tables documented in section D
- [x] Database records verified - migrations will create them
- [x] Country-specific variations handled - MXN columns included for Mexico

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods - N/A for this phase
- [x] Country-specific variations handled (CO vs MX) if applicable

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature) - N/A
