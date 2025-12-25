# Feature: Defer Fraud Checks Until Finalization

## Feature Description
Refactor the risk evaluation workflow to defer all fraud checks (including blacklist verification) until the user explicitly clicks the "Finalizar Evaluación" button. Currently, fraud checks and preliminary scoring run immediately when a NIT is entered. This change ensures comprehensive validation by aggregating cross-validation, email chain, and external contact validation results before calculating the final risk score.

The new workflow creates evaluations in a `PENDING_DOCUMENTS` state with zero score, allows document upload and validation, transitions to `PENDING_FINALIZATION` after cross-validation, and only runs all fraud checks when the user manually finalizes the evaluation.

## User Story
As a **risk_analyst or risk_manager**
I want to defer all fraud detection checks until I click "Finalizar Evaluación"
So that I can ensure all documents are uploaded and validated before the final risk score is calculated, preventing premature auto-approvals

## Problem Statement
The current workflow has several issues:
1. **Blacklist check runs immediately on NIT entry** - Should be deferred until finalization
2. **Preliminary fraud score calculated before all evidence gathered** - Results in inaccurate early assessments
3. **Cross-validation auto-triggers `finalize_evaluation()`** - Auto-approves LOW risk without user control
4. **Email chain and external contact validations are separate** - Not incorporated into the final score
5. **No unified "finalize" action** - User lacks explicit control over when final determination is made

## Solution Statement
Implement a new workflow that:
1. Creates evaluations with `PENDING_DOCUMENTS` status and score=0 (no fraud checks)
2. Allows document upload and AI extraction (unchanged)
3. Transitions to `PENDING_FINALIZATION` after cross-validation (no auto-finalization)
4. Provides a "Finalizar Evaluación" button that runs ALL checks:
   - Blacklist check
   - Cross-validation results aggregation
   - Email chain validation results
   - External contact validation results
   - Final score calculation
5. Tracks finalization with `finalized_by` and `finalized_at` audit fields
6. Generates comprehensive PDF report with all validation findings

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`
- Backend Protection: Use `require_roles(['risk_analyst', 'risk_manager'])` from `rbac_dependencies.py`
- Frontend Protection: Existing role checks in `RiskEvaluationDetail.tsx` for decision-making

## Relevant Files
Use these files to implement the feature:

### Backend - Core Logic
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Modify `evaluate_client()` to skip blacklist/fraud checks, add `finalize_evaluation_complete()` method
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Used by finalization for score calculation
- `backend/src/core/servicios/risk/cross_validation_service.py` - Provides cross-validation results aggregation
- `backend/src/core/servicios/risk/email_chain_service.py` - Provides email chain validation results
- `backend/src/core/servicios/risk/external_contact_service.py` - Provides external contact validation results
- `backend/src/core/servicios/risk/alert_service.py` - Create alerts after finalization

### Backend - API Layer
- `backend/src/adapter/rest/risk_routes.py` - Add `/finalize` endpoint, remove auto-finalization from cross-validation, add finalization status and config endpoints
- `backend/src/adapter/rest/rbac_dependencies.py` - Role-based access control

### Backend - Data Layer
- `backend/src/interface/risk_dtos.py` - Add `PENDING_FINALIZATION` status, new DTOs for finalization
- `backend/src/repositorio/risk_repository.py` - Repository for assessment CRUD

### Frontend - Types & Service
- `frontend/src/types/risk.ts` - Add new TypeScript types and status config
- `frontend/src/services/riskService.ts` - Add finalization API methods

### Frontend - UI Components
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Add FKFinalizeButton, update workflow
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Update success message, remove auto-finalization reference
- `frontend/src/utils/crossValidationPdfExport.ts` - Enhance comprehensive report

### E2E Test Reference
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/e2e_onhold/test_login.md` - Example E2E test format

