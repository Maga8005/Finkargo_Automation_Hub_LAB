# Feature: Add PDF Export to Approved Contracts Screen

## Feature Description
Add PDF export functionality to the "Contratos Aprobados" screen in the Operations module. This feature will allow operations users to export the approved contracts list as a single PDF document containing all visible contracts in a professional, printable format. Currently, the module only supports Excel export - this feature adds PDF as an additional export option for users who need formatted documents for reports or physical filing.

## User Story
As an operations team member
I want to export the approved contracts list to a PDF file
So that I can generate professional reports for management, create printable archives, and share formatted contract summaries with stakeholders who require PDF documents

## Problem Statement
The Operations module currently supports Excel export for approved contracts, which is excellent for data analysis. However, users frequently need to generate professional PDF reports for:
- Executive summaries and management presentations
- Physical archival and filing requirements
- Email attachments that are universally readable without spreadsheet software
- Official reports that require consistent formatting and pagination

Without PDF export, users must manually create PDFs from Excel files or copy-paste data into document editors, which is time-consuming and error-prone.

## Solution Statement
Implement PDF export functionality using the `jsPDF` library with `jspdf-autotable` plugin for professional table formatting. The solution will:
- Add a "Exportar PDF" button next to the existing "Exportar Excel" button
- Generate a PDF document with Finkargo branding (logo, colors)
- Display approved contracts in a well-formatted table with all columns
- Apply appropriate formatting (dates, currency, contract types)
- Respect active filters (exports only visible contracts)
- Include metadata (export date, total contracts, filter summary)
- Support both standard contracts and Paga Local CO contracts

The implementation follows the existing Excel export pattern for consistency.

## Access Control
- **Required Role(s):** `operations` or `admin`
- **Backend Protection:** No new backend endpoint needed - PDF generation is client-side like Excel export
- **Frontend Protection:** Inherits existing role protection from `FKApprovedContracts` and `FKPagaLocalCOApprovedContracts` components, which are accessed through `RoleProtectedRoute` in the Operations Dashboard

## Relevant Files
Use these files to implement the feature:

### Existing Files to Modify

- **`frontend/src/components/forms/FKApprovedContracts.tsx`** (555 lines)
  - Currently implements Excel export button and handler
  - Need to add PDF export button next to Excel button
  - Need to add `handleExportPDF()` handler that calls PDF utility
  - Import PDF export utility function

- **`frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx`** (524 lines)
  - Mirror implementation from FKApprovedContracts
  - Add PDF export button for Paga Local CO contracts
  - Add handler specific to Paga Local CO contract types

- **`frontend/package.json`**
  - Add `jspdf` dependency (~2.5.2)
  - Add `jspdf-autotable` dependency (~3.8.4)

### Reference Files (Study Before Implementation)

- **`frontend/src/utils/excelExport.ts`** (167 lines)
  - Excellent reference for export utility structure
  - Shows how to format dates, currency, contract types
  - Demonstrates column configuration and data mapping
  - Pattern to follow for PDF export utility

- **`frontend/src/services/operationsService.ts`**
  - Shows data structure of `ContractGeneration` type
  - Confirms no backend changes needed (client-side export)

- **`frontend/src/theme/theme.ts`**
  - Finkargo brand colors for PDF styling:
    - Primary dark: #0C147B
    - Primary main: #3C47D3
    - Coral: #EB8774

- **`.claude/commands/test_e2e.md`**
  - E2E test framework instructions
  - How to structure test files

- **`.claude/commands/e2e/test_login.md`**
  - Example E2E test showing authentication flow
  - Pattern for verifying UI elements

- **`.claude/commands/e2e/test_export_approved_contracts_excel.md`**
  - Existing test for Excel export (can be adapted for PDF)
  - Shows validation steps for export functionality

### New Files

- **`frontend/src/utils/pdfExport.ts`** (~250 lines estimated)
  - Main PDF export utility module
  - `exportContractsToPDF(contracts: ContractGeneration[]): void` - Export standard contracts
  - `exportPagaLocalContractsToPDF(contracts: ContractGeneration[]): void` - Export Paga Local CO contracts
  - Helper functions for formatting and table generation
  - Finkargo branding (logo positioning, colors, typography)

- **`.claude/commands/e2e/test_export_approved_contracts_pdf.md`** (~100 lines estimated)
  - E2E test validating PDF export functionality
  - Based on existing Excel export test structure
  - Verifies button presence, file download, PDF format

## Implementation Plan

