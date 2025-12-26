# Patch: Make Email Chains Mandatory and Disable Finalization Until Complete

## Metadata
adw_id: `7e637553`
review_change_request: `The email chains or <Cadenas de correo> should be changed to mandatory. Additionally, there should not be a way to finalize the evaluation unless all the mandatory steps are completed. Please adjust the process so that the <Finalizar Evaluación> button is disabled until the mandatory steps <Documentos>, <Validación cruzada> and <Cadena de correos> are completed. Additionally, please remove this text as there shouldnt be a way to force evaluation as only after the mandatory steps are completed should the evaluation be run; text to remove <o use "Forzar Finalización" en el diálogo de confirmación.>`

## Issue Summary
**Original Spec:** specs/issue-40-adw-7e637553-sdlc_planner-fraud-status-checklist-fix.md
**Issue:** Email chains (Cadenas de correo) are currently optional, but should be mandatory. The "Finalizar Evaluación" button can be clicked even when mandatory steps are incomplete via "force complete" option. Users can see text suggesting they can force finalization which should be removed.
**Solution:**
1. Change email chain validation from optional to mandatory in backend logic
2. Update `can_finalize` calculation to require email chains (when they exist) to be validated
3. Disable the finalize button until all 3 mandatory steps are complete (Documentos, Validación cruzada, Cadena de correos)
4. Remove the "force finalization" option from the UI since mandatory steps cannot be skipped
5. Remove the helper text mentioning "Forzar Finalización"

## Files to Modify
Use these files to implement the patch:

- **`backend/src/core/servicios/risk/fraud_detection_service.py`** (lines 948-994): Update `require_email_chain_validation` to `True` and update `can_finalize` logic to include email chains
- **`frontend/src/components/risk/FKFinalizeButton.tsx`** (lines 290-354): Remove the "force finalization" text, checkbox, and dialog warning

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Make Email Chains Mandatory in Backend
- Read `backend/src/core/servicios/risk/fraud_detection_service.py`
- At line 949, change `require_email_chain_validation = False` to `require_email_chain_validation = True`
- At lines 991-994, update the `can_finalize` logic to include email chain validation:
  ```python
  can_finalize = (
      requirements.cross_validation_done and
      requirements.min_documents_met and
      (email_chain_count == 0 or requirements.email_chains_validated)
  )
  ```
  - Note: If there are no email chains uploaded (`email_chain_count == 0`), finalization is still allowed. But if email chains exist, they must ALL be validated.

### Step 2: Remove Force Finalization Option from Frontend
- Read `frontend/src/components/risk/FKFinalizeButton.tsx`
- Remove lines 290-294 (the helper text mentioning "Forzar Finalización"):
  ```tsx
  {!canFinalize && status && (
    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
      Complete los requisitos pendientes o use "Forzar Finalización" en el diálogo de confirmación.
    </Typography>
  )}
  ```
- Remove lines 337-355 (the force complete warning alert and checkbox in the dialog):
  ```tsx
  {!canFinalize && (
    <Box sx={{ mt: 2 }}>
      <Alert severity="warning" sx={{ mb: 1 }}>
        <Typography variant="body2">
          No se han completado todos los requisitos. Puede forzar la finalización si lo desea.
        </Typography>
      </Alert>
      <FormControlLabel
        control={
          <Checkbox
            checked={forceComplete}
            onChange={(e) => setForceComplete(e.target.checked)}
            color="warning"
          />
        }
        label="Forzar finalización sin completar requisitos opcionales"
      />
    </Box>
  )}
  ```
- Update line 365 button disabled logic from `disabled={!canFinalize && !forceComplete}` to simply `disabled={!canFinalize}`
- The button at line 279 already has `disabled={finalizing || (!canFinalize && !status)}` which is correct - when `canFinalize` is false, button is disabled

### Step 3: Update Button Disabled Logic at Main Finalize Button
- The main "Finalizar Evaluación" button at line 279 has:
  ```tsx
  disabled={finalizing || (!canFinalize && !status)}
  ```
  This allows clicking when status exists but canFinalize is false. Change to:
  ```tsx
  disabled={finalizing || !canFinalize}
  ```
  This ensures the button is disabled until all mandatory requirements are met.

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Backend linting:**
   ```bash
   cd backend && ./venv/bin/ruff check src/
   ```

2. **Backend tests:**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

3. **Frontend linting:**
   ```bash
   cd frontend && npm run lint
   ```

4. **TypeScript type check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend build:**
   ```bash
   cd frontend && npm run build
   ```

## Patch Scope
**Lines of code to change:** ~25 lines
**Risk level:** low
**Testing required:** Manual verification that the finalize button is disabled until Documentos, Validación cruzada, and Cadena de correos (when present) are all completed. Verify force finalization option is removed from UI.
