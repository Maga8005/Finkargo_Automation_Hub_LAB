# E2E Test: Treasury Declaration Matching Menu Item

Test that the Declaration Matching menu item appears in the Treasury sidebar submenu and navigates correctly.

## User Story

As a Finkargo treasury user
I want to see the "Coincidencia Declaraciones" option in the Tesoreria sidebar menu
So that I can easily access the Declaration-Historial matching workflow

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with admin or treasury role

## Test Credentials

Use test account (configure in test environment):
- Email: admin@finkargo.com
- Password: [configured test password]
- Expected Role: admin

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Enter test email in email field
4. Enter test password in password field
5. Click "Iniciar Sesion" button
6. Wait for authentication to complete
7. **Verify** successful redirect occurs (URL changes from /login)
8. Take a screenshot of the dashboard

9. Locate the "Tesoreria" department in the sidebar
10. Click on "Tesoreria" to expand the submenu
11. Take a screenshot showing the expanded Tesoreria submenu
12. **Verify** the following menu items are visible in the Tesoreria submenu:
    - "Plantillas NetSuite"
    - "Aplicacion Pagos CO"
    - "Aplicacion Pagos MX"
    - "Coincidencia Declaraciones"
13. Take a screenshot showing all 4 treasury menu items

14. Click on "Coincidencia Declaraciones" menu item
15. Wait for navigation to complete
16. **Verify** the URL is now `/treasury/declaration-matching`
17. **Verify** the page title "Coincidencia Declaraciones - Historial de Pagos" is visible
18. **Verify** the Tesoreria submenu is still expanded (auto-expand feature)
19. **Verify** the "Coincidencia Declaraciones" menu item appears highlighted/active
20. Take a screenshot of the Declaration Matching page

## Success Criteria

- Login completes successfully
- Tesoreria department expands on click
- All 4 treasury submenu items are visible
- "Coincidencia Declaraciones" menu item is clickable
- Navigation to `/treasury/declaration-matching` works
- Page loads with correct title
- Treasury menu auto-expands when on `/treasury/` route
- Active menu item is highlighted
- 4 screenshots are captured:
  1. Dashboard after login
  2. Expanded Tesoreria submenu
  3. All 4 treasury menu items visible
  4. Declaration Matching page with active menu state

## Error Scenarios to Note

- If "Coincidencia Declaraciones" is not visible, the fix was not applied correctly
- If clicking the menu item doesn't navigate, the route may be misconfigured
- If the menu doesn't auto-expand on the treasury page, the auto-expand logic is incorrect
