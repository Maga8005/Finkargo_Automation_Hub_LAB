# Chore: Fix Moratorios Column Mapping for Colombia

## Chore Description

The `concept_type` "MORATORIOS" is not appearing in the output file even though the input Excel file contains records with balances in the corresponding moratorios columns. This is caused by a **mismatch between the column mappings in the code and the actual column names in the Excel file**.

**Root Cause Analysis:**

The current code in `payment_catalogs.py` defines these moratorios column mappings:
```python
"INTERESES_MORA_PAR_30": "Intereses de Mora PAR 30",
"INTERESES_MORA_PAR_60": "Intereses de Mora PAR 60",
"INTERESES_MORA_PAR_90": "Intereses de Mora PAR 90",
"INTERESES_MORA_PAR_120": "Intereses de Mora PAR 120+",
```

But the **actual Excel file** (`Historial_de_pagos_2025-01-01_2025-12-31.xlsx`) has these column names:
- `Intereses de Mora (Tasa corriente) PAR 60` (1,598 non-zero records)
- `Intereses de Mora (Tasa restante de mora) PAR 60` (1,383 non-zero records)
- `Intereses de Mora (Tasa corriente) PAR 61` (201 non-zero records)
- `Intereses de Mora (Tasa restante de mora) PAR 61` (179 non-zero records)

Similarly, the condonación (forgiveness) columns also have different names:
- **Code expects**: `Condonación Mora 30`, `Condonación Mora 60`, etc.
- **Excel has**: `Condonación intereses de mora (Tasa corriente) Par 60`, `Condonación intereses de mora (Tasa restante de mora) Par 60`, etc.

Since the column names don't match, the `get_numeric_value()` function returns 0.0 for all moratorios columns, resulting in no MORATORIOS rows in the output.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** - Contains the `COLOMBIA_CONCEPT_COLUMNS` dictionary with the incorrect column mappings. This is where the column names need to be updated to match the actual Excel file structure.

- **`backend/src/core/servicios/payment_template_service.py`** - Contains the `_process_concepts` method that calculates MORATORIOS by summing PAR columns and subtracting condonaciones. The logic may need adjustment to handle the new column structure (PAR 60/61 with Tasa corriente/Tasa restante).

### Files for Reference (Read-Only)
- **`Example Files for Reqs/Historial_de_pagos_2025-01-01_2025-12-31.xlsx`** - The input file with actual column names for verification.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update COLOMBIA_CONCEPT_COLUMNS Moratorios Mappings

Update `backend/src/core/servicios/catalogs/payment_catalogs.py` to use the correct column names:

- Remove the old mappings:
  - `"INTERESES_MORA_PAR_30"`: Not present in Excel
  - `"INTERESES_MORA_PAR_60"`: Wrong format
  - `"INTERESES_MORA_PAR_90"`: Not present in Excel
  - `"INTERESES_MORA_PAR_120"`: Not present in Excel

- Add new mappings for the actual Excel columns:
  - `"INTERESES_MORA_TASA_CORRIENTE_PAR_60"`: "Intereses de Mora (Tasa corriente) PAR 60"
  - `"INTERESES_MORA_TASA_RESTANTE_PAR_60"`: "Intereses de Mora (Tasa restante de mora) PAR 60"
  - `"INTERESES_MORA_TASA_CORRIENTE_PAR_61"`: "Intereses de Mora (Tasa corriente) PAR 61"
  - `"INTERESES_MORA_TASA_RESTANTE_PAR_61"`: "Intereses de Mora (Tasa restante de mora) PAR 61"

### Step 2: Update Condonación Mora Column Mappings

Update `backend/src/core/servicios/catalogs/payment_catalogs.py` to fix condonación column names:

- Remove old mappings:
  - `"CONDONACION_MORA_30"`, `"CONDONACION_MORA_60"`, `"CONDONACION_MORA_90"`, `"CONDONACION_MORA_120"`

