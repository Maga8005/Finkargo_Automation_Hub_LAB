# Feature: Binary Pass/Fail System (Replace Scoring)

## Feature Description
Replace the current numeric risk scoring system (0-100 with weighted algorithm) with a simple binary PASS/FAIL outcome. The stakeholder explicitly requested that users should NOT see numeric scores, as this leads to justifications like "it scored 90 points so I passed it." Instead, the system should show a simple binary result: either ✅ PASS (all data is consistent) or ❌ REQUIRES MANUAL VERIFICATION (any discrepancy detected).

The underlying scoring calculation will be retained for internal analytics and audit purposes, but the UI will only display the binary outcome with green/red color coding.

## User Story
As a Risk Analyst or Risk Manager
I want to see a simple PASS or FAIL indicator instead of a numeric score
So that I cannot justify passing a risky evaluation based on a numeric threshold and must always manually verify any discrepancies

## Problem Statement
The current system displays numeric risk scores (0-100) with colored risk levels (LOW, MEDIUM, HIGH, CRITICAL). This creates a problem where users justify passing high-score evaluations by saying "it scored 90 points so I passed it." The stakeholder (Andrés Ferrer) explicitly stated: "Yo no le metería puntaje... esto si da rojos, hay alguna información que no coincida, hay que ir a mirar y verificar manualmente." (Translation: "I wouldn't use scores... if anything shows red, if there's any information that doesn't match, you have to manually verify it.")

## Solution Statement
Transform the risk display from a numeric score system to a binary Pass/Fail system:

1. **Backend**: Keep the underlying score calculation for internal analytics/audit, but add a new `verification_status` field with values: `PASS` or `REQUIRES_MANUAL_VERIFICATION`
2. **Frontend**: Replace all numeric score displays with binary indicators:
   - ✅ PASS (green) - No discrepancies detected
   - ❌ REQUIRES MANUAL VERIFICATION (red) - Any discrepancy found
3. **Decision Logic**: ANY discrepancy detected (even low severity) results in REQUIRES_MANUAL_VERIFICATION
4. **Acknowledgment Flow**: When verification is required, users must acknowledge they reviewed the discrepancies before proceeding

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: Existing RBAC dependencies from `backend/src/adapter/rest/rbac_dependencies.py` (no changes needed)
- Frontend Protection: Existing `RoleProtectedRoute` configuration (no changes needed)

## Relevant Files
Use these files to implement the feature:

**Backend DTOs (to add new types)**:
- `backend/src/interface/risk_dtos.py` - Add `VerificationStatus` enum and update response models to include `verification_status` field

**Backend Services (core logic changes)**:
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Add method to determine binary verification status based on discrepancies
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Update to set verification_status based on any discrepancy detection

**Backend API (response updates)**:
- `backend/src/adapter/rest/risk_routes.py` - Ensure endpoints return the new verification_status field

**Backend Repository (database updates if needed)**:
- `backend/src/repositorio/risk_repository.py` - No changes needed if we compute verification_status from existing data

**Frontend Types (TypeScript updates)**:
- `frontend/src/types/risk.ts` - Add `VerificationStatus` type and `VERIFICATION_STATUS_CONFIG` for UI styling

**Frontend Components (UI changes)**:
- `frontend/src/components/risk/FKRiskScoreCard.tsx` - Replace circular score display with binary pass/fail indicator
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Update to show binary status after validation
- `frontend/src/components/risk/FKRiskMetrics.tsx` - Update dashboard metrics to show pass/fail counts instead of risk level counts

**Frontend Pages (page-level updates)**:
- `frontend/src/pages/risk/RiskDashboard.tsx` - Update DataGrid to show verification status instead of score column
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Update to show binary status and require acknowledgment

