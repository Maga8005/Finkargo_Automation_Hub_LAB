# Feature: Fraud Detection and Risk Department Module

## Feature Description
Create a comprehensive fraud detection system integrated into a new "Riesgos" (Risk) department within the Finkargo Automation Hub. This system will automatically detect and prevent fraud attempts similar to the Azelis case, where fraudsters used legitimate identities with fake companies and professionally forged documents. The module will include:

1. **New Risk Department** - Add "Riesgos" to navigation with role-based access (risk_analyst, risk_manager roles)
2. **Automated Fraud Detection Engine** - Validation services detecting identity inconsistencies, suspicious email domains, document authenticity issues, and NIT format violations
3. **Risk Scoring System** - Weighted algorithm (0-100) with 4 risk levels (Low, Medium, High, Critical)
4. **Integration Points** - Hook into legal contract generation and credit application workflows
5. **Database Tables** - risk_assessments, fraud_detection_rules, risk_blacklist, risk_alerts
6. **User Interface** - Dashboard, evaluation details, configuration panel for risk managers

## User Story
As a **Risk Analyst or Risk Manager**
I want to **evaluate client fraud risk using automated detection algorithms and manual review workflows**
So that **I can prevent financial losses from fraudulent applications like the Azelis case**

## Problem Statement
The Azelis fraud case exposed critical vulnerabilities in the client onboarding process:
- Fraudsters used legitimate IDs (real person) with fake company representations (ROCSA vs AZELIS)
- Professional-looking forged financial statements claiming PwC audit
- Domain spoofing (acelis.com.co vs legitimate azelis.com)
- Inconsistent company names across documents (ROCSA COLOMBIA S.A. vs AZELIS COLOMBIA S.A.S.)

Currently, there is no automated system to detect these patterns, leaving the company vulnerable to similar attacks.

