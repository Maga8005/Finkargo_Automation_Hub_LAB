# Feature: Individual Discrepancy Validation Checkboxes in Riesgos Module

## Feature Description
Add the ability for Mesa de Control analysts to validate individual discrepancies with specific reasons and comments. Currently, the Riesgos module only has a general confirmation checkbox for acknowledging discrepancies. This feature will enable analysts to validate each discrepancy individually, select from predefined validation reasons, add custom comments, and update the assessment status to "validated_by_mesa_control" when all discrepancies have been validated. The PDF report will also be updated to show "Validado por Mesa de Control" along with reasons and validator information.

## User Story
As a **Mesa de Control analyst (mesa_control role)**
I want to **validate individual discrepancies with specific reasons and add comments**
So that **I can document why each discrepancy was reviewed and approved, providing a proper audit trail for risk assessments**

## Problem Statement
Mesa de Control needs to validate discrepancies individually with specific reasons. Currently, only a general confirmation checkbox exists in the `FKVerificationStatusCard` component. This approach:
- Does not capture why a specific discrepancy was validated
- Provides no audit trail per discrepancy
- Does not support comments for explaining validation decisions
- Cannot track which discrepancies are still pending validation
- Does not update the assessment status based on validation completion

## Solution Statement
Implement a discrepancy validation system that:
1. **Per-Discrepancy Checkboxes**: Add a checkbox and validation controls next to each discrepancy in the `FKCrossValidationResults` component
2. **Validation Reason Dropdown**: Provide a dropdown with common reasons: "Validación manual", "Verificado por email", "Error de carga", "Justificación del cliente"
3. **Comments Field**: Add a text field for analyst comments per discrepancy
4. **Status Updates**: When all discrepancies are validated, update the assessment status to "validated_by_mesa_control"
5. **PDF Report Updates**: Show "Validado por Mesa de Control" in the PDF with reasons and validator info

## Access Control
- Required Role(s): `mesa_control`, `risk_manager`, `admin`
- Backend Protection: Use `require_roles(['mesa_control', 'risk_manager', 'admin'])` from `rbac_dependencies.py`
- Frontend Protection: Use `RoleProtectedRoute` with `allowedRoles={['mesa_control', 'risk_manager', 'admin']}`

## Relevant Files
Use these files to implement the feature:

### Backend Files
- `backend/src/adapter/rest/risk_routes.py` - Add new endpoints for discrepancy validation
- `backend/src/interface/risk_dtos.py` - Add DTOs for validation request/response
- `backend/src/repositorio/risk_repository.py` - Add methods to store/retrieve validation data
- `backend/src/core/servicios/risk/cross_validation_service.py` - Add business logic for validation

### Frontend Files
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Add individual checkboxes and validation UI per discrepancy
- `frontend/src/components/risk/FKVerificationStatusCard.tsx` - Update to show validation progress
- `frontend/src/types/risk.ts` - Add TypeScript types for validation
- `frontend/src/services/riskService.ts` - Add API methods for validation
- `frontend/src/utils/crossValidationPdfExport.ts` - Update PDF to show validation info

### Database
- `backend/database/migration_add_discrepancy_validations.sql` - New table for validation records

### E2E Test Reference
- `.claude/commands/test_e2e.md` - Understand E2E test format
- `.claude/commands/e2e/test_risk_dashboard.md` - Example E2E test for risk module

### New Files
- `backend/database/migration_add_discrepancy_validations.sql` - Database migration for validation table and status enum update
- `frontend/src/components/risk/FKDiscrepancyValidationItem.tsx` - Component for individual discrepancy validation row
- `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md` - E2E test file for this feature

## Pre-Implementation Verification

### Feature Category
- [x] CRUD Operations (basic data management) → Complete sections D, E
- [x] Reporting (queries, history) → Complete sections D, G (PDF report updates)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| CrossValidationRepository.get_by_assessment() | List[dict] | data['is_discrepancy'] | Returns list of dicts |
| RiskAssessmentRepository.get_by_id() | dict | data['status'] | Returns single dict |
| RiskAssessmentRepository.update() | dict | data['status'] | Returns updated dict |
| DiscrepancyValidationRepository.create() | dict | data['id'] | New - returns created record |
| DiscrepancyValidationRepository.get_by_assessment() | List[dict] | data['validation_reason'] | New - returns list of validations |
| DiscrepancyValidationRepository.get_by_discrepancy() | dict | data['validated_by'] | New - returns single validation |

