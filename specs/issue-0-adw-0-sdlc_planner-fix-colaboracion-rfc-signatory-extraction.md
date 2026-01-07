# Chore: Fix RFC and Signatory Extraction for Colaboración Contracts

## Chore Description

When the contract type is "Colaboración", the system extracts Finkargo's RFC and signatory name instead of the Broker's. The contract signature section has two columns:
- **Left (FINKARGO)**: Alma Angélica Guzmán Martínez, RFC No. GUMA790902MR2, Representante Legal
- **Right (FREELANCE)**: Samuel Orval Vera de Luna, RFC VELS720821EL1, Por su propio derecho

The current extraction logic finds the first RFC in the document (Finkargo's RFC) rather than the broker/freelance RFC. For COLABORACIÓN contracts specifically, the system needs to:
1. Extract the RFC from the **FREELANCE** column (right side) - the broker's RFC
2. Extract the signatory name from the **FREELANCE** column (right side) - the broker's name

## Relevant Files

Use these files to resolve the chore:

- **`backend/src/core/servicios/broker_incentive_extractor.py`** - Contains the `BrokerIncentiveExtractor` class with `extract_signatory_info()` method (lines 508-541) that extracts RFC and signatory name. The RFC patterns (lines 106-112) and signatory patterns (lines 116-123) need to be extended for COLABORACIÓN contracts.

- **`backend/src/interface/broker_incentive_dtos.py`** - Contains the `SignatoryInfo` dataclass used to return extracted signatory information. No changes needed here.

- **`backend/tests/test_broker_incentive_extraction.py`** - Contains unit tests for broker incentive extraction. New tests need to be added to validate COLABORACIÓN-specific RFC and signatory extraction.

## Step by Step Tasks

### Step 1: Add COLABORACIÓN-Specific RFC and Signatory Patterns

Add new regex patterns specifically for COLABORACIÓN contract format in `broker_incentive_extractor.py`:

- Add `COLABORACION_RFC_PATTERNS` list to extract RFC from the FREELANCE column:
  - Pattern to match "FREELANCE" followed by signature info and RFC
  - Pattern to match RFC that appears after "Por su propio derecho" (indicates freelance/broker)
  - Pattern to extract RFC on the right side of the signature block (after "FINKARGO" section ends)

- Add `COLABORACION_SIGNATORY_PATTERNS` list to extract signatory name from FREELANCE column:
  - Pattern to match name appearing under "FREELANCE" header
  - Pattern to match name appearing before "RFC VELS..." format
  - Pattern to match name above "Por su propio derecho"

### Step 2: Create Specialized COLABORACIÓN Signatory Extraction Method

Add a new method `_extract_colaboracion_signatory_info()` to handle the specific signature block structure:

- The method should:
  1. Identify the signature section (look for "FINKARGO" and "FREELANCE" headers)
  2. Parse the FREELANCE column specifically to extract:
     - Name (appears right after "FREELANCE," header or above RFC)
     - RFC (appears as "RFC [XXXX...]" after the name)
  3. Return `SignatoryInfo(name=broker_name, rfc=broker_rfc)`

### Step 3: Update extract_signatory_info to Route COLABORACIÓN Contracts

Modify the `extract_signatory_info()` method to accept an optional `contract_type` parameter:

- Add `contract_type: Optional[ContractType] = None` parameter
- If `contract_type == ContractType.COLABORACION`:
  - Call `_extract_colaboracion_signatory_info(text)` first
  - Only fall back to generic extraction if COLABORACIÓN-specific fails
- For other contract types, use existing logic

### Step 4: Update extract_from_pdf to Pass Contract Type

Update the `extract_from_pdf()` method to pass the identified contract type to `extract_signatory_info()`:

- Change line 268 from:
  ```python
  signatory_info = self.extract_signatory_info(text)
  ```
- To:
  ```python
  signatory_info = self.extract_signatory_info(text, contract_type)
  ```

### Step 5: Add Unit Tests for COLABORACIÓN RFC/Signatory Extraction

Add new tests to `test_broker_incentive_extraction.py`:

- `test_extract_colaboracion_rfc_from_freelance_column` - Verify RFC is extracted from FREELANCE side
- `test_extract_colaboracion_signatory_from_freelance_column` - Verify name is extracted from FREELANCE side
- `test_extract_colaboracion_signatory_info_complete` - Verify both name and RFC extracted correctly
- `test_extract_colaboracion_signatory_excludes_finkargo_rfc` - Verify Finkargo's RFC is NOT extracted
- `test_extract_colaboracion_signatory_excludes_finkargo_name` - Verify Finkargo's representative name is NOT extracted

Sample test data should include the signature block format:
```text
FINKARGO,                                       FREELANCE,

DocuSigned by:                                  DocuSigned by:
Angélica Guzmán                                 [Broker Signature]

Alma Angélica Guzmán Martínez                   Samuel Orval Vera de Luna
RFC No. GUMA790902MR2                           RFC VELS720821EL1
Representante Legal                             Por su propio derecho
```

### Step 6: Run Validation Commands

Execute all validation commands to ensure zero regressions:

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - Run broker incentive tests
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - Run broker incentive extraction tests
- `cd backend && python -m pytest` - Run all backend tests
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **Signature Block Structure**: COLABORACIÓN contracts have a two-column signature block at the end of the document:
   - Left column: Finkargo representative (Alma Angélica Guzmán Martínez, RFC GUMA790902MR2)
   - Right column: Freelance/Broker (varies per contract)

2. **Key Identifiers for FREELANCE Column**:
   - Header text: "FREELANCE," (note the comma)
   - Footer text: "Por su propio derecho" (indicates the broker is signing for themselves)
   - RFC format: "RFC VELS720821EL1" (RFC followed by space, then the RFC value)

3. **Key Identifiers for FINKARGO Column (to exclude)**:
   - Header text: "FINKARGO,"
   - Footer text: "Representante Legal"
   - RFC format: "RFC No. GUMA790902MR2" (includes "No." which can help differentiate)

4. **Pattern Priority**: For COLABORACIÓN contracts, the COLABORACIÓN-specific patterns should be tried FIRST before falling back to generic patterns. This ensures we don't accidentally pick up Finkargo's data.

5. **No Frontend Changes Required**: This is a backend-only fix affecting data extraction logic. The frontend display components will automatically show the correct data once the backend extracts it properly.
