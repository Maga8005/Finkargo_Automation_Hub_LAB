# Feature: Contador/Revisor Fiscal Cross-Validation in Riesgos Module

## Feature Description

This feature adds cross-validation capability for accountants (contador) and fiscal auditors (revisor fiscal) who sign financial statements in the Riesgos (Risk/Fraud Detection) module. The system will extract contador/revisor fiscal information from official documents (Camara de Comercio, RUT) and compare them against the signatories found in the financial statements. This helps detect potential fraud where someone unauthorized signs the financial statements or where signatory credentials don't match official registrations.

Colombian regulations require financial statements to be signed by authorized professionals:
- **Contador (Accountant)**: Prepares and certifies the financial statements
- **Revisor Fiscal (Fiscal Auditor)**: Independent auditor required for certain company sizes

Mismatches between declared professionals and actual signatories can indicate:
- Fraudulent financial statements
- Identity impersonation
- Regulatory non-compliance
- Document manipulation

## User Story

As a **Risk Analyst or Risk Manager**
I want to **validate that the contador/revisor fiscal signing financial statements matches the one registered in official documents**
So that **I can detect potential fraud involving fake or unauthorized financial statement signatories**

## Problem Statement

The Riesgos module currently validates company names, NITs, legal representatives, shareholders, financial continuity, and email domains across documents. However, it does not validate the professional credentials of the accountant or fiscal auditor who signs financial statements against those registered in official documents (Camara de Comercio, RUT). This is a significant fraud vector where:
1. Fraudsters can forge financial statements with fake professional signatures
2. Someone other than the declared contador/revisor fiscal signs the statements
3. Professional license numbers can be fabricated or belong to someone else

## Solution Statement

Add a new cross-validation type `CONTADOR_REVISOR_FISCAL` that:

1. **Extracts contador/revisor fiscal data from official documents**:
   - From Camara de Comercio (Certificado de Existencia): contador name, contador cedula, revisor fiscal name, revisor fiscal cedula
   - From RUT: contador/revisor fiscal information if available

2. **Extracts signatory data from financial statements**:
   - signatory_name, signatory_id, signatory_role (already in extraction schema)
   - auditor_name, auditor_license (already in extraction schema)

3. **Cross-validates the data**:
   - Compare signatory in financial statements against declared contador/revisor fiscal
   - Use fuzzy name matching (85% threshold) for format variations
   - Validate professional license format if available

4. **Assigns appropriate severity**:
   - CRITICAL: Signatory not found in any official document
   - HIGH: Name mismatch between signatory and declared professional
   - MEDIUM: ID/cedula mismatch
   - INFO: Verified - signatory matches declared professional

## Access Control

- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: Use existing RBAC dependencies from `rbac_dependencies.py` - the cross-validation endpoint already has protection
- Frontend Protection: No changes needed - the RiskEvaluationDetail page already uses RoleProtectedRoute

## Relevant Files

Use these files to implement the feature:

**Backend - Core Implementation:**
- `backend/src/core/servicios/risk/cross_validation_service.py` - Add the new `_validate_contador_revisor_fiscal()` method following existing patterns (like `_validate_legal_representative()`)
- `backend/src/core/servicios/risk/normalization_service.py` - Use existing `normalize_person_name()` and fuzzy matching via `calculate_similarity()`
- `backend/src/interface/risk_dtos.py` - Add `CONTADOR_REVISOR_FISCAL` to `ValidationType` enum
- `backend/src/core/servicios/risk/document_extraction_service.py` - Update extraction schemas to add contador/revisor fiscal fields to Certificado de Existencia

**Backend - Tests:**
- `backend/tests/test_fraud_detection_service.py` - Add test cases for contador/revisor fiscal validation

**Frontend - Type Updates:**
- `frontend/src/types/risk.ts` - Add `contador_revisor_fiscal` to `ValidationType` union type and `VALIDATION_TYPE_LABELS` mapping

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - Understand E2E test structure
- `.claude/commands/e2e/test_risk_dashboard.md` - Example E2E test for reference

**Documentation:**
- `app_docs/feature-fefa5443-fraud-detection-risk-module.md` - Understand existing fraud detection patterns
- `app_docs/feature-ec3ddef5-fraud-risk-module-fixes.md` - Understand discrepancy severity patterns

### New Files

