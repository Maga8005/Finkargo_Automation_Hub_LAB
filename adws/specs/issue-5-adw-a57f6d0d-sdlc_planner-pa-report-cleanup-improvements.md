# Feature: PA Report Cleanup Improvements - Data Preservation and Column Formatting

## Feature Description
This feature enhances the PA Report cleanup process in the Finance module to preserve original data values, maintain proper column naming conventions, add new classification columns, implement financial value conversion with Colombian formatting, and apply sign correction rules for USD transactions. The improvements ensure data integrity during the cleanup step while supporting files up to 15-20 MB.

## User Story
As a Finance user
I want the PA Report cleanup process to preserve my original Débito/Crédito values, maintain column names from the source file, and properly format financial values with Colombian number formatting
So that I can accurately process and classify PA transactions without losing important financial data

## Problem Statement
The current PA Report cleanup process has several issues that affect data integrity and usability:
1. Column names are being renamed incorrectly during processing (Mensajes, notas columns)
2. Débito and Crédito values are potentially being cleared during cleanup
3. Column E (fecha de vencimiento) needs to be removed with subsequent columns reordered
4. Only two columns should be renamed: Saldo → Valor COP, Importe (moneda extranjera) → Valor USD
5. New classification columns (AA-AH) are not properly formatted with correct names
6. Financial values need to be converted from Colombian text format ($37.634,41) to numeric while preserving visual formatting
7. USD values need sign correction based on Débito/Crédito conditions

## Solution Statement
Modify the `PAReportService.clean_data()` method to:
1. **Preserve original column names** from the source file, only renaming Saldo→Valor COP and Importe (moneda extranjera)→Valor USD
2. **Remove column E** (fecha de vencimiento) and reorder columns so "Tipo de transacción" becomes column E and the sequence ends with "Entidad (línea): ID interno" at column Z
3. **Preserve Débito and Crédito values** completely during cleanup
4. **Add 8 new columns (AA-AH)** with proper capitalized names and spaces: PA, Categoria, Subcategoria, Clasificacion, Nexo, Comprobacion saldos, Cuenta Homologacion, Nombre Homologacion
5. **Convert financial values** from Colombian text format to numeric while maintaining display format
6. **Apply USD sign correction**: Débitos USD must be positive, Créditos USD must be negative

## Access Control
- Required Role(s): `finance`, `finance_admin`, `admin`
- Backend Protection: `require_roles(['finance', 'finance_admin', 'admin'])` on PA processing endpoints
- Frontend Protection: `RoleProtectedRoute` with `allowedRoles={['finance', 'finance_admin', 'admin']}`

## Relevant Files
Use these files to implement the feature:

**Backend - Core Service (Primary Changes):**
- `backend/src/core/servicios/pa_report_service.py` - Main file to modify. Contains `clean_data()` method (lines 341-492) that handles column renaming, data transformation, and output generation. Key areas:
  - Lines 48-64: `SOURCE_COLUMN_MAPPING` - Defines column name mappings
  - Lines 78-87: `OUTPUT_COLUMNS` - Defines new columns to add
  - Lines 381-384: Column renaming logic (currently renames saldo→valor_cop, importe→valor_usd)
  - Lines 387-389: Numeric conversion for financial columns
  - Lines 391-404: Adding new classification columns

**Backend - DTOs:**
- `backend/src/interface/pa_dtos.py` - Contains Pydantic models for PA processing. May need updates to reflect new column structure and formatting options.

**Backend - Tests:**
- `backend/tests/test_pa_report_service.py` - Existing tests for PA service. Add new tests for data preservation, column ordering, and sign correction logic.

**Documentation:**
- `app_docs/feature-550a54d1-pa-report-classification.md` - Reference documentation for PA Report feature architecture
- `.claude/commands/test_e2e.md` - E2E test runner documentation for understanding test execution
- `.claude/commands/e2e/test_pa_csv_upload.md` - Existing E2E test for PA CSV upload (reference for new E2E test)

### New Files
- `.claude/commands/e2e/test_pa_report_cleanup_improvements.md` - New E2E test file to validate the cleanup improvements: column preservation, data integrity, new columns, and sign correction

## Pre-Implementation Verification

### Feature Category
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Document Generation (contracts, PDFs)
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [ ] Reporting (queries, history)
- [ ] CRUD Operations (basic data management)