## Solution Statement
Implement a rule-based fraud detection system with:
1. **Automated validation services** that detect inconsistencies across documents (NIT, company name, email domains)
2. **Risk scoring algorithm** that weighs multiple fraud indicators to produce a 0-100 risk score
3. **Workflow integration** that blocks high-risk applications automatically
4. **Manual review queue** for medium-risk cases requiring human judgment
5. **Audit trail** for all decisions (compliance requirement)
6. **Configuration panel** for risk managers to adjust detection rules and thresholds

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager` (new roles to be added), and `admin`
- Backend Protection: Use `require_roles(['risk_analyst', 'risk_manager'])` from `rbac_dependencies.py`
- Frontend Protection: Use `<RoleProtectedRoute allowedRoles={[UserRole.RISK_ANALYST, UserRole.RISK_MANAGER, UserRole.ADMIN]}>` for all risk pages

## Relevant Files
Use these files to implement the feature:

**Backend - Routes (Controllers):**
- `backend/src/adapter/rest/legal_routes.py` - Reference for route patterns (RBAC, dependencies, response models)
- `backend/src/adapter/rest/rbac_dependencies.py` - Add `require_risk_role` and `require_risk_manager_role` dependencies
- `backend/src/adapter/rest/dependencies.py` - Reference for dependency injection patterns

**Backend - Services (Business Logic):**
- `backend/src/core/servicios/contract_service.py` - Reference for service patterns
- `backend/src/core/servicios/document_service.py` - Reference for document processing

**Backend - Repository (Data Access):**
- `backend/src/repositorio/contract_repository.py` - Reference for repository patterns (Supabase CRUD)
- `backend/src/repositorio/client_repository.py` - Reference for client data access (will query clients for risk evaluation)

**Backend - DTOs (Interface):**
- `backend/src/interface/legal_dtos.py` - Reference for DTO patterns (Pydantic models, enums)

**Backend - Config:**
- `backend/src/config/supabase_config.py` - Supabase client initialization
- `backend/main.py` - Register new routes

**Database - Migrations:**
- `backend/database/migration_add_legal_operations_roles.sql` - Reference for adding new roles
- `backend/database/migration_create_user_profiles.sql` - Reference for RLS policies

**Frontend - Pages:**
- `frontend/src/pages/legal/LegalDashboard.tsx` - Reference for dashboard page structure (tabs, cards, stats)
- `frontend/src/pages/alianzas/BrokersPage.tsx` - Reference for CRUD page patterns

**Frontend - Components:**
- `frontend/src/components/forms/FKContractRequest.tsx` - Reference for form components (react-hook-form + MUI)
- `frontend/src/components/RoleProtectedRoute.tsx` - Use for role-based route protection

**Frontend - Services:**
- `frontend/src/services/legalService.ts` - Reference for service layer pattern (API calls)

**Frontend - Types:**
- `frontend/src/types/index.ts` - Add new `risk_analyst` and `risk_manager` to UserRole type
- `frontend/src/types/legal.ts` - Reference for type definition patterns

**Frontend - App:**
- `frontend/src/App.tsx` - Register new risk routes

**E2E Testing:**
- `.claude/commands/test_e2e.md` - Instructions for creating E2E tests
- `.claude/commands/e2e/test_login.md` - Reference E2E test structure

### New Files

**Backend:**
- `backend/src/adapter/rest/risk_routes.py` - Risk management API endpoints
- `backend/src/core/servicios/risk/__init__.py` - Risk services package
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Core fraud detection logic
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Risk score calculation
- `backend/src/core/servicios/risk/alert_service.py` - Alert/notification handling
- `backend/src/repositorio/risk_repository.py` - Risk data access layer
- `backend/src/interface/risk_dtos.py` - Risk DTOs and request/response models

**Backend - Database Migrations:**
- `backend/database/migration_add_risk_roles.sql` - Add risk_analyst, risk_manager roles
- `backend/database/migration_create_risk_tables.sql` - Create risk_assessments, fraud_detection_rules, risk_blacklist, risk_alerts tables

**Frontend:**
- `frontend/src/pages/risk/RiskDashboard.tsx` - Main risk dashboard page
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Detailed evaluation view
- `frontend/src/pages/risk/RiskConfiguration.tsx` - Rules configuration page
- `frontend/src/components/risk/FKRiskScoreCard.tsx` - Risk score visualization component
- `frontend/src/components/risk/FKAlertList.tsx` - Active alerts display component
- `frontend/src/components/risk/FKRiskMetrics.tsx` - Dashboard metrics cards
- `frontend/src/components/risk/FKRiskEvaluationForm.tsx` - Trigger evaluation form
- `frontend/src/components/risk/FKBlacklistManager.tsx` - Blacklist management component
- `frontend/src/services/riskService.ts` - Risk API service layer
- `frontend/src/types/risk.ts` - Risk TypeScript types

**E2E Test:**
- `.claude/commands/e2e/test_risk_dashboard.md` - E2E test for risk dashboard flow

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs)
- [ ] Excel Processing (treasury, finance)
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [x] Reporting (queries, history) - Dashboard with risk metrics and history
- [x] CRUD Operations (basic data management) - Risk assessments, rules, blacklist

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| risk_repo.create() | dict | data['id'] | Not data.id |
| risk_repo.get_by_id() | dict or None | data['risk_level'] | Check None first |
| risk_repo.search() | list[dict] | for item in data: item['status'] | List of dicts |
| risk_repo.get_stats() | dict | stats['total_assessments'] | Direct dict access |
| client_repo.get_by_nit() | dict or None | client['razon_social'] | Check None first |
| blacklist_repo.is_blacklisted() | bool | Direct boolean | True/False |

### E. Database Dependencies Checklist
- [x] Required enums will be added in DTOs: `RiskLevel`, `AssessmentStatus`, `AlertSeverity`
- [x] No template files required (not document generation)
- [x] Database records created via migrations: risk_assessments, fraud_detection_rules, risk_blacklist, risk_alerts
- [x] Country-specific: Focus on Colombia first (NIT validation format: XXX.XXX.XXX-X)

### G. Query Specification (Reporting)

| Filter | Type | Required | Default |
|--------|------|----------|---------|
| status | string | No | All statuses |
| risk_level | string | No | All levels |
| client_nit | string | No | None (all clients) |
| date_from | date | No | 30 days ago |
| date_to | date | No | Today |
| assessed_by | uuid | No | All analysts |
| limit | int | No | 50 |
| offset | int | No | 0 |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| id | id | string (UUID) | Primary key |
| assessment_id | assessment_id | string | Business ID: RISK-2025-001 |
| client_nit | client_nit | string | Colombian tax ID |
| risk_level | risk_level | RiskLevel | low/medium/high/critical |
| risk_score | risk_score | number | 0.00 - 100.00 (Decimal) |
| fraud_indicators | fraud_indicators | FraudIndicator[] | JSONB array |
| status | status | AssessmentStatus | pending/in_progress/completed/escalated |
| assessed_by | assessed_by | string (UUID) | FK to user_profiles |
| assessed_at | assessed_at | string (ISO date) | Timestamp |
| review_notes | review_notes | string | Free text |
| created_at | created_at | string (ISO date) | Timestamp |
| updated_at | updated_at | string (ISO date) | Timestamp |

## Implementation Plan

### Phase 1: Foundation
1. **Database Setup** - Create migrations for new roles and tables
2. **Backend DTOs** - Define Pydantic models for risk data structures
3. **Backend Repository** - Implement data access layer for risk tables
4. **RBAC Update** - Add risk roles to rbac_dependencies.py

### Phase 2: Core Implementation
5. **Fraud Detection Service** - Implement validation logic:
   - Identity consistency checks (company name matching across documents)
   - Email domain validation (detect typosquatting like acelis vs azelis)
   - NIT format validation (Colombian format: XXX.XXX.XXX-X)
   - Document metadata analysis
6. **Risk Scoring Service** - Implement weighted scoring algorithm
7. **Alert Service** - Handle notifications and escalations
8. **API Routes** - Create REST endpoints for all risk operations

### Phase 3: Frontend Implementation
9. **TypeScript Types** - Define risk-related types
10. **API Service** - Create riskService.ts
11. **Dashboard Page** - Main risk dashboard with stats and alerts
12. **Evaluation Detail Page** - Detailed view with actions
13. **Configuration Page** - Rules and threshold management
14. **Components** - FK-prefixed reusable components

### Phase 4: Integration
15. **App Routing** - Add risk routes to App.tsx
16. **Navigation** - Add "Riesgos" to sidebar menu
17. **Roles Update** - Add new roles to frontend types

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Database Migration for Risk Roles
- Create `backend/database/migration_add_risk_roles.sql`
- Add `risk_analyst` and `risk_manager` to `user_profiles` role CHECK constraint
- Follow pattern from `migration_add_legal_operations_roles.sql`

### Step 2: Create Database Migration for Risk Tables
- Create `backend/database/migration_create_risk_tables.sql`
- Create `risk_assessments` table:
  - id (UUID PK)
  - assessment_id (VARCHAR, unique business ID: RISK-2025-001)
  - client_nit (VARCHAR, FK to clients)
  - risk_level (VARCHAR CHECK: low, medium, high, critical)
  - risk_score (DECIMAL 5,2)
  - fraud_indicators (JSONB)
  - status (VARCHAR CHECK: pending, in_progress, completed, escalated, approved, rejected)
  - assessed_by (UUID FK to user_profiles)
  - assessed_at (TIMESTAMP)
  - reviewed_by (UUID FK to user_profiles)
  - reviewed_at (TIMESTAMP)
  - review_notes (TEXT)
  - created_at, updated_at (TIMESTAMP)
- Create `fraud_detection_rules` table:
  - id (UUID PK)
  - rule_name (VARCHAR unique)
  - rule_type (VARCHAR: identity, email, document, nit, address)
  - description (TEXT)
  - weight (DECIMAL 3,2: 0.00-1.00)
  - threshold (DECIMAL 5,2)
  - is_active (BOOLEAN)
  - config (JSONB for rule-specific settings)
  - created_at, updated_at
- Create `risk_blacklist` table:
  - id (UUID PK)
  - entity_type (VARCHAR: nit, email_domain, company_name, person_id)
  - entity_value (VARCHAR)
  - reason (TEXT)
  - added_by (UUID FK to user_profiles)
  - added_at (TIMESTAMP)
  - is_active (BOOLEAN)
- Create `risk_alerts` table:
  - id (UUID PK)
  - assessment_id (UUID FK to risk_assessments)
  - alert_type (VARCHAR: new_critical, escalation, threshold_breach)
  - severity (VARCHAR: info, warning, critical)
  - message (TEXT)
  - is_read (BOOLEAN)
  - read_by (UUID FK)
  - created_at
- Enable RLS on all tables
- Create indexes for performance
- Create function `generate_risk_assessment_id()` for business IDs

### Step 3: Create E2E Test Specification
- Create `.claude/commands/e2e/test_risk_dashboard.md`
- Define test for:
  - Navigate to risk dashboard
  - Verify role-based access (only risk_analyst/risk_manager/admin)
  - View dashboard metrics
  - Create new risk evaluation
  - View evaluation details
  - Approve/reject/escalate assessment
- Reference `test_login.md` and `test_e2e.md` for format

### Step 4: Create Backend DTOs
- Create `backend/src/interface/risk_dtos.py`
- Define enums:
  - `RiskLevel(str, Enum)`: low, medium, high, critical
  - `AssessmentStatus(str, Enum)`: pending, in_progress, completed, escalated, approved, rejected
  - `AlertSeverity(str, Enum)`: info, warning, critical
  - `EntityType(str, Enum)`: nit, email_domain, company_name, person_id
  - `RuleType(str, Enum)`: identity, email, document, nit, address
- Define models:
  - `FraudIndicator(BaseModel)`: indicator_name, indicator_value (bool), severity, evidence, score_impact
  - `RiskAssessmentRequest(BaseModel)`: client_nit, assessment_type
  - `RiskAssessmentResponse(BaseModel)`: id, assessment_id, client_nit, risk_level, risk_score, fraud_indicators, status, created_at
  - `RiskAssessmentDetail(BaseModel)`: extends Response with assessed_by, assessed_at, review_notes, reviewed_by, client_info
  - `RiskDecisionRequest(BaseModel)`: status, notes
  - `RiskStatsResponse(BaseModel)`: total_assessments, pending_review, high_risk_count, critical_risk_count, approval_rate, rejection_rate
  - `FraudDetectionRuleResponse(BaseModel)`: id, rule_name, rule_type, description, weight, threshold, is_active
  - `RuleUpdateRequest(BaseModel)`: weight, threshold, is_active
  - `BlacklistEntryRequest(BaseModel)`: entity_type, entity_value, reason
  - `BlacklistEntryResponse(BaseModel)`: id, entity_type, entity_value, reason, added_by, added_at, is_active
  - `RiskAlertResponse(BaseModel)`: id, assessment_id, alert_type, severity, message, is_read, created_at

### Step 5: Create Risk Repository
- Create `backend/src/repositorio/risk_repository.py`
- Implement `RiskAssessmentRepository`:
  - `__init__(self, supabase_client)` - Store client reference
  - `create(self, data: dict) -> dict` - Insert assessment, return created record
  - `get_by_id(self, id: str) -> Optional[dict]` - Get single assessment
  - `get_by_assessment_id(self, assessment_id: str) -> Optional[dict]` - Get by business ID
  - `search(self, filters: dict) -> List[dict]` - Search with filters (status, risk_level, date range, limit/offset)
  - `update(self, id: str, updates: dict) -> Optional[dict]` - Update assessment
  - `get_stats(self) -> dict` - Aggregate statistics
- Implement `FraudRulesRepository`:
  - `list_active(self) -> List[dict]` - Get active rules ordered by weight
  - `get_by_id(self, id: str) -> Optional[dict]`
  - `update(self, id: str, updates: dict) -> Optional[dict]`
  - `create(self, data: dict) -> dict`
- Implement `BlacklistRepository`:
  - `is_blacklisted(self, entity_type: str, entity_value: str) -> bool`
  - `search(self, filters: dict) -> List[dict]`
  - `add(self, data: dict) -> dict`
  - `remove(self, id: str) -> bool`
- Implement `AlertRepository`:
  - `create(self, data: dict) -> dict`
  - `get_unread(self, limit: int) -> List[dict]`
  - `mark_read(self, id: str, user_id: str) -> bool`

### Step 6: Create Fraud Detection Service
- Create `backend/src/core/servicios/risk/__init__.py` (empty or exports)
- Create `backend/src/core/servicios/risk/fraud_detection_service.py`
- Implement `FraudDetectionService`:
  - `__init__(self, risk_repo, rules_repo, blacklist_repo, client_repo)` - Inject dependencies
  - `async evaluate_client(self, client_nit: str, user_id: str) -> dict`:
    1. Fetch client data from client_repo
    2. Check blacklist (immediate critical if found)
    3. Run all active validation rules:
       - `_check_identity_consistency()` - Company name across documents
       - `_check_email_domain()` - Detect typosquatting
       - `_check_nit_format()` - Colombian NIT validation
       - `_check_document_metadata()` - Basic document checks
       - `_check_company_history()` - Time in business
       - `_check_address_verification()` - Address consistency
    4. Calculate weighted risk score
    5. Determine risk level (0-30: low, 31-60: medium, 61-80: high, 81-100: critical)
    6. Store assessment in database
    7. Create alerts if high/critical
    8. Return assessment result
  - `_check_identity_consistency(self, client_data: dict) -> FraudIndicator`:
    - Compare razon_social across all documents
    - Flag inconsistencies (e.g., "ROCSA" vs "AZELIS")
  - `_check_email_domain(self, email: str) -> FraudIndicator`:
    - Extract domain
    - Check against known company domains for typosquatting
    - Use Levenshtein distance for similarity detection
  - `_check_nit_format(self, nit: str) -> FraudIndicator`:
    - Validate Colombian NIT format (XXX.XXX.XXX-X)
    - Verify check digit
  - Helper methods for each validation type

### Step 7: Create Risk Scoring Service
- Create `backend/src/core/servicios/risk/risk_scoring_service.py`
- Implement `RiskScoringService`:
  - `__init__(self, rules_repo)` - Load rule weights
  - `calculate_score(self, indicators: List[FraudIndicator]) -> Tuple[Decimal, RiskLevel]`:
    - Apply weights from rules configuration
    - Sum weighted scores for each indicator
    - Normalize to 0-100 scale
    - Determine risk level based on thresholds:
      - 0-30: LOW (auto-approve)
      - 31-60: MEDIUM (manual review)
      - 61-80: HIGH (detailed review + additional checks)
      - 81-100: CRITICAL (auto-reject + investigation)
    - Return (score, level)
  - Default weights (configurable via rules table):
    - identity_inconsistency: 35%
    - suspicious_email_domain: 25%
    - financial_document_issues: 20%
    - company_history: 10%
    - address_verification: 10%

### Step 8: Create Alert Service
- Create `backend/src/core/servicios/risk/alert_service.py`
- Implement `AlertService`:
  - `__init__(self, alert_repo)` - Inject dependency
  - `create_alert(self, assessment_id: str, alert_type: str, severity: str, message: str) -> dict`:
    - Insert alert into database
    - (Future: send email/Slack notification)
  - `get_active_alerts(self, limit: int = 20) -> List[dict]`:
    - Fetch unread alerts ordered by severity/date
  - `mark_alert_read(self, alert_id: str, user_id: str) -> bool`:
    - Update is_read flag

### Step 9: Create Risk Routes
- Create `backend/src/adapter/rest/risk_routes.py`
- Import required dependencies from rbac_dependencies
- Create router: `APIRouter(prefix="/api/risk", tags=["Risk Management"])`
- Create dependency factories:
  - `get_risk_repo()` - Return RiskAssessmentRepository
  - `get_rules_repo()` - Return FraudRulesRepository
  - `get_blacklist_repo()` - Return BlacklistRepository
  - `get_alert_repo()` - Return AlertRepository
  - `get_fraud_service()` - Compose FraudDetectionService with repos
- Implement endpoints:
  - `GET /dashboard` - RiskStatsResponse (require_roles(['risk_analyst', 'risk_manager']))
  - `GET /evaluations` - List[RiskAssessmentDetail] with query params (require_roles(['risk_analyst', 'risk_manager']))
  - `GET /evaluations/{id}` - RiskAssessmentDetail (require_roles(['risk_analyst', 'risk_manager']))
  - `POST /evaluate` - RiskAssessmentResponse (require_roles(['risk_analyst', 'risk_manager']))
  - `PUT /evaluations/{id}/decision` - RiskAssessmentDetail (require_roles(['risk_manager'])) - Only managers can decide
  - `GET /rules` - List[FraudDetectionRuleResponse] (require_roles(['risk_manager']))
  - `PUT /rules/{id}` - FraudDetectionRuleResponse (require_roles(['risk_manager']))
  - `GET /blacklist` - List[BlacklistEntryResponse] (require_roles(['risk_analyst', 'risk_manager']))
  - `POST /blacklist` - BlacklistEntryResponse (require_roles(['risk_manager']))
  - `DELETE /blacklist/{id}` - Success message (require_roles(['risk_manager']))
  - `GET /alerts` - List[RiskAlertResponse] (require_roles(['risk_analyst', 'risk_manager']))
  - `PUT /alerts/{id}/read` - Success message (require_roles(['risk_analyst', 'risk_manager']))

### Step 10: Update RBAC Dependencies
- Edit `backend/src/adapter/rest/rbac_dependencies.py`
- Add pre-configured dependencies:
  ```python
  require_risk_analyst_role = require_roles(['risk_analyst'])
  require_risk_manager_role = require_roles(['risk_manager'])
  require_risk_role = require_roles(['risk_analyst', 'risk_manager'])
  ```

### Step 11: Register Risk Routes in Main App
- Edit `backend/main.py`
- Add import: `from src.adapter.rest.risk_routes import router as risk_router`
- Add router: `app.include_router(risk_router)`

### Step 12: Create Frontend Types
- Create `frontend/src/types/risk.ts`
- Define TypeScript types mirroring backend DTOs:
  - `type RiskLevel = 'low' | 'medium' | 'high' | 'critical'`
  - `type AssessmentStatus = 'pending' | 'in_progress' | 'completed' | 'escalated' | 'approved' | 'rejected'`
  - `type AlertSeverity = 'info' | 'warning' | 'critical'`
  - `type EntityType = 'nit' | 'email_domain' | 'company_name' | 'person_id'`
  - `type RuleType = 'identity' | 'email' | 'document' | 'nit' | 'address'`
  - `interface FraudIndicator { indicator_name: string; indicator_value: boolean; severity: RiskLevel; evidence?: string; score_impact: number; }`
  - `interface RiskAssessment { ... }` (all fields from backend)
  - `interface RiskAssessmentDetail extends RiskAssessment { ... }`
  - `interface RiskStats { ... }`
  - `interface FraudDetectionRule { ... }`
  - `interface BlacklistEntry { ... }`
  - `interface RiskAlert { ... }`
  - `interface RiskDecisionRequest { status: AssessmentStatus; notes?: string; }`

### Step 13: Update Frontend UserRole Types
- Edit `frontend/src/types/index.ts`
- Add to `UserRole` type union: `| 'risk_analyst' | 'risk_manager'`
- Add to `UserRole` const object:
  ```typescript
  RISK_ANALYST: 'risk_analyst' as const,
  RISK_MANAGER: 'risk_manager' as const,
  ```

### Step 14: Create Risk Service
- Create `frontend/src/services/riskService.ts`
- Import apiClient and types
- Export `riskService` object with methods:
  - `getDashboard(): Promise<RiskStats>`
  - `getEvaluations(filters?): Promise<RiskAssessmentDetail[]>`
  - `getEvaluation(id: string): Promise<RiskAssessmentDetail>`
  - `createEvaluation(request): Promise<RiskAssessment>`
  - `submitDecision(id: string, decision): Promise<RiskAssessmentDetail>`
  - `getRules(): Promise<FraudDetectionRule[]>`
  - `updateRule(id: string, updates): Promise<FraudDetectionRule>`
  - `getBlacklist(filters?): Promise<BlacklistEntry[]>`
  - `addToBlacklist(entry): Promise<BlacklistEntry>`
  - `removeFromBlacklist(id: string): Promise<void>`
  - `getAlerts(): Promise<RiskAlert[]>`
  - `markAlertRead(id: string): Promise<void>`

### Step 15: Create FKRiskScoreCard Component
- Create `frontend/src/components/risk/FKRiskScoreCard.tsx`
- Props: `{ score: number; level: RiskLevel; indicators: FraudIndicator[] }`
- Display:
  - Circular progress with score (0-100)
  - Color-coded by risk level (green/yellow/orange/red)
  - Level label (Bajo/Medio/Alto/Crítico)
  - List of indicators with severity icons
- Use Material-UI CircularProgress, Card, Chip

### Step 16: Create FKRiskMetrics Component
- Create `frontend/src/components/risk/FKRiskMetrics.tsx`
- Props: `{ stats: RiskStats }`
- Display grid of metric cards:
  - Total evaluaciones
  - Pendientes de revisión
  - Alto riesgo
  - Críticos
  - Tasa de aprobación
  - Tasa de rechazo
- Use Material-UI Grid, Card, Typography with icons

### Step 17: Create FKAlertList Component
- Create `frontend/src/components/risk/FKAlertList.tsx`
- Props: `{ alerts: RiskAlert[]; onMarkRead: (id: string) => void }`
- Display list of active alerts:
  - Severity icon/color
  - Alert message
  - Timestamp
  - Mark as read button
- Use Material-UI List, ListItem, IconButton, Chip

### Step 18: Create FKRiskEvaluationForm Component
- Create `frontend/src/components/risk/FKRiskEvaluationForm.tsx`
- Props: `{ onEvaluate: (nit: string) => Promise<void> }`
- Use react-hook-form
- Fields:
  - Client NIT input (with validation)
  - Assessment type select (comprehensive, quick)
- Submit button with loading state
- Success/error alerts
- Use Material-UI TextField, Select, Button, Alert

### Step 19: Create FKBlacklistManager Component
- Create `frontend/src/components/risk/FKBlacklistManager.tsx`
- Props: `{ entries: BlacklistEntry[]; onAdd: (entry) => Promise<void>; onRemove: (id: string) => Promise<void>; canManage: boolean }`
- Display:
  - Table of blacklist entries (entity_type, entity_value, reason, added_by, date)
  - Add new entry form (modal or inline)
  - Remove button (if canManage)
- Use Material-UI Table, Dialog, Button

### Step 20: Create RiskDashboard Page
- Create `frontend/src/pages/risk/RiskDashboard.tsx`
- Layout:
  - Header: "Gestión de Riesgos y Fraude" with subtitle
  - Stats cards row (FKRiskMetrics)
  - Tabs: "Evaluaciones" | "Alertas" | "Blacklist"
  - Tab 0: Recent evaluations table with filters (status, risk_level, date range)
  - Tab 1: Active alerts (FKAlertList)
  - Tab 2: Blacklist management (FKBlacklistManager)
- State: currentTab, stats, evaluations, alerts, blacklist, loading, filters
- Effects: Load data on mount, refresh on tab change
- Actions: Navigate to detail, create evaluation, manage blacklist
- Use Material-UI Tabs, DataGrid, filters

### Step 21: Create RiskEvaluationDetail Page
- Create `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Route param: `:id`
- Layout:
  - Header with back button and assessment ID
  - Client info card (NIT, company name, contact)
  - Risk score card (FKRiskScoreCard)
  - Fraud indicators breakdown (expandable panels)
  - Decision section (for risk_manager):
    - Status select (approve/reject/escalate)
    - Notes textarea
    - Submit button
  - Audit history timeline
