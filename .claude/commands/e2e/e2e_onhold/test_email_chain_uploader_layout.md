# E2E Test: Email Chain Uploader Layout

Test the email chain uploader component layout to verify all buttons are properly visible and clickable without scrollbar overlap.

## User Story

As a Risk Analyst or Admin
I want all buttons in the email chain uploader to be fully visible and clickable
So that I can upload email chains without UI interaction issues

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation to test with

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: risk_analyst or risk_manager

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. Log in with test credentials
3. Wait for redirect to dashboard
4. Navigate to Risk Dashboard (/risk)
5. **Verify** risk evaluations list is displayed
6. Click on an existing evaluation
7. **Verify** evaluation detail page loads
8. Navigate to "Contacto Externo" tab (Tab 3)
9. Expand the "Cadenas de Email" accordion section
10. Take a screenshot of the email chain uploader section
11. **Verify** the following elements are fully visible and not obscured:
    - "Pegar Texto" button (should be contained/filled style)
    - "Subir Archivo" button (should be outlined style)
    - TextField for pasting email content
    - "Subir" button at bottom-right
12. **Verify** the "Subir" button is NOT overlapped by any scrollbar:
    - The button should have clear space on the right
    - The entire button text and icon should be visible
13. Click the "Subir Archivo" button to switch modes
14. **Verify** mode switches successfully:
    - "Subir Archivo" button becomes contained
    - "Pegar Texto" button becomes outlined
    - File upload area appears
15. Take a screenshot of the file upload mode
16. **Verify** the file upload button is fully visible and clickable:
    - "Seleccionar archivo .eml o .msg" button should be centered
    - "Máximo 10MB" caption should be visible below
17. Click the "Pegar Texto" button to switch back
18. **Verify** mode switches back successfully
19. **Verify** proper spacing between mode toggle buttons and TextField:
    - There should be clear visual separation
    - The buttons should not appear inside the TextField area
20. Type some text in the TextField
21. **Verify** the "Subir" button becomes enabled
22. Click the "Subir" button
23. **Verify** the button responds to the click (loading state or action)
24. Take a final screenshot showing the component in working state

## Success Criteria

- Login completes successfully
- Risk Dashboard loads with evaluations
- External Contact tab shows email chain uploader
- Mode toggle buttons ("Pegar Texto", "Subir Archivo") are fully visible and clickable
- TextField is properly contained with clear boundaries
- "Subir" button is fully visible without scrollbar overlap
- Mode switching works correctly (text ↔ file)
- File upload button in file mode is fully visible and clickable
- All interactions work without UI blocking issues
- 3 screenshots are captured:
  1. Email chain uploader in text mode (initial state)
  2. Email chain uploader in file mode
  3. Final state after interaction

## Layout Verification Points

- [ ] Card has proper stacking context (content not overlapped by external scrollbars)
- [ ] Mode toggle buttons have adequate spacing from TextField (24px gap)
- [ ] "Subir" button has right padding to prevent scrollbar overlap
- [ ] TextField placeholder text stays within bounds
- [ ] All clickable elements respond to clicks without dead zones

## Error Scenarios to Note

- If the "Subir" button is unclickable, the scrollbar overlap issue persists
- If mode toggle buttons appear inside TextField, layout issue not fixed
- If any button clicks don't register, check for z-index issues
