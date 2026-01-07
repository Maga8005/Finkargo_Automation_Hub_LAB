# Application Validation Test Suite

Execute comprehensive validation tests for both frontend and backend components, returning results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the Finkargo Automation Hub before they impact users or developers. By running this comprehensive test suite, you can:
- Detect syntax errors, type mismatches, and import failures
- Identify broken tests or security vulnerabilities  
- Verify build processes and dependencies
- Ensure the application is in a healthy state

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Execute all tests even if some fail
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
  - IMPORTANT: If a test fails, stop processing tests and return the results thus far
- Some tests may have dependencies (e.g., server must be stopped for port availability)
- Test execution order is important - dependencies should be validated first
- All file paths are relative to the project root
- Always run `pwd` and `cd` before each test to ensure you're operating in the correct directory for the given test

## Test Execution Sequence

### Backend Tests

1. **Python Syntax Check**
   - Preparation Command: None
   - Command: `cd backend && python -m py_compile src/main.py`
   - test_name: "python_syntax_check"
   - test_purpose: "Validates Python syntax by compiling main entry point, catching syntax errors like missing colons, invalid indentation, or malformed statements"

2. **Backend Code Quality Check**
   - Preparation Command: None
   - Command: `cd backend && ./venv/bin/ruff check src/`
   - test_name: "backend_linting"
   - test_purpose: "Validates Python code quality, identifies unused imports, style violations, and potential bugs"

3. **All Backend Tests**
   - Preparation Command: None
   - Command: `cd backend && python -m pytest -v --tb=short`
   - test_name: "all_backend_tests"
   - test_purpose: "Validates all backend functionality including contract generation, document services, API endpoints, and business logic"

### Frontend Tests

4. **Frontend Linting**
   - Preparation Command: None
   - Command: `cd frontend && npm run lint`
   - test_name: "frontend_linting"
   - test_purpose: "Validates frontend code quality with ESLint, catching style issues and potential bugs"

5. **TypeScript Type Check**
   - Preparation Command: None
   - Command: `cd frontend && npx tsc --noEmit`
   - test_name: "typescript_check"
   - test_purpose: "Validates TypeScript type correctness without generating output files, catching type errors, missing imports, and incorrect function signatures"

6. **Frontend Build**
   - Preparation Command: None
   - Command: `cd frontend && npm run build`
   - test_name: "frontend_build"
   - test_purpose: "Validates the complete frontend build process including Vite bundling, asset optimization, and production compilation"

### Runtime Verification Tests (Post-Build Validation)

7. **DTO Import Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "from src.interface.legal_dtos import *; print('DTOs OK')"`
   - test_name: "dto_import_validation"
   - test_purpose: "Validates all DTO definitions are syntactically correct and importable without errors"

8. **Document Service Import Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "from src.core.servicios.document_service import DocumentService; print('DocumentService OK')"`
   - test_name: "document_service_import"
   - test_purpose: "Validates document service can be imported without errors, catching missing dependencies or syntax issues"

9. **Repository Layer Validation**
   - Preparation Command: None
   - Command: `cd backend && python -c "from src.repositorio.client_repository import ClientRepository; from src.repositorio.contract_repository import ContractRepository; print('Repositories OK')"`
   - test_name: "repository_import_validation"
   - test_purpose: "Validates repository layer imports correctly, catching circular dependencies or missing modules"

10. **Frontend Type Definitions Validation**
    - Preparation Command: None
    - Command: `cd frontend && npx tsc --noEmit src/types/legal.ts src/types/index.ts`
    - test_name: "frontend_types_validation"
    - test_purpose: "Validates frontend type definitions specifically, catching interface mismatches early"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

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
    "test_name": "frontend_build",
    "passed": false,
    "execution_command": "cd frontend && npm run build",
    "test_purpose": "Validates the complete frontend build process including Vite bundling, asset optimization, and production compilation",
    "error": "TS2345: Argument of type 'string' is not assignable to parameter of type 'number'"
  },
  {
    "test_name": "all_backend_tests",
    "passed": true,
    "execution_command": "cd backend && python -m pytest -v --tb=short",
    "test_purpose": "Validates all backend functionality including contract generation, document services, API endpoints, and business logic"
  }
]
```
