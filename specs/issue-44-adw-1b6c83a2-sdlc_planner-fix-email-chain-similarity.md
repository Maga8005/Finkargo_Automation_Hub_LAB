# Bug: Email Chain Validation Missing calculate_similarity Method

## Bug Description
When validating email chains in the Fraud Risk module for process RISK-2025-034 with email address `comercial@multivalvulas.com.co`, an error occurs: `'NormalizationService' object has no attribute 'calculate_similarity'`. The email chain validation process fails because the `EmailChainService` calls methods that don't exist on `NormalizationService`.

The actual symptoms are:
- Email chain validation fails with an AttributeError
- The error message: `Error validating email chain: 'NormalizationService' object has no attribute 'calculate_similarity'`
- Risk assessors cannot complete email chain cross-validation for fraud detection

Expected behavior:
- Email chain validation should complete successfully
- Company names and representative names should be compared using similarity matching
- Validation results should be returned with appropriate discrepancy detection

## Problem Statement
The `EmailChainService` calls two methods on `NormalizationService` that do not exist:
1. `calculate_similarity()` - Called in 6 places (lines 570, 594, 597, 719, 743, 746)
2. `normalize_name()` - Called in 4 places (lines 715, 718, 744, 747)

The `NormalizationService` has `normalize_person_name()` but not `normalize_name()`, and it lacks any similarity calculation method. The `calculate_similarity()` method exists in `TyposquattingService` but the code is calling it on the wrong service.

## Solution Statement
Add the missing `calculate_similarity()` method to `NormalizationService` to provide string similarity comparison for fraud detection cross-validation. This follows the separation of concerns principle - `NormalizationService` handles data normalization AND similarity comparison for normalized data, while `TyposquattingService` handles domain-specific typosquatting detection.

Additionally, add an alias method `normalize_name()` that calls `normalize_person_name()` for backward compatibility, or update the calls to use the correct method name.

The minimal fix approach:
1. Add `calculate_similarity()` to `NormalizationService` (copy implementation from `TyposquattingService`)
2. Add `normalize_name()` alias method to `NormalizationService` that delegates to `normalize_person_name()`

## Steps to Reproduce
1. Log in to the Finkargo Automation Hub with risk_analyst or risk_manager role
2. Navigate to the Fraud Risk module (/risk)
3. Open or create a risk evaluation (e.g., RISK-2025-034)
4. Go to the Email Chain / External Contacts section
5. Upload an email chain (file or paste text)
6. Click "Validar" (Validate) button for the email chain
7. Observe the error: `Error validating email chain: 'NormalizationService' object has no attribute 'calculate_similarity'`

## Root Cause Analysis
The `EmailChainService` was implemented with calls to methods that were expected to exist on `NormalizationService` but were never added:

1. **`calculate_similarity()` missing**: In `email_chain_service.py`, the code calls `self.normalization_service.calculate_similarity()` at lines 570-571, 594-595, 597-599, 719-721, 743-745, and 746-748. However, `NormalizationService` in `normalization_service.py` does not have this method. The method exists in `TyposquattingService` at lines 232-246.

2. **`normalize_name()` missing**: The code calls `self.normalization_service.normalize_name()` at lines 715, 718, 744, and 747. The correct method in `NormalizationService` is `normalize_person_name()`.

This is an implementation oversight where the service interface was assumed but not fully implemented.

## Affected Layer
- [x] Backend: core/servicios (business logic)

## Relevant Files
Use these files to fix the bug:

- `backend/src/core/servicios/risk/normalization_service.py` - **Primary fix location**. Add `calculate_similarity()` method and `normalize_name()` alias method to this service. Currently has `normalize_person_name()` but missing the methods being called by `EmailChainService`.

- `backend/src/core/servicios/risk/email_chain_service.py` - **Reference file**. Contains the code calling the missing methods. Lines 570-571, 594-595, 597-599, 719-721, 743-745, 746-748 call `calculate_similarity()`. Lines 715, 718, 744, 747 call `normalize_name()`. No changes needed here - we'll fix the service instead.

- `backend/src/core/servicios/risk/typosquatting_service.py` - **Reference implementation**. Contains the working `calculate_similarity()` implementation at lines 232-246 that we'll adapt for `NormalizationService`.

