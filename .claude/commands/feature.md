# Feature Planning

Create a new plan to implement the `Feature` using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan use the `Relevant Files` to focus on the right files.

## Variables
issue_number: $1
adw_id: $2
issue_json: $3

## Instructions

- IMPORTANT: You're writing a plan to implement a net new feature based on the `Feature` that will add value to the application.
- IMPORTANT: The `Feature` describes the feature that will be implemented but remember we're not implementing a new feature, we're creating the plan that will be used to implement the feature based on the `Plan Format` below.
- Create the plan in the `specs/` directory with filename: `issue-{issue_number}-adw-{adw_id}-sdlc_planner-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short, descriptive name based on the feature (e.g., "add-contract-type", "implement-approval-workflow", "create-finance-report")
- Use the `Plan Format` below to create the plan. 
- Research the codebase to understand existing patterns, architecture, and conventions before planning the feature.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to implement the feature successfully.
- Use your reasoning model: THINK HARD about the feature requirements, design, and implementation approach.
- Follow existing patterns and conventions in the codebase. Don't reinvent the wheel.
- Design for extensibility and maintainability.
- If you need a new library:
  - Backend: add to `backend/requirements.txt`
  - Frontend: use `npm install <package>`
  - Report it in the `Notes` section of the `Plan Format`.

## Architecture Rules

- **Backend follows Clean Architecture**: adapter/rest → core/servicios → repositorio
- **Frontend follows**: pages → components → services → api
- **Components use FK prefix** (e.g., `FKContractRequest.tsx`, `FKExcelUploader.tsx`)
- **Forms use react-hook-form with MUI**
- **State management**: Context API for global, useState for local
- **100% TypeScript** on frontend, no `any` types
- **No decorators** in backend. Keep it simple.

## Role-Based Access

Consider which roles should access the feature:
- `admin` - Full system access
- `legal` - Contract review/approval
- `operations` - Contract requests, downloads
- `commercial` - Sales operations
- `analyst` - Read-only access
- `mesa_control` - Control desk workflows
- `manager` - Department supervision
- `user` - Basic authenticated
- `cliente` - External client dashboard

If the feature requires role protection:
- Backend: Use RBAC dependencies from `backend/src/adapter/rest/rbac_dependencies.py`
- Frontend: Use `RoleProtectedRoute` component

## E2E Test Requirements

- IMPORTANT: If the feature includes UI components or user interactions:
  - Add a task in the `Step by Step Tasks` section to create a separate E2E test file in `.claude/commands/e2e/test_<descriptive_name>.md` based on examples in that directory
  - Add E2E test validation to your Validation Commands section
  - IMPORTANT: When you fill out the `Plan Format: Relevant Files` section, add an instruction to read `.claude/commands/test_e2e.md`, and `.claude/commands/e2e/test_login.md` to understand how to create an E2E test file. List your new E2E test file to the `Plan Format: New Files` section.
  - To be clear, we're not creating a new E2E test file, we're creating a task to create a new E2E test file in the `Plan Format` below
- Respect requested files in the `Relevant Files` section.
- Start your research by reading the `README.md` file.

## Feature Category Classification

First, identify which category this feature belongs to and apply the relevant verification requirements:

| Category | Examples | Key Verification |
|----------|----------|------------------|
| **Document Generation** | Contracts, Solicitud de Desembolso | Template placeholders, database records |
| **Excel Processing** | Invoice upload, Payment conversion | Column mapping, data transformation |
| **Data Import/Export** | CSV import, ZIP download | File format validation, field mapping |
| **API Integration** | Google Drive sync, external services | Auth, endpoint contracts, error handling |
| **Reporting** | Finance reports, audit history | Query structure, pagination, filtering |
| **CRUD Operations** | Client management, template CRUD | Repository patterns, validation rules |

## Verification Requirements by Feature Category

### A. Document Generation Features (Contracts, PDFs)
- CRITICAL: If the feature involves Word document generation or modification:
  1. **Extract ALL placeholders programmatically** by running:
     ```python
     cd backend && python -c "
     from docx import Document
     import re
     doc = Document('templates/YOUR_TEMPLATE.docx')
     placeholders = set()
     for para in doc.paragraphs:
         found = re.findall(r'\[[^\]]+\]', para.text)
         placeholders.update(found)
     for table in doc.tables:
         for row in table.rows:
             for cell in row.cells:
                 found = re.findall(r'\[[^\]]+\]', cell.text)
                 placeholders.update(found)
     for p in sorted(placeholders):
         print(p)
     "
     ```
  2. **Document the EXACT placeholder strings** in the plan (case-sensitive, may contain spaces)
  3. **Create a placeholder mapping table**: Placeholder -> Data Source -> Format
  4. **Verify database records**: template record in `contract_templates`, enum in DTOs

### B. Excel Processing Features (Treasury, Finance, Operations)
- CRITICAL: If the feature involves Excel file processing or conversion:
  1. **Document source Excel structure**:
     - List ALL expected columns with exact names (case-sensitive)
     - Note required vs optional columns
     - Document data types and formats (dates, numbers, text)
  2. **Document output Excel structure** (if generating output):
     - Target column names and order
     - Data transformation rules (1:1 or 1:N row expansion)
     - Formulas or calculations applied
  3. **Identify existing similar services** to follow patterns:
     - `PaymentTemplateService` for payment conversions
     - `ExcelValidationService` for upload validation
     - `ExcelMergeService` for data consolidation
  4. **Document catalog/lookup dependencies**:
     - AR account mappings
     - Product classifications
     - Country-specific variations (CO vs MX)

### C. Data Import/Export Features
- CRITICAL: If the feature involves file import or export:
  1. **Document file format specifications**:
     - Supported formats (CSV, XLSX, ZIP)
     - Size limits and validation rules
     - Required headers or structure
  2. **Map input fields to internal data model**:
     - Field name mapping (source -> internal)
     - Data type conversions
     - Validation rules per field
  3. **Document error handling**:
     - What happens on invalid rows?
     - Partial success handling
     - Error message format

### D. API/Integration Features
- CRITICAL: If the feature involves external service integration:
  1. **Document external API contract**:
     - Endpoint URLs and methods
     - Authentication method
     - Request/response formats
  2. **Error handling strategy**:
     - Retry logic
     - Timeout handling
     - Fallback behavior
  3. **Data synchronization**:
     - Conflict resolution
     - Idempotency requirements

### E. Reporting Features
- CRITICAL: If the feature involves reports or data queries:
  1. **Document query requirements**:
     - Filter parameters
     - Pagination needs
     - Sort options
  2. **Performance considerations**:
     - Expected data volume
     - Indexing needs
     - Caching strategy

## Data Contract Verification Requirements (ALL Features)

- CRITICAL: Before implementing API endpoints:
  1. **Verify return types** of all repository methods (check if they return `dict` or model objects)
  2. **Document access patterns** - use `['key']` for dicts, `.attribute` for objects
  3. **Match frontend/backend field naming**:
     - This project's backend Pydantic models use **snake_case** (Python convention)
     - Frontend TypeScript should use **snake_case** to match API responses (NOT camelCase)
     - If different naming is required, explicitly document the transformation layer
  4. **Create an Interface Mapping Table** showing Frontend Field -> Backend Field -> Type

## Database Dependencies Requirements

- CRITICAL: For features involving new database entities:
  1. **Check if required records exist** in relevant tables
  2. **Create migration file** if new database records are needed
  3. **For contract features**, verify:
     - Contract type enum in `legal_dtos.py`
     - Contract ID prefix in database function
     - Template file in `backend/templates/`
     - Template record in `contract_templates` table
  4. **For catalog/lookup features**, verify:
     - Catalog data exists or migration creates it
     - Country-specific variations handled (CO vs MX)

## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and instructions.
- `backend/src/adapter/rest/` - API routes (controllers)
- `backend/src/core/servicios/` - Business logic services
- `backend/src/repositorio/` - Data access layer
- `backend/src/interface/` - DTOs and request/response models
- `backend/src/models/` - SQLAlchemy database models
- `frontend/src/pages/` - Route pages by module (legal/, operations/, finance/)
- `frontend/src/components/` - UI components (FK-prefixed)
- `frontend/src/services/` - API service layer
- `frontend/src/types/` - TypeScript types
- `frontend/src/contexts/` - React Context providers
- `scripts/` - Contains the scripts to start and stop the server + client.
- `adws/` - Contains the AI Developer Workflow (ADW) scripts.

- Read `.claude/commands/conditional_docs.md` to check if your task requires additional documentation
- If your task matches any of the conditions listed, include those documentation files in the `Plan Format: Relevant Files` section of your plan

Ignore all other files in the codebase.

## Plan Format

```md
# Feature: <feature name>

