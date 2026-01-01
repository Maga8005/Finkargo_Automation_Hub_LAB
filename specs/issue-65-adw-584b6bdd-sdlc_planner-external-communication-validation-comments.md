# Feature: External Communication Validation Comments

## Feature Description
This feature extends the discrepancy validation functionality from issue 63 to the "Comunicación Externa" (External Communication) page alerts in the Riesgos module. Mesa de Control analysts will be able to validate alerts raised from email chain analysis and external contact validations, selecting validation reasons from a dropdown and providing comments. This validation data will be persisted and included in the evaluation report (reporte_evaluación) generated from the Evaluación page.

## User Story
As a Mesa de Control analyst (mesa_control role)
I want to validate individual alerts from the external communication page with specific reasons and comments
So that I can document my review of email domain discrepancies, typosquatting alerts, and company name mismatches, providing a proper audit trail for risk assessments

## Problem Statement
The external communication page displays alerts when email chains or external contacts reveal:
- Mismatched email domains (potential typosquatting)
- Domain existence issues
- Domain age concerns (recently created domains)
- Company name discrepancies
- Other fraud indicators

Currently, these alerts cannot be validated with reasons and comments like the cross-validation discrepancies (from issue 63). This creates an incomplete audit trail and prevents Mesa de Control analysts from documenting their review decisions for external communication alerts.

## Solution Statement
Implement validation controls for external communication alerts following the same pattern as issue 63's discrepancy validation:

1. **Database**: Create new tables to store external contact validations and email chain discrepancy validations
2. **Backend**: Add API endpoints for CRUD operations on these validations
3. **Frontend**: Extend the FKEmailChainUploader and FKExternalContactTab components to display validation controls for each alert
4. **PDF Export**: Extend the comprehensive evaluation report to include external communication validation data

## Access Control
- Required Role(s): `mesa_control`, `risk_manager`, `admin`
- Backend Protection: Use `require_roles(['mesa_control', 'risk_manager', 'admin'])` from rbac_dependencies
- Frontend Protection: Check user roles before rendering validation controls, disable controls for unauthorized users

## Relevant Files
Use these files to implement the feature:

**Documentation to read:**
- `app_docs/feature-6a9aabdc-discrepancy-validation-checkboxes.md` - Reference implementation pattern from issue 63
- `.claude/commands/test_e2e.md` - Understand E2E test execution patterns
- `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md` - Reference E2E test structure

**Backend Files:**
- `backend/src/adapter/rest/risk_routes.py` - Add new API endpoints for external communication validations (lines 1681-2100 contain existing external contact and email chain endpoints)
- `backend/src/interface/risk_dtos.py` - Add DTOs for external communication validation requests/responses
- `backend/src/repositorio/risk_repository.py` - Add validation repository classes (follow DiscrepancyValidationRepository pattern at line 1135)
- `backend/database/migration_add_discrepancy_validations.sql` - Reference for database migration pattern

**Frontend Files:**
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Add validation controls to email chain discrepancy items
- `frontend/src/components/risk/FKExternalContactTab.tsx` - Add validation controls to external contact alerts
- `frontend/src/components/risk/FKDiscrepancyValidationItem.tsx` - Reference UI pattern for validation controls
- `frontend/src/types/risk.ts` - Add TypeScript types for external communication validations
- `frontend/src/services/riskService.ts` - Add API methods for validation CRUD
- `frontend/src/utils/crossValidationPdfExport.ts` - Extend PDF export to include external communication validations

### New Files
- `backend/database/migration_add_external_communication_validations.sql` - Database migration for validation tables
- `frontend/src/components/risk/FKEmailChainValidationItem.tsx` - UI component for email chain discrepancy validation
- `frontend/src/components/risk/FKExternalContactValidationItem.tsx` - UI component for external contact validation
- `.claude/commands/e2e/test_external_communication_validation_comments.md` - E2E test specification

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| EmailChainValidationRepo.get_by_email_chain() | dict | data['id'] | Not data.id |
| EmailChainValidationRepo.get_by_assessment() | List[dict] | data[0]['email_chain_id'] | Loop through list |
| ExternalContactValidationRepo.get_by_contact() | dict | data['id'] | Not data.id |
| ExternalContactValidationRepo.get_by_assessment() | List[dict] | data[0]['external_contact_id'] | Loop through list |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (use same `DiscrepancyValidationReason` enum from issue 63)
- [ ] Database migration needs to be created for validation tables
- [ ] RLS policies need to be added for new tables

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| is_validated | is_validated | boolean | Validation state |
| validation_reason | validation_reason | string (enum) | Uses same DiscrepancyValidationReason |
| comments | comments | string | Max 2000 chars |
| validated_by | validated_by | string (UUID) | User ID reference |
| validated_by_name | validated_by_name | string | Resolved from user_profiles |
| validated_at | validated_at | string (ISO datetime) | Timestamp |

