# Implementation Report: DIAN Mandato (IM) Contract Generation

**Date:** 2025-12-07
**Module:** Operations - Paga Local Colombia
**Feature:** DIAN Mandato (IM) Document Generation

## Summary

Implemented the DIAN Mandato (IM) contract generation feature for Paga Local Colombia operations. This enables operations users to generate "Template DIAN - Mandato (IM)" documents for DIAN (tax authority) payments. Unlike the regular Mandato (IM) which requires Bank Certificate PDFs for each creditor, the DIAN Mandato uses only the Cotización PDF plus client data from the database.

## Work Completed

### Backend Changes

- **DTO Addition** (`backend/src/interface/legal_dtos.py`)
  - Added `DIANMandatoRequest` Pydantic model with validation
  - Fields: `client_nit`, `numero_cotizacion_desembolso`, `fecha_contrato_mandato`, `monto`
  - No `acreedores` field (key difference from regular Mandato)

- **Document Service** (`backend/src/core/servicios/document_service.py`)
  - Added routing case for `pl_co_dian_mandato_im` contract type
  - Created `generate_dian_mandato_document()` method
  - Reuses `_prepare_instruccion_mandato_replacements()` for placeholder mapping
  - Template: `FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx`
  - No creditor table population needed (DIAN template is simpler)

- **API Endpoints** (`backend/src/adapter/rest/operations_routes.py`)
  - `POST /api/operations/contracts/dian-mandato/parse-cotizacion` - Parse Cotización PDF
  - `POST /api/operations/contracts/dian-mandato/generate` - Generate DIAN Mandato contract
  - Both protected with `require_operations_role` RBAC

- **Database Migration** (`backend/database/migration_add_dian_mandato_im_template.sql`)
  - Creates template record for `pl_co_dian_mandato_im` in `contract_templates` table
  - Must be run manually in Supabase SQL Editor

### Frontend Changes

- **TypeScript Types** (`frontend/src/types/legal.ts`)
  - Added `DIANMandatoRequest` interface

- **Service Methods** (`frontend/src/services/operationsService.ts`)
  - Added `parseCotizacionForDIANMandato(file)` method
  - Added `generateDIANMandato(request)` method

- **Form Component** (`frontend/src/components/forms/FKDIANMandatoForm.tsx`)
  - New simplified form with 4 sections:
    1. Client Search (by NIT or name)
    2. Cotización PDF Upload & Extraction
    3. Data Review (quote number, date, amount)
    4. Generate Document
  - NO Bank Certificate upload section
  - Info alert explaining this is for DIAN payments

- **Parent Component** (`frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`)
  - Updated to use `FKDIANMandatoForm` for the DIAN Mandato tab

### E2E Test

- **Test File** (`.claude/commands/e2e/test_dian_mandato_im_form.md`)
  - Comprehensive test steps for the DIAN Mandato workflow
  - Screenshots at each step
  - Success criteria verification
  - Key difference documentation vs regular Mandato

## Discrepancies Found

**None.** The plan was accurate:
- Template placeholders matched exactly (9 placeholders, no creditor table)
- Contract type enum already existed in DTOs
- Contract ID prefix `PLDI` already configured in database function
- Only missing item was the template record, which was addressed by migration

## Template Placeholders Mapped

| Placeholder | Data Source | Format |
|-------------|-------------|--------|
| `[Fecha actual]` | System datetime | "DD de MONTH de YYYY" (Spanish) |
| `[Número de cotización de desembolso]` | Cotización PDF | String |
| `[día de firma contrato mandato]` | Cotización PDF | Integer |
| `[mes de firma contrato mandato]` | Cotización PDF | Spanish month name |
| `[año de firma contrato mandato]` | Cotización PDF | Integer |
| `[monto a transferir en letras]` | Cotización PDF | Spanish words uppercase |
| `[monto a transferir en números]` | Cotización PDF | "$739,860" format |
| `[Nombre del representante legal del Cliente]` | Database | String |
| `[número ID representante legal]` | Database | String |

## Files Changed

```
 backend/src/adapter/rest/operations_routes.py      | 160 ++++++++++++++
 backend/src/core/servicios/document_service.py     |  73 +++++++
 backend/src/interface/legal_dtos.py                |  22 +++
 frontend/src/components/forms/FKDIANMandatoForm.tsx| 395 (new)
 frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx | 5 +-
 frontend/src/services/operationsService.ts         |  33 ++++
 frontend/src/types/legal.ts                        |   8 ++
```

**New Files:**
- `backend/database/migration_add_dian_mandato_im_template.sql`
- `frontend/src/components/forms/FKDIANMandatoForm.tsx`
- `.claude/commands/e2e/test_dian_mandato_im_form.md`
- `specs/issue-0-adw-0-sdlc_planner-implement-dian-mandato-im-generation.md`

**Total Lines Changed:** ~700 (including new files)

## Validation Results

| Check | Status |
|-------|--------|
| Backend Linting (`ruff check src/`) | ✅ All checks passed |
| Frontend Linting (`npm run lint`) | ✅ No errors |
| TypeScript (`npm run build`) | ✅ Build successful |
| Backend Tests (`pytest`) | ✅ 48 tests passed |

## Key Differences from Regular Mandato (IM)

| Aspect | Regular Mandato (IM) | DIAN Mandato (IM) |
|--------|---------------------|-------------------|
| Contract Type | `pl_co_mandato_im` | `pl_co_dian_mandato_im` |
| Contract ID Prefix | `PLMI-` | `PLDI-` |
| Template | `FK COL - Fin. COP - Mandato (IM).docx` | `FK COL - Fin. COP - Template DIAN -  Mandato (IM).docx` |
| Bank Certificate | Required (1-3 per doc) | NOT required |
| Creditor Table | Populated with bank info | No creditor table |
| API Endpoint | `/contracts/instruccion-mandato/generate` | `/contracts/dian-mandato/generate` |

## Post-Implementation Steps Required

1. **Run Database Migration:**
   - Open Supabase Dashboard → SQL Editor
   - Execute `backend/database/migration_add_dian_mandato_im_template.sql`
   - Verify with: `SELECT * FROM contract_templates WHERE contract_type = 'pl_co_dian_mandato_im';`

2. **Manual Testing:**
   - Navigate to Operations → Paga Local Colombia → Documentos de Operación → DIAN Mandato (IM)
   - Upload a Cotización PDF
   - Generate a test document
   - Verify contract ID starts with `PLDI-`

## Notes

- The DIAN template is simpler than the regular Mandato template - no nested creditor table
- Same Cotización parser is reused from regular Mandato workflow
- The form explicitly informs users that no bank certificates are needed for DIAN payments
