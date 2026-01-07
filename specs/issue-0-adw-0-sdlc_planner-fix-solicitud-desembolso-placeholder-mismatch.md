# Bug: Solicitud de Desembolso Word Document Placeholders Not Filled

## Bug Description
When generating a Solicitud de Desembolso document in the Legal module review workflow, none of the placeholders in the Word document are being filled in with the corresponding data. The generated document shows all placeholders still in place with `[]` characters (e.g., `[Número de cotización de desembolso]`, `[día]`, `[mes]`, `[monto]`, `[número de días de plazo]`).

**Symptoms:**
- All placeholders remain unfilled in the generated Word document
- Data from the contract generation request is not being applied to the template
- The document is unusable for legal review since it contains no actual data

**Expected Behavior:**
- All placeholders should be replaced with the corresponding data from the Solicitud de Desembolso request
- Date fields should show the actual dates in Spanish format
- Financial fields should show formatted amounts
- The Anexo I table should be populated with the payment details

**Actual Behavior:**
- Placeholders remain as-is: `[Número de cotización de desembolso]`, `[día]`, `[mes]`, `[monto]`, etc.
- No data substitution occurs

## Problem Statement
The `_prepare_solicitud_desembolso_replacements()` method in `document_service.py` defines placeholder keys that do not match the actual placeholders in the Word template `FK COL - Fin. COP - Solicitud de Desembolso.docx`.

**Code defines placeholders like:**
- `[NUMERO_COTIZACION_DESEMBOLSO]`
- `[MONTO]`
- `[DIAS_PLAZO]`
- `[FECHA_SOLICITUD]`
- `[FECHA_CONTRATO_CREDITO]`

**Template actually contains:**
- `[Número de cotización de desembolso]`
- `[monto]`
- `[número de días de plazo]`
- `[día]`, `[mes]`, `202[•]` (for request date)
- `[día de firma del contrato de crédito]`, `[mes de firma del contrato de crédito]`, `[ año de firma del contrato de crédito]`

The mismatch between placeholder keys and template placeholders causes the replacement logic to find no matches.

## Solution Statement
Update the `_prepare_solicitud_desembolso_replacements()` method in `document_service.py` to use the exact placeholder strings that exist in the Word template. This requires:

1. Mapping the exact placeholder text from the template to the corresponding data values
2. Handling date components separately (day, month, year) for both solicitud date and contrato credito date
3. Properly formatting financial amounts
4. Ensuring the Anexo I table population method works correctly with the existing table structure

The fix is surgical: only the placeholder mapping dictionary needs to be updated to match the template.

## Steps to Reproduce
1. Login to the application as an Operations user
2. Navigate to Operations → Paga Local Colombia → Solicitud de Desembolso tab
3. Search and select a client by NIT
4. Upload a valid Cotización PDF
5. Click "Extraer Datos" to extract data
6. Fill in required fields (numero cotizacion, fecha contrato, dias plazo)
7. Click "Solicitar Documento" to generate the contract
8. Navigate to Legal module → Review Queue
9. Find the newly created PLSD contract
10. Click to download/preview the Word document
11. **Observe:** All placeholders remain unfilled (e.g., `[monto]`, `[día]`, `[Número de cotización de desembolso]`)

## Root Cause Analysis
The root cause is a **placeholder key mismatch** between the document generation code and the Word template.

**Technical Analysis:**

1. The template `FK COL - Fin. COP - Solicitud de Desembolso.docx` uses Spanish-language, mixed-case placeholders:
   - `[Número de cotización de desembolso]`
   - `[día de firma del contrato de crédito]`
   - `[mes de firma del contrato de crédito]`
   - `[ año de firma del contrato de crédito]` (note: space before "año")
   - `[monto]`
   - `[número de días de plazo]`
   - `[día]` and `[mes]` and `[•]` for current date

2. The code in `_prepare_solicitud_desembolso_replacements()` (lines 1216-1266) uses UPPERCASE_SNAKE_CASE placeholder keys that don't exist in the template:
   ```python
   replacements = {
       '[NUMERO_COTIZACION_DESEMBOLSO]': data.get('numero_cotizacion_desembolso', ''),
       '[FECHA_SOLICITUD]': fecha_solicitud_str,
       '[MONTO]': monto_formatted,
       '[DIAS_PLAZO]': dias_plazo,
       ...
   }
   ```

3. When `generate_solicitud_desembolso_document()` iterates through paragraphs and tables, it calls:
   ```python
   if placeholder in paragraph.text:
       paragraph.text = paragraph.text.replace(placeholder, str(value))
   ```
   Since `[MONTO]` ≠ `[monto]`, no replacements occur.

4. Additionally, the template uses a multi-part date format requiring separate day/month/year placeholders, but the code provides a single formatted date string.

## Affected Layer
- [x] Backend: core/servicios (business logic)
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`backend/src/core/servicios/document_service.py`** - Contains the `_prepare_solicitud_desembolso_replacements()` method (lines 1216-1266) that must be updated to use correct placeholder keys matching the template. Also contains `generate_solicitud_desembolso_document()` method (lines 1156-1214) and `_populate_anexo_table()` method (lines 1268-1312).