## Implementation Plan

### Phase 1: Foundation
1. **Database Migration**: Create tables for `email_chain_discrepancy_validations` and `external_contact_validations`
   - Mirror structure from `discrepancy_validations` table
   - Add foreign keys to email_chains and external_contacts tables
   - Enable RLS with appropriate policies

2. **Backend DTOs**: Extend `risk_dtos.py` with new validation types
   - Reuse existing `DiscrepancyValidationReason` enum
   - Create response types for email chain and external contact validations

3. **Repository Layer**: Add validation repositories in `risk_repository.py`
   - `EmailChainDiscrepancyValidationRepository`
   - `ExternalContactValidationRepository`
   - Follow patterns from `DiscrepancyValidationRepository`

### Phase 2: Core Implementation
4. **Backend API Endpoints**: Add endpoints in `risk_routes.py`
   - GET/PUT/DELETE for email chain discrepancy validations
   - GET/PUT/DELETE for external contact validations
   - Include validation progress endpoints

5. **Frontend Types**: Extend `risk.ts` with validation types
   - `EmailChainDiscrepancyValidation`
   - `ExternalContactValidation`
   - Validation progress interfaces

6. **Frontend Service**: Extend `riskService.ts` with API methods
   - CRUD methods for both validation types
   - Progress tracking methods

7. **UI Components**: Create validation item components
   - `FKEmailChainValidationItem.tsx` - For email chain discrepancies
   - `FKExternalContactValidationItem.tsx` - For external contacts
   - Follow pattern from `FKDiscrepancyValidationItem.tsx`

### Phase 3: Integration
8. **Integrate into Email Chain Uploader**: Modify `FKEmailChainUploader.tsx`
   - Display validation controls for each discrepancy in validation_result.discrepancies
   - Show validation progress indicator
   - Handle validation state updates

9. **Integrate into External Contact Tab**: Modify `FKExternalContactTab.tsx`
   - Display validation controls for suspicious/critical contacts
   - Show validation progress indicator
   - Handle validation state updates

10. **PDF Export Integration**: Modify `crossValidationPdfExport.ts`
    - Fetch external communication validation data
    - Add "Validaciones de Comunicación Externa" section to PDF
    - Include validation reasons, comments, and validator info

## Step by Step Tasks

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_discrepancy_validation_checkboxes.md` to understand E2E test patterns
- Create `.claude/commands/e2e/test_external_communication_validation_comments.md` with test steps for:
  - Validating email chain discrepancies with reasons and comments
  - Validating external contact alerts with reasons and comments
  - Verifying validation progress tracking
  - Verifying PDF export includes validation data
  - Testing role-based access control

### Step 2: Create Database Migration
- Create `backend/database/migration_add_external_communication_validations.sql`
- Create `email_chain_discrepancy_validations` table:
  - `id` UUID PRIMARY KEY
  - `email_chain_id` UUID NOT NULL REFERENCES risk_email_chains(id) ON DELETE CASCADE
  - `discrepancy_index` INTEGER NOT NULL (index of discrepancy in validation_result.discrepancies array)
  - `is_validated` BOOLEAN NOT NULL DEFAULT FALSE
  - `validation_reason` TEXT (enum value)
  - `comments` TEXT (max 2000 chars)
  - `validated_by` UUID REFERENCES auth.users(id)
  - `validated_at` TIMESTAMPTZ
  - `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
  - `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
  - UNIQUE (email_chain_id, discrepancy_index)
- Create `external_contact_validations` table:
  - `id` UUID PRIMARY KEY
  - `external_contact_id` UUID NOT NULL REFERENCES risk_external_contacts(id) ON DELETE CASCADE
  - `is_validated` BOOLEAN NOT NULL DEFAULT FALSE
  - `validation_reason` TEXT
  - `comments` TEXT
  - `validated_by` UUID REFERENCES auth.users(id)
  - `validated_at` TIMESTAMPTZ
  - `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()
  - `updated_at` TIMESTAMPTZ NOT NULL DEFAULT now()
  - UNIQUE (external_contact_id)
