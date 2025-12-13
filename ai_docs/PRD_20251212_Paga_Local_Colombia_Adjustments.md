# PRD: Paga Local Colombia - Adjustments and Commercial Team Rollout

**Document Version:** 1.0
**Date:** 2024-12-12
**Source:** Transcript from meeting with Sofia Tobón (Legal Analyst)
**Priority:** High
**Module:** Operations > Paga Local Colombia

---

## Executive Summary

This PRD documents adjustments required to the Paga Local Colombia module based on feedback from the Legal team. The changes focus on improving the Instrucción de Mandato document generation, enabling approved contract downloads, and preparing the system for Commercial team adoption with appropriate access controls.

---

## Background

The Paga Local Colombia module automates the generation of legal documents for domestic payment operations, including:
- **Contrato de Mandato** (Mandate Contract)
- **Instrucción de Mandato** (Mandate Instruction) - for DIAN and other creditors
- **Solicitud de Desembolso** (Disbursement Request)

The Legal team has been testing the module and identified several adjustments needed before rolling out to the Commercial team.

---

## Requirements

### REQ-001: Enable Word Document Download for Approved Contracts

**Priority:** High
**Complexity:** Low
**Affected Component:** `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`

**Current State:**
- The "Contratos Aprobados" (Approved Contracts) tab exists
- The "Acciones" (Actions) column is grayed out/disabled
- Users cannot download approved contracts

**Required Changes:**
1. Enable the download action button in the approved contracts table
2. Provide DOCX download (not PDF due to technical complexity)
3. Users download Word document, make any final edits, and convert to PDF manually if needed

**Acceptance Criteria:**
- [ ] Download button is enabled in "Contratos Aprobados" tab
- [ ] Clicking download retrieves the DOCX file
- [ ] File downloads with appropriate naming convention

---

### REQ-002: DIAN Checkbox for Instrucción de Mandato

**Priority:** High
**Complexity:** Medium
**Affected Components:**
- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`
- `backend/src/core/servicios/document_service.py`
- `backend/src/adapter/rest/operations_routes.py`

**Current State:**
- Two separate forms exist: one for DIAN creditors, one for generic creditors
- When a payment has both DIAN and non-DIAN creditors, users must manually combine documents
- Bank certificate upload is always required, even for DIAN payments

**Required Changes:**

1. **Add DIAN Checkbox per Creditor:**
   - Each creditor row should have a "Es DIAN" (Is DIAN) checkbox
   - When checked:
     - Auto-populate predefined DIAN wording
     - Bank certificate upload is NOT required for that creditor
   - When unchecked:
     - Bank certificate upload IS required
     - Extract data from uploaded certificate

2. **Support Multiple Creditors of Mixed Types:**
   - Allow adding multiple creditors (existing functionality)
   - Each creditor can independently be marked as DIAN or not
   - Generate single document containing all creditors with appropriate wording

3. **Fix Account Type Extraction:**
   - Currently showing "PC" when it should be "PSE" for DIAN payments
   - Correct the tipo_transferencia/tipo_cuenta field mapping

**User Flow:**
```
1. User uploads quotation PDF
2. System extracts creditor data
3. For each creditor:
   a. If DIAN → Check "Es DIAN" checkbox → Auto-fill DIAN wording
   b. If not DIAN → Upload bank certificate → Extract bank details
4. Generate unified Instrucción de Mandato with all creditors
```

**DIAN Wording (to be auto-populated):**
> "Transferencia electrónica PSE a favor de la DIAN"

**Acceptance Criteria:**
- [ ] Each creditor row has "Es DIAN" checkbox
- [ ] Checking DIAN disables bank certificate upload requirement for that creditor
- [ ] DIAN wording is auto-populated when checkbox is checked
- [ ] Multiple creditors (mixed DIAN/non-DIAN) supported in single document
- [ ] Account type correctly shows "PSE" for DIAN transfers

---

### REQ-003: Contract Iteration Number Input Field

**Priority:** Medium
**Complexity:** Low
**Affected Components:**
- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`
- `backend/src/adapter/rest/operations_routes.py`

**Current State:**
- Contract code is auto-generated with fixed iteration (always "1")
- Format: `CO.M[iteration].[type]DOM` (e.g., `CO.M2.DOM`)
- When credit limit (290M COP) is reached, new contract needed with incremented number

**Required Changes:**

