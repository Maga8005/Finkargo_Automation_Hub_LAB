# E2E Test: Database Existence Check Removal from Risk Score

Test that the database existence check (company history) no longer contributes to the risk score calculation.

## User Story

As a Risk Analyst
I want new customers (without previous evaluations) to NOT have inflated risk scores due to "no history"
So that the risk score accurately reflects only document cross-validation results

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- A test NIT that has NEVER been evaluated before (new customer)

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Phase 1: Verify API Response for New Customer

1. Log in with risk analyst credentials
2. Navigate to Risk Dashboard (/department/riesgo)
3. Click "Nueva Evaluacion" button
4. Enter a NIT for a customer that has NEVER been evaluated before
5. Submit the evaluation
6. **Verify** the API response (check network tab) shows:
   - `company_history` indicator with `indicator_value: false`
   - `company_history` indicator with `score_impact: 0`
   - Evidence text should be "Primera evaluacion para este cliente" (informational only)
7. Take a screenshot of the network response showing the indicator values

### Phase 2: Verify Preliminary Score

8. **Verify** the preliminary risk score is 0 or only reflects other triggered document-based rules
9. **Verify** the `company_history` indicator does NOT appear as a "triggered" risk factor in the UI
10. Take a screenshot of the evaluation details showing the indicators list

### Phase 3: Verify Score After Cross-Validation

11. Upload at least 2 documents (e.g., RUT and Financial Statement)
12. Run document extraction
13. Run cross-validation
14. **Verify** the final risk score:
    - If no discrepancies found: score should remain at 0 (or baseline)
    - If discrepancies found: score should only reflect cross-validation impacts
    - Company history should NOT be a factor in either case
15. Take a screenshot of the final risk score

### Phase 4: Compare with Returning Customer (Optional)

16. Create a new evaluation for a customer that HAS been evaluated before
17. **Verify** the `company_history` indicator still shows `indicator_value: false` and `score_impact: 0`
18. Evidence should show "Historial: X evaluaciones previas" (informational)
19. **Verify** there is NO score difference due to history between new and returning customers

## Success Criteria

- New customer evaluations do NOT get score impact from "no history"
- `company_history` indicator always has:
  - `indicator_value: false`
  - `score_impact: 0`
- Preliminary risk score is 0 when no other rules trigger
- Only document cross-validation results affect the final risk score
- The "company_history" indicator provides informational evidence only

## Expected Indicator Response

For a new customer (no previous evaluations):
```json
{
  "indicator_name": "company_history",
  "indicator_value": false,
  "severity": "low",
  "evidence": "Primera evaluacion para este cliente",
  "score_impact": 0
}
```

For a returning customer (with previous evaluations):
```json
{
  "indicator_name": "company_history",
  "indicator_value": false,
  "severity": "low",
  "evidence": "Historial: 3 evaluaciones previas",
  "score_impact": 0
}
```

## Screenshots Required

1. Network response showing company_history indicator values
2. Evaluation details showing indicators list (company_history not triggered)
3. Final risk score after cross-validation
4. (Optional) Comparison between new and returning customer scores

## Error Scenarios to Note

- If company_history shows `indicator_value: true`, the bug was NOT fixed
- If company_history shows `score_impact > 0`, the bug was NOT fixed
- If preliminary score is > 0 without any other triggered rules, investigate source

## Related Files

- `backend/src/core/servicios/risk/fraud_detection_service.py` - Contains the `_check_company_history` method
- `backend/tests/test_fraud_detection_service.py` - Contains unit tests for this behavior
