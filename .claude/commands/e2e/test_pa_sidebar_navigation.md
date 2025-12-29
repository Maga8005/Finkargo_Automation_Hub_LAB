# E2E Test: PA Sidebar Navigation

Test the PA Report Classification sidebar navigation in the Finance department for the Finkargo Automation Hub application.

## User Story

As a Finance user or Finance Admin
I want to access PA Report Classification pages from the sidebar menu
So that I can navigate to classification rules and report processing features

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Database migrations applied (migration_pa_classification.sql, migration_add_finance_admin_role.sql)
- Admin account exists with full system access

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (can access all finance features)

Note: Admin role has full access to finance module including:
- Reporte PA (report processing)
- Reglas Clasificación PA (rules management)

## Test Steps

### Part 1: Authentication and Access

1. Navigate to the `Application URL` (http://localhost:5175)
2. **Verify** login page is displayed
3. Enter admin email (`$TEST_ADMIN_EMAIL`) in email field
4. Enter admin password (`$TEST_ADMIN_PASSWORD`) in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Take a screenshot of successful login

### Part 2: Sidebar Finance Menu Verification

8. Locate "Finanzas" department in the sidebar
9. Click on "Finanzas" to expand the submenu
10. **Verify** submenu expands and shows 4 menu items:
    - "Reportería Automática CO"
    - "Reportería Automática MX"
    - "Reporte PA"
    - "Reglas Clasificación PA"
11. Take a screenshot of expanded Finance sidebar submenu

### Part 3: Navigate to Reporte PA

12. Click on "Reporte PA" menu item
13. **Verify** navigation to URL `/finance/reporte-pa`
14. **Verify** page loads with title containing "Reporte PA" or "Clasificación PA"
15. **Verify** the page shows the main content area (stepper or upload section)
16. Take a screenshot of Reporte PA page

### Part 4: Navigate to Reglas Clasificación PA

17. Click on "Finanzas" in sidebar to expand submenu (if collapsed)
18. Click on "Reglas Clasificación PA" menu item
19. **Verify** navigation to URL `/finance/reglas-clasificacion-pa`
20. **Verify** page loads with title containing "Reglas" or "Clasificación"
21. **Verify** the page shows tabs for different rule types (Catálogo, Clasificación, etc.)
22. Take a screenshot of Reglas Clasificación PA page

### Part 5: Active State Verification

23. **Verify** "Reglas Clasificación PA" menu item is highlighted/active in sidebar
24. Navigate to "/finance/reporte-pa" via URL
25. **Verify** sidebar auto-expands Finance department
26. **Verify** "Reporte PA" menu item is highlighted/active
27. Take a screenshot showing active menu state

## Success Criteria

- Login succeeds with admin credentials
- Finance department sidebar expands on click
- All 4 finance menu items are visible (including new PA items)
- "Reporte PA" menu item navigates to `/finance/reporte-pa`
- "Reglas Clasificación PA" menu item navigates to `/finance/reglas-clasificacion-pa`
- Both PA pages load without errors
- Active menu item is visually highlighted
- Screenshots captured at each major step (minimum 5)

## Error Scenarios to Note

- Missing menu items indicate `financeModules` array not updated
- 404 errors indicate route not defined in App.tsx
- Access denied indicates role permission issues
- Page not rendering indicates component not imported correctly

## Expected Screenshots

1. Successful login/homepage
2. Expanded Finance sidebar submenu (showing all 4 items)
3. Reporte PA page loaded
4. Reglas Clasificación PA page loaded
5. Active menu state highlighted
