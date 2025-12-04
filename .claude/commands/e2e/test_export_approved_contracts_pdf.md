# E2E Test: Export Approved Contracts to PDF

## Test Overview
**Feature**: PDF Export for Approved Contracts
**Module**: Operations
**User Role**: operations, admin
**Estimated Duration**: 5-7 minutes
**Prerequisites**:
- Operations user account with valid credentials
- At least one approved contract in the database
- Browser with download permissions enabled
- Development servers running (frontend + backend)

## Test Objectives
1. Verify "Exportar PDF" button is visible in Contratos Aprobados screen
2. Validate PDF export generates and downloads a file
3. Verify PDF filename follows the naming convention
4. Test export functionality with filters applied
5. Validate Paga Local CO tab export works independently
6. Verify button states (enabled/disabled/loading) work correctly

## Environment Setup

### 1. Start Development Servers
```bash
cd /Users/danielrestrepo/Finkargo_Automation_Hub
cd scripts && ./start-dev.sh
```

**Verify servers are running:**
- Frontend: http://localhost:5173 (React app should load)
- Backend: http://localhost:8000/api/health (should return `{"status": "healthy"}`)

### 2. Prepare Test Data
Ensure there are approved contracts in the database. If not:
1. Navigate to Legal module
2. Generate a contract
3. Submit for review
4. Approve the contract (as admin/legal user)
5. Verify it appears in Operations → Contratos Aprobados

## Test Steps

### Test Case 1: Standard Contracts PDF Export

**Scenario**: Export standard contracts (Activos, Otrosí, Inventario) to PDF

#### Steps:
1. **Navigate to Operations Dashboard**
   - URL: http://localhost:5173/operations
   - Expected: Operations dashboard loads successfully

2. **Access Contratos Aprobados**
   - Click on "Contratos Aprobados" in the sidebar or dashboard
   - Expected: List of approved contracts displays in a table

3. **Verify "Exportar PDF" Button Presence**
   - Location: Top-right header section, next to "Actualizar" button
   - Expected: Button is visible with text "Exportar PDF" and download icon
   - Screenshot: `test_screenshots/pdf_export_button_visible.png`

4. **Verify Button State When Contracts Exist**
   - Expected: Button is ENABLED (not grayed out)
   - Expected: Button shows blue background (variant="contained")

5. **Click "Exportar PDF" Button**
   - Action: Click the "Exportar PDF" button
   - Expected: Button text changes to "Exportando..." with loading spinner
   - Expected: Button becomes disabled during export
   - Screenshot: `test_screenshots/pdf_export_loading_state.png`

6. **Verify PDF Download**
   - Expected: PDF file downloads to browser's default download location
   - Expected: Download completes within 2-3 seconds
   - Expected: No error messages appear

7. **Verify Filename Format**
   - Expected filename pattern: `contratos_aprobados_YYYY-MM-DD.pdf`
   - Example: `contratos_aprobados_2025-12-04.pdf`
   - Verify date matches current date

