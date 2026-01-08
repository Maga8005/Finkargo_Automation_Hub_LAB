# Bug: Mexico COMISION Concept Types Not Generating in Output

## Bug Description
When uploading a Historial de Pagos file for Mexico in the Tesorería module (Aplicación de Pagos México), the output file is not generating line items for COMISION-type concept_type values. The user reports that even though the upload file has values in the column `<Comisión del desembolso + IVA>`, no output rows are generated for:
- COMISION DESEMBOLSO
- COMISION DISPOSICION
- COMISION SWIFT
- COMISION ADMINISTRACION
- COMISION APERTURA

Additionally, COSTOS ADICIONALES may also be affected.

**Expected Behavior:** When the input Excel file has non-zero values in COMISION columns, the output should contain corresponding rows with the appropriate concept_type.

**Actual Behavior:** COMISION and possibly COSTOS ADICIONALES concept types are not appearing in the output file, even when the source columns have values.

## Problem Statement
The column name matching in `payment_template_service.py` uses case-insensitive normalization (`.lower()`), but this does **not** normalize accented characters. The `MEXICO_CONCEPT_COLUMNS` catalog defines column names **without** Spanish accents (e.g., `"Comision del desembolso + IVA"`), but the actual Excel files likely contain column names **with** proper Spanish accents (e.g., `"Comisión del desembolso + IVA"`).

When comparing:
- Catalog (normalized): `"comision del desembolso + iva"` (without accent)
- Excel (normalized): `"comisión del desembolso + iva"` (with accent)

These strings are **not equal** because `ó ≠ o`, causing the column lookup to fail silently and return 0.0 for all COMISION columns.

## Solution Statement
Update the `MEXICO_CONCEPT_COLUMNS` dictionary in `payment_catalogs.py` to use the correct Spanish accented column names that match the actual Excel file headers. This is the minimal, surgical fix that addresses the root cause without modifying the matching logic.

Affected columns to update:
- `"Comision del desembolso + IVA"` → `"Comisión del desembolso + IVA"`
- `"Comision por disposicion de crédito + IVA"` → `"Comisión por disposición de crédito + IVA"`
- `"Comision swift"` → `"Comisión swift"`
- `"Comision administracion y manejo"` → `"Comisión administración y manejo"`
- `"Comision de apertura"` → `"Comisión de apertura"`

## Steps to Reproduce
1. Navigate to http://localhost:5173/tesoreria/plantillas-netsuite/mexico
2. Upload a Mexico Historial de Pagos Excel file that contains:
   - Values in the "Comisión del desembolso + IVA" column (with accent)
   - Values in other COMISION columns (with accents)
3. Click "Convertir y Descargar"
4. Open the downloaded file
5. **Observe:** No rows with concept_type "COMISION DESEMBOLSO" or other COMISION types appear
6. **Expected:** Rows with COMISION concept types should appear with the corresponding payment_amount values

## Root Cause Analysis
The root cause is a **character encoding mismatch** between the catalog definitions and the actual Excel column headers:

1. **Catalog Definition** (`payment_catalogs.py:171-175`):
   ```python
   "COMISION DESEMBOLSO": "Comision del desembolso + IVA",  # Missing accent on "ó"
   "COMISION DISPOSICION": "Comision por disposicion de crédito + IVA",  # Missing accents
   "COMISION SWIFT": "Comision swift",  # Missing accent
   "COMISION ADMINISTRACION": "Comision administracion y manejo",  # Missing accents
   "COMISION APERTURA": "Comision de apertura",  # Missing accent
   ```

2. **Matching Logic** (`payment_template_service.py:479-481`):
   ```python
   def get_numeric_value(col_name: str) -> float:
       normalized = col_name.strip().lower()  # Does NOT normalize accents!
       source_col = df_columns_normalized.get(normalized)
   ```

