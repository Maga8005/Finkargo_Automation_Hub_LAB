# Patch: Fix LandingAI schema validation for signatories array

## Metadata
adw_id: `b0a5e4a8`
review_change_request: `When doing the financial statements extraction. The app is now returning this error: LandingAI API error (400): {"error":"Field extraction invalid: Failed to extract the fields from the input schema. Error: 'Schema validation failed: Type list at root.signatories cannot contain 'object' or 'array'. Please use '`

## Issue Summary
**Original Spec:** specs/issue-61-adw-b0a5e4a8-sdlc_planner-contador-revisor-fiscal-validation.md
**Issue:** LandingAI ADE API rejects the `signatories` field schema because it uses `"type": ["array", "null"]` which violates LandingAI's schema validation rules - type arrays cannot contain 'object' or 'array' types.
**Solution:** Change the `signatories` field type from `["array", "null"]` to just `"array"` in both FINANCIAL_STATEMENT_CURRENT and FINANCIAL_STATEMENT_PRIOR schemas, matching the working pattern used by `shareholders`, `board_members`, and `legal_representatives`.

## Files to Modify
Use these files to implement the patch:

- `backend/src/core/servicios/risk/document_extraction_service.py` (lines 38-50 and 72-84)

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Fix FINANCIAL_STATEMENT_CURRENT signatories schema
- Change line 39 from `"type": ["array", "null"]` to `"type": "array"`
- This matches the pattern used by working arrays like `shareholders` (line 116)

### Step 2: Fix FINANCIAL_STATEMENT_PRIOR signatories schema
- Change line 73 from `"type": ["array", "null"]` to `"type": "array"`
- This is the same fix applied to the prior year financial statement schema

## Validation
Execute every command to validate the patch is complete with zero regressions.

1. **Python Syntax Check:**
   ```bash
   cd backend && python -m py_compile src/core/servicios/risk/document_extraction_service.py
   ```

2. **Backend Linting:**
   ```bash
   cd backend && ./venv/bin/ruff check src/core/servicios/risk/document_extraction_service.py
   ```

3. **Backend Unit Tests:**
   ```bash
   cd backend && python -m pytest tests/test_fraud_detection_service.py -v --tb=short
   ```

4. **Import Validation:**
   ```bash
   cd backend && python -c "from src.core.servicios.risk.document_extraction_service import DocumentExtractionService, EXTRACTION_SCHEMAS; print('Import OK'); print('signatories type:', EXTRACTION_SCHEMAS['financial_statement_current']['properties']['signatories']['type'])"
   ```

## Patch Scope
**Lines of code to change:** 2
**Risk level:** low
**Testing required:** Verify schema compiles and API accepts the extraction request for financial statements
