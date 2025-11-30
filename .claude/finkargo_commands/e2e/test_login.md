# E2E Test: Login Flow

Test authentication flow for the Finkargo Automation Hub application.

## User Story

As a Finkargo user  
I want to log in with my Supabase credentials  
So that I can access my department dashboard based on my role

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists in Supabase with known credentials

## Test Credentials

Use test account (configure in test environment):
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Take a screenshot of the login page
4. **Verify** login form elements are present:
   - Email input field
   - Password input field
   - "Iniciar Sesión" button
   - Finkargo branding/logo

5. Enter test email in email field
6. Enter test password in password field
7. Take a screenshot of filled login form
8. Click "Iniciar Sesión" button
9. Wait for authentication to complete (loading state)
10. **Verify** successful redirect occurs (URL changes from /login)
11. **Verify** user lands on appropriate dashboard based on role:
    - Operations users → /operations/* routes
    - Legal users → /department/legal
    - Admin users → home dashboard
12. **Verify** user profile information appears in header/nav
13. Take a screenshot of the dashboard after login

## Success Criteria
- Login page loads without errors
- Form accepts email and password input
- Submit button triggers authentication
- Successful login redirects to role-appropriate dashboard
- User session is established (no re-login required on page refresh)
- 3 screenshots are captured:
  1. Initial login page
  2. Filled login form
  3. Dashboard after successful login

## Error Scenarios to Note
- Invalid credentials should show error message
- Network errors should be handled gracefully
- Session timeout should redirect back to login
