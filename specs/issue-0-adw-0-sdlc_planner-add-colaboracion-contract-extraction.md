# Chore: Add CONTRATO DE COLABORACIÓN Contract Format Extraction

## Chore Description
The broker incentive extraction logic is failing for brokers like "Alan Duran" and "Miguel Angel Perez" with the error: "Could not determine contract type, Credit line incentive not found; Operations incentive not found".

This is because these brokers use a different contract format called "CONTRATO DE COLABORACIÓN" (Collaboration Contract) instead of the previously supported "Bono" or "Incentivos" formats.

The "CONTRATO DE COLABORACIÓN" format has a section called "ARTÍCULO III INCENTIVOS" with subsection "Sección 3.01 Descripción y condiciones para el ejercicio de Incentivos". Within this section:
- Paragraph (a) describes the operations incentive: "Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible"
- This type of contract may only have operations incentive and no credit line (apertura) incentive

The task is to add fallback extraction logic for this contract format when the existing "Anexo A" Bono approach doesn't find any incentives.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/broker_incentive_extractor.py`** - Main extraction logic file. This is where we need to:
  - Add new regex patterns for "CONTRATO DE COLABORACIÓN" format
  - Add new contract type indicator for "COLABORACIÓN"
  - Add fallback extraction methods for the "ARTÍCULO III INCENTIVOS" format
  - Update the extraction logic flow to try "COLABORACIÓN" patterns as fallback

- **`backend/src/interface/broker_incentive_dtos.py`** - DTOs file. We need to:
  - Add a new `ContractType.COLABORACION` enum value

- **`backend/tests/test_broker_incentive_extraction.py`** - Test file. We need to:
  - Add test cases for the "CONTRATO DE COLABORACIÓN" contract format
  - Add tests for the new regex patterns
  - Add tests for the extraction fallback logic

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add COLABORACION Contract Type to DTOs

- Edit `backend/src/interface/broker_incentive_dtos.py`
- Add new enum value `COLABORACION = "colaboracion"` to the `ContractType` enum after `INCENTIVOS`
- This follows the existing pattern and allows the UI/reports to identify this contract type

### Step 2: Add Contract Type Detection Patterns for COLABORACIÓN

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Add a new class constant `CONTRACT_TYPE_COLABORACION_INDICATORS` with patterns:
  - `r'CONTRATO\s+DE\s+COLABORACI[ÓO]N'` - Matches the contract title
  - `r'ART[IÍ]CULO\s+III.*INCENTIVOS'` - Matches the incentives article header
  - `r'Secci[oó]n\s+3\.01.*Descripci[oó]n'` - Matches the section header
- These patterns identify the COLABORACIÓN contract type distinctly from BONO and INCENTIVOS

### Step 3: Add COLABORACIÓN Operations Incentive Extraction Patterns

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Add a new class constant `COLABORACION_OPERATIONS_PATTERNS` with patterns to match text like:
  - "Finkargo reconocerá un incentivo equivalente al cero punto cero siete por ciento (0.07%)"
  - Pattern: `r'Finkargo\s+reconocer[áa]\s+un\s+incentivo\s+equivalente\s+al[^(]*\(([\d.,]+)\s*%\)'`
  - Pattern: `r'incentivo\s+equivalente\s+al[^%]*?([\d.,]+)\s*%\s*\)[^.]*[Oo]peraci[oó]n\s+[Ee]legible'`
  - Pattern: `r'Secci[oó]n\s+3\.01[^%]*?([\d.,]+)\s*%\s*\)[^.]*[Oo]peraci[oó]n'`
- The patterns should capture the percentage value in parentheses (e.g., "(0.07%)")

### Step 4: Add COLABORACIÓN Credit Line Extraction Patterns (Optional Detection)

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Add a new class constant `COLABORACION_CREDIT_LINE_PATTERNS` with patterns to match credit line incentives if present:
  - Pattern for "bono de apertura" or similar within COLABORACIÓN context
  - This may be empty or minimal since COLABORACIÓN contracts may not have credit line incentives
- If no credit line pattern is found in COLABORACIÓN contracts, this is expected behavior

### Step 5: Update Contract Type Detection Logic

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Update the `identify_contract_type` method to:
  - Add score calculation for COLABORACIÓN indicators (similar to existing BONO and INCENTIVOS)
  - Return `ContractType.COLABORACION` if colaboracion_score is highest
  - Maintain precedence: BONO > INCENTIVOS > COLABORACION > UNKNOWN

