# Bug: Fraud Status Checklist Shows Incorrect Completion for Email Chains and External Contacts

## Bug Description
When a user navigates to the Fraud Risk module and enters a NIT to start a new validation, the system immediately flags "Cadenas de correo" (email chains) and "Contactos externos" (external contacts) as "Completado" (completed) in the "Requisitos para Finalización" (Finalization Requirements) checklist. This is incorrect because the user has not yet uploaded or validated any email chains or external contacts - the process hasn't even started.

**Observed behavior:** Both "Cadenas de correo validadas" and "Contactos externos validados" show green checkmarks with "Completado" status immediately when starting a new evaluation.

**Expected behavior:** These items should show as "Opcional" (Optional) or "No iniciado" (Not started) when there are 0 items of each type, and only show as "Completado" once validation has actually been performed via the "Contacto Externo" tab.

## Problem Statement
The finalization requirements logic incorrectly treats "no items exist" (`count == 0`) as "all items validated", which is semantically incorrect. When there are no email chains or external contacts uploaded, the frontend displays them as "Completado" because the backend returns `email_chains_validated: true` and `external_contacts_validated: true`.

## Solution Statement
Modify the logic in `FraudDetectionService.get_finalization_status()` to return `false` for `email_chains_validated` and `external_contacts_validated` when there are no items of that type. Additionally, update the frontend `FKFinalizeButton.tsx` component to distinguish between "no items uploaded" (optional/not started) vs "all items validated" (completed) states and display appropriate status text.

## Steps to Reproduce
1. Navigate to the Fraud Risk module at `/risk/dashboard`
2. Enter a valid NIT to start a new evaluation
3. Once the evaluation is created, navigate to the evaluation detail page
4. Observe the "Requisitos para Finalización" checklist in the `FKFinalizeButton` component
5. Note that "Cadenas de correo validadas" and "Contactos externos validados" both show as "Completado" with green checkmarks despite no items being uploaded or validated

## Root Cause Analysis
The bug originates in the backend service `FraudDetectionService.get_finalization_status()` in `backend/src/core/servicios/risk/fraud_detection_service.py` at lines 955-965:

```python
requirements = FinalizationRequirements(
    cross_validation_done=cross_validation_count > 0,
    email_chains_validated=(
        email_chain_count == 0 or  # <-- BUG: "no items" treated as "validated"
        email_chain_validated_count >= email_chain_count
    ),
    external_contacts_validated=(
        external_contact_count == 0 or  # <-- BUG: "no items" treated as "validated"
        external_contact_validated_count >= external_contact_count
    ),
    min_documents_met=document_count >= min_documents_required,
)
```

The logic `email_chain_count == 0` returns `True` when there are zero email chains, which the frontend interprets as "validated/completed". The same issue exists for `external_contact_count == 0`.

The frontend component `FKFinalizeButton.tsx` at lines 199-225 renders these boolean values directly without distinguishing between "none to validate" and "all validated".

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [x] Frontend: components

## Relevant Files
Use these files to fix the bug:

- **`backend/src/core/servicios/risk/fraud_detection_service.py`** (lines 917-998): Contains the `get_finalization_status()` method where the incorrect logic resides. The `FinalizationRequirements` object is constructed with the flawed boolean logic.

- **`backend/src/interface/risk_dtos.py`** (lines 715-730): Contains the `FinalizationRequirements` and `FinalizationStatusResponse` DTOs. Need to add new fields to track counts so frontend can distinguish between "none" and "validated".

- **`frontend/src/types/risk.ts`**: Contains TypeScript types for `FinalizationRequirements` and `FinalizationStatus`. Need to add corresponding count fields.

- **`frontend/src/components/risk/FKFinalizeButton.tsx`** (lines 199-225): Contains the requirements checklist rendering. Need to update to show "Opcional" when count is 0 instead of "Completado".

- **`backend/src/adapter/rest/risk_routes.py`** (lines 1264-1328): Contains the `get_finalization_status` endpoint. Already passes counts to the service, just need to ensure they're returned to frontend.

