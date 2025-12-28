# E2E Test: Email/Contact Information Correlation Tab

Test the external contact email validation functionality in the risk evaluation detail page.

## User Story

As a Mesa de Control user (risk_analyst role)
I want to input the sender's email address received via commercial channels and validate it against document data
So that I can detect potential typosquatting fraud attempts before approving a risk evaluation

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or mesa_control role
- At least one risk evaluation exists in the system

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: risk_analyst

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Login with risk_analyst credentials
4. Navigate to Risk Dashboard (/risk/dashboard)
5. **Verify** risk dashboard loads successfully
6. Click on an existing evaluation to open the detail page
7. Take a screenshot of the evaluation detail page
8. Click on the "Contacto Externo" tab (Tab index 3)
9. **Verify** the tab content is visible with:
   - Form to add new external contact
   - Email input field
   - Sender name input field (optional)
   - Source dropdown
   - Notes text field
   - "Agregar Contacto" button
10. Take a screenshot of the empty "Contacto Externo" tab
11. Fill in the external contact form:
    - Email: test@azelis.com.co
    - Sender name: Juan Perez
    - Source: comercial_team
    - Notes: Recibido via WhatsApp
12. Click "Agregar Contacto" button
13. **Verify** the contact is added to the list
14. Take a screenshot of the contact added to the list
15. Click "Validar Dominio" button for the added contact
16. Wait for validation to complete (loading state)
17. **Verify** validation result is displayed with:
    - Validation status chip (validated, suspicious, or critical)
    - Similarity percentage if typosquatting detected
    - Description of the validation result
18. Take a screenshot of the validation result
19. For a typosquatting case (e.g., azelis.com.co vs azelis.com):
    - **Verify** warning alert is shown
    - **Verify** "TLD variation" or "Typosquatting" detection type is displayed
    - **Verify** similar domain is shown (e.g., "Similar to: azelis.com")
20. Add another contact with a free email provider:
    - Email: contact@gmail.com
    - Sender name: Maria Lopez
    - Source: comercial_team
21. Click "Validar Dominio" for the gmail contact
22. **Verify** medium severity warning is shown for free email provider
23. Take a screenshot showing multiple contacts with validation results
24. Click the delete button for one of the contacts
25. **Verify** contact is removed from the list
26. Take a screenshot of the final state

## Success Criteria

- "Contacto Externo" tab appears in risk evaluation detail (Tab index 3)
- Form accepts email, sender name, source, and notes input
- "Agregar Contacto" button successfully adds contact to the list
- Added contacts appear in a list below the form
- "Validar Dominio" button triggers email domain validation
- Validation results display:
  - Status chip with appropriate color (green=valid, orange=medium, red=critical)
  - Similarity score for typosquatting detection
  - Detection type (typosquatting, tld_variation, provider_domain, etc.)
  - Description explaining the result
- TLD variations (e.g., .com vs .com.co) are flagged appropriately
- Free email providers (gmail.com) are flagged as medium severity
- Delete button removes contacts from the list
- 6 screenshots are captured:
  1. Evaluation detail page
  2. Empty "Contacto Externo" tab
  3. Contact added to list
  4. Validation result displayed
  5. Multiple contacts with validation results
  6. Final state after delete

## Error Scenarios to Note

- Empty email should show validation error
- Invalid email format should show format error
- Network errors during validation should display error message
- Failed validation should not crash the tab
