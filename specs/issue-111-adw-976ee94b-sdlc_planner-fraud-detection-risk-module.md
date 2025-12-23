# Feature: Fraud Detection and Risk Department Module

## Feature Description
Implement a comprehensive fraud detection system integrated into a new "Riesgos" (Risk) department within the Finkargo Automation Hub. This system will automatically detect and prevent fraud attempts similar to the Azelis case, where fraudsters used legitimate identities with fake companies and professionally forged documents. The module includes:

- A new Risk department with dedicated dashboard and role-based access
- Automated fraud detection engine with multiple validation rules
- Risk scoring system with weighted algorithm (0-100 scale)
- Integration with existing legal contract generation workflow
- Database tables for assessments, rules, and blacklist management
- Configuration panel for rule management and threshold adjustments

## User Story
As a **Risk Analyst or Risk Manager**
I want to **evaluate client applications for potential fraud indicators and receive automated risk scores**
So that **I can prevent fraudulent transactions, protect the company from financial losses, and ensure legitimate clients receive timely service**

## Problem Statement
The current system lacks automated fraud detection capabilities. The Azelis fraud case demonstrated critical vulnerabilities:
- Fraudsters can use legitimate personal identities with fake companies
- Professional-looking forged financial statements pass manual review
- Domain spoofing (similar domains to legitimate companies) goes undetected
- Inconsistent company names across documents are not flagged
- No systematic way to track, block, or investigate high-risk applications

Without automated fraud detection, manual review is time-consuming, error-prone, and allows sophisticated fraud attempts to succeed.

## Solution Statement
Build a new "Riesgos" department module with:

1. **Automated Fraud Detection Engine**: Rule-based validation services that detect:
   - Identity inconsistencies (company names across documents)
   - Suspicious email domains (typosquatting, similar to known companies)
   - Document authenticity issues (auditor verification, format checks)
   - NIT format validation (Colombian tax ID rules)

2. **Risk Scoring System**: Weighted scoring algorithm that calculates overall risk:
   - Low (0-30): Auto-approve eligible
   - Medium (31-60): Manual review required
   - High (61-80): Detailed review + additional verification
   - Critical (81-100): Auto-reject + investigation

3. **Dashboard & UI**: Real-time metrics, evaluation queue, and decision workflow

4. **Integration**: Hook into legal contract generation to validate clients before contract creation

## Access Control
- **Required Role(s)**: `risk_analyst`, `risk_manager`, `admin`
- **Backend Protection**: New RBAC dependency `require_risk_role = require_roles(['risk_analyst', 'risk_manager'])` in `rbac_dependencies.py`
- **Frontend Protection**: `<RoleProtectedRoute allowedRoles={['risk_analyst', 'risk_manager', 'admin']}>` for all risk routes

## Relevant Files
Use these files to implement the feature:

### Backend Reference Files
- `backend/src/adapter/rest/legal_routes.py` - Route pattern example (RBAC, dependency injection, error handling)
- `backend/src/adapter/rest/rbac_dependencies.py` - Add new risk role dependencies
- `backend/src/core/servicios/contract_service.py` - Service layer pattern example
- `backend/src/repositorio/contract_repository.py` - Repository pattern with Supabase
- `backend/src/interface/legal_dtos.py` - DTO pattern with Pydantic models and enums
- `backend/main.py` - Router registration and departments endpoint
- `backend/database/schema.sql` - Database schema patterns

### Frontend Reference Files
- `frontend/src/pages/legal/LegalDashboard.tsx` - Dashboard page pattern with tabs and stats
- `frontend/src/components/forms/FKContractRequest.tsx` - Form component pattern
- `frontend/src/components/forms/FKReviewQueue.tsx` - Queue/list component pattern
- `frontend/src/services/legalService.ts` - Service layer pattern with typed methods
- `frontend/src/types/legal.ts` - TypeScript interface patterns
- `frontend/src/types/index.ts` - Global type definitions, UserRole enum
- `frontend/src/App.tsx` - Route registration with RoleProtectedRoute
- `frontend/src/constants/departments.ts` - Department configuration

