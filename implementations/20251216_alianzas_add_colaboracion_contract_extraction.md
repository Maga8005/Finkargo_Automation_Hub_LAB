# Implementation: Add COLABORACIÓN Contract Format Extraction

**Date:** 2025-12-16
**Module:** Alianzas (Broker Incentive Extraction)
**Plan:** `specs/issue-0-adw-0-sdlc_planner-add-colaboracion-contract-extraction.md`

## Summary

Added support for extracting incentive data from "CONTRATO DE COLABORACIÓN" (Collaboration Contract) format. This contract type uses a different structure than the previously supported "Bono" and "Incentivos" formats, with incentives defined in "ARTÍCULO III INCENTIVOS" and "Sección 3.01".

## Changes Made

### Backend Changes

- **Added `COLABORACION` contract type to DTOs** (`broker_incentive_dtos.py`)
  - New enum value `ContractType.COLABORACION = "colaboracion"`

- **Added contract type detection patterns** (`broker_incentive_extractor.py`)
  - `CONTRACT_TYPE_COLABORACION_INDICATORS`: Patterns to identify COLABORACIÓN contracts
    - `CONTRATO DE COLABORACIÓN` title
    - `ARTÍCULO III INCENTIVOS` section header
    - `Sección 3.01 Descripción` subsection

- **Added incentive extraction patterns** (`broker_incentive_extractor.py`)
  - `COLABORACION_OPERATIONS_PATTERNS`: Patterns to extract operations incentive percentages from text like "Finkargo reconocerá un incentivo equivalente al cero punto cero siete por ciento (0.07%)"
  - `COLABORACION_CREDIT_LINE_PATTERNS`: Patterns for credit line incentives (optional in this contract type)

- **Updated contract type detection logic** (`broker_incentive_extractor.py`)
  - Added COLABORACIÓN score calculation in `identify_contract_type` method
  - Maintained precedence: BONO > INCENTIVOS > COLABORACION > UNKNOWN

- **Added extraction methods** (`broker_incentive_extractor.py`)
  - `_extract_colaboracion_operations_incentive()`: Extracts operations percentage
  - `_extract_colaboracion_credit_line_incentive()`: Extracts credit line percentage

- **Updated main extraction logic with fallback** (`broker_incentive_extractor.py`)
  - Added handling for `ContractType.COLABORACION` in `extract_from_pdf`
  - Added fallback: If UNKNOWN type and no incentives found, try COLABORACIÓN patterns
  - COLABORACIÓN contracts don't generate warning for missing credit line (expected behavior)

- **Updated Excel generator** (`broker_incentive_excel_generator.py`)
  - Added "Colaboración" display formatting for contract type
  - Added blue styling for COLABORACIÓN contracts in Excel output
  - Added `colaboracion_contracts` count to statistics
  - Added "Contratos Colaboración" row to summary sheet

### Tests Added

- `test_identify_contract_type_colaboracion`: Verifies contract type detection
- `test_extract_operations_colaboracion_format`: Tests 0.07% extraction
- `test_extract_operations_colaboracion_0_10_format`: Tests 0.10% extraction
- `test_extract_operations_colaboracion_0_05_format`: Tests 0.05% extraction
- `test_format_contract_type`: Updated to include COLABORACIÓN
- `test_full_extraction_colaboracion_contract`: Integration test for full contract extraction

## Discrepancies Found

**None.** The plan was accurate and all assumptions were correct.

## Validation Results

All validation commands passed:

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - **41 tests passed**
- `cd backend && ruff check src/` - **All checks passed**
- `cd frontend && npm run lint` - **0 errors** (4 pre-existing warnings unrelated to changes)
- `cd frontend && npx tsc --noEmit` - **No errors**
- `cd frontend && npm run build` - **Build successful**

## Files Changed

```
 backend/src/core/servicios/broker_incentive_excel_generator.py  |  13 ++
 backend/src/core/servicios/broker_incentive_extractor.py        | 130 ++++++++++++
 backend/src/interface/broker_incentive_dtos.py                  |   1 +
 backend/tests/test_broker_incentive_extraction.py               | 137 +++++++++++++
 frontend/src/components/alianzas/FKBrokerContractScanForm.tsx   |   4 +-
 frontend/src/services/brokerIncentiveService.ts                 |   2 +-
 6 files changed, 280 insertions(+), 7 deletions(-)
```

## Affected Brokers

This fix resolves extraction issues for:
- Alan Duran
- Miguel Angel Perez
- Any other brokers using the COLABORACIÓN contract format

## Notes

1. COLABORACIÓN contracts may only have operations incentives (no credit line/apertura). This is expected behavior and no warning is generated for missing credit line in this contract type.

2. The percentage format in COLABORACIÓN contracts typically uses words followed by numeric value in parentheses: e.g., "cero punto cero siete por ciento (0.07%)". The regex patterns capture the numeric value.

3. Fallback logic ensures that if a contract can't be identified as BONO or INCENTIVOS but contains COLABORACIÓN patterns, it will be correctly classified.
