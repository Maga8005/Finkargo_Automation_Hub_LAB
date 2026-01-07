# Feature: Differentiate Paga Local Crédito Contract ID Prefixes

## Feature Description
The three Paga Local Colombia K° Crédito contract types currently share the same contract ID prefix (`PLCR`), causing duplicate contract ID generation errors (HTTP 500) when contracts of different aval types are created. This feature updates the database function to use unique prefixes for each contract type:
- `pl_co_credito_aval_pj` (Aval Persona Jurídica) → **PLCRJ**
- `pl_co_credito_aval_pn` (Aval Persona Natural) → **PLCRN**
- `pl_co_credito_no_aval` (Sin Aval) → **PLCRS**

## User Story
As an **operations** team member
I want to generate K° Crédito contracts for different aval types without duplicate ID errors
So that I can efficiently request contracts for all client scenarios without encountering 500 errors

## Problem Statement
The current `generate_contract_id()` database function assigns the same prefix `PLCR` to three different contract types:
- `pl_co_credito_no_aval`
- `pl_co_credito_aval_pj`
- `pl_co_credito_aval_pn`

Since these contract types share the same prefix but use individual sequence counters per `contract_type`, the generated IDs can collide. For example:
- First `pl_co_credito_aval_pj` contract → `PLCR-2025-001`
- First `pl_co_credito_aval_pn` contract → `PLCR-2025-001` (DUPLICATE!)

This causes a unique constraint violation on the `contract_id` column, resulting in HTTP 500 errors when users attempt to generate contracts.

## Solution Statement
Update the `generate_contract_id()` PostgreSQL function to assign unique prefixes to each K° Crédito contract type:
- `pl_co_credito_aval_pj` → **PLCRJ** (Paga Local CRédito Jurídica)
- `pl_co_credito_aval_pn` → **PLCRN** (Paga Local CRédito Natural)
- `pl_co_credito_no_aval` → **PLCRS** (Paga Local CRédito Sin aval)

This ensures each contract type generates unique IDs even when their sequence counters are at the same value:
- First `pl_co_credito_aval_pj` → `PLCRJ-2025-001`
- First `pl_co_credito_aval_pn` → `PLCRN-2025-001`
- First `pl_co_credito_no_aval` → `PLCRS-2025-001`

## Access Control
- Required Role(s): `operations`, `admin` (users who generate contracts)
- Backend Protection: No changes needed - existing RBAC covers contract generation
- Frontend Protection: No changes needed - existing RoleProtectedRoute covers operations pages

## Relevant Files
Use these files to implement the feature:

- `backend/database/migration_add_paga_local_contract_id_prefixes.sql` - The current migration that defines the `generate_contract_id()` function with the incorrect shared prefix. This file needs to be referenced to understand the current implementation.
- `backend/src/repositorio/contract_repository.py` - Repository that calls the `generate_contract_id()` database function via RPC. No changes needed, but useful for understanding the flow.
- `backend/src/core/servicios/contract_service.py` - Service layer that orchestrates contract generation. No changes needed.
- `backend/src/interface/legal_dtos.py` - Contains the `ContractType` enum defining all contract types. No changes needed.

### New Files
- `backend/database/migration_differentiate_paga_local_credito_prefixes.sql` - New migration to update the `generate_contract_id()` function with differentiated prefixes for K° Crédito contract types.

## Implementation Plan

### Phase 1: Foundation
- Analyze current `generate_contract_id()` function to understand the CASE statement structure
- Design the updated prefix mapping:
  - `pl_co_credito_aval_pj` → `PLCRJ`
  - `pl_co_credito_aval_pn` → `PLCRN`
  - `pl_co_credito_no_aval` → `PLCRS`

### Phase 2: Core Implementation
- Create a new SQL migration that:
  1. Drops the existing `generate_contract_id()` function
  2. Recreates it with the updated prefix mappings
  3. No sequence changes needed (sequences are per contract_type, not per prefix)

### Phase 3: Integration
- Apply migration to Supabase database
- Test all three contract types to verify unique IDs
- Verify existing contract types (activos, otrosi, inventario_bodega) still work correctly

## Step by Step Tasks