3. **Actual Excel Headers** (from user's file):
   - `"Comisión del desembolso + IVA"` (with proper Spanish accents)

The `.lower()` method in Python does not convert accented characters to their unaccented equivalents. Therefore `"comisión".lower()` returns `"comisión"`, not `"comision"`.

## Affected Layer
- [x] Backend: core/servicios (business logic) - catalog definitions
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (lines 169-191) - Contains `MEXICO_CONCEPT_COLUMNS` dictionary with the incorrect column names. **This is the primary file to fix.** Update the column name values to include proper Spanish accents.

- **`backend/src/core/servicios/payment_template_service.py`** (lines 479-529) - Contains the `_process_concepts` method that uses these column mappings. No changes needed here as the fix is in the catalog.

- **`frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx`** (lines 147-151) - Contains the frontend instructions that show the expected column names. These already show the correct accented names, confirming the mismatch.

### New Files
- **`.claude/commands/e2e/test_mexico_comision_concept_fix.md`** - E2E test file to validate the COMISION concept types are correctly generated in the output.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Update MEXICO_CONCEPT_COLUMNS with Correct Accented Column Names
- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Locate the `MEXICO_CONCEPT_COLUMNS` dictionary (lines 169-191)
- Update the following column name values to include proper Spanish accents:

```python
# Before:
"COMISION DESEMBOLSO": "Comision del desembolso + IVA",
"COMISION DISPOSICION": "Comision por disposicion de crédito + IVA",
"COMISION SWIFT": "Comision swift",
"COMISION ADMINISTRACION": "Comision administracion y manejo",
"COMISION APERTURA": "Comision de apertura",

# After:
"COMISION DESEMBOLSO": "Comisión del desembolso + IVA",
"COMISION DISPOSICION": "Comisión por disposición de crédito + IVA",
"COMISION SWIFT": "Comisión swift",
"COMISION ADMINISTRACION": "Comisión administración y manejo",
"COMISION APERTURA": "Comisión de apertura",
```

- Also verify `COSTOS ADICIONALES` column name is correct (currently `"Costos adicionales"` - may need to check if actual Excel has different casing/accents)

### Task 2: Create E2E Test File for COMISION Concept Validation
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/test_e2e.md` to understand the E2E test format
- Create `.claude/commands/e2e/test_mexico_comision_concept_fix.md` with:
  - User story for validating COMISION concept types appear in output
  - Prerequisites: servers running, test Excel file with COMISION values
  - Test steps to:
    1. Navigate to Mexico payment template page
    2. Upload a test file with known COMISION values
    3. Convert and download the output
    4. Verify the output contains COMISION DESEMBOLSO and other concept types
  - Success criteria confirming COMISION rows appear with correct amounts
  - Screenshot requirements

### Task 3: Run Validation Commands
Execute all validation commands to ensure the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Pre-fix Reproduction (document current behavior)
1. Navigate to http://localhost:5173/tesoreria/plantillas-netsuite/mexico
2. Upload a test Mexico Historial de Pagos file with values in COMISION columns
3. Download the output and verify COMISION concept types are missing (document this)

### Post-fix Validation
1. After applying the fix, repeat the upload with the same test file
2. Verify the output now contains rows with:
   - concept_type = "COMISION DESEMBOLSO"
   - concept_type = "COMISION DISPOSICION"
   - concept_type = "COMISION SWIFT"
   - concept_type = "COMISION ADMINISTRACION"
   - concept_type = "COMISION APERTURA"
   - concept_type = "COSTOS ADICIONALES" (if applicable)

### Automated Validation Commands
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting (ensure no syntax errors from accent characters)
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

### E2E Test Validation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_mexico_comision_concept_fix.md` to validate the COMISION concept types are correctly generated.

## Notes
- **Character Encoding**: Ensure the `payment_catalogs.py` file is saved with UTF-8 encoding to preserve Spanish accents.
- **No New Dependencies**: This fix does not require any new npm or pip packages.
- **Colombia Unchanged**: This fix only affects Mexico column mappings. Colombia column names in `COLOMBIA_CONCEPT_COLUMNS` are not modified.
- **Minimal Change**: This is a surgical fix that only updates the string values in the dictionary. No logic changes are required.
- **Frontend Already Correct**: The frontend instructions in `PlantillasNetSuiteMX.tsx` already show the correct accented column names (lines 147-149), which confirms the expected format.
