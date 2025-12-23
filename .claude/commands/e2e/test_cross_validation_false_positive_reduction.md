# E2E Test: Cross-Validation False Positive Reduction

Test the improved cross-validation logic that eliminates false positives from formatting differences while detecting real fraud indicators.

## User Story

As a Risk Analyst
I want cross-validation to only flag REAL discrepancies (not formatting differences)
So that I can focus on actual fraud indicators without alert fatigue

## Feature Overview

This test validates the improvements to the cross-validation system:

1. **Data Normalization** - Company names, NITs, and cities with different formatting should NOT be flagged
2. **Typosquatting Detection** - Similar-looking domains (e.g., acelis.com.co vs azelis.com) should be flagged
3. **Check Digit Validation** - NITs with same base but different check digits should be flagged separately
4. **Provider Domain Detection** - Free email providers (Gmail, Hotmail) for business use should be flagged

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User logged in with `risk_analyst` or `risk_manager` role

## Test Credentials

Use test account:
- Email: test-risk@finkargo.com
- Password: [configured test password]
- Expected Role: risk_analyst or risk_manager

## Test Steps

### Part 1: Verify False Positives are Eliminated

This test validates that formatting differences are NOT flagged as discrepancies.

#### Test Case 1.1: Company Name S.A.S. Variations

1. Login as Risk Analyst
2. Navigate to `/risk/dashboard`
3. Create a new evaluation with a test client NIT
4. Upload or simulate documents with:
   - Document 1 (RUT): Company name = "AZELIS COLOMBIA S.A.S."
   - Document 2 (Certificado): Company name = "AZELIS COLOMBIA SAS"
5. Run cross-validation
6. **Verify**: Company name validation shows "Consistente" (no discrepancy)
7. **Verify**: Description mentions "diferencias de formato ignoradas"
8. **Verify**: Score impact is 0 points
9. Take a screenshot

#### Test Case 1.2: NIT Formatting Variations

1. In the same evaluation, verify NIT validation with:
   - Document 1 (RUT): NIT = "830.027.231-3"
   - Document 2 (Certificado): NIT = "830027231 3"
2. **Verify**: NIT validation shows "Consistente" (no discrepancy)
3. **Verify**: Score impact is 0 points
4. Take a screenshot

#### Test Case 1.3: City with Department Info

1. Verify city validation with:
   - Document 1 (RUT): City = "Tenjo (Cundinamarca)"
   - Document 2 (Certificado): City = "Tenjo"
2. **Verify**: Address validation shows "Consistente" (no discrepancy)
3. **Verify**: Score impact is 0 points
4. Take a screenshot

### Part 2: Verify Real Discrepancies are Detected

This test validates that actual fraud indicators are properly flagged.

#### Test Case 2.1: Different Company Names

1. Create a new evaluation
2. Upload/simulate documents with:
   - Document 1 (RUT): Company name = "ROCSA COLOMBIA S.A."
   - Document 2 (Certificado): Company name = "AZELIS COLOMBIA S.A.S."
3. Run cross-validation
4. **Verify**: Company name validation shows CRITICAL discrepancy
5. **Verify**: Score impact is 25 points
6. **Verify**: Description shows both normalized company names
7. Take a screenshot showing the CRITICAL alert

#### Test Case 2.2: Different NIT Base Numbers

1. Verify NIT validation with different base numbers:
   - Document 1 (RUT): NIT = "830.027.231-3"
   - Document 2 (Certificado): NIT = "900.123.456-7"
2. **Verify**: NIT validation shows CRITICAL discrepancy
3. **Verify**: Score impact is 25 points
4. Take a screenshot

#### Test Case 2.3: Different Check Digits Only

1. Verify NIT validation with same base but different check digits:
   - Document 1 (RUT): NIT = "830.027.231-3"
   - Document 2 (Certificado): NIT = "830.027.231-1"
2. **Verify**: A HIGH severity discrepancy is flagged
3. **Verify**: Validation type shows "NIT Check Digit" or "Dígito de Verificación NIT"
4. **Verify**: Score impact is 15 points (not 25)
5. **Verify**: Description mentions "posible error de digitación"
6. Take a screenshot

### Part 3: Verify Typosquatting Detection

