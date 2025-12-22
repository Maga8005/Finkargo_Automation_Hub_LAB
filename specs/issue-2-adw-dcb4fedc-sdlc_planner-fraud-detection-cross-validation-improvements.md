# Feature: Fraud Detection Cross-Validation Improvements

## Feature Description

Improve the fraud detection cross-validation system to eliminate false positives caused by formatting differences (company name, NIT, city) and add critical typosquatting detection for email domains. The current cross-validation system has a ~60% false positive rate because it flags formatting differences (e.g., "S.A.S." vs "SAS") as CRITICAL discrepancies. This causes alert fatigue and buries real fraud indicators. Additionally, the system missed the actual fraud pattern in the Azelis case (email domain typosquatting where `acelis.com.co` looked similar to `azelis.com`).

Key improvements:
1. **Data Normalization** - Implement robust normalization for company names, NITs, and city names before comparison to eliminate false positives from formatting differences
2. **Typosquatting Detection** - Add string similarity detection using both Levenshtein distance and SequenceMatcher to catch domain variations like `acelis.com.co` vs `azelis.com`
3. **Provider Domain Validation** - Validate email domains against known legitimate provider domains
4. **Updated Severity Classification** - Only flag semantically different data as discrepancies (not formatting variations)

## User Story

As a **risk_analyst** or **risk_manager**
I want the cross-validation report to only show REAL discrepancies (not formatting differences)
So that I can focus on actual fraud indicators without alert fatigue

## Problem Statement

The current cross-validation system identified in the Azelis fraud case analysis has two critical issues:

1. **High False Positive Rate (~60%)**: The system flags formatting differences as CRITICAL discrepancies:
   - Company name: "AZELIS COLOMBIA S.A.S." vs "AZELIS COLOMBIA S A S" → flagged as CRITICAL (false positive)
   - NIT: "830027231 3" vs "830.027.231-3" → flagged as CRITICAL (false positive)
   - City: "Tenjo" vs "Tenjo (Cundinamarca)" → flagged as MEDIUM (false positive)

2. **Missing Critical Fraud Indicators**: The system missed the actual fraud patterns:
   - Email domain typosquatting: `acelis.com.co` vs `azelis.com` was NOT detected
   - Provider email domain validation was missing
   - These were the EXACT patterns used in the $2.3M fraud attempt

## Solution Statement

1. **Implement Enhanced Data Normalization**:
   - Company names: Remove all legal suffix variations (SAS, S.A.S., S A S, etc.), normalize punctuation and whitespace
   - NIT: Extract digits only, but separately track check digit for validation
   - City: Normalize to base city name, remove parenthetical department info

2. **Add Typosquatting Detection**:
   - Use SequenceMatcher similarity ratio (already partially implemented but not effective)
   - Add Levenshtein distance check as secondary measure
   - Check domain base AND TLD variations (`.com` vs `.com.co`)
   - Add dynamic known domains from company data itself

3. **Update Severity Classification**:
   - NONE (0 points): Formatting differences only
   - CRITICAL (25 points): Different company names/NITs after normalization, typosquatting
   - HIGH (15 points): Different check digits, legal representative mismatch, provider domain mismatch
   - MEDIUM (8 points): Address differences (not city formatting)
   - LOW (3 points): Minor informational discrepancies

## Access Control

- Required Role(s): `risk_analyst`, `risk_manager`
- Backend Protection: Use existing `require_roles(['risk_analyst', 'risk_manager'])` dependency
- Frontend Protection: Existing role protection already in place for risk module routes

## Relevant Files

Use these files to implement the feature:

### Backend Files
- `backend/src/core/servicios/risk/cross_validation_service.py` - **PRIMARY FILE**: Core cross-validation logic, contains `_normalize_company_name()`, `_normalize_nit()`, `_normalize_city()`, and `_validate_email_domain()` methods that need enhancement
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Contains typosquatting detection logic in `_check_email_domain()` and `_levenshtein_distance()` that can be reused/improved
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Risk scoring calculations; may need adjustment for new severity classifications
- `backend/src/interface/risk_dtos.py` - DTOs including `DiscrepancySeverity`, `ValidationType`, `CrossValidationResult` - may need new validation types
- `backend/src/adapter/rest/risk_routes.py` - API endpoints for cross-validation; `trigger_cross_validation()` endpoint

### Frontend Files
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - UI component displaying cross-validation results and discrepancies
- `frontend/src/types/risk.ts` - TypeScript types for risk module including `CrossValidationResult`, `DiscrepancySeverity`, `ValidationType`
- `frontend/src/services/riskService.ts` - API service for risk operations

### Testing Files
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test for reference
- `.claude/commands/e2e/test_fraud_document_cross_validation.md` - Existing E2E test for cross-validation that will need to validate improved behavior

### New Files

- `backend/src/core/servicios/risk/normalization_service.py` - New service for centralized data normalization functions
- `backend/src/core/servicios/risk/typosquatting_service.py` - New service for typosquatting detection logic
- `backend/tests/test_normalization_service.py` - Unit tests for normalization
- `backend/tests/test_typosquatting_service.py` - Unit tests for typosquatting detection
- `backend/tests/test_cross_validation_improvements.py` - Integration tests for improved cross-validation
- `.claude/commands/e2e/test_cross_validation_false_positive_reduction.md` - E2E test for false positive reduction

## Pre-Implementation Verification

### Feature Category
- [x] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [x] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)

N/A - This feature does not involve Word document generation.

### B. Excel Column Mapping (Excel Processing only)

N/A - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)

N/A - This feature does not involve file import/export.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| CrossValidationRepository.get_by_assessment() | List[dict] | `result['is_discrepancy']` | Dict access |
| CrossValidationRepository.create_batch() | List[dict] | N/A (insert only) | - |
| DocumentExtractionRepository.get_by_assessment() | List[dict] | `ext['extracted_data']` | Dict access |
| RiskAssessmentRepository.update() | dict | `assessment['risk_score']` | Dict access |

### E. Database Dependencies Checklist (Document/CRUD only)

- [x] Required enums exist in DTOs - `DiscrepancySeverity` and `ValidationType` already defined
- [x] No new database tables required - using existing `cross_validation_results` table
- [x] No migrations needed - existing schema supports all required fields
- [ ] May need to add new `ValidationType` values: `TYPOSQUATTING`, `PROVIDER_DOMAIN` (if not using existing `EMAIL_DOMAIN`)

### F. External API Contract (Integration only)

N/A - This feature does not involve external API integration.

### G. Query Specification (Reporting only)

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| assessment_id | string (UUID) | Yes | N/A |

Cross-validation results are retrieved by assessment_id only, no additional filtering needed.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| validation_type | validation_type | string (ValidationType enum) | Use snake_case in both |
| is_discrepancy | is_discrepancy | boolean | |
| severity | severity | string (DiscrepancySeverity enum) | null if not a discrepancy |
| score_impact | score_impact | number (Decimal in backend) | 0-100 range |
| description | description | string | Human-readable explanation |
| values_found | values_found | Record<string, unknown> | Document type -> extracted value |
| documents_compared | documents_compared | string[] | List of document types compared |

## Implementation Plan

### Phase 1: Foundation - Normalization Service

Create a dedicated normalization service with comprehensive data cleaning functions:
- Company name normalization (handle all legal suffix variations)
- NIT normalization (separate base digits from check digit)
- City name normalization (handle parenthetical info, accents, abbreviations)
- Person name normalization (handle accents, case, extra whitespace)

### Phase 2: Core Implementation - Enhanced Cross-Validation