### E2E Test Reference Files
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_login.md` - E2E test file pattern example

### New Files

#### Backend New Files
| File Path | Purpose |
|-----------|---------|
| `backend/src/interface/risk_dtos.py` | DTOs for risk assessments, rules, blacklist, alerts |
| `backend/src/repositorio/risk_repository.py` | Data access for risk tables |
| `backend/src/core/servicios/risk/fraud_detection_service.py` | Core fraud detection logic |
| `backend/src/core/servicios/risk/risk_scoring_service.py` | Risk score calculation |
| `backend/src/core/servicios/risk/alert_service.py` | Alert notification service |
| `backend/src/adapter/rest/risk_routes.py` | Risk API endpoints |
| `backend/database/migration_add_risk_roles.sql` | Add risk_analyst and risk_manager roles |
| `backend/database/migration_create_risk_tables.sql` | Create risk assessment tables |

#### Frontend New Files
| File Path | Purpose |
|-----------|---------|
| `frontend/src/types/risk.ts` | TypeScript types for risk module |
| `frontend/src/services/riskService.ts` | Risk API service layer |
| `frontend/src/pages/risk/RiskDashboard.tsx` | Main risk dashboard with metrics |
| `frontend/src/pages/risk/RiskEvaluationDetail.tsx` | Detailed evaluation view |
| `frontend/src/pages/risk/RiskConfiguration.tsx` | Rules configuration panel |
| `frontend/src/components/risk/FKRiskScoreCard.tsx` | Risk score visualization |
| `frontend/src/components/risk/FKAlertList.tsx` | Active alerts display |
| `frontend/src/components/risk/FKRiskMetrics.tsx` | Dashboard metrics cards |
| `frontend/src/components/risk/FKEvaluationQueue.tsx` | Evaluation queue table |
| `frontend/src/components/risk/FKBlacklistManager.tsx` | Blacklist management |

#### E2E Test New Files
| File Path | Purpose |
|-----------|---------|
| `.claude/commands/e2e/test_risk_dashboard.md` | E2E test for risk dashboard and evaluation flow |

## Pre-Implementation Verification

### Feature Category
- [x] CRUD Operations (basic data management) - Risk assessments, rules, blacklist
- [x] Reporting (queries, history) - Dashboard metrics, evaluation history
- [ ] Document Generation (contracts, PDFs)
- [ ] Excel Processing (treasury, finance)
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| `risk_repo.create_assessment()` | `dict` | `data['id']` | Assessment creation |
| `risk_repo.get_assessment_by_id()` | `Optional[dict]` | `data['risk_score']` | Get single assessment |
| `risk_repo.get_assessments()` | `List[dict]` | `[item['status'] for item]` | List assessments |
| `risk_repo.get_rules()` | `List[dict]` | `[rule['weight'] for rule]` | Get detection rules |
| `risk_repo.get_blacklist()` | `List[dict]` | `entry['entity_id']` | Blacklist entries |
| `risk_repo.get_dashboard_stats()` | `dict` | `stats['total_evaluations']` | Dashboard metrics |

### E. Database Dependencies Checklist
- [ ] Required enums exist in DTOs (will be added): `RiskLevel`, `AssessmentStatus`, `AlertPriority`, `RuleCategory`
- [ ] Database records exist (migration will create): `risk_assessments`, `fraud_detection_rules`, `risk_blacklist`, `risk_alerts`
- [ ] Roles exist (migration will add): `risk_analyst`, `risk_manager`
- [ ] Country-specific: Colombia-focused (NIT validation, Colombian company patterns)

### G. Query Specification (Reporting)

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| `status` | enum | No | All |
| `risk_level` | enum | No | All |
| `date_from` | datetime | No | 30 days ago |
| `date_to` | datetime | No | Now |
| `client_nit` | string | No | None |
| `assigned_to` | uuid | No | None |
| `limit` | int | No | 50 |
| `offset` | int | No | 0 |

### Interface Mapping (Frontend <-> Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| `id` | `id` | string (UUID) | Primary key |
| `client_nit` | `client_nit` | string | Client tax ID |
| `client_name` | `client_name` | string | Company name |
| `risk_score` | `risk_score` | number | 0-100 scale |
| `risk_level` | `risk_level` | enum | low/medium/high/critical |
| `status` | `status` | enum | pending/in_review/approved/rejected/escalated |
| `validation_results` | `validation_results` | object | JSON with check results |
| `created_at` | `created_at` | string (ISO) | Timestamp |
| `assigned_to` | `assigned_to` | string (UUID) | Analyst user ID |
| `decision_by` | `decision_by` | string (UUID) | Who made decision |
| `decision_at` | `decision_at` | string (ISO) | Decision timestamp |
| `decision_notes` | `decision_notes` | string | Review notes |

## Implementation Plan

### Phase 1: Foundation
1. **Database Migrations**
   - Add `risk_analyst` and `risk_manager` to user_profiles role CHECK constraint
   - Create `risk_assessments` table for storing evaluation results
   - Create `fraud_detection_rules` table for configurable rules
   - Create `risk_blacklist` table for blocked entities
   - Create `risk_alerts` table for notification tracking
   - Add indexes for performance on status, risk_level, created_at

2. **Backend DTOs** (`interface/risk_dtos.py`)
   - Define enums: `RiskLevel`, `AssessmentStatus`, `AlertPriority`, `RuleCategory`
   - Create request/response models for assessments, rules, blacklist
   - Add validation for Colombian NIT format

3. **Backend Repository** (`repositorio/risk_repository.py`)
   - Implement CRUD for all risk tables
   - Add query methods with filtering and pagination
   - Implement dashboard statistics aggregation

### Phase 2: Core Implementation
4. **Fraud Detection Services** (`core/servicios/risk/`)
   - `fraud_detection_service.py`: Core validation logic
     - Identity consistency check (cross-document name matching)
     - Email domain validation (typosquatting detection)
     - NIT format validation
     - Known blacklist check
   - `risk_scoring_service.py`: Weighted score calculation
     - Apply rule weights from database
     - Calculate final risk level
   - `alert_service.py`: Alert creation and notification

5. **Backend Routes** (`adapter/rest/risk_routes.py`)
   - Dashboard endpoint: `GET /api/risk/dashboard`
   - Assessments CRUD: `GET/POST /api/risk/assessments`
   - Evaluation trigger: `POST /api/risk/evaluate`
   - Decision endpoint: `PUT /api/risk/assessments/{id}/decision`
   - Rules management: `GET/PUT /api/risk/rules`
   - Blacklist management: `GET/POST/DELETE /api/risk/blacklist`

6. **Frontend Types** (`types/risk.ts`)
   - TypeScript interfaces matching backend DTOs
   - Type unions for enums
   - Props interfaces for components

7. **Frontend Service** (`services/riskService.ts`)
   - API client methods for all risk endpoints
   - Error handling with typed responses

### Phase 3: Integration
8. **Frontend Pages**
   - `RiskDashboard.tsx`: Main dashboard with tabs (Queue, History, Config)
   - `RiskEvaluationDetail.tsx`: Full evaluation view with decision buttons
   - `RiskConfiguration.tsx`: Rules and thresholds management

9. **Frontend Components**
   - `FKRiskScoreCard.tsx`: Visual score display with color coding
   - `FKRiskMetrics.tsx`: Dashboard stat cards
   - `FKAlertList.tsx`: Active alerts with priority indicators
   - `FKEvaluationQueue.tsx`: DataGrid with evaluations
   - `FKBlacklistManager.tsx`: Blacklist CRUD interface

10. **App Integration**
    - Add routes in `App.tsx` with RoleProtectedRoute
    - Add "Riesgos" to departments constant
    - Add UserRole constants for risk roles
    - Update backend departments endpoint
    - Register risk_routes in main.py

11. **Legal Integration**
    - Add optional risk validation step to contract generation
    - Block contract generation for critical-risk clients

## Step by Step Tasks

### Step 1: Create Database Migration for Risk Roles
- Read `backend/database/migration_add_legal_operations_roles.sql` for pattern
- Create `backend/database/migration_add_risk_roles.sql`
- Add `risk_analyst` and `risk_manager` to user_profiles role CHECK constraint
- Verify SQL syntax is correct

### Step 2: Create Database Migration for Risk Tables
- Read `backend/database/schema.sql` for table patterns
- Create `backend/database/migration_create_risk_tables.sql` with:
  - `risk_assessments` table (id, client_nit, client_name, risk_score, risk_level, status, validation_results, assigned_to, decision_by, decision_at, decision_notes, created_at, updated_at)
  - `fraud_detection_rules` table (id, name, category, description, weight, threshold, is_active, created_at, updated_at)
  - `risk_blacklist` table (id, entity_type, entity_id, entity_name, reason, added_by, created_at, expires_at)
  - `risk_alerts` table (id, assessment_id, priority, message, is_read, created_at)
  - Add RLS policies for authenticated users
  - Add indexes for performance
  - Insert default detection rules with weights

### Step 3: Create Backend DTOs
- Read `backend/src/interface/legal_dtos.py` for patterns
- Create `backend/src/interface/risk_dtos.py` with:
  - Enums: `RiskLevel`, `AssessmentStatus`, `AlertPriority`, `RuleCategory`
  - Request models: `RiskAssessmentCreate`, `RiskEvaluationRequest`, `RiskDecisionRequest`, `RuleUpdateRequest`, `BlacklistEntryCreate`
  - Response models: `RiskAssessmentResponse`, `RiskDashboardStats`, `FraudDetectionRuleResponse`, `BlacklistEntryResponse`, `AlertResponse`
  - Filter model: `RiskAssessmentFilter`

### Step 4: Create Risk Repository
- Read `backend/src/repositorio/contract_repository.py` for patterns
- Create `backend/src/repositorio/risk_repository.py` with:
  - `RiskRepository` class with Supabase client
  - CRUD methods for assessments, rules, blacklist, alerts
  - `get_dashboard_stats()` for aggregated metrics
  - `search_assessments()` with filtering and pagination
  - `check_blacklist()` to validate against blacklist

### Step 5: Create Fraud Detection Service
- Read `backend/src/core/servicios/contract_service.py` for service patterns
- Create `backend/src/core/servicios/risk/fraud_detection_service.py` with:
  - `FraudDetectionService` class
  - `validate_identity_consistency()` - Check company names across documents
  - `validate_email_domain()` - Detect typosquatting domains
  - `validate_nit_format()` - Colombian NIT validation with check digit
  - `check_blacklist()` - Compare against blocked entities
  - `run_all_validations()` - Execute all checks, return ValidationResults

### Step 6: Create Risk Scoring Service
- Create `backend/src/core/servicios/risk/risk_scoring_service.py` with:
  - `RiskScoringService` class
  - `calculate_risk_score()` - Apply weighted rules to validation results
  - `determine_risk_level()` - Map score to Low/Medium/High/Critical
  - `get_rule_weights()` - Fetch active rules from database

### Step 7: Create Alert Service
- Create `backend/src/core/servicios/risk/alert_service.py` with:
  - `AlertService` class
  - `create_alert()` - Create new alert for assessment
  - `mark_as_read()` - Update alert status
  - `get_unread_alerts()` - Fetch pending alerts

### Step 8: Create Risk Routes
- Read `backend/src/adapter/rest/legal_routes.py` for route patterns
- Create `backend/src/adapter/rest/risk_routes.py` with:
  - Router prefix: `/api/risk`
  - Add RBAC dependency injection
  - Endpoints:
    - `GET /dashboard` - Dashboard metrics
    - `GET /evaluations` - List with filters
    - `GET /evaluations/{id}` - Single evaluation
    - `POST /evaluate` - Trigger new evaluation
    - `PUT /evaluations/{id}/decision` - Record decision
    - `GET /rules` - List detection rules
    - `PUT /rules/{id}` - Update rule
    - `GET /blacklist` - List blacklist
    - `POST /blacklist` - Add to blacklist
    - `DELETE /blacklist/{id}` - Remove from blacklist
    - `GET /alerts` - Get alerts

### Step 9: Update RBAC Dependencies
- Edit `backend/src/adapter/rest/rbac_dependencies.py`
- Add: `require_risk_role = require_roles(['risk_analyst', 'risk_manager'])`

### Step 10: Register Risk Routes in Main App
- Edit `backend/main.py`
- Import risk_routes
- Add: `app.include_router(risk_routes.router)`
- Add "Riesgos" department to departments endpoint

### Step 11: Create Frontend Types
- Read `frontend/src/types/legal.ts` for patterns
- Create `frontend/src/types/risk.ts` with:
  - Interfaces matching all backend DTOs
  - Type unions for enums
  - Component prop interfaces

### Step 12: Create Frontend Service
- Read `frontend/src/services/legalService.ts` for patterns
- Create `frontend/src/services/riskService.ts` with:
  - All API methods for risk endpoints
  - Typed request/response handling

### Step 13: Create FKRiskMetrics Component
- Read `frontend/src/pages/legal/LegalDashboard.tsx` for metrics pattern
- Create `frontend/src/components/risk/FKRiskMetrics.tsx` with:
  - Props: `stats: RiskDashboardStats`
  - Grid of Card components showing:
    - Total evaluations
    - Pending review count
    - High risk alerts
    - Approval rate

### Step 14: Create FKRiskScoreCard Component
- Create `frontend/src/components/risk/FKRiskScoreCard.tsx` with:
  - Props: `score: number`, `level: RiskLevel`
  - Visual gauge/indicator (circular progress or bar)
  - Color coding: green (low), yellow (medium), orange (high), red (critical)
  - Score breakdown section

### Step 15: Create FKEvaluationQueue Component
- Read `frontend/src/components/forms/FKReviewQueue.tsx` for queue pattern
- Create `frontend/src/components/risk/FKEvaluationQueue.tsx` with:
  - DataGrid with evaluation list
  - Columns: client_nit, client_name, risk_score, risk_level, status, assigned_to, created_at
  - Row click to navigate to detail
  - Status filters

### Step 16: Create FKAlertList Component
- Create `frontend/src/components/risk/FKAlertList.tsx` with:
  - List of active alerts
  - Priority indicators (Critical, High, Medium, Low)
  - Mark as read functionality
  - Link to related assessment

### Step 17: Create FKBlacklistManager Component
- Create `frontend/src/components/risk/FKBlacklistManager.tsx` with:
  - DataGrid with blacklist entries
  - Add new entry form (entity_type, entity_id, entity_name, reason)
  - Delete entry button
  - Expiration date handling

### Step 18: Create RiskDashboard Page
- Read `frontend/src/pages/legal/LegalDashboard.tsx` for dashboard pattern
- Create `frontend/src/pages/risk/RiskDashboard.tsx` with:
  - Tabs: "Cola de Evaluaciones", "Historial", "Configuracion"
  - FKRiskMetrics at top
  - FKEvaluationQueue in main content
  - FKAlertList in sidebar

### Step 19: Create RiskEvaluationDetail Page
- Create `frontend/src/pages/risk/RiskEvaluationDetail.tsx` with:
  - Client information section
  - FKRiskScoreCard with breakdown
  - Validation results section (pass/fail per check)
  - Document analysis results
  - Action buttons: Approve, Reject, Escalate, Request More Docs
  - Notes text field
  - Decision submission

### Step 20: Create RiskConfiguration Page
- Create `frontend/src/pages/risk/RiskConfiguration.tsx` with:
  - Rules management table
  - Edit weight/threshold per rule
  - Enable/disable rules
  - FKBlacklistManager component
  - Threshold configuration (score ranges for each level)

### Step 21: Add UserRole Constants for Risk
- Edit `frontend/src/types/index.ts`
- Add: `RISK_ANALYST: 'risk_analyst'` and `RISK_MANAGER: 'risk_manager'` to UserRole

### Step 22: Add Riesgos Department
- Edit `frontend/src/constants/departments.ts`
- Add: `{ id: 'riesgos', name: 'Riesgos', icon: 'Security' }`

### Step 23: Register Risk Routes in App.tsx
- Edit `frontend/src/App.tsx`
- Import risk pages
- Add routes:
  ```tsx
  <Route path="riesgos" element={
    <RoleProtectedRoute allowedRoles={['risk_analyst', 'risk_manager', 'admin']}>
      <RiskDashboard />
    </RoleProtectedRoute>
  } />
  <Route path="riesgos/evaluation/:id" element={
    <RoleProtectedRoute allowedRoles={['risk_analyst', 'risk_manager', 'admin']}>
      <RiskEvaluationDetail />
    </RoleProtectedRoute>
  } />
  <Route path="riesgos/config" element={
    <RoleProtectedRoute allowedRoles={['risk_manager', 'admin']}>
      <RiskConfiguration />
    </RoleProtectedRoute>
  } />
  ```

### Step 24: Create E2E Test File
- Read `.claude/commands/test_e2e.md` for E2E test runner instructions
- Read `.claude/commands/e2e/test_login.md` for E2E test file pattern
- Create `.claude/commands/e2e/test_risk_dashboard.md` with:
  - User story for risk analyst accessing dashboard
  - Test steps: login, navigate to Riesgos, verify metrics, view evaluation
  - Success criteria and screenshot requirements

### Step 25: Add Backend Unit Tests
- Create `backend/tests/test_risk_services.py` with:
  - Tests for NIT validation
  - Tests for email domain validation
  - Tests for risk score calculation
  - Tests for blacklist checking

### Step 26: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Run E2E test to verify the feature works end-to-end

## Testing Strategy

### Unit Tests
- **NIT Validation**: Test valid/invalid Colombian NIT formats with check digit
- **Email Domain**: Test typosquatting detection (acelis vs azelis)
- **Risk Scoring**: Test weighted calculation with various validation results
- **Blacklist Check**: Test entity matching and expiration handling

### Edge Cases
- Client with no documents uploaded (no validation possible)
- Exact match to blacklisted entity
- Partial name match (should flag but not auto-reject)
- Expired blacklist entry (should not block)
- Zero-weight rules (should be skipped in calculation)
- Critical risk with no assigned analyst (should auto-reject)
- Multiple validation failures across categories

## Acceptance Criteria
1. Risk department appears in navigation for users with risk_analyst, risk_manager, or admin roles
2. Dashboard shows real-time metrics: total evaluations, pending review, high risk alerts
3. Evaluation queue displays all pending assessments with filtering by status and risk level
4. Risk score is calculated correctly using weighted rules from database
5. Evaluation detail page shows complete validation breakdown
6. Analysts can approve, reject, or escalate evaluations with notes
7. Configuration page allows risk_manager to adjust rule weights and thresholds
8. Blacklist management (add/view/remove) works correctly
9. All API endpoints require proper authentication and role authorization
10. High-risk applications (81-100) cannot proceed to contract generation
11. All decisions are logged with timestamp and user information (audit trail)
12. 3 E2E screenshots captured: dashboard, evaluation detail, configuration

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

# Frontend production build
cd frontend && npm run build
```