1. `.claude/commands/e2e/test_contador_revisor_fiscal_validation.md` - E2E test for validating the new cross-validation type
2. `backend/database/migration_add_contador_revisor_fiscal_fields.sql` - Database migration to add contador/revisor fiscal fields to extraction schemas (if needed for storage)

## Pre-Implementation Verification

### Feature Category

- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] **Excel Processing (treasury, finance)** → Not applicable
- [ ] Data Import/Export (CSV, ZIP) → Not applicable
- [ ] API Integration (external services) → Not applicable
- [ ] Reporting (queries, history) → Not applicable
- [x] **CRUD Operations (basic data management)** → Complete sections D, E
- [x] **Custom: Cross-Validation Feature** → Extends existing validation framework

### A. Template Placeholder Inventory (Document Generation only)

Not applicable - this feature does not involve document generation.

### B. Excel Column Mapping (Excel Processing only)

Not applicable - this feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)

Not applicable - this feature does not involve file import/export.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `extractions.get(DocumentType.CERTIFICADO_EXISTENCIA, {})` | dict or None | `data.get('contador_name', '')` | Empty string if not found |
| `extractions.get(DocumentType.FINANCIAL_STATEMENT_CURRENT, {})` | dict or None | `data.get('signatory_name', '')` | Empty string if not found |
| `self.normalizer.normalize_person_name(name)` | str | Direct return | Normalized uppercase string |
| `self._names_match(name1, name2)` | bool | Direct return | True if similarity >= 0.85 |

### E. Database Dependencies Checklist (Document/CRUD only)

- [x] Required enums exist in DTOs (ValidationType will be added)
- [x] Template file exists (N/A - no templates needed)
- [x] Database records exist (extraction schemas need updating)
- [x] Country-specific data handled (Colombian documents only - CO)

**Extraction Schema Updates Needed:**

The `CERTIFICADO_EXISTENCIA` extraction schema in `document_extraction_service.py` needs new fields:
```python
"contador_name": {"type": ["string", "null"], "description": "Name of registered contador (accountant)"},
"contador_cedula": {"type": ["string", "null"], "description": "Cedula of registered contador"},
"contador_license": {"type": ["string", "null"], "description": "Professional license (tarjeta profesional) of contador"},
"revisor_fiscal_name": {"type": ["string", "null"], "description": "Name of registered revisor fiscal (fiscal auditor)"},
"revisor_fiscal_cedula": {"type": ["string", "null"], "description": "Cedula of revisor fiscal"},
"revisor_fiscal_license": {"type": ["string", "null"], "description": "Professional license of revisor fiscal"}
```

### F. External API Contract (Integration only)

Not applicable - this feature does not involve external APIs.

### G. Query Specification (Reporting only)

Not applicable - this feature does not involve new queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `contador_revisor_fiscal` | `CONTADOR_REVISOR_FISCAL` | ValidationType | New validation type enum value |
| `validation_type` | `validation_type` | string | Use snake_case in both |
| `severity` | `severity` | DiscrepancySeverity | Existing pattern |
| `is_discrepancy` | `is_discrepancy` | boolean | Existing pattern |

## Implementation Plan

### Phase 1: Foundation

1. **Update Backend DTOs**
   - Add `CONTADOR_REVISOR_FISCAL` to `ValidationType` enum in `risk_dtos.py`

2. **Update Extraction Schema**
   - Add contador/revisor fiscal fields to `CERTIFICADO_EXISTENCIA` schema in `document_extraction_service.py`

3. **Update Frontend Types**
   - Add `contador_revisor_fiscal` to `ValidationType` union type in `risk.ts`
   - Add Spanish label to `VALIDATION_TYPE_LABELS` mapping

### Phase 2: Core Implementation

1. **Implement Cross-Validation Logic**
   - Add `_validate_contador_revisor_fiscal()` method to `CrossValidationService`
   - Extract contador/revisor fiscal from Certificado de Existencia
   - Extract signatory/auditor from Financial Statements (current and prior)
   - Compare using fuzzy name matching (reuse existing `_names_match()`)
   - Assign appropriate severity based on match results

2. **Wire Up Validation**
   - Add call to new validation method in `validate_documents()` main orchestrator

### Phase 3: Integration

1. **Add Unit Tests**
   - Test cases for matching contador/signatory
   - Test cases for mismatched names
   - Test cases for missing data (graceful handling)
   - Test fuzzy matching variations

