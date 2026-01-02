# Patch: Fix PA Report Download Screen Disappearing

## Metadata
adw_id: `b13fe784`
review_change_request: `Both when finishing the clean up process and the classification process, a screen shows up for split second and then disappears. I assume this is where the download can be done, but it happens very fast and then goes away. The user is unable to do the export due to this.`

## Issue Summary
**Original Spec:** specs/issue-69-adw-b13fe784-sdlc_planner-pa-accounts-csv-semicolon-delimiter.md
**Issue:** The PA Report download UI (showing stats and download buttons) appears briefly then disappears after cleaning and classification steps complete. This is caused by MUI Stepper's `StepContent` component collapsing when `activeStep` advances beyond the current step.
**Solution:** Keep `activeStep` at the current step after processing completes (do not advance), so the `StepContent` remains visible with the download button. Only advance the step when the user explicitly clicks to proceed OR add a completion step that displays the download options.

## Root Cause Analysis

The `ReportePA.tsx` component uses Material-UI's vertical Stepper with `StepContent`. The issue:

1. **Clean step (index 1)**: After `cleanData()` succeeds, `setActiveStep(2)` is called (line 210). This collapses Step 1's `StepContent`, hiding the `cleanedPreview` and download button rendered inside it.

2. **Classify step (index 2)**: After `classifyData()` succeeds, `setActiveStep(3)` is called (line 234). Since there are only 3 steps (indices 0-2), setting `activeStep=3` collapses all `StepContent` sections.

The download buttons are rendered inside `StepContent`, so when the step advances, they immediately disappear.

## Files to Modify

- `frontend/src/pages/finance/ReportePA.tsx`: Fix the step progression logic to keep download UI visible

## Implementation Steps

### Step 1: Keep activeStep at current step after processing

Modify the `handleClean` and `handleClassify` functions to NOT advance the step after successful processing. The user should see the results and download button, then manually proceed.

In `handleClean` (around line 210):
- Remove: `setActiveStep(2);`
- The `cleanedPreview` state update is sufficient to show the results

In `handleClassify` (around line 234):
- Remove: `setActiveStep(3);`
- The `classifiedPreview` state update is sufficient to show the results

### Step 2: Add explicit "Continue" buttons to advance steps

Add a "Continuar" button after the download button that explicitly advances to the next step:

For Step 1 (Clean):
- Add a secondary button "Continuar a Clasificar" that calls `setActiveStep(2)`
- This button should only appear when `cleanedPreview` exists

For Step 2 (Classify):
- Add a "Ver Resumen Final" or just keep the download button visible
- Since this is the last processing step, no need to advance further
- Keep `activeStep` at 2 so the download button stays visible

### Step 3: Handle the completion state properly

When classification is complete:
- Keep `activeStep` at 2 (the classify step)
- The `classifiedPreview` section with stats and download button remains visible
- User can use the "Nuevo Reporte" button to reset

## Validation

Execute every command to validate the patch is complete with zero regressions.

1. **TypeScript Check**:
   ```bash
   cd frontend && npx tsc --noEmit
   ```

2. **Frontend Linting**:
   ```bash
   cd frontend && npm run lint
   ```

3. **Frontend Build**:
   ```bash
   cd frontend && npm run build
   ```

4. **Manual Testing** (if running locally):
   - Navigate to Finance > Reporte PA
   - Upload a NetSuite movements file
   - Click "Ejecutar Limpieza" - verify results and download button remain visible
   - Click "Continuar a Clasificar" to advance to next step
   - Click "Ejecutar Clasificacion" - verify results and download button remain visible
   - Click "Descargar Archivo Clasificado" - verify download works

## Patch Scope
**Lines of code to change:** ~15-20 lines
**Risk level:** Low
**Testing required:** Manual UI testing to verify download buttons remain visible after processing steps complete
