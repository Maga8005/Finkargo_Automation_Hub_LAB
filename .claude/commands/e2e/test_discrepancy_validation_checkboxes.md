# E2E Test: Discrepancy Validation Checkboxes

Test the individual discrepancy validation functionality in the Riesgos module for the Finkargo Automation Hub application.

## User Story

As a Mesa de Control analyst (mesa_control role)
I want to validate individual discrepancies with specific reasons and add comments
So that I can document why each discrepancy was reviewed and approved, providing a proper audit trail for risk assessments

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (including migration_add_discrepancy_validations.sql)
- Admin or mesa_control account exists with access to risk module
- At least one risk evaluation with discrepancies exists (or create one during test)

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) or a mesa_control user
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin or mesa_control (can validate discrepancies)

Note: mesa_control, risk_manager, and admin roles have access to validate discrepancies.

## Test Steps

### Part 1: Authentication and Navigation

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter admin/mesa_control email in email field
4. Enter password in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/risk/dashboard`
8. **Verify** user can access `/risk/dashboard` (page loads successfully)
9. Take a screenshot of successful dashboard access

### Part 2: Navigate to Evaluation with Discrepancies

10. Find an evaluation with discrepancies in the evaluations list
    - Look for evaluations with "REQUIERE REVISIÓN" status or discrepancy count > 0
11. Click on the evaluation row to view details
12. **Verify** navigation to `/risk/evaluations/:id`
13. **Verify** detail page shows cross-validation results section
14. Take a screenshot of evaluation detail page

### Part 3: Cross-Validation Results with Discrepancies

15. Scroll to "Validación Cruzada de Documentos" section
16. **Verify** discrepancy items are displayed with individual validation controls
17. **Verify** each discrepancy shows:
    - Checkbox for validation
    - Validation type and field information
    - Severity indicator (color-coded)
18. Take a screenshot of discrepancy list with validation controls

### Part 4: Validate Single Discrepancy

19. Click on a discrepancy item to expand it
20. **Verify** validation controls appear:
    - Dropdown with validation reasons
    - Text field for comments
    - "Guardar Validación" button
21. Select a validation reason from the dropdown (e.g., "Validación manual")
22. Enter a comment: "Verified against original documents - data is correct"
23. Take a screenshot of validation form filled out
24. Click "Guardar Validación" button
25. **Verify** success message appears
26. **Verify** discrepancy now shows:
    - Green checkmark indicating validated
    - Validation reason label
    - Validator name and timestamp
27. Take a screenshot of validated discrepancy

### Part 5: Validation Progress Tracking

28. **Verify** validation progress indicator shows updated count (e.g., "Validados: 1/3")
29. Validate remaining discrepancies (repeat steps 19-26 for each)
30. **Verify** progress updates with each validation
31. Take a screenshot of progress indicator

### Part 6: All Discrepancies Validated

32. After validating all discrepancies:
    - **Verify** success banner appears indicating all discrepancies validated
    - **Verify** status shows "VALIDADO POR MESA DE CONTROL" styling
33. Take a screenshot of fully validated state
34. Refresh the page
35. **Verify** all validations persist after refresh
36. **Verify** validation info still shows correctly

### Part 7: Remove Validation

37. Click on a validated discrepancy
38. **Verify** "Quitar Validación" button is visible
39. Click "Quitar Validación" button
40. **Verify** confirmation dialog appears
41. Confirm removal
42. **Verify** discrepancy returns to unvalidated state
43. **Verify** progress indicator decrements (e.g., "Validados: 2/3")
44. Take a screenshot after removing validation

### Part 8: PDF Export with Validations

45. Re-validate the discrepancy removed in Part 7
46. Click "Exportar PDF" button
47. **Verify** PDF downloads successfully
48. **Verify** PDF contains:
    - "Validaciones de Mesa de Control" section
    - Validated discrepancies with reasons
    - Validator names and timestamps
    - "Validado por Mesa de Control" header text
49. Take a screenshot of PDF export (if possible to view in browser)

### Part 9: Role-Based Access Control (Optional)

50. Log out
51. Log in as a user with risk_analyst role (no mesa_control permissions)
52. Navigate to the same evaluation
53. **Verify** validation controls are NOT visible or are disabled
54. Take a screenshot showing restricted access

## Success Criteria

- Individual checkboxes appear next to each discrepancy
- Validation reason dropdown contains all 4 options:
  - "Validación manual"
  - "Verificado por email"
  - "Error de carga"
  - "Justificación del cliente"
- Comments field accepts up to 2000 characters
- Validation progress shows correctly (e.g., "Validados: 3/5")
- Validated items show green checkmark, reason, and validator info
- Status updates to "validated_by_mesa_control" when all validated
- Validations can be removed
- PDF export includes validation information
- Only authorized roles can validate (mesa_control, risk_manager, admin)
- All validations persist after page refresh

## Error Scenarios to Note

- Attempting to validate without selecting a reason → Show validation error
- Attempting to validate same discrepancy twice → Handle gracefully (update or ignore)
- Network error during validation → Show error message
- Comments exceeding 2000 characters → Prevent submission with clear error
- Unauthorized role attempting to validate → Hide controls or show 403

## Expected Screenshots

1. Dashboard access (after login)
2. Evaluation detail page
3. Discrepancy list with validation controls
4. Validation form filled out
5. Validated discrepancy (with checkmark, reason, timestamp)
6. Validation progress indicator
7. Fully validated state
8. After removing validation
9. Restricted access for unauthorized role (optional)
