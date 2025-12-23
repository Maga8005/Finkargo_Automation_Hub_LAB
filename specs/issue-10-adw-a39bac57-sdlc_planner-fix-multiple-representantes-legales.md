# Bug: Multiple Representantes Legales Not Handled in Cross-Validation

## Bug Description

In the Riesgos (Risk) department module, when performing document cross-validation for fraud detection, the system only extracts and compares a **single** Representante Legal from the RUT and Certificado de Existencia documents. However, Colombian companies can have multiple Representantes Legales:
- **Representante Legal Principal** (marked as `REPRS LEGAL PRIN` in RUT's Representación field)
- **Representantes Legales Suplentes** (marked as `REPRS LEGAL SUPL` in RUT's Representación field)

When a company like Azelis has multiple Representantes Legales, the system incorrectly flags a discrepancy because it only compares the first/principal Representante Legal from the RUT against the Cedula document. If the Cedula belongs to a Representante Legal Suplente, the validation fails with a false positive.

**Expected behavior**: The system should extract ALL Representantes Legales from both RUT and Certificado de Existencia, then check if ANY of them match the Cedula document's person data.

**Actual behavior**: The system only extracts one Representante Legal from each document, leading to false positive discrepancies when the Cedula belongs to a secondary Representante Legal.

## Problem Statement

The current document extraction schema and cross-validation logic only supports a single legal representative per document, causing false positive fraud alerts when companies have multiple authorized representatives.

## Solution Statement

Modify the document extraction schemas and cross-validation logic to:
1. Extract ALL Representantes Legales from RUT and Certificado de Existencia documents
2. Include their role type (principal/suplente) for context
3. Update cross-validation to check if the Cedula document matches ANY of the Representantes Legales
4. Update the Cedula comparison logic to validate against the matching representative's ID

## Steps to Reproduce

1. Create a new Risk Evaluation for a company with multiple Representantes Legales
2. Upload documents:
   - RUT document with multiple representatives (principal + suplentes)
   - Cedula of a Representante Legal Suplente (not the principal)
   - Certificado de Existencia listing multiple representatives
3. Trigger AI extraction
4. Run cross-validation
5. **Observe**: System reports "Nombres de representante legal no coinciden" and "Cédulas del representante legal no coinciden" as HIGH severity discrepancies
6. **Expected**: No discrepancy should be reported since the Cedula belongs to one of the authorized Representantes Legales

## Root Cause Analysis

The root cause is in two locations:

1. **Document Extraction Schemas** (`backend/src/core/servicios/risk/document_extraction_service.py`):
   - RUT schema only has `legal_representative_name` and `legal_representative_id` as single values
   - Certificado Existencia schema only has `legal_representative_name` and `legal_representative_id` as single values
   - No schema support for extracting multiple representatives or their roles

2. **Cross-Validation Logic** (`backend/src/core/servicios/risk/cross_validation_service.py`):
   - `_validate_legal_representative()` method at lines 288-388 only extracts single values from each document
   - Comparison logic uses simple string matching expecting exact match between single values

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

- `backend/src/core/servicios/risk/document_extraction_service.py` - Contains the LandingAI extraction schemas. The RUT schema (lines 108-125) and Certificado Existencia schema (lines 127-158) need to be updated to extract arrays of legal representatives instead of single values.

- `backend/src/core/servicios/risk/cross_validation_service.py` - Contains the cross-validation logic. The `_validate_legal_representative()` method (lines 288-388) needs to be updated to handle multiple representatives and check if ANY representative matches across documents.

- `backend/src/interface/risk_dtos.py` - Contains the data transfer objects. May need new DTOs to represent multiple legal representatives with their roles.

- `backend/src/core/servicios/risk/normalization_service.py` - Contains normalization utilities for names and IDs. Used by cross-validation for comparing names. No changes expected but may be referenced.

- `backend/tests/test_cross_validation_improvements.py` - Contains existing cross-validation tests. New tests should be added here to cover multiple representatives scenario.

- `.claude/commands/e2e/test_fraud_document_cross_validation.md` - Existing E2E test for cross-validation. Reference for creating new E2E test.

- `.claude/commands/test_e2e.md` - E2E test runner instructions.

### New Files

- `.claude/commands/e2e/test_cross_validation_multiple_representantes.md` - New E2E test file to validate the bug fix works correctly in the UI.

## Step by Step Tasks

### Step 1: Update Document Extraction Schemas for RUT

- Update the RUT schema in `backend/src/core/servicios/risk/document_extraction_service.py` to extract an array of legal representatives
- Change `legal_representative_name` and `legal_representative_id` to `legal_representatives` array
- Each item should include:
  - `name`: Full name of the representative
  - `id_number`: Cedula number
  - `id_type`: Document type (CC, CE, etc.)
  - `role`: Role type ("principal" or "suplente")
  - `representation_type`: The raw value from RUT ("REPRS LEGAL PRIN" or "REPRS LEGAL SUPL")
- Keep backward compatibility by also extracting the principal representative into the original single fields

### Step 2: Update Document Extraction Schemas for Certificado de Existencia

- Update the Certificado de Existencia schema in `backend/src/core/servicios/risk/document_extraction_service.py`
- Add `legal_representatives` array similar to RUT schema
- Each item should include:
  - `name`: Full name
  - `id_number`: Cedula number
  - `id_type`: Document type
  - `role`: Role type ("principal" or "suplente" based on section headers)
- The AI should extract from the `<REPRESENTANTES LEGALES>` section, identifying principals (marked with `<principal>` two rows below) and suplentes (marked with `<suplente>`)

### Step 3: Update Cross-Validation Logic for Legal Representatives

- Modify `_validate_legal_representative()` in `backend/src/core/servicios/risk/cross_validation_service.py`
- Update name comparison logic:
  - Extract all representatives from RUT (`legal_representatives` array)
  - Extract all representatives from Certificado (`legal_representatives` array)
  - Extract the person from Cedula (`full_name`, `document_number`)
  - Check if the Cedula person matches ANY representative in the RUT list
  - Check if the Cedula person matches ANY representative in the Certificado list
  - Only flag as discrepancy if the Cedula person is NOT found in either list
- Update ID comparison logic similarly:
  - Check if Cedula `document_number` matches ANY representative's `id_number` in RUT
  - Check if Cedula `document_number` matches ANY representative's `id_number` in Certificado
  - Only flag discrepancy if no match found
- Add informative description indicating which representative matched (if any)

### Step 4: Update Cross-Validation Result Messages

- When a match is found, include the role of the matched representative in the description
- Example: "Representante legal verificado: Juan Pérez (Suplente) - Cédula coincide con RUT y Certificado"
- When no match is found, list all representatives that were checked for debugging

### Step 5: Add Unit Tests for Multiple Representatives

- Add new test cases in `backend/tests/test_cross_validation_improvements.py`:
  - Test: Cedula matches principal representative → no discrepancy
  - Test: Cedula matches suplente representative → no discrepancy
  - Test: Cedula matches no representative → HIGH severity discrepancy
  - Test: Multiple suplentes, Cedula matches one → no discrepancy
  - Test: RUT has representatives but Certificado missing → handle gracefully
  - Test: Backward compatibility with single representative data

### Step 6: Create E2E Test File

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_fraud_document_cross_validation.md` for format reference
- Create `.claude/commands/e2e/test_cross_validation_multiple_representantes.md` with:
  - User story: As a Risk Analyst, I want the system to correctly validate companies with multiple Representantes Legales so that I don't get false positive fraud alerts
  - Prerequisites: Test documents with multiple representatives
  - Test steps: Upload RUT with multiple reps, upload Cedula of a suplente, run validation, verify NO discrepancy is shown
  - Success criteria: Validation passes, no false positive, correct representative role shown in results

### Step 7: Run Validation Commands

- Execute all validation commands to ensure the fix works correctly with zero regressions

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -m pytest tests/test_cross_validation_improvements.py -v` - Run the updated cross-validation tests to verify multiple representatives handling
- `cd backend && python -m pytest` - Run all backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_cross_validation_multiple_representantes.md` test file to validate this functionality works in the UI

## Notes

- The LandingAI ADE API may need specific prompting to extract ALL representatives. The schema description should be explicit about extracting multiple entries.
- The existing `board_members` field in Certificado Existencia already uses an array pattern - this can be referenced for the implementation.
- Backward compatibility is important: existing extractions with single representative fields should still work. The new array field is additive.
- Colombian RUT documents have a specific structure where representatives are listed in the "Representación" section with role codes like "REPRS LEGAL PRIN" and "REPRS LEGAL SUPL".
- The Certificado de Existencia has a `<REPRESENTANTES LEGALES>` section where roles are indicated in subsequent rows with `<principal>` or `<suplente>` markers.
- Consider adding logging to help debug which representative was matched during validation.
