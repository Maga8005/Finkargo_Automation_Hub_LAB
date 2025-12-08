# Bug: Instrucción de Mandato generate_contract() incorrect keyword arguments

## Bug Description
When attempting to generate an Instrucción de Mandato document, the system returns the error: `"Error al generar documento: Error generating contract: generate_contract() got an unexpected keyword argument 'client_nit'"`. The frontend form completes successfully (client selection, Cotización PDF upload, bank certificate extraction), but the final API call to generate the document fails with this backend error.

**Expected behavior:** The Instrucción de Mandato document should be generated successfully and placed in the Legal review queue.

**Actual behavior:** The API returns a 500 error with the message about unexpected keyword argument.

## Problem Statement
The `generate_instruccion_mandato` endpoint in `operations_routes.py` is calling `ContractService.generate_contract()` with incorrect keyword arguments that don't match the method's signature. The method expects `(request: ContractGenerationRequest, user_id: str, custom_data_snapshot: Optional[Dict])` but the endpoint is passing `(client_nit, contract_type, generated_by, data_snapshot)`.

## Solution Statement
Fix the API endpoint to call `service.generate_contract()` with the correct signature by:
1. Creating a `ContractGenerationRequest` object with the proper fields
2. Passing `request`, `user_id`, and `custom_data_snapshot` as the method expects

This follows the same pattern already correctly implemented in the `generate_solicitud_desembolso` endpoint (lines 304-316).

## Steps to Reproduce
1. Login as an operations user
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click "Documentos Operación" tab
4. Click "Mandato (IM)" subtab
5. Search and select a client (e.g., NIT: 900436389)
6. Upload a Cotización PDF
7. Click "Extraer Datos del PDF"
8. Add at least one creditor with bank information
9. Click "Generar Instrucción de Mandato"
10. Observe error: "Error al generar documento: Error generating contract: generate_contract() got an unexpected keyword argument 'client_nit'"

## Root Cause Analysis
In `backend/src/adapter/rest/operations_routes.py` at lines 714-719, the endpoint incorrectly calls:

```python
contract = await service.generate_contract(
    client_nit=request.client_nit,
    contract_type="pl_co_mandato_im",
    generated_by=user_id,
    data_snapshot=data_snapshot
)
```

But `ContractService.generate_contract()` (defined in `contract_service.py` at lines 41-46) expects:

```python
async def generate_contract(
    self,
    request: ContractGenerationRequest,
    user_id: str,
    custom_data_snapshot: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
```

The correct pattern is used in `generate_solicitud_desembolso` (lines 304-316):

```python
contract_request = ContractGenerationRequest(
    client_nit=request.client_nit,
    contract_type=ContractType.PL_CO_SOLICITUD_DESEMBOLSO,
    custodian_data=None
)

contract = await service.generate_contract(
    request=contract_request,
    user_id=user_id,
    custom_data_snapshot=data_snapshot
)
```

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`backend/src/adapter/rest/operations_routes.py`** (lines 639-741)
  - Contains the buggy `generate_instruccion_mandato` endpoint
  - Lines 714-719 have the incorrect `service.generate_contract()` call
  - Reference lines 304-316 (`generate_solicitud_desembolso`) for correct pattern

- **`backend/src/core/servicios/contract_service.py`** (lines 41-46)
  - Contains the `generate_contract()` method signature
  - Used to verify correct parameter names: `request`, `user_id`, `custom_data_snapshot`

- **`backend/src/interface/legal_dtos.py`** (lines 1-100)
  - Contains `ContractGenerationRequest` and `ContractType` definitions
  - Confirm `ContractType.PL_CO_MANDATO_IM` exists (line 30)

- **`.claude/commands/e2e/test_instruccion_mandato_form.md`**
  - Existing E2E test file to validate the bug fix
  - Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Verify the Bug Exists

- Start development servers: `./scripts/start-dev.sh`
- Check backend logs while attempting to generate an Instrucción de Mandato
- Confirm the error message matches: `generate_contract() got an unexpected keyword argument 'client_nit'`

### Task 2: Verify ContractType.PL_CO_MANDATO_IM Exists

- Read `backend/src/interface/legal_dtos.py`
- Confirm `PL_CO_MANDATO_IM = "pl_co_mandato_im"` exists in the `ContractType` enum
- If missing, add it (but based on analysis, it exists at line 30)

### Task 3: Fix the generate_instruccion_mandato Endpoint

- Open `backend/src/adapter/rest/operations_routes.py`
- Locate the `generate_instruccion_mandato` function (line 639)
- Replace lines 713-719 with the correct pattern:

**Before (incorrect):**
```python
# Generate contract using service
contract = await service.generate_contract(
    client_nit=request.client_nit,
    contract_type="pl_co_mandato_im",
    generated_by=user_id,
    data_snapshot=data_snapshot
)
```

**After (correct):**
```python
# Create contract generation request
contract_request = ContractGenerationRequest(
    client_nit=request.client_nit,
    contract_type=ContractType.PL_CO_MANDATO_IM,
    custodian_data=None  # Not needed for Instrucción de Mandato
)

# Generate contract with custom data snapshot
contract = await service.generate_contract(
    request=contract_request,
    user_id=user_id,
    custom_data_snapshot=data_snapshot
)
```

- Ensure `ContractGenerationRequest` and `ContractType` are imported at the top of the file (they should already be imported based on line 22-31)

### Task 4: Update Response Handling

- Review lines 721-734 in the same endpoint
- The current code accesses `contract['contract_id']` as a dict, which is correct for the service return type
- However, update line 718 (after the fix) to handle the response correctly:

**Before:**
```python
logger.info(f"Generated Instrucción de Mandato contract: {contract['contract_id']}")
```

**After (should be moved after service call):**
```python
contract_id = contract.get('contract_id', 'unknown')
logger.info(f"Generated Instrucción de Mandato contract: {contract_id}")
```

### Task 5: Run Backend Linting and Tests

- Run `cd backend && ruff check src/` to verify no linting errors
- Run `cd backend && python -m pytest` to ensure no regressions

### Task 6: Test the Fix Manually

- Start development servers if not running: `./scripts/start-dev.sh`
- Login as operations user
- Navigate to Paga Local Colombia → Documentos Operación → Mandato (IM)
- Complete the form and generate a document
- Verify successful generation with contract ID displayed
- Check Legal review queue for the new contract

### Task 7: Run Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && ruff check src/` - Run backend linting
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_instruccion_mandato_form.md` to validate the complete workflow end-to-end

## Notes

### Pattern Consistency
This fix aligns the `generate_instruccion_mandato` endpoint with the already-working `generate_solicitud_desembolso` endpoint. Both should use the same pattern:

1. Create a `ContractGenerationRequest` object
2. Call `service.generate_contract(request=..., user_id=..., custom_data_snapshot=...)`

### No Database Changes Needed
The contract template for `pl_co_mandato_im` should already exist in the database from migration `migration_add_paga_local_mandato_pj_pn_templates.sql`. If document generation fails after this fix with "No active contract template found", a separate migration may be needed.

### Minimal Change
This is a surgical fix - only lines 713-719 in `operations_routes.py` need to be modified to correct the API call signature. The frontend, types, and other backend layers are functioning correctly.
