# Bug: Cotización PDF Parser Fails to Extract Anexo Table Data

## Bug Description
When uploading a Cotización PDF document in the "Solicitud de Desembolso" feature under Paga Local, the system returns an error:

```
Error al extraer datos del PDF: Error parsing Cotización document: Error parsing Cotización PDF:
1 validation error for CotizacionData monto_total Value error, monto_total must be greater than 0
[type=value_error, input_value=Decimal('0'), input_type=Decimal]
```

The `monto_total` is calculated as `Decimal('0')` because no `anexo_items` are being extracted from the PDF, despite the PDF containing valid table data with three payment items totaling COP 739,860.

**Expected behavior**: The parser should extract 3 items from Anexo I:
1. Entidad de pago de Impuestos - 1003887257 - COP 407,001.00
2. Entidad de pago de Impuestos - 1003887254 - COP 290,000.00
3. Entidad de pago de Impuestos - 1003887815 - COP 42,859.00

**Actual behavior**: Zero items are extracted, resulting in `monto_total = 0`, which fails Pydantic validation.

## Problem Statement
The `_extract_anexo_table` method in `CotizacionParserService` fails to parse the Anexo I table because:

1. **Wrong "Anexo I" match position**: The text "Anexo I" appears twice in the document - first as "Anexo I de la presente Cotización" in the body text (page 1), and then as the actual table heading at the END of page 3. The parser finds the first occurrence and starts parsing from there, completely missing the actual table data.

2. **Multi-line table cell extraction**: PyMuPDF extracts table cells on separate lines:
   ```
   Line 3: 'Entidad de pago de Impuestos'
   Line 4: '1003887257'
   Line 5: ' COP                                                                         407.001,00 '
   ```
   But the current regex `([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+(\d+)\s+\$?\s?([\d,\.]+)` expects all three columns on a SINGLE line.

3. **Empty row matching**: The regex matches empty rows like "0 0  COP -" extracting `monto='0'`, which fails validation and is skipped, but no valid rows are matched.

## Solution Statement
Fix the `_extract_anexo_table` method to:

1. **Search for the table section on Page 3 specifically** or search for the last occurrence of "Anexo I" / "ANEXO I" in the document, which is the actual table heading.

2. **Parse multi-line table structure**: Process lines sequentially in groups of 3 (acreedor, numero_instrumento, monto) or detect the table structure by looking for lines containing "COP" amounts.

3. **Improve amount parsing**: Handle Colombian currency format (COP prefix, spaces, periods as thousands separators, commas as decimal separators).

## Steps to Reproduce
1. Navigate to http://localhost:5173 and log in with operations role
2. Go to "Paga Local" > "Solicitud de Desembolso" (or equivalent navigation path)
3. Upload the PDF file: `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`
4. Observe the error: "Error al extraer datos del PDF: Error parsing Cotización document..."

## Root Cause Analysis
The parsing logic has two fundamental issues:

### Issue 1: Wrong starting position for table parsing
```python
# Line 258-267 in cotizacion_parser_service.py
anexo_pattern = r'Anexo\s+I'
anexo_match = re.search(anexo_pattern, text, re.IGNORECASE)
...
anexo_start = anexo_match.end()
anexo_text = text[anexo_start:anexo_start + 5000]  # Parses from first match
```

The first match is at position ~3742 (page 1 body text), but the actual table is at the END of the document (page 3, around position ~5500+). This means `anexo_text` contains the wrong section.

### Issue 2: Single-line regex expectation
```python
# Line 283 in cotizacion_parser_service.py
row_pattern = r'([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)\s+(\d+)\s+\$?\s?([\d,\.]+)'
```

This pattern expects: `"Entidad de pago 1003887257 407.001,00"` on ONE line.

But PyMuPDF extracts as SEPARATE lines:
```
"Entidad de pago de Impuestos"
"1003887257"
" COP                                                                         407.001,00 "
```

### Issue 3: Amount format mismatch
The amount format in the PDF is ` COP                              407.001,00 ` with:
- "COP" prefix (not "$")
- Large whitespace padding
- Period as thousands separator (407.001)
- Comma as decimal separator (,00)

The current regex `\$?\s?([\d,\.]+)` doesn't properly handle the "COP" prefix pattern.

