# E2E Test: Binary Pass/Fail System

Test the binary pass/fail risk verification system that replaces numeric scoring.

## User Story

As a Risk Analyst or Risk Manager
I want to see a simple PASS or FAIL indicator instead of a numeric score
So that I cannot justify passing a risky evaluation based on a numeric threshold and must always manually verify any discrepancies

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- At least one existing risk evaluation in the system (or ability to create one)

## Test Credentials

Use test account (configure in test environment):
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Part 1: Dashboard Binary Display

1. Navigate to the `Application URL` (http://localhost:5173)
2. Login with test credentials if required
3. Navigate to `/risk/dashboard`
4. Take a screenshot of the risk dashboard
5. **Verify** the metrics section shows:
   - "Aprobados" count (PASS count) - with green styling
   - "Requieren Verificación" count (REQUIRES_MANUAL_VERIFICATION count) - with red styling
6. **Verify** the evaluations data grid:
   - Has a "Verificación" column showing binary status chips
   - Does NOT show "Puntaje" column with numeric scores
   - Does NOT show "Nivel" column with risk levels (LOW/MEDIUM/HIGH/CRITICAL)
7. Take a screenshot of the data grid showing verification status column

### Part 2: Evaluation Detail - PASS Case

8. Click on a row in the data grid to navigate to an evaluation detail
9. Take a screenshot of the evaluation detail page
10. **Verify** the risk score card:
    - Does NOT display a circular progress with numeric score
    - Shows binary verification status indicator
    - If status is "APROBADO": displays green checkmark icon and "APROBADO" text
    - If status is "REQUIERE VERIFICACIÓN MANUAL": displays red warning icon

### Part 3: Evaluation Detail - REQUIRES VERIFICATION Case

11. If current evaluation shows PASS, find or create an evaluation with discrepancies
12. Navigate to an evaluation with discrepancies (REQUIRES_MANUAL_VERIFICATION status)
13. Take a screenshot showing the red verification status
14. **Verify** the verification status card shows:
    - Red warning icon
    - "REQUIERE VERIFICACIÓN MANUAL" label
    - Discrepancy count information
    - Acknowledgment checkbox or button
15. **Verify** the decision form is disabled until acknowledgment is provided
16. Check the acknowledgment checkbox/button
17. Take a screenshot after acknowledgment
18. **Verify** the decision form becomes enabled after acknowledgment

### Part 4: Cross-Validation Results Binary Display

19. Navigate to the "Validación Cruzada" tab
20. Take a screenshot of the cross-validation results
21. **Verify** after validation completes:
    - If no discrepancies: green banner with "APROBADO - Todos los datos son consistentes"
    - If discrepancies found: red banner with "REQUIERE VERIFICACIÓN MANUAL"
22. **Verify** score impact text does NOT show numeric points (hidden from UI)

### Part 5: Filter by Verification Status

23. Navigate back to `/risk/dashboard`
24. **Verify** filter options include verification_status filter
25. Select "Requiere Verificación" filter
26. Take a screenshot of filtered results
27. **Verify** only evaluations with requires_manual_verification status are shown

## Success Criteria

- No numeric risk scores (0-100) are displayed anywhere in the UI
- No risk level labels (LOW, MEDIUM, HIGH, CRITICAL) are displayed to users
- Binary pass/fail indicator shows "APROBADO" (green) or "REQUIERE VERIFICACIÓN MANUAL" (red)
- Dashboard metrics show pass/fail counts instead of risk level counts
- Data grid shows verification status column instead of score column
- Users must acknowledge reviewing discrepancies before making a decision on flagged evaluations
- Cross-validation results show binary outcome banner
- 8 screenshots are captured:
  1. Risk dashboard with metrics
  2. Data grid with verification status column
  3. Evaluation detail page (PASS case)
  4. Evaluation detail page (REQUIRES VERIFICATION case)
  5. Acknowledgment interaction
  6. Cross-validation results
  7. Filtered results by verification status
  8. Final state after complete flow

## Error Scenarios to Note

- If no evaluations exist, create a new one and verify initial state
- If no discrepancies exist after validation, the status should be PASS
- Network errors should be handled gracefully
- Session timeout should redirect back to login

## Notes

- This test validates the stakeholder requirement: "Yo no le metería puntaje... esto si da rojos, hay alguna información que no coincida, hay que ir a mirar y verificar manualmente."
- Internal score calculation is preserved for analytics but hidden from UI
- ANY discrepancy (regardless of severity) triggers REQUIRES_MANUAL_VERIFICATION