1. **Add Contract Number Input Field:**
   - Add text/number input field labeled "Número de Contrato" or "Iteración del Contrato"
   - Default value: "1" or last known iteration
   - Commercial team inputs the contract iteration number provided by Mesa de Control

2. **Update Code Generation:**
   - Use the input value to generate correct contract code
   - Example: If user enters "3", code becomes `CO.M3.DOM`

**User Flow:**
```
1. Commercial receives contract iteration number from Mesa de Control
2. When creating contract, enters the number in new field
3. System generates documents with correct contract code
```

**Acceptance Criteria:**
- [ ] New input field for contract iteration number is visible
- [ ] Field accepts numeric values (1, 2, 3, etc.)
- [ ] Generated documents use the provided iteration number in contract code
- [ ] Default value is "1" if not specified

---

### REQ-004: Fix Quotation Extraction for Multiple Creditors

**Priority:** Medium
**Complexity:** Medium
**Affected Components:**
- `backend/src/core/servicios/cotizacion_parser_service.py`
- `backend/src/core/servicios/landingai_contract_parser_service.py`

**Current State:**
- When quotation contains multiple creditors (e.g., DIAN + freight agent), only DIAN is extracted
- Total amount shows only DIAN portion, not full quotation amount
- Example: 78M COP quotation showing as 71M COP (only DIAN portion)

**Required Changes:**

1. **Extract All Creditors from Quotation:**
   - Parse quotation PDF for all payment recipients
   - Extract amounts for each creditor
   - Calculate and display correct total amount

2. **Pre-populate Creditor Rows:**
   - Create a row for each extracted creditor
   - Auto-determine if creditor is DIAN based on name matching

**Investigation Needed:**
- Analyze quotation PDF format for multi-creditor scenarios
- Determine extraction patterns for non-DIAN creditors (freight agents, customs brokers, etc.)

**Acceptance Criteria:**
- [ ] All creditors are extracted from quotation PDF
- [ ] Correct total amount is displayed
- [ ] Each creditor appears as separate row in form
- [ ] DIAN creditors are auto-detected and checkbox pre-checked

---

### REQ-005: Granular Permissions for Commercial Team

**Priority:** High
**Complexity:** Medium
**Affected Components:**
- `backend/src/adapter/rest/rbac_dependencies.py`
- `frontend/src/App.tsx`
- `frontend/src/components/RoleProtectedRoute.tsx`
- Database: `user_profiles` table

**Current State:**
- Permissions are at module level (Operations module = all operations features)
- No way to restrict access to specific sub-features within a module
- Commercial would see both "Paga Local Colombia" AND "Contratos Activos" if given Operations access

**Required Changes:**

1. **Create New Role: `comercial_paga_local`:**
   - Access to: Paga Local Colombia (create contracts)
   - NO access to: Contratos Activos, other contract types
   - NO access to: Legal review queue (cannot approve own contracts)

2. **Implement Sub-Module Permissions:**
   - Add permission checks at route level for specific pages
   - Options:
     - a) New role specifically for Paga Local
     - b) Feature flags per role
     - c) Sub-module permission array in user profile

3. **Hide Unauthorized Menu Items:**
   - Commercial users should only see menu items they can access
   - "Contratos Activos" should not appear in sidebar for `comercial_paga_local` role

**Acceptance Criteria:**
- [ ] New role `comercial_paga_local` (or similar) created
- [ ] Users with this role can only access Paga Local Colombia
- [ ] Contratos Activos is hidden from unauthorized users
- [ ] Legal review features remain restricted to Legal team

---

### REQ-006: Phase 1 Workflow - Commercial Creates, Legal Reviews

**Priority:** High
**Complexity:** Low
**Affected Components:**
- Workflow documentation
- User training materials

**Current State:**
- Legal team generates and reviews contracts

**Phase 1 Workflow:**
1. Commercial team creates contract requests in Paga Local Colombia
2. Contracts appear in Legal review queue
3. Legal downloads DOCX, reviews, approves/rejects
4. Approved contracts available in "Contratos Aprobados" for download

**Communication:**
- Commercial notifies Legal via Slack channel "Domestic Payments" when contracts are ready for review
- No automated Slack notifications needed in Phase 1

**Phase 2 (Future - after 2 weeks of stability):**
- Evaluate removing Legal review step
- Commercial team fully autonomous

**Acceptance Criteria:**
- [ ] Commercial can create contracts
- [ ] Contracts appear in Legal review queue
- [ ] Legal can download, review, approve/reject
- [ ] Approved contracts downloadable from "Contratos Aprobados" tab

