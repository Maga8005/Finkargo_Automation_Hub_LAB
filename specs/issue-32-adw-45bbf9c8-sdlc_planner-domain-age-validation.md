# Feature: Domain Existence and Age Validation for Risk Module

## Feature Description

This feature adds **domain existence validation** (DNS lookup) and **domain age validation** (WHOIS lookup) to the Fraud Detection & Risk Management Module. The system will verify that email domains actually exist (resolve via DNS) and compare the domain registration age against company registration dates from official documents (RUT, Certificado de Existencia).

Fraudsters often register lookalike domains (typosquatting) shortly before committing fraud. While the current system detects domain similarity through typosquatting analysis, it cannot detect:
- Domains that **don't actually exist** (registered but not resolving)
- Domains that are **suspiciously young** relative to an established company
- Domains registered **after** the company's official registration date

This enhancement adds another layer of fraud detection to the existing risk assessment workflow.

## User Story

As a **Risk Analyst**
I want to see if email domains exist and how old they are
So that I can detect recently-registered fraudulent domains used for typosquatting

## Problem Statement

Fraudsters register lookalike domains shortly before fraud attempts. The current typosquatting detection catches similarity but not domain age. A domain registered days ago for a company that's been operating for 15 years is highly suspicious.

**Example from Azelis fraud case:**
- Company founded: 2010 (15 years old)
- Fraudulent domain `acelis.com.co` registered: 2024 (< 1 year old)
- **Red flag**: Domain age is < 10% of company age

## Solution Statement

1. Add DNS lookup using `socket.gethostbyname()` to verify domain existence
2. Add WHOIS lookup using `python-whois` library to get domain creation date
3. Compare domain age against company age from documents (RUT `registration_date`, Certificado `constitution_date`)
4. Flag non-existent domains as CRITICAL severity (25 points)
5. Flag young domains as HIGH/MEDIUM severity based on thresholds:
   - Domain < 90 days old → HIGH (15 points)
   - Domain < 1 year AND < 10% of company age → HIGH (15 points)
   - Domain < 1 year (no company date available) → MEDIUM (8 points)
6. Integrate validation into cross-validation, email chains, and external contacts services
7. Display results in frontend with severity-colored indicators
8. Cache WHOIS results for 24 hours to avoid rate limiting

## Access Control

- Required Role(s): `admin`, `legal`, `operations`, `analyst`, `mesa_control`
- Backend Protection: Existing risk assessment routes already protected by RBAC via `require_roles()` in `rbac_dependencies.py`
- Frontend Protection: Risk dashboard already protected by `RoleProtectedRoute` - no changes needed

## Relevant Files

Use these files to implement the feature:

### Backend - Core Services (to modify)
- `backend/src/core/servicios/risk/cross_validation_service.py` - Main cross-validation service that validates documents. Add domain age validation in `_validate_email_domain()` method.
- `backend/src/core/servicios/risk/email_chain_service.py` - Email chain validation service. Add domain age validation for sender domains in `validate_email_chain()`.
- `backend/src/core/servicios/risk/external_contact_service.py` - External contact email validation. Add domain age validation in `validate_email()` method.
- `backend/src/core/servicios/risk/typosquatting_service.py` - Reference for domain handling patterns.
- `backend/src/core/servicios/risk/normalization_service.py` - Reference for data normalization patterns.

### Backend - DTOs and Types (to modify)
- `backend/src/interface/risk_dtos.py` - Add new `ValidationType` enum values (`DOMAIN_EXISTENCE`, `DOMAIN_AGE`) and update `EmailValidationResult` model with new fields.

### Backend - Dependencies
- `backend/requirements.txt` - Add `python-whois>=0.8.0` dependency.

### Frontend - Components (to modify)
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Display domain age validation results with severity colors.
- `frontend/src/components/risk/FKExternalContactTab.tsx` - Show domain age in external contact validation results.
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Display domain age validation for sender domains.
- `frontend/src/components/risk/FKEmailValidationResult.tsx` - Update email validation result display to show domain age.

### Frontend - Types (to modify)
- `frontend/src/types/risk.ts` - Add new `ValidationType` values and update `EmailValidationResult` interface with domain age fields.

### New Files

- `backend/src/core/servicios/risk/domain_validation_service.py` - **New service** implementing DNS lookup, WHOIS lookup, domain age validation, and caching.
- `backend/tests/test_domain_validation_service.py` - **Unit tests** for the new domain validation service.
- `.claude/commands/e2e/test_domain_age_validation.md` - **E2E test file** for domain age validation feature.

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### F. External API Contract (Integration only)

**DNS Lookup (socket.gethostbyname):**
| Operation | Method | Auth | Input | Output |
|-----------|--------|------|-------|--------|
| Domain resolution | `socket.gethostbyname(domain)` | None (system call) | Domain string | IP address or socket.gaierror |

