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

## E2E Validation (if UI changed)

7. If changes affected UI components:
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