### E. Database Dependencies Checklist
- [ ] Required enums exist in DTOs (or will be added) - **Will add `DiscrepancyValidationReason` enum**
- [ ] Template file exists in `backend/templates/` (if applicable) - **N/A**
- [ ] Database records exist (or migration created) - **Migration will be created**
- [ ] Country-specific data handled (CO vs MX) - **N/A - validation is country-agnostic**

### G. Query Specification (Reporting only)

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| assessment_id | UUID | Yes | N/A |
| discrepancy_id | UUID | No | N/A |
| validated_by | UUID | No | N/A |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| discrepancy_id | discrepancy_id | string (UUID) | Cross-validation result ID |
| validation_reason | validation_reason | string (enum) | One of: manually_validated, email_verified, upload_error, client_justification |
| comments | comments | string | Analyst's notes, max 2000 chars |
| validated_by | validated_by | string (UUID) | User ID who validated |
| validated_at | validated_at | string (ISO date) | Timestamp of validation |
| is_validated | is_validated | boolean | Whether this discrepancy is validated |

## Implementation Plan

### Phase 1: Foundation
1. Create database migration for `discrepancy_validations` table
2. Add new DTOs for validation request/response in `risk_dtos.py`
3. Add validation reason enum to DTOs
4. Create repository methods for validation CRUD
5. Add TypeScript types in `risk.ts`

### Phase 2: Core Implementation
1. Create backend endpoints for:
   - `POST /api/risk/evaluations/{id}/discrepancies/{discrepancy_id}/validate` - Validate single discrepancy
   - `GET /api/risk/evaluations/{id}/discrepancies/validations` - Get all validations for assessment
   - `DELETE /api/risk/evaluations/{id}/discrepancies/{discrepancy_id}/validate` - Remove validation
2. Add service layer logic to check if all discrepancies validated and update status
3. Create `FKDiscrepancyValidationItem` component for per-discrepancy validation UI
4. Update `FKCrossValidationResults` to include validation controls
5. Add API methods to `riskService.ts`

### Phase 3: Integration
1. Update `FKVerificationStatusCard` to show validation progress (e.g., "3/5 validated")
2. Update PDF export to include validation info section
3. Add "Validado por Mesa de Control" section with reasons and validator info
4. Connect status update logic when all discrepancies validated

## Step by Step Tasks

### Task 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_risk_dashboard.md` to understand E2E test format
- Create `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md` with test steps for:
  - Login as mesa_control role user
  - Navigate to risk evaluation with discrepancies
  - Validate individual discrepancy with reason dropdown and comments
  - Verify validation is saved and displayed
  - Validate all discrepancies and verify status updates to "validated_by_mesa_control"
  - Export PDF and verify validation info appears

### Task 2: Create Database Migration
- Create `backend/database/migration_add_discrepancy_validations.sql`
- Add `discrepancy_validations` table with columns:
  - `id` UUID PRIMARY KEY
  - `assessment_id` UUID (FK to risk_assessments)
  - `cross_validation_result_id` UUID (FK to risk_cross_validation_results)
  - `validation_reason` VARCHAR with CHECK constraint for enum values
  - `comments` TEXT (max 2000 chars)
  - `validated_by` UUID (FK to user_profiles)
  - `validated_at` TIMESTAMP
  - `created_at` TIMESTAMP
- Update `risk_assessments.status` CHECK constraint to include 'validated_by_mesa_control'
- Add RLS policies for mesa_control, risk_manager, admin roles
- Add indexes for efficient lookups

