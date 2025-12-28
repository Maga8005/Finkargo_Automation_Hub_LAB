# E2E Test: Cross-Validation PDF Report Export

## Test Overview
**Feature**: PDF Report Export for Cross-Validation Results
**Module**: Risk Management (Gestión de Riesgos)
**User Role**: risk_analyst, risk_manager, admin
**Estimated Duration**: 5-7 minutes
**Prerequisites**:
- Risk user account with valid credentials
- At least one risk evaluation with completed cross-validation
- Browser with download permissions enabled
- Development servers running (frontend + backend)

## User Story

As a risk analyst or risk manager
I want to export cross-validation findings as a PDF report
So that I can share the fraud detection analysis with stakeholders and maintain compliance records

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with risk_analyst or risk_manager role
- At least one risk evaluation with:
  - Uploaded documents (minimum 2)
  - Completed cross-validation with results

## Test Credentials

Use credentials from `backend/.env`:
- Email: `$TEST_ADMIN_EMAIL` (admin@finkargo.com)
- Password: `$TEST_ADMIN_PASSWORD`
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Test Case 1: Export PDF with Discrepancies

**Scenario**: Export cross-validation results that contain discrepancies

#### Steps:

1. **Navigate to Login Page**
   - URL: http://localhost:5173
   - Expected: Login page loads successfully

2. **Authenticate as Risk User**
   - Enter test email and password
   - Click "Iniciar Sesión"
   - Expected: Successful redirect to dashboard

3. **Navigate to Risk Dashboard**
   - Click on "Gestión de Riesgos" in sidebar
   - Expected: Risk dashboard loads with evaluations list

4. **Open Risk Evaluation Detail**
   - Click on an existing risk evaluation row (one with completed validation)
   - Expected: Evaluation detail page loads with tabs

5. **Navigate to Cross-Validation Tab**
   - Click on "Validación Cruzada" tab
   - Expected: Cross-validation results display
   - **Verify**: Results are visible with discrepancy counts
   - Screenshot: `01_cross_validation_results.png`

6. **Verify Export Button Presence**
   - Location: Header section, next to "Actualizar" button
   - Expected: "Exportar PDF" button is visible with PDF icon
   - Expected: Button is ENABLED (not grayed out)
   - Screenshot: `02_export_button_visible.png`

7. **Click Export PDF Button**
   - Action: Click the "Exportar PDF" button
   - Expected: Button text changes to "Exportando..." with loading spinner
   - Expected: Button becomes disabled during export
   - Screenshot: `03_export_loading_state.png`

8. **Verify PDF Download**
   - Expected: PDF file downloads to browser's default download location
   - Expected: Download completes within 1-2 seconds
   - Expected: No error messages appear

9. **Verify Filename Format**
   - Expected filename pattern: `validacion_cruzada_{assessment_id}_{YYYY-MM-DD}.pdf`
   - Example: `validacion_cruzada_RISK-2024-001_2025-12-22.pdf`
   - Verify date matches current date

10. **Open and Inspect PDF**
    - Open the downloaded PDF file
    - Expected: PDF opens without errors
    - Expected: Content includes:
      - Title: "Reporte de Validación Cruzada"
      - Subtitle: "Finkargo - Módulo de Gestión de Riesgos"
      - Assessment ID displayed
      - Client NIT displayed
      - Company name (if available)
      - Export date and validation date
      - Summary section with discrepancy counts
      - Discrepancies table (sorted by severity)
      - Passed validations table
      - Page numbers in footer
    - Screenshot: `04_pdf_content.png`

### Test Case 2: PDF Content Validation

**Scenario**: Verify PDF content accuracy

#### Steps:

1. **Compare Summary Statistics**
   - Match PDF summary counts with on-screen values:
     - Total validations count
     - Total discrepancies
     - Critical count
     - High count
     - Medium/Low count
   - Expected: All counts match exactly

2. **Verify Discrepancies Table**
   - Expected: Table has columns:
     - Tipo de Validación
     - Campo
     - Severidad
     - Impacto
     - Descripción
   - Expected: Rows sorted by severity (critical first)
   - Expected: Severity cells are color-coded:
     - Crítico: Red background with white text
     - Alto: Light red background
     - Medio: Orange/yellow background
     - Bajo: Green background
   - Screenshot: `05_discrepancies_table.png`

3. **Verify Passed Validations Table**
   - Expected: Table has columns:
     - Tipo de Validación
     - Campo
     - Documentos Comparados
     - Resultado
   - Expected: All rows show "Consistente" in Resultado column

4. **Verify Spanish Labels**
   - Expected: All text in Spanish
   - Validation types have Spanish labels:
     - company_name → "Nombre de Empresa"
     - nit → "NIT"
     - legal_representative → "Representante Legal"
     - shareholders → "Accionistas"
     - financial_continuity → "Continuidad Financiera"

### Test Case 3: Export with No Discrepancies

**Scenario**: Export when all validations passed

#### Steps:

1. **Navigate to Evaluation with No Discrepancies**
   - Find an evaluation where all cross-validations passed
   - Expected: Total discrepancies shows 0

2. **Export PDF**
   - Click "Exportar PDF" button
   - Expected: PDF generates successfully

