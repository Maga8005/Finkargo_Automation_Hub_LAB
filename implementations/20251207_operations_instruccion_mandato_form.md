# Implementation Report: Instrucción de Mandato (IM) PDF Upload Form

**Date:** 2025-12-07
**Module:** Operations / Paga Local Colombia
**Feature:** Mandato (IM) PDF Upload Form with Cotización and Bank Certificate extraction

## Summary

Implemented a specialized frontend form `FKInstruccionMandatoForm.tsx` for generating Instrucción de Mandato documents in the Paga Local Colombia workflow. The form enables:

- Client search and selection
- Cotización PDF upload with automatic data extraction
- Bank Certificate PDF upload for creditor bank account information
- Review and edit extracted data before document generation
- Support for multiple creditors (up to 3 per document)

## Work Completed

- **Created `FKInstruccionMandatoForm.tsx`** (703 lines): New specialized form component following the existing `FKSolicitudDesembolsoRequest.tsx` pattern with:
  - Client search via NIT or name
  - Cotización PDF upload and parsing (max 5MB, PDF only)
  - Editable extracted data (numero_cotizacion, fecha_contrato_mandato, monto_total)
  - Creditor management section with Bank Certificate upload per creditor
  - Bank account fields: razón social, NIT, banco, tipo_cuenta (dropdown), número_cuenta
  - Form validation and error handling
  - Success state after document generation

- **Updated `FKPagaLocalCODocumentosOperacion.tsx`**: Integrated the new form to replace the generic form for `pl_co_mandato_im` contract type

- **Created E2E test file** `test_instruccion_mandato_form.md` (131 lines): Comprehensive test covering:
  - Client search flow
  - Cotización upload and extraction
  - Bank Certificate upload and extraction
  - Document generation
  - Form reset functionality

## Discrepancies Found and Resolved

**None.** The plan was accurate:
- All TypeScript types existed as documented (`BankCertificateData`, `AcreedorGastosNacionales`, `InstruccionMandatoRequest`, `InstruccionMandatoFormData`, `CotizacionData`)
- All service methods existed as documented (`parseCotizacionForMandato()`, `parseBankCertificate()`, `generateInstruccionMandato()`)
- The parent component structure matched expectations

## Validation Results

| Command | Status |
|---------|--------|
| `cd frontend && npm run lint` | ✅ Passed |
| `cd frontend && npx tsc --noEmit` | ✅ Passed |
| `cd frontend && npm run build` | ✅ Passed |
| `cd backend && python -m pytest tests/` | ✅ 47 tests passed |
| `cd backend && ruff check src/` | ✅ All checks passed |

## Files Changed

```
.claude/commands/e2e/test_instruccion_mandato_form.md                |  131 +++++++ (new)
frontend/src/components/forms/FKInstruccionMandatoForm.tsx           |  703 +++++++ (new)
frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx   |    5 +- (modified)
```

**Total:** 839 lines added, 1 line modified

## Architecture Notes

The implementation follows the existing patterns in the codebase:

1. **Component Structure**: Follows `FKSolicitudDesembolsoRequest.tsx` pattern with numbered sections
2. **State Management**: Uses React `useState` hooks for form state
3. **Service Layer**: Calls existing `operationsService` methods (no direct API calls)
4. **Error Handling**: Displays user-friendly error messages with dismissible alerts
5. **Validation**: Client-side validation for required fields before submission
6. **UI Components**: Uses Material-UI components consistent with the design system

## Next Steps

1. Execute E2E test to validate complete workflow: `/test_e2e .claude/commands/e2e/test_instruccion_mandato_form.md`
2. Manual testing with real Cotización and Bank Certificate PDFs
3. Future enhancement: Implement specialized form for `pl_co_dian_mandato_im` (DIAN Mandato) with pre-populated static values
