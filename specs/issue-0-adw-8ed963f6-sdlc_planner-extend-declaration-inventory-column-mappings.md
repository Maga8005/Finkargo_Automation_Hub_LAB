# Feature: Extend Declaration Inventory Upload Column Mappings

## Feature Description

Extend the "Inventario de Declaraciones" (Declaration Inventory) upload in the Treasury Declaration Matching workflow to accept a new Excel file format with columns from an automated scanner output. The current implementation expects Spanish column names (`Cliente`, `Fecha`, `Monto`, `Numero DC`), but the new format uses English column names from an automated PDF scanner (`Customer Name`, `Date Folder`, `Amount Folder`, `Declaration Number`, `PDF File Name`, etc.).

The feature will:
1. Add new column name variations to the backend parser
2. Handle the new date format (`DD-MM-YYYY` from folder names)
3. Parse the new amount format (`8.111,43` European format with dot thousands separator and comma decimal)
4. Extract declaration number from the `Declaration Number` column
5. Update frontend UI text to reflect the new accepted formats
6. Handle the `Parsed Date` and `Parsed Amount` columns as alternative sources

## User Story

As a **Treasury (tesoreria) team member**
I want to **upload my automated scanner output Excel file as the declaration inventory**
So that I can **match declarations to payments without manually reformatting the Excel file**

## Problem Statement

Treasury users have an automated scanner that generates an Excel file with declaration information from PDF files in a specific folder structure. The current declaration inventory upload only accepts files with Spanish column names (`Cliente`, `Fecha`, `Monto`, `Numero`), requiring users to manually rename columns before uploading. This creates friction and potential for errors.

The scanner output file `20251215 Diveco Test.xlsx` has these columns:
- `Customer Name` (instead of `Cliente`)
- `Date Folder` (format: `DD-MM-YYYY`, e.g., `01-07-2025`)
- `Amount Folder` (European format: `8.111,43`)
- `PDF File Name` (e.g., `DC 4.862,00.pdf`)
- `Declaration Number` (e.g., `81590`)
- `Parsed Date` (alternative date source, format: `YYYY-MM-DD`)
- `Parsed Amount` (alternative amount source, format: `$4,862.00`)

## Solution Statement

Update the backend `upload_declarations` endpoint to:
1. Accept both Spanish and English column name variations
2. Prioritize `Parsed Date` over `Date Folder` when available (cleaner format)
3. Prioritize `Parsed Amount` over `Amount Folder` when available (standard format)
4. Parse European amount format (`8.111,43`) from `Amount Folder`
5. Parse folder date format (`DD-MM-YYYY`) from `Date Folder`
6. Use `PDF File Name` column for the PDF filename field

Update the frontend uploader component to show the new accepted column formats in the UI hint text.

## Access Control

- **Required Role(s)**: `tesoreria`, `admin`
- **Backend Protection**: Already uses `require_roles(['tesoreria'])` from `rbac_dependencies.py`
- **Frontend Protection**: Already uses `<RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>` for the matching page route

## Relevant Files

Use these files to implement the feature:

### Backend Files
- `backend/src/adapter/rest/treasury_matching_routes.py` (lines 170-330) - Contains the `upload_declarations` endpoint with column mapping logic that needs to be extended with new column variations
- `backend/src/core/servicios/treasury/historial_parser_service.py` - Reference for the `_normalize_customer_name` function already being used

### Frontend Files
- `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx` (lines 263-314) - The declaration inventory upload section with UI text that shows required columns
- `frontend/src/types/treasuryMatching.ts` - TypeScript types (no changes needed, but reference for type definitions)