## Feature Description
<describe the feature in detail, including its purpose and value to users>

## User Story
As a <type of user - specify role: legal/operations/admin/etc>
I want to <action/goal>
So that <benefit/value>

## Problem Statement
<clearly define the specific problem or opportunity this feature addresses>

## Solution Statement
<describe the proposed solution approach and how it solves the problem>

## Access Control
- Required Role(s): <list roles that can access this feature>
- Backend Protection: <describe RBAC dependency to use>
- Frontend Protection: <describe RoleProtectedRoute configuration>

## Relevant Files
Use these files to implement the feature:

<find and list the files that are relevant to the feature describe why they are relevant in bullet points. If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.>

### New Files
<list new files to be created with their purpose>

## Pre-Implementation Verification

### Feature Category
<Mark which category applies - this determines which verification sections are required:>
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Template Placeholder Inventory (Document Generation only)
<If this feature involves Word document generation, run the placeholder extraction script and list ALL placeholders:>

| Placeholder | Data Source | Format | Notes |
|-------------|-------------|--------|-------|
| [Example Placeholder] | data.field_name | String | Exact case matters |

### B. Excel Column Mapping (Excel Processing only)
<If this feature involves Excel processing, document the column structure:>

**Source Excel Structure:**
| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| Número de Operación | Yes | String | Not empty |