**WHOIS Lookup (python-whois):**
| Operation | Method | Auth | Input | Output |
|-----------|--------|------|-------|--------|
| WHOIS query | `whois.whois(domain)` | None (public WHOIS) | Domain string | WhoisData object with creation_date, registrar, etc. |

**Error Handling Strategy:**
- DNS timeout (5s): Mark domain existence as "unknown", log warning, no discrepancy created
- WHOIS timeout (10s): Mark age as "unavailable", continue validation, no penalty
- WHOIS privacy/blocked: Return `lookup_status="unavailable"`, no penalty
- Invalid domain format: Return early, no network calls
- Rate limiting: Cache results for 24 hours to reduce queries

### D. Data Contract Verification (ALL features)

| Repository/Service Method | Return Type | Access Pattern | Example |
|---------------------------|-------------|----------------|---------|
| `cross_validation_service._validate_email_domain()` | `List[CrossValidationResult]` | List of result objects | `results.append(result)` |
| `external_contact_service.validate_email()` | `dict` | Dict from repository | `contact['email']` |
| `email_chain_service.validate_email_chain()` | `dict` | Dict from repository | `chain['assessment_id']` |
| `domain_validation_service.check_domain_existence()` | `DomainExistenceResult` | Dataclass | `result.exists` |
| `domain_validation_service.get_domain_age()` | `DomainAgeResult` | Dataclass | `result.creation_date` |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|----------------|---------------|------|-------|
| domain_exists | domain_exists | boolean | null = unknown/pending |
| domain_age_days | domain_age_days | number | null = unavailable |
| domain_creation_date | domain_creation_date | string (ISO datetime) | null = unavailable |
| age_lookup_status | age_lookup_status | string | 'success', 'failed', 'unavailable' |
| domain_registrar | domain_registrar | string | null = unavailable |

## Implementation Plan

### Phase 1: Foundation
1. Add `python-whois>=0.8.0` to `backend/requirements.txt`
2. Add new `ValidationType` enum values (`DOMAIN_EXISTENCE`, `DOMAIN_AGE`) to `risk_dtos.py`
3. Create `DomainValidationService` class with DNS and WHOIS logic
4. Implement in-memory cache with 24-hour TTL
5. Write unit tests for the new service

### Phase 2: Core Backend Integration
6. Modify `cross_validation_service.py`:
   - Import `DomainValidationService`
   - Extract `registration_date` from RUT and `constitution_date` from Certificado
   - Call domain validation in `_validate_email_domain()`
   - Add `CrossValidationResult` entries for domain existence and age checks
7. Modify `email_chain_service.py`:
   - Integrate domain validation for sender domains in `validate_email_chain()`
8. Modify `external_contact_service.py`:
   - Integrate domain validation in `validate_email()`
   - Update returned data with new fields

### Phase 3: Frontend UI Updates
9. Update `frontend/src/types/risk.ts`:
   - Add `domain_existence` and `domain_age` to `ValidationType`
   - Extend `EmailValidationResult` interface
   - Add labels for new validation types
10. Update `FKCrossValidationResults.tsx`:
    - Display domain existence and age validation results
    - Show severity colors based on domain age
11. Update `FKExternalContactTab.tsx` and `FKEmailValidationResult.tsx`:
    - Display domain age information
12. Update `FKEmailChainUploader.tsx`:
    - Show domain age for sender domains

### Phase 4: Testing
13. Create E2E test file for domain age validation
14. Run full test suite
15. Validate all validation commands pass

## Step by Step Tasks

### Step 1: Add python-whois dependency
- Open `backend/requirements.txt`
- Add `python-whois>=0.8.0` after the existing dependencies in alphabetical order or in an appropriate section
- Verify no conflicts with existing packages

### Step 2: Update ValidationType enum in DTOs
- Open `backend/src/interface/risk_dtos.py`
- Add to `ValidationType` enum:
  ```python
  DOMAIN_EXISTENCE = "domain_existence"
  DOMAIN_AGE = "domain_age"
  ```
- Add new fields to `EmailValidationResult`:
  ```python
  domain_exists: Optional[bool] = None
  domain_age_days: Optional[int] = None
  domain_creation_date: Optional[datetime] = None
  age_lookup_status: str = "pending"  # 'success', 'failed', 'unavailable', 'pending'
  domain_registrar: Optional[str] = None
  ```

### Step 3: Create DomainValidationService
- Create `backend/src/core/servicios/risk/domain_validation_service.py`
- Implement dataclasses:
  - `DomainExistenceResult`: domain, exists, error_message
  - `DomainAgeResult`: domain, creation_date, age_days, registrar, lookup_status
  - `DomainCompanyAgeComparison`: all fields for comparison result