- Add indexes and RLS policies
- Add update trigger for updated_at

### Step 3: Add Backend DTOs
- Edit `backend/src/interface/risk_dtos.py`
- Add `EmailChainDiscrepancyValidationRequest` class:
  - `is_validated: bool`
  - `validation_reason: Optional[DiscrepancyValidationReason]`
  - `comments: Optional[str]` (max 2000 chars)
- Add `EmailChainDiscrepancyValidationResponse` class with all fields
- Add `ExternalContactValidationRequest` class (same structure)
- Add `ExternalContactValidationResponse` class
- Add `EmailChainWithValidations` to extend EmailChainResponse with validation data
- Add `ExternalContactWithValidation` to extend ExternalContactResponse with validation data
- Add progress response types for both

### Step 4: Add Backend Repositories
- Edit `backend/src/repositorio/risk_repository.py`
- Add `EmailChainDiscrepancyValidationRepository` class:
  - `create(data: dict)` - Create validation record
  - `get_by_id(id: str)` - Get by UUID
  - `get_by_email_chain_and_index(email_chain_id: str, discrepancy_index: int)` - Get validation for specific discrepancy
  - `get_by_email_chain(email_chain_id: str)` - Get all validations for an email chain
  - `get_by_assessment(assessment_id: str)` - Get all email chain validations for assessment
  - `upsert(email_chain_id: str, discrepancy_index: int, data: dict)` - Create or update
  - `delete(id: str)` - Delete validation
  - `get_validation_progress(assessment_id: str)` - Get validation counts
- Add `ExternalContactValidationRepository` class (similar methods)

### Step 5: Add Backend API Endpoints
- Edit `backend/src/adapter/rest/risk_routes.py`
- Add dependency factories for new repositories
- Add email chain discrepancy validation endpoints:
  - `GET /evaluations/{id}/email-chain-validations` - Get all with progress
  - `PUT /evaluations/{id}/email-chains/{chain_id}/discrepancy-validations/{index}` - Validate discrepancy
  - `DELETE /evaluations/{id}/email-chains/{chain_id}/discrepancy-validations/{index}` - Remove validation
- Add external contact validation endpoints:
  - `GET /evaluations/{id}/external-contact-validations` - Get all with progress
  - `PUT /evaluations/{id}/external-contacts/{contact_id}/validation` - Validate contact
  - `DELETE /evaluations/{id}/external-contacts/{contact_id}/validation` - Remove validation
- Use `require_roles(['mesa_control', 'risk_manager', 'admin'])` for write endpoints
- Add helper mapping functions

### Step 6: Add Frontend Types
- Edit `frontend/src/types/risk.ts`
- Add `EmailChainDiscrepancyValidation` interface
- Add `EmailChainDiscrepancyValidationRequest` interface
- Add `EmailChainDiscrepancyWithValidation` extending EmailChainDiscrepancy
- Add `EmailChainWithValidations` extending EmailChain
- Add `EmailChainValidationProgress` interface
- Add `ExternalContactValidation` interface
- Add `ExternalContactValidationRequest` interface
- Add `ExternalContactWithValidation` extending ExternalContact
- Add `ExternalContactValidationProgress` interface

### Step 7: Add Frontend API Service Methods
- Edit `frontend/src/services/riskService.ts`
- Add email chain validation methods:
  - `getEmailChainValidations(evaluationId: string)`
  - `validateEmailChainDiscrepancy(evaluationId: string, chainId: string, index: number, request)`
  - `removeEmailChainDiscrepancyValidation(evaluationId: string, chainId: string, index: number)`
- Add external contact validation methods:
  - `getExternalContactValidations(evaluationId: string)`
  - `validateExternalContact(evaluationId: string, contactId: string, request)`
  - `removeExternalContactValidation(evaluationId: string, contactId: string)`

### Step 8: Create Email Chain Validation Item Component
- Create `frontend/src/components/risk/FKEmailChainValidationItem.tsx`
- Follow pattern from `FKDiscrepancyValidationItem.tsx`
- Props: `discrepancy`, `discrepancyIndex`, `validation`, `canValidate`, `onValidate`, `onRemoveValidation`
- UI elements:
  - Expandable row with discrepancy info and severity
  - Validation status icon (checkmark if validated, warning if not)
  - Validation reason dropdown (same options as cross-validation)
  - Comments text field (max 2000 chars)
  - Save/Remove validation buttons
  - Validator name and timestamp display

