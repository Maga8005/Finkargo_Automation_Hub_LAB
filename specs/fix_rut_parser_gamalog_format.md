# Feature: Fix RUT Parser for GAMALOG S.A.S Format

## Feature Description
The RUT parser service (`rut_parser_service.py`) is failing to correctly extract custodian information from certain RUT document formats, specifically the GAMALOG S.A.S RUT (4 RUT COMPLETO 30 07 2024.pdf). The parser is returning incorrect values for the NIT, Legal Representative name, and Legal Representative ID. This feature fix will update the parsing logic to handle this RUT format while maintaining backward compatibility with existing RUT formats that already work correctly.

## User Story
As an Operations team member
I want the RUT parser to correctly extract custodian information from all RUT document formats
So that Inventario Bodega contracts are generated with accurate custodian data without manual intervention

## Problem Statement
The current RUT parser is failing to extract correct values from the GAMALOG S.A.S RUT document:

**Current (Incorrect) Extractions:**
- NIT: Showing file path instead of actual NIT
- Legal Representative Name: Showing "[Image #1]" or incorrect text
- Legal Representative ID: Showing file path instead of actual ID number

**Expected (Correct) Values from RUT:**
- NIT: `900026089-2`
- Legal Representative Name: `GALVIS FRANCO GABRIEL IGNACIO` (first REPRS LEGAL PRIN entry on page 3)
- Legal Representative ID: `73094097`
- Company Name: `GAMALOG S.A.S`
- City: `Bogotá, D.C.`
- Email: `gerencia.logistica@redgama.com`

The RUT document is a 7-page DIAN document with the standard Colombian RUT format. The parsing strategies in the current implementation are not correctly handling the specific text layout and spacing patterns in this document.

## Solution Statement
Update the RUT parser service extraction methods to:

1. **Improve NIT extraction (`_extract_nit_with_dv`)**: Handle different text layouts where NIT digits may be formatted differently
2. **Improve Legal Rep Name extraction (`_extract_legal_rep_name`)**: Better pattern matching for the REPRS LEGAL PRIN section on page 3, correctly extracting fields 104-107 (GALVIS FRANCO GABRIEL IGNACIO)
3. **Improve Legal Rep ID extraction (`_extract_legal_rep_id`)**: Handle cases where the ID number `73094097` is formatted with different spacing patterns
4. **Add fallback strategies**: Implement additional regex patterns as fallbacks when primary strategies fail
5. **Maintain backward compatibility**: Ensure existing RUT formats (like APPLIK LOGISTICS) continue to parse correctly

## Relevant Files
Use these files to implement the feature:

### Backend - Core Service (MODIFY)
- **`backend/src/core/servicios/rut_parser_service.py`** - The main RUT parsing service containing all extraction logic
  - `_extract_nit_with_dv()` method (lines 354-409) - Needs additional patterns for NIT extraction
  - `_extract_legal_rep_name()` method (lines 441-521) - Needs improved pattern matching for representative name
  - `_extract_legal_rep_id()` method (lines 523-617) - Needs additional strategies for ID extraction
  - `_extract_razon_social()` method (lines 157-227) - May need adjustments for company name
  - `_extract_city()` method (lines 229-352) - May need adjustments for city extraction

### Test Files (VERIFY/CREATE)
- **`backend/tests/test_rut_parser_service.py`** - Add tests for GAMALOG RUT format

### Reference Documents
- **`/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf`** - The problematic RUT document (GAMALOG S.A.S)

### New Files
None - This is a bug fix modifying existing code.

## Implementation Plan

### Phase 1: Analysis and Debugging
**Objective**: Understand exactly why the current parser fails for GAMALOG RUT

1. Add debug logging to capture raw text extraction from each page
2. Compare text structure between GAMALOG RUT and working RUT documents
3. Identify specific patterns that differ between RUT formats
4. Document the exact text patterns for GAMALOG fields

### Phase 2: Core Implementation - Parser Fixes
**Objective**: Update extraction methods with improved pattern matching

1. Update `_extract_nit_with_dv()` with additional patterns for NIT extraction
2. Update `_extract_legal_rep_name()` to handle GAMALOG page 3 structure
3. Update `_extract_legal_rep_id()` with improved strategies for ID extraction
4. Add fallback strategies that try multiple patterns before failing
5. Improve robustness of existing strategies

### Phase 3: Testing and Validation
**Objective**: Ensure both GAMALOG and existing RUT formats parse correctly

1. Test GAMALOG RUT extraction with all 7 fields
2. Test APPLIK LOGISTICS RUT (if available) to ensure no regression
3. Add unit tests for both RUT format variants
4. Run end-to-end contract generation test

## Step by Step Tasks

### Step 1: Debug GAMALOG RUT Text Extraction
- Open Python shell in backend directory
- Load the GAMALOG RUT PDF using PyMuPDF
- Extract text from all pages and analyze structure
- Identify exact text patterns for NIT, Legal Rep Name, and Legal Rep ID
- Compare with expected parsing patterns in current code
```python
import fitz
with open('/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
    doc = fitz.open(stream=f.read(), filetype="pdf")
    # Print page 1 text (NIT, company name, email, city)
    print("=== PAGE 1 ===")
    print(doc[0].get_text())
    # Print page 3 text (Legal representative info)
    print("=== PAGE 3 ===")
    print(doc[2].get_text())
```

