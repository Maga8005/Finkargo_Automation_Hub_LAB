# Chore: Configure Google Drive Service Account Credentials for Render Deployment

## Chore Description
The Finanzas department's Mexico reports functionality generates Excel files and ZIP packages with invoice PDFs fetched from Google Drive. Currently, the `GoogleDriveService` expects a credentials JSON file at a local path (`./credentials/drive-service-account.json`), which doesn't work on Render because:

1. Render deployments are ephemeral - local files don't persist across deploys
2. Secrets should never be committed to git repositories
3. The current implementation uses `Credentials.from_service_account_file()` which requires a physical file

The solution is to:
1. Store the service account JSON as a base64-encoded environment variable on Render
2. Modify the `GoogleDriveService` to support loading credentials from an environment variable
3. Update the settings configuration to handle both file-based (local dev) and env-based (production) credentials

## Relevant Files
Use these files to resolve the chore:

- `backend/src/config/settings.py` - Settings class that loads environment variables. Needs a new setting for the JSON credentials as a string.
- `backend/src/core/servicios/google_drive_service.py` - The service that authenticates with Google Drive. Currently uses `from_service_account_file()`, needs to support `from_service_account_info()` for env-based credentials.
- `backend/.env.example` - Example environment file. Needs documentation for the new credential variable.

### New Files
No new files need to be created. All changes are modifications to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add New Environment Variable Setting
Update `backend/src/config/settings.py` to add a new setting for JSON credentials as a string:

- Add `GOOGLE_DRIVE_CREDENTIALS_JSON: str = ""` setting to the `Settings` class
- This will hold the base64-encoded or raw JSON string of the service account credentials
- Keep `GOOGLE_DRIVE_CREDENTIALS_PATH` as a fallback for local development

### Step 2: Modify GoogleDriveService Authentication Logic
Update `backend/src/core/servicios/google_drive_service.py` to support both credential methods:

- Import `base64` and `json` modules at the top
- Modify the `authenticate()` method to:
  1. First check if `GOOGLE_DRIVE_CREDENTIALS_JSON` is set and non-empty
  2. If yes, decode the base64 string (if encoded) or parse directly as JSON
  3. Use `Credentials.from_service_account_info(credentials_dict, scopes=self.scopes)` to authenticate
  4. If `GOOGLE_DRIVE_CREDENTIALS_JSON` is empty, fall back to file-based authentication using `GOOGLE_DRIVE_CREDENTIALS_PATH`
- Add error handling for malformed JSON credentials
- Update the `__init__` method to store `settings.GOOGLE_DRIVE_CREDENTIALS_JSON`

### Step 3: Update Environment Example File
Update `backend/.env.example` to document the new credential variable:

- Add `GOOGLE_DRIVE_CREDENTIALS_JSON` with clear documentation
- Explain that it should contain the base64-encoded service account JSON
- Provide a command example for encoding: `cat credentials.json | base64`
- Note that for local development, the file-based approach can still be used

### Step 4: Configure Render Environment Variables
Document the steps to set up credentials on Render (this is a manual step):

- Go to Render Dashboard > Your Service > Environment
- Add new environment variable: `GOOGLE_DRIVE_CREDENTIALS_JSON`
- Value: Base64-encode the entire service account JSON:
  ```bash
  echo '{"type":"service_account","project_id":"api-producto-476819",...}' | base64
  ```
- Or paste the raw JSON as a single line (the code will handle both formats)
- Add `GOOGLE_DRIVE_FOLDER_ID` if not already set
- Ensure `GOOGLE_DRIVE_SCOPES` is properly set as a JSON array

### Step 5: Run Validation Commands
Execute all validation commands to ensure the changes work correctly.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -c "from src.config.settings import get_settings; s = get_settings(); print('Settings OK:', bool(s.APP_NAME))"` - Verify settings load correctly with new field
- `cd backend && python -c "from src.core.servicios.google_drive_service import GoogleDriveService; print('Import OK')"` - Verify GoogleDriveService imports without errors
- `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &` then `sleep 3 && curl -s http://localhost:8000/api/health | grep -q 'healthy' && echo 'Health check OK'` - Verify backend starts and health endpoint works
- `cd backend && pkill -f uvicorn || true` - Clean up test server

## Notes

### Credential Encoding Options
The implementation should support two formats for `GOOGLE_DRIVE_CREDENTIALS_JSON`:
1. **Base64-encoded JSON** (recommended for safety): No issues with special characters in environment variables
2. **Raw JSON string**: Works but may have issues with newlines in private keys on some systems

### Security Considerations
- Never commit the actual credentials to git
- The private key in the credentials contains newlines (`\n`) which are preserved in JSON format
- Base64 encoding is preferred as it handles all special characters cleanly

### Local Development
Developers can continue using the file-based approach:
1. Save credentials to `backend/credentials/drive-service-account.json`
2. Leave `GOOGLE_DRIVE_CREDENTIALS_JSON` empty in `.env`
3. The service will fall back to file-based authentication

### Render Deployment Steps Summary
1. Go to Render Dashboard
2. Select the backend service
3. Go to "Environment" tab
4. Add: `GOOGLE_DRIVE_CREDENTIALS_JSON` = `<base64-encoded-json>`
5. Add: `GOOGLE_DRIVE_FOLDER_ID` = `1A5fxY8LnJYs0QTO3aYHD10IuRIgebx46` (if not set)
6. Redeploy the service

### Testing Authentication
After deployment, test the Google Drive connection by:
1. Uploading an Excel file in the Finanzas > Reporteria Automatica MX page
2. Verifying the Drive sync succeeds (check logs for "Autenticación con Google Drive exitosa")
3. Generating a ZIP with invoices to confirm PDF download works
