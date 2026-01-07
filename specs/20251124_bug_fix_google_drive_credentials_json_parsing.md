# Bug: Google Drive Credentials JSON Parsing Failure

## Bug Description
The Finanzas module for Mexico fails to download PDF invoices from Google Drive when generating ZIP packages. The error occurs during authentication with Google Drive, specifically when parsing the `GOOGLE_DRIVE_CREDENTIALS_JSON` environment variable. The error message indicates:

```
ERROR:src.core.servicios.google_drive_service:Error al autenticar con Google Drive: Failed to parse credentials JSON: Invalid control character at: line 1 column 170 (char 169)
```

This results in:
- No PDFs or XMLs being downloaded from Google Drive
- ZIP files containing only the Excel report without invoice attachments
- Repeated authentication failures for every invoice UUID

Expected behavior: The system should successfully authenticate with Google Drive, download PDF and XML invoice files, and include them in the generated ZIP package.

Actual behavior: Authentication fails with JSON parsing error at character 169, preventing all Google Drive operations.

## Problem Statement
The `GOOGLE_DRIVE_CREDENTIALS_JSON` environment variable in Render contains invalid control characters (likely unescaped newlines in the private key) that prevent the JSON parser from correctly decoding the service account credentials. The current implementation in `google_drive_service.py` attempts to parse credentials using `json.loads()` which fails when encountering literal newline characters (LF, ASCII 10) instead of the escaped `\n` sequence.

Character 169-170 typically falls within the `private_key` field of Google service account credentials, where the RSA private key contains newlines that must be escaped in JSON format.

## Solution Statement
Enhance the `_parse_credentials_json()` method in `GoogleDriveService` to handle malformed JSON with unescaped control characters. The solution will:

1. Add pre-processing to detect and fix common control character issues before JSON parsing
2. Specifically handle unescaped newlines in the private_key field by replacing literal newlines with escaped `\n`
3. Preserve the existing base64 and raw JSON parsing logic
4. Add comprehensive error logging to identify the exact parsing issue
5. Maintain backward compatibility with correctly formatted credentials

This approach is surgical and minimal - it fixes only the JSON parsing logic without changing authentication flow, Drive API interactions, or deployment configuration.

## Steps to Reproduce
1. Set `GOOGLE_DRIVE_CREDENTIALS_JSON` environment variable in Render with credentials containing literal newlines (common when copying/pasting JSON)
2. Deploy the backend to Render
3. Navigate to Finanzas > Reporteria Automatica MX
4. Upload an Excel file with invoice data
5. Search for invoices by RFC
6. Click "Generar ZIP" button
7. Observe:
   - Render logs show repeated "Invalid control character at: line 1 column 170" errors
   - Generated ZIP contains only Excel file, no PDFs or XMLs
   - Frontend shows success but files are missing

## Root Cause Analysis
The root cause is in `/Users/danielrestrepo/Finkargo_Automation_Hub/backend/src/core/servicios/google_drive_service.py` at line 98 where `json.loads(credentials_string)` is called.

**Why it fails:**
1. Google service account JSON credentials contain an RSA private key with actual newlines
2. Valid JSON requires these newlines to be escaped as `\n` in string values
3. When setting environment variables in Render, users may paste credentials that have literal newlines instead of escaped sequences
4. Python's `json.loads()` strictly enforces JSON spec and rejects literal control characters (ASCII 0-31) in strings
5. At character 169, the parser encounters a literal newline (LF, ASCII 10) within the `private_key` field

**Why existing code doesn't handle it:**
- The base64 decode path (lines 89-92) works because base64 encoding removes control characters
- The raw JSON path (lines 97-100) assumes valid JSON but doesn't sanitize control characters
- No pre-processing exists to normalize the JSON before parsing
- Error message doesn't help users understand how to fix their credentials

**Chain of failures:**
1. `authenticate()` calls `_parse_credentials_json()` → ValueError raised
2. `search_file_by_uuid()` calls `authenticate()` → returns None for month folder
3. `get_invoice_files()` returns (None, None) for each UUID
4. `_download_invoice_files()` produces 0 PDFs and 0 XMLs
5. ZIP contains only Excel report, no invoice files

## Relevant Files
Use these files to fix the bug:

- **backend/src/core/servicios/google_drive_service.py** (lines 74-102)
  - Contains `_parse_credentials_json()` method that needs enhancement
  - Specifically line 98 where `json.loads()` fails on control characters
  - Need to add pre-processing before JSON parsing
  - Add better error logging to identify exact character/position of parsing failures

- **backend/src/config/settings.py** (lines 40-41)
  - Contains `GOOGLE_DRIVE_CREDENTIALS_JSON` setting definition
  - May need to add a comment documenting the expected format
  - No code changes required, but should verify setting is correctly defined

- **backend/.env.example**
  - Should be updated to provide clear instructions on how to properly format credentials
  - Add example showing that newlines must be escaped in JSON
  - Document both base64 and properly-escaped JSON formats

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Read Current Implementation
- Read `backend/src/core/servicios/google_drive_service.py` to understand current `_parse_credentials_json()` implementation
- Read `backend/src/config/settings.py` to verify settings configuration
- Read `backend/.env.example` to see current documentation

### Step 2: Enhance JSON Parsing with Control Character Handling
Update `backend/src/core/servicios/google_drive_service.py`:

- In `_parse_credentials_json()` method (lines 74-102):
  - Add `import re` at the top of the file if not already present
  - After base64 decode attempt (line 94), before raw JSON parsing (line 97)
  - Add pre-processing step to sanitize control characters:
    ```python
    # Sanitize control characters before JSON parsing
    # Replace literal newlines with escaped newlines in string values
    credentials_string = credentials_string.replace('\n', '\\n')
    credentials_string = credentials_string.replace('\r', '\\r')
    credentials_string = credentials_string.replace('\t', '\\t')
    ```
  - Enhance error logging at line 102 to show the problematic character:
    ```python
    except json.JSONDecodeError as e:
        # Log the position and surrounding characters for debugging
        pos = e.pos
        start = max(0, pos - 20)
        end = min(len(credentials_string), pos + 20)
        context = credentials_string[start:end]
        logger.error(f"JSON parse error at position {pos}: {e.msg}")
        logger.error(f"Context around error: ...{repr(context)}...")
        raise ValueError(f"Failed to parse credentials JSON: {str(e)}")
    ```
  - Add a debug log when raw JSON parsing succeeds to confirm which path was used

### Step 3: Update Environment Documentation
Update `backend/.env.example`:

- Add detailed comment for `GOOGLE_DRIVE_CREDENTIALS_JSON`:
  ```
  # Google Drive Service Account Credentials (for production/Render)
  # Two options:
  # 1. Base64-encoded JSON (recommended):
  #    cat credentials.json | base64 -w 0
  # 2. Raw JSON (ensure newlines are escaped):
  #    Must be single-line with \n instead of actual newlines
  #    Example: {"type":"service_account","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE..."}
  # For local development, use GOOGLE_DRIVE_CREDENTIALS_PATH instead
  GOOGLE_DRIVE_CREDENTIALS_JSON=
  ```

### Step 4: Add Validation Logging
Update `backend/src/core/servicios/google_drive_service.py`:

- In `__init__` method (around line 50):
  - Add logging to show credential source and length
  ```python
  if self.credentials_json:
      creds_length = len(self.credentials_json)
      logger.info(f"GoogleDriveService initialized with env-based credentials ({creds_length} chars)")
  ```
- In `_parse_credentials_json` after successful parsing (line 100):
  ```python
  credentials_dict = json.loads(credentials_string)
  logger.debug(f"Credentials parsed from raw JSON string (project_id: {credentials_dict.get('project_id', 'unknown')})")
  return credentials_dict
  ```

### Step 5: Run Local Tests
Before testing on Render, verify the changes work locally:

- Create a test credentials string with literal newlines:
  ```python
  test_creds = '{"type":"service_account","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE"}'
  ```
- Run Python interpreter and test the parsing:
  ```bash
  cd backend
  python3 -c "
  from src.core.servicios.google_drive_service import GoogleDriveService
  test_json = '{\"type\":\"service_account\",\"private_key\":\"-----BEGIN\\nKEY\"}'
  service = GoogleDriveService()
  result = service._parse_credentials_json(test_json)
  print('Parse test OK:', 'type' in result)
  "
  ```

### Step 6: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python3 -c "from src.core.servicios.google_drive_service import GoogleDriveService; print('Import OK')"` - Verify GoogleDriveService imports without errors
- `cd backend && python3 -c "from src.config.settings import get_settings; s = get_settings(); print('Settings OK:', hasattr(s, 'GOOGLE_DRIVE_CREDENTIALS_JSON'))"` - Verify settings contain credentials field
- `cd backend && python3 -c "import json; test='{\\"key\\":\\"value\\nwith newline\\"}'; fixed=test.replace('\\n', '\\\\n'); result=json.loads(fixed); print('Control char fix OK:', result['key'])"` - Verify newline replacement logic works
- `cd backend && python3 -m pytest test_document_generation.py -v` - Run existing tests (if they exist)
- `cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &` then `sleep 5 && curl -s http://localhost:8000/api/health && pkill -f uvicorn` - Verify backend starts without errors

## Notes

### Control Characters in JSON
JSON specification (RFC 8259) explicitly disallows unescaped control characters (U+0000 through U+001F) in strings. The most common culprits:
- `\n` (newline, ASCII 10) - appears in RSA private keys
- `\r` (carriage return, ASCII 13) - may appear in Windows-generated files
- `\t` (tab, ASCII 9) - rarely in credentials but good to handle

### Why Position 169?
Google service account JSON structure:
```json
{
  "type": "service_account",
  "project_id": "api-producto-476819",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE..."
}
```
Position ~170 is typically the first newline in the `private_key` field's PEM-formatted RSA key.

### Alternative Solutions Considered
1. **Require base64 encoding**: Would work but breaks backward compatibility and requires documentation changes
2. **Use `json.loads(credentials_string, strict=False)`: Python's json module doesn't have a `strict` parameter that disables control character checking
3. **Regex-based key replacement**: More complex, error-prone for edge cases
4. **Pre-validation with specific key parsing**: Over-engineered for this issue

**Chosen solution is best because:**
- Simple, surgical fix to the parsing logic
- Maintains backward compatibility with correct credentials
- Works for both literal newlines and other control characters
- No changes to authentication flow or API
- No deployment configuration changes needed

### Testing Strategy
After deploying the fix to Render:
1. Update `GOOGLE_DRIVE_CREDENTIALS_JSON` with the existing (problematic) credentials
2. Trigger a deployment
3. Monitor logs for "Autenticación con Google Drive exitosa"
4. Upload an Excel file in Finanzas > Reporteria Automatica MX
5. Search for invoices and generate ZIP
6. Verify logs show "Archivo encontrado" and "PDF/XML descargado"
7. Download ZIP and confirm PDFs/XMLs are included

### Security Considerations
- The fix does not expose credentials in logs (only length and project_id)
- Control character sanitization happens before JSON parsing, not after
- No credentials are stored in memory beyond the authentication process
- Base64 path remains unchanged and preferred for production