### Step 2: Update NIT Extraction (`_extract_nit_with_dv`)
- Open `backend/src/core/servicios/rut_parser_service.py`
- Locate `_extract_nit_with_dv()` method (lines 354-409)
- Add new strategy for GAMALOG-style NIT format:
  - Look for pattern after "5. Número de Identificación Tributaria (NIT)"
  - Extract space-separated digits: "9 0 0 0 2 6 0 8 9"
  - Extract DV from field 6: "2"
  - Combine as "900026089-2"
- Add alternative pattern to search for digit sequences near "6. DV" label
- Ensure existing pattern still works for other RUT formats
- Add detailed logging for debugging

### Step 3: Update Legal Rep Name Extraction (`_extract_legal_rep_name`)
- Locate `_extract_legal_rep_name()` method (lines 441-521)
- Analyze GAMALOG page 3 structure:
  - "REPRS LEGAL PRIN 1 8" header
  - Fields 104-107 contain: GALVIS, FRANCO, GABRIEL, IGNACIO
- Add new extraction strategy:
  - Find "REPRS LEGAL PRIN" section
  - Look for pattern: lines containing single capitalized words in sequence
  - Extract 4 name parts from fields 104 (GALVIS), 105 (FRANCO), 106 (GABRIEL), 107 (IGNACIO)
  - Combine in correct order: "GALVIS FRANCO GABRIEL IGNACIO"
- Add fallback strategy using line-by-line scanning after field labels
- Preserve existing strategies for other RUT formats

### Step 4: Update Legal Rep ID Extraction (`_extract_legal_rep_id`)
- Locate `_extract_legal_rep_id()` method (lines 523-617)
- Analyze GAMALOG ID format on page 3:
  - ID appears as "7 3 0 9 4 0 9 7" (space-separated digits)
  - Located after "Cédula de Ciudadaní" type indicator
- Add new strategy:
  - After finding "REPRS LEGAL PRIN", locate "Cédula de Ciudadan"
  - Find next line with space-separated digits (7-10 digits)
  - Remove spaces: "73094097"
- Improve pattern to handle multiple space formats
- Add validation: ID should be 7-10 digits for Colombian cédula

### Step 5: Test GAMALOG RUT Parsing
- Create Python test script to validate parsing:
```python
from src.core.servicios.rut_parser_service import RUTParserService

with open('/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
    rut_bytes = f.read()

parser = RUTParserService()
custodian_data = parser.parse_rut_pdf(rut_bytes)

# Verify all fields
assert custodian_data.nombre_operador_custodio == "GAMALOG S.A.S", f"Got: {custodian_data.nombre_operador_custodio}"
assert custodian_data.ciudad_domicilio_custodio == "Bogotá, D.C.", f"Got: {custodian_data.ciudad_domicilio_custodio}"
assert custodian_data.nit_operador_custodio == "900026089-2", f"Got: {custodian_data.nit_operador_custodio}"
assert custodian_data.nombre_representante_legal_custodio == "GALVIS FRANCO GABRIEL IGNACIO", f"Got: {custodian_data.nombre_representante_legal_custodio}"
assert custodian_data.email_operador_custodio == "gerencia.logistica@redgama.com", f"Got: {custodian_data.email_operador_custodio}"
assert custodian_data.cc_representante_legal_custodio == "73094097", f"Got: {custodian_data.cc_representante_legal_custodio}"
print("✓ All GAMALOG RUT fields extracted correctly!")
```

### Step 6: Test Backward Compatibility
- If APPLIK LOGISTICS RUT is available, test it still parses correctly
- Run existing unit tests if available
- Verify no regression in other RUT parsing

### Step 7: Add Unit Tests for Both Formats
- Open or create `backend/tests/test_rut_parser_service.py`
- Add test case for GAMALOG RUT format:
```python
def test_parse_gamalog_rut():
    """Test parsing GAMALOG S.A.S RUT format"""
    with open('Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
        rut_bytes = f.read()

    parser = RUTParserService()
    result = parser.parse_rut_pdf(rut_bytes)

    assert result.nombre_operador_custodio == "GAMALOG S.A.S"
    assert result.nit_operador_custodio == "900026089-2"
    assert result.nombre_representante_legal_custodio == "GALVIS FRANCO GABRIEL IGNACIO"
    assert result.cc_representante_legal_custodio == "73094097"
```

### Step 8: Run Full Test Suite
- Execute: `cd backend && pytest tests/test_rut_parser_service.py -v`
- Verify all tests pass
- Fix any failures

### Step 9: End-to-End Validation
- Start backend server: `cd backend && python -m uvicorn main:app --reload`
- Start frontend server: `cd frontend && npm run dev`
- Upload GAMALOG RUT for Inventario Bodega contract
- Verify contract generates with correct custodian data
- Download and check PDF for correct field values

## Testing Strategy

