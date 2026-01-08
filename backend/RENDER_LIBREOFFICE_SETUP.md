# Installing LibreOffice on Render

This guide explains how to enable PDF generation by installing LibreOffice on your Render web service.

## What You Need

LibreOffice is required for converting DOCX contract documents to PDF format during the contract approval workflow.

## Installation Steps

### Step 1: Update Render Build Command

In your Render dashboard:

1. Go to your backend web service: **finkargo-automation-hub**
2. Navigate to **Settings** → **Build & Deploy**
3. Change the **Build Command** from:
   ```bash
   pip install -r requirements.txt
   ```

   To:
   ```bash
   chmod +x render-build.sh && ./render-build.sh
   ```

### Step 2: Deploy Changes

1. Commit and push the `render-build.sh` file to GitHub:
   ```bash
   git add backend/render-build.sh
   git commit -m "Add LibreOffice installation script for Render"
   git push
   ```

2. Render will automatically redeploy with the new build script

### Step 3: Verify Installation

After deployment completes:

1. Check the build logs in Render dashboard
2. Look for "Installing LibreOffice" messages
3. Verify no errors during package installation

### Step 4: Re-enable PDF Generation

Once LibreOffice is installed, uncomment the PDF generation code in:

**File:** `backend/src/core/servicios/contract_service.py`

**Method:** `review_contract()`

**Line:** ~165

Uncomment the entire try-except block that generates and uploads PDFs.

## What the Build Script Does

The `render-build.sh` script:

1. ✅ Updates apt package list
2. ✅ Installs LibreOffice (headless version)
3. ✅ Installs libreoffice-writer (for DOCX support)
4. ✅ Installs Python dependencies from requirements.txt

## Expected Build Time

- **Without LibreOffice:** ~2-3 minutes
- **With LibreOffice:** ~5-7 minutes (first time)

Subsequent builds are faster due to Render's caching.

## Troubleshooting

### Build fails with "Permission denied"
- Make sure the script has execute permissions: `chmod +x render-build.sh`

### Build fails with "apt-get: command not found"
- Render uses Ubuntu/Debian by default - this should not happen
- Verify you're using a Docker-based service (not Native Environment)

### LibreOffice not found after installation
- Check build logs for "libreoffice" installation messages
- Verify the script completed without errors
- Try manually triggering a redeploy

### PDF conversion still fails
- Check backend logs for LibreOffice error messages
- Verify the path `/usr/bin/libreoffice` exists on the server
- Ensure the contract_service.py PDF code is uncommented

## Alternative: Use Docker

If the build script approach doesn't work, you can use a custom Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
```

Then change Render service to use Docker instead of Python environment.

## Cost Impact

LibreOffice installation does NOT increase costs:
- ✅ Free tier compatible
- ✅ Same instance resources
- ✅ Slightly longer build time (one-time cost)

## Security

The headless LibreOffice installation:
- ✅ No GUI components (smaller footprint)
- ✅ Only includes necessary conversion tools
- ✅ Runs in sandboxed Render environment

## Next Steps

After LibreOffice is working:

1. Test contract approval workflow end-to-end
2. Verify PDF is uploaded to Supabase Storage
3. Confirm Operations team can access approved PDFs
4. Update deployment documentation with final configuration
