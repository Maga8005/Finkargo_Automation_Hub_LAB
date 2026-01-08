# Implementation: Fix PA Report Download Screen Disappearing

## Metadata
- **Date:** 2026-01-02
- **Patch ID:** adw-b13fe784
- **Issue:** #69
- **Module:** Finance (PA Report)

## Summary

Fixed an issue where the PA Report download UI (showing stats and download buttons) would appear briefly then disappear after cleaning and classification steps complete.

## Root Cause

The `ReportePA.tsx` component uses Material-UI's vertical Stepper with `StepContent`. The problem was:

1. **Clean step (index 1)**: After `cleanData()` succeeded, `setActiveStep(2)` was called which collapsed Step 1's `StepContent`, hiding the download button.

2. **Classify step (index 2)**: After `classifyData()` succeeded, `setActiveStep(3)` was called. Since there are only 3 steps (indices 0-2), setting `activeStep=3` collapsed all `StepContent` sections.

## Changes Made

- **Removed automatic step advancement** in `handleClean` - no longer calls `setActiveStep(2)` after successful cleaning
- **Removed automatic step advancement** in `handleClassify` - no longer calls `setActiveStep(3)` after successful classification
- **Added "Continuar a Clasificar" button** after the clean step download button, allowing users to explicitly advance to the classification step when ready
- Results and download buttons now remain visible after each processing step completes

## Discrepancies Found

None. The plan accurately described the issue and solution.

## Validation

All validation commands passed:

1. **TypeScript Check**: `npx tsc --noEmit` - No errors
2. **Frontend Linting**: `npm run lint` - No errors (only pre-existing warnings)
3. **Frontend Build**: `npm run build` - Successful

## Files Changed

```
frontend/src/pages/finance/ReportePA.tsx | 32 +++++++++++++++++++++-----------
1 file changed, 21 insertions(+), 11 deletions(-)
```

## User Experience Impact

Before:
- Download buttons appeared for a split second then disappeared
- Users could not download processed files

After:
- Clean step: Results and download button remain visible; "Continuar a Clasificar" button advances to next step
- Classify step: Results and download button remain visible; "Nuevo Reporte" button resets the workflow