- **`backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx`** - The Word template containing the actual placeholder text that must be matched. Reference for exact placeholder strings.

- **`backend/src/adapter/rest/operations_routes.py`** - Contains the endpoint that builds the data snapshot. Verify that all required data fields are present in the snapshot passed to document generation.

- **`backend/src/interface/legal_dtos.py`** - Contains `SolicitudDesembolsoRequest` DTO defining the fields available for document generation.

- **`.claude/commands/test_e2e.md`** and **`.claude/commands/e2e/test_login.md`** - Read these to understand E2E test structure for creating a validation test.

### New Files
- **`.claude/commands/e2e/test_solicitud_desembolso_document_generation.md`** - E2E test file to validate that placeholders are correctly filled in the generated document.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Analyze Template Placeholders
- Read the Word template to extract all exact placeholder strings
- Run the following Python script to list all placeholders:
  ```python
  from docx import Document
  doc = Document('backend/templates/FK COL - Fin. COP - Solicitud de Desembolso.docx')
  placeholders = set()
  for para in doc.paragraphs:
      import re
      found = re.findall(r'\[[^\]]+\]', para.text)
      placeholders.update(found)
  for table in doc.tables:
      for row in table.rows:
          for cell in row.cells:
              found = re.findall(r'\[[^\]]+\]', cell.text)
              placeholders.update(found)
  print(sorted(placeholders))
  ```
- Document the exact placeholder strings for the fix

### Task 2: Update `_prepare_solicitud_desembolso_replacements()` Method
- Open `backend/src/core/servicios/document_service.py`
- Locate the `_prepare_solicitud_desembolso_replacements()` method (around line 1216)
- Replace the placeholder mapping dictionary with the correct keys matching the template:
  ```python
  replacements = {
      # Numero de cotizacion
      '[Número de cotización de desembolso]': data.get('numero_cotizacion_desembolso', ''),

      # Fecha de solicitud (current date) - split into components
      '[día]': str(fecha_solicitud.day),
      '[mes]': self._get_month_name_spanish(fecha_solicitud.month),
      '[•]': str(fecha_solicitud.year)[-1],  # Last digit of year for 202[•]

      # Fecha contrato credito - split into components
      '[día de firma del contrato de crédito]': str(fecha_contrato_dt.day) if fecha_contrato_dt else '',
      '[mes de firma del contrato de crédito]': self._get_month_name_spanish(fecha_contrato_dt.month) if fecha_contrato_dt else '',
      '[ año de firma del contrato de crédito]': str(fecha_contrato_dt.year) if fecha_contrato_dt else '',

      # Financial fields
      '[monto]': monto_formatted,
      '[número de días de plazo]': str(dias_plazo),
  }
  ```
- Parse `fecha_contrato_credito` into a datetime object before extracting day/month/year components
- Ensure the year placeholder includes the space: `[ año de firma del contrato de crédito]`

### Task 3: Fix Date Parsing in the Method
- Update the method to properly parse the fecha_contrato_credito string into a datetime object
- Handle both ISO format (`2025-11-06`) and potential alternative formats
- Extract day, month name (Spanish), and year as separate values
- Add error handling for invalid date formats with logging

### Task 4: Verify Anexo I Table Population
- Review `_populate_anexo_table()` method
- Confirm it correctly identifies Table 1 (index 1) which contains the Anexo I data rows
- The template has rows 2-11 with `[•]` placeholders - these should be replaced or rows should be cleared and repopulated
- Update the method to:
  1. Clear existing placeholder rows (rows with `[•]`)
  2. Add new rows with actual data from `anexo_items`
  3. Add a total row at the end
- Consider using cell-by-cell replacement instead of adding new rows if the table structure must be preserved

### Task 5: Add Logging for Debug Purposes
- Add debug logging to `generate_solicitud_desembolso_document()` to log:
  - The data_snapshot being used
  - The replacements dictionary being applied
  - Number of replacements made per section (paragraphs vs tables)
- This will help troubleshoot future placeholder issues

### Task 6: Write Backend Unit Test
- Create or update `backend/tests/test_document_service.py` to add test:
  ```python
  def test_solicitud_desembolso_placeholders_replaced():
      """Test that Solicitud de Desembolso placeholders are correctly replaced"""
      # Prepare test data
      contract_data = {
          'data_snapshot': {
              'numero_cotizacion_desembolso': 'CO:900436389:1:2:DOM',
              'fecha_contrato_credito': '2025-11-06',
              'monto': 739860.00,
              'dias_plazo': 120,
              'nit': '900436389',
              'nombre_importador': 'Test Company',
              'anexo_items': [
                  {'acreedor': 'Test Acreedor', 'numero_instrumento': '123456', 'monto': 739860.00}
              ]
          }
      }

      # Generate document
      service = DocumentService()
      doc_bytes = service.generate_solicitud_desembolso_document(contract_data)

      # Load generated document and verify no placeholders remain
      from docx import Document
      import io
      doc = Document(io.BytesIO(doc_bytes))

      full_text = ''
      for para in doc.paragraphs:
          full_text += para.text
      for table in doc.tables:
          for row in table.rows:
              for cell in row.cells:
                  full_text += cell.text

      # Verify specific placeholders are replaced
      assert '[Número de cotización de desembolso]' not in full_text
      assert '[monto]' not in full_text
      assert '[número de días de plazo]' not in full_text
      assert '[día de firma del contrato de crédito]' not in full_text

      # Verify data appears in document
      assert 'CO:900436389:1:2:DOM' in full_text
      assert '120' in full_text
  ```
