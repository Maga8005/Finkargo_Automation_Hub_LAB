# Feature: Email Domain Validation Against Official Documents

## Feature Description
Add email chain sender domain validation against official document (RUT and Certificado de Existencia) email domains. When an email chain is validated, the system should compare the sender's email domain against the official email domains extracted from RUT and Certificado de Existencia documents. If there is a mismatch (even a subtle one like `@azelis.com` vs `@azelis.com.co`), the system should flag this as a CRITICAL discrepancy requiring manual revision, as it may indicate typosquatting fraud.

## User Story
As a **Risk Analyst or Risk Manager**
I want to validate email chain sender domains against official document email domains
So that I can detect potential fraud attempts where attackers use similar-looking domains (typosquatting) to impersonate legitimate companies

## Problem Statement
Currently, the email chain validation system extracts sender domains and validates them against known domains, free email providers, and performs typosquatting detection against company names. However, it does NOT directly compare the email chain sender domain against the official email domains extracted from RUT and Certificado de Existencia documents.

This creates a critical gap: if a fraudster sends emails from `contacto@azelis.com.co` but the RUT shows the official company email as `contacto@azelis.com`, this mismatch is NOT detected. Official government documents (RUT, Certificado de Existencia) provide authoritative email domain information that should serve as the primary source of truth.

## Solution Statement
Enhance the `EmailChainService.validate_email_chain()` method to:
1. Track official email domains separately from general email domains during document data extraction
2. Add a new validation step that compares email chain sender domains against official document email domains
3. Flag any mismatch as a CRITICAL discrepancy with field type `official_document_domain`
4. Use the existing `TyposquattingService` to detect subtle variations (TLD variations, typosquatting)
5. Update the frontend to display this new discrepancy field with appropriate labeling

The key principle: **If the sender domain doesn't exactly match an official document email domain, and no documents have email domains to compare against, the validation passes. But if documents DO have email domains and the sender domain differs, it's a CRITICAL flag.**

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: RBAC dependencies already in place for risk routes (`require_roles(['risk_analyst', 'risk_manager', 'admin'])`)
- Frontend Protection: Existing `RoleProtectedRoute` configuration for `/risk/*` routes

## Relevant Files
Use these files to implement the feature:

**Backend - Core Service Layer:**
- `backend/src/core/servicios/risk/email_chain_service.py` - Main service that performs email chain validation. **This is where the primary changes will be made.** The `_get_document_data()` method needs to track official document email domains separately, and a new `_validate_against_official_document_domains()` method needs to be added.
- `backend/src/core/servicios/risk/typosquatting_service.py` - Existing typosquatting detection service that will be reused for domain comparison.
- `backend/src/core/servicios/risk/normalization_service.py` - Provides email domain extraction utilities.

**Backend - DTOs:**
- `backend/src/interface/risk_dtos.py` - No changes needed; the existing `EmailChainDiscrepancy` model already supports the required fields.

**Frontend - Types:**
- `frontend/src/types/risk.ts` - Needs to add `official_document_domain` to `EMAIL_CHAIN_FIELD_LABELS` constant.

**Frontend - Components:**
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - No code changes needed; already dynamically uses `EMAIL_CHAIN_FIELD_LABELS` for display.

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format
- `.claude/commands/e2e/test_email_chain_validation.md` - Existing email chain validation test (reference)

### New Files
- `.claude/commands/e2e/test_email_domain_official_document_validation.md` - E2E test to validate the new official document domain comparison feature

## Pre-Implementation Verification

### Feature Category
- [x] CRUD Operations (basic data management) → Complete sections D, E

This feature enhances existing validation logic without requiring database changes, new templates, or external API integrations.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `extraction_repo.get_by_assessment()` | `List[dict]` | `extraction['extracted_data']` | Already used in `_get_document_data()` |
| `chain_repo.get_by_id()` | `dict` | `chain['parsed_data']` | Already used in `validate_email_chain()` |
| `assessment_repo.get_by_id()` | `dict` | `assessment['client_data_snapshot']` | Already used in `validate_email_chain()` |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs - `DiscrepancySeverity.CRITICAL` already exists
- [x] No template files needed
- [x] No database migrations needed - no schema changes required
- [x] Country-specific data handled - Not applicable (domain comparison is universal)

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `EMAIL_CHAIN_FIELD_LABELS['official_document_domain']` | discrepancy.field = 'official_document_domain' | string | New field label |
| `EmailChainDiscrepancy.field` | `field` | string | Already supports arbitrary strings |
| `EmailChainDiscrepancy.severity` | `severity` | DiscrepancySeverity | Use `critical` |
| `EmailChainDiscrepancy.is_typosquatting` | `is_typosquatting` | boolean | Set to `True` when TLD variation or typosquatting detected |

