# Feature: Add CSV Upload Support to PA Report

## Feature Description
This feature extends the PA Report Classification feature to accept CSV files in addition to the currently supported Excel formats (.xlsx, .xls). Users often receive NetSuite exports in CSV format, and being able to upload these directly without first converting to Excel will improve workflow efficiency and reduce manual steps.

## User Story
As a Finance user
I want to upload CSV files to the PA Report processing page
So that I can process NetSuite exports in their native format without converting to Excel first

## Problem Statement
The current PA Report feature at `/finance/reporte-pa` only accepts Excel files (.xlsx, .xls) for NetSuite movement uploads. NetSuite frequently exports data as CSV files, forcing users to manually convert these files to Excel before uploading. This adds unnecessary friction to the workflow.

## Solution Statement
Extend the file upload functionality in both the frontend and backend to accept CSV files alongside Excel files. The backend will use pandas' `read_csv()` function with appropriate encoding and delimiter handling to parse CSV files. The frontend will update the file input accept attribute to include `.csv` extension and update helper text to inform users of the new capability.

## Access Control
- Required Role(s): `finance`, `finance_admin`, `admin`
- Backend Protection: Uses `get_current_user` dependency (existing - no changes needed)
- Frontend Protection: Page already protected via route configuration (no changes needed)

## Relevant Files
Use these files to implement the feature:

### Backend Files
- `backend/src/adapter/rest/pa_routes.py` (lines 290-318) - Contains the `/process/upload` endpoint that validates file extension. Need to add `.csv` to accepted extensions.
- `backend/src/core/servicios/pa_report_service.py` (lines 82-200) - Contains `upload_netsuite_file()` method that parses files using pandas. Need to add CSV parsing logic with `pd.read_csv()`.

### Frontend Files
- `frontend/src/pages/finance/ReportePA.tsx` (lines 397-413) - Contains the file input element with `accept=".xlsx,.xls"`. Need to add `.csv` to accepted types.

### E2E Test Reference Files
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_pa_report_classification.md` - Existing PA report E2E test for reference

### New Files
- `.claude/commands/e2e/test_pa_csv_upload.md` - E2E test file to validate CSV upload functionality

## Pre-Implementation Verification

### Feature Category
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D

### C. File Format Specification (Import/Export only)
| Format | Max Size | Required Headers | Validation Rules |
|--------|----------|------------------|------------------|
| CSV | 10MB (same as Excel) | Same as Excel: "Cuenta (línea): Número", "Cuenta (línea): Nombre", "Débito", "Crédito", "Saldo" | Non-empty rows, valid numeric values for Débito/Crédito/Saldo |
| XLSX | 10MB | Same headers | Same validation |
| XLS | 10MB | Same headers | Same validation |

**CSV Parsing Considerations:**
- Encoding: UTF-8 with fallback to latin-1 (common for Spanish text)
- Delimiter: Comma (`,`) with fallback to semicolon (`;`) detection
- Quote character: Double quote (`"`)
- Decimal separator: Period (`.`) - standard for NetSuite exports
- Thousands separator: Comma (`,`) in text fields - must be handled

**Field Mapping (Same for CSV and Excel):**
| Source Column | Internal Name | Required |
|--------------|---------------|----------|
| Cuenta (línea): Número | cuenta_linea_numero | Yes |
| Cuenta (línea): Nombre | cuenta_linea_nombre | Yes |
| Fecha | fecha | No |
| Fecha de creación | fecha_creacion | No |
| Tipo de Transacción | tipo_transaccion | No |
| Tipo de comprobante | tipo_comprobante | No |
| Número de documento | numero_documento | No |
| Entidad | entidad | No |
| Notas | notas | No |
| Débito | debito | Yes |
| Crédito | credito | Yes |
| Saldo | saldo (→ valor_cop) | Yes |
| Moneda: Nombre | moneda_nombre | No |
| Tipo de cambio | tipo_cambio | No |
| Importe (moneda extranjera) | importe_moneda_extranjera (→ valor_usd) | No |

### D. Data Contract Verification (ALL features)
| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| repository.get_all_catalog_accounts() | list[str] | list iteration | `if account in catalog_accounts` |
| repository.create_processing_session() | str (session_id) | direct value | `session_id = await repo.create...` |

**File Extension Validation (Backend):**
```python
# Current (pa_routes.py:305-306):
if not file.filename.endswith((".xlsx", ".xls")):
    raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx o .xls")

# New:
if not file.filename.endswith((".xlsx", ".xls", ".csv")):
    raise HTTPException(status_code=400, detail="Formato no soportado. Use .xlsx, .xls o .csv")
```

### Interface Mapping (Frontend ↔ Backend)
| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| file (File object) | file (UploadFile) | multipart/form-data | No field name changes |

## Implementation Plan

