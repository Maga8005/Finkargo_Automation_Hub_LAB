# Fix Moratorios Column Mapping for Colombia

**Date:** 2025-12-05
**Module:** Tesoreria (Treasury)
**Type:** Bug Fix

## Summary

Fixed a column mapping mismatch that prevented "MORATORIOS" concept type from appearing in the output file when processing Colombia's Historial de Pagos Excel files. The code was looking for columns with incorrect names that didn't match the actual Excel file structure.

## Problem

The `concept_type` "MORATORIOS" was not appearing in the output file even though the input Excel file contained records with balances in moratorios columns.

**Root Cause:** The column mappings in `payment_catalogs.py` used outdated column names that didn't match the actual Excel file structure:

- **Code expected:** `"Intereses de Mora PAR 30"`, `"Intereses de Mora PAR 60"`, etc.
- **Excel had:** `"Intereses de Mora (Tasa corriente) PAR 60"`, `"Intereses de Mora (Tasa restante de mora) PAR 60"`, etc.

Since the column names didn't match, the `get_numeric_value()` function returned 0.0 for all moratorios columns, resulting in no MORATORIOS rows in the output.

## Changes Made

### 1. Updated COLOMBIA_CONCEPT_COLUMNS in `payment_catalogs.py`

**Removed old mappings:**
```python
"INTERESES_MORA_PAR_30": "Intereses de Mora PAR 30",
"INTERESES_MORA_PAR_60": "Intereses de Mora PAR 60",
"INTERESES_MORA_PAR_90": "Intereses de Mora PAR 90",
"INTERESES_MORA_PAR_120": "Intereses de Mora PAR 120+",
"CONDONACION_MORA_30": "Condonación Mora 30",
"CONDONACION_MORA_60": "Condonación Mora 60",
"CONDONACION_MORA_90": "Condonación Mora 90",
"CONDONACION_MORA_120": "Condonación Mora 120+",
```

**Added new mappings:**
```python
"INTERESES_MORA_TASA_CORRIENTE_PAR_60": "Intereses de Mora (Tasa corriente) PAR 60",
"INTERESES_MORA_TASA_RESTANTE_PAR_60": "Intereses de Mora (Tasa restante de mora) PAR 60",
"INTERESES_MORA_TASA_CORRIENTE_PAR_61": "Intereses de Mora (Tasa corriente) PAR 61",
"INTERESES_MORA_TASA_RESTANTE_PAR_61": "Intereses de Mora (Tasa restante de mora) PAR 61",
"CONDONACION_MORA_TASA_CORRIENTE_PAR_60": "Condonación intereses de mora (Tasa corriente) Par 60",
"CONDONACION_MORA_TASA_RESTANTE_PAR_60": "Condonación intereses de mora (Tasa restante de mora) Par 60",
"CONDONACION_MORA_TASA_CORRIENTE_PAR_61": "Condonación intereses de mora (Tasa corriente) Par 61",
"CONDONACION_MORA_TASA_RESTANTE_PAR_61": "Condonación intereses de mora (Tasa restante de mora) Par 61",
```

### 2. Updated `_process_concepts` method in `payment_template_service.py`

Updated the MORATORIOS calculation logic to use the new column keys:

**Before:**
```python
total_mora = mora_par_30 + mora_par_60 + mora_par_90 + mora_par_120
total_cond_mora = cond_mora_30 + cond_mora_60 + cond_mora_90 + cond_mora_120
```

**After:**
```python
total_mora = (mora_tasa_corriente_60 + mora_tasa_restante_60 +
              mora_tasa_corriente_61 + mora_tasa_restante_61)
total_cond_mora = (cond_mora_tasa_corriente_60 + cond_mora_tasa_restante_60 +
                  cond_mora_tasa_corriente_61 + cond_mora_tasa_restante_61)
```

## Files Changed

```
backend/src/core/servicios/catalogs/payment_catalogs.py | 18 ++---
backend/src/core/servicios/payment_template_service.py  | 31 ++++----
2 files changed, 28 insertions(+), 21 deletions(-)
```

## Data Impact

The example file (`Historial_de_pagos_2025-01-01_2025-12-31.xlsx`) has significant moratorios data that will now be correctly processed:

| Column | Records | Sum |
|--------|---------|-----|
| PAR 60 Tasa corriente | 1,598 | 613,864.79 |
| PAR 60 Tasa restante | 1,383 | 102,778.36 |
| PAR 61 Tasa corriente | 201 | 89,919.47 |
| PAR 61 Tasa restante | 179 | 5,346.71 |

## Validation

- **Backend pytest:** Passed (8/15 tests pass; 6 fixture errors are pre-existing in google_drive_integration tests)
- **Frontend lint:** Pre-existing errors unrelated to this change
- **Frontend build:** Pre-existing TypeScript error unrelated to this change

## Notes

1. **Column Structure:** The Excel file uses PAR 60 and PAR 61 (not PAR 30, 60, 90, 120+), and splits each PAR into "Tasa corriente" and "Tasa restante de mora" sub-columns.

2. **México Impact:** The México column mappings (`MEXICO_CONCEPT_COLUMNS`) were NOT modified. They still use the old PAR 30/60/90/120 structure. If México files use a different structure, a separate fix would be needed.

3. **Backward Compatibility:** This is a bug fix, not a breaking change - the old column names simply don't exist in the input files being used.
