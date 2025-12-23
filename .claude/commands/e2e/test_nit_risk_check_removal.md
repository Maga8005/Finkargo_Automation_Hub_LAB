# E2E Test: NIT Database Existence Check and Evaluation Type Removal

Test that the NIT database existence check no longer assigns a risk score of 75, and that the evaluation type dropdown has been removed from the UI.

## User Story

As a Risk Analyst
I want new customers (NIT not in database) to NOT receive an automatic risk score of 75
So that risk scores are assigned ONLY after document cross-validation

## Bug Fixes Validated

1. **Evaluation Type Selection Removed**: The UI no longer shows "Completa" (comprehensive) or "Rapida" (quick) evaluation options. There is only one workflow.

2. **NIT Database Check Removed**: When entering a NIT that does NOT exist in the database, the system no longer creates an error assessment with risk_score=75 and system_error indicator.

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- A test NIT that does NOT exist in the database (e.g., "999.999.999-9")

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Phase 1: Verify Evaluation Type Dropdown Removed

1. Log in with risk analyst credentials
2. Navigate to Risk Dashboard (/department/riesgo)
3. Click "Nueva Evaluacion" button
4. **Verify** the evaluation form is displayed
5. **Verify** there is NO dropdown for "Tipo de Evaluacion"
6. **Verify** only the NIT input field and submit button are present
7. Take a screenshot of the evaluation form (showing no dropdown)

### Phase 2: Verify New Client Assessment with Zero Score

8. Enter a NIT that does NOT exist in the database (e.g., "999.999.999-9")
9. Click "Iniciar Evaluacion" button
10. **Verify** the API response (check network tab) shows:
    - `risk_score: 0` (NOT 75)
    - `risk_level: "low"` (NOT "high")
    - `status: "pending_documents"`
    - `fraud_indicators` contains `new_client` indicator with:
      - `indicator_name: "new_client"`
      - `indicator_value: false`
      - `score_impact: 0`
      - `evidence: "Nuevo cliente - pendiente validacion de documentos"`
11. **Verify** there is NO `system_error` indicator
12. Take a screenshot of the network response

### Phase 3: Verify UI Displays Correct Score

13. **Verify** the evaluation details page shows:
    - Risk score: 0 (or baseline with no high-risk indicators)
    - Risk level: Bajo (Low)
    - Status: Pendiente Documentos
14. **Verify** the UI allows user to proceed to document upload phase
15. Take a screenshot of the evaluation details

### Phase 4: Verify Document Upload Flow Available

16. Navigate to the evaluation details page
17. **Verify** document upload functionality is accessible
18. **Verify** the user can upload at least one document
19. Take a screenshot showing document upload is available

## Success Criteria

### Bug #1 Fix - Evaluation Type Removal
- No evaluation type dropdown is present in the form
- Form only contains NIT input field and submit button
- No reference to "Completa" or "Rapida" evaluation types

### Bug #2 Fix - NIT Database Check Removal
- New client (NIT not in database) gets `risk_score: 0`
- New client gets `risk_level: "low"`
- New client gets `status: "pending_documents"`
- No `system_error` indicator is present
- `new_client` indicator has `score_impact: 0`
- User can proceed to document upload workflow

## Expected API Response for New Client

```json
{
  "id": "uuid",
  "assessment_id": "RISK-2024-001",
  "client_nit": "999.999.999-9",
  "risk_level": "low",
  "risk_score": 0,
  "fraud_indicators": [
    {
      "indicator_name": "new_client",
      "indicator_value": false,
      "severity": "low",
      "evidence": "Nuevo cliente - pendiente validacion de documentos",
      "score_impact": 0
    }
  ],
  "status": "pending_documents",
  "assessment_type": "comprehensive",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Screenshots Required

1. Evaluation form showing NO evaluation type dropdown
2. Network response for new client showing risk_score=0
3. Evaluation details page showing low risk and pending_documents status
4. Document upload section available for the new client

## Error Scenarios to Note

- If an evaluation type dropdown is visible, Bug #1 was NOT fixed
- If risk_score is 75, Bug #2 was NOT fixed
- If status is "pending" instead of "pending_documents", check service logic
- If `system_error` indicator exists, the old error assessment is still being created
- If user cannot proceed to document upload, check status handling

## Comparison with Previous Behavior (Before Fix)

Before this fix:
```json
{
  "risk_level": "high",
  "risk_score": 75,
  "fraud_indicators": [
    {
      "indicator_name": "system_error",
      "indicator_value": true,
      "severity": "high",
      "evidence": "Cliente no encontrado en el sistema",
      "score_impact": 75
    }
  ],
  "status": "pending"
}
```

After this fix:
```json
{
  "risk_level": "low",
  "risk_score": 0,
  "fraud_indicators": [
    {
      "indicator_name": "new_client",
      "indicator_value": false,
      "severity": "low",
      "evidence": "Nuevo cliente - pendiente validacion de documentos",
      "score_impact": 0
    }
  ],
  "status": "pending_documents"
}
```

## Related Files

- `frontend/src/components/risk/FKRiskEvaluationForm.tsx` - Form component (dropdown removed)
- `frontend/src/types/risk.ts` - TypeScript types (AssessmentType removed)
- `backend/src/interface/risk_dtos.py` - DTOs (AssessmentType enum removed)
- `backend/src/adapter/rest/risk_routes.py` - Route handler (assessment_type removed)
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Service (new client handling)
