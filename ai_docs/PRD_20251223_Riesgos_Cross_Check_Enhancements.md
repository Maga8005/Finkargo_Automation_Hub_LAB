# PRD: Riesgos Cross-Check Enhancements

**Document ID:** PRD-20251223-RISK-CROSSCHECK
**Version:** 1.0
**Date:** December 23, 2025
**Source:** Meeting Transcript - Cross Check Riesgos (Andrés Ferrer / Daniel Restrepo)
**Status:** Requirements Captured

---

## Executive Summary

This document captures new feature requirements for the **Fraud Detection & Risk Management Module** (Riesgos) based on a meeting between Andrés Ferrer (stakeholder) and Daniel Restrepo (tech lead) on December 23, 2025. The meeting reviewed the current cross-validation functionality and identified enhancements needed to improve fraud detection.

**Key Decisions:**
1. **Binary Pass/Fail** - Replace scoring system with pass/fail (any discrepancy = manual review required)
2. **Email Correlation Tab** - Add ability to input and validate email/contact information
3. **Email Chain Upload** - Allow uploading email threads as additional validation source
4. **Document Manipulation Detection** - Add PDF metadata analysis
5. **Domain Validation** - Validate email domains including multi-TLD support

---

## 1. Current State (As Demonstrated)

### 1.1 What's Working

Daniel demonstrated the current Riesgos module functionality:

| Feature | Status | Notes |
|---------|--------|-------|
| Create evaluation by NIT | ✅ Working | User enters NIT to start evaluation |
| Document upload | ✅ Working | Estados financieros, RUT, Cédula, Certificado Existencia |
| AI Data Extraction | ✅ Working | Extracts NIT, representante legal, composición accionaria |
| Cross-validation | ✅ Working | Compares extracted data between documents |
| PDF Report Export | ✅ Working | Exportable validation report |
| Discrepancy Display | ✅ Working | Color-coded UI for inconsistencies |

### 1.2 Current Documents Supported

| Document Type | Key Fields Extracted |
|--------------|---------------------|
| Estados Financieros | NIT, año fiscal, auditor, compañía, representante legal |
| RUT | NIT, información tributaria |
| Cédula | Número de cédula, nombre completo |
| Certificado de Existencia y Representación Legal | Compañía, representante legal, composición accionaria |
| Composición Accionaria | Shareholders, porcentajes |

### 1.3 Issues Identified

| Issue | Impact | Quote from Meeting |
|-------|--------|-------------------|
| False positives | High noise ratio | "me decía que este NIT era distinto que este cuando no es o que representante legal no era, lo que pasa es que es uno suplente" |
| Scoring creates ambiguity | Users ignore warnings | "después alguien dice, no, pero eso dio 90 puntos y yo lo pasé" |
| Missing email validation | Missed fraud patterns | "ponerle pon la información de la... el correo electrónico listo, ya de una vez habíamos encontrado una inconsistencia" |

---

## 2. New Feature Requirements

### 2.1 CRITICAL: Binary Pass/Fail System (Replace Scoring)

**Stakeholder Request (Andrés Ferrer):**
> "Yo no le metería puntaje, yo le diría todo o nada, entonces o todo concuerda o no, o si hay un error yo así está rojo, verificación manual. OK, sí, sí, aquí no hay, aquí mejor dicho, yo no quiero que le diga qué tan, porque después alguien dice, no, pero eso dio 90 puntos y yo lo pasé. No, no, esto si da rojos, hay alguna información que no coincida, hay que ir a mirar y verificar manualmente."

**Current Behavior:**
- Risk score 0-100 with weighted algorithm
- Risk levels: LOW (0-30), MEDIUM (31-60), HIGH (61-80), CRITICAL (81-100)
- Users can justify passing high-score evaluations

**Required Behavior:**
- **Binary outcome ONLY:** ✅ PASS or ❌ REQUIRES MANUAL VERIFICATION
- ANY discrepancy detected → ❌ REQUIRES MANUAL VERIFICATION
- NO numeric score displayed to users
- Color coding: GREEN (all consistent) or RED (any inconsistency found)

**Implementation Notes:**
- Keep underlying score calculation for internal analytics/audit
- UI should NOT show numeric scores to end users
- Replace score display with simple pass/fail indicator
- Red flag requires acknowledgment before proceeding

### 2.2 HIGH: Email/Contact Information Correlation Tab

