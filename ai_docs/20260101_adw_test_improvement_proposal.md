# ADW Test Improvement Proposal: Catching Enum and Field Name Bugs

**Date:** 2026-01-01
**Reference:** `ai_docs/20260101_adw_test_improvements_enum_and_field_bugs.md`
**Author:** Claude Code

## Executive Summary

This document proposes enhancements to the ADW testing infrastructure to catch enum case mismatches and field name bugs early in the development cycle. These bugs cost significant troubleshooting time because they only manifest at runtime and often produce misleading error messages (e.g., CORS errors masking 500 Internal Server Errors).

---

## Problem Analysis

### Why Current Tests Miss These Bugs

| Bug Type | Current Test | Why It Fails to Catch |
|----------|--------------|----------------------|
| Enum case mismatch (`EmailChainValidationStatus.pending` vs `.PENDING`) | `ruff check`, `py_compile` | Linters/compilers don't execute code paths |
| Wrong field name (`user_type` vs `role`) | `npx tsc --noEmit` | Both fields exist on type, `includes()` accepts string |

### Root Cause

**Static analysis is insufficient** - Both bugs are syntactically and type-theoretically valid. They only fail at runtime when:
1. The enum member is actually accessed
2. The `includes()` check always returns `false`

---

## Proposed Solutions

### Solution 1: Enhanced Python Import Tests (Backend)

**New Test: Enum Reference Validation**

Add to `/test` command a new test that imports all route files and validates enum references by actually executing a simple import that forces Python to evaluate the code.

**Proposed Test Command:**
```bash
cd backend && python -c "
import ast
import sys
from pathlib import Path

# Import all DTOs first to get enum definitions
from src.interface.risk_dtos import *
from src.interface.legal_dtos import *

# Now import all route files - this will fail if enum references are wrong
from src.adapter.rest import risk_routes
from src.adapter.rest import legal_routes
from src.adapter.rest import operations_routes
from src.adapter.rest import auth_routes

print('All route imports OK - enum references validated')
"
```

**Why This Works:**
- Python imports execute top-level code
- Function bodies aren't executed during import, BUT...
- We can add a secondary check that uses `ast` to find enum references and validate them

**New Test File to Add:** `backend/tests/test_enum_references.py`

```python
"""
Validate all enum references use correct member names.
Catches bugs like: EmailChainValidationStatus.pending (should be .PENDING)
"""
import ast
import re
from pathlib import Path
import importlib.util
import pytest


def get_enum_members(module_path: str, enum_name: str) -> set:
    """Extract member names from an enum definition."""
    spec = importlib.util.spec_from_file_location("module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    enum_class = getattr(module, enum_name)
    return {member.name for member in enum_class}


# Define all enums and their source files
ENUM_DEFINITIONS = {
    'EmailChainValidationStatus': 'src/interface/risk_dtos.py',
    'ExternalContactValidationStatus': 'src/interface/risk_dtos.py',
    'EmailChainDiscrepancyType': 'src/interface/risk_dtos.py',
    'ExternalContactDiscrepancyType': 'src/interface/risk_dtos.py',
    'ContractType': 'src/interface/legal_dtos.py',
    'ContractStatus': 'src/interface/legal_dtos.py',
}


def test_enum_member_case_consistency():
    """Verify enum members are referenced with correct case."""
    errors = []

    # Load valid members for each enum
    valid_members = {}
    for enum_name, source_file in ENUM_DEFINITIONS.items():
        source_path = Path('backend') / source_file
        if source_path.exists():
            valid_members[enum_name] = get_enum_members(str(source_path), enum_name)

    # Scan all Python files for enum references
    for py_file in Path('backend/src').rglob('*.py'):
        content = py_file.read_text()

        for enum_name, members in valid_members.items():
            # Find all references like EnumName.member
            pattern = rf'{enum_name}\.(\w+)'
            for match in re.finditer(pattern, content):
                member = match.group(1)
                # Skip method/property calls
                if member in ['value', 'name', '__members__']:
                    continue
                if member not in members:
                    line_num = content[:match.start()].count('\n') + 1
                    errors.append(
                        f"{py_file}:{line_num}: Invalid enum member {enum_name}.{member}. "
                        f"Valid members: {sorted(members)}"
                    )

    if errors:
        pytest.fail("\n".join(errors))


def test_route_imports_succeed():
    """Verify all route modules can be imported without error."""
    route_modules = [
        'src.adapter.rest.risk_routes',
        'src.adapter.rest.legal_routes',
        'src.adapter.rest.operations_routes',
        'src.adapter.rest.auth_routes',
        'src.adapter.rest.financial_ingestion_routes',
    ]

    errors = []
    for module_path in route_modules:
        try:
            __import__(module_path.replace('/', '.').replace('\\', '.'))
        except Exception as e:
            errors.append(f"{module_path}: {type(e).__name__}: {e}")

    if errors:
        pytest.fail("\n".join(errors))
```

