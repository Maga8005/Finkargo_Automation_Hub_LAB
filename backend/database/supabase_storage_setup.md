# Supabase Storage Setup for Contract Documents

## Overview
Approved contracts are stored in Supabase Storage to allow Operations team to download signed copies for customers.

## Setup Steps

### 1. Create Storage Bucket in Supabase

1. Go to your Supabase project: https://supabase.com/dashboard
2. Navigate to **Storage** in the left sidebar
3. Click **New Bucket**
4. Configure the bucket:
   - **Name**: `contract-documents`
   - **Public bucket**: **NO** (contracts are private)
   - **File size limit**: 10 MB (sufficient for PDFs)
   - **Allowed MIME types**: `application/pdf`

### 2. Set Up Row Level Security (RLS) Policies

Apply these policies to the `contract-documents` bucket:

#### Policy 1: Allow Authenticated Users to Upload
```sql
-- Allow authenticated users to upload approved contracts
CREATE POLICY "Allow authenticated uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'contract-documents'
);
```

#### Policy 2: Allow Authenticated Users to Read
```sql
-- Allow authenticated users to download contracts
CREATE POLICY "Allow authenticated downloads"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'contract-documents'
);
```

#### Policy 3: Prevent Deletions (Optional - for audit trail)
```sql
-- Prevent deletion of approved contracts for audit purposes
CREATE POLICY "Prevent deletions"
ON storage.objects
FOR DELETE
TO authenticated
USING (false);  -- No one can delete
```

### 3. File Naming Convention

Files are stored with the following naming pattern:
```
contracts/{contract_id}/{contract_id}_approved.pdf
```

Example:
```
contracts/2acd620a-f5b9-4603-8b8f-b2067ab0a17a/2acd620a-f5b9-4603-8b8f-b2067ab0a17a_approved.pdf
```

### 4. Environment Variables

Ensure these variables are set in your `.env` file:

```bash
# Already configured
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key  # Required for storage operations
```

### 5. Database Schema Update

Add the `approved_document_url` column to track stored documents:

```sql
-- Add column to store Supabase Storage URL
ALTER TABLE contract_generations
ADD COLUMN approved_document_url TEXT;

-- Add comment
COMMENT ON COLUMN contract_generations.approved_document_url
IS 'Supabase Storage URL for approved contract PDF';

-- Add index for faster queries
CREATE INDEX idx_contract_generations_approved_url
ON contract_generations(approved_document_url)
WHERE approved_document_url IS NOT NULL;
```

## Usage Flow

### When Legal Approves a Contract:
1. Generate PDF from DOCX template
2. Upload PDF to Supabase Storage bucket `contract-documents`
3. Store the public URL in `approved_document_url` field
4. Mark contract status as `approved`

### When Operations Downloads:
1. Query contracts with status `approved`
2. Use `approved_document_url` to fetch PDF from Supabase Storage
3. Stream PDF to browser for download

## Testing

### Test Upload (via Python):
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Upload test file
with open('test.pdf', 'rb') as f:
    result = supabase.storage.from_('contract-documents').upload(
        path='test/test.pdf',
        file=f,
        file_options={"content-type": "application/pdf"}
    )
    print(result)
```

### Test Download:
```python
# Get public URL (for authenticated access)
url = supabase.storage.from_('contract-documents').get_public_url('test/test.pdf')
print(url)

# Or download directly
result = supabase.storage.from_('contract-documents').download('test/test.pdf')
```

## Security Notes

- **Private Bucket**: Contracts contain sensitive information - keep bucket private
- **RLS Policies**: Ensure only authenticated users can access
- **Audit Trail**: Consider preventing deletions to maintain compliance records
- **Access Logs**: Supabase logs all storage access for audit purposes

## Troubleshooting

### Error: "Bucket not found"
- Verify bucket name is exactly `contract-documents`
- Check bucket exists in Supabase Storage dashboard

### Error: "Row Level Security policy violation"
- Ensure RLS policies are correctly applied
- Verify user is authenticated with valid JWT

### Error: "File too large"
- Check bucket file size limit (default 10 MB)
- Optimize PDF generation to reduce file size

### Error: "Invalid MIME type"
- Ensure file is uploaded with `content-type: application/pdf`
- Check allowed MIME types in bucket settings
