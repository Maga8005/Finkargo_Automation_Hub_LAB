# Feature: Cross-Validation PDF Report for Risk Module

## Feature Description
Add a PDF report generation functionality to the Validación Cruzada (Cross-Validation) screen in the Risk module. This feature enables users to generate a professional PDF document summarizing all cross-validation findings, discrepancies, and risk indicators for a specific risk evaluation. The report can then be forwarded to stakeholders for review or compliance documentation purposes.

## User Story
As a **risk analyst or risk manager**
I want to **generate a PDF report of cross-validation findings**
So that **I can share the fraud detection analysis with stakeholders, maintain compliance records, and facilitate decision-making processes**

## Problem Statement
Currently, users can view cross-validation results on the screen but have no way to export these findings in a shareable, professional format. This limits the ability to:
- Share fraud detection findings with external stakeholders (compliance, auditors, management)
- Create an audit trail of risk assessments
- Generate documentation for regulatory compliance
- Communicate risk findings in offline scenarios

## Solution Statement
Implement a client-side PDF generation feature using the existing jsPDF library (already used in `frontend/src/utils/pdfExport.ts`). The PDF report will include:
- Header with Finkargo branding and report metadata
- Client/company information section
- Executive summary of validation results (discrepancy counts by severity)
- Detailed table of all validation checks with results
- Risk score impact summary
- Timestamp and generation metadata

The implementation follows the established pattern from the existing contract PDF export functionality, ensuring consistency across the application.

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: Not required (PDF generation is client-side using existing data)
- Frontend Protection: Button visibility tied to user having risk module access (already enforced by page-level protection)

## Relevant Files
Use these files to implement the feature:

**Frontend - Reference Files (read for patterns):**
- `frontend/src/utils/pdfExport.ts:1-274` - **Critical**: Existing PDF export utility with Finkargo branding colors and jsPDF patterns. Copy the approach for styling and structure.
- `frontend/src/components/risk/FKCrossValidationResults.tsx:1-455` - **Critical**: Current cross-validation display component where the "Export PDF" button will be added. Understand the data structures and display logic.
- `frontend/src/types/risk.ts:1-443` - TypeScript types for risk module, including `CrossValidationResponse`, `CrossValidationResult`, `DiscrepancySeverity`, etc.
- `frontend/src/services/riskService.ts:227-247` - Risk service methods for getting cross-validation data.
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx:1-454` - Parent page that hosts the cross-validation tab with assessment context.

**Backend - Reference Files (read for data understanding):**
- `backend/src/interface/risk_dtos.py:429-503` - DTOs for cross-validation data structures.
- `backend/src/core/servicios/risk/cross_validation_service.py:1-638` - Business logic for cross-validation checks (to understand what each validation type means).

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test structure
- `.claude/commands/e2e/test_export_approved_contracts_pdf.md` - **Critical**: PDF export E2E test example to follow for this feature

### New Files
- `frontend/src/utils/crossValidationPdfExport.ts` - New utility for cross-validation PDF generation
- `.claude/commands/e2e/test_cross_validation_pdf_report.md` - E2E test file for validating PDF export functionality

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [x] **Reporting (queries, history)** → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `riskService.getDiscrepancies()` | `Promise<CrossValidationResponse>` | object properties | `response.results`, `response.total_discrepancies` |
| `riskService.getEvaluation()` | `Promise<RiskAssessmentDetail>` | object properties | `assessment.client_nit`, `assessment.client_info?.nombre_importador` |

**Data structures used for PDF generation:**

```typescript
// CrossValidationResponse (from types/risk.ts)
interface CrossValidationResponse {
  assessment_id: string;
  total_discrepancies: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_score_impact: number;
  results: CrossValidationResult[];
  validated_at?: string;
}

// CrossValidationResult
interface CrossValidationResult {
  id?: string;
  validation_type: ValidationType;
  documents_compared: string[];
  field_compared?: string;
  values_found: Record<string, unknown>;
  is_discrepancy: boolean;
  severity?: DiscrepancySeverity;
  description?: string;
  score_impact: number;
}

