# Chore: Add Unique Contract ID Prefix for Paga Local Colombia Sin Aval Contracts

## Chore Description
The Paga Local Colombia "Sin Aval" contracts (K° Crédito No Aval and K° Mandato No Aval) are currently generating contract IDs with the same `ACT-YYYY-NNN` format as regular Activos contracts. This makes it difficult to differentiate Paga Local contracts from other contract types at a glance.

**Requirements:**
1. Create a SQL migration to update the `generate_contract_id` database function to handle Paga Local contract types with a unique prefix (e.g., `PLC-YYYY-NNN` for Paga Local Colombia)
2. Initialize sequence records for the new Paga Local contract types
3. The frontend already has contract type badge/chip labels in the approved contracts table (line 57-67 in `FKPagaLocalCOApprovedContracts.tsx`), so no frontend changes needed for differentiation - the contract_id prefix itself will provide visual distinction

**Proposed Prefixes:**

### Existing Contract Types (Already Implemented)
| Contract Type | Prefix | Example | Status |
|--------------|--------|---------|--------|
| activos | ACT | ACT-2025-001 | ✅ Implemented |
| otrosi | OTRO | OTRO-2025-001 | ✅ Implemented |
| inventario_bodega | INV | INV-2025-001 | ✅ Implemented |

### Paga Local Colombia - Contratos Cuenta Cliente (Account-Level Contracts)
| Contract Type | Prefix | Example | Status |
|--------------|--------|---------|--------|
| pl_co_credito_no_aval | PLCR | PLCR-2025-001 | 🆕 New |
| pl_co_credito_aval_pj | PLCR | PLCR-2025-001 | 🆕 New |
| pl_co_credito_aval_pn | PLCR | PLCR-2025-001 | 🆕 New |
| pl_co_mandato_no_aval | PLCM | PLCM-2025-001 | 🆕 New |
| pl_co_mandato_pj | PLCM | PLCM-2025-001 | 🆕 New |
| pl_co_mandato_pn | PLCM | PLCM-2025-001 | 🆕 New |

### Paga Local Colombia - Documentos Operación (Operation-Level Documents)
| Contract Type | Prefix | Example | Status |
|--------------|--------|---------|--------|
| pl_co_mandato_im | PLMI | PLMI-2025-001 | 🆕 New |
| pl_co_solicitud_desembolso | PLSD | PLSD-2025-001 | 🆕 New |
| pl_co_dian_mandato_im | PLDI | PLDI-2025-001 | 🆕 New |

**Prefix Logic:**
- `PLCR` = **P**aga **L**ocal **CR**édito (all crédito account contracts share this)
- `PLCM` = **P**aga **L**ocal **C**uenta **M**andato (all mandato account contracts share this)
- `PLMI` = **P**aga **L**ocal **M**andato **I**mportación (operation document)
- `PLSD` = **P**aga **L**ocal **S**olicitud **D**esembolso (operation document)
- `PLDI` = **P**aga **L**ocal **D**IAN (operation document)

## Relevant Files
Use these files to resolve the chore:

- `backend/database/migration_add_otrosi_support_FIXED.sql` (lines 97-143) - Contains the current `generate_contract_id()` function implementation. This shows the pattern for how contract type prefixes are mapped. Need to understand structure before creating new migration.

- `backend/src/repositorio/contract_repository.py` (lines 22-33) - Repository method that calls the `generate_contract_id` RPC function. **No changes needed** - it already passes `contract_type` parameter.

- `backend/src/core/servicios/contract_service.py` (line 77) - Service that calls repository to generate contract ID. **No changes needed** - it already passes the correct `contract_type`.

- `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx` (lines 57-67) - Already has contract type badges with appropriate colors and labels. **No changes needed** - this provides the visual differentiation in the UI.

### New Files
- `backend/database/migration_add_paga_local_contract_id_prefixes.sql` - New migration to update the `generate_contract_id()` function with Paga Local prefixes and initialize sequences

## Step by Step Tasks

### Step 1: Create the SQL Migration File
- Create new file: `backend/database/migration_add_paga_local_contract_id_prefixes.sql`
- The migration should:
  1. Drop and recreate the `generate_contract_id(VARCHAR)` function
  2. Add prefix mappings for all Paga Local contract types:
     - `pl_co_credito_no_aval` → `PLCR`
     - `pl_co_mandato_no_aval` → `PLCM`
     - `pl_co_credito_aval_pj` → `PLCR`
     - `pl_co_mandato_pj` → `PLCM`
     - `pl_co_credito_aval_pn` → `PLCR`
     - `pl_co_mandato_pn` → `PLCM`
     - `pl_co_mandato_im` → `PLMI`
     - `pl_co_solicitud_desembolso` → `PLSD`
     - `pl_co_dian_mandato_im` → `PLDI`
     - `inventario_bodega` → `INV`
  3. Initialize sequence records for each new contract type
  4. Include verification queries