### B. Excel Column Mapping (Excel Processing)

**Source Excel Structure (NetSuite Movements File):**
| Column Letter | Column Name (exact) | Required | Data Type | Notes |
|--------------|---------------------|----------|-----------|-------|
| A | Cuenta (línea): Número | Yes | String | Account number |
| B | Cuenta (línea): Nombre | Yes | String | Account name |
| C | Fecha | Yes | Date | Transaction date |
| D | Fecha de creación | Yes | Date | Creation date |
| E | Fecha de vencimiento | No | Date | **TO BE REMOVED** |
| F | Tipo de Transacción | Yes | String | Transaction type |
| G | Tipo de comprobante | Yes | String | Document type |
| H | Número de documento | Yes | String | Document number |
| I | Entidad | Yes | String | Entity name |
| J | notas | No | String | Notes (keep lowercase) |
| K | Mensajes | No | String | Messages (keep original name) |
| L | Débito | Yes | Currency | **PRESERVE VALUES** |
| M | Crédito | Yes | Currency | **PRESERVE VALUES** |
| N | Saldo | Yes | Currency | **RENAME TO: Valor COP** |
| O | Moneda: Nombre | Yes | String | Currency name (USD/COP) |
| P | Tipo de cambio | No | Decimal | Exchange rate |
| Q | Importe (moneda extranjera) | Yes | Currency | **RENAME TO: Valor USD** |
| ... | (additional columns) | | | |
| Z | Entidad (línea): ID interno | Yes | String | Internal entity ID |

**Output Excel Structure (After Cleanup):**
| Column | Column Name | Source | Transformation |
|--------|-------------|--------|----------------|
| A | Cuenta (línea): Número | Direct | No change |
| B | Cuenta (línea): Nombre | Direct | No change |
| C | Fecha | Direct | No change |
| D | Fecha de creación | Direct | No change |
| E | Tipo de Transacción | Direct | **Moved from F after removing fecha vencimiento** |
| F | Tipo de comprobante | Direct | Reordered |
| ... | ... | ... | ... |
| (varies) | notas | Direct | Keep original name |
| (varies) | Mensajes | Direct | Keep original name (NOT rename to notas) |
| (varies) | Débito | Direct | **PRESERVE - Convert text to numeric** |
| (varies) | Crédito | Direct | **PRESERVE - Convert text to numeric** |
| (varies) | Valor COP | Saldo | **Renamed** - Convert text to numeric |
| (varies) | Valor USD | Importe (moneda extranjera) | **Renamed** - Convert text to numeric, apply sign correction |
| Z | Entidad (línea): ID interno | Direct | Last column before new columns |
| AA | PA | New | Default value: "X" |
| AB | Categoria | New | Empty (filled in classification step) |
| AC | Subcategoria | New | Empty (filled in classification step) |
| AD | Clasificacion | New | Empty (filled in classification step) |
| AE | Nexo | New | Empty (filled in classification step) |
| AF | Comprobacion saldos | New | Empty (filled in classification step) |
| AG | Cuenta Homologacion | Catalog lookup | From pa_account_catalog |
| AH | Nombre Homologacion | Catalog lookup | From pa_account_catalog |

**Financial Value Conversion Rules:**
| Source Format | Internal Value | Display Format |
|--------------|----------------|----------------|
| `$37.634,41` | `37634.41` | `$37.634,41` (Colombian: dot=thousands, comma=decimal) |
| `$1.234.567,89` | `1234567.89` | `$1.234.567,89` |
| Empty/blank | `0` | `$0,00` |

**USD Sign Correction Rules:**
| Condition | Valor USD Validation | Action |
|-----------|---------------------|--------|
| Moneda: Nombre = "USD" AND Débito has value (not empty, not 0) | Must be positive (> 0) | If negative → make positive |
| Moneda: Nombre = "USD" AND Crédito has value (not empty, not 0) | Must be negative (< 0) | If positive → make negative |

**Catalog Dependencies:**
- [x] PA account catalog (`pa_account_catalog` table) for Cuenta Homologacion and Nombre Homologacion lookups
- [ ] No country-specific variations (Colombia only)

