# API Integration Tests

Execute curl-based integration tests for new or modified API endpoints discovered via git diff.

## Purpose

Catch API response format issues and endpoint bugs that unit tests miss by actually calling endpoints with curl. This complements unit tests (which mock external APIs) and E2E tests (which focus on UI flows).

## Variables

BASE_URL: $1 (default: http://localhost:8000)

## Instructions

### Step 1: Check Server Availability

First, verify the backend server is running:

```bash
curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/api/health
```

If the server is not running (connection refused or non-200 status):
- Return a single failed test result indicating server is not available
- Include instructions to start the server

### Step 2: Detect Changed Route Files

Find modified route files in the current branch:

```bash
git diff origin/main --name-only | grep -E "backend/src/adapter/rest/.*_routes\.py$"
```

If no route files changed:
- Return empty results array `[]`
- This is not a failure, just nothing to test

### Step 3: Parse Endpoints from Changed Files

For each changed route file, extract endpoint definitions by:

1. Reading the file content
2. Finding all `@router.<method>("<path>")` patterns
3. Building a list of (method, path) tuples

Look for patterns like:
- `@router.get("/path")`
- `@router.post("/path")`
- `@router.put("/path/{id}")`
- `@router.delete("/path/{id}")`

### Step 4: Generate and Execute Curl Tests

For each endpoint found, generate and execute appropriate curl commands:

#### GET Endpoints
```bash
curl -s -w "\n%{http_code}" -H "Content-Type: application/json" "${BASE_URL}${path}"
```

#### POST Endpoints (without file upload)
```bash
curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d '{}' "${BASE_URL}${path}"
```

#### POST Endpoints (file upload - multipart)
Skip these for now, mark as "skipped" in results.

#### PUT/PATCH Endpoints
```bash
curl -s -w "\n%{http_code}" -X PUT -H "Content-Type: application/json" -d '{}' "${BASE_URL}${path}"
```

#### DELETE Endpoints
Skip DELETE endpoints to avoid data loss, mark as "skipped" in results.

### Step 5: Evaluate Results

For each curl execution:

1. **Extract status code** from the last line of output
2. **Evaluate success** based on status code:
   - `2xx`: Pass
   - `401/403`: Pass (auth required, expected behavior)
   - `400`: Check if it's validation error (expected for empty payload)
   - `404`: Fail (endpoint not found)
   - `500`: Fail (server error - this is what we want to catch!)
   - `502/503`: Fail (service unavailable)

3. **Check response body**:
   - Should be valid JSON (unless explicitly non-JSON endpoint)
   - Should not contain Python tracebacks
   - Should not contain "KeyError", "TypeError", "AttributeError" etc.

### Step 6: Handle Authentication

If an endpoint returns 401:
1. Check if `TEST_API_TOKEN` environment variable is set
2. If set, retry with `Authorization: Bearer ${TEST_API_TOKEN}` header
3. If not set, mark as "skipped (auth required)"

### Step 7: Report Results

Return ONLY a JSON array with test results. Do not include any other text.

## Output Format

```json
[
  {
    "test_name": "GET /api/endpoint",
    "passed": true,
    "execution_command": "curl -s ...",
    "test_purpose": "Validates endpoint returns expected response"
  },
  {
    "test_name": "POST /api/endpoint",
    "passed": false,
    "execution_command": "curl -s -X POST ...",
    "test_purpose": "Validates endpoint accepts POST requests",
    "error": "Status 500: KeyError: 0 in response"
  }
]
```

## Test Purpose Guidelines

Generate meaningful test_purpose descriptions:

| Endpoint Pattern | Test Purpose |
|------------------|--------------|
| GET /api/*/list | Validates list endpoint returns array |
| GET /api/*/{id} | Validates single item retrieval |
| POST /api/*/upload | Validates file upload endpoint |
| POST /api/* | Validates create endpoint accepts payload |
| PUT /api/*/{id} | Validates update endpoint |
| DELETE /api/*/{id} | Validates delete endpoint (skipped) |

## Error Detection Patterns

Flag these patterns in response body as errors:

- `"KeyError"` - Missing dictionary key (like our bug!)
- `"TypeError"` - Type mismatch
- `"AttributeError"` - Missing attribute
- `"ValidationError"` - Pydantic validation failed
- `"Traceback"` - Python exception traceback
- `"Internal Server Error"` - Generic 500 error

## Example Execution

```bash
# Server running at localhost:8000
# Changed file: backend/src/adapter/rest/financial_ingestion_routes.py
# Contains: @router.post("/upload/pdf")

# Generated curl:
curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  "http://localhost:8000/api/financial/upload/pdf"

# Response:
{"detail":"file field required"}
422

# Result: PASS (422 is expected for missing required field)
```

## Report

- IMPORTANT: Return results exclusively as a JSON array
- Sort failed tests first, then passed, then skipped
- Include all tested endpoints
- The execution_command field should contain the exact curl command used
