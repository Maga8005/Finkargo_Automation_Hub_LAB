# E2E Test: Risk Dashboard Flow

Test the Risk Department (Riesgos) dashboard and fraud detection workflow for the Finkargo Automation Hub application.

## User Story

As a Risk Analyst or Risk Manager
I want to evaluate client fraud risk using automated detection algorithms
So that I can prevent financial losses from fraudulent applications

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (migration_add_risk_roles.sql, migration_create_risk_tables.sql)
- Admin account exists (admin@finkargo.com) with full system access
- At least one client record exists in the database for testing

## Test Credentials

Use admin account (has access to all modules including risk):
- Email: admin@finkargo.com
- Password: Automation2025*_2026
- Expected Role: admin (can access all risk features)

Note: Admin role has full access to risk module including:
- Risk dashboard viewing
- Creating risk evaluations
- Risk configuration management
- Making approval/rejection decisions

## Test Steps

### Part 1: Authentication and Access

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter admin email (admin@finkargo.com) in email field
4. Enter admin password (Automation2025*_2026) in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/risk/dashboard`
8. **Verify** user can access `/risk/dashboard` (page loads successfully)
9. Take a screenshot of successful dashboard access

### Part 2: Dashboard Overview

10. **Verify** page title shows "Gestión de Riesgos y Fraude"
11. **Verify** dashboard metrics cards are visible:
    - Total evaluaciones
    - Pendientes de revisión
    - Alto riesgo
    - Críticos
12. Take a screenshot of dashboard metrics
13. **Verify** tabs are present: "Evaluaciones", "Alertas", "Blacklist"
14. **Verify** evaluations table displays with columns:
    - ID (RISK-YYYY-NNN format)
    - Cliente (NIT)
    - Nivel de Riesgo
    - Puntaje
    - Estado
    - Fecha
    - Acciones

### Part 3: Create Risk Evaluation

15. Click "Nueva Evaluación" button
16. **Verify** evaluation form modal/dialog opens
17. Enter a valid client NIT in the form
18. Take a screenshot of the evaluation form
19. Click "Evaluar" or submit button
20. Wait for evaluation to complete (loading state)
21. **Verify** new evaluation appears in the list
22. **Verify** risk score is calculated (0-100)
23. **Verify** risk level is assigned (Bajo/Medio/Alto/Crítico)
24. Take a screenshot showing new evaluation in list

### Part 4: Evaluation Detail View

25. Click on an evaluation row to view details
26. **Verify** navigation to `/risk/evaluations/:id`
27. **Verify** detail page shows:
    - Assessment ID
    - Client information (NIT, company name)
    - Risk score visualization (circular progress)
    - Risk level badge with color
    - List of fraud indicators with severity
28. Take a screenshot of evaluation detail page
29. **Verify** fraud indicators show:
    - Indicator name
    - Value (pass/fail)
    - Severity level
    - Score impact
30. Click back button to return to dashboard

### Part 5: Alerts Tab

31. Navigate to "Alertas" tab
32. **Verify** alerts list displays with:
    - Severity indicator (icon/color)
    - Alert message
    - Timestamp
    - Mark as read button
33. If alerts exist, click "Marcar como leído" on one
34. **Verify** alert visual state changes (marked as read)
35. Take a screenshot of alerts tab

### Part 6: Blacklist Tab

36. Navigate to "Blacklist" tab
37. **Verify** blacklist table displays with columns:
    - Tipo de entidad
    - Valor
    - Razón
    - Agregado por
    - Fecha
    - Estado
38. Take a screenshot of blacklist tab
39. **Verify** "Agregar a blacklist" button is visible

### Part 7: Configuration Page (Admin Access)

40. Navigate to `/risk/configuration`
41. **Verify** access is granted (admin has full access)
42. **Verify** rules table displays with:
    - Rule name
    - Type
    - Weight (slider or input)
    - Threshold
    - Active toggle
43. Take a screenshot of configuration page
44. (Optional) Adjust a rule weight if editable
45. **Verify** configuration page loads without errors

### Part 8: Decision Flow (Admin Access)

46. Navigate to an evaluation detail page with status "pending" or "in_progress"
47. **Verify** decision section is visible with:
    - Status dropdown (Aprobar/Rechazar/Escalar)
    - Notes textarea
    - Submit button
48. Select "Aprobar" from dropdown
49. Enter review notes
50. Take a screenshot before submission
51. Click submit button
52. **Verify** status changes to "approved"
53. **Verify** review information is recorded (reviewed_by, reviewed_at)
54. Take a screenshot of approved evaluation

## Success Criteria

- Dashboard loads without errors for authorized users (admin account)
- Admin can access all risk module features including:
  - Risk dashboard viewing
  - Creating risk evaluations
  - Viewing evaluation details
  - Accessing alerts and blacklist tabs
  - Configuration page access
  - Making approval/rejection decisions
- Risk evaluation creates successfully with score calculation
- Fraud indicators display correctly with severity levels
- Alerts functionality works (view, mark as read)
- Blacklist displays correctly
- Configuration page loads successfully
- Decision workflow completes successfully
- Screenshots captured at each major step (minimum 8)

## Error Scenarios to Note

- Invalid NIT format should show validation error
- Network errors should be handled gracefully
- Missing client data should show appropriate error message
- Concurrent evaluations should not cause conflicts
- Blacklisted entities should immediately flag as critical risk

## Expected Screenshots

1. Successful dashboard access (after login)
2. Dashboard with metrics cards
3. Evaluation form
4. Evaluation list with new entry
5. Evaluation detail page
6. Alerts tab
7. Blacklist tab
8. Configuration page
9. Decision flow before submission
10. Approved evaluation detail
