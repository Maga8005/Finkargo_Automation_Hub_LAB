# Implementation Prompts for Paga Local Colombia Adjustments

**PRD Reference:** `ai_docs/PRD_20251212_Paga_Local_Colombia_Adjustments.md`
**Date:** 2024-12-12

## Execution Order

Execute these prompts in order using the `/feature` slash command:

```
/feature <issue_number> <adw_id> '<issue_json>'
```

**Recommended Order:**
1. PROMPT-001: Enable Word Download (foundation)
2. PROMPT-002: Granular Permissions (foundation for Commercial rollout)
3. PROMPT-003: Contract Iteration Number Field (low complexity)
4. PROMPT-004: DIAN Checkbox Feature (medium complexity)
5. PROMPT-005: Multi-Creditor Quotation Extraction (medium complexity)

---

## PROMPT-001: Enable Word Document Download for Approved Contracts

**Issue Number:** 1
**ADW ID:** paga-local-001

```
/feature 1 paga-local-001 '{"title": "Enable Word Document Download for Approved Paga Local Contracts", "body": "## Context\nThe Paga Local Colombia module has a \"Contratos Aprobados\" (Approved Contracts) tab that displays approved contracts. Currently, the Actions column is grayed out and users cannot download the approved documents.\n\n## Current State\n- Approved contracts table exists in `OperationsPagaLocalColombia.tsx`\n- Actions column shows but button is disabled\n- No download functionality implemented for approved contracts\n\n## Requirements\n1. Enable the download action button in the approved contracts DataGrid\n2. Implement DOCX download (NOT PDF - PDF has technical issues)\n3. Download should retrieve the generated Word document from Supabase storage\n4. File should download with appropriate naming: `{contract_code}-{client_name}.docx`\n\n## Technical Notes\n- Documents are stored in Supabase storage after generation\n- Follow existing download patterns from standard contracts module\n- The `document_url` field contains the storage path\n\n## Acceptance Criteria\n- [ ] Download button is enabled and clickable in Contratos Aprobados tab\n- [ ] Clicking download retrieves the DOCX file from storage\n- [ ] File downloads with correct naming convention\n- [ ] Error handling for missing documents\n\n## Affected Files\n- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`\n- `frontend/src/services/operationsService.ts`\n- `backend/src/adapter/rest/operations_routes.py` (if new endpoint needed)"}'
```
(DONE)

---

## PROMPT-002: Granular Permissions for Commercial Team

**Issue Number:** 2
**ADW ID:** paga-local-002

```
/feature 2 paga-local-002 '{"title": "Implement Granular Permissions for Commercial Team - Paga Local Only Access", "body": "## Context\nThe Commercial team needs access to create Paga Local Colombia contracts, but they should NOT have access to other contract types like \"Contratos Activos\". Current permissions are at module level, which would grant access to all Operations features.\n\n## Current State\n- Permissions are role-based at module level\n- `operations` role grants access to entire Operations module\n- No sub-module level permission control exists\n- Commercial users would see both Paga Local and Activos if given Operations access\n\n## Requirements\n1. Create new role `comercial_paga_local` with limited access:\n   - CAN access: Paga Local Colombia (create contracts)\n   - CANNOT access: Contratos Activos, Contratos Mexico, other contract types\n   - CANNOT access: Legal review queue (cannot approve own contracts)\n\n2. Implement sub-module permission checks:\n   - Backend: Add role check in operations_routes.py for Paga Local endpoints\n   - Frontend: Filter menu items based on user role\n\n3. Update sidebar/navigation:\n   - Hide unauthorized menu items for `comercial_paga_local` role\n   - Only show \"Paga Local Colombia\" under Operations\n\n## Technical Approach\nOption A (Recommended): Add new role to existing RBAC system\n- Add `comercial_paga_local` to UserRole enum\n- Create new RBAC dependency `require_paga_local_role`\n- Update RoleProtectedRoute to handle new role\n\n## Database Changes\n```sql\n-- Add new role value to user_profiles role enum (if using enum)\n-- Or simply allow new role string in user_profiles.role column\n```\n\n## Acceptance Criteria\n- [ ] New `comercial_paga_local` role exists in system\n- [ ] Users with this role can access Paga Local Colombia page\n- [ ] Users with this role CANNOT access Contratos Activos\n- [ ] Users with this role CANNOT access Legal review features\n- [ ] Sidebar shows only authorized menu items\n- [ ] Backend endpoints properly restrict access by role\n\n## Affected Files\n- `frontend/src/types/index.ts` (UserRole enum)\n- `frontend/src/App.tsx` (route protection)\n- `frontend/src/components/ui/FKSidebar.tsx` (menu filtering)\n- `backend/src/adapter/rest/rbac_dependencies.py`\n- `backend/src/adapter/rest/operations_routes.py`\n- `backend/database/` (migration for new role if needed)"}'
```(DONE)

---

## PROMPT-003: Contract Iteration Number Input Field

**Issue Number:** 3
**ADW ID:** paga-local-003

```
/feature 3 paga-local-003 '{"title": "Add Contract Iteration Number Input Field for Paga Local Colombia", "body": "## Context\nPaga Local contracts have a credit limit of 290M COP. When this limit is reached, a new contract must be created with an incremented code. Currently, the contract code iteration is hardcoded to \"1\", but Commercial team needs to input the correct iteration number provided by Mesa de Control.\n\n## Current State\n- Contract code format: `CO:[NIT]:[ITERATION]:D:M:DOM` (e.g., `CO.M2.DOM`)\n- Iteration number is hardcoded in the template or defaults to 1\n- No UI field exists to input the iteration number\n- Mesa de Control tells Commercial which iteration to use\n\n## Requirements\n1. Add input field labeled \"Numero de Contrato\" or \"Iteracion del Contrato\":\n   - Field type: number input (positive integers only)\n   - Default value: 1\n   - Validation: required, min=1, max=99\n   - Position: In the contract request form, near client selection\n\n2. Update contract code generation:\n   - Use the input value in the contract code\n   - Example: If user enters \"3\", code becomes `CO:[NIT]:3:D:M:DOM `\n\n3. Pass iteration to backend:\n   - Include in contract generation request payload\n   - Store in contract record for reference\n\n## User Flow\n1. Commercial receives iteration number from Mesa de Control\n2. Opens Paga Local Colombia contract form\n3. Selects client, fills form\n4. Enters contract iteration number (e.g., \"2\" or \"3\")\n5. "Solicitud de Desembolso" template will have a variable [ITERACION] that should be replaced with the iteration number. Generates contract with correct code\n\n## Technical Notes\n- Check existing contract code generation logic in document_service.py\n- May need to update DTOs for the new field\n- Frontend should use react-hook-form for validation\n\n## Acceptance Criteria\n- [ ] New numeric input field visible in contract form\n- [ ] Field has proper validation (required, positive integer)\n- [ ] Default value is 1\n- [ ] Generated documents contain correct contract code with iteration\n- [ ] Iteration is stored in database record\n\n## Affected Files\n- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`\n- `backend/src/adapter/rest/operations_routes.py`\n- `backend/src/core/servicios/document_service.py`\n- `backend/src/interface/` (DTOs if needed)"}'
```

---

## PROMPT-004: DIAN Checkbox Feature for Instruccion de Mandato

**Issue Number:** 4
**ADW ID:** paga-local-004

```
/feature 4 paga-local-004 '{"title": "Implement DIAN Checkbox for Instruccion de Mandato with Auto-Wording", "body": "## Context\nThe Instruccion de Mandato document can have creditors that are either DIAN (tax authority) or other entities (freight agents, customs brokers). Currently, there are two separate forms - one for DIAN and one for generic creditors. When a payment has BOTH types, users must manually combine documents.\n\n## Current State\n- Two separate form paths: DIAN-specific and generic\n- Bank certificate upload is always required\n- No way to handle mixed creditor types in single document\n- Account type shows \"PC\" instead of \"PSE\" for DIAN transfers\n\n## Requirements\n\n### 1. Add DIAN Checkbox per Creditor Row\n- Each creditor in the \"Acreedores\" table should have a checkbox \"Es DIAN\"\n- Checkbox behavior:\n  - **CHECKED (Is DIAN):**\n    - Auto-populate wording: \"Transferencia electronica PSE a favor de la DIAN\"\n    - Bank certificate upload is DISABLED/not required\n    - Account type defaults to \"PSE\"\n  - **UNCHECKED (Not DIAN):**\n    - Bank certificate upload is REQUIRED\n    - Extract bank details from uploaded certificate\n    - User enters creditor name manually\n\n### 2. Support Multiple Mixed Creditors\n- Allow adding multiple creditors (existing + button)\n- Each creditor independently marked as DIAN or not\n- Generate single unified document with all creditors\n- Each creditor section has appropriate wording based on type\n\n### 3. Fix Account Type Bug\n- Current: Shows \"PC\" for tipo_transferencia\n- Expected: Should show \"PSE\" for DIAN transfers\n- Check bank_certificate_parser_service.py and cotizacion_parser_service.py\n\n### 4. Auto-Detection (Enhancement)\n- When creditor name contains \"DIAN\" or \"Direccion de Impuestos\", auto-check the DIAN checkbox\n- User can still uncheck if needed\n\n## DIAN Wording Constant\n```python\nDIAN_WORDING = \"Transferencia electronica PSE a favor de la DIAN\"\nDIAN_KEYWORDS = [\"DIAN\", \"Direccion de Impuestos\", \"Aduanas Nacionales\"]\n```\n\n## User Flow (Mixed Creditors Example)\n1. Upload quotation PDF with DIAN + Freight Agent\n2. System extracts creditors, auto-detects DIAN\n3. Creditor 1 (DIAN): Checkbox checked, wording auto-filled, no cert needed\n4. Creditor 2 (Freight): Checkbox unchecked, upload bank certificate\n5. Generate single Instruccion de Mandato with both creditors\n\n## Acceptance Criteria\n- [ ] Each creditor row has \"Es DIAN\" checkbox\n- [ ] Checking DIAN auto-fills predefined wording\n- [ ] Checking DIAN disables bank certificate upload for that row\n- [ ] Unchecked rows require bank certificate upload\n- [ ] Multiple mixed creditors can be added to single document\n- [ ] Account type correctly shows \"PSE\" for DIAN\n- [ ] DIAN auto-detection works based on creditor name\n- [ ] Generated document contains correct wording for each creditor type\n\n## Affected Files\n- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`\n- `frontend/src/components/` (creditor form components)\n- `backend/src/adapter/rest/operations_routes.py`\n- `backend/src/core/servicios/document_service.py`\n- `backend/src/core/servicios/cotizacion_parser_service.py`\n- `backend/src/core/servicios/bank_certificate_parser_service.py`\n- `backend/templates/` (Instruccion de Mandato template)"}'
```

---

## PROMPT-005: Fix Multi-Creditor Quotation Extraction

**Issue Number:** 5
**ADW ID:** paga-local-005

```
/feature 5 paga-local-005 '{"title": "Fix Quotation Extraction to Support Multiple Creditors", "body": "## Context\nWhen a quotation PDF contains multiple creditors (e.g., DIAN payment + freight agent payment), the extraction only captures the DIAN portion. The total amount shown is incorrect, missing the non-DIAN creditors.\n\n## Current State\n- Quotation parser extracts DIAN payments correctly\n- Non-DIAN creditors (freight agents, customs brokers) are NOT extracted\n- Total amount shows only DIAN portion\n- Example: 78M COP quotation shows as 71M COP (only DIAN part)\n\n## Requirements\n\n### 1. Extract ALL Creditors from Quotation\n- Parse quotation PDF for all payment line items\n- Identify each creditor/recipient in the quotation\n- Extract amount for each creditor separately\n- Calculate correct grand total\n\n### 2. Creditor Type Detection\n- DIAN creditors: Match keywords like \"DIAN\", \"Impuestos\", etc.\n- Freight/Cargo agents: Match patterns like \"Agente de Carga\", company names\n- Customs brokers: Match \"Agencia de Aduanas\", \"SIA\"\n- Other: Any remaining payment items\n\n### 3. Pre-populate Creditor Rows\n- Create a form row for each extracted creditor\n- Auto-check DIAN checkbox for detected DIAN creditors\n- Pre-fill amounts from extraction\n- Show correct total at bottom\n\n### 4. Handle Extraction Errors Gracefully\n- If extraction fails for some items, show partial results\n- Allow manual entry/correction\n- Show warning if extracted total differs from PDF total\n\n## Technical Investigation Needed\n- Analyze quotation PDF format for Finkargo\n- Identify text patterns for different creditor types\n- Review LandingAI integration for multi-section extraction\n- Consider regex patterns for Colombian tax IDs (NIT)\n\n## Example Quotation Structure\n```\nCOTIZACION CO90043638912\n---------------------------\n1. Pago DIAN - Tributos Aduaneros\n   Monto: $71,000,000 COP\n   \n2. Agente de Carga - MGB Logistics\n   Monto: $7,105,000 COP\n   Cuenta: Bancolombia 123-456789\n   \nTOTAL: $78,105,000 COP\n```\n\n## Acceptance Criteria\n- [ ] All creditors extracted from quotation PDF\n- [ ] Correct total amount displayed (sum of all creditors)\n- [ ] Each creditor appears as separate row in form\n- [ ] DIAN creditors auto-detected and marked\n- [ ] Non-DIAN creditors show extracted bank details (if available)\n- [ ] Manual override available for extraction errors\n- [ ] Warning shown if extraction seems incomplete\n\n## Affected Files\n- `backend/src/core/servicios/cotizacion_parser_service.py`\n- `backend/src/core/servicios/landingai_contract_parser_service.py` (if using AI)\n- `backend/src/adapter/rest/operations_routes.py`\n- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`\n\n## Test Data Needed\n- Sample quotation PDFs with multiple creditors\n- Sofia to provide example files for testing"}'
```

---

## Execution Checklist

Use this checklist to track implementation progress:

| # | Prompt | Status | PR # | Notes |
|---|--------|--------|------|-------|
| 1 | Enable Word Download | [ ] Pending | - | Foundation |
| 2 | Granular Permissions | [ ] Pending | - | Foundation |
| 3 | Contract Iteration Field | [ ] Pending | - | Low complexity |
| 4 | DIAN Checkbox | [ ] Pending | - | Medium complexity |
| 5 | Multi-Creditor Extraction | [ ] Pending | - | Medium complexity |

---

## Dependencies Between Prompts

```
PROMPT-001 (Download) ──────────────────────────────────┐
                                                        │
