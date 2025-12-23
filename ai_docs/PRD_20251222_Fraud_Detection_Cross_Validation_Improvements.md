# PRD: Fraud Detection Cross-Validation Improvements

**Document ID:** PRD-20251222-FRAUD-CV
**Version:** 1.0
**Date:** December 22, 2025
**Author:** Analysis of Azelis Fraud Case Post-Mortem
**Status:** Ready for Implementation

---

## Executive Summary

This document captures improvements required for the Fraud Detection & Risk Management Module based on the analysis of the **Azelis fraud case** (December 2025) and validation of the current cross-validation report output. The current implementation has significant **false positive issues** and **missing critical checks** that would have failed to detect the actual fraud patterns while generating noise from formatting differences.

**Key Finding:** The current report would have raised alerts **for the wrong reasons** (formatting noise) while **missing the actual fraud indicators** (email typosquatting, provider domain validation).

---

## 1. Background: The Azelis Fraud Case

### 1.1 What Happened

A sophisticated fraud attempt targeted Finkargo with a **$2.3 million credit request**. The fraudsters:

1. **Started with 2 REAL documents:**
   - Cámara de Comercio (Chamber of Commerce certificate) - REAL
   - RUT (Tax registration) - REAL
   - Both from AZELIS, a legitimate multinational company

2. **Built fake documents around the real ones:**
   - **Fake cédula**: Real person's data (Daniel Fajardo) but with fraudster's photo
   - **Fake financial statements**: 30 pages "audited by PricewaterhouseCoopers" - actually copied from another company
   - **Fake email domain**: `acelis.com.co` instead of `azelis.com` (typosquatting)
   - **Fake provider email**: `californiadavisinc.com` instead of the real California Davis domain
   - **Fake bank certification**: Bank of America statement

### 1.2 How They Were Caught

The fraud was detected through a **combination of human observation and luck**, NOT automated systems:

| Detection Method | Who Caught It | Could Be Automated? |
|-----------------|---------------|---------------------|
| Message with spelling errors | Elizabeth (CAM) | Partially |
| Provider email domain mismatch | Martín Nicholls | **YES - Missing in current tool** |
| Biometric photo context (person in "ranchería") | Manual review | Difficult |
| Email domain `acelis.com.co` vs `azelis.com` | Post-incident review | **YES - Partially implemented but failing** |
| Financial statement signature from wrong person | Molina (knew the person) | Difficult |
| PDF had visible manipulation artifacts (moveable layers) | Post-incident review | **YES - Missing in current tool** |

### 1.3 Key Quotes from Meeting Transcripts

> "El correo electrónico de la cámara de comercio era **azelis.com** y el correo falso con el que se registraron ellos era **azelis.com.co**" - Martín Nicholls

> "El proveedor original se llama California Davis y el correo al que nos pidieron escribirle al proveedor se llama **californiadariesinc.com**" - Martín Nicholls

> "Los estados financieros le copian un logo encima del otro logo y ni siquiera se toman el trabajo de que quede fijo. Uno puede quitar la foto que le pusieron encima del otro logo." - Andrés Ferrer

> "Lo que hicieron fue tomar la información de una empresa real... la Cámara de Comercio y el RUT son los únicos documentos reales." - Andrés Valdez

---

## 2. Current Report Analysis

### 2.1 Report Evaluated

**Report:** `validacion_cruzada_RISK-2025-003_2025-12-22.pdf`
- **NIT Cliente:** 830027231-3
- **Discrepancies Found:** 5
- **Critical:** 2, **High:** 2, **Medium:** 1
- **Total Score Impact:** +88 points

### 2.2 What the Report Found (Claimed Discrepancies)

| Finding | Severity | Actual Assessment |
|---------|----------|-------------------|
| Legal Representative Name Mismatch (Daniel Fajardo vs Jaime Romero) | HIGH | **VALID** - Real fraud indicator |
| Legal Representative ID Mismatch (79.908.064 vs 6135391) | HIGH | **VALID** - Real fraud indicator |
| City Mismatch (Tenjo vs Tenjo Cundinamarca) | MEDIUM | **FALSE POSITIVE** - Same city |
| Company Name (AZELIS COLOMBIA S.A.S. vs S A S vs S.A.S) | CRITICAL | **FALSE POSITIVE** - Same name, different formatting |
| NIT (830027231 3 vs 830027231-1 vs 830.027.231-3) | CRITICAL | **MOSTLY FALSE POSITIVE** - Only -1 vs -3 is real |