2. **Create E2E Test**
   - Validate the validation appears in cross-validation results
   - Test with matching and mismatching documents

## Step by Step Tasks

### Step 1: Update Backend ValidationType Enum

Add the new validation type to the enum:

- Open `backend/src/interface/risk_dtos.py`
- Find `class ValidationType(str, Enum)`
- Add `CONTADOR_REVISOR_FISCAL = "contador_revisor_fiscal"` after `DOMAIN_AGE`

### Step 2: Update Certificado de Existencia Extraction Schema

Add new fields for contador/revisor fiscal extraction:

- Open `backend/src/core/servicios/risk/document_extraction_service.py`
- Find `DocumentType.CERTIFICADO_EXISTENCIA` schema
- Add new properties after `board_members`:
  ```python
  "contador_name": {"type": ["string", "null"], "description": "Name of registered contador (accountant)"},
  "contador_cedula": {"type": ["string", "null"], "description": "Cedula of registered contador"},
  "contador_license": {"type": ["string", "null"], "description": "Professional license (tarjeta profesional) of contador"},
  "revisor_fiscal_name": {"type": ["string", "null"], "description": "Name of registered revisor fiscal (fiscal auditor)"},
  "revisor_fiscal_cedula": {"type": ["string", "null"], "description": "Cedula of revisor fiscal"},
  "revisor_fiscal_license": {"type": ["string", "null"], "description": "Professional license of revisor fiscal"}
  ```

### Step 3: Implement Cross-Validation Method

Add the new validation method to `CrossValidationService`:

- Open `backend/src/core/servicios/risk/cross_validation_service.py`
- Add new method `_validate_contador_revisor_fiscal()` after `_validate_address_consistency()`
- The method should:
  1. Extract contador/revisor fiscal from Certificado de Existencia
  2. Extract signatory/auditor from both Financial Statement documents
  3. Compare using normalized names and fuzzy matching
  4. Return `CrossValidationResult` with appropriate severity:
     - INFO: Verified match
     - MEDIUM: ID/cedula mismatch only
     - HIGH: Name mismatch
     - CRITICAL: Signatory not found in official documents

### Step 4: Wire Up Validation in Main Orchestrator

Add call to new validation in `validate_documents()`:

- In `cross_validation_service.py`, find `validate_documents()` method
- After domain age validation (line ~127), add:
  ```python
  # 9. Contador/Revisor Fiscal validation
  contador_results = self._validate_contador_revisor_fiscal(extractions)
  results.extend(contador_results)
  ```

### Step 5: Update Frontend ValidationType

Add the new type to frontend types:

- Open `frontend/src/types/risk.ts`
- Find `export type ValidationType =`
- Add `| 'contador_revisor_fiscal'` to the union type
- Find `VALIDATION_TYPE_LABELS`
- Add: `contador_revisor_fiscal: 'Contador/Revisor Fiscal',`

### Step 6: Add Unit Tests

Create test cases for the new validation:

- Open `backend/tests/test_fraud_detection_service.py`
- Add new test class or methods for contador/revisor fiscal validation:
  - `test_contador_revisor_fiscal_verified()` - matching signatory
  - `test_contador_revisor_fiscal_name_mismatch()` - name doesn't match
  - `test_contador_revisor_fiscal_cedula_mismatch()` - ID doesn't match
  - `test_contador_revisor_fiscal_not_found()` - signatory not in official docs
  - `test_contador_revisor_fiscal_missing_data()` - graceful handling of missing fields
  - `test_contador_revisor_fiscal_fuzzy_match()` - name variations still match

### Step 7: Create E2E Test Specification

Create E2E test file:

- Create `.claude/commands/e2e/test_contador_revisor_fiscal_validation.md`
- Follow the pattern from `test_risk_dashboard.md`
- Test steps should validate:
  1. Upload Certificado de Existencia with contador/revisor fiscal info
  2. Upload Financial Statement with signatory info
  3. Run cross-validation
  4. Verify contador/revisor fiscal validation appears in results
  5. Verify correct severity based on match/mismatch

### Step 8: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests

**Backend Unit Tests (pytest):**

1. **Test Verified Match (INFO)**
   - Certificado has contador "JUAN CARLOS PEREZ" with cedula "12345678"
   - Financial statement signatory matches exactly
   - Expected: is_discrepancy=False, severity=None (INFO in description)

