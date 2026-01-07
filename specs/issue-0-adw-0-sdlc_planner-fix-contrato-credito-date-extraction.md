# Chore: Fix Contrato de Crédito Date Extraction in Cotización Parser

## Chore Description
The Solicitud de Desembolso feature is incorrectly extracting the "fecha_contrato_credito" (credit contract date) from Cotización PDFs. Currently, both `fecha_cotizacion` and `fecha_contrato_credito` use the same `_parse_spanish_date` method which simply returns the **first** Spanish date found in the document.

According to the Cotización PDF structure, the first paragraph contains TWO different dates:
1. **Fecha de Cotización de Desembolso**: e.g., "10 de noviembre de 2025" - the date when the quotation was issued
2. **Contrato de Crédito en Pesos de fecha**: e.g., "6 de noviembre de 2025" - the date of the credit contract (highlighted in orange in the screenshot)

The current implementation returns the same date for both fields because `_parse_spanish_date` finds only the first date match. The `fecha_contrato_credito` should specifically extract the date that follows the phrase "Contrato de Crédito en Pesos de fecha".

**Expected behavior**: Extract the date that appears after "Contrato de Crédito en Pesos de fecha" in the first paragraph for `fecha_contrato_credito`.

**Current behavior**: Returns the first date found in the document (the Cotización date) for both fields.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/cotizacion_parser_service.py`**: Main parser service containing `_extract_fecha_contrato_credito()` and `_parse_spanish_date()` methods. This is the primary file to modify.
- **`backend/tests/test_cotizacion_parser_service.py`**: Unit tests for the parser. Need to add/update test cases to verify correct extraction of `fecha_contrato_credito`.
- **`Example FIles for Reqs/Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf`**: Example Cotización PDF for testing. Contains both dates (cotización: 2025-11-10, contrato de crédito: 2025-11-06).
- **`backend/src/interface/legal_dtos.py`**: Contains `CotizacionData` model definition. No changes needed but useful for reference.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Understand the PDF Text Structure
- Read the example Cotización PDF text to understand the exact phrasing used for the credit contract date
- The pattern is: "Contrato de Crédito en Pesos de fecha **6 de noviembre de 2025**"
- Note that the phrase may have variations: "Contrato de Crédito" with or without "en Pesos"

### Step 2: Update `_extract_fecha_contrato_credito` Method
- Open `backend/src/core/servicios/cotizacion_parser_service.py`
- Modify the `_extract_fecha_contrato_credito` method (lines 151-156) to use a context-aware search
- Instead of calling the generic `_parse_spanish_date`, implement a specific pattern that:
  1. Searches for "Contrato de Crédito" followed by optional text and "de fecha"
  2. Captures the Spanish date that immediately follows this phrase
  3. Pattern example: `r'Contrato\s+de\s+Cr[eé]dito.*?de\s+fecha\s+(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'`
- Parse the captured date string into ISO format (YYYY-MM-DD)
- Add fallback to generic `_parse_spanish_date` if specific pattern not found (for backward compatibility)
- Add appropriate logging for debugging

### Step 3: Update `_extract_fecha_cotizacion` Method (if needed)
- Review `_extract_fecha_cotizacion` method to ensure it captures the correct date
- The cotización date appears in the header table "Fecha de Cotización de Desembolso:"
- Consider making this extraction more specific as well (e.g., look for "Fecha de Cotización de Desembolso:" followed by date)
- This ensures both dates are extracted from their proper contexts

### Step 4: Add Helper Method for Spanish Date String Parsing
- Create a new helper method `_parse_spanish_date_string(date_str: str) -> Optional[str]`
- This method takes a Spanish date string like "6 de noviembre de 2025" and returns ISO format "2025-11-06"
- Refactor existing `_parse_spanish_date` to use this helper
- This promotes code reuse and single responsibility

### Step 5: Update Unit Tests
- Open `backend/tests/test_cotizacion_parser_service.py`
- Add new test case `test_parse_cotizacion_fecha_contrato_credito`:
  - Verify `fecha_contrato_credito` equals "2025-11-06" (not "2025-11-10")
  - This is the key validation that the fix works
- Update `test_parse_cotizacion_all_fields` to also assert `fecha_contrato_credito`
- Add test case `test_fecha_contrato_credito_different_from_cotizacion`:
  - Assert `result.fecha_contrato_credito != result.fecha_cotizacion` when dates are different in the PDF

### Step 6: Run Tests and Validate
- Run the unit tests to verify the fix works with the example PDF
- Execute all validation commands to ensure no regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest tests/test_cotizacion_parser_service.py -v` - Run cotización parser tests specifically
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **PDF Text Extraction Quirks**: PyMuPDF extracts text sequentially. The first paragraph containing both dates will have them extracted in order of appearance. The current implementation's `re.finditer` finds ALL dates but only returns the first one.

2. **Pattern Flexibility**: The regex pattern for "Contrato de Crédito" should handle variations:
   - "Contrato de Crédito en Pesos de fecha"
   - "Contrato de Crédito de fecha" (without "en Pesos")
   - Case insensitivity for accent marks: "Crédito" vs "Credito"

3. **Backward Compatibility**: The fallback mechanism ensures that if the specific pattern isn't found, the system still works (returns first date found) rather than failing completely.

4. **Test Data**: The example PDF `Quotation CO90043638912DOM SAFETY  PUERTO 10112025.pdf` has:
   - Fecha de Cotización de Desembolso: 10 de noviembre de 2025 (2025-11-10)
   - Contrato de Crédito en Pesos de fecha: 6 de noviembre de 2025 (2025-11-06)

5. **No Frontend Changes Required**: This is purely a backend parser fix. The frontend already displays whatever dates the backend returns.
