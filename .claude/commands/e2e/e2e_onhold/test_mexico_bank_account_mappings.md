# E2E Test: Mexico Bank Account Mappings

Test the new Mexico bank account mappings for Aplicacion de Pagos NetSuite template conversion.

## User Story

As a Treasury (Tesorería) department user
I want the system to correctly map Mexico bank account numbers to NetSuite codes in the Aplicacion de Pagos output
So that payments are automatically assigned to the correct NetSuite accounts without manual intervention

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with Mexico Historial de Pagos format with the new bank accounts

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_mx_bank_accounts.xlsx`

This fixture contains test rows with:
- Required columns: Cliente, Identificación del cliente, Código de desembolso, etc.
- Key column: `Cuenta Remitente` with values `012180001189708826` and `738250227`
- At least one concept column (e.g., Capital, Intereses)

## Test Excel File Requirements

The test Excel file (Historial de Pagos México) must contain columns including:
- Cliente - Client name
- Identificación del cliente - Customer external ID (RFC)
- Código de desembolso - Invoice core ID
- Código de recaudo - Payment reference
- Fecha de pago - Payment date
- Moneda - Currency
- Capital - Principal amount
- Cuenta Remitente - Sender bank account number (the key field being tested)

## Test Steps

1. **Login as tesorería or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite`

3. Take a screenshot of the landing page

4. **Verify** landing page elements are present:
   - Page title "Plantillas para Cargar NetSuite"
   - México country card with description

5. Click on "México" card to navigate to México converter

6. **Verify** URL is `/tesoreria/plantillas-netsuite/mexico`

7. Take a screenshot of the México converter page

8. **Verify** México converter page elements:
   - Page title "Aplicación de Pagos - México"
   - Back button to landing page
   - File upload area (drag & drop zone)
   - Convert button (initially disabled)

9. Click on upload area or file input

10. Select test Historial de Pagos México Excel file (.xlsx) containing the new bank accounts

11. **Verify** file upload begins (loading indicator)

12. Wait for file validation to complete

13. **Verify** validation preview appears:
    - Source row count displayed
    - Column validation status (all required columns found)
    - No critical validation errors

14. Take a screenshot of validation preview

15. **Verify** Convert button is now enabled

16. Click "Convertir y Descargar" button

17. **Verify** conversion starts:
    - Loading/progress indicator appears
    - Button becomes disabled during processing

18. **Verify** conversion completes:
    - Download starts automatically or download link appears
    - Success message with conversion statistics displayed

19. Take a screenshot of completion state with statistics

20. **Verify** the downloaded Excel file:
    - Row with Cuenta Remitente `012180001189708826` has `account` field = `2111`
    - Row with Cuenta Remitente `738250227` has `account` field = `2519`
    - Row with Cuenta Remitente `12180001189708826` (no leading zero) has `account` field = `2111`

## Success Criteria

- México converter page loads correctly
- File upload accepts .xlsx files
- Validation preview displays correct statistics
- Convert button enables after successful validation
- Conversion generates downloadable Excel file
- **New bank account mappings are applied correctly:**
  - `012180001189708826` → `2111`
  - `738250227` → `2519`
  - `12180001189708826` → `2111` (without leading zero)
- 4 screenshots are captured:
  1. Landing page with country selection
  2. México converter page initial state
  3. Validation preview after file upload
  4. Conversion completion with statistics

## Error Handling to Verify

- Missing required columns are flagged with specific column names
- Empty file shows meaningful error
- Unauthorized users (non-tesorería role) are redirected or shown access denied

## API Endpoints Exercised

- `POST /api/tesoreria/validate/mexico` - Validate uploaded file
- `POST /api/tesoreria/convert/mexico` - Convert and download template

## Notes

- This test validates the new bank account mappings added for issue #4
- Account `012180001189708826` should map to NetSuite code `2111`
- Account `738250227` should map to NetSuite code `2519`
- The leading zero variant is also tested (`12180001189708826` → `2111`)
- Output file should have NetSuite-compatible column format with `account` field populated