---

## Out of Scope

The following items were discussed but will NOT be included in this implementation:

1. **Date Field in Documents:**
   - Issue: Documents showing today's date instead of contract signing date
   - Resolution: Sofia will remove this field from the template directly
   - No code changes required

2. **Automated Slack Notifications:**
   - Not needed for Phase 1
   - Commercial will manually notify Legal via existing Slack channel

3. **PDF Export:**
   - Technical complexity too high
   - Users will download DOCX and convert manually

---

## Technical Implementation Notes

### Database Changes

```sql
-- Option A: Add new role
INSERT INTO user_roles (role_name, description)
VALUES ('comercial_paga_local', 'Commercial team - Paga Local access only');

-- Option B: Add feature permissions to user_profiles
ALTER TABLE user_profiles
ADD COLUMN feature_permissions JSONB DEFAULT '{}';

-- Example feature permissions structure:
-- {"paga_local_colombia": true, "contratos_activos": false}
```

### Frontend Route Protection

```typescript
// In App.tsx - granular route protection
<Route
  path="operations/paga-local-colombia"
  element={
    <RoleProtectedRoute
      allowedRoles={[UserRole.COMERCIAL_PAGA_LOCAL, UserRole.OPERATIONS, UserRole.ADMIN]}
    >
      <OperationsPagaLocalColombia />
    </RoleProtectedRoute>
  }
/>
```

### Backend DIAN Detection Logic

```python
# In operations_routes.py or document_service.py
DIAN_KEYWORDS = ["DIAN", "Dirección de Impuestos", "Aduanas Nacionales"]

def is_dian_creditor(creditor_name: str) -> bool:
    return any(keyword.lower() in creditor_name.lower() for keyword in DIAN_KEYWORDS)

DIAN_WORDING = "Transferencia electrónica PSE a favor de la DIAN"
```

---

## Dependencies

| Dependency | Description | Status |
|------------|-------------|--------|
| Updated DOCX Templates | Sofia to provide updated templates without date field | Pending (Sofia sending Saturday) |
| Test Quotation PDFs | Multi-creditor quotation examples | Pending (Sofia to send) |
| Bank Certificate Examples | For testing extraction | Pending (Sofia to send) |

---

## Rollout Plan

| Phase | Description | Timeline |
|-------|-------------|----------|
| Development | Implement REQ-001 through REQ-005 | By Monday afternoon |
| Testing | Legal team validates changes | Monday-Tuesday |
| Commercial Onboarding | Meeting with Martín and Juan Pablo González | Monday (scheduled) |
| User Creation | Create Commercial team user accounts | After onboarding meeting |
| Soft Launch | Commercial creates, Legal reviews (2 weeks) | Week of Dec 16 |
| Full Launch | Remove Legal review step (if stable) | End of December |

---

## Files to be Modified

### Frontend
- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`
- `frontend/src/App.tsx`
- `frontend/src/components/RoleProtectedRoute.tsx`
- `frontend/src/types/index.ts` (add new role)

### Backend
- `backend/src/adapter/rest/operations_routes.py`
- `backend/src/adapter/rest/rbac_dependencies.py`
- `backend/src/core/servicios/document_service.py`
- `backend/src/core/servicios/cotizacion_parser_service.py`

### Database
- Migration for new role or feature permissions

---

## Success Metrics

1. Commercial team can independently create Paga Local contracts
2. Legal review time reduced (no longer generating documents)
3. Zero access control violations (Commercial cannot access Activos)
4. Document generation accuracy maintained (DIAN wording correct, amounts correct)

---

## Appendix: Transcript Key Quotes

> "Los documentos de la operación, la instrucción de mandato y la solicitud desembolso están saliendo perfectos"
> - Sofia confirming core functionality works

> "A m me gustaría hacerlo por fases. Le sueltas a Comercial y Operaciones la parte de generarlo y tú verificas"
> - Daniel proposing phased rollout

> "A ellos solo se les vería habilitado paga local, que no se me vayan a emocionar sacando contratos de activos"
> - Sofia requesting restricted access

> "El contrato tiene un cupo de 290 millones de pesos. Cada que se cope ese cupo se tiene que hacer un nuevo contrato, cambia el código"
> - Sofia explaining contract iteration requirement

> "Cuando sea DIAN sea un checkbox, y ese checkbox trae el texto. De lo contrario, entonces hay que subir el certificado bancario"
> - Daniel confirming DIAN checkbox solution
