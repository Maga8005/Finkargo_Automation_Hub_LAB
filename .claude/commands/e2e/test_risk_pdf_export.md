# E2E Test: Risk Evaluation PDF Export

Test the PDF export functionality for risk evaluations, ensuring the "Generar Reporte" button works correctly and generates a downloadable PDF.

## User Story

As a Risk Analyst
I want to export a comprehensive PDF report of a risk evaluation
So that I can share the evaluation results with stakeholders or archive them for compliance

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- An existing risk evaluation with cross-validation results

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
4. **Verify** risk dashboard loads with assessment list
5. Take a screenshot of the risk dashboard

### Phase 2: Select an Evaluation

6. Look for an existing evaluation in the list (any status)
7. Click on the evaluation to view details
8. **Verify** evaluation detail page loads with:
   - Risk score displayed
   - Risk level badge (low/medium/high/critical)
   - Fraud indicators section
9. Take a screenshot of evaluation detail page

### Phase 3: Locate and Click Generate Report Button

10. Scroll to find the "Generar Reporte" button (may be in Actions section or toolbar)
11. **Verify** the button is visible and enabled
12. Take a screenshot showing the report button

### Phase 4: Generate PDF Report

13. Click "Generar Reporte" button
14. Wait for PDF generation (may show loading spinner)
15. **Verify** NO error message appears (specifically NOT "Error al generar el reporte")
16. **Verify** NO browser console errors about "toFixed is not a function"
17. **Verify** PDF file downloads or browser shows download prompt
18. Take a screenshot after successful generation

### Phase 5: Verify PDF Content (if accessible)

19. If PDF opened in browser:
    - **Verify** PDF contains evaluation ID (RISK-YYYY-XXX format)
    - **Verify** PDF contains risk score
    - **Verify** PDF contains client NIT
20. Take a screenshot of PDF preview if available

## Success Criteria

- "Generar Reporte" button is visible and clickable
- Clicking the button does NOT produce any errors
- No "TypeError: assessment.risk_score.toFixed is not a function" in console
- PDF file is generated and downloads successfully
- PDF filename contains the assessment ID

## Screenshots Required

1. Risk dashboard with evaluation list
2. Evaluation detail page with risk score
3. Report generation button visible
4. Successful PDF download (no error)
5. PDF preview if accessible

## Error Scenarios to Verify Are FIXED

- **FIXED BUG**: Clicking "Generar Reporte" no longer throws TypeError
- **FIXED BUG**: No "Error al generar el reporte" message appears
- **FIXED BUG**: `risk_score.toFixed()` now works correctly with Number() wrapper

## Technical Notes

The bug was caused by `risk_score` being serialized as a string from the backend (Pydantic Decimal type). The fix wraps numeric values with `Number()` before calling `toFixed()`:
- `assessment.risk_score.toFixed(0)` → `Number(assessment.risk_score).toFixed(0)`
- `ind.score_impact.toFixed(0)` → `Number(ind.score_impact).toFixed(0)`
