# E2E Test: External Communication Validation Comments

Test the individual validation functionality for external communication alerts (email chain discrepancies and external contact alerts) in the Riesgos module.

## User Story

As a Mesa de Control analyst (mesa_control role)
I want to validate individual alerts from the external communication page with specific reasons and comments
So that I can document my review of email domain discrepancies, typosquatting alerts, and company name mismatches, providing a proper audit trail for risk assessments

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (including migration_add_external_communication_validations.sql)
- Admin or mesa_control account exists with access to risk module
- At least one risk evaluation with email chains or external contacts that have validation results

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) or a mesa_control user
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin or mesa_control (can validate alerts)

Note: mesa_control, risk_manager, and admin roles have access to validate external communication alerts.

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

### Part 2: Navigate to Evaluation with External Communication Data

10. Find an evaluation with email chains or external contacts that have validation results
    - Look for evaluations with suspicious/critical email chains or external contacts
11. Click on the evaluation row to view details
12. **Verify** navigation to `/risk/evaluations/:id`
13. Navigate to the "Comunicación Externa" tab
14. **Verify** the tab shows email chain uploader and external contacts sections
15. Take a screenshot of external communication tab

### Part 3: Email Chain Discrepancy Validation

16. Locate an email chain with discrepancies (suspicious or critical status)
17. Expand the email chain to view its discrepancies
18. **Verify** each discrepancy shows:
    - Severity indicator (color-coded chip)
    - Field label (e.g., "Dominio del Remitente", "Nombre de Empresa")
    - Description of the issue
    - Validation controls (if user has permission)
19. Click on a discrepancy item to expand validation form
20. **Verify** validation controls appear:
    - Dropdown with validation reasons
    - Text field for comments (max 2000 chars)
    - "Guardar Validación" button
21. Select a validation reason from the dropdown (e.g., "Validación manual")
22. Enter a comment: "Verificado - el dominio corresponde a una subsidiaria autorizada"
23. Take a screenshot of validation form filled out
24. Click "Guardar Validación" button
25. **Verify** success message appears
26. **Verify** discrepancy now shows:
    - Green checkmark indicating validated
    - Validation reason label
    - Validator name and timestamp
27. Take a screenshot of validated email chain discrepancy

### Part 4: External Contact Alert Validation

28. Scroll to the "Contactos Externos Individuales" section
29. Find an external contact with suspicious or critical status
30. **Verify** the contact shows validation result details (typosquatting info, domain age, etc.)
31. Click on the contact's validation control to expand
32. **Verify** validation form appears with same options as email chain discrepancies
33. Select validation reason: "Verificado por email"
34. Enter comment: "Confirmado mediante comunicación directa con el cliente"
35. Take a screenshot of external contact validation form
36. Click "Guardar Validación" button
37. **Verify** success message appears
38. **Verify** contact now shows validated status with reason and timestamp
39. Take a screenshot of validated external contact

### Part 5: Validation Progress Tracking

40. **Verify** validation progress indicators show for both sections:
    - Email chains: "Validados: X/Y" count
    - External contacts: "Validados: X/Y" count
41. Take a screenshot of progress indicators
42. Refresh the page
43. **Verify** all validations persist after refresh
44. **Verify** validation info still shows correctly

### Part 6: Remove Validation

45. Click on a validated email chain discrepancy
46. **Verify** "Quitar Validación" button is visible
47. Click "Quitar Validación" button
48. **Verify** confirmation or immediate removal
49. **Verify** discrepancy returns to unvalidated state
50. **Verify** progress indicator decrements
51. Take a screenshot after removing validation

### Part 7: PDF Export with Validations

52. Re-validate the discrepancy removed in Part 6
53. Navigate to evaluation detail page header
54. Click "Exportar PDF" or "Reporte Completo" button
55. **Verify** PDF downloads successfully
56. **Verify** PDF contains:
    - "Alertas de Comunicación Externa" section
    - Email chain discrepancies with validation status
    - External contact alerts with validation status
    - Comments from validations
    - Validator names and timestamps
57. Take a screenshot of PDF section showing external communication validations (if viewable)

### Part 8: Role-Based Access Control (Optional)

58. Log out
59. Log in as a user with only risk_analyst role (no mesa_control permissions)
60. Navigate to the same evaluation's external communication tab
61. **Verify** validation controls are NOT visible or are disabled
62. Take a screenshot showing restricted access

## Success Criteria

- Validation controls appear for each email chain discrepancy
- Validation controls appear for each suspicious/critical external contact
- Validation reason dropdown contains all 4 options:
  - "Validación manual"
  - "Verificado por email"
  - "Error de carga"
  - "Justificación del cliente"
- Comments field accepts up to 2000 characters
- Validation progress shows correctly (e.g., "Validados: 3/5")
- Validated items show green checkmark, reason, and validator info
- Validations can be removed by authorized users
- PDF export includes external communication validation information
- Only authorized roles can validate (mesa_control, risk_manager, admin)
- All validations persist after page refresh

## Error Scenarios to Note

- Attempting to validate without selecting a reason → Show validation error
- Attempting to validate same item twice → Handle gracefully (update or ignore)
- Network error during validation → Show error message
- Comments exceeding 2000 characters → Prevent submission with clear error
- Unauthorized role attempting to validate → Hide controls or show 403

## Expected Screenshots

1. Dashboard access (after login)
2. External communication tab
3. Email chain discrepancy with validation form
4. Validated email chain discrepancy (with checkmark, reason, timestamp)
5. External contact validation form
6. Validated external contact
7. Validation progress indicators
8. After removing validation
9. Restricted access for unauthorized role (optional)
