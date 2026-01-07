# Test Single API Endpoint

Execute a curl test against a specific API endpoint and validate the response.

## Purpose

Quickly test a single API endpoint during development or debugging. Unlike `/test_api` which tests all changed endpoints, this command focuses on one endpoint with detailed output.

## Variables

endpoint_path: $1 (required, e.g., /api/financial/upload/pdf)
method: $2 (optional, default: GET)
payload: $3 (optional, JSON payload or path to JSON file)
base_url: $4 (optional, default: http://localhost:8000)

## Instructions

### Step 1: Validate Arguments

1. `endpoint_path` is required - if missing, show usage and exit
2. `method` defaults to GET if not provided
3. `payload` can be:
   - Inline JSON string: `'{"key": "value"}'`
   - Path to JSON file: `backend/tests/fixtures/sample.json`
   - Empty for GET requests

### Step 2: Build Curl Command

Based on the method, construct the appropriate curl command:

#### GET Request
```bash
curl -v -H "Content-Type: application/json" "${base_url}${endpoint_path}"
```

#### POST/PUT/PATCH Request
```bash
curl -v -X ${method} \
  -H "Content-Type: application/json" \
  -d '${payload}' \
  "${base_url}${endpoint_path}"
```

#### Multipart (File Upload)
If payload is a file path ending in `.pdf`, `.xlsx`, `.csv`:
```bash
curl -v -X POST \
  -F "file=@${payload}" \
  "${base_url}${endpoint_path}"
```

### Step 3: Execute and Analyze

1. Execute the curl command with verbose output (`-v`)
2. Capture:
   - HTTP status code
   - Response headers
   - Response body
   - Timing information

### Step 4: Validate Response

Check for common error patterns:

| Pattern | Severity | Meaning |
|---------|----------|---------|
| Status 2xx | OK | Success |
| Status 400 | Warning | Validation error (check payload) |
| Status 401/403 | Info | Auth required |
| Status 404 | Error | Endpoint not found |
| Status 500 | Error | Server error - investigate! |
| "KeyError" in body | Error | Missing dict key |
| "TypeError" in body | Error | Type mismatch |
| "Traceback" in body | Error | Unhandled exception |

### Step 5: Report Results

Provide a detailed report:

```markdown
## Endpoint Test: ${method} ${endpoint_path}

### Request
- URL: ${base_url}${endpoint_path}
- Method: ${method}
- Payload: ${payload or "None"}

### Response
- Status: ${status_code} ${status_text}
- Time: ${response_time}ms

### Headers
${response_headers}

### Body
```json
${response_body}
```

### Analysis
- Result: PASS/FAIL
- Issues Found: ${issues or "None"}
- Suggestions: ${suggestions}
```

## Usage Examples

### Test a GET endpoint
```
/test_endpoint /api/health
```

### Test a POST endpoint with inline JSON
```
/test_endpoint /api/financial/metrics POST '{"code": "REVENUE_TOTAL", "name": "Total Revenue"}'
```

### Test a POST endpoint with file payload
```
/test_endpoint /api/financial/upload/excel POST backend/tests/fixtures/sample_pl.xlsx
```

### Test against staging server
```
/test_endpoint /api/health GET '' https://system0-hub.onrender.com
```

## Error Recovery Suggestions

If the test fails, provide actionable suggestions:

| Error | Suggestion |
|-------|------------|
| Connection refused | Start the backend server: `cd backend && uv run uvicorn main:app --reload` |
| 401 Unauthorized | Set TEST_API_TOKEN or login first |
| 404 Not Found | Check endpoint path matches route definition |
| 422 Validation Error | Check payload matches DTO schema |
| 500 Internal Error | Check backend logs for traceback |

## Report

Provide the detailed markdown report as described in Step 5. Include:
1. Full curl command used (for reproducibility)
2. Complete response
3. Pass/Fail determination
4. Any issues found
5. Suggestions for fixing failures
