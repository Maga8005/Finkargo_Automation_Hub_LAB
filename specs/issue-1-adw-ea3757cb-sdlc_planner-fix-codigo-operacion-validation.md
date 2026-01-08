# Bug: ConsolidatedRecord codigo_operacion validation error on None value

## Bug Description
When processing files in "Reportería Automática" (tab "Cargar Archivos"), clicking the "Procesar Archivos" button fails with a Pydantic validation error. The error occurs because the `codigo_operacion` field in the `ConsolidatedRecord` model is defined as a required string (`str`), but receives `None` when the "ORDEN DE COMPRA" column in the Noova Excel file contains empty/null values.

**Error message:**
```
1 validation error for ConsolidatedRecord
codigo_operacion
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

## Problem Statement
The `ConsolidatedRecord` Pydantic model requires `codigo_operacion` to be a non-null string, but when reading Excel files with empty "ORDEN DE COMPRA" cells, the value `None` is stored in the record dictionary. The `dict.get("codigo_operacion", "")` call in `consolidate_data` returns `None` instead of the default `""` because the key exists with a `None` value. This causes Pydantic validation to fail when instantiating `ConsolidatedRecord`.

## Solution Statement
Make the `codigo_operacion` field in `ConsolidatedRecord` optional (`Optional[str]`) with a default empty string, and ensure that `None` values from the Excel are handled gracefully. Additionally, apply the same fix to other string fields that come from Noova data (`nit`, `nombre_cliente`, `email`, `estado`, `envio`, `codigo_producto`, `concepto`) to prevent similar issues.

## Steps to Reproduce
1. Go to Finanzas → Reportería Automática
2. Select tab "Cargar Archivos"
3. Upload Noova file(s) that contain rows with empty "ORDEN DE COMPRA" column
4. Upload corresponding Netsuite file(s)
5. Click "Procesar Archivos"
6. Observe error 422/400 with Pydantic validation message

## Root Cause Analysis
The bug occurs due to a chain of events:

1. **Excel reading** (`file_processor_co.py` lines 139-153): When reading Excel cells, if `value is None`, the code assigns `None` to the record dictionary:
   ```python
   if value is not None:
       # ... convert value
   record[std_field] = value  # None assigned when cell is empty
   ```

2. **Consolidation** (`file_processor_co.py` lines 239-252): When creating `ConsolidatedRecord`, the code uses:
   ```python
   codigo_operacion=noova.get("codigo_operacion", ""),
   ```
   The `dict.get()` method only returns the default when the key is **missing**, not when the key exists with a `None` value.

3. **Pydantic validation** (`finance_dtos_co.py` line 108): The model defines:
   ```python
   codigo_operacion: str  # Required, non-null string
   ```
   This causes validation to fail when `None` is passed.

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [x] Backend: interface (DTOs)

## Relevant Files
Use these files to fix the bug:

- `backend/src/interface/finance_dtos_co.py` - Contains the `ConsolidatedRecord` Pydantic model definition. Line 108 defines `codigo_operacion: str` which needs to be made optional or have a validator.
- `backend/src/core/servicios/file_processor_co.py` - Contains `consolidate_data` method (lines 176-272) that creates `ConsolidatedRecord` objects. The fix should handle `None` values explicitly using `or ""` pattern.
- `backend/config/colombia/column_mapping.json` - Reference file showing the mapping from Excel column "ORDEN DE COMPRA" to field `codigo_operacion`.
- `backend/tests/test_enum_references.py` - Existing test file to understand test patterns for DTOs.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update ConsolidatedRecord model to handle None values
- Edit `backend/src/interface/finance_dtos_co.py`
- Make `codigo_operacion` field use a default value with the pattern `str = ""` instead of required `str`
- This allows the field to accept empty strings as default while maintaining str type
- Apply the same pattern to other Noova string fields that could be null:
  - `nit: str = ""`
  - `nombre_cliente: str = ""`
  - `email: str = ""`
  - `estado: str = ""`
  - `envio: str = ""`
  - `codigo_producto: str = ""`
  - `concepto: str = ""`
- Keep `numero_factura` and `fecha` as required since they are critical for data integrity

### Step 2: Fix consolidate_data to handle None values explicitly
- Edit `backend/src/core/servicios/file_processor_co.py`
- In the `consolidate_data` method (around line 239), update the `ConsolidatedRecord` instantiation to use `or ""` pattern for all string fields:
  ```python
  record = ConsolidatedRecord(
      fecha=noova.get("fecha"),
      numero_factura=numero_factura,
      nit=noova.get("nit") or "",
      nombre_cliente=noova.get("nombre_cliente") or "",
      email=noova.get("email") or "",
      estado=noova.get("estado") or "",
      envio=noova.get("envio") or "",
      codigo_operacion=noova.get("codigo_operacion") or "",
      codigo_producto=noova.get("codigo_producto") or "",
      concepto=noova.get("concepto") or "",
      moneda=netsuite_match.get("moneda") if netsuite_match else None,
      valor_netsuite=netsuite_match.get("valor") if netsuite_match else None
  )
  ```
- The `or ""` pattern correctly handles both missing keys AND keys with `None` values

### Step 3: Add unit test for ConsolidatedRecord with None values
- Create or update test in `backend/tests/test_file_processor_co.py`
- Add test case that creates `ConsolidatedRecord` with empty/None source data:
  ```python
  def test_consolidated_record_handles_none_codigo_operacion():
      """Test that ConsolidatedRecord handles None codigo_operacion gracefully."""
      from src.interface.finance_dtos_co import ConsolidatedRecord
      from datetime import date

      # This should not raise validation error
      record = ConsolidatedRecord(
          fecha=date(2025, 1, 1),
          numero_factura="FE-12345",
          nit="",
          nombre_cliente="",
          email="",
          estado="",
          envio="",
          codigo_operacion="",  # Empty string instead of None
          codigo_producto="",
          concepto=""
      )
      assert record.codigo_operacion == ""
  ```

### Step 4: Run Validation Commands
Execute the validation commands listed below to confirm the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -c "from src.interface.finance_dtos_co import ConsolidatedRecord; from datetime import date; r = ConsolidatedRecord(fecha=date.today(), numero_factura='FE-123', nit='', nombre_cliente='', email='', estado='', envio='', codigo_operacion='', codigo_producto='', concepto=''); print('SUCCESS: ConsolidatedRecord created with empty strings')"` - Verify ConsolidatedRecord accepts empty strings
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -m pytest tests/ -v -k "consolidated or file_processor"` - Run related unit tests
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -m pytest` - Run all backend tests to validate bug fix with zero regressions
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && ruff check src/` - Run backend linting
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npm run lint` - Run frontend linting (no frontend changes but verify codebase health)
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- The same pattern of `None` values from empty Excel cells could affect other parts of the codebase. If similar bugs occur, apply the same fix: use `or ""` when extracting string values from dictionaries that may contain `None`.
- The `NoovaRecord` DTO also has required string fields. If raw Noova parsing needs to handle `None`, that model should be updated similarly. However, since the bug specifically occurs in `ConsolidatedRecord`, we focus the fix there.
- This is a data validation issue at the boundary between external data (Excel files) and internal domain models. The fix follows the principle of being lenient in what you accept (handle `None` gracefully) while maintaining type safety for internal processing.