- Implement `DomainValidationService` class:
  - Configuration constants: `DNS_TIMEOUT = 5`, `WHOIS_TIMEOUT = 10`, `CACHE_TTL = 86400`
  - Threshold constants: `VERY_YOUNG_THRESHOLD = 90`, `YOUNG_THRESHOLD = 365`, `SUSPICIOUS_AGE_RATIO = 0.1`
  - `check_domain_existence(domain: str) -> DomainExistenceResult`: Use `socket.gethostbyname()` with timeout
  - `get_domain_age(domain: str) -> DomainAgeResult`: Use `whois.whois()`, cache results
  - `compare_domain_vs_company_age(domain, company_registration_date, company_constitution_date) -> DomainCompanyAgeComparison`
  - `_validate_domain_format(domain: str) -> bool`: Basic domain format validation
  - Implement in-memory cache with TTL for WHOIS results

### Step 4: Write unit tests for DomainValidationService
- Create `backend/tests/test_domain_validation_service.py`
- Test cases:
  - `test_existing_domain_resolves`: google.com should resolve
  - `test_nonexistent_domain_fails`: random gibberish domain fails
  - `test_dns_timeout_handled_gracefully`: Mock timeout, verify graceful handling
  - `test_whois_returns_creation_date`: Mock WHOIS response with creation date
  - `test_whois_failure_handled_gracefully`: Mock WHOIS failure
  - `test_cache_works`: Second call returns cached result
  - `test_young_domain_vs_old_company_flagged`: Domain < 90 days, company > 5 years
  - `test_old_domain_ok`: Domain > 5 years, no issue
  - `test_invalid_domain_format_returns_early`: Invalid format, no network calls

### Step 5: Integrate into cross_validation_service.py
- Open `backend/src/core/servicios/risk/cross_validation_service.py`
- Import `DomainValidationService`
- Add `domain_validation_service` to `__init__` with optional parameter
- Modify `_validate_email_domain()` method:
  1. After existing typosquatting check, add domain existence check
  2. If domain doesn't exist, create CRITICAL discrepancy (25 points)
  3. Extract company dates from extractions:
     - RUT: `extracted_data.get('registration_date')` or `extracted_data.get('fecha_inscripcion')`
     - Certificado: `extracted_data.get('constitution_date')` or `extracted_data.get('fecha_constitucion')`
  4. Call `domain_validation_service.compare_domain_vs_company_age()`
  5. Create appropriate discrepancy based on result:
     - Domain < 90 days: HIGH severity (15 points)
     - Domain < 1 year AND < 10% company age: HIGH severity (15 points)
     - Domain < 1 year (no company date): MEDIUM severity (8 points)
     - WHOIS unavailable: No discrepancy (info only)

### Step 6: Integrate into email_chain_service.py
- Open `backend/src/core/servicios/risk/email_chain_service.py`
- Import `DomainValidationService`
- Add `domain_validation_service` to `__init__`
- In `validate_email_chain()` method, after sender domain validation:
  1. Call `domain_validation_service.check_domain_existence(domain)`
  2. If domain doesn't exist, add CRITICAL discrepancy
  3. Call `domain_validation_service.get_domain_age(domain)`
  4. If domain < 90 days, add HIGH severity discrepancy
  5. Include domain age info in validation result

### Step 7: Integrate into external_contact_service.py
- Open `backend/src/core/servicios/risk/external_contact_service.py`
- Import `DomainValidationService`
- Add `domain_validation_service` to `__init__`
- In `validate_email()` method:
  1. After typosquatting check, call domain existence check
  2. Call domain age check
  3. Update `EmailValidationResult` with new fields:
     - `domain_exists`
     - `domain_age_days`
     - `domain_creation_date`
     - `age_lookup_status`
     - `domain_registrar`
  4. Adjust `_determine_status()` to factor in domain age

### Step 8: Update frontend TypeScript types
- Open `frontend/src/types/risk.ts`
- Add to `ValidationType` union:
  ```typescript
  | 'domain_existence'
  | 'domain_age'
  ```
- Update `EmailValidationResult` interface:
  ```typescript
  domain_exists?: boolean | null;
  domain_age_days?: number | null;
  domain_creation_date?: string | null;
  age_lookup_status?: string;
  domain_registrar?: string | null;
  ```
- Add to `VALIDATION_TYPE_LABELS`:
  ```typescript
  domain_existence: 'Existencia de Dominio',
  domain_age: 'Antigüedad de Dominio',
  ```

### Step 9: Update FKCrossValidationResults component
- Open `frontend/src/components/risk/FKCrossValidationResults.tsx`
- Ensure new validation types are properly displayed
- The component already handles all `ValidationType` values via `VALIDATION_TYPE_LABELS`
- Verify domain age discrepancies show with correct severity colors
- Consider adding special display for domain age showing days/years

