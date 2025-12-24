# PRD: Domain Existence and Age Validation for Risk Module

**Document ID:** PRD-20251223-RISK-DOMAIN-AGE
**Version:** 1.0
**Date:** December 23, 2025
**Status:** Planning Complete - Ready for Implementation

---

## Executive Summary

This document specifies the implementation of **domain existence validation** (DNS lookup) and **domain age validation** (WHOIS lookup) for the Fraud Detection & Risk Management Module. The feature compares email domain age against company registration dates from official documents to detect fraudulent domains.

**Key Decisions:**
1. **WHOIS Library**: `python-whois` (free, direct queries)
2. **Trigger Points**: Email chains + External contacts + Cross-validation
3. **Age Thresholds**: Conservative (< 90 days = HIGH, < 1 year = MEDIUM)
4. **Frontend**: Full display of domain age validation results

---

## 1. Problem Statement

Fraudsters often register lookalike domains (typosquatting) shortly before committing fraud. While the current system detects domain similarity, it cannot detect:
- Domains that **don't actually exist** (registered but not resolving)
- Domains that are **suspiciously young** relative to an established company
- Domains registered **after** the company's official registration date

**Example from Azelis fraud case:**
- Company founded: 2010 (15 years old)
- Fraudulent domain `acelis.com.co` registered: 2024 (< 1 year old)
- **Red flag**: Domain age is < 10% of company age

---

## 2. Solution Overview

### 2.1 Domain Existence Check (DNS)

Use `socket.gethostbyname()` to verify domain resolves to an IP address.

| Result | Meaning | Severity |
|--------|---------|----------|
| Resolves | Domain exists and is active | - |
| Timeout | Network issue, inconclusive | Info only |
| Not found | Domain does not exist | CRITICAL |

### 2.2 Domain Age Check (WHOIS)

Use `python-whois` library to retrieve domain creation date.

| Age | Company Date Available | Severity |
|-----|------------------------|----------|
| < 90 days | Any | HIGH (25 points) |
| < 1 year | Company > 5 years | HIGH (15 points) |
| < 1 year | No company date | MEDIUM (8 points) |
| Lookup failed | Any | Info only (0 points) |

### 2.3 Integration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DomainValidationService (NEW)                     │
│  - check_domain_existence() → DNS                                   │
│  - get_domain_age() → WHOIS + Cache                                 │
│  - compare_domain_vs_company_age()                                  │
└─────────────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
┌────────┴────────┐  ┌───────┴────────┐  ┌───────┴────────┐
│ CrossValidation │  │ EmailChainSvc  │  │ ExternalContact│
│ Service         │  │                │  │ Service        │
└─────────────────┘  └────────────────┘  └────────────────┘
```

---

## 3. Technical Specification

### 3.1 New Files to Create

#### `backend/src/core/servicios/risk/domain_validation_service.py`

```python
@dataclass
class DomainValidationResult:
    domain: str
    exists: bool                           # DNS resolved
    existence_error: Optional[str]
    creation_date: Optional[datetime]      # From WHOIS
    age_days: Optional[int]
    registrar: Optional[str]
    age_lookup_status: str                 # 'success', 'failed', 'unavailable'
    is_suspicious: bool
    severity: Optional[DiscrepancySeverity]
    description: str

class DomainValidationService:
    # Configuration
    DNS_TIMEOUT = 5          # seconds
    WHOIS_TIMEOUT = 10       # seconds
    CACHE_TTL = 86400        # 24 hours

    # Thresholds
    VERY_YOUNG_THRESHOLD = 90    # days → HIGH severity
    YOUNG_THRESHOLD = 365        # days → MEDIUM severity
    SUSPICIOUS_AGE_RATIO = 0.1   # domain age < 10% company age

    def check_domain_existence(self, domain: str) -> DomainExistenceResult
    def get_domain_age(self, domain: str) -> DomainAgeResult
    def compare_domain_vs_company_age(
        self,
        domain: str,
        company_registration_date: Optional[str],
        company_constitution_date: Optional[str]
    ) -> DomainCompanyAgeComparison
```

#### `backend/tests/test_domain_validation_service.py`

Unit tests for DNS, WHOIS, caching, and age comparison logic.

### 3.2 Files to Modify

#### `backend/requirements.txt`
```
python-whois>=0.8.0
```

#### `backend/src/interface/risk_dtos.py`

Add to `ValidationType` enum:
```python
DOMAIN_EXISTENCE = "domain_existence"
DOMAIN_AGE = "domain_age"
```

Add to `EmailValidationResult`:
```python
domain_exists: Optional[bool] = None
domain_age_days: Optional[int] = None
domain_creation_date: Optional[datetime] = None
```

#### `backend/src/core/servicios/risk/cross_validation_service.py`

Modify `_validate_email_domain()` to:
1. Import `DomainValidationService`
2. Extract dates from RUT (`registration_date`) and Certificado (`constitution_date`)
3. Call domain existence/age validation
4. Add `CrossValidationResult` entries for new validation types

#### `backend/src/core/servicios/risk/email_chain_service.py`

Modify `validate_email_chain()` to:
1. For each sender domain, run existence/age validation
2. Add discrepancies for non-existent or young domains

#### `backend/src/core/servicios/risk/external_contact_service.py`

Modify `validate_email()` to:
1. Run existence/age check alongside typosquatting
2. Update `EmailValidationResult` with new fields

### 3.3 Frontend Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/components/risk/FKCrossValidationResults.tsx` | Display domain existence/age with severity colors |
| `frontend/src/components/risk/FKExternalContactTab.tsx` | Show domain age in validation results |
| `frontend/src/components/risk/FKEmailChainUploader.tsx` | Display domain validation for sender domains |
| `frontend/src/types/risk.ts` | Add types for domain validation |

