# E2E Test: Risk Score After Cross-Validation

Test the two-phase risk scoring workflow where final risk score is calculated after document cross-validation completes.

## User Story

As a Risk Analyst
I want the risk score to be calculated after all document cross-validation checks are complete
So that the final risk assessment incorporates discrepancies found between documents for a more accurate fraud detection

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- Test client data available in Supabase (NIT: 9014447631)

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

1. Navigate to the Application URL (http://localhost:5173)
2. Log in with risk analyst credentials
3. Navigate to Risk Dashboard (/department/riesgo)
4. **Verify** risk dashboard loads with stats and assessment list
5. Take a screenshot of the risk dashboard

### Phase 1: Create New Evaluation

6. Click "Nueva Evaluación" button to open evaluation dialog
7. Enter test NIT (9014447631) in the NIT field
8. Click "Evaluar" to create the evaluation
9. Wait for evaluation to complete
10. **Verify** new evaluation appears in the list with:
    - Status showing "Pendiente Documentos" (pending_documents)
    - Risk score displayed with "Puntaje Preliminar" indicator
11. Take a screenshot showing the preliminary score indicator
12. Click on the new evaluation to view details

### Phase 2: Verify Preliminary Score UI

13. **Verify** the evaluation detail page shows:
    - Risk score card with "Puntaje Preliminar" badge
    - Tooltip explaining "El puntaje final se calculará después de la validación cruzada de documentos"
    - Status chip showing "Pendiente Documentos"
    - Alert message: "Suba y valide documentos para calcular el puntaje final de riesgo"
14. Take a screenshot of the evaluation detail showing preliminary indicator
15. Navigate to "Documentos" tab

### Phase 3: Upload Documents

16. **Verify** document uploader shows alert: "Suba documentos y ejecute la validación cruzada para calcular el puntaje final de riesgo"
17. Upload at least 2 documents:
    - Financial Statement (current year)
    - RUT document
18. Wait for upload to complete
19. **Verify** documents appear in the list with "Pendiente" extraction status
20. Take a screenshot of uploaded documents

### Phase 4: Process Extraction

21. Click "Procesar Extracción" button
22. Wait for extraction to complete (polling or auto-refresh)
23. **Verify** extraction status changes to "Completado" for uploaded documents
24. Take a screenshot of completed extractions

### Phase 5: Run Cross-Validation

25. Navigate to "Validación Cruzada" tab or section
26. **Verify** cross-validation button is enabled (2+ documents processed)
27. Click "Ejecutar Validación Cruzada" button
28. Wait for validation to complete
29. **Verify** cross-validation results appear with:
    - Discrepancy count
    - Score impact values
    - Severity indicators
30. Take a screenshot of cross-validation results

### Phase 6: Verify Final Score Update

31. **Verify** success message appears: "Puntaje de riesgo actualizado con resultados de validación cruzada"
32. Navigate back to "Evaluación" tab
33. **Verify** the following changes occurred:
    - Risk score card NO LONGER shows "Puntaje Preliminar" badge
    - Status changed from "pending_documents" to appropriate status
    - Risk score may have changed (if discrepancies added score impact)
    - Risk level reflects the updated score
34. Take a screenshot of the final updated risk score
35. **Verify** if discrepancies were found, the final score >= preliminary score

### Phase 7: Verify Alerts (Optional)

36. Navigate to alerts section or check notification indicator
37. **Verify** if risk level is high/critical, an alert was created
38. Take a screenshot of any alerts created

## Success Criteria

- New evaluation starts with status "pending_documents"
- Preliminary score is clearly indicated with badge/chip
- User guidance messages appear at each stage
- Cross-validation triggers final score calculation
- Final score incorporates cross-validation score impacts
- Status transitions from "pending_documents" to final status
- UI updates to reflect final (non-preliminary) score
- Alerts are only created after final scoring (for high/critical)

## Screenshots Required

1. Risk dashboard before creating evaluation
2. Evaluation list showing preliminary score indicator
3. Evaluation detail with preliminary badge and guidance
4. Document uploader with pending documents alert
5. Completed document extractions
6. Cross-validation results with discrepancies
7. Final risk score after cross-validation (no preliminary badge)

## Error Scenarios to Note

- Creating evaluation for non-existent NIT should show error
- Cross-validation with <2 documents should be disabled
- Network errors during extraction should be handled gracefully
- Timeout during AI extraction should show appropriate message
