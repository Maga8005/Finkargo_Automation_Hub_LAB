# E2E Test: Mexico Finance Excel Upload

Test the Excel upload and invoice processing workflow for Mexico invoicing automation.

## User Story

As a Finance team member  
I want to upload an Excel file with invoice data  
So that I can match invoices with PDFs/XMLs from Google Drive and download a ZIP package

## Prerequisites

- User logged in (any authenticated role)
- Backend and frontend servers running
- Test Excel file with required columns available
- Google Drive integration configured (for full flow)

## Test Excel File Requirements

The test Excel file must contain these columns:
- UUID - Invoice unique identifier
- CODIGO DE OPERACIÓN - Operation code
- Conceptos - Invoice concepts
- Fecha emision - Issue date
- RFC receptor - Recipient RFC
- Razon receptor - Recipient business name
- SubTotal - Subtotal amount
- IVA Trasladado - Transferred VAT
- IVA Exento - Exempt VAT
- Total - Total amount

## Test Steps

1. **Login as authenticated user**
2. Navigate to `/finance/reporteria-automatica-mx`
3. Take a screenshot of the Finance/Mexico Invoicing dashboard
4. **Verify** dashboard elements are present:
   - Excel upload area (FKExcelUploader component)
   - Instructions or column requirements
   - Session status (if any)

5. Click on upload area or file input
6. Select test Excel file for upload
7. **Verify** file upload begins (loading indicator)
8. Wait for file processing to complete
9. **Verify** validation results appear:
   - Row count displayed
   - Column validation status
   - Any validation errors highlighted

10. Take a screenshot of parsed data preview

11. **Verify** parsed data displays correctly:
    - Table/grid shows invoice data
    - Required columns are populated
    - Row count matches expected

12. If search/filter functionality exists:
    - Enter a search term (e.g., RFC or UUID)
    - **Verify** results filter correctly

13. Take a screenshot of filtered/searched results

14. Click "Generar ZIP" or equivalent button to generate download package
15. **Verify** ZIP generation initiates:
    - Loading/progress indicator appears
    - Google Drive sync occurs (if applicable)

16. **Verify** ZIP generation completes:
    - Download starts or download link appears
    - Success message displayed

17. Take a screenshot of completion state

## Success Criteria
- Dashboard loads correctly
- Excel file upload works
- File validation identifies required columns
- Parsed data displays in readable format
- Search/filter functionality works (if present)
- ZIP generation completes without errors
- 4 screenshots are captured:
  1. Initial Finance dashboard
  2. Parsed data preview after upload
  3. Search/filter results
  4. ZIP generation completion

## Error Handling to Verify
- Invalid file format shows appropriate error
- Missing required columns are flagged
- Large file uploads are handled
- Network errors during upload show user-friendly message

## API Endpoints Exercised
- POST `/api/finance/upload-excel`
- POST `/api/finance/search`
- GET `/api/finance/session/{id}/stats`
- POST `/api/finance/generate-zip`