- State: assessment, loading, decision form
- Effects: Load assessment on mount
- Actions: Submit decision, navigate back
- Use Material-UI Card, Accordion, Timeline, Button

### Step 22: Create RiskConfiguration Page
- Create `frontend/src/pages/risk/RiskConfiguration.tsx`
- Access: risk_manager only
- Layout:
  - Header: "Configuración de Reglas de Detección"
  - Rules table:
    - Rule name, type, description
    - Weight slider (0-100%)
    - Threshold input
    - Active toggle
    - Save button per row
  - Threshold configuration section:
    - Low/Medium/High/Critical cutoffs
- State: rules, loading, editingRule
- Effects: Load rules on mount
- Actions: Update rule, save thresholds
- Use Material-UI Table, Slider, Switch, TextField

### Step 23: Add Risk Routes to App.tsx
- Edit `frontend/src/App.tsx`
- Add imports for risk pages
- Add routes inside protected layout:
  ```tsx
  {/* Risk Routes */}
  <Route
    path="risk/dashboard"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.RISK_ANALYST, UserRole.RISK_MANAGER, UserRole.ADMIN]}>
        <RiskDashboard />
      </RoleProtectedRoute>
    }
  />
  <Route
    path="risk/evaluations/:id"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.RISK_ANALYST, UserRole.RISK_MANAGER, UserRole.ADMIN]}>
        <RiskEvaluationDetail />
      </RoleProtectedRoute>
    }
  />
  <Route
    path="risk/configuration"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.RISK_MANAGER, UserRole.ADMIN]}>
        <RiskConfiguration />
      </RoleProtectedRoute>
    }
  />
  {/* Department redirect */}
  <Route
    path="department/risk"
    element={<Navigate to="/risk/dashboard" replace />}
  />
  ```

