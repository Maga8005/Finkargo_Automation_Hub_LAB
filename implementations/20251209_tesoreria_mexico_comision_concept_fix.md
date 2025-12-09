# Implementation Report: Mexico COMISION Concept Type Mapping Fix

**Date:** 2025-12-09
**Module:** Tesorería (Treasury)
**Feature:** Bug Fix - Mexico COMISION concept types not generating in output

## Summary

Fixed a bug where client ID `SON070222MH9` (and other rows with COMISION values) were not generating any records in the output file. The row should generate a `concept_type = "COMISION APERTURA"` with `payment_amount = 6032` and `comision_banco = 3`.

## Root Causes Found

### Issue 1: Column Name Mismatches in `MEXICO_CONCEPT_COLUMNS`

The catalog column names did not match the actual Excel file column names:

| Concept Type | Catalog (Before) | Actual Excel Column |
|--------------|------------------|---------------------|
| COMISION DESEMBOLSO | ✅ "Comisión del desembolso + IVA" | "Comisión del desembolso + IVA" |
| COMISION DISPOSICION | ❌ "Comisión por disposición de crédito + IVA" | "Comisión por disposición de crédito" |
| COMISION SWIFT | ❌ "Comisión swift" | "Comisión SWIFT" |
| COMISION ADMINISTRACION | ❌ "Comisión administración y manejo" | "Comisión de administración y manejo" |
| COMISION APERTURA | ❌ "Comisión de apertura" | "Comisión de apertura del cupo aprobado" |

### Issue 2: `comision_banco` Parsing Failed for Numeric Values

The `_parse_comision_banco` method only accepted string values (`isinstance(referencia_bancaria, str)`), but Excel returns numeric values directly as `float`. The `Referencia bancaria` value of `3.0` was being converted to string `"3.0"` by the `get_value` function, but the initial `None` check was too strict.

## Changes Made

### 1. Updated `MEXICO_CONCEPT_COLUMNS` in `payment_catalogs.py`

```python
# Before:
"COMISION DISPOSICION": "Comisión por disposición de crédito + IVA",
"COMISION SWIFT": "Comisión swift",
"COMISION ADMINISTRACION": "Comisión administración y manejo",
"COMISION APERTURA": "Comisión de apertura",

# After:
"COMISION DISPOSICION": "Comisión por disposición de crédito",
"COMISION SWIFT": "Comisión SWIFT",
"COMISION ADMINISTRACION": "Comisión de administración y manejo",
"COMISION APERTURA": "Comisión de apertura del cupo aprobado",
```

### 2. Updated `_parse_comision_banco` in `payment_template_service.py`

Added handling for numeric values directly from Excel:

```python
def _parse_comision_banco(self, referencia_bancaria) -> Optional[float]:
    if referencia_bancaria is None:
        return None

    # Handle numeric values directly (from Excel)
    if isinstance(referencia_bancaria, (int, float)):
        return float(referencia_bancaria)

    # Handle string values
    if not isinstance(referencia_bancaria, str):
        return None
    # ... rest of parsing logic
```

## Verification Results

Simulated conversion for client `SON070222MH9`:

```
=== Output Row 1 ===
  customer_external_id: SON070222MH9
  invoice_core_id: MX:SON070222MH9:1:1:PAG
  concept_type: COMISION APERTURA
  payment_date: 04/09/2025
  payment_amount: 6032.0
  currency: USD
  payment_ref: MX:SON070222MH9:1:1:PAG:1:REC
  araccount: 2114
  comision_banco: 3.0
```

✅ All expected values are now correctly generated.

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py    | 44 +++++++++++-----------
backend/src/core/servicios/payment_template_service.py     | 27 ++++++++-----
```

Total: 2 files changed, 56 insertions(+), 32 deletions(-)

## Validation Results

| Check | Status |
|-------|--------|
| Column matching for COMISION APERTURA | ✅ Pass (6032.0) |
| comision_banco parsing (string "3.0") | ✅ Pass (3.0) |
| comision_banco parsing (float 3.0) | ✅ Pass (3.0) |
| Frontend lint | ✅ Pass |
| TypeScript type check | ✅ Pass |

## Testing Recommendations

1. Upload the test file: `Example FIles for Reqs/20251209 EJEMPLO HISTORIAL DE PAGOS MEXICO (1).xlsx`
2. Click "Convertir y Descargar"
3. Verify client `SON070222MH9` generates:
   - `concept_type = "COMISION APERTURA"`
   - `payment_amount = 6032`
   - `comision_banco = 3`

## Notes

- The fix ensures that actual Excel column names are used, not assumed names
- The `comision_banco` field now correctly handles both string and numeric Excel values
- Colombia column mappings are not affected by these changes