### New Files
- `backend/database/migration_add_finalization_workflow.sql` - Database migration for finalization columns and config table
- `frontend/src/components/risk/FKFinalizeButton.tsx` - New finalization button component with confirmation dialog
- `.claude/commands/e2e/test_risk_evaluation_finalization.md` - E2E test for finalization workflow

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
| `risk_repo.get_by_id()` | dict | `data['field']` | `assessment['client_nit']` |
| `risk_repo.create()` | dict | `data['field']` | `assessment['id']` |
| `risk_repo.update()` | dict | `data['field']` | `updated['status']` |
| `validation_repo.get_by_assessment()` | List[dict] | `result.get('is_discrepancy')` | `results[0]['severity']` |
| `email_chain_repo.get_by_assessment()` | List[dict] | `chain['validation_result']` | `chain['validation_status']` |
| `contact_repo.get_by_assessment()` | List[dict] | `contact['validation_result']` | `contact['validation_status']` |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs - `AssessmentStatus.PENDING_FINALIZATION` to be added
- [ ] Template file exists in `backend/templates/` - N/A for this feature
- [x] Database records exist (or migration created) - Migration adds columns and config table
- [ ] Country-specific data handled (CO vs MX) - N/A for this feature

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `status` | `status` | string | Add `pending_finalization` value |
| `can_finalize` | `can_finalize` | boolean | New field in finalization status |
| `requirements` | `requirements` | object | `{cross_validation_done, email_chains_validated, external_contacts_validated}` |
| `pending_items` | `pending_items` | string[] | List of incomplete requirements |
| `force_complete` | `force_complete` | boolean | Skip optional validations |
| `finalized_by` | `finalized_by` | string (UUID) | User who finalized |
| `finalized_at` | `finalized_at` | string (ISO datetime) | When finalization occurred |

## Implementation Plan

### Phase 1: Foundation
1. **Database Migration** - Add `finalized_by`, `finalized_at` columns to `risk_assessments`, create `evaluation_requirements_config` table, update status constraint
2. **Backend DTOs** - Add `PENDING_FINALIZATION` to `AssessmentStatus` enum, create `FinalizeEvaluationRequest`, `FinalizationStatusResponse`, `EvaluationRequirementsConfig` Pydantic models
3. **Frontend Types** - Add corresponding TypeScript types and update `ASSESSMENT_STATUS_CONFIG`

### Phase 2: Core Implementation
1. **Modify `evaluate_client()`** - Remove blacklist check and fraud indicator checks, always return score=0 with `PENDING_DOCUMENTS` status
2. **Create `finalize_evaluation_complete()`** - New method that runs all checks, aggregates results, calculates final score, and updates assessment
3. **Modify cross-validation endpoint** - Remove auto-finalization, update status to `PENDING_FINALIZATION` instead
4. **Create finalization endpoints** - `POST /finalize`, `GET /finalization-status`, `GET /config/requirements`, `PUT /config/requirements`

### Phase 3: Integration
1. **Create FKFinalizeButton component** - Button with confirmation dialog, validation checklist, force-complete option
2. **Update RiskEvaluationDetail.tsx** - Add FKFinalizeButton in Decision card, handle finalization flow
3. **Update FKCrossValidationResults.tsx** - Change success message to guide user to finalization
4. **Enhance PDF report** - Include all validation sections (cross-validation, email chains, external contacts)
5. **Create E2E test** - Validate complete finalization workflow

## Step by Step Tasks

### Step 1: Create Database Migration
- Create `backend/database/migration_add_finalization_workflow.sql`
- Add `finalized_by UUID REFERENCES user_profiles(id)` to `risk_assessments`
- Add `finalized_at TIMESTAMP WITH TIME ZONE` to `risk_assessments`
- Update status constraint to include `pending_finalization`
- Create `evaluation_requirements_config` table with default settings
- Insert default configuration record

### Step 2: Update Backend DTOs
- Add `PENDING_FINALIZATION = "pending_finalization"` to `AssessmentStatus` enum in `backend/src/interface/risk_dtos.py`
- Create `FinalizeEvaluationRequest` Pydantic model with `force_complete: bool = False`
- Create `FinalizationStatusResponse` model with `can_finalize`, `requirements`, `pending_items`
- Create `EvaluationRequirementsConfig` model with requirement flags and min_documents

