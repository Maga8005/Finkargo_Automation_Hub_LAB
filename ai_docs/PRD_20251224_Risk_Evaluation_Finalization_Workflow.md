# PRD: Risk Evaluation Finalization Workflow

**Date:** 2024-12-24
**Status:** Planned
**Module:** Riesgos (Risk/Fraud Detection)

---

## Executive Summary

Refactor the risk evaluation workflow to defer all fraud checks until the user explicitly clicks "Finalizar Evaluación" button, instead of running checks immediately when NIT is entered. This ensures comprehensive validation before any risk determination is made.

---

## Problem Statement

### Current Flow (Issue)
1. User enters NIT → `evaluate_client()` **immediately** runs:
   - Blacklist check
   - All fraud indicator checks (identity, email, NIT format, address, history)
   - Calculates preliminary risk score
2. User uploads documents → AI extraction
3. User runs cross-validation → `finalize_evaluation()` auto-determines status:
   - LOW risk → `COMPLETED` (auto-approved)
   - MEDIUM/HIGH → `PENDING`
   - CRITICAL → `ESCALATED`
4. Email chains and external contacts validated separately, **NOT incorporated** into final score

### Issues
- Blacklist check runs immediately on NIT entry
- Preliminary fraud score calculated before all evidence gathered
- Auto-approval can happen before email/contact validations complete
- No unified "finalize" action that considers ALL validation results
- Evaluations can be marked "approved" before comprehensive review

---

## Proposed Solution

### New Workflow
```
1. Enter NIT → Create record with PENDING_DOCUMENTS status
   - NO blacklist check
   - NO fraud indicator checks
   - Score = 0

2. Upload documents → AI extraction (unchanged)

3. Cross-validation → Detect discrepancies
   - Status changes to PENDING_FINALIZATION
   - Score NOT calculated yet

4. Email chains → Domain validation (optional/configurable)

5. External contacts → Email validation (optional/configurable)

6. User clicks "Finalizar Evaluación" → Run ALL checks:
   - Blacklist check
   - Aggregate cross-validation results
   - Aggregate email chain validation results
   - Aggregate external contact validation results
   - Calculate final score
   - Determine verification status and final status

7. Generate comprehensive PDF report
```

### User Requirements (Confirmed)
| Requirement | Decision |
|-------------|----------|
| Blacklist check | Defer to final evaluation |
| Trigger mechanism | Manual "Finalizar Evaluación" button |
| Report content | Comprehensive PDF with all validations |
| Validation requirements | Configurable (email/contact optional or required) |

---

## Technical Implementation

### Phase 1: Backend - DTOs & Database

#### 1.1 New Status Value
**File:** `backend/src/interface/risk_dtos.py`

```python
class AssessmentStatus(str, Enum):
    PENDING = "pending"
    PENDING_DOCUMENTS = "pending_documents"
    PENDING_FINALIZATION = "pending_finalization"  # NEW
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    APPROVED = "approved"
    REJECTED = "rejected"
```

#### 1.2 New DTOs
**File:** `backend/src/interface/risk_dtos.py`

```python
class FinalizeEvaluationRequest(BaseModel):
    force_complete: bool = Field(default=False, description="Skip validation requirement checks")

class FinalizationStatusResponse(BaseModel):
    can_finalize: bool
    requirements: Dict[str, bool]  # cross_validation_done, email_chains_validated, etc.
    pending_items: List[str]

class EvaluationRequirementsConfig(BaseModel):
    require_cross_validation: bool = True
    require_email_chain_validation: bool = False
    require_external_contact_validation: bool = False
    min_documents_for_cross_validation: int = 2
```

#### 1.3 Database Migration
**New File:** `backend/database/migration_add_finalization_workflow.sql`

