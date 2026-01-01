# Feature: Email Chain Alerts Table in Reporte de Evaluacion Completa

## Feature Description
Add a dedicated table for email chain alerts (discrepancies) to the "Reporte de Evaluacion Completa" PDF report in the risk module. This table will display email chain issues identified during fraud detection, similar to the existing cross-validation discrepancies table, and will include manual validation comments added by Mesa de Control analysts. The feature enhances the comprehensive evaluation report by providing complete visibility into all communication-related risk factors.

## User Story
As a Mesa de Control Riesgos analyst
I want to see email chain alerts with their validation comments in the comprehensive evaluation PDF report
So that I can have a complete audit trail of all communication-related fraud indicators and the validation decisions made for each alert

## Problem Statement
When completing a risk assessment, the system generates a PDF report (Reporte de Evaluacion Completa) that shows:
1. A table consolidating all fraud indicators
2. A cross-validation discrepancies table with validation comments
3. An individual contact issues table

However, the report is missing a dedicated table for email chain alerts/discrepancies. This data exists and is validated in the UI (as implemented in issue #65), but is not being rendered in the PDF report. Mesa de Control analysts need this table to have a complete record of all risk factors and their validation status.

## Solution Statement
Enhance the `exportComprehensiveEvaluationReport()` function in `crossValidationPdfExport.ts` to:
1. Add a new "Alertas de Cadenas de Email" table section after the Cross-Validation Results
2. Display email chain discrepancies with columns: Cadena (identifier), Campo (field), Severidad, Valor (email value), Descripcion, Validacion (status), and Comentarios
3. Include manual validation comments from Mesa de Control analysts (similar to cross-validation discrepancies)
4. Apply severity color-coding and validation status formatting consistent with existing tables
5. Filter to show only significant discrepancies (HIGH, CRITICAL, MEDIUM severity - excluding INFO)

## Access Control
- Required Role(s): risk_analyst, risk_manager, admin, mesa_control (read access to view/export report)
- Backend Protection: No changes needed - existing assessment detail endpoint already returns email chain data with validations
- Frontend Protection: No changes needed - export function is already protected by page-level role protection

## Relevant Files
Use these files to implement the feature:

**Primary File (Frontend)**
- `frontend/src/utils/crossValidationPdfExport.ts` - The main PDF export utility that generates the comprehensive evaluation report. This is the primary file to modify - it already has the Email Chain Discrepancies section at lines 867-993, but we need to verify it's working correctly and matches the cross-validation pattern with validation comments.

**Type Definitions (Frontend)**
- `frontend/src/types/risk.ts` - Contains all TypeScript types for email chains, including `EmailChainWithValidations`, `EmailChainDiscrepancyWithValidation`, `EmailChainValidationResultWithValidations`. Already has `EMAIL_CHAIN_FIELD_LABELS` for Spanish translations.

**Reference Files**
- `app_docs/feature-584b6bdd-external-communication-validation-comments.md` - Documentation for the validation feature that added email chain discrepancy validation support (issue #65). This confirms the validation data structure.
- `.claude/commands/test_e2e.md` - E2E test runner documentation for creating the test file.
- `.claude/commands/e2e/test_RiskModule_external_communication_validation_comments.md` - Existing E2E test for validation comments - use as reference for new E2E test structure.

**Backend Reference (Read-Only)**
- `backend/src/adapter/rest/risk_routes.py` - Risk API endpoints. Verify the finalization endpoint includes email chain validation data.
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Fraud detection service that aggregates email chain data for finalization.
- `backend/src/repositorio/risk_repository.py` - Email chain repository with validation data access.

### New Files
- `.claude/commands/e2e/test_email_chain_alerts_pdf_table.md` - E2E test file to validate the email chain alerts table appears correctly in the PDF export.

## Pre-Implementation Verification

### Feature Category
- [x] Reporting (queries, history) - Complete sections D, G
- [ ] Document Generation (contracts, PDFs)
- [ ] Excel Processing (treasury, finance)
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [ ] CRUD Operations (basic data management)

Note: While this involves PDF generation, it's primarily a reporting feature that adds a new table to an existing report using existing data structures. No template files are involved.

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this feature uses jsPDF dynamic table generation, not Word templates.

### B. Excel Column Mapping (Excel Processing only)
Not applicable.

### C. File Format Specification (Import/Export only)
Not applicable.

### D. Data Contract Verification (ALL features)
Document return types and access patterns for repository methods used:

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| email_chain_repo.get_chains_with_validations() | List[dict] | data['validation_result']['discrepancies'] | Array of EmailChainDiscrepancy |
| Discrepancy validation access | dict | disc['validation'] | Optional validation object |
| Validation comments | dict | disc['validation']['comments'] | String up to 2000 chars |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - `DiscrepancyValidationReason` already defined
- [x] Template file exists - N/A (jsPDF generation)
- [x] Database records exist - `email_chain_discrepancy_validations` table exists (issue #65)
- [x] Country-specific data handled - N/A (single country)

### F. External API Contract (Integration only)
Not applicable.

### G. Query Specification (Reporting only)
Email chain data is already retrieved by the existing finalization flow. The PDF export receives:

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| assessment.email_chains | EmailChainWithValidations[] | No | Empty array |
| Discrepancy filtering | Severity check | Yes | Exclude 'info' severity |

**Data Flow:**
1. Frontend calls finalization endpoint to get assessment data
2. Assessment includes `email_chains` array with `validation_result.discrepancies`
3. Each discrepancy may have a `validation` object with `is_validated`, `validation_reason`, `comments`
4. PDF export filters to significant severities and renders table

### Interface Mapping (Frontend <-> Backend)
Map frontend TypeScript fields to backend Pydantic fields:

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| chain.id | id | string (UUID) | Email chain identifier |
| chain.original_filename | original_filename | string | Display name for chain |
| chain.validation_result | validation_result | object | Contains discrepancies array |
| disc.field | field | string | Domain, company_name, nit, etc. |
| disc.severity | severity | string | critical, high, medium, low, info |
| disc.email_value | email_value | string | The problematic value |
| disc.description | description | string | Issue description |
| disc.validation | validation | object | Optional validation data |
| disc.validation.is_validated | is_validated | boolean | Validation status |
| disc.validation.validation_reason | validation_reason | string | Reason enum value |
| disc.validation.comments | comments | string | Analyst comments (max 2000) |

## Implementation Plan

### Phase 1: Analysis and Verification
- Review the existing email chain discrepancies section in `crossValidationPdfExport.ts` (lines 867-993)
- Compare against the cross-validation discrepancies table to ensure consistent patterns
- Verify the email chains data includes validation information from the finalization endpoint
- Identify any gaps in the current implementation

### Phase 2: Core Implementation (if gaps found)
Based on code review, the email chain discrepancies table already exists at lines 867-993 with:
- Filtering for HIGH, CRITICAL, MEDIUM severity
- Columns: Cadena, Campo, Severidad, Valor, Descripcion, Validacion, Comentarios
- Severity color-coding
- Validation status color-coding

If the table is complete, focus on:
- Verifying data flow from finalization to PDF export
- Testing with real data to confirm table renders
- Ensuring validation comments display correctly

### Phase 3: Testing and Validation
- Create E2E test file for email chain alerts PDF table
- Run validation commands to ensure no regressions
- Test PDF export with email chains that have validated discrepancies
- Verify table formatting and styling matches design

## Step by Step Tasks

### Step 1: Read and Analyze Current Implementation
- Read `frontend/src/utils/crossValidationPdfExport.ts` lines 867-993 to understand the existing email chain discrepancies table
- Read lines 758-865 to understand the cross-validation table pattern (our reference)
- Identify if the email chain table has all required columns and validation data display

### Step 2: Read E2E Test Documentation
- Read `.claude/commands/test_e2e.md` to understand E2E test structure
- Read `.claude/commands/e2e/test_RiskModule_external_communication_validation_comments.md` for test pattern reference

### Step 3: Create E2E Test File
- Create `.claude/commands/e2e/test_email_chain_alerts_pdf_table.md`
- Include test steps for:
  1. Login as mesa_control user
  2. Navigate to a risk evaluation with validated email chain discrepancies
  3. Export the comprehensive evaluation PDF
  4. Verify the PDF contains the email chain alerts table
  5. Verify table columns: Cadena, Campo, Severidad, Valor, Descripcion, Validacion, Comentarios
  6. Verify validated discrepancies show validation reason and comments
  7. Verify severity color-coding

### Step 4: Verify Data Flow (if needed)
- If analysis shows gaps, trace data flow from:
  1. `risk_routes.py` finalization endpoint
  2. Through `fraud_detection_service.py` aggregation
  3. To frontend component that calls PDF export
- Ensure `ComprehensiveReportContext.email_chains` includes validation data

### Step 5: Fix Implementation Gaps (if any found)
- If the email chain table is missing or incomplete:
  1. Add/update the table section in `exportComprehensiveEvaluationReport()`
  2. Ensure validation status column shows "Pendiente" or reason label
  3. Ensure comments column displays truncated comments (80 chars)
  4. Apply consistent severity and validation status color-coding

### Step 6: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Fix any TypeScript, linting, or build errors

## Testing Strategy

### Unit Tests
- No new pytest tests needed - this is a frontend-only PDF rendering change
- The existing data flow from backend is already tested

### E2E Test
- Test email chain alerts table appears in PDF
- Test validation status and comments display correctly
- Test severity filtering (INFO excluded)
- Test table styling and formatting

### Edge Cases
- No email chains uploaded -> Table section should not appear
- Email chains with no discrepancies -> Table section should not appear
- All discrepancies are INFO severity -> Table section should not appear (filtered out)
- Discrepancy without validation -> Shows "Pendiente" status
- Discrepancy with validation but no comments -> Shows reason, "-" for comments
- Very long comments -> Truncated at 80 characters with "..."

## Acceptance Criteria
1. The comprehensive evaluation PDF includes an "Alertas de Cadenas de Email" table
2. Table only appears when there are HIGH, CRITICAL, or MEDIUM severity email chain discrepancies
3. Table includes columns: Cadena, Campo, Severidad, Valor, Descripcion, Validacion, Comentarios
4. Validated discrepancies show the validation reason label (e.g., "Validacion manual")
5. Validated discrepancies show the analyst's comments (truncated if > 80 chars)
6. Unvalidated discrepancies show "Pendiente" in the validation column
7. Severity column uses color-coding consistent with other tables
8. Validation status uses color-coding (Pendiente=orange, Validado=green)
9. Table styling matches existing tables (grid theme, alternating rows, Finkargo colors)
10. Page management handles table overflow correctly (new page if needed)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_email_chain_alerts_pdf_table.md` to validate the email chain alerts table appears correctly in the PDF export

## Notes

### Key Findings from Research
1. The email chain discrepancies table already exists in `crossValidationPdfExport.ts` at lines 867-993
2. The table has all required columns including Validation and Comments
3. The implementation follows the same pattern as cross-validation discrepancies
4. Color-coding for severity and validation status is implemented
5. Filtering for significant severities (excluding INFO) is in place

### Potential Implementation Gaps to Verify
1. Verify the email_chains array is being passed correctly to `exportComprehensiveEvaluationReport()`
2. Verify the validation data structure matches `EmailChainDiscrepancyWithValidation` type
3. Verify the table title says "Alertas de Cadenas de Email" (or similar Spanish)
4. The current code shows "Discrepancias en Cadenas de Email" - this is acceptable

### No New Dependencies Required
The feature uses existing libraries: jsPDF, jspdf-autotable, date-fns

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (Step 3)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Reporting:**
- [x] Query filters and parameters documented
- [x] Pagination/sorting requirements specified (handled by existing table implementation)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (N/A - Colombia only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