### Step 3: Update Frontend Types
- Add `'pending_finalization'` to `AssessmentStatus` union type in `frontend/src/types/risk.ts`
- Add `{ label: 'Pendiente Finalización', color: 'warning' }` to `ASSESSMENT_STATUS_CONFIG`
- Create `FinalizationStatus` interface
- Create `FinalizeEvaluationRequest` interface
- Create `EvaluationRequirementsConfig` interface

### Step 4: Modify evaluate_client() Method
- Edit `backend/src/core/servicios/risk/fraud_detection_service.py`
- Remove blacklist check (lines 112-121) - defer to finalization
- Remove `_run_all_checks()` call (line 127) - defer to finalization
- Set `risk_score: 0.0` for all new evaluations (both new clients and existing clients)
- Set `status: PENDING_DOCUMENTS` for all new evaluations
- Keep client_data_snapshot for later use during finalization
- Log the change: "Created evaluation for NIT: {nit}, Score: 0, Status: pending_documents"

### Step 5: Create finalize_evaluation_complete() Method
- Add new method to `FraudDetectionService` class
- Accept `assessment_id`, `user_id`, optional `requirements_config`
- Validate assessment exists and is in valid state for finalization
- Run blacklist check NOW (moved from evaluate_client)
- If blacklisted, return immediately with REJECTED status
- Gather cross-validation results from `CrossValidationRepository`
- Gather email chain validation results from `EmailChainRepository`
- Gather external contact validation results from `ExternalContactRepository`
- Build comprehensive `FraudIndicator` list from all validation types
- Calculate final score using `scoring_service.calculate_score()`
- Determine final status based on risk level
- Update assessment with final values including `finalized_by` and `finalized_at`
- Create alerts for HIGH/CRITICAL risk levels
- Return updated assessment

### Step 6: Remove Auto-Finalization from Cross-Validation Endpoint
- Edit `backend/src/adapter/rest/risk_routes.py` at lines 1133-1139
- Remove call to `fraud_service.finalize_evaluation()`
- Replace with `risk_repo.update(id, {'status': AssessmentStatus.PENDING_FINALIZATION.value})`
- Update log message to indicate pending finalization

### Step 7: Create Finalization API Endpoints
- Add `POST /evaluations/{id}/finalize` endpoint
  - Accept `FinalizeEvaluationRequest` body
  - Validate assessment state (must be `pending_documents` or `pending_finalization`)
  - Check requirements unless `force_complete=True`
  - Call `fraud_service.finalize_evaluation_complete()`
  - Return `RiskAssessmentDetail`
- Add `GET /evaluations/{id}/finalization-status` endpoint
  - Check cross-validation completed
  - Check email chains validated (if required)
  - Check external contacts validated (if required)
  - Return `FinalizationStatusResponse`
- Add `GET /config/requirements` and `PUT /config/requirements` endpoints
  - CRUD for evaluation requirements configuration

### Step 8: Add Frontend Service Methods
- Edit `frontend/src/services/riskService.ts`
- Add `finalizeEvaluation(evaluationId: string, forceComplete?: boolean)` method
- Add `getFinalizationStatus(evaluationId: string)` method
- Add `getRequirementsConfig()` method
- Add `updateRequirementsConfig(config: EvaluationRequirementsConfig)` method

### Step 9: Create FKFinalizeButton Component
- Create `frontend/src/components/risk/FKFinalizeButton.tsx`
- Props: `evaluationId`, `evaluationStatus`, `onFinalized`, `disabled`
- Fetch finalization status on mount
- Show "Finalizar Evaluación" primary button
- On click, open confirmation dialog with:
  - Validation checklist (✓ cross-validation, optional email/contacts)
  - Warning about irreversible action
  - "Forzar completar" checkbox for skipping optional validations
- Handle loading state during finalization
- Show error/success messages
- Call `onFinalized` callback with updated assessment

### Step 10: Update RiskEvaluationDetail.tsx
- Import `FKFinalizeButton` component
- Add FKFinalizeButton to Decision card (right column)
- Show only for `pending_documents` or `pending_finalization` status
- Pass `evaluationId`, `evaluationStatus`, `onFinalized` callback
- On finalization complete, refresh assessment data
- Update `canMakeDecision` logic to include finalized assessments

