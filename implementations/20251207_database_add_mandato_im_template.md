# Implementation: Add Instrucción de Mandato Contract Template Database Record

**Date:** 2025-12-07
**Module:** Database / Operations
**Issue:** Missing contract_templates record for pl_co_mandato_im

## Summary

Created a SQL migration to add the missing `contract_templates` database record for the `pl_co_mandato_im` (Instrucción de Mandato) contract type. This fixes the bug where document generation fails with "No active contract template found for type: pl_co_mandato_im".

## Work Completed

- **Verified template file exists**: Confirmed `FK COL - Fin. COP - Mandato (IM).docx` exists in `backend/templates/`
- **Reviewed reference migration pattern**: Used `migration_add_solicitud_desembolso_template.sql` as reference
- **Created migration file**: `backend/database/migration_add_instruccion_mandato_template.sql`
  - Inserts template record with `contract_type = 'pl_co_mandato_im'`
  - Sets `template_content = 'FK COL - Fin. COP - Mandato (IM).docx'`
  - Sets `active = true` and `version = '1.0.0'`
  - Uses `ON CONFLICT DO NOTHING` to prevent duplicate insertion
  - Includes verification SELECT query

## Discrepancies Found

**None.** The plan accurately described the issue:
- Template file exists at expected location
- Reference migration pattern matches expected format
- No code changes were required - purely database migration

## Validation Results

| Check | Result |
|-------|--------|
| Backend linting (`ruff check src/`) | ✅ All checks passed |
| Backend tests (`pytest`) | ✅ 48 passed, 31 warnings (deprecation) |
| Frontend linting (`npm run lint`) | ✅ Passed |
| TypeScript check (`tsc --noEmit`) | ✅ No errors |
| Frontend build (`npm run build`) | ✅ Built in 5.74s |

## Files Changed

```
backend/database/migration_add_instruccion_mandato_template.sql | 37 lines (new file)
```

## Migration SQL

```sql
INSERT INTO contract_templates (
    contract_type,
    version,
    template_content,
    active,
    created_at
) VALUES (
    'pl_co_mandato_im',
    '1.0.0',
    'FK COL - Fin. COP - Mandato (IM).docx',
    true,
    NOW()
) ON CONFLICT (contract_type, version) DO NOTHING;
```

## Post-Implementation Steps

1. **Apply the migration** to the database via Supabase Dashboard SQL Editor or psql
2. **Verify the record was created** with:
   ```sql
   SELECT * FROM contract_templates WHERE contract_type = 'pl_co_mandato_im';
   ```
3. **Test the feature** by navigating to Paga Local Colombia → Documentos Operación → Mandato (IM) and generating a document

## Related Files

- **Migration created**: `backend/database/migration_add_instruccion_mandato_template.sql`
- **Template file**: `backend/templates/FK COL - Fin. COP - Mandato (IM).docx`
- **Spec file**: `specs/issue-69-adw-a62436e0-sdlc_planner-add-mandato-im-template.md`

## Notes

This is a database-only fix. The following components were already correctly implemented:
- API endpoint: `POST /api/operations/contracts/instruccion-mandato/generate`
- Document service: `generate_instruccion_mandato_document()` method
- Frontend form: `FKInstruccionMandatoForm.tsx`
- Contract ID prefix: `PLMI` for `pl_co_mandato_im`