**Output Excel Structure (if applicable):**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| Operation ID | Número de Operación | Direct copy |

**Catalog Dependencies:**
- [ ] AR account mappings documented
- [ ] Country-specific variations identified (CO vs MX)

### C. File Format Specification (Import/Export only)
<If this feature involves file import/export:>

| Format | Max Size | Required Headers | Validation Rules |
|--------|----------|------------------|------------------|
| XLSX | 10MB | Column A, B, C | Non-empty rows |

### D. Data Contract Verification (ALL features)
<Document return types and access patterns for repository methods used:>

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| client_repo.get_by_nit() | dict | data['nit'] | Not data.nit |

### E. Database Dependencies Checklist (Document/CRUD only)
- [ ] Required enums exist in DTOs (or will be added)
- [ ] Template file exists in `backend/templates/` (if applicable)
- [ ] Database records exist (or migration created)
- [ ] Country-specific data handled (CO vs MX)

### F. External API Contract (Integration only)
<If this feature involves external APIs:>

| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| /api/v1/data | POST | Bearer Token | JSON | JSON |

### G. Query Specification (Reporting only)
<If this feature involves data queries:>

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| date_from | date | No | 30 days ago |

### Interface Mapping (Frontend ↔ Backend)
<Map frontend TypeScript fields to backend Pydantic fields:>

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| numero_cotizacion | numero_cotizacion | string | Use snake_case in both |

## Implementation Plan
### Phase 1: Foundation
<describe the foundational work needed before implementing the main feature>
- Database models/migrations if needed
- DTOs and interfaces
- Repository layer changes

### Phase 2: Core Implementation
<describe the main implementation work for the feature>
- Service layer business logic
- API endpoints
- Frontend components and pages

### Phase 3: Integration
<describe how the feature will integrate with existing functionality>
- Connect to existing workflows
- Update navigation/routing
- Add role protection

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. use as many h3 headers as needed to implement the feature. Order matters, start with the foundational shared changes required then move on to the specific implementation. Include creating tests throughout the implementation process.>

<If the feature affects UI, include a task to create a E2E test file (like `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md`) as one of your early tasks. That e2e test should validate the feature works as expected, be specific with the steps to demonstrate the new functionality. We want the minimal set of steps to validate the feature works as expected and screen shots to prove it if possible.>

<Your last step should be running the `Validation Commands` to validate the feature works correctly with zero regressions.>

## Testing Strategy
### Unit Tests
<describe unit tests needed for the feature - pytest for backend>

### Edge Cases
<list edge cases that need to be tested>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the feature to be considered complete>

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

<list commands you'll use to validate with 100% confidence the feature is implemented correctly with zero regressions. every command must execute without errors so be specific about what you want to run to validate the feature works as expected. Include commands to test the feature end-to-end.>

<If you created an E2E test, include the following validation step: `Read .claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_<descriptive_name>.md` test file to validate this functionality works.>

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
<optionally list any additional notes, future considerations, or context that are relevant to the feature that will be helpful to the developer>

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [ ] Feature category identified in Pre-Implementation Verification
- [ ] All new files listed in "New Files" section
- [ ] All database migrations identified and tasks created
- [ ] E2E test file task included (if UI feature)
- [ ] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**Document Generation:**
- [ ] ALL template placeholders extracted and documented
- [ ] Placeholder mapping table complete with data sources
- [ ] Database records verified (template, enum, prefix)

**Excel Processing:**
- [ ] Source Excel columns documented with exact names
- [ ] Output Excel structure documented (if applicable)
- [ ] Data transformation rules specified (1:1 or 1:N)
- [ ] Catalog/lookup dependencies identified

**Data Import/Export:**
- [ ] File format specifications documented
- [ ] Field mapping table complete
- [ ] Error handling strategy defined

**API Integration:**
- [ ] External API contract documented
- [ ] Auth method specified
- [ ] Error/retry strategy defined

**Reporting:**
- [ ] Query filters and parameters documented
- [ ] Pagination/sorting requirements specified

### Consistency (ALL features)
- [ ] Data types match between frontend and backend
- [ ] Field naming conventions use snake_case consistently
- [ ] Access patterns (dict vs object) verified for repository methods
- [ ] Country-specific variations handled (CO vs MX) if applicable

### Testing
- [ ] Validation commands test all new functionality
- [ ] Edge cases documented in Testing Strategy
- [ ] E2E test covers happy path with screenshots (if UI feature)
```

## Feature
Extract the feature details from the `issue_json` variable (parse the JSON and use the title and body fields).

## Report
- Summarize the work you've just done in a concise bullet point list.
- Include the full path to the plan file you created (e.g., `specs/issue-456-adw-xyz789-sdlc_planner-add-contract-type.md`)
