# Feature: Email/Contact Information Correlation Tab

## Feature Description
Add a new "Contacto Externo" (External Contact) tab in the risk evaluation detail page where users can input the sender's email address received from commercial channels. The system will cross-validate the email domain against company documents to detect potential typosquatting fraud attempts.

This feature directly addresses the Azelis fraud case where documents showed company "AZELIS COLOMBIA S.A.S." but emails were received from `azelis.com.co` instead of the legitimate `azelis.com` domain. The system will flag such domain mismatches for manual verification.

## User Story
As a Mesa de Control user (risk_analyst role)
I want to input the sender's email address received via commercial channels and validate it against document data
So that I can detect potential typosquatting fraud attempts before approving a risk evaluation

## Problem Statement
Currently, the risk evaluation system performs cross-validation on uploaded documents but does not have a mechanism to correlate the email/contact information received through commercial channels with the company information extracted from documents. This gap was exploited in the Azelis fraud case where fraudsters used a typosquatted domain (`azelis.com.co`) that looked legitimate but was not the company's actual domain (`azelis.com`).

## Solution Statement
Implement a new "Contacto Externo" tab in the risk evaluation detail page that:
1. Allows users to input one or more sender email addresses
2. Stores external contact information in the database associated with the evaluation
3. Uses the existing TyposquattingService to validate email domains against:
   - Company name extracted from documents (deriving expected domain)
   - Known legitimate domains in the system
4. Displays validation results with similarity scores and typosquatting alerts
5. Integrates validation results into the overall cross-validation workflow

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`, `mesa_control`
- Backend Protection: Use `require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control'])` RBAC dependency
- Frontend Protection: Tab will be visible within the existing RoleProtectedRoute for risk evaluation pages

## Relevant Files
Use these files to implement the feature:

**Backend - API Routes:**
- `backend/src/adapter/rest/risk_routes.py` - Add endpoints for external contact CRUD and email validation
- `backend/src/adapter/rest/dependencies.py` - Existing dependency injection patterns

**Backend - Services:**
- `backend/src/core/servicios/risk/typosquatting_service.py` - Existing service for domain similarity detection (will be reused)
- `backend/src/core/servicios/risk/cross_validation_service.py` - May integrate external contact validation into cross-validation
- `backend/src/core/servicios/risk/normalization_service.py` - Domain extraction utilities

**Backend - DTOs:**
- `backend/src/interface/risk_dtos.py` - Add DTOs for external contact and email validation

**Backend - Repository:**
- `backend/src/repositorio/risk_repository.py` - Add ExternalContactRepository for CRUD operations

**Backend - Database:**
- `backend/database/` - Add migration for risk_external_contacts table

**Frontend - Pages:**
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Add new "Contacto Externo" tab (Tab index 3)

**Frontend - Components:**
- `frontend/src/components/risk/FKExternalContactTab.tsx` - New component for the tab content
- `frontend/src/components/risk/FKEmailValidationResult.tsx` - Component to display validation results

**Frontend - Services:**
- `frontend/src/services/riskService.ts` - Add API methods for external contacts

**Frontend - Types:**
- `frontend/src/types/risk.ts` - Add TypeScript types for external contacts

**E2E Test References:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `backend/database/migration_add_risk_external_contacts.sql` - Database migration for external contacts table
- `frontend/src/components/risk/FKExternalContactTab.tsx` - New tab component
- `frontend/src/components/risk/FKEmailValidationResult.tsx` - Email validation result display component
- `.claude/commands/e2e/test_email_contact_correlation.md` - E2E test for this feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [x] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature does not involve document generation.

### B. Excel Column Mapping (Excel Processing only)
N/A - This feature does not involve Excel processing.

### C. File Format Specification (Import/Export only)
N/A - This feature does not involve file import/export.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| external_contact_repo.create() | dict | data['id'] | Not data.id |
| external_contact_repo.get_by_assessment() | List[dict] | contact['email'] | Not contact.email |
| external_contact_repo.update() | dict | data['validated_at'] | Not data.validated_at |
| external_contact_repo.delete() | None | N/A | Soft delete |
| typosquatting_service.check_domain_typosquatting() | TyposquattingResult | result.is_suspicious | Object access |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs (or will be added) - Add `ExternalContactValidationStatus`
- [ ] Template file exists in `backend/templates/` (if applicable) - N/A
- [x] Database records exist (or migration created) - Migration will create `risk_external_contacts` table
- [ ] Country-specific data handled (CO vs MX) - N/A

### F. External API Contract (Integration only)
N/A - This feature does not integrate with external APIs.

### G. Query Specification (Reporting only)
N/A - This feature does not involve reporting queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| id | id | string (UUID) | Primary key |
| assessment_id | assessment_id | string | Foreign key to risk_assessments |
| email | email | string | Email address provided by user |
| sender_name | sender_name | string | Optional sender name |
| source | source | string | Where email was received (e.g., 'comercial_team') |
| validation_status | validation_status | string | 'pending', 'validated', 'suspicious', 'critical' |
| validation_result | validation_result | object | TyposquattingResult data |
| validated_at | validated_at | string (ISO date) | When validation was performed |
| created_at | created_at | string (ISO date) | Record creation timestamp |
| created_by | created_by | string | User ID who created the record |
| notes | notes | string | Optional user notes |