### Phase 1: Foundation
**Install Dependencies and Study References**
- Install `jspdf` and `jspdf-autotable` npm packages
- Read and understand `excelExport.ts` structure and patterns
- Read `FKApprovedContracts.tsx` to understand current export button placement
- Study Finkargo theme colors from `theme.ts`
- Review `ContractGeneration` type structure from `operationsService.ts`

### Phase 2: Core Implementation
**Create PDF Export Utility**
- Create `frontend/src/utils/pdfExport.ts` with two main functions:
  - `exportContractsToPDF()` - Standard contracts (Activos, Otrosí, Inventario)
  - `exportPagaLocalContractsToPDF()` - Paga Local CO contracts
- Implement PDF document setup:
  - A4 portrait format
  - Finkargo branding (title, logo positioning, colors)
  - Metadata (title, subject, author, creation date)
- Implement table generation with columns:
  - ID Contrato (monospace font)
  - Tipo (Spanish labels with color coding)
  - Cliente
  - NIT
  - Cupo Aprobado (COP currency format)
  - Fecha Aprobación (DD/MM/YYYY HH:mm format)
  - Estado (always "Aprobado")
- Apply professional formatting:
  - Header row: Dark blue background (#0C147B), white text, bold
  - Alternating row colors for readability
  - Currency formatting with thousand separators
  - Date formatting using `date-fns`
  - Auto column widths
- Add footer with page numbers and export date
- Include summary section:
  - Total contracts exported
  - Active filters summary (if any)
  - Export timestamp

**Update Components**
- Modify `FKApprovedContracts.tsx`:
  - Import PDF export function
  - Add `exporting` state for PDF export loading
  - Add `handleExportPDF()` handler
  - Add "Exportar PDF" button next to "Exportar Excel" button
  - Button shows loading state during generation
  - Button disabled when no contracts
- Modify `FKPagaLocalCOApprovedContracts.tsx`:
  - Same changes as above
  - Use Paga Local CO specific export function

### Phase 3: Integration
**Connect to Existing Workflows**
- Ensure PDF export respects active filters (exports visible data only)
- Match Excel export button styling and placement for consistency
- Test with different data scenarios:
  - Empty list (button should be disabled)
  - Single contract
  - Large list (100+ contracts, pagination handling)
  - Filtered data
  - Special characters in client names
- Ensure proper error handling and user feedback

**Create E2E Test**
- Create `.claude/commands/e2e/test_export_approved_contracts_pdf.md`
- Based on existing Excel export test structure
- Validate PDF download and file properties

## Step by Step Tasks

### 1. Install Dependencies
- Run `cd frontend && npm install jspdf jspdf-autotable`
- Run `npm install --save-dev @types/jspdf-autotable` (if types available)
- Verify installation with `npm list jspdf jspdf-autotable`

### 2. Study Reference Files
- Read `frontend/src/utils/excelExport.ts` to understand:
  - Export utility structure and function signatures
  - Date formatting patterns (using `date-fns`)
  - Currency formatting for COP
  - Contract type label mapping
  - Filename conventions
- Read `frontend/src/components/forms/FKApprovedContracts.tsx` lines 234-254 to understand:
  - Current button placement in header section
  - Button styling patterns
  - Loading state management
- Read `frontend/src/theme/theme.ts` to extract Finkargo brand colors

### 3. Create PDF Export Utility
- Create `frontend/src/utils/pdfExport.ts` with:
  - Import statements: `jspdf`, `jspdf-autotable`, `date-fns`
  - Type imports: `ContractGeneration` from `types/legal`
  - Constants: Finkargo colors, table styles, font sizes
  - Helper function: `formatContractTypeLabel(type: string): string` - Map contract types to Spanish labels
  - Helper function: `formatCurrency(amount: number): string` - Format COP currency
  - Helper function: `formatDate(dateString: string): string` - Format dates as DD/MM/YYYY HH:mm
  - Main function: `exportContractsToPDF(contracts: ContractGeneration[]): void`
    - Create jsPDF instance (A4, portrait)
    - Add title "Contratos Aprobados - Finkargo"
    - Add export date metadata
    - Configure table with 7 columns
    - Map contract data to table rows with formatting
    - Apply Finkargo brand styling
    - Add page numbers in footer
    - Save as `contratos_aprobados_YYYY-MM-DD.pdf`
  - Main function: `exportPagaLocalContractsToPDF(contracts: ContractGeneration[]): void`
    - Same as above but titled "Paga Local CO - Contratos Aprobados"
    - Save as `paga_local_co_contratos_aprobados_YYYY-MM-DD.pdf`

### 4. Update FKApprovedContracts Component
- Open `frontend/src/components/forms/FKApprovedContracts.tsx`
- Add import: `import { exportContractsToPDF } from '../../utils/pdfExport';`
- Add state: `const [exportingPDF, setExportingPDF] = useState(false);`
- Add handler function after `handleDownloadPDF()`:
  ```typescript
  const handleExportPDF = async () => {
    try {
      setExportingPDF(true);
      exportContractsToPDF(contracts);
    } catch (err) {
      console.error('Error exporting PDF:', err);
      alert('Error al exportar PDF');
    } finally {
      setExportingPDF(false);
    }
  };
  ```
- Add PDF export button in header section (around line 254, after "Actualizar" button):
  ```tsx
  <Button
    variant="contained"
    size="small"
    onClick={handleExportPDF}
    disabled={contracts.length === 0 || exportingPDF}
    startIcon={exportingPDF ? <CircularProgress size={16} /> : <PictureAsPdf />}
    sx={{ textTransform: 'none' }}
  >
    {exportingPDF ? 'Exportando...' : 'Exportar PDF'}
  </Button>
  ```
- Import `PictureAsPdf` icon from `@mui/icons-material` if not already imported

### 5. Update FKPagaLocalCOApprovedContracts Component
- Open `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx`
- Make identical changes as Step 4, but:
  - Import `exportPagaLocalContractsToPDF` instead
  - Call `exportPagaLocalContractsToPDF(contracts)` in handler

### 6. Create E2E Test File
- Create `.claude/commands/e2e/test_export_approved_contracts_pdf.md`
- Based on structure from `test_export_approved_contracts_excel.md`
- Include test steps:
  1. Login with operations role
  2. Navigate to Operations → Contratos Aprobados
  3. Verify "Exportar PDF" button is visible
  4. Click "Exportar PDF" button
  5. Verify button shows loading state
  6. Verify PDF file downloads
  7. Verify filename format: `contratos_aprobados_YYYY-MM-DD.pdf`
  8. (Optional) Verify PDF contains expected data
  9. Test with filters applied
  10. Test Paga Local CO tab export
- Define success criteria
- Specify screenshot locations

### 7. Run Validation Commands
Execute all validation commands listed below to ensure zero regressions and successful implementation.

## Testing Strategy

### Unit Tests
Currently, the frontend does not have a testing framework configured (per CLAUDE.md). When testing infrastructure is added:
- **PDF Export Utility Tests** (`pdfExport.test.ts`):
  - Test `formatContractTypeLabel()` with all contract types
  - Test `formatCurrency()` with various amounts (0, decimals, large numbers)
  - Test `formatDate()` with valid dates and edge cases
  - Mock jsPDF and verify table data and styling
  - Test empty contracts array handling
  - Test special characters in client names
- **Component Tests**:
  - Test "Exportar PDF" button renders correctly
  - Test button is disabled when `contracts.length === 0`
  - Test loading state shows during export
  - Test error handling when export fails

### Integration Tests
- **E2E Test** (`.claude/commands/e2e/test_export_approved_contracts_pdf.md`):
  - Full user flow from login to PDF download
  - Verify file download mechanism
  - Verify PDF format and filename
  - Test with filters applied
  - Test both standard and Paga Local CO tabs

### Edge Cases
- **Empty contracts list**: Button should be disabled with appropriate styling
- **Large datasets (100+ contracts)**: Verify PDF handles pagination correctly without timeouts
- **Missing/null data fields**: Verify "N/A" is displayed for missing data
- **Special characters in client names**: Verify UTF-8 encoding in PDF (accents, ñ, special symbols)
- **Very long client names**: Verify text wrapping in table cells
- **Zero or negative cupo values**: Verify currency formatting handles edge cases
- **Active filters**: Verify PDF export only includes filtered/visible contracts
- **Browser download blocking**: User should see appropriate error message

## Acceptance Criteria
1. **PDF Export Button Present**: "Exportar PDF" button appears in header section of both FKApprovedContracts and FKPagaLocalCOApprovedContracts components
2. **Button Styling**: Button matches existing Finkargo design system (Material-UI theme, proper sizing, icon)
3. **Button States**:
   - Enabled when contracts exist
   - Disabled when no contracts or during export
   - Shows loading spinner and "Exportando..." text during generation
4. **PDF Generation**: Clicking button generates and downloads a PDF file
5. **Filename Format**:
   - Standard: `contratos_aprobados_YYYY-MM-DD.pdf`
   - Paga Local CO: `paga_local_co_contratos_aprobados_YYYY-MM-DD.pdf`
6. **PDF Content**: PDF contains all visible contracts with 7 columns (ID, Tipo, Cliente, NIT, Cupo, Fecha, Estado)
7. **PDF Formatting**:
   - Professional table layout with Finkargo brand colors
   - Dates formatted as DD/MM/YYYY HH:mm
   - Currency formatted as COP with thousand separators
   - Contract types with Spanish labels
   - Page numbers in footer
   - Export metadata (date, total count)
8. **Filter Respect**: PDF export includes only contracts visible with active filters
9. **Error Handling**: Appropriate error messages shown if export fails
10. **No Console Errors**: No errors in browser console during export
11. **TypeScript Compliance**: No TypeScript errors (`npx tsc --noEmit` passes)
12. **Linting Compliance**: Code passes ESLint (`npm run lint` passes)
13. **Build Success**: Frontend builds successfully (`npm run build` passes)
14. **E2E Test Exists**: Test file created and documented
15. **Cross-browser Compatibility**: PDF download works in Chrome, Firefox, Safari, Edge

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# 1. Verify dependencies installed
cd frontend && npm list jspdf jspdf-autotable

# 2. Run TypeScript type check (must pass with no errors)
cd frontend && npx tsc --noEmit

# 3. Run frontend linting (must pass with no errors)
cd frontend && npm run lint

# 4. Run frontend production build (must complete successfully)
cd frontend && npm run build

# 5. Run backend tests to ensure no regressions
cd backend && python -m pytest

# 6. Run backend linting
cd backend && ruff check src/

# 7. Manual E2E Test Execution
# Read and execute the E2E test file:
# - Read `.claude/commands/test_e2e.md`
# - Read and execute `.claude/commands/e2e/test_export_approved_contracts_pdf.md`
# - Validate all success criteria pass
# - Verify screenshots are captured

# 8. Manual Browser Testing
# - Start dev servers: `cd scripts && ./start-dev.sh`
# - Navigate to http://localhost:5173
# - Login with operations test account
# - Go to Operations → Contratos Aprobados
# - Verify "Exportar PDF" button appears next to "Exportar Excel"
# - Click "Exportar PDF" button
# - Verify PDF downloads with correct filename
# - Open PDF and verify:
#   - All contracts are present
#   - Table formatting is professional
#   - Dates and currency are formatted correctly
#   - Finkargo branding is visible
#   - Page numbers appear
# - Test with filters applied (verify only filtered contracts export)
# - Test Paga Local CO tab export
# - Stop servers: `cd scripts && ./stop-dev.sh`
```

## Notes

### Library Choice: jsPDF vs Alternatives
- **jsPDF** chosen for consistency with common practice and simplicity
- Alternatives considered:
  - `pdfmake`: More complex configuration, overkill for table export
  - `react-pdf`: Requires React component rendering, adds complexity
  - Backend PDF generation: Unnecessary - client-side is faster and reduces server load
- **jspdf-autotable** plugin provides professional table formatting out-of-the-box

### Design Consistency
- PDF export button placement mirrors Excel export for intuitive UX
- Both buttons use similar styling (variant, size, loading states)
- Filename conventions match Excel export pattern (`_YYYY-MM-DD` suffix)
- Export respects filters to match user expectations from Excel export

### Performance Considerations
- PDF generation is synchronous but fast (< 1 second for 100 contracts)
- Loading state provides user feedback during generation
- No backend API calls needed - reduces latency
- Browser handles file download natively

### Future Enhancements (Out of Scope)
- **Batch export**: Export all contracts across multiple pages (if pagination added later)
- **Custom PDF templates**: Allow users to choose different report layouts
- **PDF email integration**: Option to email PDF instead of download
- **Print preview**: Show PDF preview before download
- **Export customization**: Allow users to select which columns to include

### Accessibility
- Export button includes proper `aria-label` for screen readers
- Loading state is announced to screen readers
- Button disabled state provides clear visual feedback
- High contrast colors in PDF for printability

### Known Limitations
- PDF generation is client-side only (no server-side archival)
- Large datasets (500+ contracts) may cause brief browser freeze during generation
- PDF size grows linearly with contract count (acceptable for typical use cases)

### Development Tips
- Test PDF generation with `localhost:5173` first before deploying
- Use browser DevTools to verify download event fires
- Check browser download settings if PDF doesn't appear
- Use `console.log()` in export utility to debug data formatting issues
- Verify UTF-8 encoding for Spanish characters (á, é, í, ó, ú, ñ)
