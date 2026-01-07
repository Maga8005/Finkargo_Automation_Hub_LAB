# PA Report Classification for Finance Module

**ADW ID:** 550a54d1
**Date:** 2025-12-29
**Specification:** specs/issue-53-adw-550a54d1-sdlc_planner-pa-report-classification.md

## Overview

This feature adds a comprehensive "Reporte PA" (Patrimonio Autónomo Report) capability to the Finance module. It enables Finance administrators to upload classification rules via Excel files and Finance users to process NetSuite movement files (~50k rows/month) through a two-step workflow that filters, cleans, and classifies PA account transactions.

## What Was Built

- **Database migrations** for PA classification tables (catalog, rules, history)
- **Finance Admin role** documentation and RBAC configuration
- **E2E test specification** for the PA Report Classification feature
- **Planning documentation** for full implementation

### Database Tables Created

1. **pa_account_catalog** - PA account mappings for filtering and homologation
2. **pa_classification_rules** - Main classification rules (tipo_transaccion + tipo_comprobante → categoria)
3. **pa_clasificacion_cuenta_rules** - Account name pattern → clasificacion rules
4. **pa_nexo_rules** - Account name pattern → nexo value rules
5. **pa_processing_history** - Tracks all PA report processing sessions

## Technical Implementation

### Files Modified

- `.claude/commands/bug.md`: Added conditional docs reference for PA feature
- `.claude/commands/chore.md`: Added conditional docs reference for PA feature
- `.claude/commands/feature.md`: Added conditional docs reference for PA feature
- `.claude/commands/e2e/test_pa_report_classification.md`: New E2E test specification
- `ai_docs/20251229_feature_pa_report_classification.md`: Feature planning document
- `backend/database/migration_pa_classification.sql`: Database migration for PA tables
- `backend/database/migration_add_finance_admin_role.sql`: Finance admin role documentation
- `specs/issue-53-adw-550a54d1-sdlc_planner-pa-report-classification.md`: Full specification

### Key Changes

- Created 5 database tables with proper indexes, RLS policies, and audit fields
- Added sequence generation for session IDs (format: PA-YYYYMMDD-HHMMSS-XXXX)
- Defined JSONB stats column for flexible processing statistics
- Established trigger functions for updated_at timestamps
- Documented finance_admin role for RBAC integration

### Database Migration Details

The migration creates:

```sql
-- Core tables
pa_account_catalog        -- cuenta_finkargo → cuenta_homologacion, nombre_homologacion
pa_classification_rules   -- tipo_transaccion + tipo_comprobante → categoria, subcategoria
pa_clasificacion_cuenta_rules  -- cuenta_nombre_patron → clasificacion
pa_nexo_rules             -- cuenta_nombre_patron → nexo
pa_processing_history     -- session tracking with JSONB stats
```

### Output Columns (8 new columns)

| Column | Source | Description |
|--------|--------|-------------|
| PA | Static | Always "X" for PA records |
| Categoria | Classification rules | Match tipo_transaccion + tipo_comprobante |
| Subcategoria | Rules + date logic | First-day-of-month special handling |
| Clasificacion | Account name rules | Pattern matching hierarchy |
| Nexo | Nexo rules | Values: "1", "2", "3", "4", "13" |
| Comprobacion saldos | Hardcoded accounts | "Cartera PA" for specific accounts |
| Cuenta Homologacion | Account catalog | Direct mapping |
| Nombre Homologacion | Account catalog | Direct mapping |

## How to Use

### Applying Database Migrations

1. Open Supabase SQL Editor
2. Execute `backend/database/migration_pa_classification.sql`
3. Execute `backend/database/migration_add_finance_admin_role.sql`
4. Verify tables were created:
   ```sql
   SELECT tablename FROM pg_tables
   WHERE tablename LIKE 'pa_%' ORDER BY tablename;
   ```

### Assigning Finance Admin Role

```sql
UPDATE user_profiles SET role = 'finance_admin' WHERE id = '<user_uuid>';
```

### Processing Workflow (Planned)

**Step 1 - Cleanup:**
1. Upload NetSuite Excel file
2. System filters to PA accounts only
3. Adds homologation columns
4. Validates balance (sum debito = sum credito)
5. Download cleaned file for review

**Step 2 - Classification:**
1. Apply all classification rules
2. Fill all 8 output columns
3. Download final classified file

## Configuration

### Access Control

| Feature | Required Roles |
|---------|----------------|
| Rules Management | `finance_admin`, `admin` |
| Report Processing | `finance`, `finance_admin`, `admin` |

### Backend RBAC

```python
# Rules endpoints
require_roles(['finance_admin'])

# Processing endpoints
require_roles(['finance', 'finance_admin'])
```

### Frontend Route Protection

```tsx
// Rules page
<RoleProtectedRoute allowedRoles={[UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>
  <ReglasClasificacionPA />
</RoleProtectedRoute>

// Processing page
<RoleProtectedRoute allowedRoles={[UserRole.FINANCE, UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>
  <ReportePA />
</RoleProtectedRoute>
```

## Testing

### E2E Test Execution

Run the E2E test specification:
```bash
# Read and execute the E2E test
# See: .claude/commands/e2e/test_pa_report_classification.md
```

### Expected Test Coverage

1. **Rules Upload**: Upload Excel files for each rule type
2. **Rules Viewing**: View current rules in tabular format
3. **File Processing**: Upload and process NetSuite files
4. **Balance Validation**: Verify sum(debito) = sum(credito)
5. **Classification**: Apply all rules correctly
6. **Download**: Download cleaned and classified files

## Notes

### Implementation Status

This documentation covers the **planning phase** of the PA Report Classification feature. The database migrations and specifications are complete. Full implementation of backend services, API routes, and frontend components is pending.

### Files Pending Implementation

**Backend:**
- `backend/src/interface/pa_dtos.py`
- `backend/src/repositorio/pa_rules_repository.py`
- `backend/src/core/servicios/pa_rules_service.py`
- `backend/src/core/servicios/pa_cleanup_service.py`
- `backend/src/core/servicios/pa_classification_engine.py`
- `backend/src/core/servicios/pa_report_service.py`
- `backend/src/adapter/rest/pa_routes.py`

**Frontend:**
- `frontend/src/types/financePA.ts`
- `frontend/src/services/financeServicePA.ts`
- `frontend/src/components/forms/FKPARulesUploader.tsx`
- `frontend/src/components/forms/FKPARulesViewer.tsx`
- `frontend/src/components/forms/FKPAFileUploader.tsx`
- `frontend/src/components/forms/FKPACleanedResults.tsx`
- `frontend/src/components/forms/FKPAClassifiedResults.tsx`
- `frontend/src/pages/finance/ReglasClasificacionPA.tsx`
- `frontend/src/pages/finance/ReportePA.tsx`

### Country Specificity

This feature is Colombia-specific. The architecture supports extension to other countries by adding country-specific rule tables and services.

### Performance Considerations

- Designed to handle ~50k rows within 2 minutes
- Consider Redis session storage for multi-instance deployment
- JSONB stats column provides flexibility for future metrics
