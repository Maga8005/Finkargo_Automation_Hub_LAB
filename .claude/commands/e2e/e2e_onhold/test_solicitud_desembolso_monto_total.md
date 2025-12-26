# E2E Test: Solicitud de Desembolso Monto Total Calculation

Test that the Monto Total is calculated as a numeric sum (not string concatenation) in the Solicitud de Desembolso form.

## User Story

As an Operations team member
I want the Monto Total field to display the correct sum of all Anexo I items
So that the disbursement request shows accurate financial totals

## Bug Description (Regression Test)

**Previous Bug**: After uploading a Cotización PDF, the Monto Total displayed a concatenated string instead of a numeric sum:
- **Expected**: `$739,860 COP` (sum of 407,001 + 290,000 + 42,859)
- **Actual**: `$0407001.00290000.0042859.00 COP` (string concatenation)

**Root Cause**: Backend serialized `Decimal` as strings in JSON, frontend performed string concatenation with `+` operator instead of numeric addition.

**Fix Applied**: Frontend now converts `monto` values from strings to numbers when receiving data from the API.

## Prerequisites

- User logged in with `operations` role
- Backend and frontend servers running
- Test PDF file available: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`
- Client exists in the database that can be searched

## Test Credentials

Use test account for operations role:
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

1. **Login as Operations user** (or verify already logged in with operations role)

2. Navigate to `/operations/paga-local-colombia`

3. **Verify** page loads with tabs visible

4. Click on "Documentos Operación" tab

5. **Verify** sub-tabs appear with "Solicitud Desembolso" visible

6. Click on "Solicitud Desembolso" sub-tab

7. Take a screenshot showing the empty form (screenshot 1)

8. **Search for a client:**
   - Enter a client NIT or name in the search field (e.g., "900436389")
   - Click "Buscar" button
   - Wait for search results
   - Select a client from results

9. **Verify** client selection shows success message

10. **Upload Cotización PDF:**
    - Click "Seleccionar Archivo PDF" button
    - Upload the test file: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`
    - **Verify** file name appears on the button

11. Click "Extraer Datos del PDF" button

12. Wait for extraction to complete

13. Take a screenshot showing Section 3 "Datos de la Solicitud" with the Monto Total field (screenshot 2)

14. **CRITICAL VERIFICATION - Monto Total Field:**
    - Locate the "Monto Total" text field in Section 3
    - **Verify** the value is a properly formatted numeric sum, NOT a concatenated string
    - Expected format: `$739,860 COP` or similar comma-separated thousands
    - FAIL if value looks like: `$0407001.00290000.0042859.00 COP`

15. Scroll down to Section 4 "Anexo I - Detalle de Pagos"

16. Take a screenshot showing the Anexo I table with TOTAL row (screenshot 3)

17. **CRITICAL VERIFICATION - Table TOTAL Row:**
    - Locate the TOTAL row at the bottom of the Anexo I table
    - **Verify** the total is a properly formatted numeric sum
    - Expected: `$739,860 COP` or similar
    - FAIL if value looks like: `$0407001.00290000.0042859.00 COP`

18. **Verify** individual monto values in table are displayed as numbers (not strings):
    - Row 1: ~407,001
    - Row 2: ~290,000
    - Row 3: ~42,859

19. Take final screenshot showing entire form populated correctly (screenshot 4)

## Success Criteria

- Solicitud de Desembolso form loads without errors
- PDF upload and extraction completes successfully
- **PRIMARY CHECK**: Monto Total in Section 3 displays numeric sum (e.g., `$739,860 COP`)
- **PRIMARY CHECK**: TOTAL row in Anexo I table displays numeric sum
- NO string concatenation visible (no values like `$0407001.00290000.0042859.00`)
- All Anexo I items display individual amounts as formatted numbers
- 4 screenshots are captured:
  1. Empty Solicitud de Desembolso form
  2. Section 3 with Monto Total field after extraction
  3. Anexo I table with TOTAL row
  4. Complete populated form

## Failure Indicators

The test FAILS if ANY of these are observed:
- Monto Total shows a very long number with no thousands separators
- Monto Total contains multiple decimal points (e.g., `0407001.00290000.00`)
- TOTAL row shows concatenated values
- Console shows `TypeError` or `NaN` related to monto calculations

## Verification Code (for manual testing)

To verify the fix programmatically, the developer can check browser console:
```javascript
// After PDF extraction, anexoItems should have numeric monto values
// This should log numbers, not strings:
// anexoItems.forEach(item => console.log(typeof item.monto, item.monto))
```
