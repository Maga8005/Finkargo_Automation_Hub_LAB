# Implementation Report: Fix Instrucción de Mandato generate_contract() Keyword Arguments

## Date: 2025-12-07

## Summary

Fixed a bug in the `generate_instruccion_mandato` API endpoint where the call to `ContractService.generate_contract()` was using incorrect keyword arguments, causing a 500 error with message: `"generate_contract() got an unexpected keyword argument 'client_nit'"`.

## Work Completed

- **Verified the bug**: Confirmed `ContractType.PL_CO_MANDATO_IM` exists in `legal_dtos.py` (line 30)
- **Verified method signature**: Confirmed `ContractService.generate_contract()` expects `(request: ContractGenerationRequest, user_id: str, custom_data_snapshot: Optional[Dict])`
- **Fixed the endpoint**: Updated `generate_instruccion_mandato` in `operations_routes.py` to:
  1. Create a `ContractGenerationRequest` object with proper fields
  2. Call `service.generate_contract()` with correct parameters: `request`, `user_id`, `custom_data_snapshot`
  3. Improved response handling with safer `contract.get()` pattern
- **Validated the fix**: All backend tests pass (47/47), frontend linting and TypeScript check pass, production build succeeds

## Discrepancies Found

**None** - The plan accurately identified the root cause and the fix pattern was correct. The implementation followed the same pattern used in the working `generate_solicitud_desembolso` endpoint (lines 304-316).

## Code Changes

### backend/src/adapter/rest/operations_routes.py

**Before (lines 713-721):**
```python
# Generate contract using service
contract = await service.generate_contract(
    client_nit=request.client_nit,
    contract_type="pl_co_mandato_im",
    generated_by=user_id,
    data_snapshot=data_snapshot
)

logger.info(f"Generated Instrucción de Mandato contract: {contract['contract_id']}")
```

**After (lines 713-728):**
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

contract_id = contract.get('contract_id', 'unknown')
logger.info(f"Generated Instrucción de Mandato contract: {contract_id}")
```

## Files Changed

```
backend/src/adapter/rest/operations_routes.py | 19 +++++++++++++------
1 file changed, 13 insertions(+), 6 deletions(-)
```

## Validation Results

| Command | Result |
|---------|--------|
| `cd backend && ruff check src/` | ✅ All checks passed |
| `cd backend && python -m pytest` | ✅ 47 tests passed |
| `cd frontend && npm run lint` | ✅ No errors |
| `cd frontend && npx tsc --noEmit` | ✅ No type errors |
| `cd frontend && npm run build` | ✅ Build successful |

## Related Files

- **Bug Plan**: `specs/issue-69-adw-a62436e0-sdlc_planner-fix-instruccion-mandato-generate.md`
- **Fixed File**: `backend/src/adapter/rest/operations_routes.py`
- **Reference Pattern**: Lines 304-316 in same file (`generate_solicitud_desembolso` endpoint)

## Testing

To validate the fix end-to-end:
1. Start dev servers: `./scripts/start-dev.sh`
2. Login as operations user
3. Navigate to `/operations/contratos-paga-local-colombia`
4. Click "Documentos Operación" tab → "Mandato (IM)" subtab
5. Search for a client, upload Cotización PDF, add creditor info
6. Click "Generar Instrucción de Mandato"
7. Verify successful generation with contract ID displayed
