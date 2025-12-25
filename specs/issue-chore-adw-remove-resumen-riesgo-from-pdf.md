# Chore: Remove "Resumen de Riesgo" Section from PDF Report

## Chore Description
Remove the "Resumen de Riesgo" (Risk Summary) section from the "Reporte de Evaluación Completa" PDF export. This section displays the risk score, risk level, alerts count, and discrepancies count in a summary box.

**Problem**: When cross-validation for documents passes, the risk score shown may be low, which misleads reviewers into thinking the overall risk is acceptable. This reduces the urgency of manual verification when there ARE inconsistencies or triggered fraud indicators.

**Solution**: Remove the entire "Resumen de Riesgo" section from the PDF. The "RESULTADO DE EVALUACIÓN" section (which shows APROBADO/FALLIDO-REQUIERE REVISIÓN) already provides the critical verification status. The detailed fraud indicators table provides the specifics when needed.

**Current PDF Structure (affected area):**
1. RESULTADO DE EVALUACIÓN (verification status) - KEEP
2. ~~Resumen de Riesgo~~ (risk score, level, alerts, discrepancies) - REMOVE
3. Indicadores de Fraude Activados (fraud indicators table) - KEEP

## Relevant Files
Use these files to resolve the chore:

- `frontend/src/utils/crossValidationPdfExport.ts` - Contains the `exportComprehensiveEvaluationToPDF` function that generates the "Reporte de Evaluación Completa" PDF. Lines 595-641 contain the "Resumen de Riesgo" section that needs to be removed.

## Step by Step Tasks

### Task 1: Remove "Resumen de Riesgo" Section from PDF Export

- Open `frontend/src/utils/crossValidationPdfExport.ts`
- Locate the `exportComprehensiveEvaluationToPDF` function
- Find the section marked with comment `// ==================== RISK ASSESSMENT SUMMARY ====================` (around line 595)
- Remove the entire block from line 595 to line 641 (inclusive), which includes:
  - The grey background rectangle
  - "Resumen de Riesgo" title
  - Risk score display ("Puntaje")
  - Risk level display ("Nivel")
  - Alerts count display ("Alertas")
  - Discrepancies count display ("Discrepancias")
  - The `yPosition += 30;` at the end of the section
- **IMPORTANT**: Update the `yPosition` increment after the VERIFICATION STATUS section. Currently it ends with `yPosition += 25;` (line 593) and the removed section added `yPosition += 30;`. The next section (Fraud Indicators) needs proper spacing.
- After removal, verify that the next section (Fraud Indicators table) follows directly after the VERIFICATION STATUS section with appropriate spacing (add `yPosition += 5;` if needed for visual separation)

### Task 2: Verify No Orphaned References

- Search the file for any references to the removed variables:
  - `riskConfig` - verify it's not used elsewhere in the function (only used in removed section)
  - `colWidth` - verify it's not used elsewhere (only used in removed section)
  - `summaryY` - verify it's not used elsewhere (only used in removed section)
- If any of these are used elsewhere, keep only the necessary parts

### Task 3: Run Validation Commands

- Execute all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

- The "RESULTADO DE EVALUACIÓN" section (lines 577-593) should remain as it provides the critical verification status (APROBADO/FALLIDO-REQUIERE REVISIÓN)
- The Fraud Indicators table (lines 643+) should remain as it provides detailed information about triggered alerts
- The risk score and level are still visible in the UI - they are only being removed from the PDF report to avoid misleading reviewers
- This change only affects the `exportComprehensiveEvaluationToPDF` function, NOT the `exportCrossValidationToPDF` function (which has its own "Resumen de Validación" section for a different purpose)
