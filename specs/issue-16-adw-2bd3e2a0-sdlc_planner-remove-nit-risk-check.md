# Bug: Remove NIT Database Existence Check and Evaluation Type Selection from Risk Assessment

## Bug Description

When starting a new risk evaluation, two issues exist:

1. **Evaluation Type Selection**: The UI presents options for "Completa" (comprehensive) or "Rápida" (quick) evaluation. This should not exist - there is only one evaluation approach which requires uploading documents for extraction and cross-validation.

2. **NIT Database Existence Check**: After entering a NIT and proceeding with the evaluation, the system immediately assigns a risk score of 75 in the "evaluacion" tab when the NIT is NOT found in the database. This check adds no value and should be removed. Risk points should only be assigned by document information cross-validation, not by whether a client exists in the database.

**Expected behavior**:
- Single evaluation approach (no full/light options)
- When a NIT is entered for a new client (not in database), the evaluation should proceed to the document upload phase with a preliminary score of 0 (or only reflecting other basic validation rules)
- Risk scores should be assigned ONLY after cross-validation of uploaded documents

**Actual behavior**:
- Two evaluation types are presented (comprehensive/quick)
- When NIT not found in database, system creates an "error assessment" with risk_score=75 and a `system_error` fraud indicator, making it appear as HIGH risk

## Problem Statement

The fraud detection service incorrectly treats "client not found in database" as a high-risk error condition, assigning 75 risk points. This penalizes new clients who haven't been onboarded yet. Additionally, the evaluation type selection (full/quick) adds unnecessary complexity when only one evaluation workflow exists.

## Solution Statement

1. **Remove evaluation type selection from UI and backend**: Eliminate the `assessment_type` field from the form, DTO, and backend processing. All evaluations will use the existing comprehensive workflow.

2. **Modify the `evaluate_client` method**: Instead of calling `_create_error_assessment` when a client is not found, create a new assessment with `pending_documents` status and zero preliminary risk score, allowing the user to proceed with document uploads for a new client.

3. **Remove `_create_error_assessment` method**: This method is no longer needed as we won't treat "client not found" as an error condition.

## Steps to Reproduce