### 2.3 What the Report MISSED

| Missing Check | Severity | Impact on Azelis Case |
|--------------|----------|----------------------|
| Email domain typosquatting (`azelis.com.co` vs `azelis.com`) | **CRITICAL** | Would have caught the fraud |
| Provider email domain validation | **CRITICAL** | Would have caught the fraud |
| Document manipulation detection (PDF layers) | **HIGH** | Would have caught the fraud |
| Financial statement signature validation | **MEDIUM** | Would have caught the fraud |
| Source document validation (download Cámara de Comercio directly) | **HIGH** | Prevents fake document submission |

### 2.4 False Positive Rate Analysis

**Current False Positive Rate:** ~60% (3 of 5 "discrepancies" are false positives)

**Impact:** High false positive rate leads to:
- Alert fatigue (users ignore all alerts)
- Real fraud indicators buried under noise
- Reduced trust in the tool
- Wasted analyst time investigating formatting differences

---

## 3. Required Improvements

### 3.1 Data Normalization (CRITICAL - Fixes False Positives)

#### 3.1.1 Company Name Normalization

**Problem:** Different representations of the same company name flagged as discrepancies.

```
Current behavior (FALSE POSITIVE):
- "AZELIS COLOMBIA S.A.S."
- "AZELIS COLOMBIA S A S"
- "AZELIS COLOMBIA S.A.S"
→ Flagged as CRITICAL discrepancy

Required behavior:
- All normalize to "AZELIS COLOMBIA"
→ No discrepancy
```

**Implementation:**
```python
def normalize_company_name(name: str) -> str:
    if not name:
        return ''
    normalized = name.upper().strip()
    # Remove ALL legal suffix variations
    legal_suffixes = [
        'S.A.S.', 'S.A.S', 'SAS', 'S A S', 'S. A. S.',
        'S.A.', 'SA', 'S A', 'S. A.',
        'LTDA.', 'LTDA', 'LTD',
        'E.U.', 'EU', 'E U',
        'Y CIA', '& CIA', 'Y COMPANIA'
    ]
    for suffix in legal_suffixes:
        normalized = normalized.replace(suffix, '')
    # Remove punctuation and normalize spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return ' '.join(normalized.split())
```

#### 3.1.2 NIT Normalization

**Problem:** Different formatting of the same NIT flagged as discrepancies.

```
Current behavior (FALSE POSITIVE):
- "830027231 3"
- "830.027.231-3"
- "830027231-3"
→ Flagged as CRITICAL discrepancy

Required behavior:
- All normalize to "8300272313" (digits only)
- Only flag if CHECK DIGIT differs (e.g., -1 vs -3 IS a real issue)
```

**Implementation:**
```python
def normalize_nit(nit: str) -> tuple[str, str]:
    """
    Returns (base_digits, check_digit) for proper comparison.
    """
    # Remove all non-digits
    digits_only = re.sub(r'[^\d]', '', nit)

    if len(digits_only) >= 9:
        base = digits_only[:9]
        check = digits_only[9:] if len(digits_only) > 9 else ''
        return (base, check)
    return (digits_only, '')

def nits_match(nit1: str, nit2: str) -> tuple[bool, str]:
    """
    Returns (match, reason).
    """
    base1, check1 = normalize_nit(nit1)
    base2, check2 = normalize_nit(nit2)

    if base1 != base2:
        return (False, f"Base NIT differs: {base1} vs {base2}")

    if check1 and check2 and check1 != check2:
        return (False, f"Check digit differs: -{check1} vs -{check2}")

    return (True, "NITs match (formatting differences ignored)")
```

#### 3.1.3 City/Address Normalization

**Problem:** Same city with different formatting flagged.

