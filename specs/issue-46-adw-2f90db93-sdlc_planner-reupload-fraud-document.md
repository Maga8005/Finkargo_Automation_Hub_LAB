# Feature: Document Reupload for Fraud Risk Module

## Feature Description
Implement functionality in the Riesgos (Fraud Risk) module to allow users to remove/cancel document extractions and reupload documents for analysis. Currently, users can upload 6 documents for AI extraction using LandingAI, but if they upload the wrong document by mistake, there is no way to stop the extraction or remove the extracted document to upload a new one. This feature adds a delete/remove button (trash icon) to stop ongoing extractions or remove completed ones, then re-enable the upload button to allow reuploading the correct document.

## User Story
As a **risk analyst or risk manager**
I want to **remove an uploaded document and reupload a correct one**
So that **I can ensure the correct document is being processed for fraud detection analysis, even if I initially uploaded the wrong file**

## Problem Statement
When users upload documents to the Fraud Risk module for AI extraction, they may accidentally upload the wrong document. Currently, there is no way to:
1. Stop an ongoing AI extraction process for a wrong document
2. Remove a completed extraction to upload the correct document
3. Re-enable the upload functionality for a document type that already has an extraction record

This leads to incorrect data being used in the cross-validation process, potentially causing false fraud alerts or missing actual fraud indicators.

## Solution Statement
Add a delete/remove functionality to each document type card in the `FKDocumentUploader` component:
1. Display a trash icon button next to documents that have been uploaded (pending, processing, completed, or failed status)
2. When clicked, cancel any ongoing extraction and delete the extraction record from the database
3. Reset the UI to show the upload button again, allowing the user to upload the correct document
4. Ensure cross-validation results are invalidated when documents are removed (since they may be based on incorrect data)

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`
- Backend Protection: Use existing `require_roles(['risk_analyst', 'risk_manager'])` dependency in `risk_routes.py`
- Frontend Protection: Component already renders within role-protected routes (`RiskEvaluationDetail` page)

## Relevant Files
Use these files to implement the feature:

### Frontend Files
- `frontend/src/components/risk/FKDocumentUploader.tsx` - Main component that handles document upload and display. **This is where the delete button and logic will be added.**
- `frontend/src/services/riskService.ts` - API service layer. **Add new `deleteExtraction` method.**
- `frontend/src/types/risk.ts` - TypeScript types. **No changes needed - types already exist.**

### Backend Files
- `backend/src/adapter/rest/risk_routes.py` - API routes. **Add new `DELETE /evaluations/{id}/extractions/{extraction_id}` endpoint.**
- `backend/src/repositorio/risk_repository.py` - Data access layer. **Already has `delete` method in `DocumentExtractionRepository`.**
- `backend/src/interface/risk_dtos.py` - DTOs. **No changes needed.**

### E2E Test Reference Files
- `.claude/commands/test_e2e.md` - Read to understand E2E test patterns
- `.claude/commands/e2e/test_login.md` - Example E2E test structure

### New Files
- `.claude/commands/e2e/test_reupload_fraud_document.md` - E2E test for document reupload functionality

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs)
- [ ] Excel Processing (treasury, finance)
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [ ] Reporting (queries, history)
- [x] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `DocumentExtractionRepository.delete(id)` | `bool` | Return value | `True` if deleted |
| `DocumentExtractionRepository.get_by_id(id)` | `dict` | `data['id']` | Not `data.id` |
| `CrossValidationRepository.delete_by_assessment(id)` | `bool` | Return value | `True` if deleted |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - `ExtractionStatus` enum exists
- [ ] Template file exists (not applicable)
- [x] Database records exist - `risk_document_extractions` table exists
- [ ] Country-specific data handled (not applicable)

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| extraction_id | extraction_id | string (UUID) | Path parameter |
| assessment_id (evaluation_id) | id | string (UUID) | Path parameter |

## Implementation Plan

### Phase 1: Foundation
1. **Backend endpoint**: Add DELETE endpoint for document extraction in `risk_routes.py`
2. **Service method**: Add `deleteExtraction` method to `riskService.ts`

### Phase 2: Core Implementation
1. **UI Enhancement**: Add delete button (trash icon) to `FKDocumentUploader.tsx` for each document card
2. **State Management**: Handle deletion state (loading, confirmation)
3. **Cross-validation invalidation**: Clear cross-validation results when documents are removed

### Phase 3: Integration
1. **Testing**: Verify the delete flow works end-to-end
2. **Edge cases**: Handle deletion during ongoing extraction
3. **E2E test**: Create automated test for the feature

## Step by Step Tasks

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` to understand the test execution pattern
- Read `.claude/commands/e2e/test_login.md` as a reference for test structure
- Create `.claude/commands/e2e/test_reupload_fraud_document.md` with:
  - User story section
  - Prerequisites (servers running, test credentials)
  - Test steps to upload a document, delete it, and reupload a different document
  - Success criteria and screenshots to capture
  - Error scenarios

