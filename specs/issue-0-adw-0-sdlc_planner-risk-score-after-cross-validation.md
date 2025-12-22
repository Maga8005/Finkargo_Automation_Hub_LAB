# Feature: Risk Score Calculation After Document Cross-Validation

## Feature Description
Adjust the risk_score calculation workflow in the risk department module so that the final risk score is calculated **after** document upload and cross-validation is completed, rather than at the initial evaluation creation. Currently, the risk score is calculated immediately when an evaluation is created based only on client data from the database. This feature will defer the final risk score calculation until document cross-validation discrepancies are incorporated, providing a more accurate and comprehensive fraud risk assessment.

## User Story
As a **Risk Analyst or Risk Manager**
I want the risk score to be calculated after all document cross-validation checks are complete
So that the final risk assessment incorporates discrepancies found between documents (like company name mismatches, NIT inconsistencies, or shareholder falsification) for a more accurate fraud detection

## Problem Statement
The current workflow has a significant gap in fraud detection:

1. **Initial evaluation** (`POST /api/risk/evaluate`) runs fraud checks against client data and immediately calculates a risk score (0-100)
2. **Document upload and extraction** happens afterward, extracting data from PDFs (financial statements, cédula, RUT, etc.)
3. **Cross-validation** (`POST /api/risk/evaluations/{id}/cross-validate`) compares extracted data across documents and finds discrepancies (critical findings like company name mismatches)
4. **The cross-validation discrepancies are NOT incorporated** into the main risk score - they only update `document_validation_status` to 'completed' and return a separate `total_score_impact`

This means critical fraud indicators discovered during document cross-validation (e.g., the Azelis case where "ROCSA" appeared vs "AZELIS" in different documents) do not affect the main risk score used for approval/rejection decisions.

## Solution Statement
Implement a two-phase risk scoring workflow:

1. **Phase 1: Initial Assessment** - When an evaluation is created, run preliminary fraud checks on client data and create an assessment with status `pending_documents` instead of calculating a final score
2. **Phase 2: Final Scoring** - After cross-validation completes, automatically recalculate the final risk score by combining:
   - Initial fraud indicators from client data checks
   - Cross-validation discrepancy score impacts
   - The combined score determines the final risk level and triggers appropriate alerts

