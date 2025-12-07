# Bug: Monto Total String Concatenation Instead of Numeric Sum

## Bug Description
In the Solicitud de Desembolso form (Paga Local Colombia), the "Monto Total" field displays a concatenated string of values instead of their numeric sum. For example, instead of showing `$739,860.00 COP` (the sum of `407001.00 + 290000.00 + 42859.00`), it displays `$0407001.00290000.0042859.00 COP` - a string concatenation of all individual amounts with a leading `0` from the reduce initial value.

**Expected Behavior:** The total should be `407001 + 290000 + 42859 = 739860` formatted as `$739,860 COP`

**Actual Behavior:** The total displays as `$0407001.00290000.0042859.00 COP` (string concatenation)

## Problem Statement
The frontend component calculates the monto total using JavaScript's `reduce()` method with the `+` operator. When the `monto` values in `anexoItems` are strings (instead of numbers), the `+` operator performs string concatenation rather than numeric addition.

## Solution Statement
Convert `monto` values to numbers when receiving data from the backend API. The backend uses Python `Decimal` type for precision, which Pydantic serializes as strings in JSON. The frontend must parse these string values to numbers before performing arithmetic operations.

## Steps to Reproduce
1. Navigate to http://localhost:5173/operations/paga-local-colombia
2. Click on "Documentos Operación" tab
3. Click on "Solicitud Desembolso" sub-tab
4. Search for a client by NIT or name
5. Upload a Cotización PDF file
6. Click "Extraer Datos del PDF"
7. Observe the "Monto Total" field in Section 3 and the TOTAL row in Section 4
8. Both show concatenated strings instead of numeric sums

## Root Cause Analysis
The bug occurs due to a type mismatch between backend and frontend:

1. **Backend (`legal_dtos.py`)**: The `AnexoItem` model defines `monto: Decimal` (line 325)
2. **Backend Serialization**: Pydantic v2 serializes `Decimal` fields as **strings** in JSON by default for precision preservation
3. **Frontend (`legal.ts`)**: The `AnexoItem` interface defines `monto: number` (line 171)
4. **Frontend Calculation** (`FKSolicitudDesembolsoRequest.tsx` line 64):
   ```typescript
   const total = anexoItems.reduce((sum, item) => sum + (item.monto || 0), 0);
   ```
5. When `item.monto` is a string like `"407001.00"`, JavaScript coerces the number `0` to `"0"` and concatenates: `"0" + "407001.00"` = `"0407001.00"`

The issue is in the frontend where `data.anexo_items` from the API is used directly without type conversion (line 129):
```typescript
setAnexoItems(data.anexo_items || []);
```

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`** - Main component with the bug. Lines 64 (useEffect calculation), 129 (setAnexoItems), and 498 (handleAnexoItemChange for monto) need attention.
- **`frontend/src/types/legal.ts`** - TypeScript interface for `AnexoItem` (line 168-172). The `monto: number` type is correct, but the runtime value is a string from the API.
- **`backend/src/interface/legal_dtos.py`** - Backend DTO with `monto: Decimal` type (line 325). Consider adding serialization config.
- **`.claude/commands/test_e2e.md`** - E2E test runner instructions.
- **`.claude/commands/e2e/test_login.md`** - E2E test example for reference.

### New Files
- **`.claude/commands/e2e/test_solicitud_desembolso_monto_total.md`** - E2E test to validate the monto total calculation fix.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix the monto type conversion in FKSolicitudDesembolsoRequest.tsx

- In `handleExtractData()` function (around line 123-139), convert `anexo_items` monto values to numbers when setting state:
  ```typescript
  // Convert monto from string to number for each anexo item
  const convertedItems = (data.anexo_items || []).map(item => ({
    ...item,
    monto: typeof item.monto === 'string' ? parseFloat(item.monto) : Number(item.monto)
  }));
  setAnexoItems(convertedItems);
  ```

- This ensures all `monto` values are proper JavaScript numbers before being stored in state.

### 2. Update the useEffect calculation to be more robust

- In the `useEffect` that calculates total (around line 63-66), ensure numeric coercion:
  ```typescript
  useEffect(() => {
    const total = anexoItems.reduce((sum, item) => {
      const monto = typeof item.monto === 'string' ? parseFloat(item.monto) : Number(item.monto);
      return sum + (monto || 0);
    }, 0);
    setMontoTotal(total);
  }, [anexoItems]);
  ```

- This defensive check ensures the calculation works even if somehow a string value gets through.

### 3. Verify handleAnexoItemChange already converts properly

- Confirm that line 498 `onChange={(e) => handleAnexoItemChange(index, 'monto', Number(e.target.value))}` correctly converts user input to numbers.
- No changes needed here, but verify during testing.

### 4. Create E2E test file

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand the E2E test format.
- Create a new E2E test file at `.claude/commands/e2e/test_solicitud_desembolso_monto_total.md` that:
  1. Logs in as an operations user
  2. Navigates to Paga Local Colombia → Documentos Operación → Solicitud Desembolso
  3. Searches for a client
  4. Uploads a test Cotización PDF
  5. Extracts data from PDF
  6. **Verifies** the Monto Total displays a properly formatted numeric sum (e.g., `$739,860 COP`)
  7. **Verifies** the TOTAL row in Anexo I table shows correct sum
  8. Takes screenshots at each step to prove the fix works

### 5. Run Validation Commands

- Execute all validation commands to confirm the bug is fixed with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_solicitud_desembolso_monto_total.md` test file to validate this functionality works

## Notes
- The bug is purely a frontend type coercion issue. The backend is correct in using `Decimal` for financial precision.
- An alternative backend fix would be to configure Pydantic to serialize `Decimal` as `float`, but this could cause precision loss for very large amounts. The frontend fix is safer and more appropriate.
- The pattern `typeof value === 'string' ? parseFloat(value) : Number(value)` handles both string and number inputs safely.
- The `|| 0` fallback handles `NaN` cases from invalid parsing.
