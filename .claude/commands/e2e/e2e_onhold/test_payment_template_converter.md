# E2E Test: Payment Template Converter (Tesorería)

Test the payment history file upload and NetSuite template conversion workflow for Treasury department.

## User Story

As a Treasury (Tesorería) department user
I want to upload payment history files ("Historial de Pagos") and convert them to NetSuite payment application templates
So that I can efficiently apply payments in NetSuite with the correct account mappings and concept breakdowns

## Prerequisites

- User logged in with `tesoreria` or `admin` role
- Backend and frontend servers running
- Test Excel file with Historial de Pagos format available

## Test Fixture File

**Location**: `.claude/commands/e2e/fixtures/test_historial_pagos_co.xlsx`

This fixture contains 3 test rows with:
- Required columns: Cliente, Identificación del cliente, Código de desembolso, etc.
- Concept columns: Capital, 4x1000, Fondo de garantías, Intereses, etc.
- Optional columns: NT (one row with "NT" for Operaciones Cedidas), Cuenta Remitente, Spread

## Test Excel File Requirements

The test Excel file (Historial de Pagos) must contain columns including:
- Cliente - Client name
- Identificación del cliente - Customer external ID (NIT)
- Código de desembolso - Invoice core ID
- Código de recaudo - Payment reference
- Fecha de pago - Payment date
- Moneda - Currency
- Capital - Principal amount
- 4x1000 - Transaction tax (Colombia)
- Fondo de garantías - Guarantee fund
- Intereses Corrientes - Regular interest
- Banco remitente - Remitting bank
- NT - Operaciones Cedidas flag (Colombia only)

## Test Steps

1. **Login as tesorería or admin user**

2. Navigate to `/tesoreria/plantillas-netsuite`

3. Take a screenshot of the landing page

4. **Verify** landing page elements are present:
   - Page title "Plantillas para Cargar NetSuite"
   - Colombia country card with description
   - México country card with description
   - Navigation links to country-specific converters

5. Click on "Colombia" card to navigate to Colombia converter

6. **Verify** URL is `/tesoreria/plantillas-netsuite/colombia`

7. Take a screenshot of the Colombia converter page

8. **Verify** Colombia converter page elements:
   - Page title "Aplicación de Pagos - Colombia"
   - Back button to landing page
   - File upload area (drag & drop zone)
   - Instructions about required file format
   - Convert button (initially disabled)

9. Click on upload area or file input

10. Select test Historial de Pagos Excel file (.xlsx)

11. **Verify** file upload begins (loading indicator)

12. Wait for file validation to complete

13. **Verify** validation preview appears:
    - Source row count displayed
    - Column validation status (all required columns found)
    - Estimated output rows calculation
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
    - Statistics show: rows processed, output rows generated, any skipped rows

19. Take a screenshot of completion state with statistics

20. Navigate back to landing page

21. Click on "México" card

22. **Verify** URL is `/tesoreria/plantillas-netsuite/mexico`

23. Take a screenshot of the México converter page

24. **Verify** México converter page elements:
    - Page title "Aplicación de Pagos - México"
    - Same UI pattern as Colombia page
    - File upload area present

## Success Criteria

- Landing page loads correctly with Colombia/México options
- Country cards navigate to correct routes
- Colombia converter page loads with all required elements
- File upload accepts .xlsx files only
- Validation preview displays correct statistics
- Convert button enables after successful validation
- Conversion generates downloadable Excel file
- México converter page follows same pattern as Colombia
- Role protection works (non-tesorería users cannot access)
- 5 screenshots are captured:
  1. Landing page with country selection
  2. Colombia converter page initial state
  3. Validation preview after file upload
  4. Conversion completion with statistics
  5. México converter page

## Error Handling to Verify

- Invalid file format (.csv, .pdf) shows appropriate error message
- Missing required columns are flagged with specific column names
- Empty file shows meaningful error
- File too large shows size limit error
- Network errors during upload/conversion show user-friendly message
- Unauthorized users (non-tesorería role) are redirected or shown access denied

## API Endpoints Exercised

- `POST /api/tesoreria/validate/{country}` - Validate uploaded file
- `POST /api/tesoreria/convert/{country}` - Convert and download template

## Notes

- Colombia and México have different concept types and AR account mappings
- Colombia has special handling for NT column (Operaciones Cedidas)
- Output file should have NetSuite-compatible column format
- Each source row may generate multiple output rows (one per non-zero concept)