**Stakeholder Request (Daniel Restrepo):**
> "Lo otro es como otra información de, no sé cómo llamarle, el tab, otra información de contacto para correlacionar."

**Feature Description:**
Add a new tab in the evaluation detail page where users can input the email address/contact information received from the client through commercial channels.

**Workflow:**
1. Mesa de Control receives documents from commercial team via email
2. User creates risk evaluation in system
3. User uploads client documents
4. **NEW:** User inputs the sender's email address in new "Contacto Externo" tab
5. System cross-validates email domain against documents
6. Flags inconsistency if email domain doesn't match company domain in documents

**Example (from Azelis fraud case):**
- Documents show company: AZELIS COLOMBIA S.A.S.
- Expected email domain: `azelis.com`
- Actual email received from: `acelis.com.co`
- **Result:** ❌ REQUIRES MANUAL VERIFICATION - domain mismatch detected

**UI Mockup:**
```
Tabs: [Documentos] [Extracciones] [Validación Cruzada] [Contacto Externo] (NEW)

Contacto Externo Tab:
┌─────────────────────────────────────────────────────────────┐
│ Información de Contacto para Validación                      │
├─────────────────────────────────────────────────────────────┤
│ Correo Electrónico del Remitente:                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ contacto@acelis.com.co                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ [Validar Dominio]                                           │
│                                                              │
│ ⚠️ ALERTA: Dominio 'acelis.com.co' es 85% similar a         │
│    'azelis.com' (dominio legítimo conocido)                 │
│    POSIBLE TYPOSQUATTING DETECTADO                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 HIGH: Email Chain/Thread Upload

**Stakeholder Request (Andrés Ferrer):**
> "El texto del correo. Yo no sé si sea posible porque eso generalmente son una o dos cadenas de correos que suceden en donde uno puede entrar y correlacionar información que hay, que se equivoquen en el nombre de la compañía, que se equivoquen en escriban mal el NIT, que el representante legal no coincida con lo que está diciendo el documento."

**Feature Description:**
Allow users to upload email chain exports (.eml, .msg, or copy-paste text) as an additional data source for cross-validation.

**Data to Extract from Email:**
- Sender email domain
- Company name mentioned in email body
- NIT mentioned in email body
- Representative name mentioned
- Provider/supplier names mentioned

**Cross-Validation Rules:**
| Email Field | Compare Against | Flag If |
|-------------|-----------------|---------|
| Sender domain | Document company domain | Different or typosquatting |
| Company name in body | Company name in documents | Different (after normalization) |
| NIT in body | NIT in documents | Different |
| Rep name in body | Rep name in documents | Different |

**Implementation:**
```python
# New document type
class DocumentType(str, Enum):
    # ... existing types ...
    EMAIL_CHAIN = "email_chain"  # NEW

# Email extraction fields
EMAIL_EXTRACTION_FIELDS = {
    'sender_email': str,
    'sender_domain': str,
    'company_names_mentioned': List[str],
    'nits_mentioned': List[str],
    'representative_names_mentioned': List[str],
    'provider_names_mentioned': List[str],
}
```

### 2.4 MEDIUM: Domain Validation with Multi-TLD Support

**Stakeholder Request (Andrés Ferrer):**
> "Es que esa, por ejemplo, esa pasa muy rápido, esa pasa muy fácil porque uno puede tener los dos dominios, por ejemplo, como finkargo, en finkargo tenemos com co mx, tenemos todos los dominios."

**Feature Description:**
Enhance domain validation to recognize that legitimate companies may have multiple TLD variants of the same domain.

**Current Behavior:**
- Only checks if domain is in known legitimate list
- `azelis.com.co` vs `azelis.com` might be flagged incorrectly

**Required Behavior:**
- Recognize that `azelis.com`, `azelis.com.co`, `azelis.mx` are all potentially legitimate for same company
- Still flag typosquatting: `acelis.com.co` (different base) vs `azelis.com`
- Alert when domain variant differs but base matches (informational, not blocking)

**Implementation:**
```python
def validate_domain_relationship(domain1: str, domain2: str) -> dict:
    """
    Compare two domains accounting for multi-TLD companies.

    Returns:
        {
            'status': 'match' | 'variant' | 'suspicious' | 'different',
            'base_match': bool,
            'message': str
        }
    """
    base1 = extract_domain_base(domain1)  # azelis.com.co -> azelis
    base2 = extract_domain_base(domain2)  # azelis.com -> azelis

    if base1 == base2:
        if domain1 == domain2:
            return {'status': 'match', 'base_match': True, 'message': 'Dominios idénticos'}
        else:
            return {'status': 'variant', 'base_match': True,
                    'message': f'Variante de TLD: {domain1} vs {domain2} - verificar si ambos pertenecen a la empresa'}

    # Check for typosquatting
    similarity = calculate_similarity(base1, base2)
    if similarity > 0.70:
        return {'status': 'suspicious', 'base_match': False,
                'message': f'POSIBLE TYPOSQUATTING: {domain1} es {similarity*100:.0f}% similar a {domain2}'}

    return {'status': 'different', 'base_match': False,
            'message': f'Dominios diferentes: {domain1} vs {domain2}'}