**Function logic should be:**
```sql
CREATE OR REPLACE FUNCTION generate_contract_id(p_contract_type VARCHAR DEFAULT 'activos')
RETURNS VARCHAR AS $$
DECLARE
    current_year INTEGER;
    next_sequence INTEGER;
    prefix VARCHAR(10);
BEGIN
    current_year := EXTRACT(YEAR FROM CURRENT_DATE);

    -- Determine prefix based on contract type
    CASE p_contract_type
        WHEN 'activos' THEN prefix := 'ACT';
        WHEN 'otrosi' THEN prefix := 'OTRO';
        WHEN 'inventario_bodega' THEN prefix := 'INV';  -- Already implemented
        -- Paga Local Colombia - Crédito contracts (NEW)
        WHEN 'pl_co_credito_no_aval' THEN prefix := 'PLCR';
        WHEN 'pl_co_credito_aval_pj' THEN prefix := 'PLCR';
        WHEN 'pl_co_credito_aval_pn' THEN prefix := 'PLCR';
        -- Paga Local Colombia - Mandato contracts (Account-Level)
        WHEN 'pl_co_mandato_no_aval' THEN prefix := 'PLCM';
        WHEN 'pl_co_mandato_pj' THEN prefix := 'PLCM';
        WHEN 'pl_co_mandato_pn' THEN prefix := 'PLCM';
        -- Paga Local Colombia - Documentos Operación (Operation-Level)
        WHEN 'pl_co_mandato_im' THEN prefix := 'PLMI';
        WHEN 'pl_co_solicitud_desembolso' THEN prefix := 'PLSD';
        WHEN 'pl_co_dian_mandato_im' THEN prefix := 'PLDI';
        ELSE prefix := 'ACT';  -- Default fallback
    END CASE;

    -- Rest of sequence logic remains the same...
END;
$$ LANGUAGE plpgsql;
```

### Step 2: Add Sequence Initialization
- In the same migration file, add INSERT statements to initialize sequences for all Paga Local contract types:
```sql
-- Only initialize sequences for NEW Paga Local contract types
-- (inventario_bodega already has its sequence)
INSERT INTO contract_id_sequence (year, contract_type, last_sequence, created_at)
VALUES
    -- Account-Level Contracts (Contratos Cuenta Cliente)
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_no_aval', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_no_aval', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_aval_pj', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_pj', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_credito_aval_pn', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_pn', 0, NOW()),
    -- Operation-Level Documents (Documentos Operación)
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_mandato_im', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_solicitud_desembolso', 0, NOW()),
    (EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER, 'pl_co_dian_mandato_im', 0, NOW())
ON CONFLICT (year, contract_type) DO NOTHING;
```

### Step 3: Add Verification Queries
- Add commented verification queries at the end of the migration:
```sql
-- Verify function works for all contract types

-- Account-Level Contracts (Contratos Cuenta Cliente)
-- SELECT generate_contract_id('pl_co_credito_no_aval');  -- Should return PLCR-2025-001
-- SELECT generate_contract_id('pl_co_mandato_no_aval');  -- Should return PLCM-2025-001
-- SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Should return PLCR-2025-001
-- SELECT generate_contract_id('pl_co_mandato_pj');       -- Should return PLCM-2025-001

-- Operation-Level Documents (Documentos Operación)
-- SELECT generate_contract_id('pl_co_mandato_im');           -- Should return PLMI-2025-001
-- SELECT generate_contract_id('pl_co_solicitud_desembolso'); -- Should return PLSD-2025-001
-- SELECT generate_contract_id('pl_co_dian_mandato_im');      -- Should return PLDI-2025-001

-- Existing types (should still work)
-- SELECT generate_contract_id('activos');                -- Should return ACT-2025-XXX
-- SELECT generate_contract_id('otrosi');                 -- Should return OTRO-2025-XXX
-- SELECT generate_contract_id('inventario_bodega');      -- Should return INV-2025-XXX

-- Verify sequence table
-- SELECT * FROM contract_id_sequence ORDER BY contract_type, year DESC;
```

### Step 4: Execute Migration in Supabase
- Open Supabase SQL Editor
- Copy and execute the migration SQL
- Run verification queries to confirm function works correctly

### Step 5: Update combined_schema.sql (Optional)
- Update `backend/database/combined_schema.sql` to include the new function definition for documentation purposes
- This ensures the complete schema is captured in version control

### Step 6: Run Validation Commands

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

**Database verification (run in Supabase SQL Editor):**
```sql
-- Test new prefixes
SELECT generate_contract_id('pl_co_credito_no_aval');  -- Should return PLCR-2025-001
SELECT generate_contract_id('pl_co_mandato_no_aval');  -- Should return PLCM-2025-001
SELECT generate_contract_id('activos');                -- Should continue working

-- Verify sequences initialized
SELECT * FROM contract_id_sequence
WHERE contract_type LIKE 'pl_co_%'
ORDER BY contract_type;
```

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- The frontend `FKPagaLocalCOApprovedContracts.tsx` already has excellent visual differentiation via colored Chip badges for each contract type (lines 57-67). The contract_id prefix change will add another layer of differentiation.
- All Paga Local Crédito types share the same `PLCR` prefix because they are conceptually the same document type (just different aval configurations). Same logic applies to Mandato types with `PLCM`.
- The sequence is tracked per contract_type, so each type has its own independent counter (e.g., PLCR-2025-001, PLCM-2025-001 can coexist).
- This migration is **additive** - it doesn't change existing contract IDs, only affects new contracts generated after the migration.
- The existing `contract_repository.py` and `contract_service.py` already pass the correct `contract_type` parameter, so no backend code changes are required.
