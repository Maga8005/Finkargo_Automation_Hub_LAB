# Fraud Detection and Risk Department Feature Request

## Feature Title
Implement Fraud Detection System with New Risk Department Module

## Feature Description
Create a comprehensive fraud detection system integrated into a new "Riesgos" (Risk) department within the Finkargo Automation Hub. This system will automatically detect and prevent fraud attempts similar to the Azelis case, where fraudsters used legitimate identities with fake companies and professionally forged documents.

## Background Context
Based on the Azelis fraud case analysis, we identified critical vulnerabilities:
- A person used their real ID (Daniel Abad Fajardo González) but claimed to represent a different company (ROCSA instead of AZELIS)
- Professional-looking forged financial statements claiming PwC audit
- Domain spoofing (acelis.com.co vs legitimate azelis.com)
- Inconsistent company names across documents (ROCSA COLOMBIA S.A. vs AZELIS COLOMBIA S.A.S.)

## Core Requirements

### 1. New Risk Department Module
- Add "Riesgos" to the main navigation menu
- Create role-based access for risk_analyst and risk_manager roles
- Implement a dashboard showing:
  - Real-time risk metrics (evaluations in progress, active alerts by level)
  - Approval/rejection rates
  - Fraud detection trends
  - Active alerts queue

### 2. Automated Fraud Detection Engine
Implement validation services that detect:
- **Identity Consistency**: Compare company names across all documents (ID, RUT, financial statements)
- **Email Domain Validation**: Detect suspicious domains similar to known companies
- **Document Authenticity**: Verify financial document format and auditor legitimacy
- **NIT Format Validation**: Ensure tax IDs follow Colombian format rules

### 3. Risk Scoring System
Create a weighted scoring algorithm:
- Identity Inconsistency: 35% weight
- Suspicious Email Domain: 25% weight  
- Financial Document Issues: 20% weight
- Company History: 10% weight
- Address Verification: 10% weight

Risk levels:
- Low (0-30): Auto-approve
- Medium (31-60): Manual review required
- High (61-80): Detailed review + additional checks
- Critical (81-100): Auto-reject + investigation

### 4. Integration Points
- Hook into existing legal contract generation workflow
- Validate clients before allowing contract creation
- Add risk assessment step to credit application process
- Block high-risk applications automatically

### 5. Database Requirements
Create new tables:
- `risk_assessments`: Store evaluation results and decisions
- `fraud_detection_rules`: Configurable detection rules
- `risk_blacklist`: Manage blacklisted entities

### 6. User Interface
- Risk evaluation detail view showing:
  - Client information
  - Validation results with specific issues found
  - Risk score breakdown by category
  - Document analysis results
  - Action buttons (approve/reject/escalate/request more docs)
- Configuration panel for risk managers to:
  - Adjust rule weights and thresholds
  - Manage blacklists
  - Configure alert recipients

## Technical Specifications

### Backend Architecture
- Create `backend/src/adapter/rest/risk_routes.py` for API endpoints
- Implement services in `backend/src/core/servicios/risk/`:
  - `fraud_detection_service.py`: Core detection logic
  - `risk_scoring_service.py`: Score calculation
  - `document_validation_service.py`: Document checks
  - `alert_service.py`: Notification system
- Add `backend/src/repositorio/risk_repository.py` for data access
- Create DTOs in `backend/src/interface/risk_dtos.py`

### Frontend Architecture  
- Create `frontend/src/pages/risk/` directory with:
  - `RiskDashboard.tsx`: Main dashboard
  - `RiskEvaluationDetail.tsx`: Detailed evaluation view
  - `RiskConfiguration.tsx`: Rules configuration
- Add components in `frontend/src/components/risk/`:
  - `FKRiskScoreCard.tsx`: Score visualization
  - `FKAlertList.tsx`: Active alerts display
  - `FKRiskMetrics.tsx`: Metrics cards
- Add service in `frontend/src/services/riskService.ts`
- Create types in `frontend/src/types/risk.ts`

### API Endpoints Required
- `GET /api/risk/dashboard` - Dashboard metrics
- `GET /api/risk/evaluations` - List evaluations with filters
- `GET /api/risk/evaluations/{id}` - Evaluation details
- `POST /api/risk/evaluate` - Trigger evaluation for client
- `PUT /api/risk/evaluations/{id}/decision` - Record analyst decision
- `GET /api/risk/rules` - List detection rules
- `PUT /api/risk/rules/{id}` - Update rule configuration
- `GET /api/risk/blacklist` - Manage blacklist
- `POST /api/risk/blacklist` - Add to blacklist

## Success Criteria
- System detects 90%+ of Azelis-type fraud patterns
- False positive rate below 5%
- Risk evaluation completes in under 3 seconds
- All high-risk cases are blocked from proceeding
- Audit trail maintained for all decisions
- Manual review queue functions properly
- Integration doesn't disrupt existing workflows

## Priority
High - This is critical for preventing financial losses and protecting the company from fraud attempts.

## Dependencies
- Existing authentication system (Supabase)
- Current legal and operations modules
- Document upload functionality

## Notes
- Must maintain compliance with Colombian data protection laws
- All automated decisions must be auditable
- Users must have an appeal process for false positives
- Consider future ML integration but start with rule-based system