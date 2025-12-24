# Feature: Email Chain/Thread Cross-Validation for Fraud Detection

## Feature Description
Allow users to upload email chain exports (.eml, .msg, or copy-paste text) as an additional data source for cross-validation against document-extracted information. The system will parse email headers and body content to extract sender domains, company names, NITs, representative names, and provider names mentioned in emails, then compare them against data extracted from uploaded documents (RUT, Certificado de Existencia, etc.) to detect fraud indicators like typosquatting or identity inconsistencies.

This feature extends the existing "Contacto Externo" tab in the Risk Evaluation Detail page to support bulk email chain validation, building upon the existing typosquatting detection and external contact validation patterns.

## User Story
As a **Risk Analyst or Admin**
I want to upload email chains/threads received during commercial communications
So that I can automatically cross-validate sender information against document-extracted data and detect potential fraud indicators like typosquatting, company name mismatches, or NIT discrepancies

## Problem Statement
Currently, the Finkargo risk evaluation system validates individual external contact emails against company information. However, fraud attempts often occur through email chains where fraudsters may:
- Use typosquatting domains that appear similar to legitimate companies (e.g., `acelis.com.co` vs `azelis.com`)
- Mention incorrect company names, NITs, or representative names in email body
- Impersonate representatives with slightly different names
- Use free email providers (gmail, hotmail) for business communications

The stakeholder (Andrés Ferrer) specifically noted: "El texto del correo... donde uno puede entrar y correlacionar información que hay, que se equivoquen en el nombre de la compañía, que se equivoquen en escriban mal el NIT, que el representante legal no coincida con lo que está diciendo el documento."

## Solution Statement
Extend the existing External Contact tab to:
1. **Support email chain upload** - Accept .eml, .msg files or copy-paste raw email text
2. **Parse email content** - Extract sender domain, body mentions of company name, NIT, representative names
3. **Cross-validate extracted data** - Compare against document-extracted data from the assessment
4. **Generate discrepancy alerts** - Flag mismatches with appropriate severity levels
5. **Integrate with risk scoring** - Impact the overall verification status when critical discrepancies are found

## Access Control
- Required Role(s): `risk_manager`, `admin`, `analyst`
- Backend Protection: Use existing RBAC dependencies from `backend/src/adapter/rest/rbac_dependencies.py` - `require_roles(['admin', 'risk_manager', 'analyst'])`
- Frontend Protection: Page already protected by `RoleProtectedRoute` in Risk module routing

## Relevant Files
Use these files to implement the feature:

**Backend - Core Services (Extend/Create):**
- `backend/src/core/servicios/risk/external_contact_service.py` - Extend to add email chain parsing and validation methods
- `backend/src/core/servicios/risk/typosquatting_service.py` - Reuse for domain validation (no changes needed)
- `backend/src/core/servicios/risk/normalization_service.py` - Reuse for name/NIT normalization (no changes needed)
- `backend/src/core/servicios/risk/cross_validation_service.py` - Reference for validation patterns

**Backend - DTOs (Extend):**
- `backend/src/interface/risk_dtos.py` - Add EmailChainRequest, EmailChainValidationResult, EmailMessage DTOs

**Backend - API Routes (Extend):**
- `backend/src/adapter/rest/risk_routes.py` - Add email chain upload and validation endpoints

**Backend - Repository (Extend):**
- `backend/src/repositorio/risk_repository.py` - Add email_chains table access if storing chain metadata

**Frontend - Components (Create/Extend):**
- `frontend/src/components/risk/FKExternalContactTab.tsx` - Extend with email chain upload section
- `frontend/src/components/risk/FKEmailValidationResult.tsx` - Reuse for displaying results

**Frontend - Types (Extend):**
- `frontend/src/types/risk.ts` - Add EmailChain, EmailMessage, EmailChainValidationResult types

**Frontend - Services (Extend):**
- `frontend/src/services/riskService.ts` - Add uploadEmailChain, validateEmailChain methods

**Frontend - Pages:**
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Already has the tab structure (Tab 3 = Contacto Externo)

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - E2E test format example

### New Files
- `backend/src/core/servicios/risk/email_chain_parser_service.py` - New service for parsing .eml/.msg files and extracting data
- `frontend/src/components/risk/FKEmailChainUploader.tsx` - New component for email chain upload and display
- `.claude/commands/e2e/test_email_chain_validation.md` - New E2E test file for this feature

## Pre-Implementation Verification

### Feature Category
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] CRUD Operations (basic data management) → Complete sections D, E

