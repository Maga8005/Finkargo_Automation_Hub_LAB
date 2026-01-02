# Patch: Fix Movements CSV Column Mapping for Account Number

## Metadata
adw_id: `b13fe784`
review_change_request: `CSV column "Cuenta (línea): Número" not being matched for PA account lookup. Error: "No se encontraron coincidencias. Cuentas en archivo: 295, Cuentas en catálogo: 65."`

## Issue Summary
**Original Spec:** specs/issue-69-adw-b13fe784-sdlc_planner-pa-accounts-csv-semicolon-delimiter.md
**Issue:** The movements CSV file has column names that don't exactly match the expected `SOURCE_COLUMN_MAPPING` in `pa_report_service.py`. The prior patch fixed the catalog column mapping, but the movements CSV parsing is still failing because the column name matching is too strict. Key discrepancies include:
1. `Tipo  de Transacción` (double space) vs expected `Tipo de Transacción` (single space)
2. `Nota` (singular) vs expected `Notas` (plural)
3. Potential whitespace/encoding differences in column names

**Solution:** Normalize column names before matching by:
1. Collapsing multiple spaces to single spaces
2. Trimming whitespace
3. Adding common column name variations to the mapping

## Files to Modify

1. `backend/src/core/servicios/pa_report_service.py` - Update `SOURCE_COLUMN_MAPPING` and add column normalization logic in `_rename_columns` and `_validate_columns`

## Implementation Steps

### Step 1: Add column name normalization helper
- Add a `_normalize_column_name` method that:
  - Strips leading/trailing whitespace
  - Collapses multiple spaces to single space
  - Returns the normalized column name

### Step 2: Update SOURCE_COLUMN_MAPPING with column variations
- Add alternative column names for common variations:
  - `"Tipo  de Transacción"` (double space variant)
  - `"Nota"` (singular variant of Notas)
  - `"Mensaje"` (alternative to Notas)

### Step 3: Update _validate_columns to use normalized comparison
- Normalize both the required column names and actual column names before comparison
- This handles whitespace variations automatically

### Step 4: Update _rename_columns to use normalized matching
- Normalize column names during the matching process
- Match normalized actual columns against normalized expected columns

### Step 5: Add debug logging for column name diagnosis
- Log actual column names vs expected to help diagnose future mismatches

## Validation

Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check:**
```bash
cd backend && python -m py_compile src/core/servicios/pa_report_service.py
```

2. **Backend Linting:**
```bash
cd backend && ruff check src/core/servicios/pa_report_service.py
```

3. **Run PA Report Service Tests:**
```bash
cd backend && python -m pytest tests/test_pa_report_service.py -v
```

4. **All Backend Tests:**
```bash
cd backend && python -m pytest -v --tb=short
```

5. **Frontend Build (ensure no regressions):**
```bash
cd frontend && npm run build
```

## Patch Scope
**Lines of code to change:** ~25 lines (1 new helper method + updates to existing methods)
**Risk level:** low
**Testing required:** Unit tests for column normalization, integration test with actual CSV file