```
Current behavior (FALSE POSITIVE):
- "Tenjo"
- "Tenjo (Cundinamarca)"
→ Flagged as MEDIUM discrepancy

Required behavior:
- Both normalize to "TENJO"
- Parenthetical department info is additional context, not a discrepancy
```

**Implementation:**
```python
def normalize_city(city: str) -> str:
    if not city:
        return ''
    normalized = city.upper().strip()
    # Remove department in parentheses
    normalized = re.sub(r'\s*\([^)]+\)\s*', '', normalized)
    # Remove accents
    replacements = {'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ñ': 'N'}
    for k, v in replacements.items():
        normalized = normalized.replace(k, v)
    # Remove D.C. variations
    normalized = re.sub(r'\s*D\.?C\.?\s*', '', normalized)
    return normalized.strip()
```

### 3.2 Typosquatting Detection (CRITICAL - Was Missing)

**Problem:** The email domain validation currently only checks if a domain exists or matches known domains. It does NOT detect typosquatting where `acelis.com.co` is similar to but NOT the same as `azelis.com`.

**Current behavior:**
- Report shows "Email domain: Consistent" ❌
- This was the EXACT fraud pattern used

**Required behavior:**
- Detect domains that are SIMILAR but NOT IDENTICAL to known legitimate domains
- Flag similarity > 70% but < 100% as HIGH severity

**Implementation:**
```python
KNOWN_LEGITIMATE_DOMAINS = [
    'azelis.com',      # Azelis
    'basf.com',        # BASF
    'dow.com',         # Dow
    'dupont.com',      # DuPont
    'evonik.com',      # Evonik
    'lanxess.com',     # Lanxess
    'brenntag.com',    # Brenntag
    'univar.com',      # Univar
    'californiadavis.com',  # California Davis
    # Add more known providers
]

def detect_typosquatting(domain: str) -> Optional[dict]:
    """
    Detect if a domain appears to be typosquatting a known legitimate domain.

    Returns dict with match info if suspected typosquatting, None otherwise.
    """
    if not domain:
        return None

    domain_lower = domain.lower()

    # Extract base domain (remove country TLD variations like .com.co)
    # acelis.com.co -> acelis
    # azelis.com -> azelis
    domain_parts = domain_lower.split('.')
    domain_base = domain_parts[0] if domain_parts else domain_lower

    for known_domain in KNOWN_LEGITIMATE_DOMAINS:
        known_base = known_domain.split('.')[0]

        # Skip if exact match (legitimate)
        if domain_base == known_base:
            continue

        # Calculate similarity
        similarity = SequenceMatcher(None, domain_base, known_base).ratio()

        # Suspicious: similar but not identical
        if 0.70 < similarity < 1.0:
            return {
                'is_typosquatting': True,
                'suspicious_domain': domain,
                'legitimate_domain': known_domain,
                'similarity_percent': round(similarity * 100, 1),
                'severity': 'CRITICAL' if similarity > 0.85 else 'HIGH',
                'description': f"POSIBLE TYPOSQUATTING: '{domain}' es {round(similarity * 100)}% similar a '{known_domain}'"
            }

    return None
```

### 3.3 Provider Domain Validation (NEW - Was Missing)

**Problem:** No validation of provider/supplier email domains. The Azelis fraud used `californiadavisinc.com` instead of the real California Davis domain.

**Required behavior:**
- Extract provider information from documents (proforma, quotation)
- Compare provider email domain against known legitimate provider domains
- Flag mismatches as HIGH severity

