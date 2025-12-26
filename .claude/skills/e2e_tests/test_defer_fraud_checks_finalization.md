# E2E Test: Defer Fraud Checks to Finalization

## Test Overview

| Property | Value |
|----------|-------|
| **Feature** | Defer fraud checks until user finalization |
| **Test Type** | E2E (End-to-End) |
| **Priority** | High |
| **Components Tested** | fraud_detection_service, risk_routes, FKFinalizeButton, RiskEvaluationDetail |

## Description

This test validates the deferred finalization workflow where fraud checks (blacklist, indicators) are NOT run during initial evaluation creation, but are deferred until the user clicks "Finalizar Evaluación" after cross-validation.

## Pre-Requisites

- Backend server running on localhost:8000
- Frontend server running on localhost:5173
- Supabase database with migration `migration_add_finalization_workflow.sql` applied
- Test user with `risk_analyst` or `risk_manager` role

## Test Cases

### Test Case 1: Initial Evaluation Creates with Zero Score

**Objective:** Verify that new evaluations start with score=0 and status=pending_documents

**Steps:**
1. POST `/api/risk/evaluate` with valid client_nit
2. Verify response has:
   - `risk_score: 0.0`
   - `risk_level: "low"`
   - `status: "pending_documents"`
   - `fraud_indicators` contains `evaluation_pending` placeholder

**Expected Result:**
- Assessment created with preliminary score of 0
- No blacklist check performed
- No fraud indicator checks performed

**API Request:**
```json
POST /api/risk/evaluate
{
  "client_nit": "900123456"
}
```

**Expected Response:**
```json
{
  "id": "...",
  "assessment_id": "RISK-...",
  "client_nit": "900123456",
  "risk_score": 0.0,
  "risk_level": "low",
  "status": "pending_documents",
  "fraud_indicators": [
    {
      "indicator_name": "evaluation_pending",
      "indicator_value": false,
      "severity": "low",
      "evidence": "Evaluación pendiente - ejecute \"Finalizar Evaluación\" para calcular el puntaje de riesgo",
      "score_impact": 0.0
    }
  ]
}
```

### Test Case 2: Cross-Validation Updates Status to pending_finalization

**Objective:** Verify that running cross-validation changes status to pending_finalization without calculating score

**Steps:**
1. Create evaluation with pending_documents status
2. Upload at least 2 documents (e.g., RUT and Financial Statement)
3. Process extractions
4. POST `/api/risk/evaluations/{id}/cross-validate`
5. Verify response and assessment status

**Expected Result:**
- Cross-validation results returned
- Assessment status updated to `pending_finalization`
- Risk score still at 0 (NOT recalculated)

### Test Case 3: Finalization Status Endpoint Returns Requirements

**Objective:** Verify the finalization-status endpoint correctly reports requirements

**Steps:**
1. GET `/api/risk/evaluations/{id}/finalization-status`
2. Verify response contains:
   - `can_finalize`: boolean based on requirements
   - `requirements`: object with completion status
   - `pending_items`: list of incomplete items

**API Request:**
```
GET /api/risk/evaluations/{id}/finalization-status
```

**Expected Response (requirements met):**
```json
{
  "assessment_id": "RISK-...",
  "can_finalize": true,
  "requirements": {
    "cross_validation_done": true,
    "email_chains_validated": true,
    "external_contacts_validated": true,
    "min_documents_met": true
  },
  "pending_items": [],
  "current_status": "pending_finalization"
}
```

**Expected Response (requirements not met):**
```json
{
  "assessment_id": "RISK-...",
  "can_finalize": false,
  "requirements": {
    "cross_validation_done": false,
    "email_chains_validated": true,
    "external_contacts_validated": true,
    "min_documents_met": false
  },
  "pending_items": [
    "Ejecutar validación cruzada de documentos",
    "Subir al menos 2 documentos (actual: 1)"
  ],
  "current_status": "pending_documents"
}
```

### Test Case 4: Finalize Evaluation Runs All Checks

**Objective:** Verify that POST /finalize runs blacklist check, fraud indicators, and calculates final score