### Step 2: Add Backend DELETE Endpoint
- Add new endpoint in `backend/src/adapter/rest/risk_routes.py`:
  - Route: `DELETE /evaluations/{id}/extractions/{extraction_id}`
  - Roles: `risk_analyst`, `risk_manager`
  - Logic:
    1. Verify extraction exists and belongs to the assessment
    2. Delete the extraction record using `DocumentExtractionRepository.delete()`
    3. Delete associated cross-validation results (since they may be invalid now)
    4. Return success message

### Step 3: Add Frontend Service Method
- Add `deleteExtraction` method to `frontend/src/services/riskService.ts`:
  ```typescript
  deleteExtraction: async (evaluationId: string, extractionId: string): Promise<void> => {
    await apiClient.delete(`/risk/evaluations/${evaluationId}/extractions/${extractionId}`);
  }
  ```

### Step 4: Update FKDocumentUploader Component
- Import `Delete` icon from MUI icons
- Add `deleting` state to track which document is being deleted: `deleting: { [docType: string]: boolean }`
- Add `handleDeleteDocument` function:
  1. Show confirmation if document has completed extraction
  2. Set deleting state to true
  3. Call `riskService.deleteExtraction()`
  4. Clear upload state for that document type
  5. Reload extractions list
  6. Notify parent about validation ready state change
- Add delete button (trash icon) in the document card header:
  - Show when extraction exists (any status: pending, processing, completed, failed)
  - Disable during deletion
  - Show spinner during deletion
  - Use `IconButton` with `Tooltip`
- Update the UI logic:
  - When extraction is deleted, show the upload button again
  - Clear any local file references for that document type

### Step 5: Handle Cross-Validation Invalidation
- In the backend DELETE endpoint, after deleting the extraction:
  - Delete all cross-validation results for the assessment using `CrossValidationRepository.delete_by_assessment()`
  - This ensures stale validation results are not used
- Update the assessment's `document_validation_status` to indicate revalidation is needed
- Frontend should show a message indicating cross-validation needs to be re-run

### Step 6: Run Validation Commands
- Execute all validation commands listed below to ensure no regressions

## Testing Strategy

### Unit Tests
- Backend: Test the DELETE endpoint with pytest:
  - Test successful deletion
  - Test deletion of non-existent extraction (404)
  - Test deletion of extraction belonging to different assessment (403/404)
  - Test cross-validation cleanup after deletion

### Edge Cases
- User clicks delete while extraction is processing (should cancel and delete)
- User deletes the only completed document (cross-validation count drops below 2)
- User deletes a document that was used in cross-validation (results should be cleared)
- Multiple rapid delete requests for the same document
- Network error during delete (should show error and allow retry)

## Acceptance Criteria
1. A trash icon button appears next to each document that has an upload/extraction record
2. Clicking the trash icon removes the document extraction from the database
3. After deletion, the upload button is re-enabled for that document type
4. If cross-validation was previously run, results are cleared after document deletion
5. User can successfully upload a new document after deleting the previous one
6. The feature works for all 6 document types
7. Appropriate loading states are shown during deletion
8. Error messages are displayed if deletion fails

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_reupload_fraud_document.md` E2E test to validate this functionality works.
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- The repository already has a `delete` method in `DocumentExtractionRepository` (line 662 of `risk_repository.py`)
- The cross-validation repository also has `delete_by_assessment` method (line 776 of `risk_repository.py`)
- The current upload flow already handles re-uploading by updating existing records (lines 971-980 of `risk_routes.py`) - but this approach doesn't work well UX-wise because the user can't see that they need to re-upload
- Consider adding a confirmation dialog for completed extractions to prevent accidental deletion
- The extraction process uses LandingAI API with 30-60 second processing time - deletion during processing should be handled gracefully
- No new npm/pip packages are required for this feature

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - using existing schema)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Repository methods verified and documented
- [x] Access patterns documented (dict vs object)
- [x] Validation rules defined (extraction must belong to assessment)

### Consistency (ALL features)
- [x] Data types match between frontend and backend (UUID strings)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (not applicable for this feature)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (Step 1)