### Task 3: Add Backend DTOs
- Add to `backend/src/interface/risk_dtos.py`:
  - `DiscrepancyValidationReason` enum with values: MANUALLY_VALIDATED, EMAIL_VERIFIED, UPLOAD_ERROR, CLIENT_JUSTIFICATION
  - `DiscrepancyValidationRequest` with: validation_reason, comments (optional)
  - `DiscrepancyValidationResponse` with: id, assessment_id, cross_validation_result_id, validation_reason, comments, validated_by, validated_by_name, validated_at
  - `DiscrepancyValidationsListResponse` with: assessment_id, total_discrepancies, validated_count, pending_count, validations list
- Update `AssessmentStatus` enum to include VALIDATED_BY_MESA_CONTROL = "validated_by_mesa_control"

### Task 4: Create Repository Methods
- Add `DiscrepancyValidationRepository` class to `backend/src/repositorio/risk_repository.py`:
  - `async def create(self, data: dict) -> dict` - Create validation record
  - `async def get_by_assessment(self, assessment_id: str) -> List[dict]` - Get all validations for assessment
  - `async def get_by_discrepancy(self, assessment_id: str, discrepancy_id: str) -> Optional[dict]` - Get validation for specific discrepancy
  - `async def delete(self, assessment_id: str, discrepancy_id: str) -> bool` - Remove validation

### Task 5: Create Backend API Endpoints
- Add to `backend/src/adapter/rest/risk_routes.py`:
  - `POST /api/risk/evaluations/{id}/discrepancies/{discrepancy_id}/validate` endpoint
    - Validate discrepancy exists in assessment's cross-validation results
    - Create validation record with user info and timestamp
    - Check if all discrepancies now validated → update status to validated_by_mesa_control
    - Return validation response
  - `GET /api/risk/evaluations/{id}/discrepancies/validations` endpoint
    - Return all validations with counts (total, validated, pending)
  - `DELETE /api/risk/evaluations/{id}/discrepancies/{discrepancy_id}/validate` endpoint
    - Remove validation
    - If status was validated_by_mesa_control, revert to previous status

### Task 6: Add Frontend TypeScript Types
- Add to `frontend/src/types/risk.ts`:
  - `DiscrepancyValidationReason` type union: 'manually_validated' | 'email_verified' | 'upload_error' | 'client_justification'
  - `DiscrepancyValidation` interface with all validation fields
  - `DiscrepancyValidationsListResponse` interface
  - `DISCREPANCY_VALIDATION_REASON_LABELS` config object with Spanish labels:
    - manually_validated: 'Validación manual'
    - email_verified: 'Verificado por email'
    - upload_error: 'Error de carga'
    - client_justification: 'Justificación del cliente'

### Task 7: Add Frontend API Methods
- Add to `frontend/src/services/riskService.ts`:
  - `validateDiscrepancy(assessmentId: string, discrepancyId: string, data: { validation_reason: string, comments?: string }): Promise<DiscrepancyValidation>`
  - `getDiscrepancyValidations(assessmentId: string): Promise<DiscrepancyValidationsListResponse>`
  - `removeDiscrepancyValidation(assessmentId: string, discrepancyId: string): Promise<void>`

### Task 8: Create FKDiscrepancyValidationItem Component
- Create `frontend/src/components/risk/FKDiscrepancyValidationItem.tsx`:
  - Props: discrepancy (CrossValidationResult), validation (optional DiscrepancyValidation), onValidate, onRemoveValidation, canValidate
  - Display discrepancy info (type, severity, description)
  - Checkbox to toggle validation
  - When checkbox checked:
    - Show dropdown with validation reasons (use DISCREPANCY_VALIDATION_REASON_LABELS)
    - Show TextField for comments (multiline, max 2000 chars)
    - Show "Guardar" button to submit validation
  - When validated:
    - Show green checkmark
    - Show validation reason label
    - Show validator name and timestamp
    - Show "Quitar validación" button (if user has permission)

### Task 9: Update FKCrossValidationResults Component
- Modify `frontend/src/components/risk/FKCrossValidationResults.tsx`:
  - Add state for validations data: `useState<DiscrepancyValidation[]>`
  - Fetch validations when component mounts: call `riskService.getDiscrepancyValidations`
  - Add prop to enable/disable validation mode (based on user role)
  - In `renderResult` function:
    - Replace existing result rendering with `FKDiscrepancyValidationItem` component
    - Pass discrepancy data and matching validation (if exists)
    - Pass validation handlers
  - Add validation progress summary at top: "Validados: X/Y discrepancias"
  - When all discrepancies validated, show success banner