This feature primarily involves importing email data and validating it, with some CRUD operations for storing validation results.

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature does not involve document generation.

### B. Excel Column Mapping (Excel Processing only)
N/A - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)

| Format | Max Size | Required Headers/Structure | Validation Rules |
|--------|----------|---------------------------|------------------|
| .eml | 10MB | Standard RFC 5322 email format | Valid MIME structure, From header required |
| .msg | 10MB | Outlook MSG format | Valid MSG structure with sender info |
| Text (paste) | 500KB | Raw email text with headers | Contains From: header or email address pattern |

**Email Data Extraction Fields:**
| Field | Source | Validation |
|-------|--------|------------|
| sender_email | From header | Valid email format |
| sender_domain | From header | Domain extraction, typosquatting check |
| sender_name | From header | Normalize for comparison |
| company_mentions | Body text | Regex + NLP extraction |
| nit_mentions | Body text | NIT pattern matching (XXX.XXX.XXX-X) |
| rep_name_mentions | Body text | Name patterns near "representante", "gerente" |
| date | Date header | ISO date parsing |
| subject | Subject header | String extraction |

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| ExternalContactRepository.create() | dict | data['id'] | Dict access |
| ExternalContactRepository.get_by_assessment() | List[dict] | for contact in data: | List of dicts |
| RiskAssessmentRepository.get_detail() | dict | data['client_data_snapshot'] | Dict access |
| DocumentExtractionRepository.get_by_assessment() | List[dict] | extraction['extracted_data'] | Dict access |

**API Endpoint Contracts:**

| Endpoint | Method | Request Body | Response |
|----------|--------|--------------|----------|
| `/evaluations/{id}/email-chains` | POST | EmailChainUploadRequest (file or text) | EmailChainResponse |
| `/evaluations/{id}/email-chains/{chain_id}/validate` | POST | None | EmailChainValidationResultResponse |
| `/evaluations/{id}/email-chains` | GET | None | EmailChainListResponse |
| `/evaluations/{id}/email-chains/{chain_id}` | DELETE | None | 204 No Content |

### E. Database Dependencies Checklist (Document/CRUD only)
- [ ] Required enums exist in DTOs (or will be added) - Add EmailChainValidationStatus enum
- [ ] Template file exists in `backend/templates/` (if applicable) - N/A
- [ ] Database records exist (or migration created) - Create migration for email_chains table
- [ ] Country-specific data handled (CO vs MX) - N/A (email parsing is universal)

**New Database Table Required: `email_chains`**
```sql
CREATE TABLE email_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID NOT NULL REFERENCES risk_assessments(id),
    original_filename VARCHAR(255),
    raw_content TEXT,
    parsed_data JSONB,  -- Stores extracted messages array
    validation_status VARCHAR(50) DEFAULT 'pending',
    validation_result JSONB,
    validated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    is_active BOOLEAN DEFAULT TRUE
);
```

### F. External API Contract (Integration only)
N/A - No external API integration needed. Email parsing is done locally using Python libraries.

### G. Query Specification (Reporting only)
N/A - This is not a reporting feature.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| chain_id | id | string (UUID) | Primary key |
| assessment_id | assessment_id | string (UUID) | Foreign key |
| original_filename | original_filename | string | File name if uploaded |
| messages | parsed_data.messages | EmailMessage[] | Array of parsed messages |
| validation_status | validation_status | EmailChainValidationStatus | pending/validated/suspicious/critical |
| validation_result | validation_result | EmailChainValidationResult | Full validation details |
| validated_at | validated_at | string (ISO datetime) | When validation ran |
| created_at | created_at | string (ISO datetime) | Creation timestamp |

## Implementation Plan

### Phase 1: Foundation
1. **Database Migration** - Create `email_chains` table with proper RLS policies
2. **Backend DTOs** - Add Pydantic models for email chain requests/responses
3. **Repository Layer** - Add EmailChainRepository for CRUD operations
4. **Frontend Types** - Add TypeScript interfaces for email chain data

### Phase 2: Core Implementation
1. **Email Parser Service** - Create service to parse .eml/.msg files and extract:
   - Sender information (name, email, domain)
   - Body content analysis (company names, NITs, representative names)
   - Email thread structure
2. **Cross-Validation Extension** - Extend validation logic to compare email data against documents
3. **API Endpoints** - Add REST endpoints for upload, validate, list, delete
4. **Frontend Component** - Create FKEmailChainUploader component

### Phase 3: Integration
1. **Tab Integration** - Add email chain uploader to FKExternalContactTab
2. **Results Display** - Show validation results with severity indicators
3. **Risk Score Integration** - Include email chain discrepancies in verification status
4. **E2E Testing** - Create and run E2E test for the complete workflow