```sql
-- Add finalization tracking columns
ALTER TABLE risk_assessments
ADD COLUMN IF NOT EXISTS finalized_by UUID REFERENCES user_profiles(id),
ADD COLUMN IF NOT EXISTS finalized_at TIMESTAMP WITH TIME ZONE;

-- Update status constraint to include pending_finalization
ALTER TABLE risk_assessments DROP CONSTRAINT IF EXISTS risk_assessments_status_check;
ALTER TABLE risk_assessments ADD CONSTRAINT risk_assessments_status_check
CHECK (status IN ('pending', 'pending_documents', 'pending_finalization',
                  'in_progress', 'completed', 'escalated', 'approved', 'rejected'));

-- Configuration table for validation requirements
CREATE TABLE IF NOT EXISTS evaluation_requirements_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    require_cross_validation BOOLEAN NOT NULL DEFAULT TRUE,
    require_email_chain_validation BOOLEAN NOT NULL DEFAULT FALSE,
    require_external_contact_validation BOOLEAN NOT NULL DEFAULT FALSE,
    min_documents_for_cross_validation INTEGER NOT NULL DEFAULT 2,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO evaluation_requirements_config
(require_cross_validation, require_email_chain_validation,
 require_external_contact_validation, min_documents_for_cross_validation)
VALUES (TRUE, FALSE, FALSE, 2) ON CONFLICT DO NOTHING;
```

---

### Phase 2: Backend - Core Service Changes

#### 2.1 Modify evaluate_client()
**File:** `backend/src/core/servicios/risk/fraud_detection_service.py` (lines 85-153)

**Current behavior to remove:**
- Lines 112-121: Blacklist check
- Line 127: `_run_all_checks()` call
- Line 130: Preliminary score calculation

**New implementation:**
```python
async def evaluate_client(self, client_nit: str, user_id: str) -> dict:
    """Create initial evaluation record - NO fraud checks performed."""
    client_data = await self._get_client_data(client_nit)

    assessment_data = {
        'client_nit': client_nit,
        'risk_level': RiskLevel.LOW.value,  # Placeholder until finalization
        'risk_score': 0.0,  # No preliminary score
        'fraud_indicators': [],  # Empty until finalization
        'status': AssessmentStatus.PENDING_DOCUMENTS.value,
        'assessment_type': 'comprehensive',
        'assessed_by': user_id,
        'assessed_at': datetime.utcnow().isoformat(),
        'client_data_snapshot': client_data,
    }

    assessment = await self.risk_repo.create(assessment_data)
    logger.info(f"Created evaluation for NIT: {client_nit}, Status: pending_documents, Score: 0")
    return assessment
```

#### 2.2 New finalize_evaluation_complete() Method
**File:** `backend/src/core/servicios/risk/fraud_detection_service.py` (add after existing finalize_evaluation)

```python
async def finalize_evaluation_complete(
    self,
    assessment_id: str,
    user_id: str,
    requirements_config: Optional[EvaluationRequirementsConfig] = None,
) -> dict:
    """
    Complete finalization of risk evaluation - runs ALL checks.

    This is the single point where all fraud detection runs:
    1. Blacklist check
    2. Cross-validation results aggregation
    3. Email chain validation results
    4. External contact validation results
    5. Final score calculation
    """
    assessment = await self.risk_repo.get_by_id(assessment_id)
    if not assessment:
        raise ValueError(f"Assessment not found: {assessment_id}")

    client_nit = assessment['client_nit']
    client_data = assessment.get('client_data_snapshot') or await self._get_client_data(client_nit)

    # 1. Run blacklist check NOW
    if client_data:
        blacklist_match = await self._check_blacklist(client_data)
        if blacklist_match:
            return await self._finalize_as_blacklisted(assessment_id, user_id, client_data, blacklist_match)

    # 2. Gather cross-validation results
    validation_repo = CrossValidationRepository(self.risk_repo.supabase)
    cross_validation_results = await validation_repo.get_by_assessment(assessment_id)

    # 3. Gather email chain validation results
    email_chain_repo = EmailChainRepository(self.risk_repo.supabase)
    email_chains = await email_chain_repo.get_by_assessment(assessment_id)
    email_chain_discrepancies = self._extract_email_chain_discrepancies(email_chains)

    # 4. Gather external contact validation results
    contact_repo = ExternalContactRepository(self.risk_repo.supabase)
    contacts = await contact_repo.get_by_assessment(assessment_id)
    contact_issues = self._extract_contact_issues(contacts)

    # 5. Build comprehensive fraud indicators
    indicators = []
    for result in cross_validation_results:
        if result.get('is_discrepancy'):
            indicators.append(FraudIndicator(
                indicator_name=f"cross_validation_{result.get('validation_type')}",
                indicator_value=True,
                severity=self._map_severity(result.get('severity')),
                evidence=result.get('description', ''),
                score_impact=Decimal(str(result.get('score_impact', 0))),
            ))

    for disc in email_chain_discrepancies:
        indicators.append(FraudIndicator(...))

    for issue in contact_issues:
        indicators.append(FraudIndicator(...))

    # 6. Calculate final score
    final_score, final_level = await self.scoring_service.calculate_score(indicators)

    # 7. Determine verification status and final status
    verification_info = self.scoring_service.get_verification_info(cross_validation_results)
    final_status = self._determine_final_status(final_level)

    # 8. Update assessment
    update_data = {
        'risk_score': float(final_score),
        'risk_level': final_level.value,
        'status': final_status,
        'fraud_indicators': [self._indicator_to_dict(ind) for ind in indicators],
        'finalized_by': user_id,
        'finalized_at': datetime.utcnow().isoformat(),
    }

    updated_assessment = await self.risk_repo.update(assessment_id, update_data)

    # 9. Create alerts if HIGH/CRITICAL risk
    if final_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        await self._create_risk_alerts(updated_assessment, final_level, indicators)

    return updated_assessment
```

