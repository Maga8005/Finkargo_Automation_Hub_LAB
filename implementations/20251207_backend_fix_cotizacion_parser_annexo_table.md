# Implementation Report: Fix Cotización Parser Anexo Table Extraction

**Date**: 2025-12-07
**Module**: Backend - core/servicios
**Type**: Bug Fix

## Summary

Fixed the Cotización PDF parser that was failing to extract Anexo I table data, causing a validation error: `monto_total must be greater than 0`.

## Problem

When uploading a Cotización de Desembolso PDF in the Solicitud de Desembolso feature, the system returned:
```
Error al extraer datos del PDF: Error parsing Cotización document: monto_total must be greater than 0
```

The root cause was three issues in `cotizacion_parser_service.py`:

1. **Wrong "Anexo I" match position**: The parser searched for the first occurrence of "Anexo I" which was in the body text (page 1), missing the actual table on page 3.

2. **Multi-line table parsing failure**: PyMuPDF extracts table cells on separate lines, but the regex expected all 3 columns on a single line.

3. **Colombian currency format**: The parser didn't properly handle the COP format with periods as thousands separators and commas as decimal separators.

## Solution

### Changes Made

1. **New table detection approach**: Instead of searching for "ANEXO I" (which appears as a footer at the end of page 3), the parser now searches for the table header row "Acreedor del Gasto Nacional de Importación" to find the table start.

2. **Multi-line parsing**: Implemented line-by-line sequential parsing that processes table rows in groups of 3 lines:
   - Line 1: Acreedor name (text with letters)
   - Line 2: Instrument number (digits only)
   - Line 3: COP amount

3. **New `_parse_cop_amount()` helper method**: Properly parses Colombian peso format:
   - Strips "COP" prefix
   - Removes whitespace padding
   - Converts periods (thousands separators) to nothing
   - Converts comma (decimal separator) to period

4. **Empty row handling**: Skips placeholder rows where acreedor is "0" and monto is "-".

## Files Changed

| File | Changes |
|------|---------|
| `backend/src/core/servicios/cotizacion_parser_service.py` | Added `_parse_cop_amount()` method, rewrote `_extract_anexo_table()` for multi-line parsing |
| `backend/tests/test_cotizacion_parser_service.py` | New unit test file with 12 test cases |
| `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` | New E2E test file |
| `specs/issue-0-adw-0-sdlc_planner-fix-cotizacion-parser-annexo-table.md` | Bug fix plan |

## Git Diff Stats

```
backend/src/core/servicios/cotizacion_parser_service.py | 182 ++++++++++++++++-----
 2 files changed, 146 insertions(+), 39 deletions(-)
```

## Test Results

### Unit Tests (12 tests - all passing)
- `test_parse_cotizacion_all_fields` - Verifies numero_cotizacion and fecha extraction
- `test_parse_cotizacion_anexo_items_count` - Verifies exactly 3 items extracted
- `test_parse_cotizacion_anexo_items_values` - Verifies each item's acreedor, numero, monto
- `test_parse_cotizacion_monto_total` - Verifies total = 739,860 COP
- `test_parse_cop_amount_*` - 5 tests for currency parsing
- `test_parse_invalid_pdf_raises_error` - Error handling
- `test_parse_empty_pdf_raises_error` - Error handling
- `test_cotizacion_data_model_has_required_fields` - Model validation

### Validation Commands (all passing)
- ✅ `python -m pytest tests/` - 19 tests passed
- ✅ `ruff check src/` - All checks passed
- ✅ `npm run lint` - No errors
- ✅ `npx tsc --noEmit` - No type errors
- ✅ `npm run build` - Build successful

## Expected Values After Fix

For the test PDF (`Quotation CO90043638912DOM SAFETY PUERTO 10112025.pdf`):

| Field | Value |
|-------|-------|
| numero_cotizacion | CO:900436389:1:2:DOM |
| fecha_cotizacion | 2025-11-10 |
| anexo_items count | 3 |
| Item 1 | Entidad de pago de Impuestos \| 1003887257 \| 407,001.00 |
| Item 2 | Entidad de pago de Impuestos \| 1003887254 \| 290,000.00 |
| Item 3 | Entidad de pago de Impuestos \| 1003887815 \| 42,859.00 |
| monto_total | 739,860.00 COP |

## Notes

- The fix is backward compatible - no API changes required
- The parser now correctly handles the specific PDF structure where "ANEXO I" appears as a footer at the bottom of page 3 rather than a header above the table
- Colombian currency format (periods for thousands, commas for decimals) is now properly handled