1. Navigate to `/department/riesgo` (Risk Dashboard)
2. Click "Nueva Evaluación" button
3. Observe the dropdown showing "Completa" and "Rápida" options (BUG #1)
4. Enter a NIT that does NOT exist in the `clients` table (e.g., "999.999.999-9")
5. Click "Iniciar Evaluación"
6. Observe the risk score immediately shows 75 with "system_error" indicator (BUG #2)

## Root Cause Analysis

### Bug #1 - Evaluation Type Selection
The `FKRiskEvaluationForm.tsx` component includes a `Select` dropdown for `assessment_type` with "comprehensive" and "quick" options. The backend `RiskAssessmentRequest` DTO has an `assessment_type` field with `AssessmentType` enum. This was designed for future differentiation but is currently unused and confuses users.

### Bug #2 - NIT Risk Score of 75
In `fraud_detection_service.py`, the `evaluate_client` method checks if client data exists in the database (line 105-114):

```python
client_data = await self._get_client_data(client_nit)
if not client_data:
    return await self._create_error_assessment(
        client_nit, user_id, assessment_type,
        "Cliente no encontrado en el sistema"
    )
```

The `_create_error_assessment` method (lines 485-510) creates an assessment with `risk_score: 75.0` and a `system_error` indicator. This incorrectly treats a missing client record as high risk.

## Affected Layer

- [x] Backend: adapter/rest (API routes)
- [x] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [x] Frontend: services
- [x] Frontend: types

## Relevant Files

Use these files to fix the bug:

- **`frontend/src/components/risk/FKRiskEvaluationForm.tsx`** - Contains the evaluation type dropdown that needs to be removed (lines 103-125)
- **`frontend/src/types/risk.ts`** - Contains `AssessmentType` type definition (line 45) and `RiskAssessmentRequest` interface (lines 92-95)
- **`frontend/src/services/riskService.ts`** - Uses `RiskAssessmentRequest` to call API (line 70-73)
- **`backend/src/interface/risk_dtos.py`** - Contains `AssessmentType` enum (lines 70-73) and `RiskAssessmentRequest` (lines 98-112)
- **`backend/src/adapter/rest/risk_routes.py`** - Uses `assessment_type` in `create_evaluation` endpoint (line 235)
- **`backend/src/core/servicios/risk/fraud_detection_service.py`** - Contains `evaluate_client` method with the faulty NIT check (lines 85-157) and `_create_error_assessment` method (lines 485-510)
- **`.claude/commands/test_e2e.md`** - Reference for creating E2E test
- **`.claude/commands/e2e/test_login.md`** - Reference E2E test format
- **`.claude/commands/e2e/test_database_existence_check_removal.md`** - Related existing E2E test (may need updates)

### New Files

- **`.claude/commands/e2e/test_nit_risk_check_removal.md`** - New E2E test file to validate the bug is fixed

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Remove AssessmentType from Backend DTOs

- Open `backend/src/interface/risk_dtos.py`
- Remove the `AssessmentType` enum (lines 70-73):
  ```python
  class AssessmentType(str, Enum):
      """Type of risk assessment"""
      COMPREHENSIVE = "comprehensive"
      QUICK = "quick"
  ```
- Modify `RiskAssessmentRequest` to remove `assessment_type` field (lines 101-104):
  - Remove the import of `AssessmentType` if no longer needed
  - Remove the `assessment_type` field from the model
  - Keep only `client_nit` field
- Also check `RiskAssessmentResponse` and `RiskAssessmentDetail` - if they have `assessment_type`, consider making it optional or defaulting to "comprehensive" for backward compatibility with existing records

### Step 2: Update Backend Route Handler

- Open `backend/src/adapter/rest/risk_routes.py`
- Modify the `create_evaluation` endpoint (line 218-238):
  - Remove `request.assessment_type.value` from the call to `fraud_service.evaluate_client()`
  - Since `assessment_type` is removed from the request, don't pass it or pass a hardcoded "comprehensive" value
  ```python
  assessment = await fraud_service.evaluate_client(
      client_nit=request.client_nit,
      user_id=user_id,
      # Remove or default assessment_type
  )
  ```

### Step 3: Fix Fraud Detection Service - Remove Error Assessment for Missing Client

- Open `backend/src/core/servicios/risk/fraud_detection_service.py`
- Modify the `evaluate_client` method (lines 85-157):
  - Remove the `assessment_type` parameter (or make it optional with default "comprehensive")
  - **Critical Change**: Remove the block that calls `_create_error_assessment` when client is not found (lines 106-114)
  - Instead, when client is not found, create a new assessment with:
    - `risk_score: 0`
    - `risk_level: low`
    - `status: pending_documents`
    - Empty `fraud_indicators` or minimal informational indicator
    - No `client_data_snapshot` (since client doesn't exist yet)
  - The new logic should allow the evaluation to proceed so users can upload documents
- Remove or deprecate the `_create_error_assessment` method (lines 485-510) as it's no longer needed
- Update `_create_blacklist_assessment` if it uses `assessment_type` - set to "comprehensive"

### Step 4: Update Frontend Types

- Open `frontend/src/types/risk.ts`
- Remove `AssessmentType` type (line 45):
  ```typescript
  // REMOVE: export type AssessmentType = 'comprehensive' | 'quick';
  ```
- Update `RiskAssessmentRequest` interface (lines 92-95):
  - Remove `assessment_type?` field
  ```typescript
  export interface RiskAssessmentRequest {
    client_nit: string;
    // Remove: assessment_type?: AssessmentType;
  }
  ```

### Step 5: Remove Evaluation Type Selection from Form Component

- Open `frontend/src/components/risk/FKRiskEvaluationForm.tsx`
- Remove the import of `AssessmentType` from types (line 18)
- Remove unused MUI imports (`FormControl`, `InputLabel`, `Select`, `MenuItem`) if no longer needed
- Modify `FormData` interface (lines 26-29):
  - Remove `assessment_type` field
  ```typescript
  interface FormData {
    client_nit: string;
    // Remove: assessment_type: AssessmentType;
  }
  ```
- Update `useForm` defaultValues (lines 42-45):
  - Remove `assessment_type` default
- Update `onSubmit` handler (lines 48-54):
  - Remove `assessment_type` from the request object
- **Remove the entire Controller block for assessment_type** (lines 103-125):
  - Delete the Select dropdown component

### Step 6: Update Frontend Service

- Open `frontend/src/services/riskService.ts`
- Verify `createEvaluation` method (lines 70-73) - no changes needed if types are properly updated
- The `RiskAssessmentRequest` will now only have `client_nit`

### Step 7: Create E2E Test File

- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_database_existence_check_removal.md` to understand E2E test format
- Create new file `.claude/commands/e2e/test_nit_risk_check_removal.md` with the following test scenarios:
  1. Verify evaluation form no longer shows evaluation type dropdown
  2. Enter a NIT that does NOT exist in the database
  3. Submit the evaluation
  4. Verify preliminary risk score is 0 (not 75)
  5. Verify status is "pending_documents"
  6. Verify no "system_error" indicator exists
  7. Verify user can proceed to document upload phase
  8. Take screenshots at each step to prove the bug is fixed

### Step 8: Run Validation Commands

Execute the validation commands listed below to ensure the bug is fixed with zero regressions.

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

Before fix (reproduce the bug):
```bash
# Start servers if not running
cd frontend && npm run dev &
cd backend && python -m uvicorn main:app --reload &

# Wait for servers to start, then manually test:
# 1. Navigate to http://localhost:5173/department/riesgo
# 2. Click "Nueva Evaluación"
# 3. Observe the evaluation type dropdown (BUG #1)
# 4. Enter a non-existent NIT
# 5. Submit and observe risk score of 75 (BUG #2)
```

After fix validation:
```bash
# Backend tests
cd backend && python -m pytest

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build
```

E2E test validation:
- Read `.claude/commands/test_e2e.md`
- Read and execute `.claude/commands/e2e/test_nit_risk_check_removal.md` to validate this functionality works

## Notes

1. **Backward Compatibility**: Existing assessment records in the database may have `assessment_type` values. The response models should handle this gracefully by making the field optional or defaulting to "comprehensive".

2. **Existing Related E2E Test**: The file `.claude/commands/e2e/test_database_existence_check_removal.md` tests a related scenario about company history not affecting scores. This test may need to be reviewed to ensure it still passes after these changes.

3. **No Database Migration Required**: This bug fix only involves code changes, not database schema changes. Existing records with `assessment_type` will continue to work.

4. **Client Repository**: The `_get_client_data` method will still return `None` for non-existent clients, but we'll handle this differently by creating a valid assessment instead of an error assessment.

5. **The evaluation flow after this fix**:
   - User enters NIT → Assessment created with `status: pending_documents`, `risk_score: 0`
   - User uploads documents → Documents stored with `extraction_status: pending`
   - User triggers extraction → AI extracts data
   - User triggers cross-validation → Discrepancies calculated, final risk score updated
   - This is the correct workflow that aligns with the business requirement