## Affected Layer
- [x] Backend: core/servicios (business logic)

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/cotizacion_parser_service.py` - Main file requiring fixes. Contains `_extract_anexo_table` method that needs to be rewritten to handle multi-line table extraction and proper "Anexo I" section detection.

- `backend/src/interface/legal_dtos.py` - Contains `AnexoItem` and `CotizacionData` models with validators. No changes needed, but helpful for understanding the expected data structure.

- `backend/src/adapter/rest/operations_routes.py` - Contains the `/contracts/solicitud-desembolso/parse-cotizacion` endpoint. No changes needed, but helpful for understanding the API flow.

- `Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf` - Test file to validate the fix.

### New Files
- `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` - New E2E test file to validate the Cotización PDF upload and parsing works correctly.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Understand the current implementation
- Read `backend/src/core/servicios/cotizacion_parser_service.py` fully
- Read `backend/src/interface/legal_dtos.py` to understand `AnexoItem` and `CotizacionData` models
- Run the existing parser with debug output to confirm the issue

### 2. Fix the Anexo I section detection
- Modify `_extract_anexo_table` to search for the LAST occurrence of "Anexo I" or "ANEXO I" in the document (this is the actual table heading at the end of page 3)
- Alternative approach: Search specifically for "ANEXO I" (uppercase, as it appears as a heading) to differentiate from inline references
- Add logging to confirm the correct section is being located

### 3. Implement multi-line table parsing
- Replace single-line regex with line-by-line sequential parsing
- Detection strategy:
  1. After finding the correct "ANEXO I" heading, process lines in the section
  2. Look for lines matching the header pattern: "Acreedor del Gasto Nacional de Importación"
  3. Parse subsequent lines in groups:
     - Line with text only (acreedor name): `Entidad de pago de Impuestos`
     - Line with digits only (instrument number): `1003887257`
     - Line containing "COP" and amount: ` COP 407.001,00 `
  4. Skip empty rows where acreedor is "0" and monto is "-"

### 4. Fix the currency amount parsing
- Handle Colombian format: `COP 407.001,00`
  - Strip "COP" prefix
  - Remove whitespace padding
  - Convert period thousands separators to nothing
  - Convert comma decimal separator to period (for Decimal parsing)
- Create helper method `_parse_cop_amount(amount_str: str) -> Decimal`
- Handle edge cases: empty amounts ("-"), zero amounts ("0")

### 5. Add comprehensive logging
- Log when "ANEXO I" section is found and its position
- Log each extracted row for debugging
- Log the total count and sum before returning

### 6. Write unit tests
- Create test file `backend/tests/test_cotizacion_parser.py` (if not exists)
- Test case 1: Parse the sample PDF and verify 3 items extracted with correct values
- Test case 2: Verify total equals COP 739,860
- Test case 3: Verify parser handles PDFs with no Anexo I gracefully
- Test case 4: Verify parser handles empty table rows correctly

### 7. Create E2E test file
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand the E2E test format
- Create `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` with steps to:
  1. Log in with operations role
  2. Navigate to Solicitud de Desembolso form
  3. Upload the test Cotización PDF
  4. Verify the form is populated with extracted data
  5. Verify the 3 Anexo items are displayed correctly
  6. Verify total amount shows COP 739,860

### 8. Run validation commands
- Execute all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Test the parser directly with the sample PDF
cd backend && source venv/bin/activate && python3 << 'EOF'
from src.core.servicios.cotizacion_parser_service import CotizacionParserService

pdf_path = "../Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf"
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

parser = CotizacionParserService()
result = parser.parse_cotizacion(pdf_bytes)

print(f"Numero Cotizacion: {result.numero_cotizacion}")
print(f"Total Items: {len(result.anexo_items)}")
print(f"Monto Total: {result.monto_total}")
for item in result.anexo_items:
    print(f"  - {item.acreedor}: {item.numero_instrumento} -> {item.monto}")

# Assertions
assert len(result.anexo_items) == 3, f"Expected 3 items, got {len(result.anexo_items)}"
assert result.monto_total == 739860, f"Expected 739860, got {result.monto_total}"
print("\nAll assertions passed!")
EOF
```

```bash
# Run backend tests
cd backend && python -m pytest tests/ -v
```

```bash
# Run backend linting
cd backend && ruff check src/
```

```bash
# Run frontend linting (no changes expected, but validate no regressions)
cd frontend && npm run lint
```

```bash
# Run TypeScript type check (no changes expected, but validate no regressions)
cd frontend && npx tsc --noEmit
```

```bash
# Run frontend build (no changes expected, but validate no regressions)
cd frontend && npm run build
```

- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test file `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` to validate the PDF upload functionality works end-to-end.

## Notes

1. **PDF Structure Insight**: The sample PDF is a "Cotización de Desembolso" document with a specific structure where "ANEXO I" appears as a standalone heading at the very end of page 3, followed by the table data. The table header row ("Acreedor del Gasto Nacional de Importación", "No. de Instrumento de Pago", "Monto del Instrumento de Pago") appears first, then data rows.

2. **PyMuPDF Table Extraction**: PyMuPDF's `get_text()` method extracts text line-by-line based on the PDF's internal structure. For tables, this often means cells are extracted on separate lines. An alternative approach could use `page.find_tables()` or `get_text("blocks")` for more structured extraction, but the line-by-line approach should work if implemented correctly.

3. **Colombian Currency Format**: Colombian pesos use periods (.) as thousands separators and commas (,) as decimal separators. The amount "407.001,00" means 407,001.00 COP. The parser must handle this correctly when converting to Decimal.

4. **Empty Rows in Table**: The PDF contains many empty rows in the table (shown as "0 | 0 | COP -"). These should be detected and skipped during parsing.

5. **No new libraries required**: The fix uses existing PyMuPDF (fitz) and standard library (re, decimal) - no new dependencies needed.
