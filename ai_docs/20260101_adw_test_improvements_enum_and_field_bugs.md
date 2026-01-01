# ADW Test Improvements: Enum Case and Field Name Bugs

**Date:** 2026-01-01
**Feature:** External Communication Validation Comments (ADW 584b6bdd)
**Related Files:** `backend/src/adapter/rest/risk_routes.py`, `frontend/src/components/risk/FKEmailChainUploader.tsx`, `frontend/src/components/risk/FKExternalContactTab.tsx`

## Executive Summary

During the implementation of feature ADW-584b6bdd (External Communication Validation Comments), several bugs were introduced that were not caught by the existing test/validation process. This document catalogs these bugs and provides recommendations for improving ADW testing to catch similar issues in the future.

---

## Bug #1: Enum Member Case Mismatch (Backend)

### Description
Python enums were defined with **UPPERCASE** member names, but code referenced them with **lowercase** names, causing `AttributeError` at runtime.

### Affected Code

**Enum Definition** (`backend/src/interface/risk_dtos.py`):
```python
class EmailChainValidationStatus(str, Enum):
    PENDING = "pending"      # Member name is UPPERCASE
    VALIDATED = "validated"
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"

class ExternalContactValidationStatus(str, Enum):
    PENDING = "pending"      # Member name is UPPERCASE
    VALIDATED = "validated"
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"
```

**Buggy Code** (`backend/src/adapter/rest/risk_routes.py`):
```python
# WRONG - lowercase member names don't exist
EmailChainValidationStatus.pending      # AttributeError!
EmailChainValidationStatus.validated    # AttributeError!
ExternalContactValidationStatus.pending # AttributeError!
```

**Correct Code**:
```python
# CORRECT - uppercase member names
EmailChainValidationStatus.PENDING
EmailChainValidationStatus.VALIDATED
ExternalContactValidationStatus.PENDING
```

### Lines Affected
| File | Line | Before | After |
|------|------|--------|-------|
| risk_routes.py | 2601 | `EmailChainValidationStatus.pending` | `EmailChainValidationStatus.PENDING` |
| risk_routes.py | 2623 | `EmailChainValidationStatus.pending` | `EmailChainValidationStatus.PENDING` |
| risk_routes.py | 2624 | `EmailChainValidationStatus.validated` | `EmailChainValidationStatus.VALIDATED` |
| risk_routes.py | 2794 | `ExternalContactValidationStatus.pending` | `ExternalContactValidationStatus.PENDING` |
| risk_routes.py | 2818 | `ExternalContactValidationStatus.pending` | `ExternalContactValidationStatus.PENDING` |
| risk_routes.py | 2819 | `ExternalContactValidationStatus.validated` | `ExternalContactValidationStatus.VALIDATED` |

### Symptom
- Browser shows **CORS error** (misleading!)
- Backend returns **500 Internal Server Error**
- Actual error: `AttributeError: type object 'EmailChainValidationStatus' has no attribute 'pending'`

### Root Cause
The implementer confused enum **values** (lowercase strings like `"pending"`) with enum **member names** (uppercase identifiers like `PENDING`).

### Why It Wasn't Caught
1. **No unit tests** for the new endpoints
2. **Linting (ruff)** doesn't catch invalid enum member access
3. **Type checking** would catch this if strict, but Python enums are tricky
4. **Manual testing** wasn't performed before marking feature complete

---

## Bug #2: Wrong Field Name for Role Check (Frontend)

### Description
Frontend code checked `userProfile.user_type` instead of `userProfile.role` to determine if user can validate discrepancies. Since `user_type` only contains `'funcionario'` or `'cliente'`, the check always failed.

### Affected Code

**Type Definition** (`frontend/src/types/index.ts`):
```typescript
export type UserType = 'funcionario' | 'cliente';  // Only these two values!

export type UserRole = 'admin' | 'risk_manager' | 'mesa_control' | ...;  // Many roles

export interface UserProfile {
  role: UserRole;        // Contains 'admin', 'risk_manager', etc.
  user_type: UserType;   // Contains 'funcionario' or 'cliente'
  // ...
}
```

**Buggy Code** (`FKEmailChainUploader.tsx` and `FKExternalContactTab.tsx`):
```typescript
// WRONG - user_type is never 'admin', 'risk_manager', or 'mesa_control'
const canValidate = userProfile?.user_type &&
  ['admin', 'risk_manager', 'mesa_control'].includes(userProfile.user_type);
// Always returns false!
```

**Correct Code**:
```typescript
// CORRECT - role contains the actual role values
const canValidate = userProfile?.role &&
  ['admin', 'risk_manager', 'mesa_control'].includes(userProfile.role);
```

### Lines Affected
| File | Line | Before | After |
|------|------|--------|-------|
| FKEmailChainUploader.tsx | 81-82 | `userProfile?.user_type` | `userProfile?.role` |
| FKExternalContactTab.tsx | 93-94 | `userProfile?.user_type` | `userProfile?.role` |

### Symptom
- Validation controls (expand button, form) **never appear** for any user
- No error messages - feature silently doesn't work
- User sees discrepancies but cannot interact with them

### Root Cause
The implementer confused two similarly-named fields:
- `user_type`: Distinguishes internal employees (`funcionario`) from external clients (`cliente`)
- `role`: Contains the actual permission role (`admin`, `risk_manager`, `mesa_control`, etc.)

