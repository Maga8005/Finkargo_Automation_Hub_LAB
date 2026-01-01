# E2E Test: Domain Age Validation (Validación de Antigüedad de Dominio)

## Test Type
E2E Test - Risk Module - Fraud Detection

## Feature Under Test
Domain age validation for fraud detection through DNS lookup and WHOIS queries.

## Description
This test verifies the domain age validation feature that detects potentially fraudulent domains by:
1. Checking if domains exist (DNS resolution)
2. Looking up domain registration age via WHOIS
3. Flagging domains that are suspiciously young compared to company age

## Prerequisites
- Backend server running on localhost:8000
- python-whois package installed
- Valid network connectivity for DNS/WHOIS lookups

## Test Scenarios

### Scenario 1: Domain Existence Check (DNS)
**Given:** A domain that does not exist
**When:** The system validates the email domain
**Then:** The validation should return:
- `domain_exists: false`
- Severity: CRITICAL
- Description containing "no existe" or "no resuelve"

### Scenario 2: Young Domain Detection (< 90 days)
**Given:** A domain registered less than 90 days ago
**When:** The system validates the email domain
**Then:** The validation should return:
- `domain_exists: true`
- `domain_age_days: < 90`
- Severity: HIGH
- Description mentioning the domain age

### Scenario 3: Domain Age vs Company Age Comparison
**Given:** A domain registered < 1 year ago for a company registered 15+ years ago
**When:** The system validates the email domain with company data
**Then:** The validation should return:
- Severity: HIGH (age ratio < 10%)
- Description comparing domain and company ages

### Scenario 4: Established Domain (> 1 year)
**Given:** A domain registered more than 1 year ago
**When:** The system validates the email domain
**Then:** The validation should return:
- No discrepancy (is_suspicious: false)
- Domain age information in response

### Scenario 5: WHOIS Privacy Protection
**Given:** A domain with WHOIS privacy enabled
**When:** The system attempts to look up domain age
**Then:** The validation should return:
- `age_lookup_status: 'unavailable'`
- No penalty applied to risk score

## Test Steps

### Step 1: Backend Unit Test Verification
```bash
cd backend
pytest tests/test_domain_validation_service.py -v
```

### Step 2: Service Integration Test
```python
# Test using Python REPL
from src.core.servicios.risk.domain_validation_service import DomainValidationService
from datetime import datetime, timezone, timedelta

service = DomainValidationService()

# Test 1: Check known good domain
result = service.check_domain_existence("google.com")
assert result.exists == True
print(f"Google.com exists: {result.exists}, IP: {result.ip_address}")

# Test 2: Check non-existent domain
result = service.check_domain_existence("thisisnotarealdomain12345xyz.com")
assert result.exists == False
print(f"Fake domain exists: {result.exists}")

# Test 3: Get domain age for known old domain
result = service.get_domain_age("google.com")
print(f"Google.com age: {result.age_days} days, status: {result.lookup_status}")

# Test 4: Compare domain vs company age
company_date = datetime.now(timezone.utc) - timedelta(days=5475)  # 15 years
result = service.compare_domain_vs_company_age(
    "google.com",
    company_constitution_date=company_date
)
print(f"Comparison result: suspicious={result.is_suspicious}, severity={result.severity}")
```

### Step 3: API Integration Test
```bash
# Trigger cross-validation which includes domain age check
curl -X POST http://localhost:8000/api/risk/assessments/{assessment_id}/validate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json"
```

### Step 4: Frontend Verification
1. Navigate to Risk Assessment detail page
2. Upload documents (RUT with email)
3. Click "Ejecutar Validación"
4. Verify domain age information appears in results:
   - Domain age chip with color-coded severity
   - Registrar information when available
   - "Dominio No Resuelve" chip for non-existent domains

## Expected Results

### Cross-Validation Response
```json
{
  "assessment_id": "uuid",
  "total_discrepancies": 1,
  "results": [
    {
      "validation_type": "domain_age",
      "documents_compared": ["rut", "certificado_existencia"],
      "field_compared": "email_domain_age",
      "values_found": {
        "email": "contacto@empresa.com",
        "domain": "empresa.com",
        "domain_age_days": 45,
        "company_age_days": 5475
      },
      "is_discrepancy": true,
      "severity": "high",
      "description": "ADVERTENCIA: El dominio 'empresa.com' tiene solo 45 días...",
      "score_impact": 15
    }
  ]
}
```

### Email Validation Result
```json
{
  "is_suspicious": true,
  "detection_type": "young_domain",
  "description": "ADVERTENCIA: El dominio tiene solo 45 días de antigüedad...",
  "domain_exists": true,
  "domain_age_days": 45,
  "domain_creation_date": "2024-11-01T00:00:00Z",
  "age_lookup_status": "success",
  "domain_registrar": "GoDaddy"
}
```

## Validation Criteria

| Scenario | Expected Outcome | Severity | Score Impact |
|----------|------------------|----------|--------------|
| Domain doesn't exist | CRITICAL alert | critical | 25 |
| Domain < 90 days old | HIGH alert | high | 15 |
| Domain < 1 year, < 10% company age | HIGH alert | high | 15 |
| Domain < 1 year, no company date | MEDIUM alert | medium | 8 |
| Domain > 1 year | No discrepancy | - | 0 |
| WHOIS unavailable | No penalty | - | 0 |

## Related Files
- `backend/src/core/servicios/risk/domain_validation_service.py`
- `backend/src/core/servicios/risk/cross_validation_service.py`
- `backend/src/core/servicios/risk/email_chain_service.py`
- `backend/src/core/servicios/risk/external_contact_service.py`
- `backend/src/interface/risk_dtos.py`
- `backend/tests/test_domain_validation_service.py`
- `frontend/src/types/risk.ts`
- `frontend/src/components/risk/FKCrossValidationResults.tsx`
- `frontend/src/components/risk/FKEmailValidationResult.tsx`

## Notes
- WHOIS lookups are cached for 24 hours to avoid rate limiting
- DNS timeout is set to 5 seconds
- WHOIS timeout is set to 10 seconds
- On timeout or error, the system assumes domain exists to avoid false positives
- Free email providers (gmail.com, hotmail.com, etc.) skip domain age validation