## Implementation Plan

### Phase 1: Foundation
1. Create database migration for `risk_external_contacts` table with:
   - id (UUID, PK)
   - assessment_id (UUID, FK to risk_assessments)
   - email (VARCHAR)
   - sender_name (VARCHAR, nullable)
   - source (VARCHAR)
   - validation_status (VARCHAR)
   - validation_result (JSONB)
   - validated_at (TIMESTAMP)
   - created_at (TIMESTAMP)
   - created_by (UUID)
   - notes (TEXT, nullable)
   - is_active (BOOLEAN)
2. Add DTOs for ExternalContactRequest, ExternalContactResponse, EmailValidationRequest, EmailValidationResponse
3. Create ExternalContactRepository with CRUD operations

### Phase 2: Core Implementation
1. Create ExternalContactService with:
   - create_contact() - Add new external contact
   - get_contacts() - Get contacts for an assessment
   - validate_email() - Validate email domain using TyposquattingService
   - delete_contact() - Soft delete contact
2. Add API endpoints:
   - POST /risk/evaluations/{id}/external-contacts - Create contact
   - GET /risk/evaluations/{id}/external-contacts - List contacts
   - POST /risk/evaluations/{id}/external-contacts/{contact_id}/validate - Validate email
   - DELETE /risk/evaluations/{id}/external-contacts/{contact_id} - Delete contact
3. Create frontend components:
   - FKExternalContactTab - Main tab component with form and list
   - FKEmailValidationResult - Display validation results with similarity scores

### Phase 3: Integration
1. Add "Contacto Externo" tab to RiskEvaluationDetail.tsx (Tab index 3)
2. Add email icon and tab label
3. Integrate with cross-validation flow:
   - Option to include external contact validation in overall cross-validation
   - Update verification_status if suspicious domains are detected
4. Add validation results to PDF export if discrepancies found

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` for E2E test patterns
- Create `.claude/commands/e2e/test_email_contact_correlation.md` with test steps:
  1. Navigate to risk evaluation detail page
  2. Click on "Contacto Externo" tab
  3. Verify the tab content is visible
  4. Add a new external contact with email
  5. Click "Validar Dominio" button
  6. Verify validation result is displayed
  7. For typosquatting case, verify warning alert is shown
  8. Capture screenshots at each step

### Task 2: Create Database Migration
- Create `backend/database/migration_add_risk_external_contacts.sql`
- Define table structure with all required fields
- Add RLS policies for authenticated users
- Add foreign key constraint to risk_assessments

### Task 3: Add Backend DTOs
- Edit `backend/src/interface/risk_dtos.py`
- Add `ExternalContactValidationStatus` enum
- Add `ExternalContactRequest` model
- Add `ExternalContactResponse` model
- Add `EmailValidationRequest` model (optional, for batch validation)
- Add `EmailValidationResponse` model with TyposquattingResult fields

### Task 4: Create External Contact Repository
- Edit `backend/src/repositorio/risk_repository.py`
- Add `ExternalContactRepository` class with methods:
  - `create(data: dict) -> dict`
  - `get_by_assessment(assessment_id: str) -> List[dict]`
  - `get_by_id(id: str) -> Optional[dict]`
  - `update(id: str, data: dict) -> dict`
  - `delete(id: str) -> None` (soft delete)

### Task 5: Create External Contact Service
- Create `backend/src/core/servicios/risk/external_contact_service.py`
- Implement `ExternalContactService` class with methods:
  - `create_contact(assessment_id, email, sender_name, source, user_id, notes) -> dict`
  - `get_contacts(assessment_id) -> List[dict]`
  - `validate_email(contact_id, company_name) -> EmailValidationResponse`
  - `delete_contact(contact_id) -> None`
- Use existing `TyposquattingService` for email validation
- Extract domain from email using `NormalizationService.extract_email_domain()`

### Task 6: Add API Endpoints
- Edit `backend/src/adapter/rest/risk_routes.py`
- Add dependency injection for `ExternalContactService`
- Add endpoints:
  - `POST /risk/evaluations/{id}/external-contacts`
  - `GET /risk/evaluations/{id}/external-contacts`
  - `POST /risk/evaluations/{id}/external-contacts/{contact_id}/validate`
  - `DELETE /risk/evaluations/{id}/external-contacts/{contact_id}`
- Apply RBAC with `require_roles(['risk_analyst', 'risk_manager', 'admin', 'mesa_control'])`

### Task 7: Add Frontend Types
- Edit `frontend/src/types/risk.ts`
- Add `ExternalContactValidationStatus` type
- Add `ExternalContact` interface
- Add `EmailValidationResult` interface (matching TyposquattingResult)
- Add `ExternalContactRequest` interface

### Task 8: Add Frontend Service Methods
- Edit `frontend/src/services/riskService.ts`
- Add methods:
  - `getExternalContacts(evaluationId: string): Promise<ExternalContact[]>`
  - `createExternalContact(evaluationId: string, request: ExternalContactRequest): Promise<ExternalContact>`
  - `validateExternalContact(evaluationId: string, contactId: string): Promise<ExternalContact>`
  - `deleteExternalContact(evaluationId: string, contactId: string): Promise<void>`

### Task 9: Create FKEmailValidationResult Component
- Create `frontend/src/components/risk/FKEmailValidationResult.tsx`
- Display validation status with appropriate colors and icons
- Show similarity score for typosquatting detection
- Display "similar_to" domain for comparison
- Use Material-UI Alert component for warnings
- Follow existing component patterns (FKVerificationStatusCard)

### Task 10: Create FKExternalContactTab Component
- Create `frontend/src/components/risk/FKExternalContactTab.tsx`
- Include:
  - Form to add new contact (email, sender name, source, notes)
  - Use react-hook-form with MUI TextField
  - List of existing contacts with validation status
  - "Validar Dominio" button for each contact
  - Delete button for each contact
  - Integration with FKEmailValidationResult for displaying results
- Props: `evaluationId`, `assessmentId`, `clientInfo` (for company name)

### Task 11: Integrate Tab into RiskEvaluationDetail
- Edit `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Import Email icon from @mui/icons-material
- Add new Tab component at index 3:
  ```tsx
  <Tab
    icon={<Email />}
    iconPosition="start"
    label="Contacto Externo"
  />
  ```
