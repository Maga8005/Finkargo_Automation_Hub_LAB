# E2E Test: Directory Scanner Error Display

Test that error messages in the Directory Scanner page are displayed as human-readable text instead of `[object Object]`.

## User Story

As a Treasury team member
I want to see clear, readable error messages when directory scanning fails
So that I can understand what went wrong and take appropriate action

## Prerequisites

- Backend and frontend servers running
- User has access to the Treasury > Directory Scanner page
- No authentication required for this page (or user is logged in)

## Test Steps

1. Navigate to the Directory Scanner page at `/treasury/directory-scanner`
2. Take a screenshot of the initial Directory Scanner page
3. **Verify** the page loads with:
   - Directory path input field
   - Output file name input (optional)
   - "Extraer Números de Declaración" checkbox
   - "Escaneo Recursivo" checkbox
   - "Escanear Directorio" button

4. Clear the directory path input and enter an invalid/non-existent path:
   - Enter: `C:/NonExistent/Invalid/Path/That/Does/Not/Exist`

5. Take a screenshot showing the invalid path entered
6. Click the "Escanear Directorio" button
7. Wait for the error response (should be quick since path doesn't exist)

8. **Verify** error message is displayed:
   - An error alert appears
   - The error message is NOT `[object Object]`
   - The error message contains human-readable text
   - The error message should mention something about invalid path or directory not found

9. Take a screenshot of the error message displayed
10. **Verify** the error message contains actual words (not just symbols or object notation)

11. Close the error alert by clicking the X button
12. **Verify** the error alert is dismissed

## Alternative Error Test (Empty Path)

13. Clear the directory path input completely (leave it empty)
14. **Verify** the "Escanear Directorio" button becomes disabled or validation error appears
15. Take a screenshot showing the validation state

## Success Criteria
- Directory Scanner page loads correctly
- When scanning fails with an invalid path, error message is readable
- Error message does NOT contain `[object Object]`
- Error message contains Spanish text explaining the error (e.g., "Invalid directory path", "Ruta de directorio inválida", or backend error message)
- User can dismiss the error alert
- Form validation prevents scanning with empty path
- 4 screenshots are captured:
  1. Initial Directory Scanner page
  2. Form with invalid path entered
  3. Error message displayed
  4. Validation state with empty path

## Error Messages to Check For

Valid error messages should be like:
- "Invalid directory path: ..."
- "Directory scan failed: ..."
- "Ruta de directorio inválida"
- "Error al escanear directorio"
- "La operación tardó demasiado tiempo..."

Invalid error display (BUG):
- `[object Object]`
- Empty string
- Raw JSON objects

## Notes

- This test validates the fix for the `[object Object]` error display bug
- The `extractErrorMessage` utility should properly format all error types
- Both the form Alert and page Snackbar should display proper messages