Update the cross-validation service to:
- Use new normalization service for all comparisons
- Implement intelligent severity classification (ignore formatting, flag real discrepancies)
- Add NIT check digit specific validation (separate from base NIT comparison)
- Improve email domain validation with typosquatting detection

### Phase 3: Typosquatting Detection Service

Create dedicated service for typosquatting detection:
- String similarity using SequenceMatcher (70-95% similarity = suspicious)
- Levenshtein distance calculation (distance <= 2 = suspicious)
- TLD variation detection (`.com` vs `.com.co`, `.com.mx`)
- Dynamic known domain extraction from company data
- Provider domain validation

### Phase 4: Integration and Testing

- Update cross-validation flow to use new services
- Add comprehensive unit tests for normalization
- Add unit tests for typosquatting detection
- Update E2E test to verify false positive reduction
- Verify scoring calculations remain correct

## Step by Step Tasks

### Step 1: Create Normalization Service

- Create `backend/src/core/servicios/risk/normalization_service.py`
- Implement `NormalizationService` class with methods:
  - `normalize_company_name(name: str) -> str` - Remove ALL legal suffix variations including: S.A.S., S.A.S, SAS, S A S, S. A. S., S.A., SA, S A, S. A., LTDA., LTDA, LTD, E.U., EU, E U, Y CIA, & CIA, Y COMPANIA
  - `normalize_nit(nit: str) -> tuple[str, str | None]` - Return (base_digits, check_digit) separately
  - `normalize_city(city: str) -> str` - Remove parenthetical department info, normalize accents
  - `normalize_person_name(name: str) -> str` - Handle accents, case, whitespace
  - `are_nits_equivalent(nit1: str, nit2: str) -> tuple[bool, str]` - Compare NITs and return (match, reason)

### Step 2: Create Typosquatting Detection Service

- Create `backend/src/core/servicios/risk/typosquatting_service.py`
- Implement `TyposquattingService` class with methods:
  - `check_domain_typosquatting(domain: str, known_domains: List[str]) -> Optional[TyposquattingResult]`
  - `calculate_similarity(s1: str, s2: str) -> float` - Using SequenceMatcher
  - `calculate_levenshtein_distance(s1: str, s2: str) -> int`
  - `extract_domain_base(domain: str) -> str` - Get base without TLD
  - `is_similar_domain(domain1: str, domain2: str, threshold: float = 0.7) -> bool`
  - `get_suspicious_tld_variations(base_domain: str, target_domain: str) -> List[str]`

### Step 3: Add Unit Tests for Normalization Service

- Create `backend/tests/test_normalization_service.py`
- Test cases for company name normalization:
  - "AZELIS COLOMBIA S.A.S." → "AZELIS COLOMBIA"
  - "AZELIS COLOMBIA S A S" → "AZELIS COLOMBIA"
  - "AZELIS COLOMBIA SAS" → "AZELIS COLOMBIA"
  - "ROCSA COLOMBIA S.A." → "ROCSA COLOMBIA"
- Test cases for NIT normalization:
  - "830.027.231-3" → ("830027231", "3")
  - "830027231 3" → ("830027231", "3")
  - "830027231-1" → ("830027231", "1")
- Test cases for city normalization:
  - "Tenjo (Cundinamarca)" → "TENJO"
  - "Bogotá D.C." → "BOGOTA"
  - "MEDELLÍN" → "MEDELLIN"

### Step 4: Add Unit Tests for Typosquatting Service

- Create `backend/tests/test_typosquatting_service.py`
- Test cases:
  - "acelis.com.co" vs "azelis.com" → typosquatting detected (high similarity, different domain)
  - "azelis.com.co" vs "azelis.com" → TLD variation detected
  - "californiadavisinc.com" vs "californiadavis.com" → typosquatting detected
  - "basf.com" vs "basf.com" → exact match, no issue
  - "completelydifferent.com" vs "azelis.com" → no similarity, no issue

### Step 5: Update Cross-Validation Service - Normalization Integration

