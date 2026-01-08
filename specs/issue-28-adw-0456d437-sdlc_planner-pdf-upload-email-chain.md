# Feature: Add PDF Upload Support to Email Chain Functionality

## Feature Description
Add support for uploading PDF files to the email chain analysis functionality. Currently, the "cadenas de correo" feature only accepts `.eml` (RFC 5322 email format) and `.msg` (Microsoft Outlook format) files. This feature extends the capability to also accept PDF files that may contain printed or exported email correspondence. The system will extract text from PDF files and parse it using the existing text parsing logic to identify email patterns, company names, NITs, and representative names for cross-validation against document extractions.

## User Story
As a Risk Analyst or Risk Manager
I want to upload PDF files containing email correspondence to the email chain validator
So that I can analyze printed or exported email communications for potential fraud indicators when the original email file format is not available

## Problem Statement
Users sometimes receive email correspondence in PDF format rather than the native `.eml` or `.msg` formats. This happens when:
1. Emails are printed to PDF for record-keeping
2. Email chains are exported as PDFs from email clients
3. Users receive scanned copies of printed emails
4. Third parties share email correspondence as PDF attachments

Currently, these users cannot utilize the email chain cross-validation feature because the system only accepts `.eml` and `.msg` files.

## Solution Statement
Extend the email chain upload functionality to accept PDF files by:
1. Adding `.pdf` as an accepted file type in both frontend and backend validation
2. Using PyMuPDF (fitz) to extract text content from uploaded PDF files
3. Passing the extracted text to the existing `parse_raw_text()` method in `EmailChainParserService` for email pattern detection
4. Maintaining backward compatibility with existing `.eml` and `.msg` file handling

The solution leverages the existing text parsing capabilities to minimize new code while enabling PDF support.

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`, `mesa_control`
- Backend Protection: Uses existing `require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control'])` dependency in `risk_routes.py`
- Frontend Protection: Existing role protection on the Risk module routes

## Relevant Files
Use these files to implement the feature:

**Backend Files:**
- `backend/src/adapter/rest/risk_routes.py` (lines 1483-1569) - API endpoint for email chain upload. Needs to add `.pdf` to accepted file types in the file validation logic.
- `backend/src/core/servicios/risk/email_chain_parser_service.py` - Parser service that handles `.eml`, `.msg`, and raw text parsing. Needs new `parse_pdf_file()` method.
- `backend/src/core/servicios/risk/email_chain_service.py` - Service layer that calls the parser. Needs to route `.pdf` files to the new parser method.
- `backend/requirements.txt` - Already includes PyMuPDF (`PyMuPDF>=1.23.0`), no changes needed.

**Frontend Files:**
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Main upload component. Needs to update file type validation from `.eml,.msg` to `.eml,.msg,.pdf`.
- `frontend/src/types/risk.ts` - TypeScript types for email chains. No changes needed (structure remains the same).
- `frontend/src/services/riskService.ts` - API service layer. No changes needed (same endpoint).

**Test Files:**
- `backend/tests/` - Directory for backend tests.
- `.claude/commands/e2e/test_email_chain_validation.md` - Existing E2E test for email chain validation.

### New Files
- `.claude/commands/e2e/test_email_chain_pdf_upload.md` - New E2E test file for testing PDF upload functionality in the email chain feature.

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this is a data import feature.

### B. Excel Column Mapping (Excel Processing only)
Not applicable - this is not an Excel processing feature.

### C. File Format Specification (Import/Export only)

| Format | Max Size | Required Headers | Validation Rules |
|--------|----------|------------------|------------------|
| PDF | 10MB | None (text extraction) | Must be valid PDF, extractable text content |
| EML | 10MB | RFC 5322 email headers | Valid email format |
| MSG | 10MB | Outlook message format | Valid MSG structure |

**Input Processing:**
- PDF files are read as binary, text extracted using PyMuPDF
- Extracted text is passed to existing `parse_raw_text()` method
- Same email pattern detection logic applies to PDF content

**Error Handling:**
- Corrupted PDFs: Return parse_errors with descriptive message
- Empty PDFs: Return parse_errors indicating no text content found
- Password-protected PDFs: Return parse_errors asking user to provide unprotected file

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| EmailChainRepository.create() | dict | data['id'] | Result is dict |
| EmailChainRepository.update() | dict | data['parsed_data'] | Result is dict |
| EmailChainService.upload_email_chain() | dict | chain['id'] | Result is dict |

**No changes to data contracts** - the PDF parsing produces the same output structure as existing parsers.

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs (no new enums needed)
- [ ] Template file exists in `backend/templates/` (not applicable)
- [x] Database records exist (using existing `email_chains` table)
- [ ] Country-specific data handled (not applicable)

### F. External API Contract (Integration only)
Not applicable - no external APIs involved.

### G. Query Specification (Reporting only)
Not applicable - this is a file upload feature.

### Interface Mapping (Frontend ↔ Backend)
No changes to interface - same request/response structure:

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| file | file | UploadFile | Now accepts .pdf in addition to .eml/.msg |
| text_content | text_content | string | Unchanged |
| parsed_data | parsed_data | EmailChainParsedData | Same structure for all file types |

