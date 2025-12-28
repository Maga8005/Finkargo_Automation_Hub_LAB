# E2E Test: Comercial Paga Local Role Permissions

Test granular permission restrictions for the `comercial_paga_local` role in the Finkargo Automation Hub.

## User Story

As a Commercial team member with `comercial_paga_local` role
I want to access only the Paga Local Colombia functionality
So that I can create Paga Local contracts without having access to other contract types

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with `comercial_paga_local` role
- Test user account exists in Supabase with `operations` role (for comparison)

## Test Credentials

### User 1: comercial_paga_local role
- Email: test-comercial-paga-local@finkargo.com
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: comercial_paga_local

### User 2: operations role (for comparison)
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: operations

## Test Steps

### Part A: Test comercial_paga_local User Access

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Enter comercial_paga_local test email in email field
4. Enter test password in password field
5. Click "Iniciar Sesión" button
6. Wait for authentication to complete
7. **Verify** user lands on Paga Local Colombia page (/operations/paga-local-colombia)
8. Take a screenshot of the Paga Local Colombia dashboard

### Part B: Test Access Restrictions for comercial_paga_local User

9. Navigate directly to `/operations/contratos-colombia`
10. **Verify** "Acceso Denegado" message is displayed
11. **Verify** message shows user role as `comercial_paga_local`
12. **Verify** message shows required roles include `operations`
13. Take a screenshot of the access denied page

14. Navigate directly to `/operations/contratos-mexico`
15. **Verify** "Acceso Denegado" message is displayed
16. Take a screenshot of the access denied page for Mexico contracts

17. Navigate directly to `/department/legal`
18. **Verify** "Acceso Denegado" message is displayed
19. Take a screenshot of the access denied page for Legal dashboard

### Part C: Test Sidebar Navigation for comercial_paga_local User

20. Navigate back to `/operations/paga-local-colombia`
21. **Verify** sidebar shows "Operations" department
22. Click on "Operations" in the sidebar
23. **Verify** user is navigated to `/operations/paga-local-colombia` (not contratos-colombia)
24. Take a screenshot showing sidebar with Operations department visible

### Part D: Test Operations User Can Access All Routes (Comparison) - OPTIONAL

**Note:** Part D is optional. If the `test-operations@finkargo.com` user does not exist, skip Part D and consider the test passed based on Parts A, B, and C.

25. Log out the comercial_paga_local user
26. Log in with operations role user (if user doesn't exist, skip to step 33)
27. Navigate to `/operations/contratos-colombia`
28. **Verify** Contratos Colombia page loads successfully (no access denied)
29. Take a screenshot of Contratos Colombia page for operations user

30. Navigate to `/operations/paga-local-colombia`
31. **Verify** Paga Local Colombia page loads successfully
32. Take a screenshot of Paga Local Colombia page for operations user

33. If Part D was skipped due to missing test user, note this in the test output but mark test as PASSED

## Success Criteria

### Required (Parts A, B, C):
- comercial_paga_local user can access Paga Local Colombia page
- comercial_paga_local user sees "Acceso Denegado" for Contratos Colombia
- comercial_paga_local user sees "Acceso Denegado" for Contratos Mexico
- comercial_paga_local user sees "Acceso Denegado" for Legal dashboard
- comercial_paga_local user sidebar click on Operations goes to Paga Local Colombia

### Optional (Part D - only if test-operations@finkargo.com user exists):
- operations user can access both Contratos Colombia and Paga Local Colombia

### Screenshots:
- 5 screenshots minimum (Parts A, B, C):
  1. Paga Local Colombia dashboard (comercial_paga_local user)
  2. Access denied for Contratos Colombia
  3. Access denied for Contratos Mexico
  4. Access denied for Legal dashboard
  5. Sidebar showing Operations department (comercial_paga_local user)
- 2 additional screenshots if Part D is completed:
  6. Contratos Colombia page (operations user)
  7. Paga Local Colombia page (operations user)

## Error Scenarios to Note

- If comercial_paga_local user bypasses UI and calls API directly, backend should return 403
- Admin users should still have access to all routes (admin bypass)
- If user role is changed while logged in, permissions should update on refresh

## Backend API Verification (Optional)

To verify backend permissions, test these API endpoints:

### Endpoints comercial_paga_local CAN access:
- POST `/api/operations/contracts/solicitud-desembolso/parse-cotizacion`
- POST `/api/operations/contracts/solicitud-desembolso/generate`
- POST `/api/operations/contracts/instruccion-mandato/parse-cotizacion`
- POST `/api/operations/contracts/instruccion-mandato/generate`
- POST `/api/operations/contracts/dian-mandato/parse-cotizacion`
- POST `/api/operations/contracts/dian-mandato/generate`
- GET `/api/operations/contracts/approved`

### Endpoints comercial_paga_local CANNOT access:
- POST `/api/operations/contracts/generate` (with contract_type=activos)