```

### 2.5 MEDIUM: Document Manipulation Detection (PDF Metadata)

**Stakeholder Request (Daniel Restrepo):**
> "Lo siguiente que le estaba trabajando para meterle era alguna forma de identificar si el documento ha sido manipulado, la metadata del documento, entonces extraemos la información, pero también validar la metadata y con eso entonces ya podemos ver documentos que han sido manipulados recientemente de algún modo."

**Feature Description:**
Analyze PDF metadata and structure to detect signs of manipulation.

**Checks to Implement:**
| Check | Flag Condition | Severity |
|-------|---------------|----------|
| PDF editing software in creator/producer | Adobe Acrobat Pro, PDFsam, iLovePDF, etc. | Medium |
| Recent modification date | Modified within last 7 days of upload | Low |
| Editable form fields present | Any fillable fields detected | Medium |
| Annotation overlays | FreeText, shapes overlaying content | High |
| Multiple page creation dates | Pages created at different times | Medium |
| Font inconsistencies | Multiple fonts unusual for document type | Low |

**Implementation:**
```python
def analyze_pdf_metadata(pdf_content: bytes) -> dict:
    """
    Analyze PDF for manipulation indicators.

    Returns:
        {
            'manipulation_indicators': List[str],
            'metadata': {
                'creator': str,
                'producer': str,
                'creation_date': datetime,
                'modification_date': datetime,
            },
            'has_editable_elements': bool,
            'has_overlays': bool,
            'overall_risk': 'low' | 'medium' | 'high'
        }
    """
```

### 2.6 LOW: Two-Module Architecture (Future)

**Stakeholder Discussion (Daniel Restrepo):**
> "Yo creo que hay dos módulos, este es el primero, este es a nivel línea, a nivel cliente y está a nivel operación, que está la validación del proveedor, certificado bancario, todo ese tipo de cosas."

**Architecture Vision:**

| Module | Level | Documents | Use Case |
|--------|-------|-----------|----------|
| Module 1 (Current) | Client/Line | Estados financieros, RUT, Cédula, Certificado Existencia | Credit line approval |
| Module 2 (Future) | Operation | Certificado bancario, Factura proveedor, Proforma | Per-operation validation |

**Future Work:**
- Operation-level validation for each disbursement
- Provider/supplier document validation
- Bank certificate cross-validation
- Invoice authenticity verification

---

## 3. Workflow Integration

### 3.1 Target User: Mesa de Control

**Stakeholder Request (Andrés Ferrer):**
> "Yo creo que el que tiene que tener acceso a esto es Mesa de Control antes de mandar el giro a tesorería, simplemente subo acá los documentos y correlacionamos la información. Antes de mandar el giro a tesorería, que es en el momento que ya tenemos todos los documentos supuestamente firmados."

**Workflow Position:**
```
Commercial Team     →    Mesa de Control    →    Tesorería
(Receives docs)          (Validates via        (Processes
                          Cross-Check)          payment)
                              ↑
                         Risk Module
                         Cross-Check