### Step 24: Add Risk Department to Navigation
- Find and edit navigation configuration (likely in `FKMainLayout.tsx` or sidebar config)
- Add "Riesgos" department with:
  - Icon: Shield or Warning icon
  - Route: /risk/dashboard
  - Roles: ['risk_analyst', 'risk_manager', 'admin']
- Add submenu items:
  - Dashboard: /risk/dashboard
  - Configuración: /risk/configuration (risk_manager only)

### Step 25: Create Backend Unit Tests
- Create `backend/tests/test_fraud_detection_service.py`
- Test cases:
  - `test_nit_format_validation_valid` - Valid Colombian NIT passes
  - `test_nit_format_validation_invalid` - Invalid NIT fails
  - `test_email_domain_typosquatting_detected` - acelis vs azelis detected
  - `test_email_domain_normal_passes` - Normal email passes
  - `test_identity_consistency_mismatch` - Different company names flagged
  - `test_identity_consistency_match` - Same names pass
  - `test_risk_score_calculation_low` - Low indicators = low score
  - `test_risk_score_calculation_critical` - High indicators = critical score
  - `test_blacklist_check_blocked` - Blacklisted NIT blocked
  - `test_blacklist_check_passes` - Non-blacklisted passes

### Step 26: Run Validation Commands
Execute all validation commands to verify implementation.

