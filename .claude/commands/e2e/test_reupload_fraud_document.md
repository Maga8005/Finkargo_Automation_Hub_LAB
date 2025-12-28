# E2E Test: Fraud Risk Module - Document Reupload Functionality

Test the document delete/reupload functionality in the fraud risk evaluation workflow.

## User Story

As a Risk Analyst or Risk Manager
I want to remove an uploaded document and reupload a correct one
So that I can ensure the correct document is being processed for fraud detection analysis, even if I initially uploaded the wrong file

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Database migrations applied (risk tables)
- Admin account exists (admin@finkargo.com) with full system access
- At least one risk evaluation exists (can be in any status)
- Sample PDF files for testing document upload

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: admin (can access all risk features)

## Test Steps

### Part 1: Authentication and Access

1. Navigate to the `Application URL` (http://localhost:5173)
2. **Verify** login page is displayed
3. Enter admin email (`$TEST_ADMIN_EMAIL`) in email field
4. Enter admin password (`$TEST_ADMIN_PASSWORD`) in password field
5. Click "Iniciar sesión" button
6. **Verify** login succeeds and redirects to homepage
7. Navigate to `/risk/dashboard`
8. **Verify** user can access `/risk/dashboard` (page loads successfully)
9. Take a screenshot of successful dashboard access

### Part 2: Navigate to Evaluation with Documents

10. Find an evaluation in the table (any status)
11. Click on the evaluation row to view details
12. **Verify** navigation to `/risk/evaluations/:id`
13. Click on the "Documentos" tab if not already active
14. **Verify** the FKDocumentUploader component is visible
15. Take a screenshot of the documents section

### Part 3: Upload Initial Document

16. Find a document type that has no upload yet (shows "Subir Documento" button)
17. Click "Subir Documento" button for that document type (e.g., "RUT")
18. Select a valid PDF file from the file system
19. **Verify** upload progress is shown
20. **Verify** extraction process begins (shows "Extrayendo..." status)
21. Wait for extraction to complete (30-60 seconds)
22. **Verify** document shows status chip (Completado, Fallido, or Pendiente)
23. **Verify** trash icon button appears next to the document
24. Take a screenshot of uploaded document with trash icon visible

### Part 4: Delete Document

25. Locate the trash icon button on the uploaded document card
26. **Verify** trash icon is clickable
27. Click the trash icon button
28. **Verify** deletion is in progress (button shows loading spinner or disabled state)
29. **Verify** after deletion, the document card resets to show "Subir Documento" button
30. **Verify** trash icon is no longer visible for that document type
31. Take a screenshot showing document ready for re-upload

### Part 5: Reupload New Document

32. Click "Subir Documento" button for the same document type
33. Select a different PDF file from the file system
34. **Verify** upload and extraction process begins
35. Wait for extraction to complete
36. **Verify** new document is shown with appropriate status
37. **Verify** trash icon appears again for the new upload
38. Take a screenshot of successfully re-uploaded document

### Part 6: Cross-Validation Impact

39. If the evaluation had cross-validation results previously:
    a. **Verify** cross-validation results are cleared after document deletion
    b. **Verify** user can re-run cross-validation with the new document
40. If no cross-validation was run:
    a. Proceed to verify the "Ejecutar Validación Cruzada" button state
41. Take a screenshot showing cross-validation section state

### Part 7: Edge Cases

42. Test deleting a document that is still processing (if applicable):
    a. Upload a document
    b. Immediately click the trash icon while extraction is in progress
    c. **Verify** the deletion still works
43. Test multiple delete-reupload cycles:
    a. Delete a document
    b. Reupload
    c. Delete again
    d. **Verify** each cycle works correctly
44. Take a screenshot of final state

## Success Criteria

- Trash icon appears next to documents that have been uploaded (any status: pending, processing, completed, failed)
- Clicking trash icon deletes the document extraction record
- After deletion, the upload button is re-enabled for that document type
- Deletion works for documents in any status (pending, processing, completed, failed)
- If cross-validation was previously run, results should be cleared
- User can successfully upload a new document after deleting the previous one
- Appropriate loading states are shown during deletion
- Error messages are displayed if deletion fails
- The feature works for all 6 document types

## Error Scenarios to Note

- Network errors during deletion should show error message and allow retry
- Deletion of processing documents should cancel the extraction
- Multiple rapid delete clicks should be handled gracefully (debounced)
- If the API returns an error, the UI should show an error message

## Expected Screenshots

1. Dashboard access after login
2. Documents section initial state
3. Uploaded document with trash icon visible
4. Document reset after deletion (showing upload button)
5. Successfully re-uploaded document
6. Cross-validation section state after document change
7. Final state after multiple operations