**Steps:**
1. Create evaluation and complete cross-validation
2. POST `/api/risk/evaluations/{id}/finalize`
3. Verify response contains:
   - Updated `risk_score` (calculated from all indicators)
   - Updated `risk_level`
   - Final `status` (completed/pending/escalated/rejected)
   - `finalized_by` and `finalized_at` populated

**API Request:**
```json
POST /api/risk/evaluations/{id}/finalize
{
  "force_complete": false
}
```

**Expected Response:**
```json
{
  "id": "...",
  "assessment_id": "RISK-...",
  "risk_score": 35.5,
  "risk_level": "medium",
  "status": "pending",
  "finalized_by": "user-uuid",
  "finalized_at": "2024-12-24T...",
  "fraud_indicators": [
    { "indicator_name": "cross_validation_nit", "..." },
    { "..." }
  ]
}
```

### Test Case 5: Blacklist Match During Finalization

**Objective:** Verify that blacklist match during finalization results in immediate rejection

**Steps:**
1. Add client NIT to blacklist
2. Create evaluation for that client
3. Complete cross-validation
4. POST `/api/risk/evaluations/{id}/finalize`
5. Verify assessment is rejected

**Expected Result:**
- Status set to `rejected`
- Risk score set to 100.0
- Risk level set to `critical`
- `blacklist_match` indicator added
- Alert created for blacklist match

### Test Case 6: Force Complete Without Requirements

**Objective:** Verify that force_complete=true allows finalization without meeting all requirements

**Steps:**
1. Create evaluation with only 1 document (requirements not met)
2. POST `/api/risk/evaluations/{id}/finalize` with `force_complete: true`
3. Verify finalization proceeds

**API Request:**
```json
POST /api/risk/evaluations/{id}/finalize
{
  "force_complete": true
}
```

**Expected Result:**
- Finalization proceeds despite unmet requirements
- Score calculated based on available data

### Test Case 7: Frontend FKFinalizeButton Component

**Objective:** Verify the finalization button displays correct state and requirements

**Steps:**
1. Navigate to risk evaluation detail page
2. Verify FKFinalizeButton shows:
   - Requirements checklist with correct status
   - "Finalizar Evaluación" button enabled/disabled based on requirements
   - Confirmation dialog with force complete option

**UI Verification:**
- Checklist items show check/error icons correctly
- Button is disabled when requirements not met
- Force complete checkbox appears when requirements not met
- Success message shows after finalization

### Test Case 8: PDF Export Includes Finalization Info

**Objective:** Verify PDF export includes finalized_by and finalized_at fields

**Steps:**
1. Finalize an evaluation
2. Navigate to cross-validation tab
3. Click "Exportar PDF"
4. Verify PDF contains:
   - "Finalizado por:" field
   - "Fecha de finalización:" field

## Error Scenarios

### Error 1: Finalize on Invalid Status

**Steps:**
1. Try to finalize an already completed/approved/rejected evaluation
2. POST `/api/risk/evaluations/{id}/finalize`

**Expected Result:**
- HTTP 400 Bad Request
- Error message: "Cannot finalize evaluation in status '...'..."

### Error 2: Finalize Without Cross-Validation

**Steps:**
1. Create evaluation without running cross-validation
2. POST `/api/risk/evaluations/{id}/finalize` with `force_complete: false`

**Expected Result:**
- HTTP 400 Bad Request
- Error message about missing cross-validation

## Test Data

### Sample Client Data
```json
{
  "nit": "900123456",
  "nombre_importador": "Test Company S.A.S.",
  "representante_legal": "John Doe",
  "ciudad_domicilio": "Bogotá"
}
```

### Required Documents for Cross-Validation
1. RUT (rut)
2. Financial Statement Current (financial_statement_current)

## Cleanup

After tests complete:
1. Delete test assessments from `risk_assessments` table
2. Remove test blacklist entries
3. Clear test document extractions

## Notes

- This test validates the new deferred finalization workflow
- Blacklist checks are only run during finalization, not initial creation
- Score remains 0 until user explicitly clicks "Finalizar Evaluación"
- The feature allows users to review cross-validation results before fraud score is calculated
