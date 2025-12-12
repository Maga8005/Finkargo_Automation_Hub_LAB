# Feature: Add Word Document Download to Contratos Colombia - Solicitar

## Feature Description
Add Word (DOCX) document download functionality to the "Contratos Aprobados" tab in the "Contratos Colombia - Solicitar" page (FKApprovedContracts component). This mirrors the existing DOCX download feature already implemented in "Paga Local Colombia - Contratos Aprobados" (FKPagaLocalCOApprovedContracts component). The feature allows operations users to download approved contracts as editable Word documents for client distribution.

## User Story
As an **operations team member**
I want to download approved contracts from "Contratos Colombia - Solicitar" as Word documents
So that I can send editable contract documents to clients for review and signature

## Problem Statement
Currently, the "Contratos Aprobados" tab in "Contratos Colombia - Solicitar" only allows downloading approved contracts as PDF files. The operations team needs the ability to download contracts as Word (DOCX) documents, the same capability that already exists in the "Paga Local Colombia - Contratos Aprobados" view. This creates an inconsistent user experience and limits operational flexibility.

## Solution Statement
Add a Word document download button to each row in the FKApprovedContracts component table. The implementation will:
1. Add a DOCX download icon button alongside (or replacing) the existing PDF download button
2. Use the existing `operationsService.downloadApprovedContractDocx()` service method
3. Use the existing backend endpoint `GET /api/operations/contracts/{contract_id}/download/docx`
4. Follow the same UX pattern as FKPagaLocalCOApprovedContracts (loading state, filename convention, error handling)

No backend changes are required as the endpoint already exists and works for all contract types.

## Access Control
- Required Role(s): `operations`, `admin`
- Backend Protection: Already implemented via `require_operations_role` dependency in `operations_routes.py`
- Frontend Protection: Already handled - FKApprovedContracts is rendered within operations routes

## Relevant Files
Use these files to implement the feature:

**Frontend (Primary change):**
- `frontend/src/components/forms/FKApprovedContracts.tsx` - Main component to modify. Add DOCX download button following the pattern from FKPagaLocalCOApprovedContracts.

**Reference implementation (read-only):**
- `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx` - Reference for the DOCX download implementation pattern (handleDownloadDOCX function, DocxIcon import, button rendering)

**Service layer (already implemented):**
- `frontend/src/services/operationsService.ts` - Already contains `downloadApprovedContractDocx()` method (lines 191-199)

**Backend (no changes needed - verify only):**
- `backend/src/adapter/rest/operations_routes.py` - Contains `/contracts/{contract_id}/download/docx` endpoint (lines 516-586)

**E2E test reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Login test example
- `.claude/commands/e2e/test_paga_local_word_download.md` - Reference E2E test for DOCX download

### New Files
- `.claude/commands/e2e/test_contratos_colombia_word_download.md` - E2E test file for validating the new DOCX download functionality

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this feature uses existing document generation infrastructure.

### B. Excel Column Mapping (Excel Processing only)
Not applicable.

### C. File Format Specification (Import/Export only)
Not applicable.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `contract_repo.get_by_id()` | dict | `contract['field']` | `contract['status']`, `contract['contract_id']` |
| `operationsService.downloadApprovedContractDocx()` | Promise<Blob> | Returns binary blob | Download via browser |

**Frontend service method (already exists):**
```typescript
// frontend/src/services/operationsService.ts (lines 191-199)
async downloadApprovedContractDocx(contractId: string): Promise<Blob> {
  const response = await apiClient.get(
    `${BASE_URL}/contracts/${contractId}/download/docx`,
    { responseType: 'blob' }
  );
  return response.data;
}
```

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - All contract types (activos, otrosi, inventario_bodega) already supported
- [x] Template files exist in `backend/templates/` - Already present for existing contract types
- [x] Database records exist - Uses existing contract_generations table
- [x] Country-specific data handled - This is for Colombia contracts only

### F. External API Contract (Integration only)
Not applicable - using existing internal API endpoint.

### G. Query Specification (Reporting only)
Not applicable.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| contract.id | id | string (UUID) | Used for download API call |
| contract.contract_id | contract_id | string | Displayed code (e.g., ACT-2025-001) |
| contract.data_snapshot.nombre_importador | data_snapshot->nombre_importador | string | Used in filename |
| contract.status | status | string | Must be 'approved' for download |

## Implementation Plan

### Phase 1: Foundation
- No foundation work needed - all infrastructure exists
- Verify backend endpoint works for non-Paga-Local contract types

