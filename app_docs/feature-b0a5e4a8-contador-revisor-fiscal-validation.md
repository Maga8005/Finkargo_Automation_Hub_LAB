# Contador/Revisor Fiscal Cross-Validation

**ADW ID:** b0a5e4a8
**Date:** 2025-12-31
**Specification:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md

## Overview

This feature adds cross-validation capability for accountants (contador) and fiscal auditors (revisor fiscal) who sign financial statements in the Riesgos (Risk/Fraud Detection) module. The system extracts contador/revisor fiscal information from official documents (Certificado de Existencia) and compares them against signatories found in financial statements to detect potential fraud involving unauthorized financial statement signatories.

## What Was Built

- New `CONTADOR_REVISOR_FISCAL` validation type added to the cross-validation framework
- Extraction schema updates for Certificado de Existencia to capture contador/revisor fiscal fields
- Cross-validation logic comparing financial statement signatories against registered professionals
- Fuzzy name matching with 85% similarity threshold for name variations
- Severity-based discrepancy detection (CRITICAL, HIGH, MEDIUM, INFO)
- Frontend type updates for displaying validation results in the UI
- Comprehensive unit tests covering all validation scenarios

## Technical Implementation

### Files Modified

- `backend/src/interface/risk_dtos.py`: Added `CONTADOR_REVISOR_FISCAL` to `ValidationType` enum
- `backend/src/core/servicios/risk/document_extraction_service.py`: Added contador/revisor fiscal fields to Certificado de Existencia extraction schema
- `backend/src/core/servicios/risk/cross_validation_service.py`: Implemented `_validate_contador_revisor_fiscal()` method (~216 lines)
- `frontend/src/types/risk.ts`: Added `contador_revisor_fiscal` to ValidationType union and labels
- `backend/tests/test_fraud_detection_service.py`: Added comprehensive test cases (~244 lines)
- `.claude/commands/e2e/test_contador_revisor_fiscal_validation.md`: E2E test specification

### Key Changes

- **Extraction Schema**: Added 6 new fields to `CERTIFICADO_EXISTENCIA` schema: `contador_name`, `contador_cedula`, `contador_license`, `revisor_fiscal_name`, `revisor_fiscal_cedula`, `revisor_fiscal_license`
- **Cross-Validation Logic**: Compares signatory/auditor from financial statements (current and prior) against registered contador/revisor fiscal in Certificado de Existencia using fuzzy name matching
- **Severity Levels**:
  - CRITICAL (25 points): Signatory cannot be verified - no registered professionals in certificate
  - HIGH (15 points): Signatory name does not match any registered professional
  - MEDIUM (8 points): Name matches but cedula/ID differs
  - INFO (0 points): Verified match - signatory matches registered professional

## How to Use

1. Upload a Certificado de Existencia document containing registered contador/revisor fiscal information
2. Upload Financial Statement(s) containing signatory information
3. Run cross-validation analysis from the Riesgos module
4. View contador/revisor fiscal validation results in the cross-validation panel
5. Review severity and description to understand match status

## Configuration

No additional configuration required. The feature uses existing cross-validation infrastructure:
- Fuzzy name matching uses 85% similarity threshold (existing `_names_match()` method)
- Severity score impacts follow existing patterns in `SCORE_IMPACT` mapping

## Testing

Run unit tests:
```bash
cd backend && python -m pytest tests/test_fraud_detection_service.py -v
```

Test cases cover:
- Verified match (INFO) - signatory matches registered professional
- Name mismatch (HIGH) - signatory doesn't match any registered professional
- Cedula mismatch (MEDIUM) - name matches but ID differs
- Not verifiable (CRITICAL) - no registered professionals in certificate
- Missing data handling - graceful handling when fields are empty
- Fuzzy matching - name variations still match within threshold

## Notes

### Colombian Regulatory Context

- **Contador Publico**: Certified accountant who prepares and certifies financial statements
- **Revisor Fiscal**: Independent auditor required for companies above certain thresholds
- Both professionals must be registered in the Certificado de Existencia from Camara de Comercio
- Financial statements must be signed by authorized professionals per Colombian regulations

### Fraud Detection Value

This validation helps detect:
- Fraudulent financial statements with fake professional signatures
- Identity impersonation using someone else's professional credentials
- Regulatory non-compliance from unsigned or improperly signed statements
- Document manipulation where signatories don't match registered professionals
