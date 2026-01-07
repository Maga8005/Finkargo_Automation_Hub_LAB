# Implementation Report: Tesorería concept_type COSTOS_FIJOS Aggregation for Colombia

**Date:** 2025-12-05
**Module:** Tesorería (Treasury)
**Feature:** Update Colombia concept_type rules for template output

## Summary

Implemented the new business rule for Colombia payment template output where cost-related columns are now aggregated into a single `COSTOS_FIJOS` concept instead of outputting individual rows for each cost type.

## Changes Made

### 1. Updated ConceptType Enum (`backend/src/interface/tesoreria_dtos.py`)
- Added `COSTOS_FIJOS = "COSTOS_FIJOS"` to the Colombia-specific concepts section of the enum
- This ensures type consistency across the application

### 2. Modified `_process_concepts` Method (`backend/src/core/servicios/payment_template_service.py`)
- Implemented country-aware concept processing:
  - **Colombia**: Now processes only `CAPITAL` and `SEGUROS` as individual concepts
  - **Colombia**: Aggregates the following columns into a single `COSTOS_FIJOS` row:
    - 4X1000 (4x1000)
    - FONDO_GARANTIAS (Fondo de garantías)
    - IVA_FONDO_GARANTIAS (IVA Fondo de garantías)
    - SERVICIO_ORIGINACION (Servicio de originación)
    - SERVICIO_GIRO (Servicio de giro + IVA)
    - COSTOS_ADICIONALES (Costos adicionales)
  - **México**: Maintains existing behavior with individual concept processing

### 3. AR Account Mapping (Verified, No Changes Needed)
- `COLOMBIA_AR_ACCOUNTS` already has `"COSTOS_FIJOS": 258`
- `COLOMBIA_NT_AR_ACCOUNTS` already has `"COSTOS_FIJOS": 310`

## Business Rule Implementation

| Output concept_type | Source Columns |
|---------------------|----------------|
| `CAPITAL` | Capital column (standalone) |
| `COSTOS_FIJOS` | Sum of: 4X1000, Fondo de garantía, IVA Fondo de Garantía, Servicio de Originación, Servicios de Giro + IVA, Costos Adicionales |
| `SEGUROS` | Seguro + IVA column (standalone) |
| `INTERESES` | Intereses Corrientes - Descuento - Condonación (unchanged) |
| `MORATORIOS` | Sum of PAR columns - Sum of Condonación columns (unchanged) |

## Files Changed

```
backend/src/core/servicios/payment_template_service.py | 53 +++++++++++++++------
backend/src/interface/tesoreria_dtos.py                |  1 +
```

**Total: 2 files changed, ~30 insertions, ~15 deletions**

## Validation Results

- **Backend Tests**: Passed (8 tests passed, 6 pre-existing fixture errors in Google Drive tests unrelated to this change)
- **Backend Linting**: Ruff not installed (skipped)
- **Frontend TypeScript Check**: Passed
- **Frontend Lint**: Pre-existing errors (4 errors in unrelated files: FKExcelUploaderCO.tsx and FKFinanceHistory.tsx)
- **Frontend Build**: Pre-existing error in FKFinanceHistory.tsx (unused variable)

## Notes

1. México processing remains unchanged - each concept is processed individually
2. The COSTOS_FIJOS row uses the summed amount from all component columns
3. AR account lookup correctly uses COSTOS_FIJOS (258 for non-NT, 310 for NT operations)
4. Pre-existing test and lint errors are unrelated to this implementation