## Implementation Plan
### Phase 1: Foundation
- Add PDF parsing method to `EmailChainParserService`
- Test text extraction from sample PDFs locally

### Phase 2: Core Implementation
- Update backend file type validation to accept `.pdf`
- Route PDF files to new parser method in `EmailChainService`
- Update frontend file input to accept `.pdf` files
- Update frontend validation error message

### Phase 3: Integration
- Test full flow with PDF uploads
- Verify validation results match expected format
- Create E2E test file

## Step by Step Tasks

### Step 1: Add PDF Parser Method to EmailChainParserService
- Open `backend/src/core/servicios/risk/email_chain_parser_service.py`
- Add new method `parse_pdf_file(self, file_content: bytes) -> dict`:
  - Use PyMuPDF (fitz) to open PDF from bytes
  - Extract text from all pages
  - If text is empty, return error in parse_errors
  - Pass extracted text to `parse_raw_text()` for email pattern detection
  - Return the result from `parse_raw_text()` with additional filename info if needed
- Handle exceptions gracefully with descriptive Spanish error messages

### Step 2: Update EmailChainService to Handle PDF Files
- Open `backend/src/core/servicios/risk/email_chain_service.py`
- In `upload_email_chain()` method, add condition for `.pdf` extension
- Route PDF files to `parser.parse_pdf_file()` method
- Log PDF parsing activity

### Step 3: Update Backend API Validation
- Open `backend/src/adapter/rest/risk_routes.py`
- Find the file type validation in `upload_email_chain()` endpoint (around line 1521)
- Change `('.eml', '.msg')` to `('.eml', '.msg', '.pdf')`
- Update error message to include PDF: "File must be .eml, .msg, or .pdf format"

### Step 4: Update Frontend File Input
- Open `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Update the `accept` attribute on file input from `.eml,.msg` to `.eml,.msg,.pdf`
- Update the file type validation check to include `.pdf`
- Update the error message from "Solo se aceptan archivos .eml o .msg" to "Solo se aceptan archivos .eml, .msg o .pdf"
- Update button text from "Seleccionar archivo .eml o .msg" to "Seleccionar archivo .eml, .msg o .pdf"

### Step 5: Create E2E Test File
- Read `.claude/commands/test_e2e.md` to understand E2E test structure
- Read `.claude/commands/e2e/test_email_chain_validation.md` as reference
- Create `.claude/commands/e2e/test_email_chain_pdf_upload.md` with test steps for:
  1. Login with risk_analyst role
  2. Navigate to risk evaluation with documents
  3. Navigate to External Contact tab
  4. Upload a sample PDF file with email content
  5. Verify upload succeeds and chain appears in list
  6. Trigger validation
  7. Verify validation results display correctly
  8. Delete the uploaded chain
  9. Capture screenshots at key steps

### Step 6: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Fix any linting or type errors that arise

## Testing Strategy
### Unit Tests
- Test `parse_pdf_file()` method with:
  - Valid PDF containing email text
  - PDF with no extractable text
  - Corrupted/invalid PDF bytes
  - Password-protected PDF (should return error)

### Edge Cases
- PDF with email content but no clear headers (should use fallback email detection)
- Multi-page PDF with email chain across pages
- PDF with images only (OCR not supported - should return error)
- PDF exported from different email clients (Outlook, Gmail, etc.)
- Very large PDF (up to 10MB limit)
- PDF with non-standard encoding

## Acceptance Criteria
1. Users can upload `.pdf` files in the email chain uploader
2. PDF text is extracted and parsed for email patterns
3. Uploaded PDF chains appear in the chains list with "Pendiente" status
4. Validation can be triggered on PDF-uploaded chains
5. Validation results display correctly with discrepancies if found
6. Error messages are displayed in Spanish for:
   - Empty PDFs (no extractable text)
   - Invalid/corrupted PDFs
   - PDFs exceeding size limit
7. Existing `.eml` and `.msg` upload functionality continues to work
8. All tests pass with zero regressions

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. **Backend tests:**
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **Backend linting:**
   ```bash
   cd backend && ruff check src/
   ```

3. **Frontend linting:**
   ```bash
   cd frontend && npm run lint
   ```

4. **Frontend TypeScript check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend build:**
   ```bash
   cd frontend && npm run build
   ```

6. **E2E Test Validation:**
   - Read `.claude/commands/test_e2e.md`
   - Execute `.claude/commands/e2e/test_email_chain_pdf_upload.md` to validate PDF upload functionality

## Notes
- **PyMuPDF is already included** in `backend/requirements.txt` as `PyMuPDF>=1.23.0`, so no new dependency is needed
- **OCR is NOT supported** - PDFs must contain extractable text (not scanned images). This is a known limitation that should be communicated to users.
- **File size limit remains 10MB** to maintain consistency with existing file types
- **Text parsing is reused** - the existing `parse_raw_text()` method handles all the heavy lifting for email pattern detection

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (PyMuPDF already included)

### Category-Specific Completeness
**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete (no changes needed)
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [ ] Country-specific variations handled (not applicable)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
