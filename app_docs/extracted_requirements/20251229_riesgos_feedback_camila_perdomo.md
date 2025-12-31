# Riesgos Module - Extracted Requirements

**Source:** Feedback Meeting with Camila Perdomo (Mesa de Control)
**Date:** December 29, 2025
**Transcript:** `Requirements_Meetings/Fraud Protection/Feedback Meetings/20251229 Feedback Camila Perdomo.txt`

---

## Summary

Meeting between Camila Perdomo (Mesa de Control) and Daniel Restrepo to review the fraud risk module after initial testing. The team identified bugs, enhancement requests, and process improvements.

---

## Bugs Identified

### BUG-001: Email Domain Extraction Errors

**Priority:** High
**Status:** Reported

**Description:**
The AI extraction is making character-level mistakes when extracting email domains from documents.

**Cases Reported:**
1. **Client: multivalsas** - Email multivazas@hotmail.com" was extracted with "Z" instead of "S"
2. **Client: Super Láminas Bogotá** - Company suffix "LTDA" was extracted as "LTD" (missing "A")

**Impact:**
- False positives in typosquatting detection
- Incorrect discrepancy alerts
- User confusion about validation results

**Action Required:**
- Review LandingAI extraction accuracy for email domains
- Investigate if OCR quality or document resolution is affecting extraction
- Consider post-processing normalization for common suffixes (LTDA, SAS, SA, etc.)

**Test Data:**
- Camila will provide document packages for both cases

---

## Enhancement Requests

### ENH-001: Individual Discrepancy Validation Checkboxes

**Priority:** High
**Status:** New Request

**Description:**
When discrepancies are found, Mesa de Control needs to validate them individually and mark each as reviewed. Currently, there's only a general "confirm reviewed" option.

**Current Behavior:**
- Shows "Confirme que revisó las discrepancias" (Confirm you reviewed the discrepancies)
- No ability to select/check individual discrepancies
- PDF report shows "Fallido, requiere revisión" even after manual validation

**Requested Behavior:**
- Display each discrepancy with a checkbox
- Allow user to mark each discrepancy as validated with a reason:
  - "Se validó manualmente" (Manually validated)
  - "Se verificó que el correo está correcto" (Verified email is correct)
  - "Se cargó erradamente" (Uploaded incorrectly) - for financial statement swap
- Update PDF report to show:
  - "Validado por Mesa de Control" instead of "Fallido, requiere revisión"
  - List which discrepancies were found and how they were resolved

**Example Flow:**
```
Discrepancy 1: Email gratuito (Hotmail)
  [ ] Validado - Reason: "Se verificó antigüedad y está registrado correctamente"

Discrepancy 2: Estados financieros año incorrecto
  [ ] Validado - Reason: "Se cargó erradamente, corregido"
```

**Acceptance Criteria:**
- [ ] Each discrepancy can be individually checked/validated
- [ ] Validation reason can be entered per discrepancy
- [ ] PDF export reflects validation status and reasons
- [ ] Final status changes from "requires_manual_verification" to "validated_by_mesa_control"

---

### ENH-002: Contador/Revisor Fiscal Cross-Validation

**Priority:** Medium
**Status:** New Request

**Description:**
Add cross-validation between the accountant (contador) or fiscal auditor (revisor fiscal) who signs the financial statements and those registered in official documents.

**Validation Logic:**
1. Extract contador/revisor fiscal from:
   - Cámara de Comercio (Chamber of Commerce certificate)
   - RUT (Tax registry)
2. Extract signatories from Estados Financieros (Financial Statements)
3. Cross-validate that the person who signed the financial statements is registered in official documents

**Expected Output:**
- Match: Green indicator showing contador/revisor fiscal verified
- Mismatch: Alert showing discrepancy between signatory and registered person

**Data Points to Extract:**
- Contador name from Cámara de Comercio
- Contador/Revisor Fiscal name from RUT
- Signatory names from Financial Statements footer/signature block

---

### ENH-003: Representative Signature Validation in Financial Statements

**Priority:** Medium
**Status:** New Request

