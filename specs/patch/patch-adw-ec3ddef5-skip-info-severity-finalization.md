# Patch: Skip INFO Severity in Finalization Processing

## Metadata
adw_id: `ec3ddef5`
review_change_request: `"When clicking <Finalizar Evaluación> the frontend shows a 500 error. This also happens when clicking on <Validar> to validate a contact on the <Contactos Externos Individuales> feature"`

## Issue Summary
**Original Spec:** specs/issue-36-adw-ec3ddef5-sdlc_planner-fraud-risk-module-fixes.md
**Issue:** The `finalize_evaluation_complete` function in `fraud_detection_service.py` fails with a 500 error when processing cross-validation or email chain discrepancies with `severity: 'info'`. The `RiskLevel` enum does not include an 'info' value (only `low`, `medium`, `high`, `critical`), so `RiskLevel('info')` throws a ValueError which propagates as a 500 Internal Server Error.
**Solution:** Skip INFO-level discrepancies when building fraud indicators in `finalize_evaluation_complete()`. INFO-level items are informational (positive verification indicators, not issues) and should not be converted to fraud indicators.

## Files to Modify

- `backend/src/core/servicios/risk/fraud_detection_service.py` (lines 820-842) - Add severity filtering to skip INFO-level items when building indicators from cross-validation and email chain results

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add INFO severity filtering for cross-validation results
- In `finalize_evaluation_complete()` around line 821-829, add a check to skip items with `severity: 'info'`
- INFO-level items are positive verification indicators and should NOT be added as fraud indicators
- Implementation:
  ```python
  # Add cross-validation discrepancies as indicators
  for cv_result in cross_validation_results:
      # Skip INFO-level items (positive indicators, not discrepancies)
      severity_value = cv_result.get('severity', 'medium')
      if severity_value == 'info':
          continue
      if cv_result.get('is_discrepancy'):
          indicators.append(FraudIndicator(
              indicator_name=f"cross_validation_{cv_result.get('validation_type', 'unknown')}",
              indicator_value=True,
              severity=RiskLevel(severity_value),
              evidence=cv_result.get('description', 'Discrepancia en validación cruzada'),
              score_impact=Decimal(str(cv_result.get('score_impact', 0))),
          ))
  ```

### Step 2: Add INFO severity filtering for email chain discrepancies
- In `finalize_evaluation_complete()` around lines 831-842, add a check to skip discrepancies with `severity: 'info'`
- Implementation:
  ```python
  # Add email chain discrepancies as indicators (if provided)
  if email_chain_results:
      for chain in email_chain_results:
          validation_result = chain.get('validation_result', {})
          for disc in validation_result.get('discrepancies', []):
              # Skip INFO-level items (positive indicators, not discrepancies)
              severity_value = disc.get('severity', 'medium')
              if severity_value == 'info':
                  continue
              indicators.append(FraudIndicator(
                  indicator_name=f"email_chain_{disc.get('field', 'unknown')}",
                  indicator_value=True,
                  severity=RiskLevel(severity_value),
                  evidence=disc.get('description', 'Discrepancia en cadena de correo'),
                  score_impact=Decimal(str(disc.get('score_impact', 5))),
              ))
  ```

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd backend && ./venv/bin/ruff check src/core/servicios/risk/fraud_detection_service.py` - Validate code quality
2. `cd backend && python -m pytest -v --tb=short` - Run all backend tests
3. `cd frontend && npm run lint` - Validate frontend linting
4. `cd frontend && npx tsc --noEmit` - Validate TypeScript types
5. `cd frontend && npm run build` - Validate frontend build

## Patch Scope
**Lines of code to change:** ~10 lines (adding 4 lines for cross-validation filter, 4 lines for email chain filter)
**Risk level:** low
**Testing required:** Run backend pytest to verify finalization works with INFO-level discrepancies; manual test of "Finalizar Evaluación" button