### D. Data Contract Verification

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `repository.get_account_catalog()` | `tuple[list[dict], int]` | `entry["cuenta_finkargo"]` | Catalog entries as dicts |
| `repository.get_all_catalog_accounts()` | `list[str]` | `accounts[0]` | List of account numbers |
| `repository.update_processing_session()` | `bool` | N/A | Update success flag |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| session_id | session_id | string | Processing session identifier |
| pa_rows | pa_rows | number | Count of PA account rows |
| total_rows | total_rows | number | Total rows in file |
| debito_sum | debito_sum | number | Sum of Débito values |
| credito_sum | credito_sum | number | Sum of Crédito values |
| valor_cop_sum | valor_cop_sum | number | Sum of Valor COP |
| valor_usd_sum | valor_usd_sum | number | Sum of Valor USD |
| balance_valid | balance_valid | boolean | Whether sums balance |
| column_headers | column_headers | string[] | List of output column names |

## Implementation Plan

### Phase 1: Foundation
- Add helper functions for Colombian number parsing and formatting
- Update column mapping constants to reflect new requirements
- Create test fixtures with sample data including edge cases

### Phase 2: Core Implementation
- Modify `_rename_columns()` to only rename Saldo and Importe columns
- Implement column removal (fecha de vencimiento) and reordering logic
- Update `clean_data()` to preserve Débito/Crédito values
- Add Colombian number parsing function for financial columns
- Implement USD sign correction logic based on Débito/Crédito conditions
- Update new column names to use proper capitalization with spaces

