# E2E Test: Email Chain PDF Upload

Test PDF file upload for email chain validation in the Finkargo Risk Assessment system.

## User Story

As a Risk Analyst or Risk Manager
I want to upload PDF files containing email correspondence to the email chain validator
So that I can analyze printed or exported email communications for potential fraud indicators when the original email file format (.eml/.msg) is not available

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account exists with risk_analyst or risk_manager role
- An existing risk evaluation with documents uploaded (for cross-validation comparison)
- Sample PDF file containing email correspondence text

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: risk_analyst or risk_manager

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** redirect to login page if not authenticated
3. Log in with test credentials
4. Wait for redirect to dashboard
5. Navigate to Risk Dashboard (/risk)
6. **Verify** risk evaluations list is displayed
7. Take a screenshot of the Risk Dashboard
8. Click on an existing evaluation with documents
9. **Verify** evaluation detail page loads
10. Navigate to "Contacto Externo" tab (Tab 3)
11. Take a screenshot of the External Contact tab
12. **Verify** the "Cadenas de Email" section is visible
13. Click "Subir Archivo" mode button
14. **Verify** file upload area shows:
    - Button text mentions ".pdf" format: "Seleccionar archivo .eml, .msg o .pdf"
    - Maximum file size note: "Maximo 10MB"
15. Take a screenshot of the file upload interface showing PDF support
16. Select a sample PDF file for upload (containing email text content)
17. Wait for upload to complete
18. **Verify** the PDF file appears in the email chains list with:
    - Original filename displayed
    - "Pendiente" validation status
19. Take a screenshot of the uploaded PDF chain
20. Click "Validar" button for the uploaded PDF chain
21. Wait for validation to complete
22. **Verify** validation results are displayed:
    - Parsed data shows extracted information from PDF
    - Sender domain analysis (if email addresses found)
    - Company name mentions (if found in text)
    - NIT mentions (if found in text)
23. **Verify** validation status changes from "Pendiente" to appropriate status:
    - "Validado" if no issues
    - "Sospechoso" if suspicious indicators
    - "Crítico" if critical discrepancies
24. Take a screenshot of the validation results
25. Test deleting the PDF email chain:
    - Click delete button on the uploaded chain
    - **Verify** chain is removed from the list
26. Take a screenshot of the final state

## Success Criteria

- Login completes successfully
- Risk Dashboard loads with evaluations
- External Contact tab shows email chain section
- File upload interface shows PDF as accepted format (.eml, .msg, .pdf)
- PDF file can be uploaded successfully
- Uploaded PDF chain appears in the list with correct filename
- Validation triggers and completes on PDF content
- Validation results display with:
  - Extracted text data from PDF
  - Email pattern detection results
  - Any discrepancy indicators if applicable
- PDF email chain can be deleted
- 6 screenshots are captured:
  1. Risk Dashboard
  2. External Contact tab with email chain uploader
  3. File upload interface showing PDF support
  4. Uploaded PDF chain (pending status)
  5. Validation results
  6. Final state after deletion

## Error Scenarios to Note

- Invalid PDF format should show validation error: "El archivo PDF esta corrupto o tiene un formato invalido"
- PDF with no extractable text should show error: "No se pudo extraer texto del archivo PDF"
- Password-protected PDF should show error: "El archivo PDF esta protegido con contrasena"
- Large files (>10MB) should be rejected with message: "El archivo es demasiado grande. Maximo 10MB"
- Non-PDF/EML/MSG files should be rejected with message: "Solo se aceptan archivos .eml, .msg o .pdf"

## Test Data

For testing, create a sample PDF file with this content:

```text
From: comercial@empresa-real.com.co
To: legal@finkargo.com
Date: Mon, 23 Dec 2024 14:30:00 -0500
Subject: RE: Contrato de Importacion

Estimados,

Adjunto los documentos solicitados para el tramite de importacion.

Empresa: IMPORTADORA REAL S.A.S
NIT: 901.234.567-8
Representante Legal: Maria Garcia Lopez

Quedamos atentos a sus comentarios.

Cordialmente,
Departamento Comercial
IMPORTADORA REAL S.A.S
Tel: +57 1 234 5678
```

Save this as a PDF for the upload test.