### Step 10: Update FKEmailValidationResult component
- Open `frontend/src/components/risk/FKEmailValidationResult.tsx`
- Add display for domain age information:
  - Show domain creation date if available
  - Show domain age in days/years
  - Show registrar if available
  - Use appropriate severity colors for young domains

### Step 11: Update FKExternalContactTab component
- Open `frontend/src/components/risk/FKExternalContactTab.tsx`
- Ensure `FKEmailValidationResult` displays new fields
- No additional changes needed if `FKEmailValidationResult` handles display

### Step 12: Update FKEmailChainUploader component
- Open `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Add domain age info to expanded details section
- Show domain existence status
- Display domain creation date and age for sender domains

### Step 13: Create E2E test file
- Read `.claude/commands/test_e2e.md` for E2E test format
- Read `.claude/commands/e2e/test_login.md` for example
- Create `.claude/commands/e2e/test_domain_age_validation.md`
- Define test steps:
  1. Login as risk analyst
  2. Navigate to risk evaluation
  3. Upload document with email
  4. Trigger cross-validation
  5. Verify domain age validation results appear
  6. Verify severity colors are correct
  7. Take screenshots at key steps

### Step 14: Run validation commands
- Execute all validation commands to ensure zero regressions
- Fix any issues that arise

## Testing Strategy

### Unit Tests
- `test_domain_validation_service.py`:
  - DNS resolution for existing domains
  - DNS failure for non-existent domains
  - WHOIS retrieval with valid domain
  - WHOIS failure handling
  - Cache functionality
  - Domain age comparison logic
  - Threshold severity mappings

### Edge Cases
- Domain with WHOIS privacy protection (no creation date)
- Domain with multiple creation dates in WHOIS response
- Newly registered domain (< 1 day old)
- International TLDs with different WHOIS formats
- Domains that exist but have no A record (only MX)
- Network timeouts during DNS or WHOIS lookup
- Invalid domain format (special characters, too long)
- Empty domain string
- Company with no registration date in documents

## Acceptance Criteria

- [ ] DNS lookup correctly identifies non-existent domains
- [ ] WHOIS lookup retrieves domain creation date
- [ ] WHOIS results are cached for 24 hours
- [ ] Timeouts are handled gracefully (no crashes)
- [ ] Domain < 90 days old flags as HIGH severity (15 points)
- [ ] Domain age compared against company age from documents
- [ ] Non-existent domains flag as CRITICAL severity (25 points)
- [ ] CrossValidationService includes domain existence and age checks
- [ ] EmailChainService includes domain existence and age checks
- [ ] ExternalContactService includes domain existence and age checks
- [ ] Frontend displays domain age validation results
- [ ] Severity colors correctly applied in frontend
- [ ] Unit tests pass
- [ ] E2E test passes
- [ ] All validation commands pass with zero errors

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_domain_age_validation.md` E2E test to validate this functionality works
- `cd backend && python -m pytest tests/test_domain_validation_service.py -v` - Run domain validation unit tests
- `cd backend && python -m pytest` - Run all backend tests to validate zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

- **New dependency**: `python-whois>=0.8.0` must be added to requirements.txt
- **WHOIS rate limiting**: WHOIS servers may rate limit. The 24-hour cache mitigates this.
- **WHOIS privacy**: Some domains have privacy protection. Handle gracefully with no penalty.
- **WHOIS response format**: `creation_date` may be a single datetime or a list. Handle both.
- **Company date fields**: Check multiple field names for company dates (Spanish and English variants):
  - RUT: `registration_date`, `fecha_inscripcion`, `fecha_registro`
  - Certificado: `constitution_date`, `fecha_constitucion`, `fecha_creacion`
- **Priority for company date**: Use `constitution_date` (most reliable), fallback to `registration_date`
- **DNS timeout**: 5 seconds is sufficient for most cases. Lower may cause false negatives.
- **Socket handling**: Use `socket.setdefaulttimeout()` or wrap in try/except with timeout handling.
- **Testing with real domains**: Unit tests should mock network calls for reliability. Integration tests can use real domains.
- **TLD-specific WHOIS**: Different TLDs have different WHOIS servers. `python-whois` handles this automatically.

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (API Integration)
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed - no new tables)
- [x] E2E test file task included (Step 13)
- [x] All external dependencies (npm/pip packages) listed in Notes (`python-whois>=0.8.0`)

### Category-Specific Completeness

**API Integration:**
- [x] External API contract documented (DNS, WHOIS)
- [x] Auth method specified (none - public services)
- [x] Error/retry strategy defined (timeout handling, caching)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) - N/A for this feature

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