**E2E Test References**:
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `frontend/src/components/risk/FKVerificationStatusCard.tsx` - New component to display binary pass/fail status with acknowledgment button
- `.claude/commands/e2e/test_binary_pass_fail.md` - E2E test for binary pass/fail feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [x] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| risk_repo.get_by_id() | dict | data['risk_score'] | Returns dict from Supabase |
| risk_repo.create() | dict | data['id'] | Returns created record as dict |
| risk_repo.update() | dict | data['risk_level'] | Returns updated record as dict |
| cross_validation_repo.get_by_assessment() | list[dict] | result['is_discrepancy'] | Returns list of validation results |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (will add `VerificationStatus` enum)
- [ ] Template file exists in `backend/templates/` (N/A - no templates)
- [x] Database records exist (no migration needed - verification_status computed from existing data)
- [x] Country-specific data handled (N/A - not country-specific)

**Note**: The `verification_status` will be computed at runtime from existing `fraud_indicators` and `cross_validation_results` data. No database migration is required because:
1. We keep the existing `risk_score` and `risk_level` fields for internal analytics
2. The binary status is derived: `has_discrepancies = any(result.is_discrepancy for result in cross_validation_results)`
3. This allows backward compatibility with existing assessments

### G. Query Specification (Reporting)

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| verification_status | enum | No | None (show all) |
| status | AssessmentStatus | No | None (show all) |
| client_nit | string | No | None |
| date_from | date | No | None |
| date_to | date | No | None |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| verification_status | verification_status | 'pass' \| 'requires_manual_verification' | New computed field |
| has_discrepancies | has_discrepancies | boolean | Derived from cross_validation_results |
| discrepancy_count | discrepancy_count | number | Count of is_discrepancy=true results |
| risk_score | risk_score | number | Kept for internal use, hidden from UI |
| risk_level | risk_level | RiskLevel | Kept for internal use, hidden from UI |

## Implementation Plan

### Phase 1: Foundation
1. Add new `VerificationStatus` enum to backend DTOs
2. Add `has_discrepancies` and `verification_status` computed properties to response models
3. Update frontend TypeScript types with new verification status types and UI config

### Phase 2: Core Implementation
1. Update `RiskScoringService` to include a method that determines verification status
2. Modify response DTOs to include the computed verification_status field
3. Create new `FKVerificationStatusCard` component for binary display
4. Update `FKRiskScoreCard` to hide numeric score and show binary status
5. Add acknowledgment state management for required verification cases

### Phase 3: Integration
1. Update `RiskDashboard` to filter/display by verification status
2. Update `RiskEvaluationDetail` to show new binary display
3. Update metrics components to show pass/fail statistics
4. Add E2E tests to validate the new behavior

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test File
Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand the E2E test format. Create `.claude/commands/e2e/test_binary_pass_fail.md` with test steps for:
- Navigating to risk dashboard
- Creating a new evaluation
- Uploading documents and triggering cross-validation
- Verifying binary PASS display when no discrepancies found
- Verifying REQUIRES MANUAL VERIFICATION display when discrepancies exist
- Testing the acknowledgment flow before proceeding

### Step 2: Add Backend VerificationStatus Enum
Update `backend/src/interface/risk_dtos.py`:
- Add `VerificationStatus` enum with values: `PASS = "pass"`, `REQUIRES_MANUAL_VERIFICATION = "requires_manual_verification"`
- Add computed field `verification_status` to `RiskAssessmentResponse` and `RiskAssessmentDetail`
- Add `has_discrepancies` and `discrepancy_count` fields to response models
- Use `@validator` or `@computed_field` (Pydantic v2) to compute these from existing data

### Step 3: Update RiskScoringService
Update `backend/src/core/servicios/risk/risk_scoring_service.py`:
- Add method `determine_verification_status(cross_validation_results: List[dict]) -> VerificationStatus`
- Logic: If ANY result has `is_discrepancy=True`, return `REQUIRES_MANUAL_VERIFICATION`, else `PASS`
- Add method `count_discrepancies(cross_validation_results: List[dict]) -> int`

