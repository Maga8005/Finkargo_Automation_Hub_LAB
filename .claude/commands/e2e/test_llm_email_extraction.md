# E2E Test: LLM Email Extraction for Riesgos Module

Test the OpenAI GPT-4o powered entity extraction toggle and functionality in the Fraud Risk module.

## User Story

As a Risk Manager
I want to enable/disable AI-powered email extraction
So that I can control costs and compare AI extraction quality against regex-based extraction

## Prerequisites

- Backend server running at http://localhost:8003
- Frontend server running at http://localhost:5175
- Test user account with admin or risk_manager role
- OpenAI API key configured in backend/.env (for AI extraction tests)
- Database migration for risk_settings table applied

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (has access to all risk features and settings)

## Test Steps

### Setup

1. Navigate to the Application URL (http://localhost:5175)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Take a screenshot of the dashboard

### Test Case 1: Verify Settings API Endpoint

6. Open browser developer tools (F12)
7. Navigate to Network tab
8. Execute API call to GET /api/risk/settings using fetch:
   ```javascript
   fetch('/api/risk/settings', {
     headers: { 'Authorization': 'Bearer ' + localStorage.getItem('supabase.auth.token') }
   }).then(r => r.json()).then(console.log)
   ```
9. **Verify** response contains settings array with `ai_email_extraction_enabled` setting
10. **Verify** default value is `false`
11. Take a screenshot of the console output

### Test Case 2: Toggle AI Extraction Setting (Admin Only)

12. Execute API call to PUT /api/risk/settings/ai_email_extraction_enabled to enable:
    ```javascript
    fetch('/api/risk/settings/ai_email_extraction_enabled?value=true', {
      method: 'PUT',
      headers: { 'Authorization': 'Bearer ' + localStorage.getItem('supabase.auth.token') }
    }).then(r => r.json()).then(console.log)
    ```
13. **Verify** response shows updated value is `true`
14. **Verify** response includes `updated_at` timestamp
15. Take a screenshot of the console output

### Test Case 3: Upload Email with AI Extraction Enabled

16. Navigate to Risk Dashboard (/risk)
17. Create a new risk evaluation or open an existing one with documents
18. Navigate to "Contactos Externos / Cadenas de Email" section (Tab 3)
19. Paste sample email text:
    ```
    From: comercial@azelis.com.co
    To: operaciones@finkargo.com
    Date: Sat, 28 Dec 2024 10:00:00 -0500
    Subject: Datos Bancarios - AZELIS COLOMBIA S.A.S.

    Buenos días,

    Por favor encuentren los datos para el pago:

    Empresa: AZELIS COLOMBIA S.A.S.
    NIT: 830.027.231-3
    Representante Legal: JUAN CARLOS MARTINEZ LOPEZ
    Gerente General: MARIA FERNANDA RODRIGUEZ

    Cuenta Bancaria: Bancolombia 123-456789-01

    Quedamos atentos.

    Cordialmente,
    Pedro Gomez
    Departamento Comercial
    AZELIS COLOMBIA
    Tel: 3101234567
    ```
20. Click "Subir" button to upload
21. **Verify** email chain appears in the list
22. Check parsed_data in response (via Network tab)
23. **Verify** `mentions.extraction_method` is "ai" (if OpenAI configured) or "regex" (if not)
24. Take a screenshot of uploaded email chain

### Test Case 4: Validate Email Chain with AI Extraction

25. Locate the uploaded email chain
26. Click "Validar" button
27. Wait for validation to complete
28. Check validation_result in response (via Network tab)
29. **Verify** response contains `ai_assisted` field
30. **Verify** response contains `extraction_method` field matching parsed_data
31. Take a screenshot of validation results

### Test Case 5: Verify Extracted Entities (AI Mode)

32. Inspect the parsed_data.mentions object
33. **Verify** company_names includes "AZELIS COLOMBIA S.A.S."
34. **Verify** nits includes "830027231-3" (normalized)
35. **Verify** representative_names includes names found by AI
36. **Verify** domains includes "azelis.com.co"
37. Take a screenshot of extracted entities

### Test Case 6: Disable AI Extraction and Re-test

38. Execute API call to disable AI extraction:
    ```javascript
    fetch('/api/risk/settings/ai_email_extraction_enabled?value=false', {
      method: 'PUT',
      headers: { 'Authorization': 'Bearer ' + localStorage.getItem('supabase.auth.token') }
    }).then(r => r.json()).then(console.log)
    ```
39. **Verify** setting is now `false`
40. Upload a new email chain with same content
41. **Verify** `mentions.extraction_method` is "regex"
42. Take a screenshot comparing AI vs regex extraction

### Test Case 7: Verify Role Protection

43. Log out from admin account
44. Log in with a risk_analyst account (if available) or skip this test
45. Attempt to update setting via PUT endpoint
46. **Verify** 403 Forbidden response if user is not admin/risk_manager
47. Take a screenshot of error response

### Cleanup

48. Delete test email chains
49. Reset AI extraction setting to `false` if changed
50. Take a final screenshot

## Success Criteria

### Settings API
- GET /api/risk/settings returns list of settings
- PUT /api/risk/settings/{key} updates setting value
- Only admin/risk_manager can update settings
- Settings persist across requests

### AI Extraction
- When enabled, extraction_method is "ai" (if OpenAI API available)
- When disabled, extraction_method is "regex"
- AI extraction captures entities accurately
- Fallback to regex works when AI unavailable (extraction_method: "regex_fallback")

### Validation Tracking
- validation_result includes ai_assisted boolean
- validation_result includes extraction_method field
- Fields match between parsed_data and validation_result

### Entity Extraction Quality (AI Mode)
- Company names extracted with legal suffixes
- NITs normalized correctly (dots removed, check digit preserved)
- Representative names identified from context
- Corporate email domains extracted (free providers excluded)

## Screenshots to Capture

1. Dashboard after login
2. GET /api/risk/settings response
3. PUT enable AI extraction response
4. Uploaded email chain with AI extraction
5. Validation results with ai_assisted field
6. Extracted entities breakdown
7. Comparison: AI vs regex extraction
8. Role protection error (if tested)
9. Final state after cleanup

## Error Scenarios to Note

- If OPENAI_API_KEY is not configured:
  - AI extraction will be unavailable
  - extraction_method will be "regex" even when setting is enabled
  - This is expected behavior

- If OpenAI API times out:
  - extraction_method will be "regex_fallback"
  - ai_assisted will be false
  - This is expected fallback behavior

- If user lacks admin/risk_manager role:
  - PUT endpoint returns 403 Forbidden
  - GET endpoint should still work for risk_analyst

- If database migration not applied:
  - Settings endpoints will return 500 Internal Server Error
  - Apply migration before testing