- Add new mappings:
  - `"CONDONACION_MORA_TASA_CORRIENTE_PAR_60"`: "Condonación intereses de mora (Tasa corriente) Par 60"
  - `"CONDONACION_MORA_TASA_RESTANTE_PAR_60"`: "Condonación intereses de mora (Tasa restante de mora) Par 60"
  - `"CONDONACION_MORA_TASA_CORRIENTE_PAR_61"`: "Condonación intereses de mora (Tasa corriente) Par 61"
  - `"CONDONACION_MORA_TASA_RESTANTE_PAR_61"`: "Condonación intereses de mora (Tasa restante de mora) Par 61"

### Step 3: Update _process_concepts Method for New Moratorios Structure

Modify `backend/src/core/servicios/payment_template_service.py` in the `_process_concepts` method:

- Update the MORATORIOS calculation to use the new column keys:
  ```python
  # Calculate MORATORIOS (sum of PAR 60/61 columns minus condonaciones)
  mora_tasa_corriente_60 = get_numeric_value(
      concept_columns.get("INTERESES_MORA_TASA_CORRIENTE_PAR_60", "")
  )
  mora_tasa_restante_60 = get_numeric_value(
      concept_columns.get("INTERESES_MORA_TASA_RESTANTE_PAR_60", "")
  )
  mora_tasa_corriente_61 = get_numeric_value(
      concept_columns.get("INTERESES_MORA_TASA_CORRIENTE_PAR_61", "")
  )
  mora_tasa_restante_61 = get_numeric_value(
      concept_columns.get("INTERESES_MORA_TASA_RESTANTE_PAR_61", "")
  )

  cond_mora_tasa_corriente_60 = get_numeric_value(
      concept_columns.get("CONDONACION_MORA_TASA_CORRIENTE_PAR_60", "")
  )
  cond_mora_tasa_restante_60 = get_numeric_value(
      concept_columns.get("CONDONACION_MORA_TASA_RESTANTE_PAR_60", "")
  )
  cond_mora_tasa_corriente_61 = get_numeric_value(
      concept_columns.get("CONDONACION_MORA_TASA_CORRIENTE_PAR_61", "")
  )
  cond_mora_tasa_restante_61 = get_numeric_value(
      concept_columns.get("CONDONACION_MORA_TASA_RESTANTE_PAR_61", "")
  )

  total_mora = (mora_tasa_corriente_60 + mora_tasa_restante_60 +
                mora_tasa_corriente_61 + mora_tasa_restante_61)
  total_cond_mora = (cond_mora_tasa_corriente_60 + cond_mora_tasa_restante_60 +
                    cond_mora_tasa_corriente_61 + cond_mora_tasa_restante_61)
  moratorios_final = total_mora - total_cond_mora
  ```

### Step 4: Test with Example File

- Run a manual test using the example file to verify MORATORIOS rows now appear in output
- Verify the calculation: sum of 4 mora columns minus sum of 4 condonación columns

### Step 5: Run Validation Commands

Execute all validation commands to ensure no regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **Column Structure Difference**: The Excel file uses PAR 60 and PAR 61 (not PAR 30, 60, 90, 120+), and splits each PAR into "Tasa corriente" and "Tasa restante de mora" sub-columns.

2. **Data Volume**: The example file has significant moratorios data:
   - PAR 60 Tasa corriente: 1,598 records, sum = 613,864.79
   - PAR 60 Tasa restante: 1,383 records, sum = 102,778.36
   - PAR 61 Tasa corriente: 201 records, sum = 89,919.47
   - PAR 61 Tasa restante: 179 records, sum = 5,346.71

3. **México Impact**: Check if México uses similar column structure or if this change should be Colombia-specific. The current code processes MORATORIOS for all countries, so México mappings should also be verified.

4. **Backward Compatibility**: This is a bug fix, not a breaking change - the old column names simply don't exist in the input files being used.
