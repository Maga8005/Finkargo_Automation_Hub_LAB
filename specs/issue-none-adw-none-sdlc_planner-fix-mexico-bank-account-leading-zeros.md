# Bug: Mexico Bank Account Mapping Fails Due to Leading Zero Mismatch

## Bug Description
When converting Mexico payment history files, only 1 out of 4 bank account mappings works. The output file shows `account` values only for client `QCO160719578` (mapped to 2110), while all other rows have empty `account` fields despite having valid `Cuenta Remitente` values in the source file.

**Expected Behavior:** All rows with valid `Cuenta Remitente` values should have their corresponding `account` field populated based on the `MEXICO_BANK_ACCOUNT_MAPPING`.

**Actual Behavior:** Only rows with `Cuenta Remitente = 669555222` get mapped to `account = 2110`. All other mappings fail silently.

## Problem Statement
The `MEXICO_BANK_ACCOUNT_MAPPING` dictionary stores account numbers with leading zeros (e.g., `"0123270165"`), but the Excel source file stores them as integers without leading zeros (e.g., `123270165`). When the value is read from Excel and converted to a string, it becomes `"123270165"` which doesn't match `"0123270165"`.

## Solution Statement
Update the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary to use account numbers **without** leading zeros, matching how they appear in the Excel source file. This is a data fix, not a logic fix.

Mappings to correct:
- `"0123270165"` → `"123270165"` (maps to 2322)
- `"0123375153"` → `"123375153"` (maps to 2320)
- `"0118970882"` → `"118970882"` (maps to 2111)
- `"669555222"` stays the same (already works)

## Steps to Reproduce
1. Navigate to http://localhost:5173/tesoreria/plantillas-netsuite/mexico
2. Upload the file: `Example FIles for Reqs/20251209 EJEMPLO HISTORIAL DE PAGOS MEXICO (1).xlsx`
3. Click "Convertir y Descargar"
4. Open the downloaded file
5. **Observe:** Only rows for client `QCO160719578` have `account = 2110`. All other rows have empty `account` field.
6. **Expected:** All rows should have `account` values:
   - `SON070222MH9`: account = 2322 (Cuenta Remitente: 123270165)
   - `APA150624K24`: account = 2322 (Cuenta Remitente: 123270165)
   - `KSK201123DBA`: account = 2322 (Cuenta Remitente: 123270165)
   - `QCO160719578`: account = 2110 (Cuenta Remitente: 669555222) ✅ Already works
   - `GEM201020UB2`: account = 2320 (Cuenta Remitente: 123375153)

## Root Cause Analysis
The root cause is a **data mismatch** between the mapping dictionary keys and the actual Excel values:

1. **Excel stores account numbers as integers**: When read by pandas, `Cuenta Remitente` values are `int64` type (e.g., `123270165`)

2. **Mapping uses string keys with leading zeros**: The `MEXICO_BANK_ACCOUNT_MAPPING` has keys like `"0123270165"`

3. **Conversion to string drops leading zeros**: When the code does `str(cuenta_remitente).strip()`, an integer `123270165` becomes `"123270165"`, not `"0123270165"`

4. **Lookup fails**: `MEXICO_BANK_ACCOUNT_MAPPING.get("123270165")` returns `None` because the key is `"0123270165"`

**Why `669555222` works:** This account number doesn't have a leading zero, so the integer and string representations are identical.

## Affected Layer
- [x] Backend: core/servicios (business logic) - catalog data

## Relevant Files
Use these files to fix the bug:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** (lines 97-102) - Contains the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary with incorrect leading zeros in the keys. The keys need to be updated to match the actual Excel values (without leading zeros).

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Update MEXICO_BANK_ACCOUNT_MAPPING Keys
- Open `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Locate the `MEXICO_BANK_ACCOUNT_MAPPING` dictionary (around line 97)
- Update the keys to remove leading zeros:

```python
# Before:
MEXICO_BANK_ACCOUNT_MAPPING: Dict[str, int] = {
    "0123270165": 2322,
    "0123375153": 2320,
    "0118970882": 2111,
    "669555222": 2110,
}

# After:
MEXICO_BANK_ACCOUNT_MAPPING: Dict[str, int] = {
    "123270165": 2322,
    "123375153": 2320,
    "118970882": 2111,
    "669555222": 2110,
}
```

### Task 2: Run Validation Commands
Execute all validation commands to ensure the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Test 123270165:', get_bank_account_id('123270165', 'mexico')); print('Test 123375153:', get_bank_account_id('123375153', 'mexico')); print('Test 118970882:', get_bank_account_id('118970882', 'mexico')); print('Test 669555222:', get_bank_account_id('669555222', 'mexico'))"` - Verify all Mexico bank account mappings work correctly
- `cd backend && python -c "from src.core.servicios.catalogs.payment_catalogs import get_bank_account_id; print('Colombia regression:', get_bank_account_id('60100001091', 'colombia'))"` - Verify Colombia mappings still work
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check

## Notes
- The original mapping values were provided by the user with leading zeros (`0123270165`), but Excel strips leading zeros when storing numbers
- This is a common issue when bank account numbers are stored as numeric values in Excel rather than text
- The fix is minimal - only the dictionary keys need to be updated, no logic changes required
- If future mappings are added, ensure they match how the values appear in the Excel source file (as integers, without leading zeros)