2. **Test Name Mismatch (HIGH)**
   - Certificado has contador "JUAN CARLOS PEREZ"
   - Financial statement has signatory "MARIA GARCIA LOPEZ"
   - Expected: is_discrepancy=True, severity=HIGH

3. **Test Cedula Mismatch (MEDIUM)**
   - Names match (fuzzy) but cedulas differ
   - Expected: is_discrepancy=True, severity=MEDIUM

4. **Test Signatory Not Found (CRITICAL)**
   - Financial statement has signatory but no match in Certificado
   - Expected: is_discrepancy=True, severity=CRITICAL

5. **Test Fuzzy Name Matching**
   - "JUAN CARLOS PEREZ GARCIA" vs "PEREZ GARCIA JUAN CARLOS"
   - Expected: Match (name reordering tolerance)

6. **Test Missing Data Handling**
   - No contador in Certificado
   - No signatory in Financial Statement
   - Expected: Graceful handling, no crash

### Edge Cases

1. **Empty signatory fields** - Should skip validation gracefully
2. **Multiple financial statements** - Compare against both current and prior year
3. **Revisor fiscal vs contador distinction** - Correctly identify which professional role
4. **Special characters in names** - Accents, apostrophes should be normalized
5. **Very similar but different names** - Should NOT match if below 85% threshold
6. **Same person as legal rep and contador** - Common for small companies, should not flag
7. **Professional license format validation** - Colombian tarjeta profesional format

## Acceptance Criteria

1. ✅ New `CONTADOR_REVISOR_FISCAL` validation type added to backend enum
2. ✅ Extraction schema updated for Certificado de Existencia with contador/revisor fiscal fields
3. ✅ Cross-validation method implemented with fuzzy name matching
4. ✅ Severity levels correctly assigned:
   - CRITICAL: Signatory not found
   - HIGH: Name mismatch
   - MEDIUM: Cedula mismatch
   - INFO: Verified match
5. ✅ Frontend type updated with new validation type and Spanish label
6. ✅ Unit tests pass for all scenarios
7. ✅ E2E test specification created
8. ✅ All linting and type checks pass
9. ✅ Build completes without errors
10. ✅ Cross-validation results show contador/revisor fiscal validation in UI

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend tests
cd backend && python -m pytest tests/test_fraud_detection_service.py -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

**E2E Validation:**
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_contador_revisor_fiscal_validation.md` E2E test

## Notes

### Colombian Professional Credentials Context

In Colombia:
- **Contador Publico (Public Accountant)**: Must be certified by the Junta Central de Contadores. Has a "tarjeta profesional" (professional license) number.
- **Revisor Fiscal**: Independent auditor required for companies above certain thresholds. Also requires professional certification.

The Certificado de Existencia (Certificate of Existence from Camara de Comercio) typically lists:
- Company's registered contador
- Company's revisor fiscal (if applicable)
- Their cedula numbers and professional license numbers

Financial statements in Colombia must be signed by:
- Legal representative
- Contador who prepared them
- Revisor fiscal (if company requires one)

### Fuzzy Matching Rationale

Name matching uses 85% similarity threshold because:
- Names may be in different order (first/last name swap)
- Minor spelling variations or OCR errors
- Accent handling differences

The existing `_names_match()` method in `CrossValidationService` already handles:
- Token-based matching (same words in different order)
- SequenceMatcher similarity for typos
- Normalized comparison (accents removed, uppercase)

### Severity Level Justification

- **CRITICAL (25 points)**: Signatory not found = potential unauthorized person signing
- **HIGH (15 points)**: Name mismatch = possible identity fraud
- **MEDIUM (8 points)**: Cedula mismatch only = likely data entry error but needs verification
- **INFO (0 points)**: Verified = positive indicator, shown as green

### Dependencies

No new npm or pip packages required. This feature uses existing:
- `difflib.SequenceMatcher` for fuzzy matching (Python stdlib)
- Existing normalization service patterns
- Existing cross-validation framework

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)

- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (schema update in extraction service)
- [x] E2E test file task included (Step 7)
- [x] All external dependencies (npm/pip packages) listed in Notes (none required)

### Category-Specific Completeness

**Cross-Validation Feature (Custom):**
- [x] New validation type enum value documented
- [x] Extraction schema updates documented
- [x] Severity levels defined with justification
- [x] Fuzzy matching approach documented

### Consistency (ALL features)

- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (Colombian documents only)

### Testing

- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
