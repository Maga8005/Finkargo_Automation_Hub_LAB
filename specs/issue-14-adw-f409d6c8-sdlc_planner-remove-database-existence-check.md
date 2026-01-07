# Bug: Remove Database Existence Check from Risk Score Calculation

## Bug Description
The riesgos (risk) module is currently checking whether a customer exists in the database and using this existence check as a risk factor in the preliminary score calculation. Specifically, the `_check_company_history` method in `fraud_detection_service.py` adds a risk indicator when a client has no previous assessments in the system, treating "first time customer" as a potential risk.

**Expected Behavior:** The risk score should only be calculated based on document data cross-checking after document extraction. The existence or absence of previous customer records in the database should NOT contribute to the risk score.

**Actual Behavior:** The system adds "Primera evaluación para este cliente - sin historial previo" as a risk indicator with a score impact when a customer has no previous assessments, artificially inflating the risk score for new customers.

## Problem Statement
The `_check_company_history` method treats "no previous assessments for this client" as a risk factor and adds to the preliminary risk score. This is incorrect behavior - at this time, only document data cross-checking (the comparison of extracted data from different documents like RUT, financial statements, bank certificates, etc.) should contribute to the final risk score.

## Solution Statement
Remove the database existence check (`_check_company_history`) from the fraud detection service's preliminary evaluation. The `company_history` rule type should either be:
1. Completely removed from the active fraud detection rules, OR
2. Modified to not trigger any score impact when there's no history

The cleanest solution is to skip the `_check_company_history` check entirely or make it return a non-triggering indicator, since the current business requirement is that only document cross-validation should affect the risk score.

## Steps to Reproduce
1. Log in as a risk analyst or risk manager
2. Navigate to `/department/riesgo` (Risk Dashboard)
3. Click "Nueva Evaluación" and enter a NIT for a customer that has never been evaluated before
4. Submit the evaluation
5. Observe that the preliminary risk score includes an indicator named "company_history" with evidence "Primera evaluación para este cliente - sin historial previo"
6. The score is artificially inflated due to this "no history" factor

## Root Cause Analysis
The root cause is in the `_check_company_history` method in `backend/src/core/servicios/risk/fraud_detection_service.py` (lines 391-419):

```python
async def _check_company_history(self, client_data: dict, rule: dict) -> FraudIndicator:
    """
    Check company history and time in business.
    Newer companies may pose higher risk.
    """
    issues = []

    # Check if there are previous assessments for this client
    previous = await self.risk_repo.get_recent_by_client(client_data.get('nit', ''), limit=10)

    if not previous:
        issues.append("Primera evaluación para este cliente - sin historial previo")
    # ...
```

This method:
1. Checks if there are previous risk assessments for the client
2. If no previous assessments exist, it adds an issue stating "first evaluation for this client - no previous history"
3. This triggers a score impact that is added to the preliminary risk score