### Task 10: Update FKVerificationStatusCard Component
- Modify `frontend/src/components/risk/FKVerificationStatusCard.tsx`:
  - Add new props: `validationProgress?: { validated: number, total: number }`
  - Show validation progress when available: "Validados: 3/5"
  - When all validated, show "VALIDADO POR MESA DE CONTROL" status with green styling
  - Update acknowledgment section to only show when not all validated

### Task 11: Update PDF Export Utility
- Modify `frontend/src/utils/crossValidationPdfExport.ts`:
  - Add optional `validations` parameter to export functions
  - Add new section in PDF: "Validaciones de Mesa de Control"
  - For each validated discrepancy, show:
    - Discrepancy type and field
    - Validation reason (Spanish label)
    - Comments (if present)
    - Validator name and timestamp
  - Add header text "Validado por Mesa de Control" when all validated
  - Style validated items with green background

### Task 12: Apply Database Migration
- Apply migration to local database for testing
- Document migration application in Notes section

### Task 13: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Backend: Test validation repository methods with pytest
- Backend: Test validation endpoints return correct responses
- Backend: Test status update logic when all discrepancies validated
- Backend: Test role-based access control for validation endpoints

### Edge Cases
- Validating a discrepancy that doesn't exist → Return 404
- Validating same discrepancy twice → Return existing validation or 409 conflict
- Removing validation from already-removed discrepancy → Return 404
- Attempting to validate without required role → Return 403
- Validation with empty comments (allowed) → Success
- Validation with comments exceeding 2000 chars → Validation error
- Validating last discrepancy triggers status update → Verify status changes
- Removing validation after all validated reverts status → Verify status changes back

## Acceptance Criteria
1. Individual checkboxes appear next to each discrepancy in the cross-validation results
2. Checking a checkbox reveals a dropdown with validation reasons and a comments field
3. Validation reasons include: "Validación manual", "Verificado por email", "Error de carga", "Justificación del cliente"
4. Analysts can add optional comments (up to 2000 characters)
5. When all discrepancies are validated, status updates to "validated_by_mesa_control"
6. PDF report shows "Validado por Mesa de Control" section with reasons and validator info
7. Only mesa_control, risk_manager, and admin roles can validate discrepancies
8. Validation records include timestamp and validator user ID
9. Validation progress is visible (e.g., "3/5 validated")
10. Validations can be removed, reverting status if needed

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md` E2E test file to validate this functionality works
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

### Database Migration Application
To apply the migration:
```bash
# Via Supabase SQL Editor
# 1. Open Supabase dashboard
# 2. Navigate to SQL Editor
# 3. Paste contents of migration_add_discrepancy_validations.sql
# 4. Execute
```

### Validation Reason Enum Values
The validation reasons are stored as snake_case values in the database:
- `manually_validated` - Analyst manually verified the data
- `email_verified` - Confirmation received via email
- `upload_error` - Discrepancy was due to upload/OCR error
- `client_justification` - Client provided acceptable explanation

### Status Flow
Current status flow for risk assessments:
```
pending → pending_documents → pending_finalization → completed/approved/rejected
```

New status addition:
```
pending_finalization → validated_by_mesa_control → approved/rejected
```

The `validated_by_mesa_control` status indicates Mesa de Control has reviewed and validated all discrepancies, but final approval/rejection still pending from risk_manager.

### UI/UX Considerations
- Validation controls should be visually distinct but not overwhelming
- Progress indicator helps users track validation status
- Validated items should be clearly marked with checkmark and green styling
- Comments field should be collapsible to save space

## Plan Quality Checklist

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes - **No new dependencies needed**

### Category-Specific Completeness
**CRUD Operations:**
- [x] Repository methods documented with return types
- [x] Access patterns verified for dict vs object
- [x] Validation rules specified (2000 char limit on comments)
- [x] Role-based access control defined

**Reporting:**
- [x] PDF export updates documented
- [x] Validation info section specified

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable - **N/A**

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