---

### Solution 2: Frontend Field Access Linting (Frontend)

**Problem:** TypeScript passes because `user_type` and `role` both exist on `UserProfile`.

**Solution A: Custom ESLint Rule**

Add to `frontend/.eslintrc.cjs`:

```javascript
// Custom rule to catch common field confusion
rules: {
  'no-restricted-syntax': [
    'error',
    {
      selector: "MemberExpression[property.name='user_type'][parent.type='CallExpression'][parent.callee.property.name='includes']",
      message: "user_type only contains 'funcionario'|'cliente'. Did you mean userProfile.role for role checks?"
    }
  ]
}
```

**Solution B: Runtime Development Warning**

Add to `frontend/src/hooks/useAuth.ts` or relevant context:

```typescript
// Development-only warning for common field confusion
if (import.meta.env.DEV && userProfile) {
  const roleValues = ['admin', 'risk_manager', 'mesa_control', 'legal', 'operations', 'analyst'];
  // Warn if someone accidentally checks role values against user_type
  const originalUserType = userProfile.user_type;
  Object.defineProperty(userProfile, 'user_type', {
    get() {
      // Check call stack for .includes() with role values (heuristic)
      return originalUserType;
    }
  });
}
```

**Solution C: Type-Safe Role Checking Utility**

Create `frontend/src/utils/roleUtils.ts`:

```typescript
import { UserProfile, UserRole } from '@/types';

/**
 * Type-safe role check utility.
 * Prevents accidentally using user_type for role checks.
 */
export function hasRole(userProfile: UserProfile | null, roles: UserRole[]): boolean {
  if (!userProfile?.role) return false;
  return roles.includes(userProfile.role);
}

// Usage:
// const canValidate = hasRole(userProfile, ['admin', 'risk_manager', 'mesa_control']);
```

---

### Solution 3: New `/test_static` Slash Command

Create a new slash command specifically for catching these semantic bugs.

**File:** `.claude/commands/test_static.md`

```markdown
# Static Analysis Deep Check

Execute deep static analysis to catch semantic bugs that standard linting misses.

## Purpose

Catch bugs like:
- Enum member case mismatches (UPPERCASE vs lowercase)
- Wrong field access (user_type vs role)
- Invalid attribute access patterns

## Instructions

Execute each check in order. Stop on first failure.

### Backend Static Analysis

1. **Enum Reference Validation**
   ```bash
   cd backend && python -c "
   from pathlib import Path
   import re

   # Known enums and their valid UPPERCASE members
   enums = {
       'EmailChainValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
       'ExternalContactValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
       'ContractType': ['ACTA_DE_CONSTITUCION', 'CONTRATO_SUMINISTRO', 'PAGARE', 'OTROSI', 'INVENTARIO_BODEGA'],
       'ContractStatus': ['PENDING', 'APPROVED', 'REJECTED'],
   }

   errors = []
   for py_file in Path('src').rglob('*.py'):
       content = py_file.read_text()
       for enum_name, valid_members in enums.items():
           pattern = rf'{enum_name}\.(\w+)'
           for match in re.finditer(pattern, content):
               member = match.group(1)
               if member in ['value', 'name']:
                   continue
               if member not in valid_members:
                   line = content[:match.start()].count('\n') + 1
                   errors.append(f'{py_file}:{line}: {enum_name}.{member} - valid: {valid_members}')

   if errors:
       print('ENUM ERRORS FOUND:')
       for e in errors:
           print(f'  {e}')
       exit(1)
   print('Enum references: OK')
   "
   ```

2. **Route Module Import Test**
   ```bash
   cd backend && python -c "
   import sys
   sys.path.insert(0, '.')

   # Force import of all route modules to catch runtime errors
   from src.adapter.rest import risk_routes
   from src.adapter.rest import legal_routes
   from src.adapter.rest import operations_routes
   from src.adapter.rest import auth_routes

   print('Route imports: OK')
   "
   ```

### Frontend Static Analysis

3. **Role vs UserType Field Check**
   ```bash
   cd frontend && grep -rn "user_type" src/ --include="*.tsx" --include="*.ts" | \
     grep -E "includes\(|\.user_type\s*===?\s*['\"]admin|\.user_type\s*===?\s*['\"]risk" && \
     echo "WARNING: Possible user_type/role confusion detected!" && exit 1 || \
     echo "Role field usage: OK"
   ```

4. **TypeScript Strict Mode Check**
   ```bash
   cd frontend && npx tsc --noEmit --strict
   ```

## Report

Return pass/fail for each check:
- Enum Reference Validation: PASS/FAIL
- Route Module Import Test: PASS/FAIL
- Role vs UserType Field Check: PASS/FAIL
- TypeScript Strict Mode: PASS/FAIL
```