According to the business requirement, the ONLY contributors to the risk score should be the cross-validation of document data extracted from uploaded documents (RUT, financial statements, bank certificates, etc.), NOT whether the customer has previous assessments in the system.

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/risk/fraud_detection_service.py` - Contains the `_check_company_history` method that performs the database existence check and adds it as a risk factor. This is the primary file to modify.
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Contains the scoring logic that calculates risk scores from indicators. Understanding this helps ensure the fix doesn't break scoring.
- `backend/src/interface/risk_dtos.py` - Contains the FraudIndicator DTO used by the service. May need to verify no changes are required.
- `backend/database/migration_create_risk_tables.sql` - Contains the fraud_detection_rules table structure. May need to deactivate the 'history' rule type.

### New Files
- `.claude/commands/e2e/test_database_existence_check_removal.md` - New E2E test file to validate that the database existence check no longer affects risk scores.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Understand the Current Implementation
- Read `backend/src/core/servicios/risk/fraud_detection_service.py` to understand how `_check_company_history` is called
- Verify that the method is called via `_run_all_checks` when rule_type == 'history'
- Confirm the issue by tracing how the score impact flows to the final score

### Step 2: Modify the `_check_company_history` Method
- In `backend/src/core/servicios/risk/fraud_detection_service.py`, modify the `_check_company_history` method to NOT add risk score impact for "no previous history"
- The method should always return a non-triggering indicator (indicator_value=False, score_impact=0) for the "no previous assessments" case
- Keep the method structure to avoid breaking existing code that may reference it
- The modified method should look like:
  ```python
  async def _check_company_history(self, client_data: dict, rule: dict) -> FraudIndicator:
      """
      Check company history and time in business.

      NOTE: Per business requirements, lack of previous assessments is NOT
      a risk factor. Only document cross-validation results should affect
      the risk score. This method now only provides informational data
      without triggering score impact.
      """
      # Get previous assessments for informational purposes only
      previous = await self.risk_repo.get_recent_by_client(client_data.get('nit', ''), limit=10)

      # Always return non-triggering indicator - no score impact
      # History information is informational only, not a risk factor
      return FraudIndicator(
          indicator_name="company_history",
          indicator_value=False,  # Never trigger as a risk factor
          severity=RiskLevel.LOW,
          evidence=f"Historial: {len(previous)} evaluaciones previas" if previous else "Primera evaluación para este cliente",
          score_impact=Decimal('0'),  # Zero impact - only cross-validation affects score
      )
  ```

### Step 3: Remove the "Cupo muy alto" Check
- In the same `_check_company_history` method, also remove the check for "Cupo muy alto para cliente sin historial" since this also depends on database existence
- The entire method should not contribute any score impact as per business requirements

### Step 4: Update Unit Tests (if they exist)
- Search for any existing tests related to `_check_company_history` or `company_history` indicator
- Update tests to reflect the new behavior where company history never triggers score impact

### Step 5: Create E2E Test File
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_risk_score_after_validation.md` to understand the E2E test file format
- Create a new E2E test file at `.claude/commands/e2e/test_database_existence_check_removal.md` that validates:
  - When a new customer (no previous evaluations) is evaluated, the "company_history" indicator should NOT contribute to the risk score
  - The preliminary risk score should be 0 (or only reflect other active rules that are document-based)
  - Only after cross-validation should the risk score increase based on document discrepancies
  - The test should verify that `company_history` indicator has `indicator_value: false` and `score_impact: 0`

### Step 6: Run Validation Commands
- Execute all validation commands to ensure the fix works correctly and there are no regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Backend Validation
```bash
# Run backend tests to validate bug fix with zero regressions
cd backend && python -m pytest tests/ -v

# Run backend linting
cd backend && ruff check src/

# Verify the code change compiles correctly
cd backend && python -c "from src.core.servicios.risk.fraud_detection_service import FraudDetectionService; print('Import successful')"
```

### Frontend Validation
```bash
# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

### E2E Test Validation
- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test file `.claude/commands/e2e/test_database_existence_check_removal.md` to validate this functionality works

### Manual Verification
1. Start the application (backend and frontend)
2. Log in as risk analyst
3. Create a new evaluation for a NIT that has never been evaluated
4. Verify the preliminary risk score is 0 (or only reflects document-based rules)
5. Verify the `company_history` indicator shows `indicator_value: false` with `score_impact: 0`
6. Verify only cross-validation results affect the final risk score

## Notes
- This is a minimal, surgical fix that only modifies the `_check_company_history` method behavior
- The method is kept in place (not removed) to avoid breaking any code that may reference it
- The indicator is still returned with informational evidence, but with no score impact
- An alternative approach would be to deactivate the 'history' rule in the database, but modifying the code ensures the behavior is correct regardless of rule configuration
- The fix aligns with the stated business requirement: "the contributors to the score should be the document data cross checking after the data extraction"
