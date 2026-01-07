# Feature: Fraud Risk Module - Excel Export for Document Extractions

## Feature Description
Add Excel export functionality to the fraud risk module's document upload and data extraction screen. Users will be able to export all extracted data from uploaded documents (financial statements, cédula, RUT, composición accionaria, certificado de existencia) to an Excel file for additional manual analysis. This provides flexibility for risk analysts who need to work with the extracted data outside the application.

## User Story
As a Risk Analyst or Risk Manager
I want to export extracted document data to Excel from the fraud evaluation documents screen
So that I can perform additional manual analysis on the extracted information using spreadsheet tools

## Problem Statement
After uploading documents and extracting data using AI in the fraud risk module, users currently cannot export this extracted data for offline analysis. Risk analysts often need to:
- Compare extracted data with external sources
- Share extracted data with colleagues who don't have system access
- Perform custom calculations or validations
- Archive extracted data in their own format

Without export functionality, users must manually copy data field by field, which is time-consuming and error-prone.

## Solution Statement
Implement an "Exportar a Excel" button in the FKDocumentUploader component that:
1. Generates an Excel file containing all extracted data from completed document extractions
2. Organizes data by document type across multiple sheets for clarity
3. Includes metadata (assessment ID, client NIT, extraction date, confidence scores)
4. Follows existing Excel export patterns in the codebase using the XLSX library (client-side) or openpyxl (server-side)
5. Downloads immediately when clicked (no server round-trip needed for client-side approach)

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: Uses existing `require_roles(['risk_analyst', 'risk_manager'])` from risk_routes.py (if implementing server-side export)
- Frontend Protection: Button only visible when user has risk module access (already handled by RoleProtectedRoute)

## Relevant Files
Use these files to implement the feature:

**Frontend Core Files:**
- `frontend/src/components/risk/FKDocumentUploader.tsx` - Main component where the export button will be added. Currently displays document upload and extracted data preview.
- `frontend/src/utils/excelExport.ts` - Existing Excel export utility using XLSX library. Follow patterns here for client-side export.
- `frontend/src/services/riskService.ts` - Risk service with API calls. Contains `getExtractions()` method that returns all document extractions.
- `frontend/src/types/risk.ts` - TypeScript types including `DocumentExtraction`, `DocumentExtractionList`, `DocumentType`, and all extracted data field definitions.