### Step 11: Update FKCrossValidationResults.tsx
- Edit `frontend/src/components/risk/FKCrossValidationResults.tsx`
- Change success message from "El puntaje de riesgo ha sido actualizado" to:
  "Validación cruzada completada. Haga clic en 'Finalizar Evaluación' para calcular el puntaje final de riesgo."
- Add informational note about finalization requirement

### Step 12: Enhance Comprehensive PDF Report
- Edit `frontend/src/utils/crossValidationPdfExport.ts`
- Create new function `exportComprehensiveRiskReportToPDF()`
- Accept assessment data, cross-validation results, email chains, external contacts
- Generate sections:
  1. Assessment Summary (client info, NIT, status, finalized by/at)
  2. Cross-Validation Results (existing functionality)
  3. Email Chain Validation (sender domains, discrepancies)
  4. External Contact Validation (email validation results)
  5. All Fraud Indicators
  6. Final Recommendation based on status

### Step 13: Create E2E Test File
- Create `.claude/commands/e2e/test_risk_evaluation_finalization.md`
- Define user story for finalization workflow
- Test steps:
  1. Login as risk_analyst
  2. Create new evaluation (verify score=0, status=pending_documents)
  3. Upload documents and run extraction
  4. Run cross-validation (verify status changes to pending_finalization)
  5. Verify "Finalizar Evaluación" button appears
  6. Click finalize and complete dialog
  7. Verify final score is calculated
  8. Verify status changes appropriately
- Define success criteria and capture screenshots

### Step 14: Run Validation Commands
- Execute all validation commands to ensure no regressions

## Testing Strategy

### Unit Tests
- Test `evaluate_client()` returns score=0 and PENDING_DOCUMENTS status
- Test `finalize_evaluation_complete()` runs all checks correctly
- Test blacklist matching at finalization rejects client
- Test aggregation of cross-validation, email chain, and contact results
- Test force_complete bypasses optional validations
- Test finalization status correctly reports requirements

### Edge Cases
- Finalization attempted on already-finalized assessment (should error)
- Finalization with zero documents uploaded (should error)
- Finalization with partial validations when force_complete=true (should succeed)
- Blacklist match detected at finalization (immediate rejection)
- Empty email chains and external contacts (should not affect score)
- Configuration changes between evaluation creation and finalization

## Acceptance Criteria
1. **New evaluations start with score=0** - No preliminary fraud checks on NIT entry
2. **Blacklist check deferred** - Only runs when "Finalizar Evaluación" is clicked
3. **Cross-validation doesn't auto-finalize** - Status becomes `pending_finalization` not `completed`
4. **Finalize button appears** - Visible for `pending_documents` and `pending_finalization` statuses
5. **Confirmation dialog shows checklist** - Lists required and optional validations
6. **Force complete option works** - Allows skipping optional validations
7. **Final score includes all validations** - Cross-validation + email chains + external contacts
8. **Audit trail maintained** - `finalized_by` and `finalized_at` recorded
9. **Comprehensive PDF generated** - Includes all validation sections
10. **E2E test passes** - Full workflow validated

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/ -v` - Run backend tests
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_risk_evaluation_finalization.md` E2E test

## Notes

### Migration Considerations
- Existing assessments with status `pending_documents` that have cross-validation results should be updated to `pending_finalization`:
  ```sql
  UPDATE risk_assessments SET status = 'pending_finalization'
  WHERE status = 'pending_documents'
  AND EXISTS (SELECT 1 FROM risk_cross_validation_results WHERE assessment_id = risk_assessments.id);
  ```
- Already completed assessments remain unchanged (processed under old workflow)

### Backward Compatibility
- The existing `finalize_evaluation()` method is kept for reference but will not be called
- New `finalize_evaluation_complete()` replaces its functionality with enhanced aggregation

### Future Enhancements
- Consider adding email notification on finalization
- Consider adding finalization summary in dashboard stats
- Consider configurable thresholds for auto-escalation at finalization

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes - None required

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [ ] Country-specific variations handled (CO vs MX) if applicable - N/A

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
