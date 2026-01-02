# Patch: Fix PA Account Catalog Column Mapping for "Cuenta Fk"

## Metadata
adw_id: `b13fe784`
review_change_request: `I get the message "No se encontraron coincidencias. Cuentas en archivo: 295, Cuentas en catálogo: 65. Verifique que el catálogo contenga las cuentas correctas." However, one of the accounts that maps to the PA catalog is 11100530. It is in row 211 of the csv. It maps to PA account 13020500101001`

## Issue Summary
**Original Spec:** specs/issue-53-adw-550a54d1-sdlc_planner-pa-report-classification.md
**Issue:** The PA account catalog Excel file uses column name "Cuenta Fk" but the `_get_catalog_column_mapping` function in `pa_rules_service.py` doesn't recognize this column name variation. When the catalog is uploaded, it fails silently or returns "Columnas no válidas" error, resulting in an empty catalog. When processing the CSV, no accounts match because the catalog is empty.

**Root Cause Analysis:**
1. The Excel catalog file `Catálogo de Cuenta.xlsx` has columns: `Cuenta Fk`, `CUENTA AUXILIAR`, `Homologacion cuenta`, `Homologacion Nombre cuenta`
2. After lowercase normalization: `cuenta fk`, `cuenta auxiliar`, `homologacion cuenta`, `homologacion nombre cuenta`
3. The current mapping logic checks for:
   - `"cuenta" in col_lower and ("finkargo" in col_lower or "netsuite" in col_lower or "linea" in col_lower)` - FAILS (no "finkargo", "netsuite", or "linea" in "cuenta fk")
   - `col_lower in ["cuenta_finkargo", "cuenta finkargo", "cuenta"]` - FAILS ("cuenta fk" not in list)
4. Since the cuenta_finkargo column isn't mapped, the catalog upload fails, leaving an empty catalog
5. When processing the CSV, 0 matches are found because catalog is empty

**Solution:** Update `_get_catalog_column_mapping` in `pa_rules_service.py` to recognize additional column name variations including "cuenta fk", "fk", and partial matches on "fk".

## Files to Modify

1. `backend/src/core/servicios/pa_rules_service.py` - Update `_get_catalog_column_mapping` method
2. `backend/tests/test_pa_report_service.py` - Add test for "Cuenta Fk" column mapping

## Implementation Steps

### Step 1: Update column mapping to recognize "Cuenta Fk"

In `backend/src/core/servicios/pa_rules_service.py`, modify `_get_catalog_column_mapping` method:

**Current code (lines 129-137):**
```python
# Cuenta Finkargo variations
for col in columns:
    col_lower = col.lower()
    if "cuenta" in col_lower and ("finkargo" in col_lower or "netsuite" in col_lower or "linea" in col_lower):
        mapping[col] = "cuenta_finkargo"
        break
    if col_lower in ["cuenta_finkargo", "cuenta finkargo", "cuenta"]:
        mapping[col] = "cuenta_finkargo"
        break
```

**Updated code:**
```python
# Cuenta Finkargo variations
for col in columns:
    col_lower = col.lower()
    # Match variations: cuenta_finkargo, cuenta finkargo, cuenta fk, cuenta netsuite, cuenta linea
    if "cuenta" in col_lower and ("finkargo" in col_lower or "netsuite" in col_lower or "linea" in col_lower or col_lower.endswith(" fk") or col_lower == "cuenta fk"):
        mapping[col] = "cuenta_finkargo"
        break
    if col_lower in ["cuenta_finkargo", "cuenta finkargo", "cuenta fk", "cuenta"]:
        mapping[col] = "cuenta_finkargo"
        break
```

### Step 2: Add test for new column mapping

In `backend/tests/test_pa_report_service.py`, add a new test class to validate the column mapping:

```python
class TestPARulesServiceColumnMapping:
    """Tests for PA rules service column mapping"""

    def test_catalog_column_mapping_cuenta_fk(self):
        """Test that 'Cuenta Fk' column is recognized"""
        from src.core.servicios.pa_rules_service import PARulesService
        from unittest.mock import MagicMock

        service = PARulesService(MagicMock())
        columns = ['cuenta fk', 'cuenta auxiliar', 'homologacion cuenta', 'homologacion nombre cuenta']

        mapping = service._get_catalog_column_mapping(columns)

        assert mapping is not None
        assert 'cuenta fk' in mapping
        assert mapping['cuenta fk'] == 'cuenta_finkargo'
        assert mapping['homologacion cuenta'] == 'cuenta_homologacion'
        assert mapping['homologacion nombre cuenta'] == 'nombre_homologacion'
```

## Validation

Execute the following commands to validate the patch:

1. **Run unit tests:**
```bash
cd backend && python -m pytest tests/test_pa_report_service.py -v
```

2. **Verify column mapping logic:**
```bash
python3 -c "
columns = ['cuenta fk', 'cuenta auxiliar', 'homologacion cuenta', 'homologacion nombre cuenta']
for col in columns:
    col_lower = col.lower()
    if 'cuenta' in col_lower and ('finkargo' in col_lower or 'netsuite' in col_lower or 'linea' in col_lower or col_lower.endswith(' fk') or col_lower == 'cuenta fk'):
        print(f'MATCH: {col} -> cuenta_finkargo')
        break
    if col_lower in ['cuenta_finkargo', 'cuenta finkargo', 'cuenta fk', 'cuenta']:
        print(f'MATCH: {col} -> cuenta_finkargo')
        break
"
```

3. **Test full flow (manual):**
   - Upload the PA account catalog Excel file
   - Verify 65 entries are uploaded (not 0)
   - Upload the MovimientoDetallado CSV
   - Verify matches are found (not "No se encontraron coincidencias")

4. **Run static analysis:**
```bash
cd backend && python -m ruff check src/core/servicios/pa_rules_service.py
```

## Patch Scope
**Lines of code to change:** ~5 lines (2 condition updates + 1 list item addition)
**Risk level:** low
**Testing required:** Unit test for column mapping, integration test for catalog upload