**Backend Files (if implementing server-side export):**
- `backend/src/adapter/rest/risk_routes.py` - Risk API routes. Would add new export endpoint here.
- `backend/src/core/servicios/comision_excel_service.py` - Existing Excel service to follow patterns for multi-sheet workbooks with Finkargo styling.
- `backend/src/core/servicios/excel_report_service.py` - Another Excel service showing professional styling patterns.
- `backend/src/interface/risk_dtos.py` - DTOs for document extraction data structures.

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_risk_dashboard.md` - Existing risk module E2E test showing patterns

### New Files
- `frontend/src/utils/riskExcelExport.ts` - New utility for exporting fraud risk document extractions to Excel (client-side approach)
- `.claude/commands/e2e/test_fraud_excel_export.md` - E2E test file for validating the export functionality

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing)

**Source Data Structure (from DocumentExtraction.extracted_data):**

Each document type has different extracted fields:

| Document Type | Key Fields | Data Types |
|--------------|------------|------------|
| `financial_statement_current` | company_name, nit, fiscal_year, period_end_date, auditor_name, total_assets, total_liabilities, total_equity, net_income, revenue, signatory_name, signatory_id | String, Number, Date |
| `financial_statement_prior` | (same as current) | String, Number, Date |
| `cedula` | full_name, first_names, last_names, document_number, document_type, birth_date, birth_place, issue_date, issue_place, gender, blood_type | String, Date |
| `composicion_accionaria` | company_name, nit, document_date, total_shares, share_value, shareholders (array with name, id_number, shares, percentage), majority_shareholder | String, Number, Array |
| `rut` | company_name, nit, city, address, email, phone, economic_activity, legal_representative (principal & suplente), registration_date | String, Date |
| `certificado_existencia` | company_name, nit, entity_type, registration_date, registered_capital | String, Number, Date |

**Output Excel Structure:**

| Sheet Name | Description |
|------------|-------------|
| Resumen | Summary sheet with assessment info, document count, extraction dates |
| Estados Financieros | Current and prior year financial data side-by-side |
| Cédula | Representative ID document data |
| Composición Accionaria | Shareholder information including array expansion |
| RUT | Tax registration data |
| Certificado Existencia | Corporate existence certificate data |

**Column Headers per Sheet:**

**Resumen Sheet:**
| Column | Source Field | Format |
|--------|-------------|--------|
| ID Evaluación | assessment_id | String |
| NIT Cliente | client_nit | String |
| Fecha Exportación | current_date | DD/MM/YYYY HH:mm |
| Documentos Procesados | completed_count | Number |
| Documentos Totales | total_documents | Number |

**Estados Financieros Sheet:**
| Column | Source | Format |
|--------|--------|--------|
| Campo | field_name | String |
| Año Actual | current_year_value | Various |
| Año Anterior | prior_year_value | Various |
| Variación | calculated | Percentage |

**Catalog Dependencies:**
- [x] No external catalog mappings needed
- [x] No country-specific variations (CO only for fraud module)

### C. File Format Specification (Import/Export)

| Format | Max Size | Required Data | Validation Rules |
|--------|----------|---------------|------------------|
| XLSX (output) | ~500KB | At least 1 completed extraction | Must have extracted_data object |

**Error Handling:**
- If no completed extractions exist, show info message "No hay datos extraídos para exportar"
- If extraction_status is not "completed", skip that document type
- Handle null/undefined values gracefully with "N/A" placeholder

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Notes |
|------------------|-------------|----------------|-------|
| riskService.getExtractions() | DocumentExtractionList | data.extractions | Returns array of DocumentExtraction |
| extraction.extracted_data | Record<string, unknown> | data['field_name'] | Dynamic object structure |
| extraction.extraction_status | ExtractionStatus | data.extraction_status | 'pending' | 'processing' | 'completed' | 'failed' |
| extraction.document_type | DocumentType | data.document_type | Enum string value |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| document_type | document_type | DocumentType (enum) | snake_case |
| extracted_data | extracted_data | Record<string, unknown> | Dynamic JSON |
| extraction_status | extraction_status | ExtractionStatus (enum) | snake_case |
| extraction_confidence | extraction_confidence | number | Decimal 0-1 |
| document_filename | document_filename | string | Original filename |
| created_at | created_at | string (ISO date) | Timestamp |

## Implementation Plan

### Phase 1: Foundation
- Create new Excel export utility file `riskExcelExport.ts`
- Define helper functions for formatting extracted data values
- Implement document type to sheet name mapping
- Add TypeScript types for export configuration

### Phase 2: Core Implementation
- Implement `exportDocumentExtractionsToExcel()` function using XLSX library
- Create multi-sheet workbook with one sheet per document type
- Add summary sheet with metadata
- Implement dynamic column generation based on extracted fields
- Handle array fields (shareholders) with row expansion
- Apply Finkargo styling (header colors, column widths)

### Phase 3: Integration
- Add "Exportar a Excel" button to FKDocumentUploader component
- Wire up button click handler to export function
- Show loading state during export generation
- Display success/error feedback to user
- Create E2E test for validation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_risk_dashboard.md` to understand E2E test format
- Create new E2E test file at `.claude/commands/e2e/test_fraud_excel_export.md`
- Define test steps for:
  1. Login as risk analyst/admin
  2. Navigate to an evaluation with completed document extractions
  3. Verify export button is visible in Documents tab
  4. Click export button
  5. Verify Excel file downloads
  6. Verify file contains expected sheets
- Include screenshot requirements for each step

### Task 2: Create Risk Excel Export Utility
- Create new file `frontend/src/utils/riskExcelExport.ts`
- Import XLSX library and date-fns for formatting
- Define document type labels in Spanish (matching DOCUMENT_TYPE_CONFIG)
- Implement helper functions:
  - `formatValueForExcel()` - Handle various data types including arrays/objects
  - `formatDateForExcel()` - Format ISO dates to DD/MM/YYYY HH:mm
  - `formatCurrencyForExcel()` - Format numbers with currency symbol
  - `formatPercentageForExcel()` - Format decimals as percentages