```

**Integration Requirements:**
1. Mesa de Control role must have access to Risk module
2. Cross-check should be part of pre-payment checklist
3. Validation result should be attached to payment authorization

### 3.2 Temporary Manual Process

**Agreed Approach (Daniel Restrepo):**
> "Entonces lo que yo puedo hacer es montamos este proceso alterno como parte del checklist, que haga no sé qué equipo y que lo tenga en cuenta por ahora mientras montamos algo en plataforma."

**Short-term Process:**
1. Cross-check tool available as standalone validation
2. Mesa de Control manually runs validation before payment
3. Screenshot/export of validation result attached to payment request
4. Future: Integrate into payment approval workflow

---

## 4. False Positive Handling

### 4.1 Known False Positive Patterns

**Issue (Daniel Restrepo):**
> "Los falsos positivos nos dañan todo... me decía que este NIT era distinto que este cuando no es o que representante legal no era, lo que pasa es que es uno suplente."

**False Positive Scenarios to Handle:**

| Scenario | Current Behavior | Required Behavior |
|----------|-----------------|-------------------|
| NIT formatting | "830.027.231-3" ≠ "830027231-3" flagged | Normalize before compare |
| Company suffix | "S.A.S." ≠ "SAS" flagged | Normalize legal suffixes |
| Representante suplente | Different name flagged | Accept if listed as suplente in Certificado |
| City formatting | "Bogotá D.C." ≠ "Bogota" flagged | Normalize city names |

### 4.2 Multiple Representantes Legales

**Issue:** Documents may list principal + suplente representatives, causing false mismatches.

**Solution:**
- Extract ALL representantes legales from Certificado Existencia
- Accept match if name matches ANY listed representative
- Flag as informational if matching suplente (not principal)

```python
def compare_legal_representatives(
    name_from_doc: str,
    representatives_from_certificado: List[dict]  # [{name, type: 'principal'|'suplente'}]
) -> dict:
    """
    Check if name matches any legal representative.
    """
    for rep in representatives_from_certificado:
        if normalize_name(name_from_doc) == normalize_name(rep['name']):
            return {
                'match': True,
                'matched_type': rep['type'],
                'flag': 'info' if rep['type'] == 'suplente' else None
            }
    return {'match': False, 'flag': 'discrepancy'}
```

---

## 5. UI/UX Requirements

### 5.1 Pass/Fail Display

**Replace score display with:**
```
┌─────────────────────────────────────────┐
│           RESULTADO VALIDACIÓN           │
├─────────────────────────────────────────┤
│                                          │
│    ✅ VALIDACIÓN EXITOSA                 │
│    Toda la información es consistente    │
│                                          │
└─────────────────────────────────────────┘

OR

┌─────────────────────────────────────────┐
│           RESULTADO VALIDACIÓN           │
├─────────────────────────────────────────┤
│                                          │
│    ❌ REQUIERE VERIFICACIÓN MANUAL       │
│    Se encontraron inconsistencias        │
│                                          │
│    Ver detalles abajo ↓                  │
└─────────────────────────────────────────┘
```

### 5.2 Discrepancy Detail Display

**Keep existing color-coded detail view:**
- RED: Critical inconsistency (different data)
- YELLOW: Warning (informational, e.g., suplente match)
- GREEN: Consistent

### 5.3 Report Export

**Stakeholder Feedback (Andrés Ferrer):**
> "De color y demás, está cheverísimo, está muy bacán."
>
> (Daniel): "Y te da un reportico que puedes exportar."

**Keep PDF export with:**
- Binary pass/fail header
- Detailed discrepancy list
- Document-by-document comparison
- Timestamp and evaluator info

---

## 6. Priority and Sequencing

### Phase 1: Quick Wins (Immediate)

| Feature | Effort | Impact | Notes |
|---------|--------|--------|-------|
| Binary Pass/Fail UI | Low | High | Hide score, show pass/fail |
| Email Input Tab | Medium | High | Single email field + domain validation |
| False positive fixes | Medium | High | Already in PRD-20251222 |

### Phase 2: Enhanced Validation (Short-term)

| Feature | Effort | Impact | Notes |
|---------|--------|--------|-------|
| Email chain upload | High | Medium | Text extraction + cross-validation |
| Multi-TLD domain support | Medium | Medium | Domain variant handling |
| Multiple rep support | Medium | Medium | Handle suplente reps |

### Phase 3: Advanced Features (Medium-term)

| Feature | Effort | Impact | Notes |
|---------|--------|--------|-------|
| PDF metadata analysis | High | Medium | Manipulation detection |
| Operation-level module | High | High | Module 2 architecture |
| Workflow integration | High | High | Mesa de Control checklist |

---

## 7. Acceptance Criteria

### 7.1 Binary Pass/Fail

- [ ] Risk score NOT visible to end users
- [ ] Evaluation result shows only ✅ PASS or ❌ REQUIRES MANUAL VERIFICATION
- [ ] ANY discrepancy triggers manual verification requirement
- [ ] PDF export shows binary result (not numeric score)

### 7.2 Email Correlation

- [ ] New tab "Contacto Externo" available in evaluation detail
- [ ] User can input sender email address
- [ ] System validates domain against company domain from documents
- [ ] Typosquatting detection flags similar but different domains
- [ ] Multi-TLD variants handled correctly (informational, not blocking)

### 7.3 False Positive Reduction

- [ ] NIT formatting differences do not trigger discrepancy
- [ ] Company name suffix differences do not trigger discrepancy
- [ ] City formatting differences do not trigger discrepancy
- [ ] Suplente representative match is accepted (flagged as info)

---

## 8. Technical Implementation Notes

### 8.1 Backend Changes

**Files to Modify:**

| File | Changes |
|------|---------|
| `backend/src/interface/risk_dtos.py` | Add `ContactInfo` model, `EmailValidationResult` |
| `backend/src/adapter/rest/risk_routes.py` | Add `/evaluations/{id}/contact` endpoint |
| `backend/src/core/servicios/risk/cross_validation_service.py` | Add email domain validation, multi-TLD support |
| `backend/src/core/servicios/risk/fraud_detection_service.py` | Update to use binary pass/fail internally |

**New Files:**

| File | Purpose |
|------|---------|
| `backend/src/core/servicios/risk/email_validation_service.py` | Email/domain validation logic |
| `backend/src/core/servicios/risk/pdf_analysis_service.py` | PDF metadata analysis |

### 8.2 Frontend Changes

**Files to Modify:**

| File | Changes |
|------|---------|
| `frontend/src/types/risk.ts` | Add `ContactInfo`, `EmailValidationResult` types |
| `frontend/src/services/riskService.ts` | Add contact validation API calls |
| `frontend/src/pages/risk/RiskEvaluationDetail.tsx` | Add Contacto Externo tab, binary result display |
| `frontend/src/components/risk/FKRiskScoreCard.tsx` | Replace score with pass/fail |

**New Files:**

| File | Purpose |
|------|---------|
| `frontend/src/components/risk/FKContactValidation.tsx` | Contact info tab component |
| `frontend/src/components/risk/FKPassFailBadge.tsx` | Binary result display component |

### 8.3 Database Changes

```sql
-- Add contact validation results to assessments
ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS
    contact_validation JSONB;

