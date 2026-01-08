# Email Chain Alerts PDF Table

**ADW ID:** 5aa7591c
**Date:** 2026-01-01
**Specification:** specs/issue-67-adw-5aa7591c-sdlc_planner-email-chain-alerts-table.md

## Overview

This feature adds email chain alert data to the comprehensive risk evaluation PDF report (Reporte de Evaluacion Completa). The PDF export now includes a "Discrepancias en Cadenas de Email" table that displays email chain discrepancies with validation status and analyst comments, providing a complete audit trail of communication-related fraud indicators.

## What Was Built

- Data flow pipeline connecting email chain state from uploader to PDF export
- Callback mechanism to propagate email chain updates through component hierarchy
- Integration of email chains into the comprehensive report context
- E2E test file for validating the email chain alerts table in PDF exports

## Technical Implementation

### Files Modified

- `frontend/src/components/risk/FKEmailChainUploader.tsx`: Added `onEmailChainsUpdate` callback prop and useEffect to notify parent when chains change
- `frontend/src/components/risk/FKExternalContactTab.tsx`: Added prop passthrough for `onEmailChainsUpdate` callback to FKEmailChainUploader
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx`: Added `emailChains` state, included in PDF report context, connected callback from FKExternalContactTab

### Key Changes

- **Callback Pattern**: FKEmailChainUploader now exposes an `onEmailChainsUpdate` callback that fires when the `chains` state changes, allowing parent components to track email chain data
- **State Propagation**: Email chains flow from FKEmailChainUploader -> FKExternalContactTab -> RiskEvaluationDetail, ensuring the page component has access to current email chain data
- **PDF Context Integration**: The `emailChains` array is now included in `ComprehensiveReportContext` when calling `exportComprehensiveEvaluationReport()`, enabling the existing PDF table code to render email chain discrepancies

### New Files

- `.claude/commands/e2e/test_email_chain_alerts_pdf_table.md`: E2E test specification for validating email chain alerts in PDF exports

## How to Use

1. Navigate to a risk evaluation detail page (`/risk/evaluations/:id`)
2. Go to the "Comunicacion Externa" tab
3. Upload email chain documents (PDF or paste text)
4. The system will analyze email chains and detect discrepancies
5. Validate discrepancies with reasons and comments (if needed)
6. Click "Exportar PDF" or "Reporte Completo" button to generate the comprehensive report
7. The downloaded PDF will include "Discrepancias en Cadenas de Email" table

## PDF Table Specifications

The email chain alerts table includes:

| Column | Description |
|--------|-------------|
| Cadena | Email chain identifier/filename |
| Campo | Field type (e.g., "Dominio del Remitente", "Nombre de Empresa", "NIT") |
| Severidad | Severity level with color coding (critical=red, high=orange, medium=yellow) |
| Valor | The email value that triggered the discrepancy |
| Descripcion | Description of the issue detected |
| Validacion | Validation status - "Pendiente" (orange) or reason label (green) |
| Comentarios | Analyst comments (truncated at 80 chars with "...") |

### Filtering Rules

- Only HIGH, CRITICAL, and MEDIUM severity discrepancies appear in the table
- INFO severity discrepancies are excluded
- Table section only appears if significant discrepancies exist

## Configuration

No additional configuration required. The feature uses existing PDF export settings and Finkargo design system colors.

## Testing

Run the E2E test to validate the feature:

1. Read `.claude/commands/test_e2e.md` for E2E test runner instructions
2. Execute `.claude/commands/e2e/test_email_chain_alerts_pdf_table.md`

Manual testing steps:
1. Login as mesa_control or admin user
2. Navigate to a risk evaluation with email chains
3. Export the comprehensive PDF report
4. Verify the "Discrepancias en Cadenas de Email" table appears with correct data

## Notes

- The PDF table rendering code already existed in `crossValidationPdfExport.ts` (lines 867-993); this implementation connected the data flow
- The existing table implementation includes all required columns, color coding, and validation display
- Page breaks are automatically handled when `yPosition > 200`
- Comments are truncated using the existing `truncateComment()` utility function