This test validates the new typosquatting detection feature.

#### Test Case 3.1: Azelis Fraud Case Pattern

1. Create a new evaluation
2. Upload/simulate RUT document with:
   - Company name = "AZELIS COLOMBIA S.A.S."
   - Email = "contacto@acelis.com.co" (typosquatting domain)
3. Run cross-validation
4. **Verify**: Typosquatting validation is triggered
5. **Verify**: Severity is CRITICAL (25 points)
6. **Verify**: Description mentions:
   - "TYPOSQUATTING" or "typosquatting"
   - Similarity percentage (should be > 70%)
   - The similar domain "azelis.com"
7. Take a screenshot of the typosquatting alert

#### Test Case 3.2: TLD Variation Detection

1. Verify email domain with TLD variation:
   - Email = "contacto@azelis.com.co" (vs expected azelis.com)
2. **Verify**: TLD variation is flagged (MEDIUM severity)
3. **Verify**: Description mentions variation between .com and .com.co
4. Take a screenshot

#### Test Case 3.3: Free Email Provider Detection

1. Verify with free email provider:
   - Email = "empresa@gmail.com"
2. **Verify**: Provider domain validation is triggered
3. **Verify**: Severity is MEDIUM (8 points)
4. **Verify**: Description mentions "proveedor de email gratuito"
5. Take a screenshot

### Part 4: Verify Scoring Accuracy

#### Test Case 4.1: Zero Score for Formatting Differences

1. Review an evaluation with only formatting differences
2. **Verify**: Total cross-validation score impact is 0
3. **Verify**: Risk score was not increased by formatting differences
4. Take a screenshot

#### Test Case 4.2: Accurate Score for Real Discrepancies

1. Review an evaluation with:
   - Company name mismatch (CRITICAL, +25)
   - Check digit mismatch (HIGH, +15)
   - City difference (MEDIUM, +8)
2. **Verify**: Total score impact = 48 points
3. Take a screenshot showing score breakdown

## Success Criteria

- Formatting differences (S.A.S. vs SAS, NIT formatting, city + department) produce 0 discrepancies
- Real discrepancies (different company names, different NITs) produce CRITICAL alerts
- Check digit mismatches produce HIGH alerts (separate from NIT mismatch)
- Typosquatting domains produce CRITICAL alerts with similarity percentage
- Free email providers produce MEDIUM alerts
- Score calculations match expected values
- UI displays new validation types correctly:
  - "Dígito de Verificación NIT" for check digit issues
  - "Typosquatting de Dominio" for domain similarity
  - "Proveedor de Email" for free email providers

## Screenshots Required

1. Formatting differences shown as consistent (no discrepancy)
2. CRITICAL company name discrepancy
3. NIT check digit HIGH discrepancy
4. Typosquatting CRITICAL alert with similarity details
5. Free email provider MEDIUM alert
6. Score breakdown showing accurate calculations

## Validation Type Labels to Verify

| Validation Type | Spanish Label |
|----------------|---------------|
| company_name | Nombre de Empresa |
| nit | NIT |
| nit_check_digit | Dígito de Verificación NIT |
| legal_representative | Representante Legal |
| shareholders | Accionistas |
| financial_continuity | Continuidad Financiera |
| email_domain | Dominio de Email |
| typosquatting | Typosquatting de Dominio |
| provider_domain | Proveedor de Email |
| address | Dirección |

## Expected Severity Mapping

| Scenario | Severity | Score Impact |
|----------|----------|-------------|
| Different company names (normalized) | CRITICAL | +25 |
| Different NIT base numbers | CRITICAL | +25 |
| Typosquatting domain detected | CRITICAL | +25 |
| Different NIT check digits only | HIGH | +15 |
| Suspicious TLD detected | HIGH | +15 |
| Different legal representative | HIGH | +15 |
| TLD variation (.com vs .com.co) | MEDIUM | +8 |
| Free email provider | MEDIUM | +8 |
| Different cities | MEDIUM | +8 |

## Notes

- This test focuses on the improved normalization and typosquatting detection
- Real document uploads are optional; the test can be performed using mock data
- The backend API can be tested directly if frontend is not available
- Cross-validation improvements are backward compatible with existing data