### Step 9: Create External Contact Validation Item Component
- Create `frontend/src/components/risk/FKExternalContactValidationItem.tsx`
- Similar structure to email chain validation item
- Props: `contact`, `validation`, `canValidate`, `onValidate`, `onRemoveValidation`
- Additional display: email, sender name, detection type, domain info

### Step 10: Integrate Validation into Email Chain Uploader
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Fetch validation data for each email chain's discrepancies
- Pass user role info to determine `canValidate`
- Render `FKEmailChainValidationItem` for each discrepancy in expanded view
- Add validation progress indicator at top of list
- Handle validation state updates and refresh

### Step 11: Integrate Validation into External Contact Tab
- Edit `frontend/src/components/risk/FKExternalContactTab.tsx`
- Fetch validation data for external contacts
- Pass user role info to determine `canValidate`
- Render `FKExternalContactValidationItem` for each suspicious/critical contact
- Add validation progress indicator
- Handle validation state updates and refresh

### Step 12: Extend PDF Export
- Edit `frontend/src/utils/crossValidationPdfExport.ts`
- In `exportComprehensiveEvaluationReport`:
  - Accept additional parameters for email chain and external contact validations
  - Add "Alertas de Comunicación Externa" section after current external contacts section
  - Include validation status, reason, comments, and validator info in the table
  - Add validation progress banner if all alerts are validated
  - Color-code validation status column (green for validated, orange for pending)

### Step 13: Update Comprehensive Report Generation
- Edit `frontend/src/pages/risk/RiskEvaluationDetail.tsx` (or wherever report is triggered)
- Fetch email chain validations and external contact validations
- Pass validation data to `exportComprehensiveEvaluationReport`

### Step 14: Run Validation Commands
- Execute validation commands to verify implementation:
  - `cd backend && python -m pytest` - Run backend tests
  - `cd backend && ruff check src/` - Run backend linting
  - `cd frontend && npm run lint` - Run frontend linting
  - `cd frontend && npx tsc --noEmit` - Run TypeScript type check
  - `cd frontend && npm run build` - Run frontend build
- Execute E2E test: Read `.claude/commands/test_e2e.md` and run `.claude/commands/e2e/test_external_communication_validation_comments.md`

## Testing Strategy

### Unit Tests
- Backend: Test repository methods for CRUD operations
- Backend: Test API endpoints with mock data
- Backend: Test authorization (only allowed roles can validate)

### Edge Cases
- Validating a discrepancy that no longer exists (email chain deleted)
- Validating when email chain has no discrepancies
- Comments exceeding 2000 characters
- Concurrent validation updates
- Network errors during validation
- PDF export with partial validations

## Acceptance Criteria
- [ ] Mesa de Control can validate individual email chain discrepancies with reasons and comments
- [ ] Mesa de Control can validate individual external contact alerts with reasons and comments
- [ ] Validation controls only appear for authorized roles (mesa_control, risk_manager, admin)
- [ ] Validation progress indicator shows X/Y validated for email chains and external contacts
- [ ] Validated items display green checkmark, validation reason, and validator info
- [ ] Validations can be removed by authorized users
- [ ] Validations persist after page refresh
- [ ] PDF evaluation report includes "Alertas de Comunicación Externa" section with validation data
- [ ] PDF shows validation status, reason, comments for each alert
- [ ] All validation data is stored in database with proper audit trail

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_external_communication_validation_comments.md` E2E test file to validate this functionality works

## Notes
- The validation reason enum (`DiscrepancyValidationReason`) is reused from issue 63, keeping options consistent:
  - `manual_validation` - "Validación manual"
  - `email_verification` - "Verificado por email"
  - `loading_error` - "Error de carga"
  - `client_justification` - "Justificación del cliente"
- Email chain discrepancies are indexed by their position in the `validation_result.discrepancies` array, since they don't have unique IDs
- External contacts already have UUIDs, so validations can reference them directly
- The PDF export should show both cross-validation discrepancy validations AND external communication validations in appropriate sections
- Consider adding a summary section showing total validated vs pending across all alert types

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (CRUD Operations)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none required)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Repository patterns follow existing codebase conventions

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (N/A - Colombia only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