### Step 4: Update Risk Routes to Include Verification Status
Update `backend/src/adapter/rest/risk_routes.py`:
- Ensure that when returning assessment details, the verification_status is computed from cross_validation_results
- Update `get_evaluation_detail` endpoint to fetch cross_validation_results and compute verification_status
- Add verification_status to dashboard stats response (counts of pass vs requires_verification)

### Step 5: Add Frontend TypeScript Types
Update `frontend/src/types/risk.ts`:
- Add `VerificationType = 'pass' | 'requires_manual_verification'` type
- Add `VERIFICATION_STATUS_CONFIG` object with labels and colors:
  ```typescript
  pass: { label: 'APROBADO', color: 'success', bgColor: '#E0F7E6', textColor: '#2CA14D', icon: 'CheckCircle' }
  requires_manual_verification: { label: 'REQUIERE VERIFICACIÓN MANUAL', color: 'error', bgColor: '#FFE4E4', textColor: '#CC071E', icon: 'Warning' }
  ```
- Update `RiskAssessment` and `RiskAssessmentDetail` interfaces to include `verification_status`, `has_discrepancies`, `discrepancy_count`

### Step 6: Create FKVerificationStatusCard Component
Create `frontend/src/components/risk/FKVerificationStatusCard.tsx`:
- Props: `verificationStatus`, `discrepancyCount`, `onAcknowledge`, `isAcknowledged`, `isPreliminary`
- Display large binary indicator (checkmark or warning icon)
- Show status label in Spanish
- If `requires_manual_verification`: show acknowledgment checkbox/button
- If `isPreliminary`: show informational message that verification is pending
- Use Finkargo design system colors (green for pass, red for requires verification)

### Step 7: Update FKRiskScoreCard Component
Update `frontend/src/components/risk/FKRiskScoreCard.tsx`:
- Remove the circular progress score display
- Remove numeric score display (the `{Number(score).toFixed(0)}` element)
- Remove the risk level chip that shows LOW/MEDIUM/HIGH/CRITICAL
- Keep the fraud indicators list but update styling:
  - Show indicators that triggered as "issues found"
  - Group by: triggered vs passed
- Replace score visualization with verification status from new component
- Import and use `FKVerificationStatusCard` for the main display

### Step 8: Update FKRiskMetrics Component
Update `frontend/src/components/risk/FKRiskMetrics.tsx`:
- Add metrics cards for:
  - "Aprobados" (PASS count) - green
  - "Requieren Verificación" (REQUIRES_MANUAL_VERIFICATION count) - red
- Keep existing status metrics (pending, completed, escalated, etc.)
- Remove or hide the risk level breakdown cards (low_risk_count, medium_risk_count, etc.) since we're moving away from risk levels in UI

### Step 9: Update RiskDashboard Page
Update `frontend/src/pages/risk/RiskDashboard.tsx`:
- Update DataGrid columns:
  - Replace `risk_score` column with `verification_status` column showing pass/fail chip
  - Remove `risk_level` column (or keep hidden for filtering purposes)
  - Add binary indicator cell renderer
- Update filters to allow filtering by verification_status
- Update the metrics section to use new pass/fail counts

### Step 10: Update RiskEvaluationDetail Page
Update `frontend/src/pages/risk/RiskEvaluationDetail.tsx`:
- Replace `FKRiskScoreCard` usage with the new binary display approach
- Add acknowledgment requirement before decision can be made:
  - If `verification_status === 'requires_manual_verification'`:
    - Disable the decision form until user acknowledges they reviewed discrepancies
    - Add an acknowledgment checkbox or button
- Update the alert messages to reflect binary system
- Remove references to "score" in UI text, replace with verification status language

### Step 11: Update FKCrossValidationResults Component
Update `frontend/src/components/risk/FKCrossValidationResults.tsx`:
- After validation completes, prominently display the binary outcome
- Update success message to indicate pass/fail result
- If any discrepancy found: show red banner with "REQUIERE VERIFICACIÓN MANUAL"
- If no discrepancies: show green banner with "APROBADO - Todos los datos son consistentes"