## Step by Step Tasks

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_email_chain_validation.md` with test steps for:
  1. Navigate to Risk Dashboard
  2. Open an evaluation detail page
  3. Go to "Contacto Externo" tab
  4. Upload an email chain file or paste email text
  5. Click validate button
  6. Verify validation results appear
  7. Check for discrepancy indicators

### Step 2: Create Database Migration
- Create `backend/database/migration_add_email_chains_table.sql`
- Include `email_chains` table with proper structure
- Add RLS policies for authenticated users
- Add indexes on `assessment_id` for query performance

### Step 3: Add Backend DTOs
- Edit `backend/src/interface/risk_dtos.py`
- Add `EmailChainValidationStatus` enum
- Add `EmailMessage` model (sender_email, sender_name, date, subject, body_excerpt)
- Add `EmailChainUploadRequest` model (file or text content)
- Add `EmailChainResponse` model
- Add `EmailChainValidationResult` model (discrepancies found, severity counts)
- Add `EmailChainListResponse` model

### Step 4: Create Email Parser Service
- Create `backend/src/core/servicios/risk/email_chain_parser_service.py`
- Implement methods:
  - `parse_eml_file(file_content: bytes) -> List[EmailMessage]`
  - `parse_msg_file(file_content: bytes) -> List[EmailMessage]`
  - `parse_raw_text(text: str) -> List[EmailMessage]`
  - `extract_company_mentions(body: str) -> List[str]`
  - `extract_nit_mentions(body: str) -> List[str]`
  - `extract_rep_name_mentions(body: str) -> List[str]`
- Use `email` standard library for .eml parsing
- Add `extract-msg` library to requirements.txt for .msg parsing

### Step 5: Add Email Chain Repository
- Edit `backend/src/repositorio/risk_repository.py`
- Add `EmailChainRepository` class with methods:
  - `create(data: dict) -> dict`
  - `get_by_assessment(assessment_id: str) -> List[dict]`
  - `get_by_id(chain_id: str) -> Optional[dict]`
  - `update(chain_id: str, updates: dict) -> Optional[dict]`
  - `delete(chain_id: str) -> bool`

### Step 6: Extend External Contact Service
- Edit `backend/src/core/servicios/risk/external_contact_service.py`
- Add methods:
  - `upload_email_chain(assessment_id: str, file_or_text: Union[bytes, str], filename: Optional[str]) -> dict`
  - `validate_email_chain(chain_id: str) -> dict`
  - `get_email_chains(assessment_id: str) -> List[dict]`
  - `delete_email_chain(chain_id: str) -> bool`
- Implement cross-validation logic:
  - Compare sender domains against document-extracted company domains
  - Compare mentioned company names against document company names
  - Compare mentioned NITs against document NITs
  - Compare mentioned representative names against document representatives
  - Use existing TyposquattingService for domain comparison
  - Use existing NormalizationService for name/NIT normalization

### Step 7: Add API Endpoints
- Edit `backend/src/adapter/rest/risk_routes.py`
- Add endpoints:
  - `POST /api/risk/evaluations/{id}/email-chains` - Upload email chain
  - `POST /api/risk/evaluations/{id}/email-chains/{chain_id}/validate` - Validate chain
  - `GET /api/risk/evaluations/{id}/email-chains` - List chains
  - `DELETE /api/risk/evaluations/{id}/email-chains/{chain_id}` - Delete chain
- Use existing RBAC protection

### Step 8: Add Frontend Types
- Edit `frontend/src/types/risk.ts`
- Add types:
  - `EmailChainValidationStatus` type
  - `EmailMessage` interface
  - `EmailChain` interface
  - `EmailChainValidationResult` interface
  - `EmailChainListResponse` interface
  - `EMAIL_CHAIN_VALIDATION_STATUS_CONFIG` constant for UI styling

### Step 9: Add Frontend Service Methods
- Edit `frontend/src/services/riskService.ts`
- Add methods:
  - `uploadEmailChain(evaluationId: string, file: File | null, text: string | null): Promise<EmailChain>`
  - `validateEmailChain(evaluationId: string, chainId: string): Promise<EmailChain>`
  - `getEmailChains(evaluationId: string): Promise<EmailChainListResponse>`
  - `deleteEmailChain(evaluationId: string, chainId: string): Promise<void>`

### Step 10: Create Email Chain Uploader Component
- Create `frontend/src/components/risk/FKEmailChainUploader.tsx`
- Include:
  - File drop zone for .eml/.msg files
  - Textarea for pasting raw email text
  - "Subir" button to upload
  - List of uploaded chains with validation status
  - "Validar" button for each chain
  - Delete button for each chain
  - Display validation results using existing FKEmailValidationResult pattern
- Follow FK prefix naming convention
- Use react-hook-form for form handling
- Use Material-UI components with Finkargo theme

### Step 11: Integrate into External Contact Tab
- Edit `frontend/src/components/risk/FKExternalContactTab.tsx`
- Add new section at top: "Cadenas de Email"
- Include the FKEmailChainUploader component
- Add divider between email chains and individual contacts sections

### Step 12: Update Requirements.txt
- Edit `backend/requirements.txt`
- Add `extract-msg>=0.45.0` for Outlook .msg file parsing

### Step 13: Run Validation Commands
- Execute all validation commands to verify implementation
- Fix any linting errors or type issues
- Ensure backend tests pass
- Ensure frontend builds successfully

### Step 14: Execute E2E Test
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_email_chain_validation.md`
- Capture screenshots as specified
- Verify all success criteria pass