- Add conditional rendering for activeTab === 3:
  ```tsx
  {activeTab === 3 && id && (
    <FKExternalContactTab
      evaluationId={id}
      assessmentId={assessment?.assessment_id}
      clientInfo={assessment?.client_info}
    />
  )}
  ```

### Task 12: Add Backend Unit Tests
- Create tests in `backend/tests/test_external_contact_service.py`
- Test cases:
  - Create external contact successfully
  - Validate email with clean domain (no typosquatting)
  - Validate email with typosquatted domain (detect suspicious)
  - Validate email with TLD variation (detect medium severity)
  - Get contacts by assessment
  - Delete contact (soft delete)

### Task 13: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Run E2E test to validate feature works as expected

## Testing Strategy

### Unit Tests
- `test_external_contact_service.py`:
  - Test email domain extraction
  - Test typosquatting detection with known cases (azelis.com vs acelis.com.co)
  - Test TLD variation detection
  - Test CRUD operations for external contacts

### Edge Cases
1. Empty email address - Should show validation error
2. Invalid email format - Should show format error
3. Free email provider (gmail.com) - Should flag as medium severity
4. Exact domain match - Should show pass status
5. Very similar domain (1-2 character difference) - Should flag as critical
6. TLD variation only (.com vs .com.co) - Should flag as medium
7. Completely different domain - Should not flag as typosquatting
8. Multiple contacts per assessment - Should handle list correctly
9. Concurrent validation requests - Should handle gracefully
10. Assessment without extracted company name - Should still validate against known domains

## Acceptance Criteria
1. New "Contacto Externo" tab appears in risk evaluation detail page (Tab index 3)
2. Users can add external contact with email address
3. "Validar Dominio" button triggers email domain validation
4. Typosquatting detection shows similarity percentage and alert for suspicious domains
5. TLD variations (e.g., .com vs .com.co) are flagged appropriately
6. Free email providers are flagged when used for business contacts
7. Validation results persist in database for audit trail
8. Users can delete contacts they no longer need
9. Tab shows count of suspicious contacts (if any) in tab label
10. All API endpoints are protected with appropriate RBAC
11. E2E test passes successfully

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_external_contact_service.py -v` - Run unit tests for external contact service
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_email_contact_correlation.md` E2E test file to validate this functionality works

## Notes

**Dependencies:**
- No new npm packages required (uses existing MUI components)
- No new pip packages required (uses existing services)

**Future Considerations:**
1. Could integrate external contact validation results into the overall risk score calculation
2. Could add batch validation for multiple emails at once
3. Could add email address history tracking (same email used across multiple evaluations)
4. Could integrate with external email verification services for deliverability checking
5. Could add phone number validation in addition to email

**UI Design Notes:**
- Follow existing tab patterns from RiskEvaluationDetail
- Use Finkargo brand colors for validation status (success green, error red, warning orange)
- Similarity percentage should be clearly visible in the alert
- Include example from Azelis case in UI help text

**Security Considerations:**
- Email addresses are PII and should be handled according to data protection policies
- Soft delete ensures audit trail is maintained
- RLS policies ensure users can only access data they're authorized for

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**CRUD Operations:**
- [x] Repository patterns defined
- [x] Validation rules specified
- [x] Soft delete behavior documented

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [ ] Country-specific variations handled (CO vs MX) if applicable - N/A

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