After all commands pass, run E2E test:
- Read `.claude/commands/test_e2e.md`
- Execute `.claude/commands/e2e/test_risk_dashboard.md` to validate the feature works end-to-end

## Notes

### Future Considerations
- **Machine Learning Integration**: The rule-based system is designed to be extensible. Future ML models can replace or augment rule-based checks by adding new validation methods to `fraud_detection_service.py`
- **External API Integration**: Consider integrating with Colombian entity verification services (RUES, DIAN) for enhanced validation
- **Real-time Notifications**: Add WebSocket support for instant alerts to analysts

### Compliance
- All automated decisions must be auditable (decision_by, decision_at, decision_notes)
- Users have appeal process via "Escalate" action
- Data retention policies should be configured per Colombian regulations

### Dependencies
- No new npm packages required (uses existing MUI, react-hook-form, date-fns)
- No new pip packages required (uses existing FastAPI, Pydantic, Supabase)

### Risk Score Weights (Default Values)
| Rule Category | Weight | Description |
|--------------|--------|-------------|
| Identity Inconsistency | 35% | Company name mismatches across documents |
| Suspicious Email Domain | 25% | Typosquatting or similar domain detection |
| Financial Document Issues | 20% | Format validation, auditor verification |
| Company History | 10% | Age of company, previous applications |
| Address Verification | 10% | Address consistency, known fraud addresses |

### Risk Level Thresholds (Default Values)
| Level | Score Range | Action |
|-------|-------------|--------|
| Low | 0-30 | Auto-approve eligible |
| Medium | 31-60 | Manual review required |
| High | 61-80 | Detailed review + additional verification |
| Critical | 81-100 | Auto-reject + investigation |

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (Step 24)
- [x] All external dependencies (npm/pip packages) listed in Notes - None required

### Category-Specific Completeness
**CRUD Operations:**
- [x] Repository patterns documented
- [x] Validation rules specified for DTOs
- [x] RBAC protection defined

**Reporting:**
- [x] Query filters and parameters documented (Section G)
- [x] Pagination/sorting requirements specified

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (Colombia-focused NIT validation)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