---

### Solution 4: Enhanced `/test` Command

Add these new tests to the existing `/test` command sequence.

**Add after test #10 (Frontend Type Definitions Validation):**

```markdown
11. **Backend Enum Reference Validation**
    - Preparation Command: None
    - Command: `cd backend && python tests/test_enum_references.py`
    - test_name: "enum_reference_validation"
    - test_purpose: "Validates all enum references use correct UPPERCASE member names, catching case mismatches like Status.pending vs Status.PENDING"

12. **Backend Route Import Validation**
    - Preparation Command: None
    - Command: `cd backend && python -c "from src.adapter.rest.risk_routes import *; from src.adapter.rest.legal_routes import *; print('Routes OK')"`
    - test_name: "route_import_validation"
    - test_purpose: "Validates all route modules can be imported without AttributeError or similar runtime errors"

13. **Frontend Role Field Check**
    - Preparation Command: None
    - Command: `cd frontend && ! grep -rn "userProfile?.user_type" src/ --include="*.tsx" | grep -q "includes" || (echo "user_type/role confusion" && exit 1)`
    - test_name: "role_field_check"
    - test_purpose: "Detects accidental use of user_type field for role-based permission checks"
```

---

### Solution 5: Enhanced `/validate` Command

Add a new validation step for semantic checks.

**Add after step 6:**

```markdown
## Semantic Validation

7. **Backend Enum Validation**
   ```bash
   cd backend && python -c "
   from pathlib import Path
   import re
   enums = {
       'EmailChainValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
       'ExternalContactValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
   }
   for py_file in Path('src').rglob('*.py'):
       content = py_file.read_text()
       for enum_name, members in enums.items():
           for m in re.finditer(rf'{enum_name}\.(\w+)', content):
               if m.group(1) not in members + ['value', 'name']:
                   raise ValueError(f'{py_file}: Invalid {enum_name}.{m.group(1)}')
   print('Enum validation: OK')
   "
   ```

8. **Frontend Role Check**
   ```bash
   cd frontend && grep -rn "user_type" src/ --include="*.tsx" | grep -v "// user_type" | grep "includes" && exit 1 || echo "Role check: OK"
   ```
```

---

### Solution 6: Pre-Implementation Checklist Enhancement

Add to `implement.md` Pre-Implementation Verification section:

```markdown
### F. Enum and Field Access Verification (ALL Features)

Before using enums or permission checks:

1. **Enum Member Case**:
   - Python enums use UPPERCASE member names: `Status.PENDING`
   - NOT lowercase: `Status.pending` (WRONG!)
   - The **value** is lowercase, the **member name** is UPPERCASE

2. **Role vs UserType Field**:
   - `userProfile.role` = 'admin', 'risk_manager', 'mesa_control', etc.
   - `userProfile.user_type` = 'funcionario' or 'cliente' ONLY
   - For permission checks, ALWAYS use `.role`, NEVER `.user_type`

3. **Verification Command**:
   ```bash
   # Check your changes for these patterns
   git diff --cached | grep -E "(Status|Type)\.[a-z]+" && echo "WARN: lowercase enum member?"
   git diff --cached | grep "user_type.*includes" && echo "WARN: user_type for role check?"
   ```
```

---

### Solution 7: New `/verify_implementation` Slash Command

Create a lightweight command to run after implementation but before commit.