- `backend/tests/test_normalization_service.py` - **Test file**. Add tests for the new `calculate_similarity()` and `normalize_name()` methods to ensure they work correctly and prevent future regressions.

### New Files
- `.claude/commands/e2e/test_email_chain_validation.md` - E2E test file to validate the bug fix through the UI.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add calculate_similarity() method to NormalizationService
- Open `backend/src/core/servicios/risk/normalization_service.py`
- Add the `difflib.SequenceMatcher` import at the top of the file
- Add the `calculate_similarity()` method after `_remove_accents()`:
  ```python
  def calculate_similarity(self, s1: str, s2: str) -> float:
      """
      Calculate string similarity using SequenceMatcher.

      Used for comparing normalized strings (company names, person names)
      to detect potential fraud through name variations.

      Args:
          s1: First string (normalized)
          s2: Second string (normalized)

      Returns:
          Similarity ratio between 0.0 and 1.0
      """
      if not s1 or not s2:
          return 0.0

      return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
  ```

### Step 2: Add normalize_name() alias method to NormalizationService
- In `backend/src/core/servicios/risk/normalization_service.py`
- Add `normalize_name()` method after `normalize_person_name()`:
  ```python
  def normalize_name(self, name: str) -> str:
      """
      Alias for normalize_person_name() for backward compatibility.

      Args:
          name: Raw person name

      Returns:
          Normalized name (uppercase, no accents, clean whitespace)
      """
      return self.normalize_person_name(name)
  ```

### Step 3: Add unit tests for new methods
- Open `backend/tests/test_normalization_service.py`
- Add a new test class `TestStringSimilarity` with tests for `calculate_similarity()`:
  - Test identical strings return 1.0
  - Test completely different strings return low similarity
  - Test similar strings return medium-high similarity (e.g., "AZELIS" vs "ACELIS" should be ~0.8-0.9)
  - Test empty strings return 0.0
  - Test None handling returns 0.0
- Add tests for `normalize_name()` alias in `TestPersonNameNormalization`:
  - Verify it returns same result as `normalize_person_name()`

### Step 4: Run backend tests to validate the fix
- Execute `cd backend && python -m pytest tests/test_normalization_service.py -v` to verify the new tests pass
- Execute `cd backend && python -m pytest` to ensure no regressions in other tests

### Step 5: Create E2E test file for email chain validation
- Read `.claude/commands/e2e/test_fraud_risk_module_fixes.md` and `.claude/commands/test_e2e.md` to understand the E2E test format
- Create a new E2E test file in `.claude/commands/e2e/test_email_chain_validation.md` that validates:
  - User can navigate to the Fraud Risk module
  - User can open a risk evaluation
  - User can upload an email chain (text paste)
  - User can click "Validar" button
  - Validation completes successfully without errors
  - Validation results show discrepancy analysis for company names/representative names
- Include specific steps to reproduce the original bug scenario and verify it's fixed

### Step 6: Run validation commands
- Execute all validation commands to confirm the bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -c "from src.core.servicios.risk.normalization_service import NormalizationService; s = NormalizationService(); print('calculate_similarity exists:', hasattr(s, 'calculate_similarity')); print('normalize_name exists:', hasattr(s, 'normalize_name')); print('Test similarity:', s.calculate_similarity('AZELIS', 'ACELIS'))"` - Quick verification that the new methods exist and work
- `cd backend && python -m pytest tests/test_normalization_service.py -v` - Run normalization service tests to validate new methods
- `cd backend && python -m pytest` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

After creating the E2E test file:
- Read `.claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_email_chain_validation.md` test file to validate this functionality works.

## Notes

- The fix is minimal and surgical - we add two methods to `NormalizationService` without modifying any code in `EmailChainService`
- The `calculate_similarity()` implementation is copied from `TyposquattingService` since it uses the same algorithm (SequenceMatcher)
- The `normalize_name()` alias maintains backward compatibility while reusing existing `normalize_person_name()` logic
- No new dependencies required - `difflib.SequenceMatcher` is part of Python's standard library
- The fix follows the existing code patterns and architecture in the codebase
- After the fix, email chain validation will properly compare company names and representative names extracted from emails against document-extracted data for fraud detection
