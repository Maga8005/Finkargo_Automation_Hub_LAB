# E2E Test: Verification Status Shows Correct Status When Fraud Alerts Are Triggered

Test that the verification status correctly shows "FALLIDO-REQUIERE REVISION" when fraud indicators are triggered, and "APROBADO" only when there are zero alerts AND zero cross-validation discrepancies.

## User Story

As a Risk Analyst
I want to see the correct verification status based on fraud alerts
So that I know which evaluations require manual verification before approval

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- A finalized risk evaluation with triggered fraud indicators (e.g., RISK-2025-023)
- A finalized risk evaluation with zero alerts AND zero discrepancies (for comparison)

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Phase 1: Login and Navigate to Risk Dashboard

1. Navigate to the Application URL (http://localhost:5173)
2. Log in with risk analyst credentials
3. Navigate to Risk Dashboard (/department/riesgo)
4. **Verify** risk dashboard loads with evaluation list
5. Take a screenshot of the risk dashboard

### Phase 2: Open Evaluation with Triggered Fraud Indicators

6. Look for evaluation RISK-2025-023 (or any finalized evaluation with "Alertas Detectadas" > 0)
7. Click on the evaluation to view details
8. **Verify** evaluation detail page loads
9. Take a screenshot of evaluation detail page

### Phase 3: Verify Fraud Indicators Section

10. Scroll to the "Indicadores de Fraude" section
11. **Verify** the "Alertas Detectadas" box shows a number greater than 0 (e.g., "2 Alertas Detectadas")
12. **Verify** at least one indicator has a red checkmark or alert icon indicating it was triggered
13. Take a screenshot of the fraud indicators section

### Phase 4: Verify Verification Status Shows FALLIDO-REQUIERE REVISION

14. Locate the "Estado de Verificacion" field in the evaluation header or summary
15. **Verify** the status shows "FALLIDO-REQUIERE REVISION" (red warning icon)
16. **Verify** the status does NOT show "APROBADO" (which would be a bug)
17. Take a screenshot showing the verification status

### Phase 5: Generate PDF Report and Verify Status

18. Click "Generar Reporte" button to export comprehensive PDF
19. Wait for PDF to generate and download
20. **Verify** no error message appears
21. Open the downloaded PDF
22. Locate the "RESULTADO DE EVALUACION" section
23. **Verify** PDF shows "RESULTADO DE EVALUACION: FALLIDO-REQUIERE REVISION" (red background)
24. **Verify** PDF does NOT show "APROBADO" (which would be a bug)
25. Take a screenshot of the PDF verification status

### Phase 6: Compare with Clean Evaluation (Optional)

26. Return to Risk Dashboard
27. Find an evaluation with 0 alerts AND 0 cross-validation discrepancies
28. Click to view details
29. **Verify** verification status shows "APROBADO" (green checkmark)
30. This confirms the logic is working correctly for both cases
31. Take a screenshot of the clean evaluation status

## Success Criteria

- Evaluations with ANY triggered fraud indicator (indicator_value=True) show "FALLIDO-REQUIERE REVISION"
- The status is displayed with a red warning indicator
- PDF export shows "RESULTADO DE EVALUACION: FALLIDO-REQUIERE REVISION" in red
- Evaluations with 0 alerts AND 0 discrepancies show "APROBADO" in green
- Status is consistent between UI and PDF report

## Screenshots Required

1. Risk dashboard with evaluation list
2. Evaluation detail page header
3. Fraud indicators section showing triggered alerts
4. Verification status showing "FALLIDO-REQUIERE REVISION"
5. PDF report showing correct status
6. (Optional) Clean evaluation showing "APROBADO"

## Error Scenarios to Verify Are FIXED

- **FIXED BUG**: Verification status no longer shows "APROBADO" when fraud indicators are triggered
- **FIXED BUG**: PDF report correctly reflects the verification status
- **FIXED BUG**: `_compute_verification_info_async` now checks fraud indicators, not just cross-validation discrepancies

## Technical Notes

The bug was caused by `_compute_verification_info_async` only checking cross-validation discrepancies. The fix:
1. Uses stored `verification_status` from database if available (set during finalization)
2. If not stored, computes from BOTH fraud indicators AND cross-validation discrepancies
3. Returns `REQUIRES_MANUAL_VERIFICATION` if ANY alert is triggered OR ANY discrepancy exists

Relevant code:
- `backend/src/adapter/rest/risk_routes.py` - `_compute_verification_info_async` function
- `backend/src/core/servicios/risk/fraud_detection_service.py` - finalization logic (lines 866-874)
- `frontend/src/types/risk.ts` - `VERIFICATION_STATUS_CONFIG` for status labels

## Verification Status Values

| Status Value | Display Label | Color | When Used |
|--------------|---------------|-------|-----------|
| `pass` | APROBADO | Green | 0 alerts AND 0 discrepancies |
| `requires_manual_verification` | FALLIDO-REQUIERE REVISION | Red | ANY alert OR ANY discrepancy |