PROMPT-002 (Permissions) ───────────────────────────────┼──> Commercial Rollout
                                                        │
PROMPT-003 (Contract Iteration) ────────────────────────┤
                                                        │
PROMPT-004 (DIAN Checkbox) ─────┬───────────────────────┤
                                │                       │
PROMPT-005 (Multi-Creditor) ────┘ (PROMPT-004 enhances) │
```

**Notes:**
- PROMPT-001, 002, 003 are independent and can be done in any order
- PROMPT-004 and PROMPT-005 are related - PROMPT-005 extraction feeds into PROMPT-004 form
- All must be complete before Commercial team rollout

---

## Post-Implementation Validation

After all prompts are implemented, run these validation commands:

```bash
# Backend validation
cd backend && python -m pytest
cd backend && ruff check src/

# Frontend validation
cd frontend && npm run lint
cd frontend && npx tsc --noEmit
cd frontend && npm run build

# E2E validation (if tests created)
# Follow test_e2e.md instructions for each new E2E test
```

---

## Rollout Timeline

| Day | Activity |
|-----|----------|
| Friday (Today) | Sofia sends updated templates and test files |
| Monday AM | Implement PROMPT-001, 002, 003 |
| Monday PM | Implement PROMPT-004, 005 |
| Monday PM | Deploy to staging, notify Sofia |
| Tuesday | Legal team validates all changes |
| Tuesday PM | Meeting with Commercial team (Martin, Juan Pablo) |
| Wednesday | Create Commercial user accounts |
| Week of Dec 16 | Phase 1: Commercial creates, Legal reviews |