**Implementation:**
```python
def validate_provider_domain(
    provider_name: str,
    provider_email: str,
    known_providers: dict[str, list[str]]  # provider_name -> [legitimate_domains]
) -> Optional[dict]:
    """
    Validate that provider email domain matches known legitimate domains.

    Args:
        provider_name: Name of the provider (e.g., "California Davis")
        provider_email: Email from provider communications
        known_providers: Mapping of provider names to their legitimate domains

    Returns:
        dict with validation result if suspicious, None if valid
    """
    if not provider_email or '@' not in provider_email:
        return None

    email_domain = provider_email.split('@')[1].lower()
    provider_normalized = provider_name.upper().strip()

    # Check against known providers
    for known_name, legitimate_domains in known_providers.items():
        if known_name.upper() in provider_normalized or provider_normalized in known_name.upper():
            # Found a potential match - check domain
            if email_domain not in [d.lower() for d in legitimate_domains]:
                return {
                    'is_suspicious': True,
                    'provider_name': provider_name,
                    'email_domain': email_domain,
                    'legitimate_domains': legitimate_domains,
                    'severity': 'HIGH',
                    'description': f"Dominio de proveedor sospechoso: '{email_domain}' no coincide con dominios conocidos de {known_name}: {', '.join(legitimate_domains)}"
                }

    return None
```

### 3.4 Document Integrity Checks (NEW - Was Missing)

**Problem:** No detection of document manipulation artifacts (moveable PDF layers, logo overlays, metadata inconsistencies).

**Required behavior:**
- Detect PDFs with editable layers/elements
- Check for metadata inconsistencies (creation date, modification history)
- Flag documents that appear to be composites

**Implementation:**
```python
import fitz  # PyMuPDF

def check_document_integrity(pdf_content: bytes) -> dict:
    """
    Analyze PDF for signs of manipulation.

    Returns:
        dict with integrity check results
    """
    results = {
        'has_editable_elements': False,
        'has_multiple_fonts': False,
        'metadata_suspicious': False,
        'issues': [],
        'severity': None
    }

    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")

        # Check for editable form fields
        for page in doc:
            widgets = page.widgets()
            if widgets:
                results['has_editable_elements'] = True
                results['issues'].append("Documento contiene campos editables")

        # Check metadata
        metadata = doc.metadata
        if metadata:
            creator = metadata.get('creator', '')
            producer = metadata.get('producer', '')

            # Check for common PDF editing tools
            editing_tools = ['Adobe Acrobat', 'PDFsam', 'iLovePDF', 'SmallPDF', 'PDF-XChange']
            for tool in editing_tools:
                if tool.lower() in producer.lower() or tool.lower() in creator.lower():
                    results['metadata_suspicious'] = True
                    results['issues'].append(f"Documento modificado con herramienta de edición: {tool}")

        # Check for text annotations/overlays
        for page in doc:
            annotations = page.annots()
            if annotations:
                for annot in annotations:
                    if annot.type[0] in [8, 9, 10]:  # FreeText, Line, Square
                        results['has_editable_elements'] = True
                        results['issues'].append("Documento contiene anotaciones/overlays")
                        break

        # Determine severity
        if results['has_editable_elements'] or results['metadata_suspicious']:
            results['severity'] = 'MEDIUM'
        if len(results['issues']) > 2:
            results['severity'] = 'HIGH'

        doc.close()

    except Exception as e:
        results['issues'].append(f"Error analizando documento: {str(e)}")

    return results
```

### 3.5 Authoritative Source Validation (NEW - Per Meeting Recommendation)

**Problem:** Currently accepting client-submitted Cámara de Comercio without verification.

**Recommendation from meeting:**
> "Ya nosotros procedemos a descargar la cámara de comercio... ya es un documento legítimo emitido por una cámara de comercio" - Martín Nicholls

**Required behavior:**
- Download Cámara de Comercio directly from official source
- Compare client-submitted version against official version
- Flag any discrepancies as CRITICAL

**Note:** This requires integration with RUES (Registro Único Empresarial y Social) or Confecámaras API.

### 3.6 Improved Severity Classification

**Current Problem:** All formatting differences flagged as CRITICAL, causing alert fatigue.

**Required Severity Matrix:**