### Step 1: Create Database Migration File
- Create `backend/database/migration_differentiate_paga_local_credito_prefixes.sql`
- Drop the existing `generate_contract_id()` function
- Recreate function with updated CASE statement:
  ```sql
  WHEN 'pl_co_credito_aval_pj' THEN prefix := 'PLCRJ';
  WHEN 'pl_co_credito_aval_pn' THEN prefix := 'PLCRN';
  WHEN 'pl_co_credito_no_aval' THEN prefix := 'PLCRS';
  ```
- Include verification queries to test the new prefixes

### Step 2: Update Combined Schema Documentation
- Update `backend/database/combined_schema.sql` to reflect the new prefix mappings in comments
- This ensures future developers understand the prefix scheme

### Step 3: Run Validation Commands
- Run backend tests to ensure no regressions
- Run linting checks
- Verify TypeScript compilation (frontend should have no changes)

## Testing Strategy

### Unit Tests
- No new Python tests needed - the logic is in the database function
- Existing contract generation tests should continue to pass

### Integration Testing (Manual via Supabase SQL Editor)
- After applying migration, run:
  ```sql
  -- Test each prefix generates correctly
  SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Should return PLCRJ-2025-XXX
  SELECT generate_contract_id('pl_co_credito_aval_pn');  -- Should return PLCRN-2025-XXX
  SELECT generate_contract_id('pl_co_credito_no_aval');  -- Should return PLCRS-2025-XXX

  -- Verify existing types still work
  SELECT generate_contract_id('activos');               -- Should return ACT-2025-XXX
  SELECT generate_contract_id('otrosi');                -- Should return OTRO-2025-XXX
  ```

### Edge Cases
- Verify function handles unknown contract types (should default to 'ACT')
- Verify Mandato contracts (PLCM prefix) are not affected
- Verify sequences increment correctly after migration

## Acceptance Criteria
1. `pl_co_credito_aval_pj` contracts generate IDs with prefix `PLCRJ` (e.g., `PLCRJ-2025-001`)
2. `pl_co_credito_aval_pn` contracts generate IDs with prefix `PLCRN` (e.g., `PLCRN-2025-001`)
3. `pl_co_credito_no_aval` contracts generate IDs with prefix `PLCRS` (e.g., `PLCRS-2025-001`)
4. No duplicate contract ID errors (HTTP 500) when generating different K° Crédito contract types
5. Existing contract types (activos, otrosi, inventario_bodega) continue to work correctly
6. Mandato contract prefixes (PLCM) remain unchanged

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

### Database Validation (Run in Supabase SQL Editor after applying migration)
```sql
-- Test differentiated prefixes
SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Expect: PLCRJ-2025-XXX
SELECT generate_contract_id('pl_co_credito_aval_pn');  -- Expect: PLCRN-2025-XXX
SELECT generate_contract_id('pl_co_credito_no_aval');  -- Expect: PLCRS-2025-XXX

-- Verify existing types unaffected
SELECT generate_contract_id('activos');               -- Expect: ACT-2025-XXX
SELECT generate_contract_id('otrosi');                -- Expect: OTRO-2025-XXX
SELECT generate_contract_id('inventario_bodega');     -- Expect: INV-2025-XXX

-- Verify Mandato types unaffected
SELECT generate_contract_id('pl_co_mandato_no_aval'); -- Expect: PLCM-2025-XXX
SELECT generate_contract_id('pl_co_mandato_pj');      -- Expect: PLCM-2025-XXX
SELECT generate_contract_id('pl_co_mandato_pn');      -- Expect: PLCM-2025-XXX
```

## Notes
- **No code changes required** - This is a database-only fix via SQL migration
- **Migration must be applied manually** to the Supabase database via SQL Editor
- **No new dependencies** required
- **Backward compatible** - Existing contracts with `PLCR-` prefix will remain unchanged; only new contracts will use the differentiated prefixes
- **Prefix naming convention**:
  - `PLCRJ` = Paga Local CRédito Jurídica (PJ)
  - `PLCRN` = Paga Local CRédito Natural (PN)
  - `PLCRS` = Paga Local CRédito Sin aval
- **Future consideration**: Consider applying the same differentiation to Mandato contracts (`PLCM`) if similar duplicate ID issues arise
