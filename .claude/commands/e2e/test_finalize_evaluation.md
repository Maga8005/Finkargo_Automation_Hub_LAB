# E2E Test: Finalize Evaluation

Test the finalization workflow for risk evaluations, ensuring the "Finalizar Evaluación" button works correctly and transitions the evaluation to a final state.

## User Story

As a Risk Analyst
I want to finalize a risk evaluation after cross-validation is complete
So that the final risk score is calculated with all fraud checks and the evaluation moves to a completed state

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- An existing evaluation with status `pending_finalization` or `pending_documents` with completed cross-validation
- Database migration `migration_add_verification_status_columns.sql` has been applied

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
4. **Verify** risk dashboard loads with stats and assessment list
5. Take a screenshot of the risk dashboard

### Phase 2: Select Evaluation Ready for Finalization

6. Look for an evaluation with status "Pendiente Finalización" (pending_finalization) or "Pendiente Documentos" (pending_documents)
7. If none exists, create a new evaluation:
   - Click "Nueva Evaluación" button
   - Enter test NIT (9014447631)
   - Click "Evaluar"
8. Click on the evaluation to view details
9. **Verify** evaluation detail page loads
10. Take a screenshot of evaluation detail page

### Phase 3: Locate Finalize Button

11. Scroll down to find the "Finalizar Evaluación" card
12. **Verify** the card displays:
    - Title "Finalizar Evaluación"
    - Requirements checklist (Documentos subidos, Validación cruzada ejecutada, etc.)
    - "Finalizar Evaluación" button
13. Take a screenshot of the finalization card

### Phase 4: Execute Finalization

14. If requirements are not met (red X icons), check "Forzar finalización" in the confirmation dialog
15. Click "Finalizar Evaluación" button
16. **Verify** confirmation dialog appears with:
    - Title "Confirmar Finalización"
    - List of actions that will be executed
    - Cancel and "Confirmar Finalización" buttons
17. Take a screenshot of the confirmation dialog
18. Click "Confirmar Finalización" button
19. Wait for finalization to complete (spinner shows "Finalizando...")

### Phase 5: Verify Successful Finalization

20. **Verify** success message appears: "Evaluación finalizada exitosamente"
21. **Verify** NO error message appears (specifically NOT "Error al finalizar la evaluación")
22. Take a screenshot of success message
23. **Verify** the evaluation status has changed to one of:
    - "Completado" (completed) for low risk
    - "Pendiente" (pending) for medium/high risk requiring review
    - "Escalado" (escalated) for critical risk
    - "Rechazado" (rejected) if blacklisted
24. Take a screenshot of the updated status

### Phase 6: Verify Updated Risk Score Display

25. **Verify** the risk score card now displays:
    - Final risk score (may have increased from preliminary)
    - Risk level badge (low/medium/high/critical)
    - NO "Puntaje Preliminar" indicator (it should be final now)
26. Take a screenshot of the final risk score display

### Phase 7: Verify Finalization Details

27. Check that finalization audit fields are displayed:
    - "Finalizado por" shows the current user's name
    - "Finalizado el" shows current date/time
28. **Verify** the "Finalizar Evaluación" card is no longer displayed (or shows "Evaluación ya finalizada")
29. Take a screenshot of the audit information

## Success Criteria

- Finalization button is visible and clickable for pending evaluations
- Confirmation dialog displays correctly
- Clicking "Confirmar Finalización" does NOT return a 500 error
- Success message "Evaluación finalizada exitosamente" appears
- Status transitions from pending_finalization/pending_documents to a final state
- Risk score and level are displayed correctly
- Finalization audit fields (finalized_by, finalized_at) are populated
- Alerts are created for high/critical risk evaluations

## Screenshots Required

1. Risk dashboard with evaluation list
2. Evaluation detail page before finalization
3. Finalization card with requirements checklist
4. Confirmation dialog
5. Success message after finalization
6. Updated evaluation status
7. Final risk score display
8. Finalization audit information

## Error Scenarios to Verify Are FIXED

- **FIXED BUG**: Clicking "Finalizar Evaluación" no longer returns 500 error
- **FIXED BUG**: No "Error al finalizar la evaluación" message appears
- Finalization properly updates all database columns without errors

## Rollback Verification

If the test fails with 500 error, verify that the database migration has been applied:
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'risk_assessments'
AND column_name IN ('verification_status', 'has_discrepancies', 'discrepancy_count');

-- Should return 3 rows
```
