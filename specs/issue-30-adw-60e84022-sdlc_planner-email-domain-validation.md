# Feature: Email Domain Validation Against RUT/Certificado de Existencia

## Feature Description
Implement email domain cross-validation between email chain sender domains and official document-extracted email domains (RUT or Certificado de Existencia). When an email chain's sender domain differs from the email domain extracted from official government documents, the system should flag the record for manual revision with a critical severity alert. This addresses potential typosquatting fraud scenarios where fraudsters use visually similar but different domains to impersonate legitimate companies.

## User Story
As a Risk Analyst
I want the system to automatically compare email chain sender domains against email domains extracted from RUT or Certificado de Existencia documents
So that I can detect potential typosquatting fraud attempts where email domains look similar but are actually different (e.g., @azelis.com vs @azelis.com.co)

## Problem Statement
Currently, the Riesgos module validates email chain data against document-extracted data for company names, NITs, and representative names. However, the critical comparison between email chain sender domains and the official email domains from RUT or Certificado de Existencia documents is NOT being performed. This gap allows potential fraud attempts where:
1. A fraudster uses a domain similar to the legitimate company (typosquatting)
2. The RUT or Certificado shows the legitimate email domain (e.g., @azelis.com)
3. The email chain contains a lookalike domain (e.g., @azelis.com.co)
4. This mismatch should be flagged as CRITICAL because the RUT/Certificado are official government documents

## Solution Statement
Enhance the email chain validation service to:
1. Extract email domains from RUT and Certificado de Existencia document extractions
2. Compare email chain sender domains against these official document domains
3. Flag any mismatches as CRITICAL severity discrepancies
4. Ensure the entire record requires manual verification when such a mismatch occurs
5. Display clear warnings in the UI about official vs email chain domain discrepancies

## Access Control
- Required Role(s): risk_analyst, risk_manager, admin
- Backend Protection: Existing RBAC dependencies in risk_routes.py
- Frontend Protection: Existing role protection in RiskEvaluationDetail.tsx

## Relevant Files
Use these files to implement the feature:

### Backend Files
- `backend/src/core/servicios/risk/email_chain_service.py` - Main email chain validation service. **Add new validation method to compare sender domains against RUT/Certificado domains**
- `backend/src/core/servicios/risk/cross_validation_service.py` - Cross-validation patterns to follow. **Reference for validation result structures and severity handling**
- `backend/src/core/servicios/risk/typosquatting_service.py` - Domain comparison utilities. **Use for domain similarity detection**
- `backend/src/core/servicios/risk/normalization_service.py` - Data normalization utilities. **Use for email domain extraction and normalization**
- `backend/src/interface/risk_dtos.py` - DTOs for validation. **May need new validation type or extend existing EmailChainDiscrepancy**
- `backend/src/repositorio/risk_repository.py` - Repository for document extractions. **DocumentExtractionRepository already available for fetching document data**

### Frontend Files
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - Email chain validation UI. **Update to display official document domain comparison results**
- `frontend/src/types/risk.ts` - TypeScript types. **May need to extend EmailChainDiscrepancy or add new field labels**