### Unit Tests
- Test `_extract_nit_with_dv()` with GAMALOG format (NIT: 900026089-2)
- Test `_extract_legal_rep_name()` with GAMALOG format (GALVIS FRANCO GABRIEL IGNACIO)
- Test `_extract_legal_rep_id()` with GAMALOG format (73094097)
- Test full `parse_rut_pdf()` with GAMALOG RUT
- Test backward compatibility with other RUT formats

### Integration Tests
- Upload GAMALOG RUT via API endpoint
- Verify `POST /api/operations/contracts/generate` returns 201 with correct custodian data
- Generate Inventario Bodega contract with GAMALOG RUT

### Edge Cases
- Test with RUT where Legal Rep has only 3 name parts (missing "Otros nombres")
- Test with RUT where spacing varies in NIT digits
- Test with RUT where ID number has different digit count (7-10 digits)
- Test with multiple legal representatives (should get first REPRS LEGAL PRIN)

## Acceptance Criteria

1. **NIT Extraction**: Parser correctly extracts NIT `900026089-2` from GAMALOG RUT
2. **Legal Rep Name**: Parser correctly extracts `GALVIS FRANCO GABRIEL IGNACIO` from GAMALOG RUT
3. **Legal Rep ID**: Parser correctly extracts `73094097` from GAMALOG RUT
4. **Company Name**: Parser correctly extracts `GAMALOG S.A.S` from GAMALOG RUT
5. **City**: Parser correctly extracts `Bogotá, D.C.` from GAMALOG RUT
6. **Email**: Parser correctly extracts `gerencia.logistica@redgama.com` from GAMALOG RUT
7. **Backward Compatibility**: Other RUT formats (APPLIK LOGISTICS, etc.) continue to parse correctly
8. **No Regressions**: Existing Inventario Bodega contract generation workflow unchanged
9. **Unit Tests**: All RUT parser tests pass
10. **End-to-End**: Contract generated with GAMALOG RUT contains correct custodian data in PDF

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

### Debug RUT Text Extraction
```bash
cd backend && python3 -c "
import fitz
with open('../Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
    doc = fitz.open(stream=f.read(), filetype='pdf')
    print('=== PAGE 1 TEXT ===')
    print(doc[0].get_text()[:2000])
    print('=== PAGE 3 TEXT ===')
    print(doc[2].get_text()[:2000])
"
```

### Test GAMALOG RUT Parsing
```bash
cd backend && python3 -c "
from src.core.servicios.rut_parser_service import RUTParserService
with open('../Example FIles for Reqs/4 RUT COMPLETO 30 07 2024.pdf', 'rb') as f:
    rut_bytes = f.read()
parser = RUTParserService()
try:
    result = parser.parse_rut_pdf(rut_bytes)
    print('nombre_operador_custodio:', result.nombre_operador_custodio)
    print('nit_operador_custodio:', result.nit_operador_custodio)
    print('nombre_representante_legal_custodio:', result.nombre_representante_legal_custodio)
    print('cc_representante_legal_custodio:', result.cc_representante_legal_custodio)
    print('ciudad_domicilio_custodio:', result.ciudad_domicilio_custodio)
    print('email_operador_custodio:', result.email_operador_custodio)
except Exception as e:
    print(f'Error: {e}')
"
```

### Run Unit Tests
- `cd backend && pytest tests/test_rut_parser_service.py -v` - Run RUT parser tests
- `cd backend && pytest tests/ -v` - Run all backend tests for regression check

### Start Backend Server
- `cd backend && python -m uvicorn main:app --reload` - Start server and verify no errors

## Notes

### RUT Document Structure (GAMALOG)
The GAMALOG RUT is a 7-page document with the following structure:
- **Page 1**: Company info (NIT 900026089-2, Razón social: GAMALOG S.A.S, Ciudad: Bogotá, D.C., Email: gerencia.logistica@redgama.com)
- **Page 2**: Organization characteristics
- **Page 3**: Legal representatives (REPRS LEGAL PRIN: GALVIS FRANCO GABRIEL IGNACIO, ID: 73094097)
- **Pages 4-5**: Partners and shareholders
- **Page 6**: Fiscal auditor and accountant
- **Page 7**: Establishments and branches

### Key Differences from Other RUTs
1. **Text spacing**: The GAMALOG RUT may have different spacing patterns in digit sequences
2. **Page structure**: The representative section on page 3 may be formatted differently
3. **Name order**: Name parts appear as separate lines: GALVIS, FRANCO, GABRIEL, IGNACIO

### Implementation Notes
- Use multiple extraction strategies with fallbacks
- Add verbose logging for debugging
- Don't break existing functionality - add new patterns alongside existing ones
- Test thoroughly with both RUT formats before merging

### Related Files
- Implementation document: `implementations/20251110_RUT_Upload_Parsing_Implementation.md`
- Original spec: `specs/20251110_RUT_Upload_And_Parsing_For_Inventario_Bodega.md`
- Legal DTOs: `backend/src/interface/legal_dtos.py` (CustodianData model)
- Operations routes: `backend/src/adapter/rest/operations_routes.py` (RUT upload endpoint)