### Task 3: Implement Main Export Function
- In `riskExcelExport.ts`, implement `exportDocumentExtractionsToExcel()`:
  - Accept `DocumentExtractionList` and `assessment_id` as parameters
  - Filter to only completed extractions
  - Create workbook with `XLSX.utils.book_new()`
  - Generate summary sheet with metadata
  - Generate one sheet per document type with extracted data
  - Handle shareholders array by expanding to multiple rows
  - Set column widths for readability
  - Generate filename with assessment_id and date
  - Trigger download with `XLSX.writeFile()`

### Task 4: Add Export Button to FKDocumentUploader
- Open `frontend/src/components/risk/FKDocumentUploader.tsx`
- Import the new `exportDocumentExtractionsToExcel` function
- Import Download icon from MUI icons
- Add "Exportar a Excel" button in the header section (next to Actualizar button)
- Disable button when no completed extractions exist
- Show tooltip explaining button state
- Implement click handler that calls export function with current extractions

### Task 5: Add Loading and Error States
- In FKDocumentUploader, add state for export loading
- Show CircularProgress on button during export
- Handle any export errors gracefully
- Show success snackbar after successful export
- Ensure button re-enables after export completes

### Task 6: Run TypeScript Type Check
- Run `cd frontend && npx tsc --noEmit`
- Fix any type errors in the new code
- Ensure all imports are correct

### Task 7: Run Linting
- Run `cd frontend && npm run lint`
- Fix any linting issues
- Ensure code follows project conventions

### Task 8: Run Frontend Build
- Run `cd frontend && npm run build`
- Verify production build succeeds
- Check for any build warnings

### Task 9: Run Validation Commands
Execute all validation commands to confirm zero regressions:
- `cd backend && python -m pytest` - Backend tests
- `cd backend && ruff check src/` - Backend linting
- `cd frontend && npm run lint` - Frontend linting
- `cd frontend && npx tsc --noEmit` - TypeScript check
- `cd frontend && npm run build` - Production build

### Task 10: Execute E2E Test
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_fraud_excel_export.md`
- Capture screenshots at each step
- Verify Excel file downloads and contains correct data

## Testing Strategy

### Unit Tests
- No backend changes required for client-side export approach
- Frontend testing can verify:
  - Export function generates valid workbook object
  - Empty extractions show appropriate message
  - Document type mapping is correct

### Edge Cases
- No completed extractions (show info message, disable button)
- Only some document types have extractions (generate partial sheets)
- Null/undefined values in extracted_data (show "N/A")
- Very long text values (truncate or wrap)
- Shareholders array with 0 items (show empty row or message)
- Shareholders array with many items (expand to multiple rows)
- Special characters in company names (encode properly)
- Large numbers in financial data (format with thousands separator)

## Acceptance Criteria
1. "Exportar a Excel" button is visible in the Documents section of Risk Evaluation Detail page
2. Button is disabled when no completed document extractions exist
3. Clicking button downloads an Excel file named `documentos_extraidos_{assessment_id}_{date}.xlsx`
4. Excel file contains a summary sheet with assessment metadata
5. Excel file contains one sheet per document type that has completed extraction
6. Each sheet displays all extracted fields with readable column headers
7. Shareholders data (array) is expanded into multiple rows if applicable
8. Currency values are formatted with $ and thousands separators
9. Dates are formatted in DD/MM/YYYY HH:mm format
10. Button shows loading state during export generation
11. Works for users with risk_analyst, risk_manager, or admin roles
12. No console errors during export process

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_fraud_excel_export.md` to validate this functionality works

## Notes
- **No new npm dependencies needed**: The `xlsx` package is already installed in the frontend (used by `frontend/src/utils/excelExport.ts`)
- **Client-side approach recommended**: Following the pattern in `excelExport.ts`, generating Excel client-side avoids server round-trips and is faster for the user
- **Server-side option available**: If more complex styling is needed (e.g., multi-color headers, formulas), could use backend openpyxl service pattern from `comision_excel_service.py`
- **Spanish labels**: All column headers and sheet names should be in Spanish to match the application's UI language
- **Finkargo styling**: Use primary color (#0C147B) for headers if the XLSX library supports styling; otherwise, focus on functionality first
- **Future enhancement**: Could add export for cross-validation results and external contacts in the same file

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented (if applicable)
- [x] Data transformation rules specified (1:1 or 1:N for shareholders)
- [x] Catalog/lookup dependencies identified (none needed)

**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO only) if applicable

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
