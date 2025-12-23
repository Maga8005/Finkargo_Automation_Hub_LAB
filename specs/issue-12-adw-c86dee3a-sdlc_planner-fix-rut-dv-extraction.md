# Bug: Fix RUT DV (Dígito de Verificación) Extraction in Riesgos Feature

## Bug Description

The DV (dígito de verificación) extraction from RUT documents in the Riesgos (Risk) Document info extraction feature is incorrect. The system should extract the DV from field 6.DV, which is the field immediately following field 5 "Número de Identificación Tributaria (NIT)" with the label "6.DV". For example, in the Azelis RUT, the DV is number 3, but the extraction is returning an incorrect value.

**Symptoms:**
- The DV value extracted from RUT documents does not match the actual 6.DV field in the document
- Cross-validation may incorrectly flag NIT check digit discrepancies

**Expected Behavior:**
- The DV should be extracted from the field labeled "6.DV" which appears directly after field "5. Número de Identificación Tributaria (NIT)"
- The extracted NIT should be in format "XXXXXXXXX-D" where D is the single digit from field 6.DV

**Actual Behavior:**
- The DV is being extracted incorrectly, possibly from a wrong field or incorrectly parsed

## Problem Statement

The LandingAI document extraction schema for RUT documents (`EXTRACTION_SCHEMAS[DocumentType.RUT]`) does not provide explicit guidance to the AI about the exact location and format of the DV field (6.DV). The current schema asks for NIT with description `"NIT with verification digit (fields 5-6)"` but doesn't clearly specify that field 6 is a **separate** field labeled "6.DV" containing a single digit.

## Solution Statement

Improve the RUT extraction schema in `document_extraction_service.py` to:
1. Add a separate `dv` field that explicitly asks for the DV from field 6.DV
2. Provide clearer description about the RUT structure (field 5 contains NIT digits, field 6.DV contains the single verification digit)
3. Update the schema to request both fields separately, then combine them programmatically

Alternatively, enhance the existing `nit` field description to be more explicit about field locations.

## Steps to Reproduce

1. Navigate to the Riesgos module
2. Create a new risk evaluation for a client
3. Upload a RUT document (e.g., Azelis RUT where DV should be 3)
4. Trigger AI extraction for the RUT document
5. Observe that the extracted NIT-DV has an incorrect DV value (not 3)

## Root Cause Analysis

The root cause is in the LandingAI extraction schema definition at `backend/src/core/servicios/risk/document_extraction_service.py`, specifically in the `EXTRACTION_SCHEMAS[DocumentType.RUT]` section.

Current schema (line 112):
```python
"nit": {"type": "string", "description": "NIT with verification digit (fields 5-6)"},
```

This description is ambiguous because:
1. It doesn't specify that field 6 has the label "6.DV"
2. It doesn't specify the location of field 6.DV relative to field 5
3. Colombian RUT documents have the DV in a small field labeled "6.DV" immediately to the right of the NIT field
4. Without explicit guidance, the AI may extract an incorrect value

The fix requires making the schema description more precise about the RUT document structure.

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

- `backend/src/core/servicios/risk/document_extraction_service.py` - **Main file to modify**. Contains the `EXTRACTION_SCHEMAS` dictionary where the RUT schema needs to be updated. The current schema at line 108-140 defines the RUT extraction structure.

- `backend/src/core/servicios/rut_parser_service.py` - Reference for understanding RUT document structure. Shows how the existing text-based RUT parser extracts NIT and DV (field 5 and 6). Look at `_extract_nit_with_dv()` method at line 353 which correctly identifies field 6.DV.

- `backend/src/core/servicios/risk/normalization_service.py` - Reference for understanding how NIT+DV is normalized. The `normalize_nit()` method at line 137 shows expected format handling.

- `backend/src/core/servicios/risk/cross_validation_service.py` - Reference for understanding how NIT and DV are validated across documents. The `_validate_nit_consistency()` method at line 189 validates both base NIT and check digit separately.

- `.claude/commands/test_e2e.md` - Reference for creating E2E test
- `.claude/commands/e2e/test_login.md` - Reference for E2E test file format

### New Files

- `.claude/commands/e2e/test_rut_dv_extraction.md` - New E2E test file to validate RUT DV extraction

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Understand the Current Schema

- Read `backend/src/core/servicios/risk/document_extraction_service.py` lines 108-140 to understand the current RUT schema
- Note how the `nit` field is currently defined with `"NIT with verification digit (fields 5-6)"`

### Step 2: Update RUT Extraction Schema

Modify `backend/src/core/servicios/risk/document_extraction_service.py`:

- Update the `EXTRACTION_SCHEMAS[DocumentType.RUT]` section to improve DV extraction
- Change the `nit` field description to be more explicit:
  ```python
  "nit": {
      "type": "string",
      "description": "NIT with verification digit. Field 5 contains the 9-digit NIT number (labeled '5. Número de Identificación Tributaria (NIT)'). Immediately after field 5, there is a small field labeled '6.DV' containing a single digit which is the verification digit (dígito de verificación). Extract as 'XXXXXXXXX-D' format where D is the digit from field 6.DV. For example, if NIT is 830027231 and 6.DV is 3, return '830027231-3'."
  }
  ```

### Step 3: Create E2E Test File

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/test_e2e.md` to understand the E2E test file format
- Create a new E2E test file at `.claude/commands/e2e/test_rut_dv_extraction.md` with the following content:
  - User Story about extracting DV correctly from RUT documents
  - Prerequisites (backend/frontend running, test RUT document available)
  - Test Steps to:
    1. Login as risk analyst
    2. Navigate to risk evaluation
    3. Upload a RUT document (Azelis or similar where DV is known)
    4. Trigger AI extraction
    5. Verify the extracted NIT contains correct DV
  - Success Criteria verifying the DV matches expected value

### Step 4: Run Validation Commands

Execute all validation commands listed below to ensure the bug is fixed with zero regressions.

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

### Backend Validation

```bash
# Run backend linting to ensure code quality
cd backend && ruff check src/

# Run backend tests
cd backend && python -m pytest tests/ -v
```

### Frontend Validation

```bash
# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build
```

### E2E Validation

- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test file `.claude/commands/e2e/test_rut_dv_extraction.md` to validate this functionality works

### Manual Verification (if E2E not available)

1. Start the application with `/start_local` skill
2. Login to the Risk module
3. Create a test risk evaluation
4. Upload a known RUT document (e.g., Azelis with DV=3)
5. Run extraction
6. Verify the NIT shows the correct format with proper DV value

## Notes

- The fix is surgical - only modifying the schema description for the NIT field in the RUT extraction schema
- No new dependencies are required
- The LandingAI API uses the description field to understand what to extract, so improving the description should fix the extraction
- The existing `rut_parser_service.py` already has correct logic for extracting NIT+DV from text-based PDFs - the AI extraction schema should match this behavior
- The change is backwards compatible - the NIT field format remains the same (XXXXXXXXX-D)
- Consider that different RUT document layouts may vary slightly, but field 6.DV is always immediately after field 5