- Modify `backend/src/core/servicios/risk/cross_validation_service.py`
- Import and use `NormalizationService` in constructor
- Update `_validate_company_names()`:
  - Use `normalize_company_name()` for comparison
  - Only flag as discrepancy if normalized names differ
  - Update description to show both raw and normalized values
- Update `_validate_nit_consistency()`:
  - Use `normalize_nit()` to separate base and check digit
  - Flag CRITICAL if base digits differ
  - Flag HIGH if only check digit differs (new validation type)
  - Ignore formatting differences entirely
- Update `_validate_address_consistency()`:
  - Use `normalize_city()` for comparison
  - Only flag if base city names actually differ

### Step 6: Update Cross-Validation Service - Typosquatting Detection

- Modify `backend/src/core/servicios/risk/cross_validation_service.py`
- Import and use `TyposquattingService`
- Update `_validate_email_domain()`:
  - Build dynamic known domains list from company name + standard domains
  - Check for typosquatting against company's expected domain
  - Check for TLD variations (`.com` vs `.com.co`)
  - Increase severity from MEDIUM to HIGH/CRITICAL for typosquatting matches
  - Add provider domain validation (check if email domain looks legitimate for a known provider)

### Step 7: Add New Validation Types (Optional Enhancement)

- Update `backend/src/interface/risk_dtos.py`:
  - Add `ValidationType.NIT_CHECK_DIGIT` for separate check digit validation
  - Add `ValidationType.TYPOSQUATTING` for typosquatting-specific alerts
  - Add `ValidationType.PROVIDER_DOMAIN` for provider email validation
- Update `frontend/src/types/risk.ts`:
  - Add corresponding TypeScript types
  - Add labels in `VALIDATION_TYPE_LABELS`

### Step 8: Update Severity Score Impacts

- Modify `backend/src/core/servicios/risk/cross_validation_service.py`
- Update `SCORE_IMPACT` dictionary:
  ```python
  SCORE_IMPACT = {
      DiscrepancySeverity.CRITICAL: Decimal('25'),  # Real discrepancies
      DiscrepancySeverity.HIGH: Decimal('15'),      # Check digit, legal rep, typosquatting
      DiscrepancySeverity.MEDIUM: Decimal('8'),     # Address differences (real ones)
      DiscrepancySeverity.LOW: Decimal('3'),        # Minor issues
  }
  ```
- Ensure formatting differences return `score_impact=0` and `is_discrepancy=False`

### Step 9: Create Integration Tests

- Create `backend/tests/test_cross_validation_improvements.py`
- Test the full cross-validation flow with:
  - Documents with formatting differences only → expect 0 discrepancies
  - Documents with real company name mismatch → expect CRITICAL discrepancy
  - Documents with typosquatting email → expect HIGH/CRITICAL discrepancy
  - Documents with check digit mismatch → expect HIGH discrepancy

### Step 10: Create E2E Test for False Positive Reduction

- Create `.claude/commands/e2e/test_cross_validation_false_positive_reduction.md`
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for format reference
- Test scenario:
  1. Upload documents with same company but different formatting ("S.A.S." vs "SAS")
  2. Run cross-validation
  3. Verify NO discrepancies are flagged for formatting differences
  4. Verify typosquatting detection works (if test data available)

### Step 11: Run Validation Commands

- Run all validation commands to ensure no regressions
- Fix any issues found during validation

## Testing Strategy

### Unit Tests

**Normalization Service Tests:**
- Test each normalization function with edge cases
- Test with Colombian-specific formats (NITs, city names with accents)
- Test with various legal suffix formats
- Test with null/empty inputs

**Typosquatting Service Tests:**
- Test similarity calculations with known similar strings
- Test Levenshtein distance calculations
- Test TLD variation detection
- Test with real fraud case examples (azelis/acelis)

