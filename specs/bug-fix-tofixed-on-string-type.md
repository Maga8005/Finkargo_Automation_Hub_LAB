# Bug: toFixed is not a function on score_impact fields

## Bug Description
When navigating to the "Validación Cruzada" tab in the risk module to process a client record (e.g., Azelis), the application crashes with the error:
```
FKCrossValidationResults.tsx:412 Uncaught TypeError: results.total_score_impact.toFixed is not a function
```

The UI expects `total_score_impact` and `score_impact` to be numbers, but they arrive as strings from the backend API.

## Problem Statement
The backend uses Pydantic's `Decimal` type for numeric precision, which serializes to strings in JSON responses. The frontend directly calls `.toFixed()` on these values without first converting them to numbers, causing a TypeError.

## Solution Statement
Convert the string values to numbers before calling `.toFixed()` in the frontend component. Use `Number()` or `parseFloat()` to safely convert the value, with fallback to 0 for null/undefined values.

## Steps to Reproduce
1. Log into the Finkargo Automation Hub
2. Navigate to Risk > Evaluations
3. Select a client record (e.g., Azelis)
4. Go to the "Validación Cruzada" (Cross-Validation) tab
5. Click "Ejecutar Validación" to trigger validation
6. Observe the TypeError crash in the console

## Root Cause Analysis
The backend DTO `CrossValidationResponse` defines `total_score_impact: Decimal` and `CrossValidationResult` defines `score_impact: Decimal`. Pydantic's default JSON serialization of `Decimal` types produces strings to preserve decimal precision. For example:
- Backend: `Decimal('15.5')`
- JSON: `"15.5"` (string)
- Frontend receives: `"15.5"` (string, not number)

The frontend code at line 412 calls:
```typescript
results.total_score_impact.toFixed(0)
```

And at line 274:
```typescript
result.score_impact.toFixed(0)
```

Since `"15.5".toFixed` is not a function (strings don't have `.toFixed()`), the error occurs.

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

- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Contains the two lines where `.toFixed()` is called on values that may be strings:
  - Line 274: `result.score_impact.toFixed(0)` in the renderResult function
  - Line 412: `results.total_score_impact.toFixed(0)` in the Score impact Alert
- `frontend/src/types/risk.ts` - TypeScript types for `CrossValidationResponse` and `CrossValidationResult`. The types define `score_impact: number` and `total_score_impact: number`, but the runtime values are actually strings.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Fix total_score_impact.toFixed() at line 409-415
Update the Score impact Alert section to safely convert the value to a number before calling `.toFixed()`:

**Current code (line 409-415):**
```typescript
{results.total_score_impact > 0 && (
  <Alert severity="warning" sx={{ mb: 2 }}>
    <Typography variant="subtitle2">
      Impacto total en puntuación de riesgo: +{results.total_score_impact.toFixed(0)} puntos
    </Typography>
  </Alert>
)}
```

**Fix:**
```typescript
{Number(results.total_score_impact) > 0 && (
  <Alert severity="warning" sx={{ mb: 2 }}>
    <Typography variant="subtitle2">
      Impacto total en puntuación de riesgo: +{Number(results.total_score_impact).toFixed(0)} puntos
    </Typography>
  </Alert>
)}
```

### Task 2: Fix result.score_impact.toFixed() at line 271-278
Update the Chip component in renderResult to safely convert the value:

**Current code (line 271-278):**
```typescript
{result.is_discrepancy && result.score_impact > 0 && (
  <Chip
    size="small"
    label={`+${result.score_impact.toFixed(0)} pts`}
    color="error"
    variant="outlined"
  />
)}
```

**Fix:**
```typescript
{result.is_discrepancy && Number(result.score_impact) > 0 && (
  <Chip
    size="small"
    label={`+${Number(result.score_impact).toFixed(0)} pts`}
    color="error"
    variant="outlined"
  />
)}
```

### Task 3: Run Validation Commands
Execute all validation commands to ensure the fix is correct with zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd frontend && npm run lint` - Run frontend linting to check for syntax errors
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check to verify type compatibility
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- The root issue is a type mismatch between TypeScript definitions (`number`) and runtime JSON values (`string` from Decimal serialization)
- Alternative fixes considered:
  1. **Backend fix**: Configure Pydantic to serialize Decimal as float. This would change API contract and may affect precision.
  2. **Service layer fix**: Transform data in `riskService.ts` to convert strings to numbers. More comprehensive but more code change.
- The chosen fix (direct Number() conversion) is minimal, surgical, and handles the immediate issue without broader refactoring.
- `Number()` safely handles both string `"15.5"` and number `15.5` inputs, returning a number in both cases.
- `Number(null)` returns `0` and `Number(undefined)` returns `NaN`, so the `> 0` check handles edge cases.