### Step 12: Update RiskStats Interface and Dashboard API
Update backend and frontend to support new stats:
- Add `pass_count` and `requires_verification_count` to `RiskStatsResponse` DTO
- Update `get_dashboard` endpoint to compute these counts
- Update frontend `RiskStats` interface

### Step 13: Run Validation Commands
Execute all validation commands to ensure zero regressions:
- Backend tests, linting, and type checking
- Frontend linting, TypeScript checks, and build
- E2E test for binary pass/fail feature

## Testing Strategy

### Unit Tests
- `test_risk_scoring_service.py`:
  - Test `determine_verification_status()` returns PASS when no discrepancies
  - Test `determine_verification_status()` returns REQUIRES_MANUAL_VERIFICATION with any discrepancy (even low severity)
  - Test `count_discrepancies()` returns correct count
- `test_fraud_detection_service.py`:
  - Test that verification_status is correctly set in assessment responses

### Edge Cases
1. **No cross-validation results yet** (pending_documents status): Show "Pending Verification" state, not PASS
2. **Empty discrepancies list**: Return PASS
3. **All discrepancies have is_discrepancy=False**: Return PASS
4. **Single low-severity discrepancy**: Return REQUIRES_MANUAL_VERIFICATION (any discrepancy = fail)
5. **Multiple discrepancies of varying severity**: Return REQUIRES_MANUAL_VERIFICATION
6. **Blacklisted entity**: Still show as REQUIRES_MANUAL_VERIFICATION (already rejected)
7. **Already approved/rejected assessments**: Show historical verification status

## Acceptance Criteria
1. ✅ Numeric risk scores (0-100) are NOT displayed to users anywhere in the UI
2. ✅ Risk level labels (LOW, MEDIUM, HIGH, CRITICAL) are NOT displayed to users
3. ✅ Binary pass/fail indicator is shown: "APROBADO" (green) or "REQUIERE VERIFICACIÓN MANUAL" (red)
4. ✅ ANY discrepancy (regardless of severity) triggers REQUIRES_MANUAL_VERIFICATION
5. ✅ Users must acknowledge reviewing discrepancies before making a decision on flagged evaluations
6. ✅ Dashboard shows counts of pass vs requires_verification instead of risk level counts
7. ✅ Data grid shows verification status column instead of score column
8. ✅ Internal score calculation is preserved for analytics/audit (backend only)
9. ✅ E2E test validates the complete pass/fail flow
10. ✅ All existing functionality continues to work (zero regressions)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_binary_pass_fail.md` to validate this functionality works
- `cd backend && python -m pytest tests/ -v` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
1. **Backward Compatibility**: Existing assessments will continue to work. The verification_status is computed from existing cross_validation_results data, so historical records will correctly show their status.

2. **Internal Analytics**: The underlying `risk_score` and `risk_level` fields are preserved in the database and API responses. This allows:
   - Historical analysis of risk patterns
   - Future ML/analytics on scoring trends
   - Audit trail of how scores were calculated
   - Potential future admin-only views of detailed scores

3. **Translation**: All user-facing text uses Spanish as per project standards:
   - "APROBADO" for PASS
   - "REQUIERE VERIFICACIÓN MANUAL" for REQUIRES_MANUAL_VERIFICATION
   - "Verificación pendiente" for pending states

4. **No New Dependencies**: This feature uses existing MUI components and React patterns. No new npm or pip packages are required.

5. **Stakeholder Quote for Context**: "Yo no le metería puntaje, yo le diría todo o nada, entonces o todo concuerda o no, o si hay un error yo así está rojo, verificación manual." - Andrés Ferrer

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - computed field)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Reporting:**
- [x] Query filters and parameters documented
- [x] Pagination/sorting requirements specified (uses existing DataGrid pagination)

**CRUD Operations:**
- [x] Repository patterns documented
- [x] Validation rules specified (any discrepancy = fail)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (N/A)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (Step 1)