---

## 4. Severity Mapping

| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Domain does NOT exist (DNS fails) | CRITICAL | 25 points |
| Domain < 90 days old | HIGH | 15 points |
| Domain < 1 year AND < 10% of company age | HIGH | 15 points |
| Domain < 1 year (no company date available) | MEDIUM | 8 points |
| WHOIS lookup failed | LOW (info only) | 0 points |

---

## 5. Error Handling

| Scenario | Behavior |
|----------|----------|
| DNS timeout (5s) | Mark as "unknown", log warning, no discrepancy |
| WHOIS timeout (10s) | Mark age as "unavailable", continue validation |
| WHOIS privacy/blocked | Return `lookup_status="unavailable"`, no penalty |
| Invalid domain format | Return early, no network calls |

### 5.1 Caching Strategy

- Cache WHOIS results in-memory for 24 hours
- Cache key: normalized lowercase domain
- Cache both success and failure results
- Reduces rate limiting issues with WHOIS servers

---

## 6. Company Age Sources

| Document | Field | Description |
|----------|-------|-------------|
| RUT | `registration_date` | Tax authority registration date |
| Certificado de Existencia | `constitution_date` | Company incorporation date |

**Priority:** Use `constitution_date` (most reliable), fallback to `registration_date`.

---

## 7. Implementation Order

### Phase 1: Foundation
1. Add `python-whois` to requirements.txt
2. Add `DOMAIN_EXISTENCE`, `DOMAIN_AGE` to ValidationType enum
3. Create `domain_validation_service.py` with DNS/WHOIS logic
4. Write unit tests

### Phase 2: Cross-Validation Integration
5. Modify `cross_validation_service.py` to use new service
6. Extract company dates from RUT/Certificado extractions
7. Write integration tests

### Phase 3: Email Chain Integration
8. Modify `email_chain_service.py`
9. Add domain validation in `validate_email_chain()`

### Phase 4: External Contact Integration
10. Modify `external_contact_service.py`
11. Update `EmailValidationResult` DTO
12. Integrate into `validate_email()`

### Phase 5: Frontend UI Updates
13. Update `FKCrossValidationResults.tsx`
14. Update `FKExternalContactTab.tsx`
15. Update `FKEmailChainUploader.tsx`
16. Add domain age visual indicators

### Phase 6: Testing
17. Run full test suite
18. Manual testing with real domains

---

## 8. Test Cases

### Unit Tests (`test_domain_validation_service.py`)

- `test_existing_domain_resolves` - google.com should resolve
- `test_nonexistent_domain_fails` - random gibberish domain fails
- `test_dns_timeout_handled_gracefully`
- `test_whois_returns_creation_date`
- `test_whois_failure_handled_gracefully`
- `test_cache_works`
- `test_young_domain_vs_old_company_flagged`
- `test_old_domain_ok`

### Integration Tests (`test_cross_validation_domain.py`)

- `test_nonexistent_domain_creates_critical_discrepancy`
- `test_young_domain_creates_high_discrepancy`
- `test_domain_age_vs_constitution_date`

---

## 9. Acceptance Criteria

- [ ] DNS lookup correctly identifies non-existent domains
- [ ] WHOIS lookup retrieves domain creation date
- [ ] WHOIS results are cached for 24 hours
- [ ] Timeouts are handled gracefully (no crashes)
- [ ] Domain < 90 days old flags as HIGH severity
- [ ] Domain age compared against company age from documents
- [ ] CrossValidationService includes domain age check
- [ ] EmailChainService includes domain age check
- [ ] ExternalContactService includes domain age check
- [ ] Frontend displays domain age validation results
- [ ] Unit tests pass
- [ ] Integration tests pass

---

## 10. Related Documents

- `ai_docs/PRD_20251223_Riesgos_Cross_Check_Enhancements.md` - Parent PRD
- `ai_docs/FRAUD_DETECTION_RISK_MODULE.md` - Module documentation
- `ai_docs/fraud_detection_cross_validation_guide.md` - Cross-validation guide

---

## 11. Feature Summary (For /feature Command)

**Title:** Domain Existence and Age Validation for Risk Module

**Description:**
Add DNS existence checking and WHOIS age validation to detect fraudulent email domains. Compare domain age against company registration dates from RUT/Certificado documents.

**User Story:**
As a Risk Analyst,
I want to see if email domains exist and how old they are,
So that I can detect recently-registered fraudulent domains used for typosquatting.

**Problem Statement:**
Fraudsters register lookalike domains shortly before fraud. Current typosquatting detection catches similarity but not domain age. A domain registered days ago for a 15-year-old company is highly suspicious.

**Solution Statement:**
1. Add DNS lookup to verify domain existence
2. Add WHOIS lookup to get domain creation date
3. Compare domain age against company age from documents
4. Flag non-existent domains (CRITICAL) and young domains (HIGH/MEDIUM)
5. Integrate into cross-validation, email chains, and external contacts
6. Display results in frontend with severity-colored indicators

---

*Document prepared from planning session - December 23, 2025*
