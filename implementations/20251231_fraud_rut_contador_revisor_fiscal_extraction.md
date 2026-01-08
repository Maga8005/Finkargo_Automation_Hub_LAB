# Implementation Report: RUT Contador/Revisor Fiscal Extraction

## Metadata
- **Date**: 2025-12-31
- **ADW ID**: `b0a5e4a8`
- **Branch**: `feature-issue-61-adw-b0a5e4a8-contador-revisor-fiscal-validation`
- **Related Spec**: `specs/patch/patch-adw-b0a5e4a8-rut-contador-revisor-fiscal-extraction.md`

## Summary

Implemented RUT-based extraction of contador (accountant) and revisor fiscal (fiscal auditor) information as a fallback source when Certificado de Existencia lacks this data. This addresses cases like IMPORTADORA MULTIVALVULAS S.A.S. where the Certificado de Existencia has no contador/revisor fiscal information but the RUT document does.

## Changes Made

### 1. RUT Extraction Schema (`document_extraction_service.py`)
Added 7 new fields to the RUT document extraction schema:
- `contador_name` - Full name of accountant (from RUT fields 152-155)
- `contador_cedula` - Accountant ID number (from RUT field 149)
- `contador_license` - Professional license if available
- `revisor_fiscal_principal_name` - Principal revisor fiscal name (from RUT fields 128-131)
- `revisor_fiscal_principal_cedula` - Principal revisor fiscal ID (from RUT field 125)
- `revisor_fiscal_suplente_name` - Suplente revisor fiscal name (from RUT fields 140-143)
- `revisor_fiscal_suplente_cedula` - Suplente revisor fiscal ID (from RUT field 137)

### 2. Cross-Validation Service (`cross_validation_service.py`)
Modified `_validate_contador_revisor_fiscal()` method to:
- Use RUT as fallback source when Certificado de Existencia lacks contador/revisor fiscal data
- Support Revisor Fiscal Suplente from RUT as an additional validation source
- Track data source (Certificado de Existencia vs RUT) in validation descriptions
- Update `documents_compared` to include 'rut' when RUT data is used
- Handle cedula validation for Revisor Fiscal Suplente

### 3. Unit Tests (`test_fraud_detection_service.py`)
Added 6 new test cases:
- `test_contador_revisor_fiscal_from_rut_when_cert_empty` - Validates RUT fallback when cert is empty
- `test_contador_revisor_fiscal_cert_takes_precedence_over_rut` - Confirms cert takes precedence
- `test_contador_revisor_fiscal_rut_revisor_suplente_validation` - Tests suplente validation
- `test_contador_revisor_fiscal_rut_revisor_principal_fallback` - Tests principal fallback
- `test_contador_revisor_fiscal_rut_suplente_cedula_mismatch` - Tests cedula mismatch for suplente

## Discrepancies Found

**None** - The plan matched reality. No discrepancies were found between the plan and the actual codebase structure.

## Validation Results

All validation commands passed:

1. **Python Syntax Check**: Both modified files compile without errors
2. **Backend Linting**: `ruff check src/` - All checks passed
3. **Backend Tests**: 35 tests passed (including 6 new tests)
4. **Frontend Linting**: 4 warnings (pre-existing, not related to this change)
5. **TypeScript Check**: Passed
6. **Frontend Build**: Successful

## Files Changed

```
backend/src/core/servicios/risk/cross_validation_service.py     | 130 ++++++++++----
backend/src/core/servicios/risk/document_extraction_service.py  |   9 +-
backend/tests/test_fraud_detection_service.py                   | 195 +++++++++++++++++++++
3 files changed, 303 insertions(+), 31 deletions(-)
```

## Key Implementation Details

### Fallback Logic
The implementation follows this priority:
1. **Certificado de Existencia** (primary source)
2. **RUT** (fallback source if Certificado is empty)

### Source Tracking
Validation result descriptions now indicate the data source:
- "Firmante 'JUAN PEREZ' verificado como contador registrado (fuente: RUT)"
- "Firmante 'MARIA LOPEZ' verificado como revisor fiscal registrado (fuente: Certificado de Existencia)"

### Revisor Fiscal Suplente
The RUT document contains Revisor Fiscal Suplente information which is now considered in validation. This is particularly useful for cases where the suplente signs financial statements.

## Testing

All new tests verify:
- RUT extraction is used when Certificado is empty
- Certificado takes precedence when both have data
- Revisor Fiscal Suplente from RUT is validated
- Cedula mismatches produce appropriate severity levels
- Source attribution in validation messages is correct