### Phase 3: Integration
- Update output Excel generation to maintain Colombian number formatting
- Add comprehensive unit tests for each transformation
- Create E2E test for full cleanup workflow validation

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` to understand E2E test structure
- Read `.claude/commands/e2e/test_pa_csv_upload.md` as reference
- Create `.claude/commands/e2e/test_pa_report_cleanup_improvements.md` with test steps:
  1. Upload a test Excel file with known Débito/Crédito values
  2. Execute cleanup step
  3. Download cleaned file
  4. Verify column names preserved (Mensajes, notas)
  5. Verify Débito/Crédito values intact
  6. Verify new columns AA-AH with correct names
  7. Verify PA column has "X" values
  8. Verify financial value conversion (text → numeric)
  9. Verify USD sign correction for Débito/Crédito transactions

### Step 2: Add Colombian Number Parsing Helper
- Edit `backend/src/core/servicios/pa_report_service.py`
- Add new helper method `_parse_colombian_number()` to convert text format to float:
  ```python
  def _parse_colombian_number(self, value) -> float:
      """
      Parse Colombian currency format to float.
      Example: '$37.634,41' -> 37634.41
      """
      if pd.isna(value) or value == '' or value is None:
          return 0.0
      if isinstance(value, (int, float)):
          return float(value)
      # Remove currency symbol and whitespace
      str_value = str(value).strip().replace('$', '').replace(' ', '')
      # Colombian format: dot=thousands, comma=decimal
      # Remove thousand separators (dots)
      str_value = str_value.replace('.', '')
      # Convert decimal separator (comma) to dot
      str_value = str_value.replace(',', '.')
      try:
          return float(str_value)
      except ValueError:
          return 0.0
  ```

### Step 3: Update Column Mapping Constants
- Edit `backend/src/core/servicios/pa_report_service.py`
- Modify `SOURCE_COLUMN_MAPPING` to preserve original column names
- Add constant for columns to remove: `COLUMNS_TO_REMOVE = ["Fecha de vencimiento"]`
- Update `OUTPUT_COLUMNS` to use proper capitalized names with spaces:
  ```python
  OUTPUT_COLUMNS = [
      "PA",                    # AA
      "Categoria",             # AB
      "Subcategoria",          # AC
      "Clasificacion",         # AD
      "Nexo",                  # AE
      "Comprobacion saldos",   # AF
      "Cuenta Homologacion",   # AG
      "Nombre Homologacion"    # AH
  ]
  ```

### Step 4: Modify Column Renaming Logic
- Edit `backend/src/core/servicios/pa_report_service.py`
- Update `_rename_columns()` method to ONLY rename these two columns:
  - `Saldo` → `Valor COP`
  - `Importe (moneda extranjera)` → `Valor USD`
- Preserve ALL other column names exactly as they appear in source file
- Specifically ensure:
  - Column N keeps name `notas` (do not change)
  - Column O keeps name `Mensajes` (do NOT rename to notas)

### Step 5: Implement Column Removal and Reordering
- Edit `backend/src/core/servicios/pa_report_service.py`
- In `clean_data()` method, add logic to:
  1. Remove "Fecha de vencimiento" column (column E)
  2. Reorder remaining columns so "Tipo de transacción" becomes column E
  3. Ensure "Entidad (línea): ID interno" is at column Z
- Use pandas DataFrame column manipulation:
  ```python
  # Remove fecha de vencimiento column
  if 'fecha_vencimiento' in pa_df.columns:
      pa_df = pa_df.drop(columns=['fecha_vencimiento'])
  # Reorder columns to maintain expected sequence
  ```

### Step 6: Preserve Débito and Crédito Values
- Edit `backend/src/core/servicios/pa_report_service.py`
- In `clean_data()` method, modify the numeric conversion section (lines 387-389)
- Apply Colombian number parsing to convert text to numeric:
  ```python
  for col in ["debito", "credito", "valor_cop", "valor_usd"]:
      if col in pa_df.columns:
          pa_df[col] = pa_df[col].apply(self._parse_colombian_number)
  ```
- CRITICAL: Do NOT clear or zero out Débito/Crédito values

### Step 7: Implement USD Sign Correction
- Edit `backend/src/core/servicios/pa_report_service.py`
- In `clean_data()` method, after numeric conversion, add sign correction logic:
  ```python
  # USD Sign Correction
  # Débitos USD: ensure positive
  mask_debito_usd = (pa_df['moneda_nombre'] == 'USD') & (pa_df['debito'].notna()) & (pa_df['debito'] != 0)
  pa_df.loc[mask_debito_usd & (pa_df['valor_usd'] < 0), 'valor_usd'] = pa_df.loc[mask_debito_usd & (pa_df['valor_usd'] < 0), 'valor_usd'].abs()

  # Créditos USD: ensure negative
  mask_credito_usd = (pa_df['moneda_nombre'] == 'USD') & (pa_df['credito'].notna()) & (pa_df['credito'] != 0)
  pa_df.loc[mask_credito_usd & (pa_df['valor_usd'] > 0), 'valor_usd'] = -pa_df.loc[mask_credito_usd & (pa_df['valor_usd'] > 0), 'valor_usd'].abs()
  ```

### Step 8: Update New Column Names to Use Proper Formatting
- Edit `backend/src/core/servicios/pa_report_service.py`
- Update the section that adds new columns (lines 391-404) to use capitalized names with spaces:
  ```python
  # Add PA marker column
  pa_df["PA"] = "X"

  # Add empty classification columns with proper names
  for col in ["Categoria", "Subcategoria", "Clasificacion", "Nexo", "Comprobacion saldos"]:
      pa_df[col] = None

  # Add homologation columns with proper names
  pa_df["Cuenta Homologacion"] = pa_df["cuenta_linea_numero"].apply(
      lambda x: catalog_dict.get(str(x), {}).get("cuenta_homologacion")
  )
  pa_df["Nombre Homologacion"] = pa_df["cuenta_linea_numero"].apply(
      lambda x: catalog_dict.get(str(x), {}).get("nombre_homologacion")
  )
  ```

### Step 9: Update Excel Output Formatting
- Edit `backend/src/core/servicios/pa_report_service.py`
- Modify the Excel generation in `clean_data()` and `get_cleaned_excel()` methods
- Apply Colombian number formatting to financial columns using openpyxl:
  ```python
  # When writing to Excel, format financial columns with Colombian style
  # Number format: '$#.##0,00' (Colombian: dot=thousands, comma=decimal)
  ```

### Step 10: Update Classification Engine for New Column Names
- Edit `backend/src/core/servicios/pa_classification_engine.py`
- Update `classify_record()` method to use new column names with proper capitalization
- Ensure the engine writes to "Categoria", "Subcategoria", etc. (not lowercase)

### Step 11: Add Unit Tests
- Edit `backend/tests/test_pa_report_service.py`
- Add new test class for cleanup improvements:
  ```python
  class TestPAReportCleanupImprovements:
      """Tests for PA Report cleanup improvements."""

      def test_colombian_number_parsing(self):
          """Test parsing of Colombian currency format."""

      def test_debito_credito_preservation(self):
          """Test that Débito and Crédito values are preserved during cleanup."""

      def test_column_name_preservation(self):
          """Test that original column names are preserved except Saldo and Importe."""

      def test_fecha_vencimiento_removed(self):
          """Test that fecha de vencimiento column is removed."""

      def test_new_column_names_format(self):
          """Test that new columns have proper capitalized names with spaces."""

      def test_pa_column_default_value(self):
          """Test that PA column has 'X' as default value."""

      def test_usd_sign_correction_debito(self):
          """Test USD sign correction for Débito transactions."""

      def test_usd_sign_correction_credito(self):
          """Test USD sign correction for Crédito transactions."""
  ```

### Step 12: Run Validation Commands
Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
- Test Colombian number parsing with various formats: `$37.634,41`, `$1.234.567,89`, empty, null
- Test Débito/Crédito value preservation through cleanup
- Test column name preservation (Mensajes, notas stay as-is)
- Test column removal and reordering
- Test USD sign correction for Débito transactions
- Test USD sign correction for Crédito transactions
- Test new column names with proper capitalization

### Edge Cases
- Empty financial values (should convert to 0)
- Negative values in wrong direction (sign correction must fix)
- Mixed USD and COP transactions in same file
- Large files (15-20 MB) processing performance
- Files with missing columns (graceful handling)
- Values already in numeric format (don't double-convert)
- Column variations (double spaces, different capitalization)

## Acceptance Criteria
- [ ] Nombres de columnas preservados del archivo original (excepto Saldo e Importe moneda extranjera)
- [ ] Columna "Mensajes" mantiene su nombre original (no renombrada a notas)
- [ ] Columna "notas" mantiene su nombre original
- [ ] Columna E (Fecha de vencimiento) eliminada y secuencia reordenada correctamente
- [ ] Columna Z = "Entidad (línea): ID interno" después de reordenamiento
- [ ] Valores de Débito preservados intactos durante limpieza
- [ ] Valores de Crédito preservados intactos durante limpieza
- [ ] 8 nuevas columnas agregadas en posiciones AA-AH:
  - [ ] PA (AA) con valor "X" en todas las filas
  - [ ] Categoria (AB)
  - [ ] Subcategoria (AC)
  - [ ] Clasificacion (AD)
  - [ ] Nexo (AE)
  - [ ] Comprobacion saldos (AF)
  - [ ] Cuenta Homologacion (AG)
  - [ ] Nombre Homologacion (AH)
- [ ] Conversión numérica funcional: `$37.634,41` → `37634.41`
- [ ] Formato visual correcto en Excel: signo `$`, puntos como separador de miles, coma como separador decimal
- [ ] Débitos USD: valores negativos corregidos a positivos
- [ ] Créditos USD: valores positivos corregidos a negativos
- [ ] Archivos de 15-20 MB procesados sin error

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -c "from src.core.servicios.pa_report_service import PAReportService; print('Import successful')"` - Verify service imports correctly after changes
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -m pytest tests/test_pa_report_service.py -v` - Run PA Report service tests
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/backend && ruff check src/` - Run backend linting
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npm run lint` - Run frontend linting
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd /mnt/c/Users/maria.gaitan/mvp_worspace/projects/Finkargo_Automation_Hub_LAB2/frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_report_cleanup_improvements.md` E2E test to validate the cleanup improvements

## Notes
- **No new libraries required** - All functionality can be implemented with existing pandas and openpyxl packages
- **Performance consideration** - The Colombian number parsing function should be vectorized using pandas `apply()` for efficiency with large files (15-20 MB)
- **Backward compatibility** - The changes to column naming may affect downstream processes that rely on specific column names. The classification engine must be updated to use new column names
- **Data integrity** - Débito/Crédito preservation is CRITICAL - these values must never be zeroed or cleared during cleanup
- **Sign correction timing** - USD sign correction must happen AFTER numeric conversion to ensure proper comparison
- **Column ordering** - The exact column order after removing fecha de vencimiento must match the requirement that "Tipo de transacción" becomes column E and "Entidad (línea): ID interno" is at column Z

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (Excel Processing)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified (none needed - schema unchanged)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies listed (none - using existing packages)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented
- [x] Data transformation rules specified (column renaming, sign correction)
- [x] Catalog/lookup dependencies identified (pa_account_catalog)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions documented
- [x] Access patterns verified for repository methods
- [x] Country-specific variations handled (Colombia-specific number format)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