| Issue Type | Severity | Score Impact | Example |
|------------|----------|--------------|---------|
| Different company name (after normalization) | CRITICAL | +25 | "ROCSA" vs "AZELIS" |
| Different NIT base digits | CRITICAL | +25 | "900123456" vs "900654321" |
| Different NIT check digit | HIGH | +15 | "-1" vs "-3" |
| Typosquatting detection | CRITICAL | +25 | `acelis.com.co` ≈ `azelis.com` |
| Legal representative mismatch | HIGH | +15 | Name or ID differs |
| Provider domain mismatch | HIGH | +15 | Unknown domain for known provider |
| Document manipulation detected | HIGH | +15 | Editable PDF layers |
| City formatting difference | NONE | 0 | "Tenjo" vs "Tenjo (Cundinamarca)" |
| Company name formatting difference | NONE | 0 | "S.A.S." vs "SAS" |
| NIT formatting difference | NONE | 0 | "830.027.231-3" vs "830027231-3" |

---

## 4. Implementation Requirements

### 4.1 Backend Changes

#### Files to Modify:

1. **`backend/src/core/servicios/risk/cross_validation_service.py`**
   - Add normalization functions
   - Improve company name comparison
   - Improve NIT comparison
   - Improve city comparison
   - Add typosquatting detection
   - Add provider domain validation

2. **`backend/src/core/servicios/risk/document_extraction_service.py`**
   - Add document integrity checks
   - Extract provider information from documents

3. **`backend/src/interface/risk_dtos.py`**
   - Add new validation types for typosquatting and provider validation
   - Update severity enum descriptions

4. **`backend/src/repositorio/risk_repository.py`**
   - Add storage for known provider domains (new table or config)

#### New Files:

1. **`backend/src/core/servicios/risk/normalization_service.py`**
   - Centralized normalization functions
   - Unit testable in isolation

2. **`backend/src/core/servicios/risk/typosquatting_service.py`**
   - Typosquatting detection logic
   - Known domains database

3. **`backend/database/migration_add_known_providers.sql`**
   - Table for storing legitimate provider domains

### 4.2 Frontend Changes

#### Files to Modify:

1. **`frontend/src/types/risk.ts`**
   - Add new validation types
   - Update type definitions

2. **`frontend/src/pages/risk/RiskEvaluationDetail.tsx`**
   - Display new validation types appropriately
   - Highlight typosquatting warnings prominently

3. **Report generation (PDF export)**
   - Update to distinguish between real discrepancies and false positives
   - Add section for typosquatting warnings

### 4.3 Database Changes

```sql
-- New table for known provider domains
CREATE TABLE known_provider_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(255) NOT NULL,
    legitimate_domain VARCHAR(255) NOT NULL,
    added_by UUID REFERENCES auth.users(id),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(provider_name, legitimate_domain)
);

-- Seed with known providers
INSERT INTO known_provider_domains (provider_name, legitimate_domain) VALUES
('Azelis', 'azelis.com'),
('California Davis', 'californiadavis.com'),
('BASF', 'basf.com'),
('Dow', 'dow.com'),
('DuPont', 'dupont.com'),
('Evonik', 'evonik.com'),
('Lanxess', 'lanxess.com'),
('Brenntag', 'brenntag.com'),
('Univar', 'univarsolutions.com');

-- RLS policies
ALTER TABLE known_provider_domains ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Risk managers can manage known providers"
ON known_provider_domains
FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE user_profiles.user_id = auth.uid()
        AND user_profiles.role IN ('risk_manager', 'admin')
    )
);
```

---

## 5. Testing Requirements

### 5.1 Unit Tests

