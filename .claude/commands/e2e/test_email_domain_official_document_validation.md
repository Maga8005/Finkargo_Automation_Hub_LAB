# E2E Test: Email Domain Official Document Validation

Test email chain sender domain validation against official document (RUT/Certificado de Existencia) email domains.

## User Story

As a Risk Analyst or Risk Manager
I want to validate email chain sender domains against official document email domains
So that I can detect potential fraud attempts where attackers use similar-looking domains (typosquatting) to impersonate legitimate companies

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation with RUT document uploaded (containing official email domain)

## Test Credentials

Use test account with appropriate role:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. **Verify** risk evaluations list is displayed
7. Take a screenshot of the Risk Dashboard
8. Create a new evaluation or select an existing one
9. Navigate to document upload section
10. Upload a RUT document that contains official email (e.g., `contacto@empresa-oficial.com`)
11. **Verify** document extraction completes with email domain extracted
12. Take a screenshot of the document extraction result
13. Navigate to "Contacto Externo" tab (Tab 3)
14. Take a screenshot of the External Contact tab
15. **Verify** the "Cadenas de Email" section is visible
16. Test pasting raw email text with mismatched domain:
    - Paste sample email text into the textarea:
      ```
      From: ventas@empresa-oficial.com.co
      To: comercial@finkargo.com
      Date: Mon, 23 Dec 2024 10:00:00 -0500
      Subject: Solicitud de Pago - Empresa Oficial

      Estimados,

      Por favor proceder con el pago a la cuenta indicada.
      NIT: 900.123.456-7
      Representante Legal: María García

      Saludos,
      Equipo Ventas
      ```
    - Note: The sender domain `empresa-oficial.com.co` differs from the RUT email domain `empresa-oficial.com`
17. Click "Subir" button
18. **Verify** email chain appears in the list with "Pendiente" status
19. Take a screenshot of the uploaded email chain
20. Click "Validar" button for the uploaded chain
21. Wait for validation to complete
22. **Verify** validation results include a CRITICAL discrepancy for `official_document_domain`:
    - Field labeled as "Dominio Email Documento Oficial"
    - Severity is CRITICAL
    - Description mentions the domain mismatch (e.g., `empresa-oficial.com.co` vs `empresa-oficial.com`)
23. Take a screenshot of the validation results showing the official document domain discrepancy
24. **Verify** validation status changes to "Crítico" due to the discrepancy
25. Take a screenshot of the final state showing critical status

## Success Criteria

- Login completes successfully
- RUT document can be uploaded with email extraction
- Email chain can be uploaded via text paste
- Validation triggers and completes
- CRITICAL discrepancy is flagged for `official_document_domain` when:
  - Sender domain (`empresa-oficial.com.co`) differs from official document email domain (`empresa-oficial.com`)
- Discrepancy displays with:
  - Field label: "Dominio Email Documento Oficial"
  - Severity: CRITICAL
  - Description explaining the TLD variation mismatch
- `is_typosquatting` flag is true for the discrepancy
- 6 screenshots are captured:
  1. Risk Dashboard
  2. Document extraction result showing extracted email
  3. External Contact tab with email chain uploader
  4. Uploaded email chain (pending status)
  5. Validation results with official_document_domain discrepancy
  6. Final state showing critical status

## Edge Cases to Test

### Case 1: No Official Document Domains Available
- If no RUT or Certificado de Existencia documents have email domains
- Expected: Validation passes for this check (no discrepancy created)

### Case 2: Exact Domain Match
- Sender domain exactly matches official document domain
- Expected: Validation passes (no discrepancy)

### Case 3: Typosquatting Detection
- Sender: `empresa-oficia1.com` (number 1 instead of letter l)
- Official: `empresa-oficial.com`
- Expected: CRITICAL discrepancy with is_typosquatting=true

### Case 4: Complete Mismatch
- Sender: `otrodominio.com`
- Official: `empresa-oficial.com`
- Expected: CRITICAL discrepancy

### Case 5: Free Email Provider
- Sender: `gmail.com`
- Official: `empresa-oficial.com`
- Expected: CRITICAL discrepancy for official_document_domain (in addition to existing free provider warning)

## Error Scenarios to Note

- Missing RUT/Certificado document should not cause errors (validation skips comparison)
- Malformed email in official document should be handled gracefully
- Network errors during validation should show appropriate message
