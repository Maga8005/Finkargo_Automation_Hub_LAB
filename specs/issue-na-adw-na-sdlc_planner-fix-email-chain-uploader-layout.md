# Bug: Email Chain Uploader Layout Overlap Issues

## Bug Description
The email chain uploader component (`FKEmailChainUploader.tsx`) has layout alignment issues where:
1. The scrollbar on the right side of the page overlaps the "Subir" (Upload) button, making it partially unclickable
2. The example/placeholder text in the TextField visually overlaps with the "Subir Archivo" button area
3. The overall layout creates visual confusion between the mode toggle buttons and the TextField content

Expected behavior: All buttons should be fully visible and clickable, with proper spacing and no overlap from scrollbars or other elements.

Actual behavior: The "Subir" button is partially obscured by a scrollbar, and the layout appears misaligned with placeholder text bleeding into button areas.

## Problem Statement
The `FKEmailChainUploader` component has CSS/layout issues that prevent proper user interaction:
1. The "Subir" button at the bottom-right is overlapped by the page/parent scrollbar
2. The mode toggle buttons and TextField content areas are not clearly separated visually
3. Users cannot reliably click the upload button due to the scrollbar overlap

## Solution Statement
Fix the layout issues by:
1. Adding right margin/padding to the button container to prevent scrollbar overlap
2. Ensuring the Card component has proper positioning (`position: relative`) to establish a stacking context
3. Adding clear visual separation between the mode toggle buttons and the TextField
4. Ensuring the "Subir" button container has proper z-index and spacing

## Steps to Reproduce
1. Navigate to the Risk module (/risk)
2. Open any risk evaluation detail page
3. Go to the "Contacto Externo" tab
4. Expand the "Cadenas de Email" accordion section
5. Observe that "Pegar Texto" mode is selected by default
6. Notice the scrollbar on the right overlaps the "Subir" button
7. Try to click the "Subir" button - it may not respond due to scrollbar overlap

## Root Cause Analysis
The root causes of this bug are:

1. **Missing right margin on button container**: The `Box` containing the "Subir" button (line 300) uses `justifyContent: 'flex-end'` which pushes the button to the far right edge, where it can be obscured by any parent scrollbar.

2. **No stacking context on Card**: The Card component doesn't establish a proper stacking context, allowing external scrollbars to render on top of its content.

3. **Dense layout without clear separation**: The mode toggle buttons are placed directly above the TextField with only `mb: 2` spacing, which can create visual confusion especially with the multiline placeholder text.

4. **TextField with long placeholder**: The placeholder text spans multiple lines and starts immediately after the mode buttons, creating visual proximity issues.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Main component with layout issues. The fix needs to adjust:
  - Line 252: Card component - add `position: relative` and possibly `zIndex`
  - Line 260-277: Mode toggle buttons Box - ensure proper spacing
  - Line 298: TextField `sx` prop - ensure proper margins
  - Line 300-309: Subir button container Box - add right margin to prevent scrollbar overlap
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - E2E test format example
- `.claude/commands/e2e/test_email_chain_validation.md` - Existing E2E test to update for layout verification

### New Files
- `.claude/commands/e2e/test_email_chain_uploader_layout.md` - New E2E test file to verify the layout fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix Card Component Positioning
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Modify the Card component (line 252) to add proper positioning:
  ```tsx
  <Card sx={{ mb: 3, position: 'relative', zIndex: 1 }}>
  ```
- This establishes a stacking context so internal elements aren't affected by external scrollbars

### Step 2: Add Right Margin to Subir Button Container
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Modify the Box containing the "Subir" button (line 300) to add right margin:
  ```tsx
  <Box sx={{ display: 'flex', justifyContent: 'flex-end', mr: 2 }}>
  ```
- This ensures the button has breathing room from any potential scrollbars

### Step 3: Improve Visual Separation Between Mode Toggle and TextField
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Add a subtle visual separator or increase spacing between mode toggle buttons and the TextField
- Modify the mode toggle Box (line 260) to add more bottom margin:
  ```tsx
  <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
  ```
- This increases spacing from `mb: 2` (16px) to `mb: 3` (24px) for clearer separation

### Step 4: Ensure TextField Has Proper Containment
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Modify the TextField (line 281-298) to ensure it has proper overflow handling:
  ```tsx
  <TextField
    multiline
    rows={8}
    fullWidth
    value={textContent}
    onChange={(e) => setTextContent(e.target.value)}
    placeholder={`Pegue aquí el contenido del email...

Ejemplo:
From: contacto@empresa.com
To: comercial@finkargo.com
Date: Mon, 23 Dec 2024 10:00:00 -0500
Subject: Solicitud de Pago

Estimados,
Por favor proceder con el pago...`}
    disabled={uploading}
    sx={{
      mb: 2,
      '& .MuiInputBase-root': {
        overflow: 'auto',
      },
    }}
  />
  ```

### Step 5: Add Padding to CardContent for Scrollbar Safety
- Edit `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Modify the CardContent (line 253) to add right padding:
  ```tsx
  <CardContent sx={{ pr: 3 }}>
  ```
- This adds extra padding on the right side to prevent content from being hidden by scrollbars

### Step 6: Create E2E Test for Layout Verification
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create a new E2E test file `.claude/commands/e2e/test_email_chain_uploader_layout.md` that:
  1. Navigates to Risk Dashboard
  2. Opens an evaluation detail page
  3. Goes to "Contacto Externo" tab
  4. Verifies the email chain uploader section is visible
  5. Verifies "Pegar Texto" and "Subir Archivo" buttons are visible and clickable
  6. Verifies the TextField is properly contained
  7. Verifies the "Subir" button is fully visible and clickable (not obscured)
  8. Takes screenshots before and after to prove the fix
  9. Tests clicking the "Subir Archivo" button to switch modes
  10. Verifies file upload button is fully visible and clickable

### Step 7: Run Validation Commands
- Execute all validation commands to verify the fix with zero regressions
- Run frontend linting, TypeScript check, and build
- Execute E2E test to visually verify the layout is correct

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build to validate production compilation
cd frontend && npm run build
```

**E2E Test Execution:**
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_email_chain_uploader_layout.md` to validate the layout fix works
- Capture screenshots showing:
  1. The "Subir" button is fully visible and not obscured
  2. The "Subir Archivo" button is clickable
  3. The mode toggle buttons are visually separated from the TextField

## Notes

- No new dependencies required
- This is a CSS/layout-only fix - no changes to business logic or API calls
- The fix should be minimal and surgical, only adjusting spacing and positioning
- Test on different viewport sizes to ensure the fix works responsively
- The scrollbar overlap issue may be more pronounced when the page has scrollable content, so test with an evaluation that has multiple documents/chains