**Cross-Validation Integration Tests:**
- Test full validation flow with mock extractions
- Verify score calculations are correct
- Verify severity classifications are appropriate

### Edge Cases

1. **Empty or null values**: Ensure graceful handling of missing data
2. **Mixed case inputs**: "AZELIS" vs "Azelis" vs "azelis"
3. **Unicode characters**: Accents in Colombian names (María, José, Bogotá)
4. **Partial matches**: Company name appears in one document but not another
5. **Multiple legal suffixes**: "EMPRESA S.A.S. LTDA." (malformed data)
6. **NIT without check digit**: "830027231" without the "-3"
7. **Very similar but different companies**: "AZELIS COLOMBIA" vs "AZELIS MEXICO"
8. **Free email providers**: gmail.com, hotmail.com for business use
9. **International domains**: .com vs .com.co vs .mx

## Acceptance Criteria

1. **False Positive Elimination**:
   - Company names differing only in legal suffix formatting (S.A.S. vs SAS) are NOT flagged as discrepancies
   - NITs differing only in formatting (dots, dashes, spaces) are NOT flagged as discrepancies
   - Cities with added department info (Tenjo vs Tenjo Cundinamarca) are NOT flagged as discrepancies

2. **Real Discrepancy Detection**:
   - Different company names after normalization ARE flagged as CRITICAL
   - Different NIT base digits ARE flagged as CRITICAL
   - Different NIT check digits ARE flagged as HIGH
   - Typosquatting domains (70-95% similarity) ARE flagged as HIGH or CRITICAL

3. **Score Impact Accuracy**:
   - Formatting differences contribute 0 points to risk score
   - Real discrepancies contribute appropriate points (15-25 depending on severity)
   - Total score impact accurately reflects actual risk

4. **Typosquatting Detection**:
   - Catches domain variations like `acelis.com.co` vs `azelis.com`
   - Catches TLD variations like `azelis.com` vs `azelis.com.co`
   - Does NOT flag exact matches as issues
   - Does NOT flag completely different domains as typosquatting

5. **All Tests Pass**:
   - Unit tests for normalization service pass
   - Unit tests for typosquatting service pass
   - Integration tests for cross-validation pass
   - E2E test demonstrates reduced false positives
   - Existing tests continue to pass (no regressions)

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run backend unit tests including new tests
cd backend && python -m pytest tests/ -v

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build

# Run E2E test for cross-validation improvements
# Read .claude/commands/test_e2e.md, then read and execute
# .claude/commands/e2e/test_cross_validation_false_positive_reduction.md
```

## Notes

### Dependencies

No new pip packages required. The implementation uses:
- `difflib.SequenceMatcher` (Python standard library) - Already imported in cross_validation_service.py
- `re` module (Python standard library) - Already imported
- `decimal.Decimal` (Python standard library) - Already imported

### Future Enhancements (Out of Scope)

These improvements were identified in the PRD but are out of scope for this implementation:

1. **Document Manipulation Detection**: Detecting PDFs with editable layers/elements, metadata inconsistencies
2. **Authoritative Source Validation**: Downloading Cámara de Comercio directly from RUES/Confecámaras API
3. **Financial Statement Signature Validation**: Verifying auditor signatures against known patterns

### Performance Considerations

- Normalization functions should be lightweight (string operations only)
- Typosquatting checks against known domains list should be O(n) where n is typically < 20
- Consider caching normalized values if same data is compared multiple times

### Backward Compatibility

- Existing cross-validation results will remain valid
- New validation types are additive, not breaking changes
- Score calculation changes may result in different scores for same data (expected improvement)

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (if UI feature) - Step 10
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness

**Reporting:**
- [x] Query filters and parameters documented
- [x] Pagination/sorting requirements specified (N/A - single assessment lookup)

**CRUD Operations:**
- [x] Repository patterns documented
- [x] Validation rules specified in normalization functions

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) - Colombian NIT format, city names with accents

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (Step 10)
