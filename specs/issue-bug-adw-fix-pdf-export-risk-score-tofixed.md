# Bug: PDF Export fails with TypeError: risk_score.toFixed is not a function

## Bug Description
When users click the "Generar Reporte" button on the Risk Evaluation Detail page to export a comprehensive evaluation PDF, the application throws a TypeError: `assessment.risk_score.toFixed is not a function`. The error occurs at line 611 in `crossValidationPdfExport.ts` because `risk_score` is a string (serialized from backend Decimal) but the code expects it to be a number.

**Symptoms:**
- User clicks "Generar Reporte" button
- Error alert appears: "Error al generar el reporte"
- Browser console shows: `TypeError: assessment.risk_score.toFixed is not a function`
- No PDF file is generated or downloaded

**Expected Behavior:**
- PDF report is generated successfully
- PDF downloads with filename like `Evaluacion_Completa_RISK-2024-XXX.pdf`
- No errors in console

## Problem Statement
The `risk_score` field is defined as `Decimal` in the backend Pydantic model (`RiskAssessmentResponse`), which gets serialized to a **string** in JSON responses (e.g., `"45.50"` instead of `45.50`). The frontend code calls `.toFixed()` on this string value, which fails because strings don't have the `toFixed()` method.

Additionally, `score_impact` fields on `fraud_indicators` may have the same issue.

## Solution Statement
Wrap all numeric values that need `toFixed()` with `Number()` to ensure they are converted to JavaScript numbers before calling numeric methods. This is a defensive coding practice that handles both cases (string or number input).

The fix should be applied to:
1. `assessment.risk_score.toFixed(0)` → `Number(assessment.risk_score).toFixed(0)`
2. `ind.score_impact.toFixed(0)` → `Number(ind.score_impact).toFixed(0)`

## Steps to Reproduce
1. Log in as a user with `risk_analyst` or `risk_manager` role
2. Navigate to Risk Dashboard (/department/riesgo)
3. Click on any existing evaluation to open details
4. Click "Generar Reporte" button (in the Actions section or toolbar)
5. **OBSERVE**: Error alert appears and no PDF is generated

## Root Cause Analysis
The root cause is a **type mismatch** between backend serialization and frontend expectations:

1. **Backend** (`risk_dtos.py`, lines 117-152):
   ```python
   class RiskAssessmentResponse(BaseModel):
       risk_score: Decimal = Field(..., ge=0, le=100)

       @validator('risk_score', pre=True)
       def coerce_risk_score(cls, v):
           return Decimal(str(v))
   ```
   Pydantic's `Decimal` type is serialized to a **string** in JSON to preserve precision.

2. **Frontend Type** (`risk.ts`, line 69):
   ```typescript
   export interface RiskAssessment {
       risk_score: number;  // TypeScript expects number
   }
   ```

3. **Error Location** (`crossValidationPdfExport.ts`, line 611):
   ```typescript
   doc.text(`${assessment.risk_score.toFixed(0)}`, 18, summaryY);
   // Fails because risk_score is actually "45.50" (string), not 45.50 (number)
   ```

The same issue affects `score_impact` on fraud indicators (line 658).

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [x] Frontend: utils (crossValidationPdfExport.ts)

## Relevant Files
Use these files to fix the bug:

- `frontend/src/utils/crossValidationPdfExport.ts` - Contains the PDF export function with the broken `toFixed()` calls. Lines 611 and 658 need fixing.
- `frontend/src/types/risk.ts` - Contains type definitions. Shows `risk_score: number` and `score_impact: number` which don't match the actual string values from API.
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Calls the export function and builds the `reportContext`. Lines 162-175 show where the data is passed.

### Reference Files (for E2E test creation)
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_risk_score_after_validation.md` - Example E2E test for risk module

### New Files
- `.claude/commands/e2e/test_risk_pdf_export.md` - E2E test to validate PDF export works

## Step by Step Tasks

### Task 1: Fix risk_score.toFixed() TypeError

- Open `frontend/src/utils/crossValidationPdfExport.ts`
- Locate line 611: `doc.text(\`${assessment.risk_score.toFixed(0)}\`, 18, summaryY);`
- Change to: `doc.text(\`${Number(assessment.risk_score).toFixed(0)}\`, 18, summaryY);`
- This ensures the string is converted to a number before calling `toFixed()`

### Task 2: Fix score_impact.toFixed() for Fraud Indicators

- In the same file, locate line 658: `` `+${ind.score_impact.toFixed(0)}`, ``
- Change to: `` `+${Number(ind.score_impact).toFixed(0)}`, ``
- This fixes the same issue for fraud indicator score impacts

### Task 3: Verify All toFixed() Calls Use Number() Wrapper

- Review all `.toFixed()` calls in the file (lines 260, 285, 611, 658, 725)
- Lines 260, 285, and 725 already use `Number()` wrapper - confirm they are correct
- Ensure lines 611 and 658 now have the `Number()` wrapper

### Task 4: Create E2E Test for PDF Export

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_risk_score_after_validation.md` for reference
- Create new E2E test file: `.claude/commands/e2e/test_risk_pdf_export.md`
- Test steps should include:
  1. Login as risk_analyst
  2. Navigate to Risk Dashboard
  3. Select an existing evaluation
  4. Click "Generar Reporte" button
  5. **Verify** no error message appears
  6. **Verify** PDF file downloads (check for file or browser download prompt)
  7. Take screenshots before and after clicking the button

### Task 5: Run Validation Commands

- Run all validation commands to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Pre-fix verification (should fail):**
- Navigate to risk evaluation detail and click "Generar Reporte" → observe error in console

**Post-fix verification:**
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- `cd backend && ruff check src/` - Run backend linting (no changes expected)

**Manual verification:**
- Navigate to risk evaluation detail
- Click "Generar Reporte" button
- **Verify** no error appears
- **Verify** PDF downloads successfully

**E2E Test validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_risk_pdf_export.md` test file to validate this functionality works.

## Notes

- This is a common issue when working with Pydantic's `Decimal` type - it serializes to strings in JSON to preserve precision, but JavaScript expects numbers.
- The fix uses `Number()` as a defensive wrapper, which works correctly for both string and number inputs.
- Consider adding a utility function like `toNumber(value: string | number): number` for consistent handling across the codebase.
- The TypeScript types (`risk_score: number`) don't catch this at compile time because the actual runtime values differ from the type annotations. This is a limitation of TypeScript when dealing with API responses.
- Alternative long-term fix: Transform API responses in the service layer to ensure numeric fields are always JavaScript numbers.