### Phase 2: Core Implementation
- Update FKApprovedContracts.tsx to add DOCX download button
- Import DocxIcon from MUI icons
- Add handleDownloadDOCX function (copy from FKPagaLocalCOApprovedContracts)
- Update table row actions column to include DOCX button
- Update instructions alert text to mention Word documents

### Phase 3: Integration
- Create E2E test file
- Run validation commands
- Test end-to-end flow

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` to understand E2E test format
- Read `.claude/commands/e2e/test_login.md` for login test example
- Read `.claude/commands/e2e/test_paga_local_word_download.md` for reference implementation
- Create `.claude/commands/e2e/test_contratos_colombia_word_download.md` with test steps for:
  - Login as operations user
  - Navigate to Operaciones > Contratos Colombia - Solicitar
  - Click "Contratos Aprobados" tab
  - Verify table displays approved contracts
  - Verify Word download button is visible with correct icon
  - Click download button and verify DOCX file downloads
  - Verify filename follows pattern `{contract_code}-{client_name}.docx`

### Step 2: Update FKApprovedContracts Component
- Read `frontend/src/components/forms/FKApprovedContracts.tsx`
- Read `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx` for reference
- Add import for `Description as DocxIcon` from `@mui/icons-material`
- Add `handleDownloadDOCX` function (copy pattern from FKPagaLocalCOApprovedContracts lines 181-208):
  ```typescript
  const handleDownloadDOCX = async (contract: ContractGeneration) => {
    try {
      setDownloadingId(contract.id);
      const blob = await operationsService.downloadApprovedContractDocx(contract.id);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      // Build filename: {contract_code}-{sanitized_client_name}.docx
      const clientName = contract.data_snapshot?.nombre_importador || 'cliente';
      const sanitizedName = clientName
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '_')
        .slice(0, 50);
      link.download = `${contract.contract_id}-${sanitizedName}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading DOCX:', err);
      alert('Error al descargar el documento Word');
    } finally {
      setDownloadingId(null);
    }
  };
  ```
- Update table actions column to add DOCX download button:
  - Add IconButton with DocxIcon
  - Add Tooltip "Descargar Word aprobado"
  - Use same loading/disabled state pattern as PDF button
- Update instructions Alert at bottom to mention Word documents

### Step 3: Run Validation Commands
- Run `cd frontend && npm run lint` to check for linting errors
- Run `cd frontend && npx tsc --noEmit` to check TypeScript types
- Run `cd frontend && npm run build` to verify production build
- Run `cd backend && python -m pytest` to verify no backend regressions
- Run `cd backend && ruff check src/` to check backend linting

## Testing Strategy

### Unit Tests
No new unit tests required - functionality uses existing tested infrastructure.

### Edge Cases
- Contract with very long client name (>50 chars): Should be truncated in filename
- Client name with special characters (ñ, accents, &, quotes): Should be sanitized
- Contract without data_snapshot.nombre_importador: Should fallback to "cliente"
- Multiple rapid clicks on download button: Should be prevented by loading state
- Non-approved contract: Backend returns 400 error, should show user-friendly message

## Acceptance Criteria
1. FKApprovedContracts component displays a Word document download button for each approved contract
2. Download button shows DocxIcon (document icon) instead of PdfIcon
3. Tooltip text reads "Descargar Word aprobado"
4. Clicking download button triggers DOCX file download
5. Downloaded file has .docx extension
6. Filename follows pattern: `{contract_id}-{sanitized_client_name}.docx`
7. Loading spinner displays during download
8. Error handling shows user-friendly alert on failure
9. Instructions alert mentions Word document download
10. No TypeScript or linting errors
11. Production build succeeds

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_contratos_colombia_word_download.md` E2E test to validate this functionality works

## Notes
- **No backend changes required**: The `/api/operations/contracts/{contract_id}/download/docx` endpoint already exists and works for all contract types
- **No new dependencies**: All required imports (DocxIcon, operationsService) are already available or used elsewhere
- **Reference implementation**: FKPagaLocalCOApprovedContracts.tsx provides the exact pattern to follow
- The PDF download button can either be replaced by DOCX or kept alongside it (recommend replacing to match Paga Local behavior shown in screenshot)
- Consider adding both PDF and DOCX buttons if users need both formats (future enhancement)

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created - N/A, no migrations needed
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes - None needed

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions verified
- [x] Access patterns (dict vs object) verified for repository methods

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable - Colombia only

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
