# Fix Exchange Rate Column Mapping

**Date**: 2025-12-01
**Module**: Treasury / Payment Templates
**Type**: Bug Fix

## Summary

Fixed the exchange rate field (`exchangerate`) returning blank in the generated `Aplicacion_Pagos_Co` Excel file by correcting the column name mapping.

## Problem

The exchange rate value was not being populated because of a mismatch between:
- **Code mapping**: `"Tasa de cambio FK/en línea"` (missing "de")
- **Actual column name**: `"Tasa de cambio de FK/en línea"` (with "de")

This caused the column lookup to fail, resulting in `None` values for the exchange rate.

## Changes Made

- Updated Colombia exchange rate column mapping in `payment_catalogs.py` (line 109):
  - From: `"Tasa de cambio FK/en línea"`
  - To: `"Tasa de cambio de FK/en línea"`

- Updated México exchange rate column mapping in `payment_catalogs.py` (line 157):
  - From: `"Tasa de cambio FK/en línea"`
  - To: `"Tasa de cambio de FK/en línea"`

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py | 2 lines changed
```

## Validation

- ✅ Backend tests: 8 passed
- ✅ Backend linting (ruff): All checks passed
- ✅ Frontend linting: Pre-existing issues only (not related to this change)
- ✅ TypeScript type check: Passed
- ✅ Frontend build: Successful