```python
# test_normalization.py

def test_company_name_normalization():
    """Same company with different formatting should normalize identically."""
    assert normalize_company_name("AZELIS COLOMBIA S.A.S.") == "AZELIS COLOMBIA"
    assert normalize_company_name("AZELIS COLOMBIA S A S") == "AZELIS COLOMBIA"
    assert normalize_company_name("Azelis Colombia SAS") == "AZELIS COLOMBIA"
    assert normalize_company_name("AZELIS COLOMBIA") == "AZELIS COLOMBIA"

def test_company_name_different():
    """Different companies should NOT normalize identically."""
    assert normalize_company_name("ROCSA COLOMBIA S.A.S.") != normalize_company_name("AZELIS COLOMBIA S.A.S.")

def test_nit_normalization():
    """Same NIT with different formatting should match."""
    assert nits_match("830.027.231-3", "830027231-3")[0] == True
    assert nits_match("830027231 3", "830.027.231-3")[0] == True

def test_nit_check_digit_mismatch():
    """Different check digits should NOT match."""
    match, reason = nits_match("830027231-1", "830027231-3")
    assert match == False
    assert "check digit" in reason.lower()

def test_city_normalization():
    """Same city with different formatting should normalize identically."""
    assert normalize_city("Tenjo") == normalize_city("Tenjo (Cundinamarca)")
    assert normalize_city("BOGOTÁ D.C.") == normalize_city("Bogota")

def test_typosquatting_detection():
    """Should detect typosquatting attempts."""
    result = detect_typosquatting("acelis.com.co")
    assert result is not None
    assert result['is_typosquatting'] == True
    assert result['legitimate_domain'] == 'azelis.com'

    result = detect_typosquatting("azelis.com")
    assert result is None  # Legitimate domain

def test_typosquatting_provider():
    """Should detect provider typosquatting."""
    result = detect_typosquatting("californiadavisinc.com")
    assert result is not None
    assert 'california' in result['legitimate_domain'].lower()
```

### 5.2 Integration Tests

```python
def test_cross_validation_no_false_positives():
    """Cross-validation should not flag formatting differences."""
    extractions = {
        DocumentType.RUT: {
            'company_name': 'AZELIS COLOMBIA S.A.S.',
            'nit': '830.027.231-3',
            'city': 'Tenjo'
        },
        DocumentType.CERTIFICADO_EXISTENCIA: {
            'company_name': 'AZELIS COLOMBIA S A S',
            'nit': '830027231-3',
            'city': 'Tenjo (Cundinamarca)'
        }
    }

    service = CrossValidationService()
    results = service.validate_documents(extractions)

    # Should NOT have discrepancies for formatting differences
    discrepancies = [r for r in results if r.is_discrepancy]
    assert len(discrepancies) == 0

def test_cross_validation_catches_real_fraud():
    """Cross-validation should catch real fraud indicators."""
    extractions = {
        DocumentType.RUT: {
            'company_name': 'AZELIS COLOMBIA S.A.S.',
            'nit': '830.027.231-3',
            'email': 'contacto@acelis.com.co'  # TYPOSQUATTING
        },
        DocumentType.CEDULA: {
            'full_name': 'DANIEL ABAD FAJARDO GONZALEZ',  # Different person
            'document_number': '79908064'
        },
        DocumentType.CERTIFICADO_EXISTENCIA: {
            'company_name': 'AZELIS COLOMBIA S.A.S.',
            'legal_representative_name': 'JAIME ALBERTO ROMERO',  # Different
            'legal_representative_id': '6135391'  # Different
        }
    }

    service = CrossValidationService()
    results = service.validate_documents(extractions)

    discrepancies = [r for r in results if r.is_discrepancy]

    # Should catch: typosquatting, legal rep name mismatch, legal rep ID mismatch
    assert len(discrepancies) >= 2

    # Should have typosquatting warning
    typosquatting = [r for r in discrepancies if 'typosquatting' in r.description.lower()]
    assert len(typosquatting) >= 1
```

### 5.3 E2E Test Scenario

Create `.claude/commands/e2e/test_cross_validation_false_positives.md`:

```markdown
# E2E Test: Cross-Validation False Positive Prevention

## Objective
Validate that the cross-validation system does NOT generate false positives for formatting differences.

## Prerequisites
- User logged in with `risk_analyst` role
- Test client with NIT exists in system

## Test Steps

### Step 1: Create Risk Evaluation
1. Navigate to `/risk/dashboard`
2. Click "Nueva Evaluación"
3. Enter test NIT
4. Submit evaluation

### Step 2: Upload Documents with Formatting Variations
Upload documents where the SAME information has different formatting:
- RUT: Company name "AZELIS COLOMBIA S.A.S.", NIT "830.027.231-3"
- Certificado: Company name "AZELIS COLOMBIA SAS", NIT "830027231-3"
- Cédula: Same legal representative

### Step 3: Run Cross-Validation
1. Click "Ejecutar Validación Cruzada"
2. Wait for processing

### Step 4: Verify Results
**Expected:**
- NO discrepancies for company name (same after normalization)
- NO discrepancies for NIT (same after normalization)
- Report shows "Validaciones Exitosas" for these fields

**Screenshot:** Capture validation results showing no false positives
```