This ensures the risk score reflects both data-level and document-level fraud signals.

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`
- Backend Protection: `require_roles(['risk_analyst', 'risk_manager'])` for evaluation and cross-validation endpoints
- Frontend Protection: `RoleProtectedRoute` with `allowedRoles={['risk_analyst', 'risk_manager']}`

## Relevant Files
Use these files to implement the feature:

**Backend - Core Services:**
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Main fraud detection logic; needs modification to split into preliminary and final scoring phases
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Risk score calculation; needs new method to incorporate cross-validation impacts
- `backend/src/core/servicios/risk/cross_validation_service.py` - Cross-validation logic; already calculates `total_score_impact`, needs to trigger final scoring

**Backend - API Layer:**
- `backend/src/adapter/rest/risk_routes.py` - API endpoints; modify `trigger_cross_validation` to call final scoring after validation completes

**Backend - Data Access:**
- `backend/src/repositorio/risk_repository.py` - Repository methods; may need new method to update risk score and level

**Backend - DTOs:**
- `backend/src/interface/risk_dtos.py` - Data transfer objects; add new status `pending_documents` to `AssessmentStatus` enum

**Frontend - Pages:**
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Detail page; update UI to show two-phase scoring status and indicate when score is preliminary vs final

**Frontend - Components:**
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Cross-validation display; may need to show that scoring was updated after validation
- `frontend/src/components/risk/FKRiskScoreCard.tsx` - Score display; add indicator for preliminary vs final score
- `frontend/src/components/risk/FKDocumentUploader.tsx` - Document upload; may show message that final scoring pending

**Frontend - Types:**
- `frontend/src/types/risk.ts` - TypeScript types; add `pending_documents` status

**Frontend - Services:**
- `frontend/src/services/riskService.ts` - API service; types already aligned

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - Test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `.claude/commands/e2e/test_risk_score_after_validation.md` - E2E test for the new workflow

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
| `risk_repo.get_by_id(id)` | `dict` | `data['field']` | `assessment['risk_score']` |
| `risk_repo.update(id, updates)` | `dict` | `data['field']` | `updated['status']` |
| `risk_repo.create(data)` | `dict` | `data['field']` | `assessment['id']` |
| `validation_repo.get_by_assessment(id)` | `List[dict]` | `item['field']` | `result['score_impact']` |
| `rules_repo.list_active()` | `List[dict]` | `rule['weight']` | Access via dict key |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - Need to add `pending_documents` status
- [ ] Template file exists in `backend/templates/` - N/A
- [x] Database records exist - `risk_assessments` table exists with `status` column
- [ ] Country-specific data handled - N/A (single workflow)

**Database Schema Note:**
The `risk_assessments` table `status` column is a VARCHAR that stores enum values. Adding `pending_documents` requires:
1. Adding to `AssessmentStatus` enum in Python DTOs
2. Adding to TypeScript `AssessmentStatus` type
3. No migration needed - VARCHAR accepts new string values

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `status` | `status` | `string` (enum) | Add `pending_documents` |
| `risk_score` | `risk_score` | `number/Decimal` | 0-100, may be null during pending_documents |
| `risk_level` | `risk_level` | `string` (enum) | May be null during pending_documents |
| `document_validation_status` | `document_validation_status` | `string` | `pending`, `extracting`, `completed` |
| `fraud_indicators` | `fraud_indicators` | `array` | Combined with cross-validation impacts |
| `is_preliminary_score` | N/A | `boolean` | Frontend-only, derived from status |

## Implementation Plan

### Phase 1: Foundation
1. **Add new assessment status** - Add `pending_documents` status to enums in both backend and frontend
2. **Update DTOs** - Ensure types support the new workflow state
3. **Add preliminary score indicator** - Add field to track if score is preliminary

### Phase 2: Core Implementation
1. **Modify fraud detection service** - Split evaluation into preliminary assessment (before documents) and final scoring (after cross-validation)
2. **Modify risk scoring service** - Add method to incorporate cross-validation score impacts
3. **Modify cross-validation endpoint** - After validation completes, trigger final score calculation and update assessment
4. **Update alert creation** - Alerts should only be created after final scoring

### Phase 3: Integration
1. **Update frontend status display** - Show appropriate status and messaging for `pending_documents` state
2. **Update risk score card** - Indicate when score is preliminary vs final
3. **Update evaluation detail page** - Guide user through document upload → cross-validation → final score flow
4. **Create E2E test** - Validate the complete workflow

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Add `pending_documents` Status to Backend Enums
- Open `backend/src/interface/risk_dtos.py`
- Add `PENDING_DOCUMENTS = "pending_documents"` to `AssessmentStatus` enum
- The enum should now have: `PENDING`, `PENDING_DOCUMENTS`, `IN_PROGRESS`, `COMPLETED`, `ESCALATED`, `APPROVED`, `REJECTED`

### Task 2: Add `pending_documents` Status to Frontend Types
- Open `frontend/src/types/risk.ts`
- Add `'pending_documents'` to `AssessmentStatus` type
- Add entry to `ASSESSMENT_STATUS_CONFIG` with label "Pendiente Documentos" and color "info"

### Task 3: Create E2E Test File for New Workflow
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_risk_score_after_validation.md`
- Include test steps for:
  1. Create new evaluation (should get `pending_documents` status, preliminary score)
  2. Upload at least 2 documents
  3. Process AI extraction
  4. Run cross-validation
  5. Verify final risk score is calculated (different from preliminary if discrepancies found)
  6. Verify status changes from `pending_documents` to `pending` or appropriate final status

### Task 4: Modify RiskScoringService to Support Combined Scoring
- Open `backend/src/core/servicios/risk/risk_scoring_service.py`
- Add new method `calculate_final_score(indicators, cross_validation_results, rules)`:
  - Takes initial fraud indicators
  - Takes cross-validation results with score impacts
  - Combines both into final score
  - Returns `(final_score, risk_level)`
- The combined score should be: initial_score + sum(cross_validation_score_impacts), capped at 100

### Task 5: Modify FraudDetectionService for Two-Phase Evaluation
- Open `backend/src/core/servicios/risk/fraud_detection_service.py`
- Modify `evaluate_client()` method:
  - Run all existing checks (identity, email, NIT, document, history, address)
  - Calculate a **preliminary** risk score
  - Set status to `pending_documents` instead of auto-determining status
  - Store preliminary score and indicators
  - Do NOT create alerts yet (defer to final scoring)
- Add new method `finalize_evaluation(assessment_id, cross_validation_results)`:
  - Retrieve existing assessment
  - Combine initial indicators with cross-validation score impacts
  - Calculate final risk score
  - Determine final status based on risk level (auto-complete low, auto-escalate critical)
  - Create alerts for high/critical risk
  - Update assessment with final score, level, and status

