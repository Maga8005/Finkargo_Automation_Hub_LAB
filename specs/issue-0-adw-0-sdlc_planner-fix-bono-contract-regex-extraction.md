# Chore: Fix Bono Contract Incentive Extraction Regex Patterns

## Chore Description
The broker incentive extraction logic is failing to extract percentages from certain "Bono" contracts, specifically for customer JOSE MARTIN GASPAR. The contract clearly contains:
- **80%** for "incentivo línea de crédito" (comisión de apertura / Bono Fijo)
- **0.1%** for "incentivo operaciones" (sobre monto de operación elegible / Bono Variable)

The text in the contract reads:
```
(a) Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado a cada Nuevo Cliente por concepto de "Bono de Apertura" en el marco del Contrato de Crédito...
(b) Un Bono equivalente al 0.1% (cero punto uno por ciento) sobre el monto de cada Operación Elegible adelantada por cada Nuevo Cliente durante el Periodo de Pago de Bono Variable...
```

The current regex patterns in `broker_incentive_extractor.py` are too restrictive and fail to match this text because:
1. **Credit Line Pattern Issue**: The first pattern expects "monto colocado|a cliente" but the contract has "monto cobrado a cada Nuevo Cliente"
2. **Operations Pattern Issue**: The patterns expect "operaciones elegibles" together, but the contract has "Operación Elegible adelantada"

The patterns need to be more flexible to handle variations in contract wording while still being precise enough to avoid false positives.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/broker_incentive_extractor.py`** (lines 52-80): Contains the `BONO_CREDIT_LINE_PATTERNS` and `BONO_OPERATIONS_PATTERNS` regex lists that need to be updated to handle the new text variations.
- **`backend/tests/test_broker_incentive_extraction.py`**: Contains tests for the extractor. New test cases should be added to verify the fix works for the JOSE MARTIN GASPAR contract format.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update BONO_CREDIT_LINE_PATTERNS regex patterns
- Open `backend/src/core/servicios/broker_incentive_extractor.py`
- Update the `BONO_CREDIT_LINE_PATTERNS` list (lines 57-66) to include new patterns that match:
  - `Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado...Bono de Apertura`
- Add these new patterns:
  ```python
  # Match "bono equivalente al X% ... del monto cobrado ... Bono de Apertura"
  r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*\([^)]+\)\s*del\s+monto\s+cobrado[^.]*bono\s+de\s+apertura',
  # Match (a) style with percentage followed by "Bono de Apertura" anywhere
  r'\(a\)[^.]*bono\s+equivalente\s+al?\s*([\d.,]+)\s*%[^.]*(?:apertura|bono\s+fijo)',
  # Generic pattern: percentage before "Bono de Apertura" within sentence
  r'([\d.,]+)\s*%\s*\([^)]+\)[^.]*bono\s+de\s+apertura',
  ```

### Step 2: Update BONO_OPERATIONS_PATTERNS regex patterns
- In the same file, update the `BONO_OPERATIONS_PATTERNS` list (lines 71-80) to include new patterns that match:
  - `Un Bono equivalente al 0.1% (cero punto uno por ciento) sobre el monto de cada Operación Elegible adelantada`
- Add these new patterns:
  ```python
  # Match "bono equivalente al X% ... sobre el monto ... Operación Elegible"
  r'bono\s+equivalente\s+al?\s*([\d.,]+)\s*%?\s*\([^)]+\)\s*sobre\s+el\s+monto[^.]*operaci[oó]n\s+elegible',
  # Match (b) style with percentage followed by "Operación Elegible" or "Bono Variable"
  r'\(b\)[^.]*bono\s+equivalente\s+al?\s*([\d.,]+)\s*%[^.]*(?:operaci[oó]n\s+elegible|bono\s+variable)',
  # Generic pattern: percentage before "Operación Elegible" within sentence
  r'([\d.,]+)\s*%\s*\([^)]+\)[^.]*operaci[oó]n\s+elegible',
  ```

### Step 3: Add unit tests for the new patterns
- Open `backend/tests/test_broker_incentive_extraction.py`
- Add new test methods to the `TestBrokerIncentiveExtractor` class (or create if it doesn't exist)
- Add these test cases:
  ```python
  def test_extract_credit_line_jose_martin_gaspar_format(self, extractor):
      """Test extracting credit line from JOSE MARTIN GASPAR contract format."""
      text = '''
      ANEXO A
      ESPECIFICACIONES DEL BONO

      1. Bonos. Para efectos de lo previsto en la Cláusula II del Contrato...

      (a) Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado a cada Nuevo
      Cliente por concepto de "Bono de Apertura" en el marco del Contrato de Crédito, con ocasión
      de la Primera Operación llevada a cabo por parte del Nuevo Cliente en mención (el "Bono Fijo").
      '''
      result = extractor.extract_credit_line_incentive(text)
      assert result == 80.0

  def test_extract_operations_jose_martin_gaspar_format(self, extractor):
      """Test extracting operations from JOSE MARTIN GASPAR contract format."""
      text = '''
      (b) Un Bono equivalente al 0.1% (cero punto uno por ciento) sobre el monto de cada
      Operación Elegible adelantada por cada Nuevo Cliente durante el Periodo de Pago de Bono Variable
      (como dicho término se define en el Numeral 2 del presente Anexo) aplicable respecto de dicho Nuevo
      Cliente (el "Bono Variable").
      '''
      result = extractor.extract_operations_incentive(text)
      assert result == 0.1

  def test_identify_contract_type_anexo_a_format(self, extractor):
      """Test contract type identification for Anexo A format."""
      text = '''
      ANEXO A
      ESPECIFICACIONES DEL BONO

      1. Bonos. Para efectos de lo previsto en la Cláusula II del Contrato...
      (a) Un Bono equivalente al 80% (ochenta por ciento) del monto cobrado...Bono de Apertura
      '''
      result = extractor.identify_contract_type(text)
      assert result == ContractType.BONO
  ```

### Step 4: Run backend tests to verify fix
- Execute `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` to verify all tests pass
- Ensure new tests for JOSE MARTIN GASPAR format pass

### Step 5: Run validation commands
- Execute all validation commands listed below to confirm the fix works with zero regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - Run specific tests for broker incentive extraction
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- The regex patterns should be ordered from most specific to least specific within each list, as the extractor uses the first matching pattern
- The new patterns use `\([^)]+\)` to match the Spanish text in parentheses like "(ochenta por ciento)" which appears after percentages in formal contracts
- Be careful not to be too permissive with patterns to avoid false positives - the patterns should still require the percentage to be near "Bono de Apertura" or "Operación Elegible" context
- Test with actual PDF from `/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/2024` to verify extraction works in practice after the fix
- Consider creating an integration test that scans a known directory and verifies extraction results
