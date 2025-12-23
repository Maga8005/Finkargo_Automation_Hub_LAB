# Fraud Detection and Risk Management Module Implementation

**Date**: 2025-12-21
**Issue**: #111 (ADW-fefa5443)
**Branch**: `feat-issue-111-adw-fefa5443-fraud-detection-risk-module`

## Overview

This implementation adds a comprehensive Fraud Detection and Risk Management module to the Finkargo Automation Hub. The module provides automated fraud detection, risk scoring, and review workflows for client evaluations.

## Features Implemented

### 1. Risk Department with Role-Based Access
- New roles: `risk_analyst` and `risk_manager`
- Department-level navigation in sidebar
- Role-protected routes for risk pages

### 2. Automated Fraud Detection Engine
- **NIT Validation**: Colombian tax ID format and check digit verification
- **Email Typosquatting Detection**: Levenshtein distance algorithm to detect similar domains (e.g., "acelis.com" vs "azelis.com")
- **Identity Consistency Checks**: Company name similarity matching
- **Blacklist Matching**: Check against known fraudulent entities

### 3. Risk Scoring System
- Weighted scoring algorithm (0-100 scale)
- Four risk levels with configurable thresholds:
  - **LOW** (0-30): Auto-approve
  - **MEDIUM** (31-60): Manual review
  - **HIGH** (61-80): Detailed review + additional checks
  - **CRITICAL** (81-100): Auto-reject + investigation

### 4. Risk Dashboard
- Real-time metrics display
- Evaluation history with DataGrid
- Active alerts management
- Blacklist management (add/remove entities)

### 5. Configuration Panel
- Rule weight configuration
- Threshold adjustment
- Enable/disable individual rules

## Files Created/Modified

### Database Migrations
- `backend/database/migration_add_risk_roles.sql` - Adds risk_analyst and risk_manager roles
- `backend/database/migration_create_risk_tables.sql` - Creates risk_assessments, fraud_detection_rules, risk_blacklist, risk_alerts tables

### Backend
- `backend/src/interface/risk_dtos.py` - Pydantic DTOs for risk module
- `backend/src/repositorio/risk_repository.py` - Repository classes for database operations
- `backend/src/core/servicios/risk/` - Service layer:
  - `__init__.py`
  - `fraud_detection_service.py` - Core fraud detection algorithms
  - `risk_scoring_service.py` - Weighted score calculation
  - `alert_service.py` - Alert creation and management
- `backend/src/adapter/rest/risk_routes.py` - REST API endpoints
- `backend/src/adapter/rest/rbac_dependencies.py` - Updated with risk role dependencies
- `backend/main.py` - Registered risk routes and department
- `backend/tests/test_fraud_detection_service.py` - Unit tests (19 tests)

### Frontend
- `frontend/src/types/risk.ts` - TypeScript type definitions
- `frontend/src/types/index.ts` - Updated UserRole enum
- `frontend/src/services/riskService.ts` - API client service
- `frontend/src/components/risk/` - Reusable components:
  - `FKRiskScoreCard.tsx` - Circular score visualization
  - `FKRiskMetrics.tsx` - Dashboard metrics cards
  - `FKAlertList.tsx` - Alerts table with actions
  - `FKRiskEvaluationForm.tsx` - New evaluation form
  - `FKBlacklistManager.tsx` - Blacklist management table
- `frontend/src/pages/risk/` - Page components:
  - `RiskDashboard.tsx` - Main dashboard with tabs
  - `RiskEvaluationDetail.tsx` - Evaluation detail and decision
  - `RiskConfiguration.tsx` - Rules configuration
- `frontend/src/App.tsx` - Added risk routes
- `frontend/src/components/ui/FKSidebar.tsx` - Added risk department navigation

### E2E Test Specification
- `.claude/commands/e2e/test_risk_dashboard.md` - E2E test specification

## API Endpoints

| Method | Endpoint | Description | Required Role |
|--------|----------|-------------|---------------|
| GET | `/api/risk/dashboard` | Get dashboard stats | risk_analyst, risk_manager |
| GET | `/api/risk/evaluations` | List evaluations | risk_analyst, risk_manager |
| POST | `/api/risk/evaluations` | Create new evaluation | risk_analyst, risk_manager |
| GET | `/api/risk/evaluations/{id}` | Get evaluation detail | risk_analyst, risk_manager |
| PUT | `/api/risk/evaluations/{id}` | Submit decision | risk_manager |
| GET | `/api/risk/rules` | Get fraud detection rules | risk_analyst, risk_manager |
| PUT | `/api/risk/rules/{id}` | Update rule | risk_manager |
| GET | `/api/risk/blacklist` | List blacklist entries | risk_analyst, risk_manager |
| POST | `/api/risk/blacklist` | Add to blacklist | risk_manager |
| DELETE | `/api/risk/blacklist/{id}` | Remove from blacklist | risk_manager |
| GET | `/api/risk/alerts` | Get alerts | risk_analyst, risk_manager |
| PUT | `/api/risk/alerts/{id}/read` | Mark alert as read | risk_analyst, risk_manager |

## Database Tables

### risk_assessments
Stores risk evaluation results with scores, indicators, and status.

### fraud_detection_rules
Configurable rules with weights and thresholds for fraud detection.

### risk_blacklist
Known fraudulent entities (NITs, domains, company names).

### risk_alerts
System-generated alerts for high-risk scenarios.

## Validation Results

### Backend Tests
```
19 passed in 0.73s
```

### Frontend Build
```
✓ built in 44.80s
```

## Next Steps (Manual)

1. Apply database migrations in Supabase:
   - `migration_add_risk_roles.sql`
   - `migration_create_risk_tables.sql`

2. Create initial fraud detection rules in database

3. Test with real NIT data to verify detection accuracy

4. Configure alert thresholds based on business requirements

## Technical Notes

### Fraud Detection Algorithms

**NIT Check Digit Calculation**:
Uses Colombian DIAN algorithm with weights [41, 37, 29, 23, 19, 17, 13, 7, 3] for module-11 check digit verification.

**Typosquatting Detection**:
Implements Levenshtein distance algorithm to detect domain names within edit distance of 2 from known legitimate domains.

**Risk Score Calculation**:
```
score = Σ(weight_i × impact_i) for triggered indicators
risk_level = determine_level(score)
```

### Architecture Compliance

This implementation follows Clean Architecture principles:
- **adapter/rest**: API routes and controllers
- **core/servicios**: Business logic services
- **repositorio**: Data access layer
- **interface**: DTOs and data contracts