### Test References
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_declaration_historial_matching.md` - Existing E2E test file to update

### New Files

1. `.claude/commands/e2e/test_treasury_declaration_matching_menu.md` - E2E test file to validate the new column format upload works correctly

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs)
- [x] **Excel Processing (treasury, finance)** ’ Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [ ] Reporting (queries, history)
- [ ] CRUD Operations (basic data management)

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (New Scanner Format - 10 columns):**

| Column Name (exact) | Required | Data Type | Validation | Notes |
|--------------------|----------|-----------|------------|-------|
| Customer Name | Yes | String | Not empty | Customer/company name from folder |
| Date Folder | Yes* | String | `DD-MM-YYYY` format | Date from folder structure |
| Amount Folder | Yes* | String | European format `8.111,43` | Amount from folder name |
| PDF File Name | No | String | - | e.g., `DC 4.862,00.pdf` |
| PDF File Path | No | String | - | Full Windows path (ignored) |
| Declaration Number | Yes | Float/String | Numeric | e.g., `81590` or `NaN` for failures |
| Extraction Status | No | String | SUCCESS/PARTIAL/FAILED | Scanner status |
| Extraction Error | No | String | - | Error message if failed |
| Parsed Date | No* | String | `YYYY-MM-DD` format | Preferred date source if available |
| Parsed Amount | No* | String | US format `$4,862.00` | Preferred amount source if available |

*Note: Either `Date Folder` OR `Parsed Date` required. Either `Amount Folder` OR `Parsed Amount` required.

**Column Mappings (Extended with New Variations):**

```python
# Existing mappings (backward compatible)
customer_cols = ['Cliente', 'Customer', 'Nombre', 'customer_name']
date_cols = ['Fecha', 'Date', 'fecha']
amount_cols = ['Monto', 'Amount', 'Valor', 'amount']
number_cols = ['Numero', 'Number', 'Declaracion', 'declaration_number', 'DC']
pdf_cols = ['PDF', 'Archivo', 'File', 'pdf_file_name', 'Nombre PDF']

