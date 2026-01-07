# External Communication Validation Comments

**ADW ID:** 584b6bdd
**Date:** 2026-01-01
**Specification:** specs/issue-65-adw-584b6bdd-sdlc_planner-external-communication-validation-comments.md

## Overview

This feature extends the discrepancy validation functionality to the "Comunicacion Externa" (External Communication) page alerts in the Riesgos module. Mesa de Control analysts can now validate individual email chain discrepancies and external contact alerts with specific reasons and optional comments, creating a proper audit trail for risk assessments.

## What Was Built

- **Email Chain Discrepancy Validation**: Ability to validate individual discrepancies found in email chain analysis (domain mismatches, typosquatting, etc.)
- **External Contact Alert Validation**: Ability to validate suspicious/critical external contact alerts
- **Validation Progress Tracking**: Visual progress indicators showing validated vs total alerts
- **PDF Export Integration**: Validation data included in comprehensive evaluation reports
- **Role-Based Access Control**: Only authorized roles (mesa_control, risk_manager, admin) can perform validations

## Technical Implementation

### Files Modified

- `backend/src/adapter/rest/risk_routes.py`: Added 6 new API endpoints for validation CRUD operations
- `backend/src/interface/risk_dtos.py`: Added DTOs for email chain and external contact validations
- `backend/src/repositorio/risk_repository.py`: Added repository classes for validation data access
- `frontend/src/components/risk/FKEmailChainUploader.tsx`: Integrated validation controls into email chain display
- `frontend/src/components/risk/FKExternalContactTab.tsx`: Integrated validation controls into external contacts
- `frontend/src/services/riskService.ts`: Added API service methods for validation operations
- `frontend/src/types/risk.ts`: Added TypeScript interfaces for validation types
- `frontend/src/utils/crossValidationPdfExport.ts`: Extended PDF export to include validation data

### New Files Created

- `backend/database/migration_add_external_communication_validations.sql`: Database migration for validation tables
- `frontend/src/components/risk/FKEmailChainValidationItem.tsx`: UI component for email chain discrepancy validation
- `frontend/src/components/risk/FKExternalContactValidationItem.tsx`: UI component for external contact validation
- `.claude/commands/e2e/test_RiskModule_external_communication_validation_comments.md`: E2E test specification

### Key Changes

- Created two new database tables: `email_chain_discrepancy_validations` and `external_contact_validations` with RLS policies
- Implemented CRUD endpoints following the pattern from discrepancy validations (issue #63)
- Added validation reason dropdown with four options: manual validation, email verification, loading error, client justification
- Integrated validation progress counters showing "X/Y validated" in component headers
- Extended PDF export to include validation status and comments columns for external communication alerts

## How to Use

1. Navigate to a risk evaluation's "Comunicacion Externa" tab
2. View email chains with discrepancies or external contacts with suspicious/critical status
3. Click on an unvalidated alert item to expand the validation form
4. Select a validation reason from the dropdown
5. Optionally add comments explaining the validation decision (up to 2000 characters)
6. Click "Validar" to save the validation
7. To remove a validation, expand a validated item and click "Quitar Validacion"
8. Export the comprehensive evaluation PDF to include validation data

## Configuration

No additional configuration required. The feature uses existing role-based access control:
- **View validations**: risk_analyst, risk_manager, admin, mesa_control
- **Create/update/delete validations**: risk_manager, admin, mesa_control

## Testing

1. Run the database migration: `backend/database/migration_add_external_communication_validations.sql`
2. Backend tests: `cd backend && python -m pytest`
3. Backend linting: `cd backend && ruff check src/`
4. Frontend linting: `cd frontend && npm run lint`
5. TypeScript check: `cd frontend && npx tsc --noEmit`
6. Frontend build: `cd frontend && npm run build`
7. E2E test: Execute `.claude/commands/e2e/test_RiskModule_external_communication_validation_comments.md`

## Notes

- The validation reason enum reuses `DiscrepancyValidationReason` from issue #63 for consistency
- Email chain discrepancies are indexed by their position in the `validation_result.discrepancies` array
- External contacts use their existing UUIDs as references
- Validation UI only appears for alerts requiring attention (suspicious/critical status)
- The PDF export dynamically adjusts column widths when validation data is present
