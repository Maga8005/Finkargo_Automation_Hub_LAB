# Implementation: Fix Solicitud de Desembolso Placeholder Mismatch

**Date:** 2025-12-07
**Module:** Backend - Document Service
**Issue:** Solicitud de Desembolso Word document placeholders not being filled

## Summary

Fixed a bug where the Solicitud de Desembolso Word document generation was not replacing placeholders with actual data. The root cause was a **placeholder key mismatch** between the code and the Word template.

## Problem

When generating a Solicitud de Desembolso document:
- All placeholders remained unfilled (e.g., `[Número de cotización de desembolso]`, `[monto]`, `[día]`)
- The document was unusable for Legal review
- No data substitution was occurring

## Root Cause

The code defined placeholder keys using `UPPERCASE_SNAKE_CASE` format:
```python
'[NUMERO_COTIZACION_DESEMBOLSO]': data.get('numero_cotizacion_desembolso', '')
'[MONTO]': monto_formatted
'[DIAS_PLAZO]': dias_plazo
```

But the Word template used Spanish-language, mixed-case placeholders:
```
[Número de cotización de desembolso]
[monto]
[número de días de plazo]
[día de firma del contrato de crédito]
```

Since string replacement uses exact matching, no replacements occurred.

## Solution

### 1. Updated `_prepare_solicitud_desembolso_replacements()` method
- Changed placeholder keys to match exact template text
- Split dates into components (day, month, year) instead of formatted strings
- Template placeholders now correctly mapped:
  - `[Número de cotización de desembolso]` → quote number
  - `[día]`, `[mes]`, `[•]` → current date components
  - `[día de firma del contrato de crédito]`, etc. → contract date components
  - `[monto]` → formatted amount
  - `[número de días de plazo]` → days number

### 2. Fixed `_populate_anexo_table()` method
- Changed from adding new rows to filling existing placeholder rows
- Template has 10 data rows (rows 2-11) with `[•]` placeholders
- Now fills existing rows and clears unused ones
- Correctly populates TOTAL row (row 12)

### 3. Added debug logging
- Logs data snapshot keys and values
- Logs all placeholder replacements
- Logs replacement counts for debugging

## Files Changed

| File | Changes |
|------|---------|
| `backend/src/core/servicios/document_service.py` | 137 insertions, 65 deletions |
| `backend/tests/test_document_service.py` | New file (7 tests) |
| `.claude/commands/e2e/test_solicitud_desembolso_document_generation.md` | New E2E test file |

## Validation

### Backend Tests
```bash
cd backend && python -m pytest tests/test_document_service.py -v
# Result: 7 passed
```

### All Backend Tests
```bash
cd backend && python -m pytest
# Result: 27 passed
```

### Linting
```bash
cd backend && ruff check src/
# Result: All checks passed!

cd frontend && npm run lint
# Result: No errors

cd frontend && npx tsc --noEmit
# Result: No errors

cd frontend && npm run build
# Result: Built successfully
```

## Test Coverage

New unit tests created:
1. `test_solicitud_desembolso_placeholders_replaced` - Verifies all placeholders are replaced
2. `test_solicitud_desembolso_date_components_replaced` - Verifies date splitting works
3. `test_solicitud_desembolso_anexo_table_populated` - Verifies Anexo I table has data
4. `test_solicitud_desembolso_total_calculated` - Verifies TOTAL row is correct
5. `test_prepare_solicitud_desembolso_replacements` - Verifies replacement dictionary
6. `test_solicitud_desembolso_empty_anexo_items` - Edge case with no items
7. `test_solicitud_desembolso_missing_fecha_contrato` - Edge case with empty date

## Placeholder Reference

| Template Placeholder | Data Source |
|---------------------|-------------|
| `[Número de cotización de desembolso]` | `numero_cotizacion_desembolso` |
| `[día]` | Current day (1-31) |
| `[mes]` | Current month (Spanish) |
| `[•]` | Last digit of year |
| `[día de firma del contrato de crédito]` | Contract date day |
| `[mes de firma del contrato de crédito]` | Contract date month (Spanish) |
| `[ año de firma del contrato de crédito]` | Contract date year |
| `[monto]` | Formatted amount |
| `[número de días de plazo]` | Days number |