# NEW mappings to add
customer_cols += ['Customer Name']
date_cols += ['Date Folder', 'Parsed Date']  # Prefer 'Parsed Date' when found
amount_cols += ['Amount Folder', 'Parsed Amount']  # Prefer 'Parsed Amount' when found
number_cols += ['Declaration Number']
pdf_cols += ['PDF File Name']
```

**Data Transformation Rules:**
1. **Date parsing priority**: `Parsed Date` (YYYY-MM-DD) > `Date Folder` (DD-MM-YYYY)
2. **Amount parsing priority**: `Parsed Amount` ($4,862.00) > `Amount Folder` (8.111,43)
3. **European amount format**: Replace `.` with nothing, replace `,` with `.` ’ `8.111,43` ’ `8111.43`
4. **US amount format**: Remove `$` and `,` ’ `$4,862.00` ’ `4862.00`
5. **Declaration number**: Convert float to int string, skip if `NaN`

**Catalog Dependencies:**
- [x] No AR account mappings needed (this is matching, not payment conversion)
- [x] No country-specific variations (Colombia-only feature)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| No repository methods | N/A | N/A | In-memory session storage only |

**Note:** This feature only modifies Excel parsing logic in the API endpoint. No repository changes needed.

### Interface Mapping (Frontend ” Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| (UI text only) | customer_cols variations | string[] | Column name variations |
| (UI text only) | date_cols variations | string[] | Column name variations |
| (UI text only) | amount_cols variations | string[] | Column name variations |
| (UI text only) | number_cols variations | string[] | Column name variations |

No new TypeScript types needed - the `DeclarationItem` interface already captures the parsed data.

## Implementation Plan

### Phase 1: Backend Column Mapping Extension
1. Update `upload_declarations` endpoint in `treasury_matching_routes.py`
2. Add new column name variations to the existing column detection lists
3. Add European amount format parsing function
4. Implement date/amount source priority logic (prefer `Parsed Date`/`Parsed Amount`)

### Phase 2: Frontend UI Updates
5. Update the UI hint text in `FKHistorialMatchingUploader.tsx` to show new accepted column formats
6. Update the image shown in step 2 description to reflect new requirements

### Phase 3: Testing
7. Create E2E test file for the new column format
8. Run validation commands

## Step by Step Tasks

### Step 1: Add European Amount Format Parser

- Open `backend/src/adapter/rest/treasury_matching_routes.py`
- Add a helper function `parse_amount_value(value)` near line 170 (before the endpoint)
- Function should handle: `8.111,43` ’ `8111.43`, also handle `$4,862.00` ’ `4862.00`
- Return float or None if parsing fails

```python
def parse_amount_value(value) -> Optional[float]:
    """Parse amount from various formats (European, US, or plain number)."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()

    # US format: $4,862.00
    if '$' in value_str:
        clean = value_str.replace('$', '').replace(',', '').strip()
        return float(clean)

    # European format: 8.111,43 (dots for thousands, comma for decimal)
    if ',' in value_str and '.' in value_str:
        # European: remove dots (thousands), replace comma with dot (decimal)
        clean = value_str.replace('.', '').replace(',', '.')
        return float(clean)

    # Simple comma decimal: 8111,43
    if ',' in value_str and '.' not in value_str:
        clean = value_str.replace(',', '.')
        return float(clean)

    # Standard number with commas as thousands: 8,111.43
    clean = value_str.replace(',', '')
    return float(clean)
```

### Step 2: Extend Column Name Variations

- In `upload_declarations` function (around lines 208-213), extend the column variation lists:

```python
# Extended column variations (backward compatible + new scanner format)
customer_cols = ['Cliente', 'Customer', 'Nombre', 'customer_name', 'Customer Name']
date_cols = ['Fecha', 'Date', 'fecha', 'Parsed Date', 'Date Folder']
amount_cols = ['Monto', 'Amount', 'Valor', 'amount', 'Parsed Amount', 'Amount Folder']
number_cols = ['Numero', 'Number', 'Declaracion', 'declaration_number', 'DC', 'Declaration Number']
pdf_cols = ['PDF', 'Archivo', 'File', 'pdf_file_name', 'Nombre PDF', 'PDF File Name']
```

### Step 3: Implement Priority Column Selection

- Update the `find_col` function to support priority-based selection
- When both `Parsed Date` and `Date Folder` exist, prefer `Parsed Date`
- When both `Parsed Amount` and `Amount Folder` exist, prefer `Parsed Amount`

```python
def find_col_with_priority(df_cols, variations):
    """Find column with priority (earlier in variations list = higher priority)."""
    df_cols_lower = {c.lower().strip(): c for c in df_cols}
    for var in variations:
        if var.lower().strip() in df_cols_lower:
            return df_cols_lower[var.lower().strip()]
    return None

# Priority order: prefer Parsed Date/Amount over folder-based values
date_cols_priority = ['Parsed Date', 'Fecha', 'Date', 'fecha', 'Date Folder']
amount_cols_priority = ['Parsed Amount', 'Monto', 'Amount', 'Valor', 'amount', 'Amount Folder']
```

### Step 4: Update Date Parsing Logic

- Update the date parsing section (around lines 254-274) to handle multiple formats:
- Add `DD-MM-YYYY` format (folder date) to the format list
- The existing code already handles `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, `MM/DD/YYYY`

### Step 5: Update Amount Parsing Logic

- Replace the amount parsing section (around lines 276-289) with the new `parse_amount_value` function
- Handle all formats: European (`8.111,43`), US (`$4,862.00`), plain numbers

### Step 6: Handle NaN Declaration Numbers

- Update declaration number extraction (around line 291) to handle float NaN values:

```python
# Handle NaN values for declaration number
number_val = row[number_col]
if pd.isna(number_val) or str(number_val).lower() == 'nan':
    # Skip rows without declaration numbers or continue with empty string
    declaration_number = ""
else:
    # Convert float to int string (81590.0 ’ "81590")
    if isinstance(number_val, float) and number_val.is_integer():
        declaration_number = str(int(number_val))
    else:
        declaration_number = str(number_val)
```

### Step 7: Update Frontend UI Hint Text

- Open `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx`
- Update line 264 description text to mention new column formats:

```tsx
<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
  Suba el archivo Excel con el inventario de declaraciones de cambio.
  Debe contener: Cliente, Fecha, Monto, Numero de Declaracion.
</Typography>
```

Change to:

```tsx
<Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
  Suba el archivo Excel con el inventario de declaraciones de cambio.
  Columnas aceptadas: Cliente/Customer Name, Fecha/Parsed Date/Date Folder, Monto/Parsed Amount/Amount Folder, Numero/Declaration Number.
</Typography>
```

- Also update the caption text on line 314:

```tsx
<Typography variant="caption" display="block" sx={{ mt: 1 }}>
  Columnas requeridas: Cliente, Fecha, Monto, Numero DC
</Typography>
```

Change to:

```tsx
<Typography variant="caption" display="block" sx={{ mt: 1 }}>
  Columnas requeridas: Cliente/Customer Name, Fecha/Date Folder, Monto/Amount Folder, Numero DC/Declaration Number
</Typography>
```

### Step 8: Create E2E Test File

- Create `.claude/commands/e2e/test_treasury_declaration_matching_menu.md`
- Test uploading the new scanner format Excel file
- Verify declarations are parsed correctly with the new column names
- Test file: `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/20251215 Diveco Test.xlsx`

### Step 9: Run Validation Commands

- Execute all validation commands to ensure zero regressions
- Fix any issues found during validation

## Testing Strategy

### Unit Tests

- `test_parse_amount_value()`: Test European format `8.111,43` ’ `8111.43`
- `test_parse_amount_value()`: Test US format `$4,862.00` ’ `4862.00`
- `test_parse_amount_value()`: Test plain number `8111.43` ’ `8111.43`
- `test_parse_amount_value()`: Test comma decimal `8111,43` ’ `8111.43`
- `test_find_col_with_priority()`: Test column priority selection

### Edge Cases

1. **Empty declaration numbers**: Handle `NaN` values gracefully (skip row or use empty string)
2. **Mixed formats in same file**: Some rows with `Parsed Amount`, others without
3. **Date format variations**: `01-07-2025` (DD-MM-YYYY) vs `2025-07-01` (YYYY-MM-DD)
4. **Amount format ambiguity**: `1.234` could be European (1234) or US (1.234) - rely on comma presence
5. **Missing optional columns**: `Parsed Date` and `Parsed Amount` may not exist
6. **Extraction failures**: Rows with `Extraction Status = FAILED` should still be processed if `Declaration Number` exists
7. **Float declaration numbers**: `81590.0` should become `"81590"`

## Acceptance Criteria

1. [ ] User can upload Excel file with `Customer Name` column instead of `Cliente`
2. [ ] User can upload Excel file with `Date Folder` column (format `DD-MM-YYYY`)
3. [ ] User can upload Excel file with `Amount Folder` column (European format `8.111,43`)
4. [ ] User can upload Excel file with `Declaration Number` column
5. [ ] User can upload Excel file with `PDF File Name` column
6. [ ] System prefers `Parsed Date` over `Date Folder` when both exist
7. [ ] System prefers `Parsed Amount` over `Amount Folder` when both exist
8. [ ] System correctly parses European amount format to USD decimal
9. [ ] System handles `NaN` declaration numbers gracefully
10. [ ] Frontend UI shows updated column format hints
11. [ ] Existing Spanish column format files still work (backward compatibility)
12. [ ] E2E test passes with the test file `20251215 Diveco Test.xlsx`

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions:

```bash
# Backend validation
cd backend && ruff check src/  # Run backend linting

# Frontend validation
cd frontend && npm run lint  # Run frontend linting
cd frontend && npx tsc --noEmit  # Run TypeScript type check
cd frontend && npm run build  # Run frontend build

# E2E validation
# Read .claude/commands/test_e2e.md
# Execute .claude/commands/e2e/test_treasury_declaration_matching_menu.md
```

## Notes

### European vs US Amount Format Detection

The European format (`8.111,43`) is detected by:
- Contains both `.` and `,`
- Comma appears after the last dot (indicates comma is decimal separator)

The US format (`$4,862.00`) is detected by:
- Contains `$` sign, OR
- Dot appears after commas (indicates dot is decimal separator)

### Backward Compatibility

The extended column variations maintain full backward compatibility:
- Files with Spanish columns (`Cliente`, `Fecha`, `Monto`, `Numero`) still work
- Files with English columns (`Customer`, `Date`, `Amount`, `Number`) still work
- New scanner format files (`Customer Name`, `Date Folder`, etc.) now work

### Test Data

The test file `20251215 Diveco Test.xlsx` contains 9 rows of Diveco SAS declarations with:
- Dates ranging from April 2025 to October 2025
- Amounts ranging from ~$4,000 to ~$18,000 USD
- Some rows with successful extraction (`Declaration Number` populated)
- Some rows with failed extraction (`Declaration Number` = NaN)

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified (N/A - no DB changes)
- [x] E2E test file task included (Step 8)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness (Excel Processing)
- [x] Source Excel columns documented with exact names (10 columns)
- [x] Output Excel structure documented (N/A - parsing input only)
- [x] Data transformation rules specified (date priority, amount format conversion)
- [x] No catalog/lookup dependencies (matching feature)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified (in-memory dict, no database)
- [x] Country-specific handling documented (Colombia-only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy (7 cases)
- [x] E2E test covers happy path with screenshots (Step 8)