### Task 6: Modify Cross-Validation Endpoint to Trigger Final Scoring
- Open `backend/src/adapter/rest/risk_routes.py`
- In `trigger_cross_validation()` endpoint (around line 870):
  - After saving validation results
  - Call `fraud_detection_service.finalize_evaluation()` with assessment_id and results
  - The endpoint should return both cross-validation response AND updated assessment data
- Consider adding a new response field `assessment_updated: bool` to indicate scoring was finalized

### Task 7: Update Frontend Score Card to Show Preliminary Indicator
- Open `frontend/src/components/risk/FKRiskScoreCard.tsx`
- Add optional prop `isPreliminary?: boolean`
- When `isPreliminary` is true, show a chip/badge indicating "Puntaje Preliminar"
- Add tooltip explaining "El puntaje final se calculará después de la validación cruzada de documentos"

### Task 8: Update Frontend Evaluation Detail Page
- Open `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Determine `isPreliminary` based on `assessment.status === 'pending_documents'`
- Pass `isPreliminary` to `FKRiskScoreCard`
- In the Evaluation tab:
  - If status is `pending_documents`, show alert: "Suba y valide documentos para calcular el puntaje final de riesgo"
  - Show a step indicator: 1) Evaluación inicial ✓ → 2) Subir documentos → 3) Validación cruzada → 4) Puntaje final
- After cross-validation completes:
  - Refresh assessment data to get updated score
  - Show success message: "Puntaje de riesgo actualizado con resultados de validación cruzada"

### Task 9: Update FKCrossValidationResults Component
- Open `frontend/src/components/risk/FKCrossValidationResults.tsx`
- After successful validation (`handleValidate`):
  - Add call to refresh parent assessment data
  - Add prop `onAssessmentUpdated?: () => void` and call it after validation
  - Show success message indicating score was updated

### Task 10: Update Frontend Document Uploader Messaging
- Open `frontend/src/components/risk/FKDocumentUploader.tsx`
- Add alert at top when evaluation status is `pending_documents`:
  - "Suba documentos y ejecute la validación cruzada para calcular el puntaje final de riesgo"
- This provides clear user guidance on the workflow

### Task 11: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Fix any linting, type, or build errors

## Testing Strategy

### Unit Tests
- `test_fraud_detection_service.py`:
  - Test `evaluate_client()` returns `pending_documents` status
  - Test `finalize_evaluation()` combines scores correctly
  - Test final status determination based on combined score
- `test_risk_scoring_service.py`:
  - Test `calculate_final_score()` combines initial + cross-validation impacts
  - Test score capping at 100
  - Test risk level determination

### Edge Cases
1. **No documents uploaded** - Evaluation stays in `pending_documents` forever; user must be guided to upload
2. **Only 1 document processed** - Cross-validation requires 2+; should not allow validation
3. **Cross-validation finds no discrepancies** - Final score equals preliminary score
4. **Cross-validation adds 100+ points** - Score should cap at 100
5. **Blacklisted client** - Should still be auto-rejected at initial evaluation (skip document flow)
6. **Client not found** - Should still return error assessment at initial evaluation
7. **Concurrent validation attempts** - Should handle gracefully

## Acceptance Criteria
1. ✅ New evaluation creates with status `pending_documents` and preliminary score
2. ✅ Preliminary score is clearly indicated in the UI
3. ✅ Cross-validation completion triggers final score calculation
4. ✅ Final score incorporates cross-validation discrepancy score impacts
5. ✅ Final risk level is determined after combined scoring
6. ✅ Alerts are created only after final scoring
7. ✅ UI updates to show final score after validation
8. ✅ Status transitions from `pending_documents` to appropriate final status
9. ✅ Blacklisted clients are still auto-rejected immediately
10. ✅ All existing E2E tests pass
11. ✅ New E2E test validates the complete workflow

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_risk_score_after_validation.md` to validate the new workflow

## Notes

### Backward Compatibility
- Existing assessments with old statuses will continue to work
- The new `pending_documents` status is additive
- Consider a one-time migration to mark old `pending` assessments as needing review

### Future Considerations
- Could add automatic document upload reminders for assessments stuck in `pending_documents`
- Could add SLA tracking for time between evaluation creation and final scoring
- Could expose preliminary vs final score history for audit purposes

### Dependencies
- No new npm or pip packages required
- Uses existing infrastructure (Supabase, LandingAI for extraction)

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified - None needed (VARCHAR accepts new values)
- [x] E2E test file task included (Task 3)
- [x] All external dependencies (npm/pip packages) listed in Notes - None needed

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data Contract Verification table complete
- [x] Interface Mapping table complete
- [x] Access patterns verified (dict access for all repos)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled - N/A (single workflow)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