### New Files
- **`.claude/commands/e2e/test_fraud_checklist_status.md`**: E2E test file to validate the bug fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update Backend DTOs to Include Counts
- Read `backend/src/interface/risk_dtos.py`
- Add the following fields to `FinalizationRequirements`:
  - `email_chain_count: int` - Total number of email chains
  - `email_chain_validated_count: int` - Number of validated email chains
  - `external_contact_count: int` - Total number of external contacts
  - `external_contact_validated_count: int` - Number of validated external contacts
- These fields allow the frontend to determine if "none exist" vs "all validated"

### Step 2: Update Backend Service Logic
- Read `backend/src/core/servicios/risk/fraud_detection_service.py`
- Modify `get_finalization_status()` method (around line 955) to:
  - Change `email_chains_validated` logic to: Only return `True` if `email_chain_count > 0 AND email_chain_validated_count >= email_chain_count`
  - Change `external_contacts_validated` logic to: Only return `True` if `external_contact_count > 0 AND external_contact_validated_count >= external_contact_count`
  - Include the counts in the `requirements` dict returned

### Step 3: Update Backend Route to Pass Counts
- Read `backend/src/adapter/rest/risk_routes.py`
- Verify the `get_finalization_status` endpoint (lines 1264-1328) correctly passes counts from the service to the response
- Ensure `FinalizationRequirements` includes the new count fields in the response

### Step 4: Update Frontend Types
- Read `frontend/src/types/risk.ts`
- Add the following optional fields to `FinalizationRequirements` interface:
  - `email_chain_count?: number`
  - `email_chain_validated_count?: number`
  - `external_contact_count?: number`
  - `external_contact_validated_count?: number`

### Step 5: Update Frontend Component Display Logic
- Read `frontend/src/components/risk/FKFinalizeButton.tsx`
- Modify the checklist rendering (lines 199-225) to:
  - For "Cadenas de correo validadas" (email chains):
    - If `email_chain_count === 0`: Show yellow warning icon with "Opcional" or "No hay cadenas" as secondary text
    - If `email_chain_count > 0 && email_chains_validated === true`: Show green check with "Completado"
    - If `email_chain_count > 0 && email_chains_validated === false`: Show red error icon with "Pendiente ({validated}/{total})"
  - Apply same logic for "Contactos externos validados" (external contacts)

### Step 6: Create E2E Test File
- Read `.claude/commands/e2e/test_fraud_risk_module_fixes.md` and `.claude/commands/test_e2e.md` to understand the E2E test format
- Create a new E2E test file at `.claude/commands/e2e/test_fraud_checklist_status.md` that validates:
  1. When creating a new evaluation, "Cadenas de correo validadas" shows "Opcional" (not "Completado")
  2. When creating a new evaluation, "Contactos externos validados" shows "Opcional" (not "Completado")
  3. After adding and validating an email chain, the status changes to "Completado"
  4. After adding and validating an external contact, the status changes to "Completado"
- Include screenshots to prove the fix works

### Step 7: Run Validation Commands
- Execute all validation commands to ensure the bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Pre-fix Verification (Reproduce Bug)
```bash
# Start the application (if not already running)
cd /mnt/c/Users/guill/danke_apps/fkhub/lab-automation-hub-amplify && ./scripts/start.sh

# Manually navigate to the Fraud Risk module, create a new evaluation, and observe the checklist shows "Completado" for email chains and external contacts (this confirms the bug)
```

### Post-fix Verification
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_fraud_checklist_status.md` E2E test file to validate the bug is fixed

### Automated Tests
```bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

## Notes
- The fix requires changes to both backend (DTO and service) and frontend (types and component)
- The "email chains" and "external contacts" validations are **optional** for finalization - users can force-complete even without them. The fix ensures the status is displayed correctly, not that these become required.
- The current logic `email_chain_count == 0 or validated_count >= count` evaluates to `True` when count is 0, which is the semantic bug. The fix changes this to only return `True` when there are actually items that have been validated.
- No database migrations required - this is purely a logic/display fix
- Consider adding a third state in the future: "not_started" vs "in_progress" vs "completed", but for now, distinguishing between "none/optional" and "completed" is sufficient for the bug fix
