# Patch: Fix Evaluation Tab Order and Premature Status Display

## Metadata
adw_id: `abc1c57a`
review_change_request: `The "evaluación" page is still showing up first in the process when it should go last. Additionally, it is still showing a message "Aprobado" as soon as the NIT is entered. It should not provide a status until the whole workflow is completed.`

## Issue Summary
**Original Spec:** specs/issue-34-adw-abc1c57a-sdlc_planner-defer-fraud-checks-finalization.md
**Issue:** Two UX problems: (1) The "Evaluación" tab appears first instead of last in the workflow, (2) The verification status shows "APROBADO" immediately when a NIT is entered before any validation is complete
**Solution:** (1) Reorder tabs so "Evaluación" is last, (2) Add a new `pending` verification status that displays "PENDIENTE" instead of "APROBADO" for preliminary evaluations

## Files to Modify
Use these files to implement the patch:

1. `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Reorder tabs (Documents, Cross-Validation, External Contact, Evaluación)
2. `frontend/src/types/risk.ts` - Add `pending` to `VerificationStatus` type and `VERIFICATION_STATUS_CONFIG`
3. `frontend/src/components/risk/FKVerificationStatusCard.tsx` - Update to use new `pending` status for preliminary evaluations

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add `pending` verification status type
- Edit `frontend/src/types/risk.ts`
- Add `'pending'` to `VerificationStatus` union type: `export type VerificationStatus = 'pending' | 'pass' | 'requires_manual_verification';`
- Add `pending` entry to `VERIFICATION_STATUS_CONFIG`:
  ```typescript
  pending: {
    label: 'PENDIENTE',
    color: 'warning' as const,
    bgColor: '#FFF4E5',
    textColor: '#B86E00',
    icon: 'HourglassEmpty' as const,
  },
  ```
- Update `VerificationStatusConfig` interface to include `'HourglassEmpty'` in icon type

### Step 2: Update FKVerificationStatusCard to show pending status
- Edit `frontend/src/components/risk/FKVerificationStatusCard.tsx`
- Import `HourglassEmpty` icon if not already imported
- Update `StatusIcon` logic: when `isPreliminary` is true and `verificationStatus` is `pass`, use `HourglassEmpty` and show "PENDIENTE" label instead of "APROBADO"
- Override the displayed config when `isPreliminary` is true to show pending state
- Remove the duplicate "Verificación Pendiente" chip since the main status will show it

### Step 3: Reorder tabs in RiskEvaluationDetail
- Edit `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Reorder the `<Tab>` components so order is:
  1. Documents (index 0)
  2. Cross-Validation (index 1)
  3. External Contact (index 2)
  4. Evaluación (index 3) - LAST
- Update the tab content conditionals to match new indices:
  - `activeTab === 0` → Documents
  - `activeTab === 1` → Cross-Validation
  - `activeTab === 2` → External Contact
  - `activeTab === 3` → Evaluación (Grid with client info, verification status, decision)
- Set default `activeTab` to `0` (Documents) instead of current default (already is 0, but confirm Documents is now first)

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. `cd frontend && npm run lint` - Run frontend linting
2. `cd frontend && npx tsc --noEmit` - Run TypeScript type check
3. `cd frontend && npm run build` - Run frontend build to validate production compilation

## Patch Scope
**Lines of code to change:** ~50 lines
**Risk level:** low
**Testing required:** Manual verification that tabs appear in correct order (Documents → Cross-Validation → External Contact → Evaluación) and that new evaluations show "PENDIENTE" status instead of "APROBADO" until finalized
