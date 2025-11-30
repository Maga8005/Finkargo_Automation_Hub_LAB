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
```

## Feature
Extract the feature details from the `issue_json` variable (parse the JSON and use the title and body fields).

## Report
- Summarize the work you've just done in a concise bullet point list.
- Include the full path to the plan file you created (e.g., `specs/issue-456-adw-xyz789-sdlc_planner-add-contract-type.md`)