### Step 6: Add COLABORACIÓN Extraction Methods

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Add new private method `_extract_colaboracion_operations_incentive(self, text: str) -> Optional[float]`:
  - Iterates through `COLABORACION_OPERATIONS_PATTERNS`
  - Extracts and parses the percentage value
  - Returns the first valid match or None
- Add new private method `_extract_colaboracion_credit_line_incentive(self, text: str) -> Optional[float]`:
  - Iterates through `COLABORACION_CREDIT_LINE_PATTERNS`
  - Returns None if no patterns match (expected for many COLABORACIÓN contracts)

### Step 7: Update Main Extraction Logic with Fallback

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Update the `extract_from_pdf` method's extraction logic:
  - After the existing contract type detection and extraction
  - If `contract_type == ContractType.COLABORACION`:
    - Call `_extract_colaboracion_operations_incentive(text)` for operations
    - Call `_extract_colaboracion_credit_line_incentive(text)` for credit line
  - If `contract_type == ContractType.UNKNOWN` and both incentives are None:
    - Try COLABORACIÓN patterns as fallback
    - If any COLABORACIÓN pattern matches, update contract_type to COLABORACION
- This ensures the COLABORACIÓN format is tried when other formats fail

### Step 8: Update Excel Generator Format Display

- Edit `backend/src/core/servicios/broker_incentive_excel_generator.py`
- Update `_format_contract_type` method to handle `ContractType.COLABORACION`:
  - Return "Colaboración" for display in Excel output
- Update `_calculate_statistics` method to count COLABORACIÓN contracts separately if needed

### Step 9: Add Unit Tests for COLABORACIÓN Contract Detection

- Edit `backend/tests/test_broker_incentive_extraction.py`
- Add test case `test_identify_contract_type_colaboracion`:
  - Use sample text with "CONTRATO DE COLABORACIÓN" and "ARTÍCULO III INCENTIVOS"
  - Assert contract type is `ContractType.COLABORACION`

### Step 10: Add Unit Tests for COLABORACIÓN Incentive Extraction

- Edit `backend/tests/test_broker_incentive_extraction.py`
- Add test case `test_extract_operations_colaboracion_format`:
  - Use sample text: "Finkargo reconocerá un incentivo equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible"
  - Assert operations incentive is 0.07
- Add test case `test_extract_operations_colaboracion_0_10_format`:
  - Use sample text with 0.10% value
  - Assert operations incentive is 0.10

### Step 11: Add Integration Test for COLABORACIÓN Contract

- Edit `backend/tests/test_broker_incentive_extraction.py`
- Add test case `test_full_extraction_colaboracion_contract`:
  - Mock `_extract_pdf_text` with full COLABORACIÓN contract text
  - Assert contract_type is COLABORACION
  - Assert operations_incentive_pct is extracted correctly
  - Assert credit_line_incentive_pct is None (expected)
  - Assert warnings include note about missing credit line

### Step 12: Run Validation Commands

- Run all validation commands to ensure zero regressions
- Fix any linting or type errors that arise
- Ensure all tests pass

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - Run broker incentive extraction tests specifically
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **COLABORACIÓN Format Structure**: The "CONTRATO DE COLABORACIÓN" format uses Roman numeral articles (ARTÍCULO III) and numbered sections (Sección 3.01) rather than the (a), (b) bullet format used in Anexo A Bono contracts.

2. **Operations-Only Contracts**: COLABORACIÓN contracts may only specify operations incentives without credit line (apertura) incentives. The code should NOT treat missing credit line as an error for this contract type - it should not add a warning for missing credit line if the contract is identified as COLABORACIÓN.

3. **Percentage in Parentheses**: The COLABORACIÓN format typically writes out the percentage in words followed by the numeric value in parentheses, e.g., "cero punto cero siete por ciento (0.07%)". The regex should capture the numeric value from within the parentheses.

4. **Fallback Priority**: The extraction should try:
   1. BONO patterns (Anexo A format)
   2. INCENTIVOS patterns (Artículo 3 format)
   3. COLABORACIÓN patterns (Artículo III format)
   4. Mark as UNKNOWN if no patterns match

5. **Example Text from Image**:
   ```
   ARTÍCULO III
   INCENTIVOS

   Sección 3.01    Descripción y condiciones para el ejercicio de Incentivos.

   (a)    Para efectos de lo previsto en la Sección 1.01, Finkargo reconocerá un incentivo
   equivalente al cero punto cero siete por ciento (0.07%) sobre el monto de cada Operación Elegible
   ```

6. **Affected Brokers**: This fix will resolve extraction issues for Alan Duran, Miguel Angel Perez, and any other brokers using the COLABORACIÓN contract format.