**Description:**
Validate that the legal representative who signs financial statements matches the representative registered in official documents.

**Validation Logic:**
1. Extract representante legal from Cámara de Comercio and RUT
2. Extract signatory (representative) from Estados Financieros
3. Confirm match between registered representative and financial statement signatory

**Expected Output:**
- Positive indicator (green) when representative is verified in financial statements
- Alert when representative in financial statements doesn't match registered representative

---

### ENH-004: Remove External Contacts Tab for Mesa de Control Workflow

**Priority:** Low
**Status:** Discussion

**Description:**
Mesa de Control doesn't use the "Contactos Externos" (External Contacts) section because:
- They don't have direct contact with clients
- Email validation is already done through document extraction
- Manual email entry just validates against already-extracted data (redundant)

**Recommendation:**
- Consider hiding or deprioritizing this section for Mesa de Control role
- Keep it for Commercial team use case (see Process Improvement below)

---

## Process Improvements

### PROC-001: Email Chain Validation in Credit Committee Workflow

**Priority:** High
**Status:** Proposed

**Description:**
Proposal to integrate email chain validation into the credit committee approval process.

**Proposed Workflow:**
1. Commercial team contacts client (initial contact via WhatsApp is OK)
2. Commercial formalizes communication via email:
   - "Según lo hablado por WhatsApp, te comparto por correo esto, agradecemos tu confirmación"
3. Commercial exports email thread as PDF
4. Before credit committee, Commercial shares PDF with Mesa de Control
5. Mesa de Control uploads PDF to Riesgos module for validation
6. If discrepancies found → Commercial validates with client → Mesa de Control decides
7. Credit committee receives validation report

**Benefits:**
- Early fraud detection (before onboarding is complete)
- Catches domain spoofing like Azelis case (acelis.com.co vs azelis.com)
- Forces formalization of client communication
- Creates audit trail of validated communications

**Stakeholder Actions Required:**
- [ ] Discuss with Andrés (Mesa de Control lead)
- [ ] Present to Commercial team
- [ ] Define when in workflow validation should occur (first operation vs onboarding)

---

### PROC-002: First Operation Email Validation

**Priority:** Medium
**Status:** Proposed

**Description:**
Special handling for first operations to ensure email domain validation is completed.

**Concern Raised:**
- Clients using free email providers (Hotmail, Gmail) are harder to validate
- First operations are most vulnerable to fraud

**Proposed Solution:**
- Make email chain upload mandatory for first operations
- Flag operations where client uses free email domain
- Require additional validation steps for free email domains

---

## Notes from Discussion

### Azelis Case Reference
- Documents (RUT, Cámara de Comercio) were legitimate
- Fraud detected through email communication
- Spoofer used "acelis.com.co" instead of official "azelis.com"
- Domain had only 42 days of existence (red flag)
- Current module would have caught this via email chain validation

### Positive Feedback
- Domain age validation feature is very useful
- Cross-validation between documents works well when documents are correct
- Module is seen as valuable by the team

### Files to be Provided
Camila will send document packages for:
- Rutibalsas case (email domain extraction error)
- Super Láminas Bogotá case (LTDA vs LTD extraction error)

---

## Action Items

| ID | Action | Owner | Status |
|----|--------|-------|--------|
| 1 | Send document packages for bug cases | Camila | Pending |
| 2 | Review extraction accuracy issues | Daniel | Pending |
| 3 | Design discrepancy checkbox UI | Daniel | Pending |
| 4 | Discuss process with Andrés | Camila | Pending |
| 5 | Present email validation workflow to Commercial | TBD | Pending |
| 6 | Add contador/revisor fiscal extraction | Daniel | Pending |

---

## Priority Matrix

| Requirement | Business Value | Effort | Priority |
|-------------|---------------|--------|----------|
| BUG-001: Extraction errors | High | Medium | P1 |
| ENH-001: Discrepancy checkboxes | High | Medium | P1 |
| ENH-002: Contador validation | Medium | High | P2 |
| ENH-003: Representative validation | Medium | Medium | P2 |
| PROC-001: Email chain workflow | High | Low (process) | P1 |