**File:** `.claude/commands/verify_implementation.md`

```markdown
# Verify Implementation

Quick semantic checks to run after implementing a feature, before committing.

## Purpose

Catch common implementation bugs that slip past linting:
- Enum case mismatches
- Field name confusion (user_type vs role)
- Missing imports

## Instructions

Run these checks on your changed files:

### Step 1: Get Changed Files

```bash
git diff --name-only HEAD
```

### Step 2: Check Python Files for Enum Issues

For each changed `.py` file:

```bash
# Check for lowercase enum member access
grep -n "Status\.\|Type\." $FILE | grep -E "\.(pending|validated|suspicious|critical|approved|rejected)" && \
  echo "ERROR: Use UPPERCASE enum members (e.g., .PENDING not .pending)"
```

### Step 3: Check TSX Files for Role Issues

For each changed `.tsx` file:

```bash
# Check for user_type in role checks
grep -n "user_type" $FILE | grep -E "includes|===.*admin|===.*risk" && \
  echo "ERROR: Use userProfile.role not user_type for role checks"
```

### Step 4: Test Route Imports

```bash
cd backend && python -c "
from src.adapter.rest.risk_routes import router as risk_router
print('Risk routes: OK')
"
```

## Report

- List any issues found
- Mark PASS if no issues
- If issues found, show exact file:line and suggested fix
```

---

## Implementation Priority

| Solution | Effort | Impact | Priority |
|----------|--------|--------|----------|
| 1. Enum validation test file | Medium | High | **P0 - Do First** |
| 4. Enhanced `/test` command | Low | High | **P0 - Do First** |
| 5. Enhanced `/validate` command | Low | High | **P0 - Do First** |
| 3. New `/test_static` command | Medium | Medium | P1 |
| 6. Pre-impl checklist enhancement | Low | Medium | P1 |
| 7. `/verify_implementation` command | Medium | Medium | P2 |
| 2. Frontend ESLint/type utils | Medium | Medium | P2 |

---

## Quick Wins (Immediate Implementation)

### Add to `/test` Command Now

Add this single test that would have caught both bugs:

```markdown
11. **New Endpoint Smoke Test**
    - Preparation Command: Start backend server in background
    - Command: See test_api.md logic, but run against new endpoints
    - test_name: "new_endpoint_smoke_test"
    - test_purpose: "Calls all new/modified endpoints with curl to catch 500 errors that static analysis misses"
```

### Add to `implement.md` Now

Add this verification step:

```markdown
## Post-Implementation Verification

Before marking implementation complete:

1. **Start backend**: `cd backend && uvicorn main:app --reload &`
2. **Test new endpoints with curl**:
   ```bash
   # For each new endpoint, test it returns 200 or expected 4xx
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/your/new/endpoint
   ```
3. **Check for 500 errors**: Any 500 indicates a bug
```

---

## Validation: How This Would Have Caught the Bugs

### Bug #1: Enum Case Mismatch

**Test:** `backend/tests/test_enum_references.py` would fail with:
```
risk_routes.py:2601: Invalid enum member EmailChainValidationStatus.pending.
Valid members: ['CRITICAL', 'PENDING', 'SUSPICIOUS', 'VALIDATED']
```

### Bug #2: Wrong Field Name

**Test:** Frontend role field check would fail with:
```
WARNING: Possible user_type/role confusion detected!
src/components/risk/FKEmailChainUploader.tsx:81:user_type...includes
```

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/tests/test_enum_references.py` | Create | Enum validation test |
| `.claude/commands/test.md` | Modify | Add new tests #11-13 |
| `.claude/commands/validate.md` | Modify | Add semantic checks |
| `.claude/commands/test_static.md` | Create | New static analysis command |
| `.claude/commands/verify_implementation.md` | Create | Pre-commit verification |
| `.claude/commands/implement.md` | Modify | Add verification section |
| `frontend/src/utils/roleUtils.ts` | Create | Type-safe role checking |

---

## Conclusion

The proposed improvements add **semantic validation** layers that catch bugs which syntactically valid but semantically incorrect. By implementing the P0 items (enhanced `/test` and `/validate` commands), future ADW runs will catch:

1. **Enum case mismatches** - Before code reaches production
2. **Field name confusion** - Before UI features silently break
3. **Runtime import errors** - Before CORS-masked 500 errors

Total estimated effort: 2-3 hours for P0 items.
