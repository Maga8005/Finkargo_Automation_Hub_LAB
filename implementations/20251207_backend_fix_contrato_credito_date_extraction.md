# Fix Contrato de Crédito Date Extraction

**Date:** December 7, 2025
**Module:** Backend - Cotización Parser Service
**Status:** Complete

## Summary

Fixed the Solicitud de Desembolso feature to correctly extract the "fecha_contrato_credito" (credit contract date) from Cotización PDFs. Previously, both `fecha_cotizacion` and `fecha_contrato_credito` were returning the same date because the parser was finding the first date in the document for both fields.

## Problem

The Cotización PDF first paragraph contains two different dates:
1. **Fecha de Cotización de Desembolso**: "10 de noviembre de 2025" (quote date)
2. **Contrato de Crédito en Pesos de fecha**: "6 de noviembre de 2025" (credit contract date)

The old implementation used `_parse_spanish_date` for both, which just returned the first date found in the document.

## Solution

Implemented context-aware date extraction:

1. **`_extract_fecha_contrato_credito`**: Now searches for the specific pattern "Contrato de Crédito en Pesos de fecha" followed by a Spanish date, extracting only the date associated with the credit contract.

2. **`_extract_fecha_cotizacion`**: Now searches for "Fecha de Cotización de Desembolso" followed by a Spanish date, extracting only the quote date.

3. **New helper method `_parse_spanish_date_string`**: Parses a Spanish date string (e.g., "6 de noviembre de 2025") directly to ISO format ("2025-11-06").

4. **Fallback mechanism**: If the specific pattern isn't found, falls back to the generic `_parse_spanish_date` method for backward compatibility.

## Files Changed

```
 backend/src/core/servicios/cotizacion_parser_service.py    |  82 ++++++++++++++++++++-
 backend/tests/test_cotizacion_parser_service.py            |  71 ++++++++++++++++++
 2 files changed, 149 insertions(+), 4 deletions(-)
```

## Code Changes

### `cotizacion_parser_service.py`

- Updated `_extract_fecha_cotizacion()` to search for "Fecha de Cotización de Desembolso:" pattern
- Updated `_extract_fecha_contrato_credito()` to search for "Contrato de Crédito en Pesos de fecha" pattern
- Added new helper method `_parse_spanish_date_string()` for direct date string parsing
- Both methods have fallback to generic date parsing for backward compatibility

### `test_cotizacion_parser_service.py`

- Updated `test_parse_cotizacion_all_fields` to assert `fecha_contrato_credito == "2025-11-06"`
- Added `test_parse_cotizacion_fecha_contrato_credito` - verifies correct extraction
- Added `test_fecha_contrato_credito_different_from_cotizacion` - verifies dates are different
- Added `test_parse_spanish_date_string` - unit tests for the new helper method

## Validation Results

- **Backend Tests**: 39/39 passed (15 cotización parser tests)
- **Backend Linting**: All checks passed
- **Frontend Linting**: Passed
- **TypeScript Check**: Passed
- **Frontend Build**: Successful

## Test Output

```
tests/test_cotizacion_parser_service.py::test_parse_cotizacion_all_fields PASSED
tests/test_cotizacion_parser_service.py::test_parse_cotizacion_fecha_contrato_credito PASSED
tests/test_cotizacion_parser_service.py::test_fecha_contrato_credito_different_from_cotizacion PASSED
tests/test_cotizacion_parser_service.py::test_parse_spanish_date_string PASSED
...
15 passed
```

## Expected Behavior After Fix

When parsing the example Cotización PDF:
- `fecha_cotizacion`: "2025-11-10" (from "Fecha de Cotización de Desembolso: 10 de noviembre de 2025")
- `fecha_contrato_credito`: "2025-11-06" (from "Contrato de Crédito en Pesos de fecha 6 de noviembre de 2025")

The Solicitud de Desembolso document will now correctly display the credit contract date instead of incorrectly using the cotización date.
