# Quick Validation

Run all validation checks for the Finkargo Automation Hub and resolve any issues.

## Purpose

Quick closed-loop validation to ensure code quality before committing or after making changes.

## Instructions

Run in order, top to bottom. If any command fails:
1. Stop immediately
2. Read the error output
3. Fix the issue
4. Rerun ALL validation commands from step 1
5. Continue only when ALL pass

## Backend Validation

1. **Backend Linting**
   ```bash
   cd backend && ruff check src/
   ```

2. **Backend Tests**
   ```bash
   cd backend && python -m pytest
   ```

3. **Python Syntax Check**
   ```bash
   cd backend && python -m py_compile src/main.py
   ```

## Frontend Validation

4. **Frontend Linting**
   ```bash
   cd frontend && npm run lint
   ```

5. **TypeScript Type Check**
   ```bash
   cd frontend && npx tsc --noEmit
   ```

6. **Frontend Build**
   ```bash
   cd frontend && npm run build
   ```

## Semantic Validation (Catches Runtime Bugs)

These checks catch bugs that pass linting but fail at runtime.

7. **Backend Enum Validation**
   ```bash
   cd backend && python -c "
from pathlib import Path
import re
import sys
enums = {
    'EmailChainValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
    'ExternalContactValidationStatus': ['PENDING', 'VALIDATED', 'SUSPICIOUS', 'CRITICAL'],
    'ContractType': ['ACTA_DE_CONSTITUCION', 'CONTRATO_SUMINISTRO', 'PAGARE', 'OTROSI', 'INVENTARIO_BODEGA', 'PAGA_LOCAL', 'K_CREDITO'],
    'ContractStatus': ['PENDING', 'APPROVED', 'REJECTED'],
}
errors = []
for py_file in Path('src').rglob('*.py'):
    content = py_file.read_text()
    for enum_name, members in enums.items():
        for m in re.finditer(rf'{enum_name}\.(\w+)', content):
            if m.group(1) not in members + ['value', 'name']:
                errors.append(f'{py_file}: Invalid {enum_name}.{m.group(1)}')
if errors:
    for e in errors: print(e)
    sys.exit(1)
print('Enum validation: OK')
"
   ```

8. **Frontend Role Field Check**
   ```bash
   cd frontend && ! grep -rn "user_type" src/ --include="*.tsx" | grep -v "// user_type" | grep "includes" | grep -E "admin|risk_manager|mesa_control" || echo "Role check: OK"
   ```

## E2E Validation (if UI changed)

9. If changes affected UI components:
   - Read `.claude/commands/test_e2e.md`
   - Execute relevant e2e test from `.claude/commands/e2e/`

## Resolution Rule

If ANY command fails:
- Read the error output carefully
- Make minimal fix to resolve the issue
- Return to step 1 and rerun ALL commands
- Do not proceed until all 6 (or 7) steps pass

## Report

- List which validations passed
- If any failed and were fixed, summarize the fix
- Confirm all validations now pass