## Implementation Plan

### Phase 1: Foundation
No foundational changes needed - all required infrastructure exists:
- `TyposquattingService` already provides domain comparison
- `NormalizationService` already extracts email domains
- `EmailChainDiscrepancy` model supports the required fields
- `EMAIL_CHAIN_FIELD_LABELS` is a simple object addition

### Phase 2: Core Implementation
1. **Enhance `_get_document_data()` in `email_chain_service.py`:**
   - Add separate tracking for `official_document_domains` from RUT and Certificado de Existencia
   - Keep existing `email_domains` for backward compatibility
   - Extract from document types: `DocumentType.RUT` and `DocumentType.CERTIFICADO_EXISTENCIA`

2. **Add new `_validate_against_official_document_domains()` method:**
   - Compare sender domain against all official document domains
   - Use `TyposquattingService.check_domain_typosquatting()` for similarity detection
   - Return CRITICAL discrepancy if mismatch detected
   - Handle edge cases: no official domains available, exact matches, partial matches

3. **Update `validate_email_chain()` to call the new validation method:**
   - Add call after existing sender domain validation
   - Append results to discrepancies list

4. **Update frontend `EMAIL_CHAIN_FIELD_LABELS`:**
   - Add `'official_document_domain': 'Dominio Email Documento Oficial'`

### Phase 3: Integration
- The feature integrates seamlessly with existing validation flow
- No routing or navigation changes needed
- No role protection changes needed (already protected)

## Step by Step Tasks

### Step 1: Create E2E Test Specification
Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand the E2E test format.

Create `.claude/commands/e2e/test_email_domain_official_document_validation.md` with test steps that:
- Upload an email chain with sender domain `@empresa-fake.com.co`
- Upload RUT document with official email `contacto@empresa-fake.com`
- Trigger validation
- Verify CRITICAL discrepancy is displayed for `official_document_domain`
- Verify the description mentions the mismatch

### Step 2: Enhance Document Data Extraction
Modify `backend/src/core/servicios/risk/email_chain_service.py`:

- Update `_get_document_data()` method to:
  - Add `official_document_domains: List[str]` to the returned dict
  - Extract email domains specifically from RUT and Certificado de Existencia documents
  - Use document type checking to identify official documents
  - Normalize domains to lowercase

```python
# Add to doc_data initialization:
doc_data = {
    'company_names': [],
    'nits': [],
    'representative_names': [],
    'email_domains': [],
    'official_document_domains': [],  # NEW: Track official doc domains separately
}

# Add logic to identify RUT and Certificado de Existencia:
doc_type = extraction.get('document_type', '')
is_official_doc = doc_type in ['rut', 'certificado_existencia']

# When extracting email domains, also add to official_document_domains if applicable
```

### Step 3: Add Official Document Domain Validation Method
Add new method `_validate_against_official_document_domains()` to `EmailChainService`:

```python
def _validate_against_official_document_domains(
    self,
    sender_domain: str,
    official_domains: List[str],
) -> Optional[dict]:
    """
    Validate sender domain against official document email domains.

    Args:
        sender_domain: Email domain from email chain sender
        official_domains: Email domains extracted from RUT/Certificado de Existencia

    Returns:
        Optional[dict]: Discrepancy if mismatch found, None if match or no official domains
    """
```

Key implementation details:
- If `official_domains` is empty, return `None` (no comparison possible)
- If `sender_domain` exactly matches any official domain, return `None`
- Use `TyposquattingService.check_domain_typosquatting()` to detect:
  - Typosquatting (similar domain name, different)
  - TLD variations (e.g., `.com` vs `.com.co`)
- Return discrepancy with:
  - `field: 'official_document_domain'`
  - `severity: DiscrepancySeverity.CRITICAL.value`
  - `is_typosquatting: True` if typosquatting/TLD variation detected
  - Descriptive message mentioning the specific domains compared

### Step 4: Integrate Validation in Main Flow
Update `validate_email_chain()` method:

- After line 197 (after sender domain validation loop), add:
```python
# 1b. Validate sender domains against official document domains
official_domains = doc_data.get('official_document_domains', [])
for domain in sender_domains:
    disc = self._validate_against_official_document_domains(domain, official_domains)
    if disc:
        discrepancies.append(disc)
```

### Step 5: Update Frontend Field Labels
Modify `frontend/src/types/risk.ts`:

Update `EMAIL_CHAIN_FIELD_LABELS` to include the new field:
```typescript
export const EMAIL_CHAIN_FIELD_LABELS: Record<string, string> = {
  sender_domain: 'Dominio del Remitente',
  company_name: 'Nombre de Empresa',
  nit: 'NIT',
  representative_name: 'Representante Legal',
  official_document_domain: 'Dominio Email Documento Oficial',  // NEW
};
```

### Step 6: Add Unit Tests
Create or update tests in `backend/tests/` to cover:
- `_validate_against_official_document_domains()` with:
  - Empty official domains (should return None)
  - Exact match (should return None)
  - TLD variation mismatch (.com vs .com.co)
  - Typosquatting mismatch (azelis vs acelis)
  - Complete mismatch (different domains entirely)

### Step 7: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests
Backend tests for the new `_validate_against_official_document_domains()` method:

```python
# Test cases:
def test_validate_official_domain_no_official_domains():
    """Should return None when no official domains available"""

def test_validate_official_domain_exact_match():
    """Should return None when sender domain exactly matches official domain"""

def test_validate_official_domain_tld_variation():
    """Should return CRITICAL discrepancy for TLD variation (azelis.com vs azelis.com.co)"""

def test_validate_official_domain_typosquatting():
    """Should return CRITICAL discrepancy for typosquatting (azelis vs acelis)"""

def test_validate_official_domain_completely_different():
    """Should return CRITICAL discrepancy for completely different domains"""

def test_validate_official_domain_case_insensitive():
    """Should match domains case-insensitively"""
```

### Edge Cases
- Email chain sender uses a subdomain (e.g., `ventas.azelis.com` vs `azelis.com`)
- Multiple sender domains in the email chain
- Multiple official domains from different documents (RUT and Certificado)
- Free email provider as sender (should still flag if official domain exists)
- Official document email field is empty or malformed

## Acceptance Criteria
1. When an email chain is validated, sender domains are compared against official document (RUT/Certificado de Existencia) email domains
2. If no official document email domains are available, validation passes without discrepancy for this check
3. If sender domain exactly matches an official document email domain, validation passes
4. If sender domain differs from official document email domain (TLD variation, typosquatting, or complete mismatch), a CRITICAL discrepancy is flagged
5. The discrepancy field is labeled `'official_document_domain'`
6. Frontend displays the discrepancy with label "Dominio Email Documento Oficial"
7. The discrepancy description clearly explains the mismatch (e.g., "Email sender domain 'azelis.com.co' differs from official document email domain 'azelis.com'")
8. All existing email chain validation functionality continues to work (no regressions)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. **Backend Unit Tests:**
   ```bash
   cd backend && python -m pytest tests/ -v
   ```

2. **Backend Linting:**
   ```bash
   cd backend && ruff check src/
   ```

3. **Frontend Linting:**
   ```bash
   cd frontend && npm run lint
   ```

4. **TypeScript Type Check:**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

5. **Frontend Build:**
   ```bash
   cd frontend && npm run build
   ```

6. **E2E Test (after creating test file):**
   - Read `.claude/commands/test_e2e.md`
   - Read and execute `.claude/commands/e2e/test_email_domain_official_document_validation.md`

## Notes

### Implementation Considerations
- The existing `_validate_sender_domain()` method performs typosquatting detection against the `client_snapshot` company name. The new validation is **complementary** - it specifically targets official document email domains which are more authoritative.
- The validation should run AFTER the existing sender domain validation to catch cases where the sender domain appears legitimate but differs from official records.

### Future Enhancements
- Consider adding a configuration option to make this validation HIGH severity instead of CRITICAL for certain use cases
- Consider extracting email domains from additional document types if they contain official contact information
- Consider adding a "known variation" allowlist for companies with multiple legitimate domains

### No New Dependencies Required
All required functionality is available through existing services:
- `TyposquattingService` for domain comparison
- `NormalizationService` for domain extraction
- Existing DTOs and types support the new discrepancy field

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (N/A - domain comparison is universal)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable (N/A)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (Step 1)