### Test Files
- `backend/tests/test_typosquatting_service.py` - Existing typosquatting tests. **Add tests for official document domain comparison**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_email_chain_validation.md` - Existing email chain E2E test. **Reference for test structure**
- `.claude/commands/e2e/test_login.md` - Login test example for E2E format

### New Files
- `.claude/commands/e2e/test_email_domain_official_document_validation.md` - New E2E test file for this feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this feature modifies validation logic, not document generation.

### B. Excel Column Mapping (Excel Processing only)
Not applicable - this feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)
Not applicable - this feature does not involve file import/export.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| extraction_repo.get_by_assessment(id) | List[dict] | data['extracted_data'] | Get extracted document data |
| chain_repo.get_by_id(id) | dict | chain['parsed_data'] | Get email chain parsed data |
| assessment_repo.get_by_id(id) | dict | assessment['client_data_snapshot'] | Get client data snapshot |

**Email Domain Extraction Fields in Documents:**
| Document Type | Field | Example Value |
|--------------|-------|---------------|
| RUT | `email`, `correo`, `email_empresa` | contacto@azelis.com |
| Certificado de Existencia | `email`, `correo` | info@azelis.com |

**Email Chain Sender Domain:**
| Source | Field | Example Value |
|--------|-------|---------------|
| Parsed Email Message | `sender_domain` | azelis.com.co |
| Extracted Mentions | `mentions.domains` | ['azelis.com.co'] |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs (DiscrepancySeverity, ValidationType already exist)
- [ ] Template file exists in `backend/templates/` - Not applicable
- [x] Database records exist - Uses existing document_extractions and email_chains tables
- [ ] Country-specific data handled - Not applicable, domain validation is universal

### F. External API Contract (Integration only)
Not applicable - this feature does not involve external APIs.

### G. Query Specification (Reporting only)
Not applicable - this feature does not involve reporting queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| discrepancy.field | field | string | 'official_document_domain' (new value) |
| discrepancy.email_value | email_value | string | Email chain sender domain |
| discrepancy.document_value | document_value | string | RUT/Certificado domain |
| discrepancy.severity | severity | DiscrepancySeverity | CRITICAL for official doc mismatch |
| discrepancy.is_typosquatting | is_typosquatting | boolean | True if domains are similar |
| discrepancy.similarity_score | similarity_score | number | Similarity between domains |

## Implementation Plan

### Phase 1: Foundation
- Update `_get_document_data()` method in email_chain_service.py to extract email domains from RUT and Certificado de Existencia specifically, marking them as "official document domains"
- Add field label for the new discrepancy type in frontend types

### Phase 2: Core Implementation
- Add new validation method `_validate_against_official_document_domains()` in EmailChainService
- Integrate the new validation into the existing `validate_email_chain()` flow
- Ensure CRITICAL severity is used when official document domain mismatches are found
- Use TyposquattingService for domain comparison to detect similar but different domains

### Phase 3: Integration
- Update FKEmailChainUploader to display the new discrepancy type with clear labeling
- Add field label mapping in risk.ts for UI display
- Create E2E test to validate the feature works correctly

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_email_chain_validation.md` to understand E2E test format
- Create `.claude/commands/e2e/test_email_domain_official_document_validation.md` with:
  - User Story describing the official document domain validation scenario
  - Prerequisites (servers running, test account, evaluation with RUT/Certificado uploaded)
  - Test Steps to:
    1. Login with risk_analyst role
    2. Navigate to an evaluation with RUT/Certificado documents uploaded
    3. Upload an email chain with a domain that differs from official document (e.g., @azelis.com.co vs @azelis.com from RUT)
    4. Validate the email chain
    5. Verify CRITICAL discrepancy is shown for "Dominio de Email Oficial"
    6. Verify the evaluation is marked for manual verification
  - Success Criteria specifying the expected discrepancy display

### Step 2: Add Field Label for New Discrepancy Type
- Edit `frontend/src/types/risk.ts`
- Add new entry to `EMAIL_CHAIN_FIELD_LABELS` constant:
  ```typescript
  official_document_domain: 'Dominio de Email (Documento Oficial)',
  ```
- This label will be used when displaying discrepancies from official document domain comparisons

### Step 3: Enhance _get_document_data() Method
- Edit `backend/src/core/servicios/risk/email_chain_service.py`
- Modify `_get_document_data()` to separately track official document domains:
  - Add `official_email_domains` list to the return dict
  - When extracting from RUT or Certificado de Existencia documents, add domains to `official_email_domains`
  - Keep track of which document type each domain came from (for better error messages)

### Step 4: Add Official Document Domain Validation Method
- Edit `backend/src/core/servicios/risk/email_chain_service.py`
- Add new method `_validate_against_official_document_domains()`:
  - Takes sender domain, official_email_domains, and known_domains
  - Uses TyposquattingService to compare sender domain against official domains
  - If sender domain exactly matches an official domain → no discrepancy
  - If sender domain is similar but different (typosquatting) → CRITICAL discrepancy with `is_typosquatting=True`
  - If sender domain is completely different from all official domains → HIGH or CRITICAL discrepancy
  - Returns EmailChainDiscrepancy with field='official_document_domain'