// Client info from assessment
interface ClientInfo {
  nit: string;
  nombre_importador?: string;
  representante_legal?: string;
  ciudad_domicilio?: string;
  cupo_plataforma?: number;
}
```

### G. Query Specification (Reporting only)

This feature does not require new backend queries. It uses existing data already loaded on the cross-validation screen:
- `CrossValidationResponse` - Already fetched by `FKCrossValidationResults` component
- `RiskAssessmentDetail` - Already available from parent `RiskEvaluationDetail` page

| Data Source | Already Available | Notes |
|-------------|-------------------|-------|
| Validation results | Yes | Passed as state from `onValidationComplete` callback |
| Assessment details | Yes | Available in parent page state |
| Client info | Yes | Part of `RiskAssessmentDetail.client_info` |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `assessment_id` | `assessment_id` | string | snake_case consistent |
| `total_discrepancies` | `total_discrepancies` | number | Direct mapping |
| `critical_count` | `critical_count` | number | Direct mapping |
| `validation_type` | `validation_type` | ValidationType enum | Uses values like 'company_name', 'nit', etc. |
| `severity` | `severity` | DiscrepancySeverity enum | 'low', 'medium', 'high', 'critical' |
| `score_impact` | `score_impact` | number (Decimal from backend) | May need toFixed() for display |

## Implementation Plan

### Phase 1: Foundation
1. Create the PDF export utility file following the existing `pdfExport.ts` pattern
2. Define helper functions for formatting validation types, severities, and values
3. Set up Finkargo brand colors and document metadata

### Phase 2: Core Implementation
1. Implement the main PDF generation function `exportCrossValidationToPDF()`
2. Create sections for:
   - Report header with title, assessment ID, and generation date
   - Client information summary
   - Executive summary cards (discrepancy counts by severity)
   - Detailed validation results table
   - Risk score impact summary
   - Footer with page numbers
3. Add the "Exportar PDF" button to `FKCrossValidationResults` component
4. Handle button states (disabled when no results, loading during generation)

### Phase 3: Integration
1. Wire up the export button to the PDF generation utility
2. Add loading state and error handling
3. Test with various data scenarios (no discrepancies, many discrepancies, special characters)
4. Create E2E test file

## Step by Step Tasks

### Task 1: Read Reference Files and Understand Patterns
- Read `frontend/src/utils/pdfExport.ts` to understand the existing PDF generation pattern
- Read `frontend/src/components/risk/FKCrossValidationResults.tsx` to understand current component structure
- Read `frontend/src/types/risk.ts` to understand all relevant types
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_export_approved_contracts_pdf.md` to understand E2E test format

### Task 2: Create PDF Export Utility
Create `frontend/src/utils/crossValidationPdfExport.ts` with:
- Import jsPDF and autoTable (already installed)
- Copy Finkargo brand colors from existing pdfExport.ts
- Create helper function `formatValidationType(type: ValidationType): string` to convert enum values to Spanish labels
- Create helper function `formatSeverity(severity: DiscrepancySeverity): { label: string; color: string }`
- Create helper function `formatValueForPdf(value: unknown): string` for displaying complex values
- Implement main function:
```typescript
export const exportCrossValidationToPDF = (
  results: CrossValidationResponse,
  assessment: {
    assessment_id: string;
    client_nit: string;
    client_info?: ClientInfo;
  }
): void
```

### Task 3: Implement PDF Document Structure
In the export function, create the following sections:

**Header Section:**
- Title: "Reporte de Validación Cruzada - Finkargo"
- Assessment ID in monospace
- Export date and time
- Client NIT and company name

**Summary Section:**
- Total validation checks count
- Total discrepancies found
- Severity breakdown (Critical, High, Medium, Low counts)
- Total risk score impact

**Discrepancies Table (if any discrepancies exist):**
- Columns: Tipo de Validación, Campo, Severidad, Impacto, Descripción
- Sorted by severity (critical first)
- Color-coded severity cells

**Passed Validations Table:**
- Columns: Tipo de Validación, Campo, Documentos Comparados, Resultado
- Show all validations that passed

**Footer:**
- Page numbers
- Generation timestamp

### Task 4: Add Export Button to FKCrossValidationResults
Modify `frontend/src/components/risk/FKCrossValidationResults.tsx`:
- Add import for the new PDF export utility
- Add `exporting` state variable
- Add `handleExportPDF` async function
- Add "Exportar PDF" button in the header section (next to "Actualizar" button)
- Button requirements:
  - Icon: `PictureAsPdf` from MUI icons
  - Disabled when: `!results` or `exporting`
  - Loading state: show `CircularProgress` during export
  - Color: `primary` variant `contained`