## Testing Strategy

### Unit Tests
- `backend/tests/test_email_chain_parser.py`:
  - Test .eml file parsing with valid email
  - Test .msg file parsing (mock if library not available)
  - Test raw text parsing with various formats
  - Test company name extraction from body
  - Test NIT extraction with various formats (XXX.XXX.XXX-X, XXXXXXXXX-X)
  - Test representative name extraction

- `backend/tests/test_email_chain_validation.py`:
  - Test domain comparison against document domains
  - Test company name comparison with normalization
  - Test NIT comparison with formatting differences
  - Test severity determination (critical for typosquatting, high for NIT mismatch, etc.)

### Edge Cases
1. **Email format variations**: RFC 5322 compliant emails, forwarded emails, reply chains
2. **Empty or minimal content**: Emails with only headers, no body content
3. **Multiple NITs in body**: Distinguish client NIT from supplier NITs
4. **Spanish/Colombian text**: Properly extract "representante legal", "gerente", etc.
5. **Encoding issues**: UTF-8, ISO-8859-1, quoted-printable encoding
6. **Large email chains**: Handle 10+ emails in a chain efficiently
7. **Malformed files**: Handle corrupt .eml/.msg files gracefully

## Acceptance Criteria
1. Users can upload .eml or .msg files up to 10MB
2. Users can paste raw email text up to 500KB
3. System correctly parses email headers (From, Date, Subject)
4. System extracts company names mentioned in email body
5. System extracts NITs mentioned in email body (XXX.XXX.XXX-X format)
6. System extracts representative names mentioned near keywords
7. Sender domain is validated against document-extracted company domains
8. Company name mentions are compared against document company names
9. NIT mentions are compared against document NITs
10. Representative name mentions are compared against document representatives
11. Discrepancies are flagged with appropriate severity (critical/high/medium/low)
12. Validation results are displayed in the UI with clear severity indicators
13. Users can delete uploaded email chains
14. All operations are protected by RBAC
15. E2E test passes with all success criteria met

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend validation
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

**E2E Test Execution:**
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_email_chain_validation.md` to validate this functionality works

## Notes

### New Dependencies
- **Backend**: `extract-msg>=0.45.0` - For parsing Outlook .msg files

### Cross-Validation Rules Summary

| Email Field | Compare Against | Flag If | Severity |
|-------------|-----------------|---------|----------|
| Sender domain | Document company domain | Different or typosquatting detected | CRITICAL |
| Sender domain | Known legitimate domains | Typosquatting similarity 70-95% | CRITICAL |
| Company name in body | Company name in documents | Different after normalization | HIGH |
| NIT in body | NIT in documents | Different base digits | CRITICAL |
| NIT in body | NIT in documents | Different check digit only | HIGH |
| Rep name in body | Rep name in documents | Different after fuzzy matching | HIGH |
| Sender domain | Free email providers | Gmail/Hotmail for business | MEDIUM |

### Integration with Existing Systems
- Reuses `TyposquattingService` for domain validation
- Reuses `NormalizationService` for name/NIT normalization
- Follows same patterns as `FKExternalContactTab` for UI
- Follows same API patterns as existing external contact endpoints
- Uses same severity color coding as cross-validation results

### Future Considerations
- Consider adding email chain visualization (thread view)
- Consider extracting attachment information
- Consider supporting additional email formats (.mbox, Gmail export)
- Consider AI-based entity extraction for more accurate company/name detection

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) if applicable - N/A

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
