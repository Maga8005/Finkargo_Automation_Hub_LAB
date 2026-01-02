# Patch: Fix PA Classification 'str' object has no attribute 'day' Error

## Metadata
adw_id: `b13fe784`
review_change_request: `The account mapping issue was addressed by implementations/20260101_finance_fix_pa_account_matching.md. However, now when I try to run <Ejecutar Clasificación> I get "'str' object has no attribute 'day'".`

## Issue Summary
**Original Spec:** `implementations/20260101_finance_fix_pa_account_matching.md`
**Issue:** When running "Ejecutar Clasificación" (PA classification step 2), the `_apply_date_logic()` method in `PAClassificationEngine` fails with `AttributeError: 'str' object has no attribute 'day'` because the `fecha` column from the DataFrame is a string, not a `date` object.
**Solution:** Convert the `fecha` string to a `date` object before passing it to the classification engine, handling both string and datetime formats.

## Files to Modify

1. `backend/src/core/servicios/pa_classification_engine.py` - Add date parsing/conversion in `_apply_date_logic()` method

## Implementation Steps

### Step 1: Update `_apply_date_logic()` to Handle String Dates
- Modify the `_apply_date_logic()` method in `PAClassificationEngine` class
- Add date parsing logic at the start of the method to convert string dates to `date` objects
- Handle multiple date formats (ISO format "YYYY-MM-DD", pandas Timestamp, and existing date objects)
- Preserve existing logic for None/empty dates

**Implementation details:**
```python
def _apply_date_logic(
    self,
    fecha: Optional[date],
    subcategoria_base: Optional[str],
    categoria: Optional[str]
) -> Optional[str]:
    """
    Apply date-based subcategoria logic.
    ...
    """
    if not subcategoria_base:
        return None

    if not fecha:
        return subcategoria_base

    # Convert string dates to date objects
    if isinstance(fecha, str):
        try:
            # Handle ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            fecha = datetime.strptime(fecha.split()[0], "%Y-%m-%d").date()
        except (ValueError, AttributeError):
            logger.warning(f"Could not parse date string: {fecha}")
            return subcategoria_base
    elif hasattr(fecha, 'date'):  # Handle pandas Timestamp or datetime
        fecha = fecha.date() if callable(getattr(fecha, 'date', None)) else fecha

    # Check if this category uses date logic
    date_logic_categories = ["Diferencia en cambio", "Recaudo"]
    ...
```

### Step 2: Add datetime Import
- Ensure `datetime` is imported from the `datetime` module (verify it's already there)
- The import `from datetime import date` exists, but we also need `datetime` for parsing

## Validation

Execute these commands to validate the patch is complete with zero regressions:

1. **Python Syntax Check**
   ```bash
   cd backend && python -m py_compile src/core/servicios/pa_classification_engine.py
   ```

2. **Backend Linting**
   ```bash
   cd backend && ./venv/bin/ruff check src/core/servicios/pa_classification_engine.py
   ```

3. **Backend Tests**
   ```bash
   cd backend && python -m pytest -v --tb=short
   ```

4. **Frontend Linting**
   ```bash
   cd frontend && npm run lint
   ```

5. **Frontend Build**
   ```bash
   cd frontend && npm run build
   ```

## Patch Scope
**Lines of code to change:** ~10-12 lines
**Risk level:** low
**Testing required:** Manual test of PA report classification flow:
1. Upload a NetSuite CSV file
2. Run "Limpiar Datos" (Step 1)
3. Run "Ejecutar Clasificación" (Step 2) - should complete without error
4. Verify classification columns are populated correctly
