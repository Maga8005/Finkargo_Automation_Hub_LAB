# E2E Test: Inventario Bodega AI-Powered RUT Extraction

Test the AI extraction feature for image-based RUT documents in the Inventario Bodega contract workflow.

## User Story

As an Operations team member
I want to use AI-powered extraction for scanned/image-based RUT documents
So that I can successfully process Inventario Bodega contracts even when the RUT PDF is not text-selectable

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with `operations` role
- `LANDINGAI_API_KEY` environment variable configured in backend
- Test client exists in database (searchable by NIT)
- Sample scanned RUT PDF available for testing

## Test Credentials

Use test account:
- Email: test-operations@finkargo.com
- Password: [configured test password]
- Expected Role: operations

## Test Steps

### Part 1: Access Inventario Bodega Form

1. **Login as Operations user** (or verify already logged in with operations role)
2. Navigate to `/operations/contratos-colombia`
3. **Verify** dashboard loads with contract tabs
4. Click on "Inventario Bodega" tab or navigate to Inventario Bodega request section
5. Take a screenshot of the Inventario Bodega request form

### Part 2: Verify AI Extraction Checkbox Presence

6. **Verify** the search client section is visible
7. Search for a test client by NIT
8. Select the test client from results
9. **Verify** the RUT file upload section appears
10. Upload a test RUT PDF file
11. **Verify** file upload success indicator appears
12. **Verify** AI extraction checkbox is visible after file upload:
   - Checkbox with label "Usar extracción AI (para PDFs escaneados)"
   - Checkbox is unchecked by default
13. Hover over the checkbox or info icon
14. **Verify** tooltip appears with message about AI extraction:
   - Should mention "más robusto"
   - Should mention processing time (30-60 segundos)
15. Take a screenshot showing the AI extraction checkbox with tooltip

### Part 3: Submit with AI Extraction Enabled

16. Check the "Usar extracción AI" checkbox
17. **Verify** checkbox is now checked
18. Take a screenshot showing checked checkbox
19. Click the submit/request button ("Solicitar Inventario Bodega de 3ro")
20. **Verify** loading indicator appears
21. **Verify** loading message indicates AI processing (should show longer loading time than normal)
22. Wait for submission to complete (allow up to 90 seconds for AI processing)

### Part 4: Verify Success

23. **Verify** success message appears confirming contract request was submitted
24. **Verify** contract ID is displayed (format: INV-YYYY-XXX)
25. Take a screenshot of the success message
26. **Verify** form is reset for next entry

## Success Criteria
- Inventario Bodega form loads with all expected fields
- AI extraction checkbox appears after RUT file upload
- Tooltip correctly explains the AI extraction feature
- Checkbox defaults to unchecked
- When checked, form submission includes AI extraction flag
- Loading state is visible during AI processing
- Contract is successfully created with extracted custodian data
- 5 screenshots are captured:
  1. Initial Inventario Bodega form
  2. AI extraction checkbox with tooltip visible
  3. Checked checkbox before submission
  4. Loading state during AI processing (if capturable)
  5. Success message after contract creation

## Form Elements to Verify
- Client search input field
- Client selection/autocomplete
- RUT file upload button (accepts PDF only)
- File upload success indicator
- AI extraction checkbox (with label and tooltip)
- Submit button ("Solicitar Inventario Bodega de 3ro")
- Loading spinner during submission
- Success/error alerts

## Error Scenarios to Note
- Missing LANDINGAI_API_KEY: Should show server error message
- AI extraction timeout: Should show timeout error after 120 seconds
- Invalid RUT document: Should show extraction failure message
- Network errors: Should be handled gracefully with retry suggestion

## Notes
- AI extraction takes 30-60 seconds, test should allow adequate wait time
- If LANDINGAI_API_KEY is not configured, the test will fail at submission step
- The checkbox only appears after a RUT file is uploaded
- Default behavior (checkbox unchecked) uses fast text-based extraction