---

### Phase 3: Backend - API Routes

#### 3.1 Remove Auto-Finalization from Cross-Validation
**File:** `backend/src/adapter/rest/risk_routes.py` (lines 1133-1139)

```python
# REMOVE this block:
# await fraud_service.finalize_evaluation(assessment_id=id, cross_validation_results=result_records)

# REPLACE with:
await risk_repo.update(id, {
    'status': AssessmentStatus.PENDING_FINALIZATION.value
})
```

#### 3.2 New Finalize Endpoint
**File:** `backend/src/adapter/rest/risk_routes.py`

```python
@router.post("/evaluations/{id}/finalize", response_model=RiskAssessmentDetail)
async def finalize_evaluation(
    id: str,
    request: FinalizeEvaluationRequest = Body(default=FinalizeEvaluationRequest()),
    current_user: dict = Depends(require_roles(['risk_analyst', 'risk_manager']))
):
    """Finalize a risk evaluation - runs all pending fraud checks."""
    # Validate assessment exists and not already finalized
    # Validate requirements unless force_complete
    # Call fraud_service.finalize_evaluation_complete()
    # Return finalized assessment
```

#### 3.3 Finalization Status Endpoint
```python
@router.get("/evaluations/{id}/finalization-status", response_model=FinalizationStatusResponse)
async def get_finalization_status(id: str, current_user: dict = Depends(...)):
    """Check if evaluation is ready for finalization."""
```

#### 3.4 Requirements Config Endpoints
```python
@router.get("/config/requirements", response_model=EvaluationRequirementsConfig)
@router.put("/config/requirements", response_model=EvaluationRequirementsConfig)
```

---

### Phase 4: Frontend - Types & Service

#### 4.1 Update TypeScript Types
**File:** `frontend/src/types/risk.ts`

```typescript
export type AssessmentStatus =
  | 'pending'
  | 'pending_documents'
  | 'pending_finalization'  // NEW
  | 'in_progress'
  | 'completed'
  | 'escalated'
  | 'approved'
  | 'rejected';

export interface FinalizationStatus {
  can_finalize: boolean;
  requirements: {
    cross_validation_done: boolean;
    email_chains_validated: boolean;
    external_contacts_validated: boolean;
  };
  pending_items: string[];
}

export interface FinalizeEvaluationRequest {
  force_complete?: boolean;
}
```

#### 4.2 Add Service Methods
**File:** `frontend/src/services/riskService.ts`

```typescript
finalizeEvaluation: async (evaluationId: string, forceComplete: boolean = false): Promise<RiskAssessmentDetail> => {
  const response = await apiClient.post<RiskAssessmentDetail>(
    `/risk/evaluations/${evaluationId}/finalize`,
    { force_complete: forceComplete }
  );
  return response.data;
},

getFinalizationStatus: async (evaluationId: string): Promise<FinalizationStatus> => {
  const response = await apiClient.get<FinalizationStatus>(
    `/risk/evaluations/${evaluationId}/finalization-status`
  );
  return response.data;
},
```

