# PDF Generation Setup for Deployment

## Overview
The application uses **LibreOffice in headless mode** to convert DOCX documents to PDF. This works on Windows, Linux, and macOS without requiring Microsoft Word.

## Local Development (Windows)

### Install LibreOffice
1. Download from: https://www.libreoffice.org/download/download/
2. Install to default location (C:\Program Files\LibreOffice)
3. Restart your backend server
4. PDF generation will now work

## Render.com Deployment

### Method 1: Using Buildpacks (Recommended)
Add LibreOffice buildpack to your Render service:

1. Go to your Render dashboard
2. Select your service
3. Go to **Settings** → **Build & Deploy**
4. Add this buildpack URL:
   ```
   https://github.com/Scalingo/apt-buildpack.git
   ```
5. Create file `Aptfile` in backend directory:
   ```
   libreoffice
   libreoffice-writer
   ```

### Method 2: Using Docker (Alternative)
If using Docker on Render, add to your Dockerfile:

```dockerfile
FROM python:3.11.9-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# ... rest of your Dockerfile
```

### Method 3: Using Render Native Build
Add to your render.yaml or build command:

```bash
apt-get update && apt-get install -y libreoffice libreoffice-writer
```

## Vercel Deployment (Frontend Only)
Vercel is for frontend hosting only - it doesn't support Python backends. Keep using Render for backend.

## How It Works

1. **DOCX Generation**: Python-docx creates the Word document with populated data
2. **PDF Conversion**: LibreOffice headless mode converts DOCX → PDF
3. **Download**: PDF is streamed to the user's browser

## Fallback Strategy
If LibreOffice is not available:
- The system will raise a clear error message
- Users can still download DOCX format
- Consider alternative: Use reportlab for direct PDF generation (requires template rewrite)

## Testing LibreOffice Installation

Test from command line:

**Windows:**
```cmd
"C:\Program Files\LibreOffice\program\soffice.exe" --version
```

**Linux/Mac:**
```bash
libreoffice --version
# or
soffice --version
```

## Troubleshooting

### Error: "LibreOffice not found"
- **Local**: Install LibreOffice from official website
- **Render**: Add buildpack or install via Aptfile

### Error: "PDF conversion timed out"
- Increase timeout in `document_service.py` (currently 30 seconds)
- Check server resources (CPU/Memory)

### Error: "Permission denied"
- Ensure temp directory is writable
- Check LibreOffice executable permissions

## Performance Notes
- First conversion may be slower (LibreOffice startup)
- Subsequent conversions are faster (process reuse)
- Consider caching PDFs if generating same contract multiple times