- Run test: `cd backend && python -m pytest tests/test_document_service.py -v -k solicitud_desembolso`

### Task 7: Create E2E Test File
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand E2E test structure
- Create `.claude/commands/e2e/test_solicitud_desembolso_document_generation.md` with the following test:
  - **User Story**: As a Legal reviewer, I want to view a Solicitud de Desembolso document with all data populated so I can approve or reject it
  - **Prerequisites**: Operations user logged in, test client exists (NIT: 900436389), backend/frontend running
  - **Test Steps**:
    1. Login as operations user
    2. Navigate to `/operations/contratos-paga-local-colombia`
    3. Click "Solicitud de Desembolso" tab
    4. Search and select client by NIT
    5. Upload test Cotización PDF
    6. Click "Extraer Datos"
    7. Verify data is extracted
    8. Click "Solicitar Documento"
    9. Verify success message
    10. Login as legal user (or navigate to Legal module)
    11. Navigate to review queue
    12. Find the PLSD contract
    13. Download the Word document
    14. Open and verify placeholders are filled:
        - Verify `[Número de cotización de desembolso]` is replaced with actual quote number
        - Verify `[monto]` is replaced with formatted amount
        - Verify `[día]`, `[mes]` are replaced with current date values
        - Verify `[día de firma del contrato de crédito]` is replaced
    15. Take screenshot of document showing populated fields
  - **Success Criteria**:
    - No `[...]` placeholders remain in the document (except `[•]` for N/A fields)
    - All data from the request appears in the document
    - Anexo I table is populated with payment items

### Task 8: Run Validation Commands
- Execute all validation commands to ensure the fix works with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# 1. Run backend tests specifically for document service
cd backend && python -m pytest tests/test_document_service.py -v

# 2. Run all backend tests to ensure no regressions
cd backend && python -m pytest

# 3. Run backend linting
cd backend && ruff check src/

# 4. Run frontend linting (no frontend changes, but verify)
cd frontend && npm run lint

# 5. Run TypeScript type check
cd frontend && npx tsc --noEmit

# 6. Run frontend build
cd frontend && npm run build
```

**Manual Validation:**
1. Start dev servers: `./scripts/start-dev.sh`
2. Login as Operations user
3. Create a new Solicitud de Desembolso with test data
4. Navigate to Legal review queue
5. Download the generated Word document
6. Open in Word/LibreOffice and verify:
   - `[Número de cotización de desembolso]` → shows actual quote number
   - `[día]`, `[mes]`, `202[•]` → shows current date (e.g., "7 de diciembre de 2025")
   - `[día de firma del contrato de crédito]`, etc. → shows contract credit date
   - `[monto]` → shows formatted amount (e.g., "$739,860.00 COP")
   - `[número de días de plazo]` → shows days (e.g., "120")
   - Anexo I table has populated rows with acreedor, numero_instrumento, monto
7. Stop dev servers: `./scripts/stop-dev.sh`

**E2E Test Validation:**
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_solicitud_desembolso_document_generation.md` test file

## Notes

### Placeholder Reference Table
Based on template analysis, here are all placeholders and their mappings:

| Template Placeholder | Data Source | Format |
|---------------------|-------------|--------|
| `[Número de cotización de desembolso]` | `data.numero_cotizacion_desembolso` | String |
| `[día]` | Current date day | Integer (1-31) |
| `[mes]` | Current date month | Spanish name |
| `202[•]` | Current year last digit | Single digit |
| `[día de firma del contrato de crédito]` | `data.fecha_contrato_credito` day | Integer |
| `[mes de firma del contrato de crédito]` | `data.fecha_contrato_credito` month | Spanish name |
| `[ año de firma del contrato de crédito]` | `data.fecha_contrato_credito` year | 4-digit year |
| `[monto]` | `data.monto` | Currency format |
| `[número de días de plazo]` | `data.dias_plazo` | Integer |
| `[•]` (in Anexo table) | Anexo item fields | Various |

### Important: Placeholder Exact Match
The replacement logic uses exact string matching. Note these details:
- `[ año de firma del contrato de crédito]` has a space before "año"
- `[•]` is used both for year digit and as table cell placeholders
- Some placeholders span multiple cells due to table merge

### No New Dependencies Required
This fix only modifies existing Python code in `document_service.py`. No new packages needed.
