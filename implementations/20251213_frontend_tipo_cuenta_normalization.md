# Implementation Report: Bank Certificate tipo_cuenta Normalization

## Issue #100 - Bug Fix

**Date**: 2025-12-13
**Module**: Frontend
**Type**: Bug Fix

## Summary

Fixed the bank certificate extraction bug where the "Tipo de Cuenta" dropdown appeared empty after extracting data from a bank certificate PDF, even though the value was successfully extracted by the backend.

## Changes Made

- Added `normalizeTipoCuenta()` helper function to `FKInstruccionMandatoForm.tsx`
- Updated `handleExtractBankCert()` function to normalize the `tipo_cuenta` value

## Technical Details

### Root Cause
The backend `bank_certificate_parser_service.py` returns account types in Colombian bank certificate format:
- `"CUENTA DE AHORROS"`
- `"CUENTA CORRIENTE"`

The frontend dropdown options are:
- `"Ahorros"`
- `"Corriente"`
- `"PSE"`

MUI's `<Select>` component displays empty when the `value` prop doesn't match any `<MenuItem>` value.

### Solution
Added a normalization function that maps backend values to frontend dropdown values:
```typescript
const normalizeTipoCuenta = (tipoCuenta: string): string => {
  const lower = tipoCuenta.toLowerCase();
  if (lower.includes('ahorr')) return 'Ahorros';
  if (lower.includes('corriente')) return 'Corriente';
  if (lower.includes('pse')) return 'PSE';
  return tipoCuenta;
};
```

Applied in `handleExtractBankCert()`:
```typescript
tipo_cuenta: data.tipo_cuenta ? normalizeTipoCuenta(data.tipo_cuenta) : '',
```

## Files Changed

| File | Lines Changed |
|------|--------------|
| `frontend/src/components/forms/FKInstruccionMandatoForm.tsx` | +14 (helper function + usage) |
| `.claude/commands/e2e/test_bank_certificate_extraction.md` | +94 (new E2E test) |

## Discrepancies Found

**None** - The plan accurately described the problem and solution. All assumptions were verified:
- `ACCOUNT_TYPES` at line 56: `['Ahorros', 'Corriente', 'PSE']` - confirmed
- Backend returns `"CUENTA DE AHORROS"` and `"CUENTA CORRIENTE"` from `_extract_tipo_cuenta()` - confirmed
- `handleExtractBankCert()` function existed at lines 241-273 - confirmed (now 254-286 after additions)

## Validation Results

### Backend Tests
```
pytest tests/ -v
227 tests passed
```

### Backend Linting
```
ruff check src/
All checks passed!
```

### Frontend Linting
```
npm run lint
0 errors, 4 warnings (pre-existing, unrelated to this change)
```

### TypeScript Check
```
npx tsc --noEmit
No errors
```

### Production Build
```
npm run build
Build successful
```

## Git Diff Stats

```
frontend/src/components/forms/FKInstruccionMandatoForm.tsx | 14 +
.claude/commands/e2e/test_bank_certificate_extraction.md  | 94 +
2 files changed, 108 insertions(+)
```

## E2E Test Created

Added E2E test file: `.claude/commands/e2e/test_bank_certificate_extraction.md`

The test validates:
1. Bank certificate upload and extraction workflow
2. Tipo de Cuenta dropdown shows correct normalized value
3. All bank certificate fields populate correctly
4. Document generates with complete bank account information

## Testing Notes

To manually verify this fix:
1. Start dev servers (`npm run dev` and `uvicorn`)
2. Navigate to Operaciones > Paga Local Colombia
3. Select a client and upload a cotizacion
4. For a non-DIAN creditor, upload a bank certificate
5. Click "Extraer Datos"
6. **Verify** the "Tipo de Cuenta" dropdown shows "Ahorros" or "Corriente" (not empty)
7. Submit and verify document generates with bank account data
