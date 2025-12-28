# E2E Test: Solicitud de Desembolso PDF Upload

Test the Cotización PDF upload and parsing workflow for the Solicitud de Desembolso feature in Paga Local.

## User Story

As an Operations team member
I want to upload a Cotización PDF to pre-populate the Solicitud de Desembolso form
So that I can quickly generate disbursement request documents with accurate data extracted from the quote

## Prerequisites

- User logged in with `operations` role
- Backend and frontend servers running
- Test PDF file available: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`
- Client with NIT `900436389` exists in the database (or similar test client)

## Test Credentials

Use test account for operations role:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com) (or configured test account)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: operations

## Test Steps

1. **Login as Operations user** (or verify already logged in with operations role)
2. Navigate to the Paga Local section (typically `/operations/paga-local` or similar)
3. Take a screenshot of the Paga Local menu/dashboard
4. **Verify** Paga Local section loads with Solicitud de Desembolso option visible

5. Click on "Solicitud de Desembolso" or navigate to the form
6. **Verify** the Solicitud de Desembolso form appears with PDF upload section
7. Take a screenshot of empty Solicitud de Desembolso form

8. **Upload Cotización PDF:**
   - Locate the PDF upload area/button
   - Upload the test file: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`
   - Wait for upload and parsing to complete

9. **Verify** parsing success:
   - No error message appears
   - Form fields are populated with extracted data:
     - Número de Cotización: `CO:900436389:1:2:DOM`
     - Fecha Cotización: `10/11/2025` or `2025-11-10`
     - Monto Total: `739,860` or similar formatted value
   - Anexo I table is populated with 3 items:
     - Entidad de pago de Impuestos | 1003887257 | COP 407,001.00
     - Entidad de pago de Impuestos | 1003887254 | COP 290,000.00
     - Entidad de pago de Impuestos | 1003887815 | COP 42,859.00

10. Take a screenshot of the populated form showing extracted data

11. **Verify** the Anexo I table displays all 3 extracted items correctly:
    - Each row has acreedor, numero_instrumento, and monto columns
    - Amounts are displayed in COP format

12. Take a screenshot of the Anexo I table section

13. **Verify** total amount calculation:
    - Total shown equals sum of all Anexo items (COP 739,860)

## Success Criteria

- Solicitud de Desembolso form loads without errors
- PDF upload component is accessible and functional
- Cotización PDF is parsed without errors (no "monto_total must be greater than 0" error)
- Extracted data populates form fields correctly:
  - Número de Cotización: `CO:900436389:1:2:DOM`
  - 3 Anexo I items extracted
  - Total amount: 739,860 COP
- User can see all extracted Anexo I items in a table
- 4 screenshots are captured:
  1. Paga Local menu/dashboard
  2. Empty Solicitud de Desembolso form
  3. Populated form after PDF upload
  4. Anexo I table with extracted items

## Error Scenarios to Note

- If PDF upload fails, capture error message in screenshot
- Previous bug showed: "Error al extraer datos del PDF: Error parsing Cotización document: monto_total must be greater than 0"
- This error should NOT appear after the fix
- If any validation errors appear, document them

## Bug Regression Check (snake_case/camelCase Fix)

This test validates the fix for the snake_case/camelCase field mismatch bug:
- **Previous Bug**: After clicking "Extraer Datos del PDF", a black screen appeared with console error:
  `TypeError: Cannot read properties of undefined (reading 'length')` at `FKSolicitudDesembolsoRequest.tsx:401`
- **Root Cause**: Frontend used `extractedData.anexoItems` but backend returns `extractedData.anexo_items`
- **Fix Applied**: Updated frontend types and component to use snake_case field names
- **Key Verification**: After PDF extraction, form should display success message "Datos extraidos exitosamente: X items encontrados" with NO black screen

## Test Data Reference

The test PDF contains:
- **Document Type**: Cotización de Desembolso (ANEXO B)
- **Quote Number**: CO:900436389:1:2:DOM
- **Quote Date**: 10 de noviembre de 2025
- **Credit Contract Date**: 6 de noviembre de 2025
- **Disbursement Amount**: COP 739,860
- **Interest Rate**: 2% monthly
- **Payment Date**: 10 de marzo de 2026

**Anexo I Table (3 valid entries + 57 empty rows):**
| Acreedor | No. Instrumento | Monto (COP) |
|----------|-----------------|-------------|
| Entidad de pago de Impuestos | 1003887257 | 407,001.00 |
| Entidad de pago de Impuestos | 1003887254 | 290,000.00 |
| Entidad de pago de Impuestos | 1003887815 | 42,859.00 |
| **Total** | | **739,860.00** |
