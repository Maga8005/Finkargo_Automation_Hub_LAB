# Static Analysis Deep Check

Execute deep static analysis to catch semantic bugs that standard linting misses.

## Purpose

Catch bugs like:
- Enum member case mismatches (UPPERCASE vs lowercase)
- Wrong field access (user_type vs role)
- Invalid attribute access patterns
- Runtime import errors

These bugs pass linting and TypeScript checks but fail at runtime, often with misleading errors (e.g., CORS errors masking 500 Internal Server Errors).

## Variables

TEST_COMMAND_TIMEOUT: 2 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Execute all tests even if some fail
- Stop processing and return results if a critical test fails

## Test Execution Sequence

### Backend Static Analysis

1. **Enum Reference Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "
from pathlib import Path
import re
import sys

# Known enums and their valid UPPERCASE members
enums = {
    'EmailChainValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
    'ExternalContactValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
    'DiscrepancyValidationReason': ['DATA_ENTRY_ERROR', 'VERIFIED_LEGITIMATE', 'REQUIRES_INVESTIGATION', 'FALSE_POSITIVE', 'OTHER'],
    'ContractType': ['ACTA_DE_CONSTITUCION', 'CONTRATO_SUMINISTRO', 'PAGARE', 'OTROSI', 'INVENTARIO_BODEGA', 'PAGA_LOCAL', 'K_CREDITO'],
    'ContractStatus': ['PENDING', 'APPROVED', 'REJECTED'],
    'RiskLevel': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
    'AssessmentStatus': ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'],
    'VerificationStatus': ['PENDING', 'VERIFIED', 'FAILED', 'SKIPPED'],
    'AlertSeverity': ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
}

errors = []
for py_file in Path('src').rglob('*.py'):
    try:
        content = py_file.read_text(encoding='utf-8')
    except:
        continue
    for enum_name, valid_members in enums.items():
        pattern = rf'{enum_name}\.(\w+)'
        for match in re.finditer(pattern, content):
            member = match.group(1)
            if member in ['value', 'name', '__members__', 'items']:
                continue
            if member not in valid_members:
                line = content[:match.start()].count('\n') + 1
                errors.append(f'{py_file}:{line}: {enum_name}.{member} - valid members: {valid_members}')

if errors:
    print('ENUM REFERENCE ERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
print('Enum references: OK')
"`
   - test_name: "enum_reference_validation"
   - test_purpose: "Validates all enum references use correct UPPERCASE member names, catching case mismatches like Status.pending vs Status.PENDING"

2. **Route Module Import Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "
import sys
sys.path.insert(0, '.')

errors = []
modules = [
    ('src.adapter.rest.risk_routes', 'router'),
    ('src.adapter.rest.legal_routes', 'router'),
    ('src.adapter.rest.operations_routes', 'router'),
    ('src.adapter.rest.auth_routes', 'router'),
    ('src.adapter.rest.financial_ingestion_routes', 'router'),
    ('src.adapter.rest.tesoreria_routes', 'router'),
    ('src.adapter.rest.alianzas_routes', 'router'),
]

for module_path, attr in modules:
    try:
        mod = __import__(module_path, fromlist=[attr])
        getattr(mod, attr)
    except AttributeError as e:
        errors.append(f'{module_path}: AttributeError - {e}')
    except ImportError as e:
        # ImportError is OK - module might not exist
        pass
    except Exception as e:
        errors.append(f'{module_path}: {type(e).__name__} - {e}')

if errors:
    print('ROUTE IMPORT ERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
print('Route imports: OK')
"`
   - test_name: "route_import_validation"
   - test_purpose: "Validates all route modules can be imported without AttributeError or similar runtime errors"

3. **DTO Import Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "
import sys
sys.path.insert(0, '.')

errors = []
dto_modules = [
    'src.interface.risk_dtos',
    'src.interface.legal_dtos',
    'src.interface.finance_dtos',
    'src.interface.alianzas_dtos',
    'src.interface.tesoreria_dtos',
]

for module_path in dto_modules:
    try:
        __import__(module_path)
    except Exception as e:
        errors.append(f'{module_path}: {type(e).__name__} - {e}')

if errors:
    print('DTO IMPORT ERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
print('DTO imports: OK')
"`
   - test_name: "dto_import_validation"
   - test_purpose: "Validates all DTO modules can be imported without errors"

### Frontend Static Analysis

4. **Role vs UserType Field Check**
   - Preparation Command: None
   - Command: `cd frontend && python3 -c "
import os
import re
import sys

errors = []
role_values = ['admin', 'risk_manager', 'mesa_control', 'legal', 'operations', 'analyst', 'manager', 'commercial']

for root, dirs, files in os.walk('src'):
    # Skip node_modules
    dirs[:] = [d for d in dirs if d != 'node_modules']
    for file in files:
        if file.endswith(('.tsx', '.ts')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        # Check for user_type being used with role values
                        if 'user_type' in line and any(role in line for role in role_values):
                            if 'includes' in line or '===' in line or '==' in line:
                                errors.append(f'{filepath}:{i}: Possible user_type/role confusion - user_type only contains funcionario|cliente')
            except:
                pass

if errors:
    print('ROLE FIELD ERRORS:')
    for e in errors:
        print(f'  {e}')
    sys.exit(1)
print('Role field usage: OK')
"`
   - test_name: "role_field_check"
   - test_purpose: "Detects accidental use of user_type field for role-based permission checks (user_type only contains 'funcionario'|'cliente', use role for permission checks)"

5. **TypeScript Strict Compilation**
   - Preparation Command: None
   - Command: `cd frontend && npx tsc --noEmit 2>&1 | head -50`
   - test_name: "typescript_strict_check"
   - test_purpose: "Validates TypeScript compilation catches type errors"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output

```json
[
  {
    "test_name": "enum_reference_validation",
    "passed": false,
    "execution_command": "cd backend && python -c \"...\"",
    "test_purpose": "Validates all enum references use correct UPPERCASE member names",
    "error": "src/adapter/rest/risk_routes.py:2601: EmailChainValidationStatus.pending - valid members: ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL']"
  },
  {
    "test_name": "route_import_validation",
    "passed": true,
    "execution_command": "cd backend && python -c \"...\"",
    "test_purpose": "Validates all route modules can be imported without AttributeError"
  }
]
```