### Task 5: Pass Assessment Context to Component
The `FKCrossValidationResults` component needs access to assessment details for the PDF. Update:
- Modify component props interface to include `assessmentId`, `clientNit`, and optionally `clientInfo`
- Update `RiskEvaluationDetail.tsx` to pass these props from the loaded assessment data

### Task 6: Create E2E Test File
Create `.claude/commands/e2e/test_cross_validation_pdf_report.md` with:
- User story for PDF export
- Prerequisites (logged in as risk user, evaluation with validation results exists)
- Test steps:
  1. Navigate to risk evaluation detail page
  2. Click on "Validación Cruzada" tab
  3. Run cross-validation (if not already run)
  4. Verify "Exportar PDF" button is visible and enabled
  5. Click "Exportar PDF" button
  6. Verify loading state appears
  7. Verify PDF file downloads
  8. Verify filename format: `validacion_cruzada_{assessment_id}_{YYYY-MM-DD}.pdf`
- Success criteria
- Screenshot locations

### Task 7: Handle Edge Cases
- No validation results yet: button disabled with tooltip "Ejecute la validación primero"
- All validations passed (no discrepancies): PDF still generates with "Sin discrepancias" message
- Special characters in company names: ensure UTF-8 encoding
- Long descriptions: text wrapping in table cells

### Task 8: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests
Since this is a client-side PDF generation feature and the project doesn't have frontend unit testing set up, validation will focus on:
- TypeScript compilation (no type errors)
- Linting passes
- E2E test for functional validation

### Edge Cases
1. **No validation results**: Button should be disabled
2. **Zero discrepancies**: PDF should generate with "No se encontraron discrepancias" message
3. **All severity levels**: PDF should correctly display all severity colors
4. **Long company names**: Text should wrap correctly in cells
5. **Special characters**: Spanish accents (á, é, í, ó, ú, ñ) should render correctly
6. **Large number of validations**: Multi-page PDF should paginate correctly
7. **Missing client info**: Should show "N/A" for missing fields

## Acceptance Criteria
1. "Exportar PDF" button appears in the Validación Cruzada tab when results are available
2. Button is disabled when no validation results exist
3. Button shows loading state during PDF generation
4. PDF downloads automatically with filename format: `validacion_cruzada_{assessment_id}_{date}.pdf`
5. PDF contains all required sections (header, client info, summary, tables)
6. Discrepancies are sorted by severity (critical first)
7. Severity levels are color-coded appropriately
8. Page numbers appear in footer
9. All Spanish text and special characters render correctly
10. No TypeScript errors or lint warnings
11. E2E test passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. **Backend Tests** (should be unaffected, run to verify no regressions):
```bash
cd backend && python -m pytest
```

2. **Backend Linting**:
```bash
cd backend && ruff check src/
```

3. **Frontend Linting**:
```bash
cd frontend && npm run lint
```

4. **TypeScript Type Check**:
```bash
cd frontend && npx tsc --noEmit
```

5. **Frontend Build** (validates production compilation):
```bash
cd frontend && npm run build
```

6. **E2E Test**:
Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_cross_validation_pdf_report.md` to validate this functionality works.

## Notes

### Dependencies
- **jsPDF**: Already installed in frontend (`frontend/node_modules/jspdf`)
- **jspdf-autotable**: Already installed (`frontend/node_modules/jspdf-autotable`)
- **date-fns**: Already installed for date formatting

### Design Decisions
1. **Client-side PDF generation**: Chosen to avoid adding backend complexity and to match existing pattern in `pdfExport.ts`
2. **No new API endpoints**: PDF uses data already available on the page
3. **Follows existing patterns**: Reuses styling and structure from contract PDF export
4. **Spanish labels**: All UI text in Spanish to match application language

### Future Considerations
- Could add option to include/exclude specific sections
- Could add option to export as Excel for further analysis
- Could integrate with email functionality to send reports directly
- Could add watermarks or digital signatures for compliance

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no database changes)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (already installed)

### Category-Specific Completeness
**Reporting:**
- [x] Query filters and parameters documented (N/A - uses existing data)
- [x] Pagination/sorting requirements specified (severity-based sorting in PDF)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable (N/A)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