### Phase 1: Foundation
No database or DTO changes required. The existing data structures already handle the parsed data - only the file reading logic needs modification.

### Phase 2: Core Implementation

**Backend Changes:**
1. Update `pa_routes.py` to accept `.csv` extension in file validation
2. Update `pa_report_service.py` to detect file type and use appropriate pandas reader:
   - For `.csv`: Use `pd.read_csv()` with encoding detection
   - For `.xlsx`/`.xls`: Continue using `pd.read_excel()`

**Frontend Changes:**
1. Update `ReportePA.tsx` file input accept attribute to include `.csv`
2. Update helper text to mention CSV support

### Phase 3: Integration
- No integration changes needed - the feature uses existing workflows
- The CSV data will flow through the same cleaning and classification pipeline

## Step by Step Tasks

### Task 1: Create E2E Test File
Create the E2E test file `.claude/commands/e2e/test_pa_csv_upload.md` that validates:
- CSV file can be uploaded successfully
- CSV file is parsed correctly
- Data flows through cleanup and classification steps
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_pa_report_classification.md` for reference

### Task 2: Update Backend Route - File Extension Validation
**File:** `backend/src/adapter/rest/pa_routes.py`
- Locate line 305-306 in `upload_netsuite_file` function
- Update the file extension check to include `.csv`
- Update error message to list `.csv` as accepted format

### Task 3: Update Backend Service - CSV Parsing Logic
**File:** `backend/src/core/servicios/pa_report_service.py`
- Update the `upload_netsuite_file` method (around line 104-106)
- Add logic to detect file extension and choose appropriate pandas reader
- For CSV files:
  - Try UTF-8 encoding first, fallback to latin-1
  - Use comma delimiter with semicolon fallback
  - Handle encoding errors gracefully with clear error messages
- Implement helper method `_parse_file()` to encapsulate file reading logic

### Task 4: Update Frontend - File Input Accept Attribute
**File:** `frontend/src/pages/finance/ReportePA.tsx`
- Locate line 399 with `accept=".xlsx,.xls"`
- Update to `accept=".xlsx,.xls,.csv"`

### Task 5: Update Frontend - Helper Text (Optional Enhancement)
**File:** `frontend/src/pages/finance/ReportePA.tsx`
- Update the step description text (line 89) to mention CSV support
- Current: "Sube el archivo de movimientos de NetSuite"
- Updated: "Sube el archivo de movimientos de NetSuite (Excel o CSV)"

### Task 6: Run Validation Commands
Execute all validation commands to ensure zero regressions and proper functionality.

## Testing Strategy

### Unit Tests
**Backend:** Add test cases to cover CSV parsing:
- Test valid CSV file upload
- Test CSV with UTF-8 encoding
- Test CSV with latin-1 encoding
- Test CSV with semicolon delimiter
- Test invalid CSV (missing required columns)
- Test empty CSV file

### Edge Cases
1. **Encoding Issues:** CSV with special characters (ñ, accents) in Spanish text
2. **Delimiter Detection:** CSV using semicolon (`;`) instead of comma
3. **Large Files:** CSV with 50K+ rows (same as Excel performance requirements)
4. **Empty Files:** CSV with headers but no data rows
5. **Missing Columns:** CSV missing required columns should show clear error
6. **Numeric Formatting:** Numbers with thousand separators in string format

## Acceptance Criteria
1. Users can upload `.csv` files at `/finance/reporte-pa`
2. CSV files are parsed correctly with proper encoding handling
3. CSV data flows through the same cleanup and classification pipeline as Excel
4. Error messages are clear when CSV format is invalid or missing columns
5. File input shows `.csv` as accepted format
6. No regressions to existing Excel upload functionality
7. Processing history correctly shows CSV uploads

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/ -v` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_csv_upload.md` to validate CSV upload functionality works

## Notes

### No New Dependencies Required
- Backend: `pandas` already supports CSV via `pd.read_csv()` - no new packages needed
- Frontend: No new packages needed - only file input attribute changes

### Encoding Detection Strategy
The implementation should try encodings in this order:
1. UTF-8 (most common for modern exports)
2. UTF-8-SIG (UTF-8 with BOM - Windows export)
3. Latin-1/ISO-8859-1 (fallback for legacy Spanish text)

### Delimiter Detection Strategy
Check the first line of the file:
1. If semicolons > commas, use semicolon delimiter
2. Otherwise, use comma delimiter (default)

### Error Message Translations
All error messages should be in Spanish to match the existing application:
- "Archivo CSV vacío o sin filas de datos"
- "Error de codificación en archivo CSV. Asegúrese de usar UTF-8."
- "Formato de archivo no soportado. Use .xlsx, .xls o .csv"

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no migrations needed)
- [x] E2E test file task included
- [x] All external dependencies (npm/pip packages) listed in Notes (N/A - none needed)

### Category-Specific Completeness
**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable (N/A - Colombia only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
