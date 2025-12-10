# E2E Test: Banxico Exchange Rate Integration

Test the USD/MXN exchange rate retrieval from Banxico API in the Alianzas module.

## User Story

As an alianzas team member
I want to fetch the official USD/MXN exchange rate from Banxico
So that I can accurately calculate broker commissions in MXN

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with `alianzas` or `admin` role
- `BANXICO_API_TOKEN` environment variable configured in backend

## Test Credentials

Use test account (configure in test environment):
- Email: test-alianzas@finkargo.com (or admin account)
- Password: [configured test password]
- Expected Role: alianzas or admin

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Enter test email in email field
4. Enter test password in password field
5. Click "Iniciar Sesión" button
6. Wait for authentication to complete
7. **Verify** successful redirect to dashboard
8. Take a screenshot of the dashboard after login

### API Endpoint Testing (via Browser Console or Direct Call)

9. Open browser developer tools (F12)
10. Navigate to Console tab
11. Execute the following to test the tipo-cambio endpoint:
```javascript
const token = localStorage.getItem('sb-auth-token') || sessionStorage.getItem('sb-auth-token');
const response = await fetch('http://localhost:8000/api/alianzas/tipo-cambio', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
console.log('Tipo de Cambio:', data);
```
12. **Verify** response contains:
    - `tipo_cambio`: A numeric value (e.g., 20.4523)
    - `fecha`: A date string in ISO format (YYYY-MM-DD)
    - `fuente`: "Banco de México (Banxico)"
13. Take a screenshot showing the console response

### Historical Date Testing

14. Execute the following to test historical date endpoint:
```javascript
const token = localStorage.getItem('sb-auth-token') || sessionStorage.getItem('sb-auth-token');
const response = await fetch('http://localhost:8000/api/alianzas/tipo-cambio/2025-01-10', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
console.log('Historical Tipo de Cambio:', data);
```
15. **Verify** response contains a valid exchange rate for the specified date
16. Take a screenshot showing the historical rate response

### Error Handling Test

17. Test weekend date (no rate published):
```javascript
const token = localStorage.getItem('sb-auth-token') || sessionStorage.getItem('sb-auth-token');
// Test with a Saturday date
const response = await fetch('http://localhost:8000/api/alianzas/tipo-cambio/2025-01-11', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();
console.log('Weekend Fallback:', data);
```
18. **Verify** response returns a valid rate (should fall back to Friday's rate)
19. Take a screenshot showing the fallback behavior

## Success Criteria

- Login successfully with alianzas/admin role
- Current exchange rate endpoint returns valid response with:
  - tipo_cambio: positive number
  - fecha: valid ISO date
  - fuente: "Banco de México (Banxico)"
- Historical date endpoint returns valid response
- Weekend/holiday fallback works (returns previous business day rate)
- All API calls return HTTP 200 status
- 4 screenshots are captured:
  1. Dashboard after login
  2. Current exchange rate response
  3. Historical exchange rate response
  4. Weekend fallback response

## Error Scenarios to Note

- Missing BANXICO_API_TOKEN should return 500 with helpful message
- Invalid date format should return 400
- Unauthorized access (no token) should return 401
- Non-alianzas role should return 403
