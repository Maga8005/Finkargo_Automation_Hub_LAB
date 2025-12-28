# E2E Test: Fraud Status Checklist Initialization

Test that the fraud risk finalization checklist correctly shows "Opcional - No hay cadenas/contactos" instead of "Completado" when no email chains or external contacts have been uploaded.

## User Story

As a Risk Analyst
I want to see accurate status indicators in the finalization requirements checklist
So that I can understand what items are truly completed versus optional/not started

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- A valid NIT that can be used to create a new risk evaluation

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (has access to all risk features)

## Test Steps

### Setup

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. Take a screenshot of the Risk Dashboard

### Test Case 1: New Evaluation Shows Correct Initial Status

7. Click on "Nueva Evaluación" or start a new risk evaluation
8. Enter a valid NIT (e.g., 830116134-9 or any valid Colombian NIT)
9. Submit to create the evaluation
10. Wait for evaluation detail page to load
11. Take a screenshot of the evaluation detail page
12. Locate the "Finalizar Evaluación" card/section
13. Find the "Requisitos para Finalización" checklist
14. Take a screenshot of the requirements checklist
15. **Verify** "Cadenas de correo validadas" shows:
    - Yellow warning icon (NOT green checkmark)
    - Secondary text "Opcional - No hay cadenas" (NOT "Completado")
16. **Verify** "Contactos externos validados" shows:
    - Yellow warning icon (NOT green checkmark)
    - Secondary text "Opcional - No hay contactos" (NOT "Completado")
17. Take a screenshot highlighting the correct status display

### Test Case 2: Adding Email Chain Changes Status

18. Navigate to "Contacto Externo" tab (Tab 3 - External Contacts)
19. Upload an email chain PDF or paste email text
20. Take a screenshot of the uploaded email chain
21. Click "Validar" to validate the email chain
22. Wait for validation to complete
23. Return to the finalization section (may need to refresh or navigate)
24. Take a screenshot of the updated requirements checklist
25. **Verify** "Cadenas de correo validadas" now shows:
    - Green checkmark icon
    - Secondary text "Completado"
26. **Verify** "Contactos externos validados" still shows:
    - Yellow warning icon
    - Secondary text "Opcional - No hay contactos"

### Test Case 3: Adding External Contact Changes Status

27. Navigate to "Contacto Externo" tab
28. Click "Agregar Contacto" button
29. Add a new external contact with email (e.g., contact@example.com)
30. Save the contact
31. Click "Validar" to validate the external contact
32. Wait for validation to complete
33. Return to the finalization section
34. Take a screenshot of the updated requirements checklist
35. **Verify** "Contactos externos validados" now shows:
    - Green checkmark icon
    - Secondary text "Completado"

### Cleanup

36. Take a final screenshot of the completed checklist

## Success Criteria

### Initial State (No Items)
- "Cadenas de correo validadas" displays with yellow warning icon
- "Cadenas de correo validadas" shows "Opcional - No hay cadenas" as secondary text
- "Contactos externos validados" displays with yellow warning icon
- "Contactos externos validados" shows "Opcional - No hay contactos" as secondary text
- Neither item shows "Completado" with green checkmark when no items exist

### After Adding and Validating Items
- "Cadenas de correo validadas" shows green checkmark and "Completado" after validating chains
- "Contactos externos validados" shows green checkmark and "Completado" after validating contacts

### Pending State (Items Added but Not All Validated)
- If items exist but not all are validated, show red error icon
- Secondary text shows "Pendiente (X/Y)" format with validation progress

## Screenshots to Capture

1. Risk Dashboard initial state
2. Evaluation detail page
3. Requirements checklist showing "Opcional" status (initial state)
4. Uploaded email chain
5. Requirements checklist after email chain validation
6. Added external contact
7. Requirements checklist after external contact validation
8. Final state with both items completed

## Error Scenarios to Note

- If checklist shows "Completado" for email chains when no chains exist = BUG NOT FIXED
- If checklist shows "Completado" for external contacts when no contacts exist = BUG NOT FIXED
- The fix changes the display logic only - finalization behavior should remain unchanged
