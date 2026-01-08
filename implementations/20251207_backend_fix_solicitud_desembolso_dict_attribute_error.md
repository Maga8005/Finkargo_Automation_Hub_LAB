# Implementation: Fix Solicitud de Desembolso 'dict' object has no attribute 'nit' error

**Date:** 2025-12-07
**Module:** Backend - adapter/rest
**Issue:** Solicitud de Desembolso generation fails with AttributeError

## Summary

Fixed the "'dict' object has no attribute 'nit'" error that occurred when generating Solicitud de Desembolso contracts. The bug was caused by accessing client data using object attribute notation when the repository returns a dictionary.

## Changes Made

- **Fixed client data access pattern** in `backend/src/adapter/rest/operations_routes.py`:
  - Changed attribute access (`client.nit`) to dictionary key access (`client['nit']`)
  - Used `.get()` method for optional fields (`direccion_comercial`, `tipo_identificacion_representante`)
  - Improved `cupo_plataforma` handling with null-safe conversion

- **Created E2E test file** at `.claude/commands/e2e/test_solicitud_desembolso_generation.md`:
  - Full test workflow for Solicitud de Desembolso generation
  - Validates bug fix with success criteria

## Root Cause

The `ClientRepository.get_by_nit()` method returns `Optional[dict]`, but the `generate_solicitud_desembolso` endpoint incorrectly accessed client data using object attribute notation:

```python
# Before (Bug)
"nit": client.nit,  # AttributeError: 'dict' object has no attribute 'nit'

# After (Fix)
"nit": client['nit'],  # Correct dictionary access
```

## Files Changed

```
backend/src/adapter/rest/operations_routes.py | 19 ++++++++---------
```

**Key changes in `operations_routes.py` (lines 273-285):**
- `client.nit` → `client['nit']`
- `client.nombre_importador` → `client['nombre_importador']`
- `client.representante_legal` → `client['representante_legal']`
- `client.cedula_representante` → `client['cedula_representante']`
- `client.ciudad_domicilio` → `client['ciudad_domicilio']`
- `client.cupo_plataforma` → `client.get('cupo_plataforma')` with safe conversion
- `client.direccion_comercial` → `client.get('direccion_comercial')`
- `client.tipo_identificacion_representante` → `client.get('tipo_identificacion_representante')`

## New Files

- `.claude/commands/e2e/test_solicitud_desembolso_generation.md` - E2E test for validation

## Validation Results

| Check | Status |
|-------|--------|
| Backend tests (pytest) | ✅ 19/19 passed |
| Backend linting (ruff) | ✅ All checks passed |
| Frontend linting (eslint) | ✅ No errors |
| TypeScript type check | ✅ No errors |
| Frontend build (vite) | ✅ Built successfully |

## Testing

To validate the fix:
1. Log in as Operations user
2. Navigate to Paga Local Colombia > Solicitud de Desembolso
3. Search and select a client
4. Upload a Cotización PDF
5. Extract data from PDF
6. Click "Solicitar Documento"
7. Verify success message appears with contract ID (format: PLSD-YYYY-XXX)

## Related Files

- Spec: `specs/issue-0-adw-0-sdlc_planner-fix-solicitud-desembolso-dict-attribute-error.md`
- E2E Test: `.claude/commands/e2e/test_solicitud_desembolso_generation.md`
