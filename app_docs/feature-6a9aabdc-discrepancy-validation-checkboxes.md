# Individual Discrepancy Validation Checkboxes

**ADW ID:** 6a9aabdc
**Date:** 2025-12-31
**Specification:** specs/issue-63-adw-6a9aabdc-sdlc_planner-discrepancy-validation-checkboxes.md

## Overview

This feature enables Mesa de Control analysts to validate individual discrepancies in the Riesgos module with specific reasons and comments. Previously, only a general confirmation checkbox existed. Now analysts can validate each discrepancy individually, select from predefined validation reasons, add custom comments, and track validation progress. The PDF report also displays validation information.

## What Was Built

- Per-discrepancy validation UI component (`FKDiscrepancyValidationItem`)
- Backend API endpoints for discrepancy validation CRUD operations
- Database table `discrepancy_validations` to persist validation records
- TypeScript types for discrepancy validation workflow
- PDF export updates to show validation status and details
- Validation progress tracking in the verification status card

## Technical Implementation

### Files Modified

- `frontend/src/components/risk/FKCrossValidationResults.tsx`: Integrated validation UI, fetches validations, displays progress summary
- `frontend/src/components/risk/FKVerificationStatusCard.tsx`: Added validation progress display (e.g., "Validados: 3/5")
- `frontend/src/types/risk.ts`: Added `DiscrepancyValidation`, `DiscrepancyValidationReason`, `DiscrepancyValidationProgress`, and related types/configs
- `frontend/src/services/riskService.ts`: Added API methods for validation operations
- `frontend/src/utils/crossValidationPdfExport.ts`: Added validation status column and "Validado por Mesa de Control" banner
- `backend/src/adapter/rest/risk_routes.py`: Added validation endpoints
- `backend/src/interface/risk_dtos.py`: Added validation DTOs
- `backend/src/repositorio/risk_repository.py`: Added `DiscrepancyValidationRepository` class

### New Files

- `frontend/src/components/risk/FKDiscrepancyValidationItem.tsx`: Individual discrepancy row with validation controls
- `backend/database/migration_add_discrepancy_validations.sql`: Database migration for validation table
- `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md`: E2E test specification

### Key Changes

- **Database schema**: New `discrepancy_validations` table with foreign key to `cross_validation_results`, validation reason enum, comments field, and audit trail (validated_by, validated_at)
- **Backend API**: Three new endpoints for validation CRUD:
  - `GET /api/risk/evaluations/{id}/discrepancies-with-validations` - Get discrepancies with validation state
  - `PUT /api/risk/evaluations/{id}/discrepancy-validations/{resultId}` - Validate/update discrepancy
  - `DELETE /api/risk/evaluations/{id}/discrepancy-validations/{resultId}` - Remove validation
- **Frontend component**: `FKDiscrepancyValidationItem` displays discrepancy info with expandable validation form including reason dropdown and comments field
- **Validation reasons**: Four predefined reasons - "Validación manual", "Verificado por email", "Error de carga", "Justificación del cliente"
- **PDF export**: Displays validation status per discrepancy and shows green banner "VALIDADO POR MESA DE CONTROL" when all discrepancies are validated

## How to Use

1. Navigate to a risk evaluation with discrepancies in the Riesgos module
2. In the Cross Validation Results section, each discrepancy displays with a warning icon if not validated
3. Click on a discrepancy row to expand the validation form
4. Select a validation reason from the dropdown (required)
5. Optionally add comments (up to 2000 characters)
6. Click "Guardar Validación" to save
7. Validated discrepancies display with a green checkmark and validation details
8. Progress is shown as "Validados: X/Y" in the verification status card
9. When exporting to PDF, validation status appears in the discrepancy table

## Configuration

- **Role-based access**: Only `mesa_control`, `risk_manager`, and `admin` roles can validate discrepancies
- **Comments limit**: Maximum 2000 characters per validation comment
- **Validation reasons** (stored as snake_case in database):
  - `manual_validation` - Validación manual
  - `email_verification` - Verificado por email
  - `loading_error` - Error de carga
  - `client_justification` - Justificación del cliente

## Testing

- E2E test specification: `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md`
- Backend tests via `pytest` for validation repository and endpoints
- Frontend type checking via `npx tsc --noEmit`
- Linting via `npm run lint` (frontend) and `ruff check src/` (backend)

## Notes

- The `discrepancy_validations` table uses Row Level Security (RLS) for access control
- Validations are linked to `cross_validation_result_id` with a unique constraint (one validation per discrepancy)
- Removing a validation is possible if the user has the appropriate role
- The assessment status can be updated to `validated_by_mesa_control` when all discrepancies are validated (workflow integration pending)