8. **Open and Inspect PDF**
   - Open the downloaded PDF file
   - Expected: PDF opens without errors
   - Expected: Title shows "Contratos Aprobados - Finkargo"
   - Expected: Export date and total contract count are displayed
   - Expected: Table contains 7 columns:
     - ID Contrato
     - Tipo
     - Cliente
     - NIT
     - Cupo Aprobado
     - Fecha Aprobación
     - Estado
   - Expected: All visible contracts from the table are present in PDF
   - Expected: Header row has dark blue background (#0C147B) with white text
   - Expected: Currency values are formatted as COP with thousand separators
   - Expected: Dates are formatted as DD/MM/YYYY HH:mm
   - Expected: Page numbers appear in footer
   - Screenshot: `test_screenshots/pdf_export_content.png`

### Test Case 2: Export with No Contracts

**Scenario**: Verify button is disabled when no contracts exist

#### Steps:
1. **Apply Filter to Show No Results**
   - Click "Filtros" button
   - Apply a filter that returns zero contracts (e.g., client NIT: "9999999999")
   - Expected: Table shows "No se encontraron contratos con los filtros aplicados"

2. **Verify Button State**
   - Expected: "Exportar PDF" button is DISABLED (grayed out)
   - Expected: Button cannot be clicked
   - Screenshot: `test_screenshots/pdf_export_button_disabled.png`

3. **Clear Filters**
   - Click "Limpiar Filtros"
   - Expected: Button becomes ENABLED again when contracts reappear

### Test Case 3: Export with Filters Applied

**Scenario**: Verify PDF export respects active filters

#### Steps:
1. **Apply Filter**
   - Click "Filtros" button
   - Select a specific contract type (e.g., "Activos" only)
   - Expected: Filter badge shows "1 filtro activo"
   - Expected: Table displays only filtered contracts

2. **Export Filtered Results**
   - Click "Exportar PDF" button
   - Expected: PDF downloads successfully

3. **Verify PDF Contains Only Filtered Data**
   - Open downloaded PDF
   - Expected: Only contracts matching the filter are included
   - Expected: Total count matches filtered count, not all contracts
   - Screenshot: `test_screenshots/pdf_export_filtered.png`

### Test Case 4: Paga Local CO Contracts Export

**Scenario**: Export Paga Local Colombia contracts independently

#### Steps:
1. **Navigate to Paga Local CO Tab**
   - In Operations → Contratos Aprobados
   - Click on "Paga Local CO" tab
   - Expected: List shows only Paga Local CO contract types

2. **Verify "Exportar PDF" Button Presence**
   - Expected: Button is visible in Paga Local CO tab
   - Expected: Button functions independently from standard tab

3. **Click "Exportar PDF" Button**
   - Action: Click the "Exportar PDF" button
   - Expected: Loading state appears

4. **Verify PDF Download**
   - Expected filename pattern: `paga_local_co_contratos_aprobados_YYYY-MM-DD.pdf`
   - Example: `paga_local_co_contratos_aprobados_2025-12-04.pdf`

5. **Open and Inspect PDF**
   - Open the downloaded PDF file
   - Expected: Title shows "Paga Local CO - Contratos Aprobados"
   - Expected: Subtitle shows "Finkargo" in coral color
   - Expected: Table contains only Paga Local CO contracts
   - Expected: Contract types include PL CO specific types:
     - Crédito Aval PJ/PN
     - Mandato PJ/PN
     - Crédito Sin Aval
     - Mandato Sin Aval
     - Mandato IM
     - Solicitud Desembolso
     - DIAN Mandato IM
   - Screenshot: `test_screenshots/pdf_export_paga_local_co.png`

### Test Case 5: Rapid Multiple Exports

**Scenario**: Test system stability with rapid consecutive exports

#### Steps:
1. **Export First PDF**
   - Click "Exportar PDF" button
   - Wait for download to complete

2. **Immediately Export Second PDF**
   - Click "Exportar PDF" button again immediately after first export
   - Expected: Second export works without errors
   - Expected: Both PDFs download successfully

3. **Verify Both Files**
   - Expected: Both PDF files exist in downloads folder
   - Expected: Both files are valid and open correctly
   - Expected: Both contain the same data (if no changes made between exports)

### Test Case 6: Special Characters in Data

**Scenario**: Verify PDF handles special characters correctly

#### Steps:
1. **Identify Contract with Special Characters**
   - Look for contracts with client names containing:
     - Spanish accents (á, é, í, ó, ú)
     - Letter ñ
     - Special symbols (&, /, -, etc.)

2. **Export PDF**
   - Click "Exportar PDF" button

3. **Verify Special Characters in PDF**
   - Open PDF
   - Expected: All Spanish characters render correctly (UTF-8 encoding)
   - Expected: No character corruption or replacement with "?"
   - Screenshot: `test_screenshots/pdf_export_special_chars.png`

## Validation Checklist

### Functional Requirements
- [ ] "Exportar PDF" button appears in standard contracts tab
- [ ] "Exportar PDF" button appears in Paga Local CO tab
- [ ] Button is enabled when contracts exist
- [ ] Button is disabled when no contracts exist
- [ ] Button shows loading state during export
- [ ] PDF file downloads successfully
- [ ] Filename follows naming convention with current date
- [ ] PDF opens without errors
- [ ] PDF contains correct title and branding

### PDF Content Validation
- [ ] Export date and total count displayed
- [ ] Table has 7 columns with correct headers
- [ ] All visible contracts are included
- [ ] Contract IDs are in monospace font
- [ ] Contract types have Spanish labels
- [ ] Client names display correctly
- [ ] NITs display correctly
- [ ] Currency values formatted as COP
- [ ] Dates formatted as DD/MM/YYYY HH:mm
- [ ] Estado column shows "Aprobado" for all rows
- [ ] Page numbers appear in footer

### PDF Styling Validation
- [ ] Header row has dark blue background (#0C147B)
- [ ] Header text is white and bold
- [ ] Alternating row colors for readability
- [ ] Text is legible and professional
- [ ] Table fits within page margins
- [ ] Multi-page PDFs have correct pagination

### Filter Integration
- [ ] Export respects active filters
- [ ] Filtered PDF count matches visible table count
- [ ] Filter summary included in PDF metadata (if implemented)

### Error Handling
- [ ] No console errors during export
- [ ] Appropriate error message if export fails
- [ ] Button re-enables after error

### Cross-Browser Compatibility
Test on multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (macOS)
- [ ] Edge (Windows)

## Known Issues & Edge Cases

### Edge Case 1: Large Datasets
If exporting 100+ contracts:
- PDF generation may take 2-5 seconds
- Browser may briefly freeze during generation
- Multiple pages should render correctly

### Edge Case 2: Very Long Client Names
- Text should wrap within table cells
- No text overflow or truncation
- Cell height adjusts automatically

### Edge Case 3: Empty Date Fields
- If `reviewed_at` is null, should display "N/A"
- No JavaScript errors in console

## Cleanup

After testing, clean up downloaded PDF files:
```bash
# Find and list PDF files
ls -lh ~/Downloads/contratos_aprobados_*.pdf
ls -lh ~/Downloads/paga_local_co_contratos_aprobados_*.pdf

# Delete test PDF files (optional)
rm ~/Downloads/contratos_aprobados_*.pdf
rm ~/Downloads/paga_local_co_contratos_aprobados_*.pdf
```

Stop development servers:
```bash
cd /Users/danielrestrepo/Finkargo_Automation_Hub
cd scripts && ./stop-dev.sh
```

## Success Criteria

**Test passes if:**
1. All checkboxes in Validation Checklist are checked
2. No console errors during any test case
3. All PDF files download and open successfully
4. PDF content matches table data exactly
5. Filters are respected correctly
6. Both standard and Paga Local CO exports work independently
7. Special characters render correctly

**Test fails if:**
- Button does not appear
- PDF fails to download
- PDF content is incorrect or incomplete
- Console errors occur
- Button states malfunction
- Filters are not respected

## Screenshots Location
All test screenshots should be saved to:
```
/Users/danielrestrepo/Finkargo_Automation_Hub/test_screenshots/
```

Screenshot naming convention:
- `pdf_export_button_visible.png`
- `pdf_export_loading_state.png`
- `pdf_export_content.png`
- `pdf_export_button_disabled.png`
- `pdf_export_filtered.png`
- `pdf_export_paga_local_co.png`
- `pdf_export_special_chars.png`

## Test Report Template

```markdown
# PDF Export E2E Test Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: Development (localhost)
**Browser**: [Chrome/Firefox/Safari/Edge] [Version]
**Status**: [PASS/FAIL]

## Test Results

### Test Case 1: Standard Contracts PDF Export
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 2: Export with No Contracts
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 3: Export with Filters Applied
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 4: Paga Local CO Contracts Export
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 5: Rapid Multiple Exports
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 6: Special Characters in Data
- Status: [PASS/FAIL]
- Notes: [Any observations]

## Issues Found
[List any bugs or issues discovered during testing]

## Recommendations
[Any suggestions for improvements]

## Screenshots
- Attached screenshots: [List screenshot files]
```

## Related Documentation
- Implementation Plan: `/Users/danielrestrepo/Finkargo_Automation_Hub/specs/issue-47-adw-20d8430f-sdlc_planner-add-pdf-export-approved-contracts.md`
- PDF Export Utility: `/Users/danielrestrepo/Finkargo_Automation_Hub/frontend/src/utils/pdfExport.ts`
- Component File: `/Users/danielrestrepo/Finkargo_Automation_Hub/frontend/src/components/forms/FKApprovedContracts.tsx`
