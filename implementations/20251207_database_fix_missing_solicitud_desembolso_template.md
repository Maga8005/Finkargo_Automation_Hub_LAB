# Implementation: Fix Missing Solicitud de Desembolso Template Record

**Date:** 2025-12-07
**Module:** Backend/Database
**Type:** Bug Fix
**Spec:** `specs/issue-0-adw-0-sdlc_planner-missing-solicitud-desembolso-template-record.md`

## Summary

Fixed the bug where Solicitud de Desembolso document generation failed with:
> "Error al generar solicitud: No active contract template found for type: pl_co_solicitud_desembolso"

The root cause was a missing database record in the `contract_templates` table for the `pl_co_solicitud_desembolso` contract type.

## Changes Made

### 1. Database Migration
**File:** `backend/database/migration_add_solicitud_desembolso_template.sql` (new)

Created a SQL migration to insert the template record:
```sql
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_solicitud_desembolso',
    '1.0.0',
    'FK COL - Fin. COP - Solicitud de Desembolso.docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;
```

### 2. Applied Migration
Applied the migration to Supabase database. Verified the record was created:
- **ID:** `2e0a3d89-a33d-4d58-a813-c13deb7a99ee`
- **contract_type:** `pl_co_solicitud_desembolso`
- **version:** `1.0.0`
- **template_content:** `FK COL - Fin. COP - Solicitud de Desembolso.docx`
- **active:** `true`

### 3. E2E Test Update
**File:** `.claude/commands/e2e/test_solicitud_desembolso_generation.md`

Updated the Bug Validation section to document this fix alongside the existing dict attribute error fix.

## Root Cause Analysis

The Solicitud de Desembolso feature implementation included:
- ✅ Word template file (`backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`)
- ✅ Contract type enum (`PL_CO_SOLICITUD_DESEMBOLSO` in `legal_dtos.py`)
- ✅ Contract ID prefix (PLSD) in database function
- ✅ Document generation method (`generate_solicitud_desembolso_document()`)
- ✅ Frontend form and API endpoints
- ❌ **Missing:** Database record in `contract_templates` table

The `ContractService.generate_contract()` method (line 74-76) requires an active template record in the database and throws an error when none is found.

## Files Changed

| File | Change |
|------|--------|
| `backend/database/migration_add_solicitud_desembolso_template.sql` | New - Database migration |
| `.claude/commands/e2e/test_solicitud_desembolso_generation.md` | Updated - Added bug documentation |

## Validation Results

| Check | Status |
|-------|--------|
| Backend tests (19 tests) | ✅ Passed |
| Backend linting (ruff) | ✅ Passed |
| Frontend linting (ESLint) | ✅ Passed |
| TypeScript type check | ✅ Passed |
| Frontend build | ✅ Passed |
| Database record exists | ✅ Verified |

## Testing

To manually verify the fix:
1. Login as Operations user
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click "Documentos Operación" → "Solicitud de Desembolso"
4. Search and select a client
5. Upload a Cotización PDF and extract data
6. Click "Solicitar Documento"
7. **Expected:** Success message with contract ID (PLSD-YYYY-XXX)
8. **Before fix:** Error "No active contract template found for type: pl_co_solicitud_desembolso"

## Notes

- No backend or frontend code changes were required
- The fix is purely a database data insertion
- The migration is idempotent (uses `ON CONFLICT DO NOTHING`)
- For production deployment, apply the migration SQL to the production Supabase database