## Testing Strategy

### Unit Tests
**Backend (pytest):**
- `test_fraud_detection_service.py`:
  - NIT format validation (valid/invalid formats)
  - Email domain typosquatting detection (acelis vs azelis)
  - Identity consistency checks (company name matching)
  - Risk score calculation with different indicator combinations
  - Blacklist checking (blocked vs allowed)
- `test_risk_scoring_service.py`:
  - Weight application
  - Score normalization
  - Level determination thresholds
- `test_risk_repository.py`:
  - CRUD operations
  - Search with filters
  - Stats aggregation

### Edge Cases
1. **Empty client data** - Should return error, not crash
2. **Missing documents** - Should note as "unable to verify" not automatic fail
3. **NIT with special characters** - Handle various formats (with/without dots/dashes)
4. **Unicode in company names** - Handle accents and special characters
5. **Very long company names** - Truncate or handle gracefully
6. **Concurrent evaluations** - Same client evaluated simultaneously
7. **Historical data** - Client with existing assessments
8. **Blacklist with wildcards** - Pattern matching for domains
9. **Rule weight changes** - Existing assessments not retroactively affected
10. **All indicators fail** - Maximum score capped at 100

## Acceptance Criteria
1. Risk analyst can access dashboard and view risk metrics
2. Risk analyst can create new risk evaluation by entering client NIT
3. System evaluates client against all active fraud detection rules in under 3 seconds
4. Risk score is calculated correctly using weighted algorithm
5. Risk level is assigned based on score thresholds (Low/Medium/High/Critical)
6. High/Critical risk evaluations generate alerts automatically
7. Risk manager can approve/reject/escalate evaluations
8. Risk manager can configure rule weights and thresholds
9. Risk manager can manage blacklist entries
10. All decisions are logged with audit trail
11. Navigation includes "Riesgos" department for authorized roles
12. Admin users have full access to all risk features
13. Unauthorized users cannot access risk pages (403 response)
14. E2E test passes for dashboard flow

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

1. Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_risk_dashboard.md` to validate this functionality works

2. Backend tests:
```bash
cd backend && python -m pytest tests/test_fraud_detection_service.py -v
```

3. Backend linting:
```bash
cd backend && ruff check src/
```

4. Frontend linting:
```bash
cd frontend && npm run lint
```

5. TypeScript type check:
```bash
cd frontend && npx tsc --noEmit
```

6. Frontend build:
```bash
cd frontend && npm run build
```

7. Backend full test suite:
```bash
cd backend && python -m pytest
```

## Notes

### New Dependencies
- **Backend**: No new pip packages required. Using existing:
  - Pydantic for DTOs
  - FastAPI for routes
  - Supabase for database
- **Frontend**: No new npm packages required. Using existing:
  - Material-UI components
  - react-hook-form for forms
  - Axios via apiClient

### Future Enhancements
1. **ML Integration**: Replace rule-based system with trained model for pattern detection
2. **Document OCR**: Integrate with AWS Textract or similar for document text extraction
3. **External Data Sources**: Connect to DIAN (Colombian tax authority) for NIT verification
4. **Email Notifications**: Send alerts to risk team when critical evaluations occur
5. **Batch Evaluation**: Evaluate multiple clients from CSV upload
6. **Risk Trends**: Historical charts showing fraud attempt patterns over time
7. **API Webhooks**: Notify external systems when risk levels change

### Compliance Considerations
- All automated decisions must be auditable (audit trail in risk_assessments table)
- Users must have appeal process for false positives (escalation workflow)
- Must comply with Colombian data protection laws (Ley 1581 de 2012)
- Personal data minimization - only store what's necessary for risk evaluation

### Performance Targets
- Risk evaluation: < 3 seconds response time
- Dashboard load: < 1 second
- 90%+ detection rate for Azelis-type fraud patterns
- < 5% false positive rate

## Plan Quality Checklist

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification (Reporting + CRUD)
- [x] All new files listed in "New Files" section (18 new files)
- [x] All database migrations identified and tasks created (2 migrations)
- [x] E2E test file task included (Step 3)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Reporting:**
- [x] Query filters and parameters documented (Section G)
- [x] Pagination/sorting requirements specified (limit/offset in repository)

**CRUD Operations:**
- [x] Repository patterns defined (Step 5)
- [x] Validation rules specified (DTOs with Pydantic validators)

### Consistency (ALL features)
- [x] Data types match between frontend and backend (Interface Mapping table)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods (Section D)
- [x] Country-specific variations handled - Colombia NIT format specified

### Testing
- [x] Validation commands test all new functionality (7 commands)
- [x] Edge cases documented in Testing Strategy (10 cases)
- [x] E2E test covers happy path with screenshots (test_risk_dashboard.md)