-- Structure:
-- {
--   "email": "contacto@acelis.com.co",
--   "domain": "acelis.com.co",
--   "validation_result": "suspicious",
--   "similar_to": "azelis.com",
--   "similarity_percent": 85,
--   "validated_at": "2025-12-23T14:30:00Z"
-- }
```

---

## 9. References

### Source Meeting

- **Title:** Cross Check - Riesgos
- **Date:** December 23, 2025, 2:00 PM
- **Participants:** Andrés Ferrer, Daniel Restrepo
- **Transcript:** `Requirements_Meetings/Fraud Protection/-Cross-Check-Riesgos-Andr-s-Daniel-fd897b52-a2e2.pdf`

### Related Documents

- `ai_docs/FRAUD_DETECTION_RISK_MODULE.md` - Module documentation
- `ai_docs/PRD_20251222_Fraud_Detection_Cross_Validation_Improvements.md` - Previous improvements PRD
- `Requirements_Meetings/Fraud Protection/Revisi-n-Tech-fraude-Azelis-47ca96d8-adaa.md` - Azelis case analysis

### Current Implementation

- Routes: `backend/src/adapter/rest/risk_routes.py`
- Services: `backend/src/core/servicios/risk/`
- Frontend: `frontend/src/pages/risk/`, `frontend/src/components/risk/`

---

## 10. Feature Request Summary (For /feature Command)

**Title:** Riesgos Cross-Check Enhancements - Binary Pass/Fail and Email Validation

**Description:**
Enhance the fraud detection cross-validation system with:
1. Binary pass/fail result (replace numeric scoring)
2. Email/contact information validation tab
3. Multi-TLD domain variant support
4. Improved false positive handling

**User Story:**
As Mesa de Control,
I want to validate client documents with a clear pass/fail result and email domain verification,
So that I can confidently authorize payments without ambiguity about risk assessment.

**Problem Statement:**
Current scoring system (0-100) creates ambiguity where users justify passing evaluations with high scores. Additionally, email domain validation is missing, which was a key fraud indicator in the Azelis case.

**Solution Statement:**
1. Replace numeric score display with binary pass/fail
2. Add email input tab with domain validation against documents
3. Implement typosquatting detection for email domains
4. Handle multi-TLD company domains correctly

---

*Document prepared from meeting transcript analysis - December 23, 2025*