### Step 5: Integrate New Validation into validate_email_chain()
- Edit `backend/src/core/servicios/risk/email_chain_service.py`
- In `validate_email_chain()` method, after getting document data:
  - Check if `official_email_domains` is available in doc_data
  - For each sender domain, call `_validate_against_official_document_domains()`
  - Add any discrepancies to the list
  - Ensure official document domain mismatches are treated as CRITICAL
- Ensure the existing `_validate_sender_domain()` continues to work for typosquatting detection against known domains

### Step 6: Write Unit Tests for New Validation Logic
- Edit `backend/tests/test_typosquatting_service.py` or create `backend/tests/test_email_chain_service.py`
- Add test cases:
  - `test_official_domain_exact_match()` - sender domain matches RUT domain exactly → no discrepancy
  - `test_official_domain_tld_variation()` - sender @azelis.com.co vs RUT @azelis.com → CRITICAL discrepancy
  - `test_official_domain_typosquatting()` - sender @acelis.com vs RUT @azelis.com → CRITICAL with is_typosquatting=True
  - `test_official_domain_completely_different()` - sender @gmail.com vs RUT @azelis.com → appropriate severity
  - `test_no_official_domains_available()` - when RUT/Certificado have no email → skip validation

### Step 7: Update UI Field Label Display
- Verify `FKEmailChainUploader.tsx` correctly displays discrepancies with the new field type
- The existing `EMAIL_CHAIN_FIELD_LABELS[disc.field]` lookup will use the new label
- No code changes needed if the label mapping is correct

### Step 8: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- Test official document domain extraction from RUT extractions
- Test official document domain extraction from Certificado de Existencia extractions
- Test domain comparison when official domain matches sender domain
- Test domain comparison when TLD varies (e.g., .com vs .com.co)
- Test domain comparison for typosquatting (single character differences)
- Test that CRITICAL severity is correctly assigned for official document mismatches
- Test that is_typosquatting flag is set correctly

### Edge Cases
- RUT has email domain but Certificado de Existencia does not
- Neither RUT nor Certificado de Existencia have email domains (skip validation gracefully)
- Email chain sender uses free email provider (existing validation handles this)
- Multiple sender domains in email chain (validate each against official domains)
- Official document has multiple email fields with different domains
- Email domains with subdomains (e.g., mail.azelis.com vs azelis.com)
- Case sensitivity in domain comparison (should be case-insensitive)

## Acceptance Criteria
1. When an email chain is validated, sender domains are compared against email domains from RUT and Certificado de Existencia documents
2. If sender domain differs from official document domain (even with TLD variation like .com vs .com.co), a CRITICAL discrepancy is created
3. The discrepancy clearly indicates the comparison is against "Dominio de Email (Documento Oficial)"
4. The discrepancy shows both the email chain domain and the official document domain
5. Typosquatting detection correctly identifies similar but different domains (e.g., acelis.com vs azelis.com)
6. The evaluation status reflects the need for manual verification when official document domain mismatches exist
7. The UI displays the new discrepancy type with appropriate CRITICAL styling (red background)
8. Existing email domain validation functionality continues to work unchanged
9. All unit tests pass
10. All linting checks pass with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_typosquatting_service.py -v` - Run typosquatting tests
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_email_domain_official_document_validation.md` to validate the E2E functionality

## Notes
- The Azelis fraud case is the reference example: fraudsters used @azelis.com.co to impersonate @azelis.com
- RUT and Certificado de Existencia are official government documents, making their email domains more trustworthy than email chain sender domains
- This feature enhances existing typosquatting detection by specifically comparing against official document sources
- The existing `_validate_sender_domain()` method handles general typosquatting detection; the new method focuses specifically on official document comparison
- No new npm packages or pip packages are required; existing TyposquattingService and NormalizationService provide all needed functionality

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (domain validation is universal)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