3. **Verify PDF Content**
   - Open downloaded PDF
   - Expected: Green success message "Sin discrepancias encontradas"
   - Expected: No discrepancies table (or empty table)
   - Expected: Passed validations table shows all checks
   - Screenshot: `06_no_discrepancies.png`

### Test Case 4: Button State Before Validation

**Scenario**: Verify button is not visible when no results exist

#### Steps:

1. **Navigate to Evaluation Without Validation**
   - Find an evaluation that hasn't been cross-validated yet
   - Expected: No validation results displayed

2. **Verify Button Not Visible**
   - Expected: "Exportar PDF" button is NOT visible
   - Expected: Only "Ejecutar Validación" button is visible
   - Screenshot: `07_no_export_before_validation.png`

3. **Run Validation**
   - Click "Ejecutar Validación"
   - Wait for validation to complete
   - Expected: Results appear

4. **Verify Button Now Visible**
   - Expected: "Exportar PDF" button appears after validation completes
   - Screenshot: `08_export_after_validation.png`

### Test Case 5: Special Characters Handling

**Scenario**: Verify PDF handles Spanish special characters

#### Steps:

1. **Find Evaluation with Special Characters**
   - Look for company names with:
     - Spanish accents (á, é, í, ó, ú)
     - Letter ñ
     - Special symbols (&, /, -)

2. **Export PDF**
   - Click "Exportar PDF" button

3. **Verify Character Rendering**
   - Open PDF
   - Expected: All Spanish characters render correctly (UTF-8)
   - Expected: No character corruption or "?" replacements
   - Screenshot: `09_special_characters.png`

## Validation Checklist

### Functional Requirements
- [ ] "Exportar PDF" button appears when validation results exist
- [ ] Button is hidden when no validation results
- [ ] Button shows loading state during export
- [ ] PDF file downloads successfully
- [ ] Filename follows naming convention with assessment ID and date

### PDF Content Validation
- [ ] Title and branding displayed correctly
- [ ] Assessment ID in monospace font
- [ ] Client NIT displayed
- [ ] Company name displayed (if available)
- [ ] Export date and validation date displayed
- [ ] Summary section shows correct counts
- [ ] Discrepancies table present (if discrepancies exist)
- [ ] Discrepancies sorted by severity
- [ ] Severity cells color-coded
- [ ] Passed validations table present
- [ ] Page numbers in footer

### PDF Styling Validation
- [ ] Finkargo brand colors used correctly
- [ ] Header uses dark blue (#0C147B)
- [ ] Coral accent color (#EB8774) for subtitle
- [ ] Table headers have proper styling
- [ ] Alternating row colors for readability
- [ ] Text is legible and professional

### Error Handling
- [ ] No console errors during export
- [ ] Error message shown if export fails
- [ ] Button re-enables after error

## Known Issues & Edge Cases

### Edge Case 1: Long Descriptions
- Description text should wrap in table cells
- Very long descriptions may be truncated

### Edge Case 2: Many Validations
- PDF should paginate correctly for large result sets
- Page numbers should update accordingly

### Edge Case 3: Missing Client Info
- If client info is unavailable, should show "N/A"
- PDF should still generate without errors

## Cleanup

After testing, clean up downloaded PDF files:
```bash
# Find and list PDF files
ls -lh ~/Downloads/validacion_cruzada_*.pdf

# Delete test PDF files (optional)
rm ~/Downloads/validacion_cruzada_*.pdf
```

Stop development servers:
```bash
cd scripts && ./stop-dev.sh
```

## Success Criteria

**Test passes if:**
1. All checkboxes in Validation Checklist are checked
2. No console errors during any test case
3. PDF files download and open successfully
4. PDF content matches on-screen data exactly
5. Severity sorting and color-coding work correctly
6. Spanish characters render correctly
7. Button states work as expected

**Test fails if:**
- Button does not appear when expected
- PDF fails to download
- PDF content is incorrect or incomplete
- Console errors occur
- Button states malfunction
- Characters are corrupted in PDF

## Screenshots Location

All test screenshots should be saved to:
```
<codebase>/agents/<adw_id>/<agent_name>/img/test_cross_validation_pdf_report/
```

Screenshot naming convention:
- `01_cross_validation_results.png`
- `02_export_button_visible.png`
- `03_export_loading_state.png`
- `04_pdf_content.png`
- `05_discrepancies_table.png`
- `06_no_discrepancies.png`
- `07_no_export_before_validation.png`
- `08_export_after_validation.png`
- `09_special_characters.png`

## Test Report Template

```markdown
# Cross-Validation PDF Export E2E Test Report

**Date**: YYYY-MM-DD
**Tester**: [Your Name]
**Environment**: Development (localhost)
**Browser**: [Chrome/Firefox/Safari/Edge] [Version]
**Status**: [PASS/FAIL]

## Test Results

### Test Case 1: Export PDF with Discrepancies
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 2: PDF Content Validation
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 3: Export with No Discrepancies
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 4: Button State Before Validation
- Status: [PASS/FAIL]
- Notes: [Any observations]

### Test Case 5: Special Characters Handling
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
- Implementation Plan: `specs/issue-0-adw-0-sdlc_planner-cross-validation-pdf-report.md`
- PDF Export Utility: `frontend/src/utils/crossValidationPdfExport.ts`
- Component File: `frontend/src/components/risk/FKCrossValidationResults.tsx`
