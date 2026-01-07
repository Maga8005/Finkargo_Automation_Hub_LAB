# Implementation: Differentiate Paga Local Contract ID Prefixes

**Date:** 2025-12-06
**Module:** Database
**Spec:** `specs/issue-N-adw-N-sdlc_planner-differentiate-paga-local-credito-prefixes.md`

## Summary

Updated the `generate_contract_id()` PostgreSQL function to use unique prefixes for each K° Crédito and Mandato contract type, preventing duplicate contract ID errors (HTTP 500) when generating contracts of different aval types.

## Problem

The Paga Local Colombia contract types shared the same prefixes within their categories:
- K° Crédito contracts all used `PLCR`
- Mandato contracts all used `PLCM`

Since each contract type has its own sequence counter, this caused ID collisions:
- First `pl_co_credito_aval_pj` contract → `PLCR-2025-001`
- First `pl_co_credito_aval_pn` contract → `PLCR-2025-001` (DUPLICATE!)

## Solution

Assigned unique prefixes to each contract type:

**K° Crédito contracts:**
- `pl_co_credito_aval_pj` → **PLCRJ** (Paga Local CRédito Jurídica)
- `pl_co_credito_aval_pn` → **PLCRN** (Paga Local CRédito Natural)
- `pl_co_credito_no_aval` → **PLCRS** (Paga Local CRédito Sin aval)

**Mandato contracts:**
- `pl_co_mandato_pj` → **PLCMJ** (Paga Local Cuenta Mandato Jurídica)
- `pl_co_mandato_pn` → **PLCMN** (Paga Local Cuenta Mandato Natural)
- `pl_co_mandato_no_aval` → **PLCMS** (Paga Local Cuenta Mandato Sin aval)

## Changes Made

- Created new migration: `backend/database/migration_differentiate_paga_local_credito_prefixes.sql`
  - Drops and recreates the `generate_contract_id()` function with differentiated prefixes
  - Includes verification queries for testing
- Updated `backend/database/combined_schema.sql` to reflect the new prefix mappings

## Files Changed

```
backend/database/combined_schema.sql                                        | 11 +++++--
backend/database/migration_differentiate_paga_local_credito_prefixes.sql    | 114 +++++++++ (new)
```

## Validation

- Backend pytest: 9 tests passed (pre-existing fixture errors in unrelated Google Drive tests)
- TypeScript type check: Passed
- Frontend build: Succeeded

## Database Validation (Run in Supabase SQL Editor after applying migration)

```sql
-- Test differentiated K° Crédito prefixes
SELECT generate_contract_id('pl_co_credito_aval_pj');  -- Expect: PLCRJ-2025-XXX
SELECT generate_contract_id('pl_co_credito_aval_pn');  -- Expect: PLCRN-2025-XXX
SELECT generate_contract_id('pl_co_credito_no_aval');  -- Expect: PLCRS-2025-XXX

-- Test differentiated Mandato prefixes
SELECT generate_contract_id('pl_co_mandato_pj');      -- Expect: PLCMJ-2025-XXX
SELECT generate_contract_id('pl_co_mandato_pn');      -- Expect: PLCMN-2025-XXX
SELECT generate_contract_id('pl_co_mandato_no_aval'); -- Expect: PLCMS-2025-XXX

-- Verify existing types unaffected
SELECT generate_contract_id('activos');               -- Expect: ACT-2025-XXX
SELECT generate_contract_id('otrosi');                -- Expect: OTRO-2025-XXX
SELECT generate_contract_id('inventario_bodega');     -- Expect: INV-2025-XXX
```

## Deployment Steps

1. Apply migration to Supabase database via SQL Editor:
   - Run `backend/database/migration_differentiate_paga_local_credito_prefixes.sql`
2. Verify with the validation queries above
3. Test contract generation in the application

## Notes

- **No code changes required** - This is a database-only fix
- **Backward compatible** - Existing contracts with old prefixes (`PLCR-`, `PLCM-`) remain unchanged; only new contracts use differentiated prefixes