### Why It Wasn't Caught
1. **TypeScript compilation passed** because both fields exist and `includes()` accepts `string`
2. **No E2E test** that verifies validation controls appear for authorized users
3. **Manual testing** wasn't performed with correct role verification
4. **No runtime warning** when the condition always fails

---

## Recommendations for ADW Test Improvements

### 1. Add Enum Validation Tests

**Create a test that validates all enum references at import time:**

```python
# tests/test_enum_references.py
import ast
import re
from pathlib import Path

def test_enum_member_case_consistency():
    """Verify enum members are referenced with correct case."""

    # Define enums and their valid members
    enums = {
        'EmailChainValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
        'ExternalContactValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
    }

    # Scan all Python files for enum references
    for py_file in Path('src').rglob('*.py'):
        content = py_file.read_text()
        for enum_name, valid_members in enums.items():
            # Find all references like EnumName.member
            pattern = rf'{enum_name}\.(\w+)'
            for match in re.finditer(pattern, content):
                member = match.group(1)
                # Skip if it's a method call like .value
                if member in ['value', 'name']:
                    continue
                assert member in valid_members, \
                    f"{py_file}:{match.start()}: Invalid enum member {enum_name}.{member}. " \
                    f"Valid members: {valid_members}"
```

### 2. Add Integration Tests for New Endpoints

**Test that endpoints return 200, not 500:**

```python
# tests/test_risk_routes_integration.py
import pytest

@pytest.mark.asyncio
async def test_email_chains_with_validations_endpoint(client, auth_headers):
    """Test that email-chains-with-validations endpoint returns valid response."""
    response = await client.get(
        "/api/risk/evaluations/test-uuid/email-chains-with-validations",
        headers=auth_headers
    )
    # Should not be 500!
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

@pytest.mark.asyncio
async def test_external_contacts_with_validations_endpoint(client, auth_headers):
    """Test that external-contacts-with-validations endpoint returns valid response."""
    response = await client.get(
        "/api/risk/evaluations/test-uuid/external-contacts-with-validations",
        headers=auth_headers
    )
    assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
```

### 3. Add Frontend Field Access Verification

**Add ESLint rule or test to catch field confusion:**

```typescript
// In ESLint config or as a custom rule
// Warn when checking role-like values against user_type

// Or add a runtime assertion in development:
if (process.env.NODE_ENV === 'development') {
  if (userProfile?.user_type &&
      ['admin', 'risk_manager', 'mesa_control', 'risk_analyst'].includes(userProfile.user_type)) {
    console.error('WARNING: Checking role values against user_type field. Did you mean userProfile.role?');
  }
}
```

### 4. Add E2E Test for Validation UI Visibility

**Create E2E test that verifies validation controls appear:**

```markdown
# .claude/commands/e2e/test_validation_controls_visibility.md

## Test: Validation Controls Visibility

### Prerequisites
- User logged in with 'admin' role
- Risk evaluation with email chain discrepancies exists

### Steps
1. Navigate to risk evaluation detail page
2. Click on "Contacto Externo" tab
3. Expand "Cadenas de Email" accordion
4. Verify email chain with discrepancies is visible
5. **CRITICAL**: Verify expand button (↓) is visible on discrepancy rows
6. Click expand button
7. Verify validation form appears with:
   - "Razón de validación" dropdown
   - "Comentarios" text field
   - "Guardar Validación" button

### Expected Result
- Validation controls are visible and functional for admin users
- Screenshot showing expanded validation form
```

### 5. Add Pre-Implementation Checklist for ADW

Add these checks to the ADW implementation workflow:

```markdown
## Pre-Merge Checklist

### Backend Changes
- [ ] All new enum references use UPPERCASE member names (not lowercase values)
- [ ] New endpoints tested manually with curl/Postman returning 200
- [ ] No 500 errors in backend logs when accessing new endpoints

### Frontend Changes
- [ ] Role/permission checks use `userProfile.role` (not `user_type`)
- [ ] New UI elements manually verified to appear for authorized users
- [ ] Console shows no errors when using new features

### Integration
- [ ] Refresh browser and verify no CORS errors
- [ ] Test with actual user account (not just assumptions about data)
```

### 6. Add Static Analysis for Common Mistakes

**Python - mypy strict mode:**
```python
# pyproject.toml
[tool.mypy]
strict = true
warn_unused_ignores = true
```

**TypeScript - stricter checks:**
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

---

## Summary of Testing Gaps

| Bug | Type | Could Be Caught By |
|-----|------|-------------------|
| Enum case mismatch | Backend | Unit test, integration test, manual curl test |
| Wrong field name | Frontend | E2E test, manual testing with role verification |

## Action Items

1. **Immediate**: Add integration tests for all new API endpoints
2. **Short-term**: Create enum validation test utility
3. **Medium-term**: Add E2E tests for permission-gated UI features
4. **Long-term**: Implement stricter static analysis in CI/CD pipeline

---

## Files Changed to Fix These Bugs

```
backend/src/adapter/rest/risk_routes.py    | 6 enum references fixed
frontend/src/components/risk/FKEmailChainUploader.tsx | 1 field name fixed
frontend/src/components/risk/FKExternalContactTab.tsx | 1 field name fixed
```

Total: 8 bugs fixed across 3 files
