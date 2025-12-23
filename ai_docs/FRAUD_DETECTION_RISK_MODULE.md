# Fraud Detection & Risk Management Module

## User Manual & Technical Documentation

**Version:** 1.0
**Last Updated:** December 2024
**Module:** Riesgos (Risk Department)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting Started](#2-getting-started)
3. [User Roles & Permissions](#3-user-roles--permissions)
4. [Risk Dashboard](#4-risk-dashboard)
5. [Creating Risk Evaluations](#5-creating-risk-evaluations)
6. [Understanding Risk Scores](#6-understanding-risk-scores)
7. [Fraud Detection Rules](#7-fraud-detection-rules)
8. [Making Decisions](#8-making-decisions)
9. [Blacklist Management](#9-blacklist-management)
10. [Alert System](#10-alert-system)
11. [API Reference](#11-api-reference)
12. [Database Schema](#12-database-schema)
13. [Configuration](#13-configuration)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Overview

The **Fraud Detection & Risk Management Module** is an enterprise-grade system for evaluating client fraud risk at Finkargo. It provides:

- **Automated Risk Assessment**: Evaluates clients through multiple fraud indicators
- **Risk Scoring**: Weighted algorithm producing scores from 0-100
- **Blacklist Management**: Block known fraudulent entities
- **Alert System**: Real-time notifications for high-risk situations
- **Decision Workflow**: Structured approval/rejection process

### Key Benefits

| Benefit | Description |
|---------|-------------|
| Fraud Prevention | Identify suspicious clients before financial exposure |
| Consistency | Standardized evaluation criteria across all assessments |
| Audit Trail | Complete history of assessments and decisions |
| Efficiency | Automated checks reduce manual review time |

---

## 2. Getting Started

### Accessing the Module

1. Log in to Finkargo Automation Hub
2. Navigate to **Riesgos** in the left sidebar
3. You'll land on the Risk Dashboard

### Prerequisites

- Active user account with `risk_analyst`, `risk_manager`, or `admin` role
- Client data must exist in the system (NIT registered)

### Navigation

```
Riesgos (Risk Department)
├── Dashboard Tab
│   ├── Risk Metrics
│   └── Recent Evaluations
├── Evaluaciones Tab
│   └── All Evaluations List
├── Alertas Tab
│   └── System Alerts
└── Lista Negra Tab
    └── Blacklist Management
```

---

## 3. User Roles & Permissions

### Available Roles

| Role | Description |
|------|-------------|
| `risk_analyst` | Can create and view evaluations |
| `risk_manager` | Full access including decisions and configuration |
| `admin` | System administrator with complete access |

### Permission Matrix

| Action | Risk Analyst | Risk Manager | Admin |
|--------|:------------:|:------------:|:-----:|
| View Dashboard | ✓ | ✓ | ✓ |
| View Evaluations | ✓ | ✓ | ✓ |
| Create Evaluation | ✓ | ✓ | ✓ |
| View Evaluation Details | ✓ | ✓ | ✓ |
| Submit Decision (Approve/Reject) | ✗ | ✓ | ✓ |
| Escalate Assessment | ✗ | ✓ | ✓ |
| View/Manage Rules | ✗ | ✓ | ✓ |
| Manage Blacklist | ✗ | ✓ | ✓ |
| View Alerts | ✓ | ✓ | ✓ |
| Mark Alerts as Read | ✓ | ✓ | ✓ |

---

## 4. Risk Dashboard

### Dashboard Components

#### Risk Metrics Card

Displays aggregate statistics:
- Total evaluations
- Evaluations by risk level (Low, Medium, High, Critical)
- Pending reviews count
- Recent activity summary

#### Evaluations Table

Shows all risk assessments with columns:
- **ID**: Assessment identifier (e.g., RISK-2025-001)
- **Cliente**: Client NIT
- **Nivel de Riesgo**: Risk level badge (color-coded)
- **Puntuación**: Numeric score (0-100)
- **Estado**: Current status
- **Fecha**: Assessment date
- **Acciones**: View details button

#### Filters Available

- Status filter (Pending, Completed, Approved, Rejected, Escalated)
- Risk level filter (Low, Medium, High, Critical)
- Date range
- Client NIT search

---

## 5. Creating Risk Evaluations

### Step-by-Step Process

1. **Open New Evaluation Dialog**
   - Click "Nueva Evaluación" button on Dashboard
   - Or use the floating action button (+)

2. **Enter Client Information**
   - **NIT del Cliente**: Enter the client's tax ID (required)
   - **Tipo de Evaluación**: Select assessment type
     - `Comprehensive`: Full fraud detection checks (recommended)
     - `Quick`: Lightweight checks for low-risk scenarios

3. **Submit Evaluation**
   - Click "Evaluar" button
   - System processes the assessment (typically 2-5 seconds)

4. **View Results**
   - Assessment appears in evaluations list
   - Click to view detailed results

### What Happens During Evaluation

```
1. Client Lookup
   └── Fetch client data from database

2. Blacklist Check
   └── Check NIT, email, company name against blacklist
   └── If matched → Auto-reject with CRITICAL score

3. Fraud Detection
   └── Run 6 detection rules:
       ├── Identity Consistency
       ├── Email Domain Validation
       ├── NIT Format Validation
       ├── Document Metadata Check
       ├── Company History Check
       └── Address Verification

4. Score Calculation
   └── Apply weighted scoring algorithm
   └── Determine risk level

5. Alert Generation
   └── Create alerts if HIGH or CRITICAL

6. Store Results
   └── Save assessment with full audit trail
```

---

## 6. Understanding Risk Scores

### Risk Score Range

The risk score is a number from **0 to 100**:

| Score Range | Risk Level | Color | Meaning |
|-------------|------------|-------|---------|
| 0-30 | **LOW** | Green | Low fraud probability, auto-approved |
| 31-60 | **MEDIUM** | Amber | Moderate risk, requires review |
| 61-80 | **HIGH** | Red | High risk, detailed review required |
| 81-100 | **CRITICAL** | Dark Red | Very high risk, investigation required |

### Score Calculation Formula

```
Risk Score = Σ (Rule Weight × Indicator Impact)

Where:
- Each rule has a weight (0.0 to 1.0)
- Each indicator has an impact score (0 to 100)
- Final score is capped at 100
```

### Example Calculation

```
Rule                    | Weight | Impact | Contribution
------------------------|--------|--------|-------------
Email Domain            | 0.25   | 80     | 20.0
Identity Consistency    | 0.35   | 40     | 14.0
NIT Validation          | 0.10   | 0      | 0.0
Document Metadata       | 0.10   | 30     | 3.0
Company History         | 0.10   | 50     | 5.0
Address Verification    | 0.10   | 20     | 2.0
------------------------|--------|--------|-------------
TOTAL RISK SCORE        |        |        | 44.0 (MEDIUM)
```

### Reading Fraud Indicators

Each assessment includes detailed fraud indicators:

```json
{
  "indicator_name": "email_domain_validation",
  "indicator_value": true,
  "severity": "high",
  "evidence": "Dominio de email similar a empresa conocida (posible typosquatting): acelis.com.co vs azelis.com",
  "score_impact": 80
}
```

| Field | Description |
|-------|-------------|
| `indicator_name` | Which check was performed |
| `indicator_value` | `true` = fraud signal detected |
| `severity` | Impact level (low/medium/high/critical) |
| `evidence` | Human-readable explanation |
| `score_impact` | Points contributed to risk score |

---

## 7. Fraud Detection Rules

### Active Detection Rules

#### 1. Identity Consistency Check

**Purpose**: Detect company name fraud and impersonation

**What It Checks**:
- Company name similarity to known legitimate companies
- Uses Levenshtein distance algorithm (fuzzy matching)
- Flags unusually short representative names

**Known Companies Database**:
- BASF, Dow, DuPont, Syngenta, Bayer, Azelis, Brenntag, Univar, IMCD, Caldic

**Example Fraud Pattern**:
```
Legitimate: "Azelis Colombia S.A.S"
Fraudulent: "Azelis Colmbia S.A.S" (typo)
Fraudulent: "Azelis Solutions" (similar name)
```

#### 2. Email Domain Validation

**Purpose**: Detect email-based fraud attempts

**What It Checks**:
- **Typosquatting**: Misspelled versions of legitimate domains
- **Suspicious TLDs**: Dangerous extensions (.xyz, .top, .tk, .ml, .ga, .cf, .gq, .work, .click)
- **Free Providers**: Business use of Gmail/Hotmail/Yahoo

**Typosquatting Detection**:
```
Legitimate: azelis.com
Suspicious: azelis.com.co (distance = 3, close match)
Suspicious: acelis.com (distance = 1, very close)
```

#### 3. NIT Format Validation

**Purpose**: Validate Colombian tax ID format

**What It Checks**:
- Format: XXX.XXX.XXX-X or XXXXXXXXX-X
- Check digit calculation using weighted prime multiplier algorithm
- Detects invalid or fabricated NITs

**Valid NIT Example**: `900.123.456-7`

#### 4. Document Metadata Check

**Purpose**: Verify documentation completeness

**What It Checks**:
- Legal representative name present
- Representative's cedula provided
- City of domicile declared
- Overall document completeness

#### 5. Company History Check

**Purpose**: Assess client history and patterns

**What It Checks**:
- First-time clients (no previous assessments)
- Credit limit appropriateness for new clients
- Previous assessment outcomes

**Flag Conditions**:
- New client with credit limit > 500M COP
- No historical data available

#### 6. Address Verification

**Purpose**: Validate address consistency

**What It Checks**:
- City matches declared domicile
- Address contains valid Colombian city reference
- Consistency between address components

**Major Cities Validated**:
- Bogotá, Medellín, Cali, Barranquilla, Cartagena

### Rule Configuration

Risk Managers can adjust rule parameters:

| Parameter | Description | Range |
|-----------|-------------|-------|
| Weight | How much rule impacts final score | 0.0 - 1.0 |
| Threshold | Sensitivity level for triggering | 0 - 100 |
| Active | Enable/disable rule | true/false |

---

## 8. Making Decisions

### Who Can Make Decisions

Only users with `risk_manager` or `admin` role can submit decisions.

### Available Actions

| Action | When to Use | Result |
|--------|-------------|--------|
| **Aprobar** (Approve) | Client passes review | Status → APPROVED |
| **Rechazar** (Reject) | Client fails review | Status → REJECTED |
| **Escalar** (Escalate) | Needs senior review | Status → ESCALATED, Alert created |

### Decision Workflow

1. **Open Evaluation Detail**
   - Click on evaluation from list
   - Review all fraud indicators
   - Check client information

2. **Analyze Risk Factors**
   - Review each indicator's evidence
   - Consider score breakdown
   - Check for blacklist matches

3. **Submit Decision**
   - Select action (Approve/Reject/Escalate)
   - Add review notes (optional but recommended)
   - Confirm decision

4. **Record Created**
   - Decision timestamp recorded
   - Reviewer ID saved
   - Notes attached to assessment

### Decision Guidelines

| Risk Level | Recommended Action |
|------------|-------------------|
| LOW (0-30) | Auto-approved, verify if needed |
| MEDIUM (31-60) | Review indicators, approve if explainable |
| HIGH (61-80) | Detailed review required, consider rejection |
| CRITICAL (81-100) | Likely reject, investigate fraud indicators |

---

## 9. Blacklist Management

### What is the Blacklist?

A database of known fraudulent or high-risk entities that are automatically rejected during assessment.

### Entity Types

| Type | Description | Example |
|------|-------------|---------|
| `nit` | Company tax ID | 900.123.456-7 |
| `email_domain` | Email domain | fraudcompany.com |
| `company_name` | Company name | Empresa Fraudulenta S.A.S |
| `person_id` | Individual's cedula | 1234567890 |
| `address` | Physical address | Calle Falsa 123 |
| `phone` | Phone number | +57 300 1234567 |

### Adding to Blacklist

1. Navigate to **Lista Negra** tab
2. Click "Agregar a Lista Negra"
3. Fill in:
   - **Tipo de Entidad**: Select entity type
   - **Valor**: Enter the value to block
   - **Razón**: Explain why (required for audit)
4. Click "Agregar"

### Blacklist Behavior

When a client is evaluated:
1. System checks all blacklist entity types
2. If ANY match found:
   - Assessment immediately receives CRITICAL score (100)
   - Status set to REJECTED
   - Alert created with `blacklist_match` type
   - No further fraud checks performed

### Removing from Blacklist

1. Find entry in blacklist table
2. Click delete icon
3. Confirm removal
4. Entry is soft-deleted (preserved for audit)

---

## 10. Alert System

### Alert Types

| Type | Severity | Trigger |
|------|----------|---------|
| `new_critical` | CRITICAL | Risk score ≥ 81 |
| `escalation` | WARNING | Assessment escalated by manager |
| `threshold_breach` | WARNING/CRITICAL | Risk threshold exceeded |
| `blacklist_match` | CRITICAL | Client on blacklist |
| `review_required` | WARNING | Risk score 61-80 |

### Alert Lifecycle

```
1. Creation
   └── Automatically generated during assessment
   └── Or on manager action (escalation)

2. Display
   └── Appears in Alertas tab
   └── Unread count shown in badge

3. Review
   └── Click alert to view details
   └── Links to related assessment

4. Resolution
   └── Mark as read
   └── Recorded with user ID and timestamp
```

### Managing Alerts

- **View Alerts**: Click "Alertas" tab
- **Filter**: By severity, read status
- **Mark as Read**: Click checkmark icon
- **View Related Assessment**: Click linked assessment ID

---

## 11. API Reference

### Base URL

```
Development: http://localhost:8000/api/risk
Production: https://api-sandbox.finkargo.com.co/fkhub/risk
```

### Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Endpoints

#### Dashboard

```http
GET /api/risk/dashboard
```

Returns aggregate statistics for the dashboard.

**Response**:
```json
{
  "total_evaluations": 150,
  "by_risk_level": {
    "low": 80,
    "medium": 45,
    "high": 20,
    "critical": 5
  },
  "pending_reviews": 12,
  "recent_evaluations": [...]
}
```

#### Evaluations

```http
POST /api/risk/evaluate
```

Create new risk evaluation.

**Request Body**:
```json
{
  "client_nit": "900.123.456-7",
  "assessment_type": "comprehensive"
}
```

**Response**:
```json
{
  "id": "uuid",
  "assessment_id": "RISK-2025-001",
  "risk_score": 45.5,
  "risk_level": "medium",
  "fraud_indicators": [...],
  "status": "pending"
}
```

---

```http
GET /api/risk/evaluations
```

List evaluations with filters.

**Query Parameters**:
- `status`: Filter by status
- `risk_level`: Filter by risk level
- `client_nit`: Search by NIT
- `date_from`, `date_to`: Date range
- `limit`, `offset`: Pagination

---

```http
GET /api/risk/evaluations/{id}
```

Get evaluation details by ID.

---

```http
PUT /api/risk/evaluations/{id}/decision
```

Submit decision on evaluation.

**Request Body**:
```json
{
  "status": "approved",
  "notes": "Client verified through additional documentation"
}
```

#### Rules

```http
GET /api/risk/rules
```

List all fraud detection rules.

---

```http
PUT /api/risk/rules/{id}
```

Update rule configuration.

**Request Body**:
```json
{
  "weight": 0.30,
  "threshold": 65,
  "is_active": true
}
```

#### Blacklist

```http
GET /api/risk/blacklist
```

List blacklist entries.

**Query Parameters**:
- `entity_type`: Filter by type
- `is_active`: Active entries only
- `limit`, `offset`: Pagination

---

```http
POST /api/risk/blacklist
```

Add entry to blacklist.

**Request Body**:
```json
{
  "entity_type": "nit",
  "entity_value": "900.999.888-7",
  "reason": "Confirmed fraud case #12345"
}
```

---

```http
DELETE /api/risk/blacklist/{id}
```

Remove entry from blacklist (soft delete).

#### Alerts

```http
GET /api/risk/alerts
```

List alerts.

**Query Parameters**:
- `include_read`: Include read alerts (default: false)
- `limit`: Max results

---

```http
PUT /api/risk/alerts/{id}/read
```

Mark alert as read.

---

## 12. Database Schema

### Tables

#### risk_assessments

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| assessment_id | VARCHAR | Business ID (RISK-YYYY-NNN) |
| client_nit | VARCHAR | Client tax ID |
| risk_level | VARCHAR | low/medium/high/critical |
| risk_score | DECIMAL | 0-100 |
| fraud_indicators | JSONB | Array of indicator objects |
| status | VARCHAR | pending/completed/approved/rejected/escalated |
| assessment_type | VARCHAR | comprehensive/quick |
| assessed_by | UUID | User who ran assessment |
| assessed_at | TIMESTAMP | Assessment timestamp |
| reviewed_by | UUID | User who reviewed |
| reviewed_at | TIMESTAMP | Review timestamp |
| review_notes | TEXT | Manager's notes |
| client_data_snapshot | JSONB | Client data at assessment time |
| created_at | TIMESTAMP | Record creation |
| updated_at | TIMESTAMP | Last update |

#### fraud_detection_rules

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| rule_name | VARCHAR | Unique rule identifier |
| rule_type | VARCHAR | identity/email/document/nit/address/history |
| description | TEXT | Human-readable description |
| weight | DECIMAL | 0.0-1.0 |
| threshold | DECIMAL | 0-100 |
| is_active | BOOLEAN | Rule enabled/disabled |
| config | JSONB | Rule-specific configuration |

#### risk_blacklist

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| entity_type | VARCHAR | nit/email_domain/company_name/person_id/address/phone |
| entity_value | VARCHAR | Value to block (normalized lowercase) |
| reason | TEXT | Why entity was blacklisted |
| source | VARCHAR | manual/system |
| added_by | UUID | User who added entry |
| added_at | TIMESTAMP | When added |
| expires_at | TIMESTAMP | Optional expiration |
| is_active | BOOLEAN | Soft delete flag |

#### risk_alerts

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| assessment_id | UUID | Linked assessment (FK) |
| alert_type | VARCHAR | new_critical/escalation/threshold_breach/blacklist_match/review_required |
| severity | VARCHAR | info/warning/critical |
| title | VARCHAR | Alert title |
| message | TEXT | Alert details |
| is_read | BOOLEAN | Read status |
| read_by | UUID | User who read alert |
| read_at | TIMESTAMP | When read |
| created_at | TIMESTAMP | Alert creation |

---

## 13. Configuration

### Environment Variables

Backend configuration in `.env`:

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# Risk Module Settings (optional)
RISK_AUTO_APPROVE_THRESHOLD=30
RISK_AUTO_ESCALATE_THRESHOLD=81
```

### Adjustable Thresholds

Risk Managers can adjust via API or future configuration UI:

| Setting | Default | Description |
|---------|---------|-------------|
| Low threshold | 30 | Scores 0-30 are LOW |
| Medium threshold | 60 | Scores 31-60 are MEDIUM |
| High threshold | 80 | Scores 61-80 are HIGH |
| Critical threshold | 81+ | Scores 81-100 are CRITICAL |

### Rule Weights

Default rule weights (adjustable):

| Rule | Default Weight |
|------|----------------|
| Identity Consistency | 0.35 |
| Email Domain | 0.25 |
| NIT Validation | 0.10 |
| Document Metadata | 0.10 |
| Company History | 0.10 |
| Address Verification | 0.10 |

**Total weights should sum to 1.0**

---

## 14. Troubleshooting

### Common Issues

#### "No se encontró cliente con NIT"

**Cause**: Client doesn't exist in database

**Solution**:
1. Verify NIT format is correct
2. Check if client was imported via Legal module
3. Import client data first

#### Assessment stuck in "Pending"

**Cause**: No reviewer has taken action

**Solution**:
1. Check alerts tab for notifications
2. Risk Manager needs to approve/reject
3. Verify reviewer has correct role

#### Risk score seems too high/low

**Cause**: Rule weights may need adjustment

**Solution**:
1. Review individual fraud indicators
2. Check if rules are correctly weighted
3. Risk Manager can adjust rule weights

#### Blacklist entry not blocking

**Cause**: Entry may be inactive or mismatched

**Solution**:
1. Verify entity type matches (e.g., `nit` vs `company_name`)
2. Check entry is marked `is_active: true`
3. Values are normalized to lowercase

#### Alerts not appearing

**Cause**: May be filtered to "unread only"

**Solution**:
1. Toggle "Include Read" filter
2. Check date range filters
3. Verify assessment triggered alert condition

### Getting Help

For technical issues:
1. Check browser console for errors
2. Review backend logs
3. Contact development team with:
   - Screenshot of error
   - Assessment ID (if applicable)
   - Steps to reproduce

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **NIT** | Número de Identificación Tributaria - Colombian tax ID |
| **Typosquatting** | Registering misspelled versions of legitimate domains |
| **Levenshtein Distance** | Algorithm measuring similarity between strings |
| **RLS** | Row Level Security - database access control |
| **JSONB** | PostgreSQL binary JSON storage format |

---

## Appendix B: Quick Reference Card

### Risk Levels at a Glance

```
Score 0-30   → LOW      → Green    → Auto-approved
Score 31-60  → MEDIUM   → Amber    → Review required
Score 61-80  → HIGH     → Red      → Detailed review
Score 81-100 → CRITICAL → Dark Red → Investigation required
```

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New Evaluation | Alt + N |
| Refresh Data | F5 |
| Search | Ctrl + F |

### Status Flow

```
NEW → PENDING → COMPLETED → APPROVED
                         → REJECTED
                         → ESCALATED → APPROVED/REJECTED
```

---

*Document generated for Finkargo Automation Hub - Fraud Detection & Risk Management Module*