---

### Phase 5: Frontend - Components

#### 5.1 New FKFinalizeButton Component
**New File:** `frontend/src/components/risk/FKFinalizeButton.tsx`

Features:
- "Finalizar Evaluación" primary button
- Confirmation dialog showing validation checklist:
  - ✓ Cross-validation done
  - ⚠ Email chains (optional/required per config)
  - ⚠ External contacts (optional/required per config)
- "Force complete" checkbox for skipping optional validations
- Loading state and error handling

#### 5.2 Update RiskEvaluationDetail.tsx
**File:** `frontend/src/pages/risk/RiskEvaluationDetail.tsx`

- Import and add `FKFinalizeButton` to Decision card
- Show button only for `pending_documents` or `pending_finalization` status
- Handle `onFinalized` callback to refresh assessment data

#### 5.3 Update FKCrossValidationResults.tsx
**File:** `frontend/src/components/risk/FKCrossValidationResults.tsx`

- Update success message: "Validación cruzada completada. Haga clic en 'Finalizar Evaluación' para calcular el puntaje final."

---

### Phase 6: PDF Report Enhancement

#### 6.1 Comprehensive Report Export
**File:** `frontend/src/utils/crossValidationPdfExport.ts`

New function `exportComprehensiveRiskReportToPDF()`:
1. **Assessment Summary** - Client info, NIT, final score, verification status
2. **Cross-Validation Results** - All document discrepancies with severity
3. **Email Chain Validation** - Domain validation results, typosquatting findings
4. **External Contact Validation** - Email validation results
5. **Risk Indicators** - All triggered fraud indicators
6. **Recommendation** - Based on final status

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/src/interface/risk_dtos.py` | Add PENDING_FINALIZATION status, new DTOs |
| `backend/src/core/servicios/risk/fraud_detection_service.py` | Modify evaluate_client(), add finalize_evaluation_complete() |
| `backend/src/adapter/rest/risk_routes.py` | Add /finalize endpoint, remove auto-finalization |
| `frontend/src/types/risk.ts` | Add new types and status |
| `frontend/src/services/riskService.ts` | Add new API methods |
| `frontend/src/pages/risk/RiskEvaluationDetail.tsx` | Add finalize button, report export |
| `frontend/src/components/risk/FKCrossValidationResults.tsx` | Update messaging |

## New Files

| File | Purpose |
|------|---------|
| `backend/database/migration_add_finalization_workflow.sql` | Database migration |
| `frontend/src/components/risk/FKFinalizeButton.tsx` | Finalize button component |

---

## Migration Strategy

1. **Apply database migration** - Adds new columns (non-breaking)
2. **Deploy backend** - New endpoint, modified evaluate_client
3. **Deploy frontend** - New button, updated messaging
4. **Update existing assessments:**
   ```sql
   UPDATE risk_assessments SET status = 'pending_finalization'
   WHERE status = 'pending_documents'
   AND EXISTS (SELECT 1 FROM risk_cross_validation_results WHERE assessment_id = risk_assessments.id);
   ```
5. **Already completed assessments** - Unchanged (processed under old workflow)

---

## Testing Checklist

- [ ] New evaluation creates record with score=0, status=pending_documents
- [ ] Blacklist check does NOT run on NIT entry
- [ ] Cross-validation updates status to pending_finalization (not completed)
- [ ] Finalize button appears for pending_documents/pending_finalization
- [ ] Finalization runs all checks and calculates final score
- [ ] Blacklist match at finalization results in REJECTED status
- [ ] Force complete works when optional validations are pending
- [ ] Comprehensive PDF report includes all validation sections
- [ ] Configuration toggles work for requirements

---

## Success Criteria

1. **No premature approvals** - Evaluations cannot be auto-approved before manual finalization
2. **Comprehensive scoring** - Final score incorporates all validation types
3. **User control** - Clear "Finalizar Evaluación" action with confirmation
4. **Configurable** - Risk managers can toggle validation requirements
5. **Audit trail** - `finalized_by` and `finalized_at` tracked
6. **Complete reports** - PDF includes all validation findings