---

## 6. Acceptance Criteria

### 6.1 False Positive Elimination

- [ ] Company name "AZELIS COLOMBIA S.A.S." equals "AZELIS COLOMBIA S A S" (no discrepancy)
- [ ] NIT "830.027.231-3" equals "830027231-3" (no discrepancy)
- [ ] City "Tenjo" equals "Tenjo (Cundinamarca)" (no discrepancy)
- [ ] False positive rate < 10% (down from ~60%)

### 6.2 Real Fraud Detection

- [ ] Typosquatting detected: `acelis.com.co` flagged as similar to `azelis.com`
- [ ] Legal representative mismatch detected when names differ
- [ ] NIT check digit mismatch detected (-1 vs -3)
- [ ] Provider domain validation warns when email domain doesn't match known provider

### 6.3 Report Quality

- [ ] Report clearly distinguishes between CRITICAL issues and formatting noise
- [ ] Typosquatting warnings displayed prominently
- [ ] Score impact reflects actual risk (not formatting differences)

---

## 7. Priority and Sequencing

### Phase 1: Critical Fixes (High Priority)
1. Implement data normalization (eliminates false positives)
2. Fix company name comparison
3. Fix NIT comparison
4. Fix city comparison

### Phase 2: Missing Detection (High Priority)
1. Add typosquatting detection
2. Add provider domain validation
3. Update severity classification

### Phase 3: Advanced Features (Medium Priority)
1. Document integrity checks (PDF manipulation detection)
2. Authoritative source validation (Cámara de Comercio download)
3. Known providers database management UI

---

## 8. References

### Source Documents
- Meeting transcript: `Requirements_Meetings/Fraud Protection/-Azelis-Inconsistencias-documentos-para-idear-controles-2c38b315-54d4.md`
- Meeting transcript: `Requirements_Meetings/Fraud Protection/Revisi-n-Tech-fraude-Azelis-47ca96d8-adaa.md`
- Sample report: `Example Files for Reqs/validacion_cruzada_RISK-2025-003_2025-12-22 (2).pdf`

### Existing Implementation
- Cross-validation service: `backend/src/core/servicios/risk/cross_validation_service.py`
- Risk scoring service: `backend/src/core/servicios/risk/risk_scoring_service.py`
- Fraud detection service: `backend/src/core/servicios/risk/fraud_detection_service.py`
- Risk types: `frontend/src/types/risk.ts`
- Risk service: `frontend/src/services/riskService.ts`

### Documentation
- Module documentation: `ai_docs/FRAUD_DETECTION_RISK_MODULE.md`

---

## 9. Feature Request Summary (For /feature Command)

**Title:** Fraud Detection Cross-Validation Improvements - Reduce False Positives and Add Typosquatting Detection

**Description:**
Improve the fraud detection cross-validation system to:
1. Eliminate false positives caused by formatting differences (company name, NIT, city)
2. Add typosquatting detection for email domains (e.g., `acelis.com.co` vs `azelis.com`)
3. Add provider domain validation
4. Update severity classification to reflect actual risk

**User Story:**
As a risk_analyst or risk_manager,
I want the cross-validation report to only show REAL discrepancies (not formatting differences),
So that I can focus on actual fraud indicators without alert fatigue.

**Problem Statement:**
The current cross-validation system has a ~60% false positive rate, flagging formatting differences (e.g., "S.A.S." vs "SAS") as CRITICAL discrepancies. This causes alert fatigue and buries real fraud indicators. Additionally, the system missed the actual fraud pattern in the Azelis case (email typosquatting).

**Solution Statement:**
1. Implement robust data normalization before comparison
2. Add typosquatting detection using string similarity algorithms
3. Add provider domain validation against known legitimate domains
4. Update severity classification to only flag semantically different data as discrepancies

---

*Document prepared for input to `/feature` command for implementation planning.*
