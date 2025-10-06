# Operations Workflow Guide
**Approved Contract Download System**

## Overview

This system allows approved contracts to be automatically stored in Supabase Storage and made available for Operations to download and send to customers for signature.

## Workflow

### 1. Legal Approval Process

When Legal approves a contract, the system automatically:

1. **Generates PDF** from the DOCX template
2. **Converts to PDF** using LibreOffice headless mode
3. **Uploads to Supabase Storage** in the `contract-documents` bucket
4. **Stores the URL** in the `approved_document_url` field
5. **Updates contract status** to `approved`

```
┌─────────────┐
│ Legal       │
│ Approves    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Generate DOCX       │
│ from template       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Convert to PDF      │
│ (LibreOffice)       │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Upload to Supabase  │
│ Storage             │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Store URL in DB     │
│ approved_document   │
│ _url field          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Available for       │
│ Operations          │
└─────────────────────┘
```

### 2. Operations Access

Operations can access approved contracts through:

**API Endpoint:**
```
GET /api/legal/contracts/approved
```

**Response:**
```json
[
  {
    "id": "uuid",
    "contract_id": "2025-001",
    "client_nit": "900123459-1",
    "status": "approved",
    "generated_at": "2025-01-15T10:30:00Z",
    "reviewed_at": "2025-01-15T14:00:00Z",
    "reviewed_by": null,
    "approved_document_url": "https://[project].supabase.co/storage/v1/object/public/contract-documents/contracts/uuid/uuid_approved.pdf",
    "data_snapshot": {
      "nombre_importador": "ACME Corp",
      "cupo_plataforma": 50000000,
      ...
    }
  }
]
```

## Database Setup

### Required Migrations

#### 1. Add `approved_document_url` Column

Run this SQL in Supabase SQL Editor:

```sql
-- Add column to store Supabase Storage URL for approved contracts
ALTER TABLE contract_generations
ADD COLUMN approved_document_url TEXT;

-- Add comment explaining the column
COMMENT ON COLUMN contract_generations.approved_document_url
IS 'Supabase Storage URL for approved contract PDF. Populated when contract is approved by Legal.';

-- Add index for faster queries on approved contracts with documents
CREATE INDEX idx_contract_generations_approved_url
ON contract_generations(approved_document_url)
WHERE approved_document_url IS NOT NULL;
```

File: `backend/database/migration_add_approved_document_url.sql`

### Required Supabase Storage Setup

#### 1. Create Storage Bucket

1. Go to Supabase Dashboard → Storage
2. Click "New Bucket"
3. Configure:
   - **Name:** `contract-documents`
   - **Public:** NO (private bucket)
   - **File size limit:** 10 MB
   - **Allowed MIME types:** `application/pdf`

#### 2. Set Up Row Level Security Policies

```sql
-- Allow authenticated users to upload approved contracts
CREATE POLICY "Allow authenticated uploads"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'contract-documents'
);

-- Allow authenticated users to download contracts
CREATE POLICY "Allow authenticated downloads"
ON storage.objects
FOR SELECT
TO authenticated
USING (
  bucket_id = 'contract-documents'
);

-- Prevent deletion of approved contracts for audit purposes
CREATE POLICY "Prevent deletions"
ON storage.objects
FOR DELETE
TO authenticated
USING (false);  -- No one can delete
```

File: `backend/database/supabase_storage_setup.md`

## File Storage Structure

Approved contracts are stored with this naming pattern:

```
contracts/{contract_id}/{contract_id}_approved.pdf
```

Example:
```
contracts/2acd620a-f5b9-4603-8b8f-b2067ab0a17a/2acd620a-f5b9-4603-8b8f-b2067ab0a17a_approved.pdf
```

## API Endpoints

### For Operations Team

#### Get All Approved Contracts
```http
GET /api/legal/contracts/approved
```

Returns all approved contracts with document URLs, sorted by review date (newest first).

**Response Fields:**
- `approved_document_url`: Direct link to PDF in Supabase Storage
- `status`: Will always be "approved"
- `reviewed_at`: When Legal approved the contract
- `data_snapshot`: Frozen copy of client data at approval time

### For Legal Team

#### Review Contract (Approve/Reject)
```http
POST /api/legal/contracts/{contract_id}/review
Content-Type: application/json

{
  "action": "approve",
  "notes": "All documentation verified"
}
```

When `action` is "approve", the system automatically generates and uploads the PDF.

## Code Changes Summary

### 1. DocumentService (`document_service.py`)

Added:
- `supabase_client` parameter to constructor
- `upload_to_storage()` method for uploading PDFs to Supabase Storage

```python
def upload_to_storage(self, pdf_bytes: bytes, contract_id: str) -> str:
    """Upload approved contract PDF to Supabase Storage"""
    # Uploads to: contracts/{contract_id}/{contract_id}_approved.pdf
    # Returns: Public URL
```

### 2. ContractService (`contract_service.py`)

Updated `review_contract()` method:
- When contract is approved:
  1. Generate DOCX
  2. Convert to PDF
  3. Upload to Supabase Storage
  4. Store URL in database

```python
if action == ContractReviewAction.APPROVE:
    # Generate DOCX
    docx_bytes = self.document_service.generate_contract_document(contract_data)

    # Convert to PDF
    pdf_bytes = self.document_service.convert_to_pdf(docx_bytes)

    # Upload to Storage
    approved_document_url = self.document_service.upload_to_storage(
        pdf_bytes, contract['id']
    )
```

### 3. ContractRepository (`contract_repository.py`)

Added:
- `approved_document_url` parameter to `update_status()` method
- `get_approved_contracts()` method for Operations

```python
async def get_approved_contracts(self) -> List[dict]:
    """Get all approved contracts with document URLs for Operations team"""
    return self.db.table('contract_generations')\
        .select('*')\
        .eq('status', 'approved')\
        .order('reviewed_at', desc=True)\
        .execute()
```

### 4. DTOs (`legal_dtos.py`)

Added `approved_document_url` field to:
- `ContractGenerationResponse`
- `ContractGenerationDetail`

```python
approved_document_url: Optional[str] = None
```

### 5. API Routes (`legal_routes.py`)

Added:
- New endpoint: `GET /api/legal/contracts/approved`
- Updated dependency injection to pass Supabase client to DocumentService

## Testing the Workflow

### 1. Setup (One-time)

```bash
# 1. Run database migration
# Execute SQL from: backend/database/migration_add_approved_document_url.sql

# 2. Create Supabase Storage bucket
# Follow instructions in: backend/database/supabase_storage_setup.md

# 3. Install LibreOffice (for PDF generation)
# Download from: https://www.libreoffice.org/download/download/
```

### 2. Test the Complete Workflow

#### Step 1: Generate a Contract
```bash
curl -X POST http://localhost:8000/api/legal/contracts/generate \
  -H "Content-Type: application/json" \
  -d '{"client_nit": "900123459-1"}'
```

#### Step 2: Legal Approves Contract
```bash
curl -X POST http://localhost:8000/api/legal/contracts/{contract_id}/review \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "notes": "Approved for customer signature"
  }'
```

Expected behavior:
- ✅ PDF is generated
- ✅ PDF is uploaded to Supabase Storage
- ✅ `approved_document_url` is populated in database
- ✅ Contract status is "approved"

#### Step 3: Operations Views Approved Contracts
```bash
curl http://localhost:8000/api/legal/contracts/approved
```

Expected response:
```json
[
  {
    "id": "...",
    "contract_id": "2025-001",
    "status": "approved",
    "approved_document_url": "https://[project].supabase.co/storage/v1/object/public/contract-documents/contracts/uuid/uuid_approved.pdf",
    ...
  }
]
```

#### Step 4: Operations Downloads PDF
The `approved_document_url` can be used directly to download the PDF:
```bash
curl -o contract.pdf "{approved_document_url}"
```

## Security Considerations

### 1. Private Bucket
- Contracts contain sensitive financial information
- Bucket is configured as **private**
- Only authenticated users can access

### 2. Row Level Security
- Upload policy: Authenticated users only
- Download policy: Authenticated users only
- Delete policy: No one (audit trail)

### 3. Audit Trail
- All approvals are logged with timestamps
- Document URLs are immutable once set
- Deletions are prevented to maintain compliance records

## Troubleshooting

### PDF Upload Fails

**Error:** "Supabase client not configured for storage operations"

**Solution:** Ensure `get_contract_service()` in `legal_routes.py` passes Supabase client to DocumentService:
```python
supabase = get_supabase_client()
document_service = DocumentService(supabase_client=supabase)
```

### PDF Generation Fails

**Error:** "LibreOffice not found"

**Solution:** Install LibreOffice from https://www.libreoffice.org/download/download/

### Bucket Not Found

**Error:** "Bucket 'contract-documents' not found"

**Solution:** Create the bucket in Supabase Dashboard → Storage

### Permission Denied

**Error:** "Row Level Security policy violation"

**Solution:** Verify RLS policies are correctly applied (see `supabase_storage_setup.md`)

## Performance Notes

- PDF generation: ~2-5 seconds (includes LibreOffice conversion)
- Storage upload: ~1-2 seconds (depends on file size)
- Total approval time: ~3-7 seconds

## Future Enhancements

### Planned Features:
1. **Email Notification:** Notify Operations when contract is approved
2. **Bulk Download:** Download multiple approved contracts as ZIP
3. **Customer Portal:** Allow customers to download their contracts directly
4. **Digital Signature Integration:** DocuSign/Adobe Sign integration
5. **Expiration Tracking:** Alert when contracts are expiring

## Support

For questions or issues:
1. Check this documentation
2. Review `backend/database/supabase_storage_setup.md`
3. Check `backend/DEPLOYMENT_PDF_SETUP.md` for PDF generation issues
4. Contact development team

## Summary of Files Changed

| File | Changes |
|------|---------|
| `document_service.py` | Added `upload_to_storage()` method |
| `contract_service.py` | Updated `review_contract()` to upload PDFs on approval |
| `contract_repository.py` | Added `get_approved_contracts()` and updated `update_status()` |
| `legal_dtos.py` | Added `approved_document_url` field to response models |
| `legal_routes.py` | Added `/contracts/approved` endpoint |

### New Files Created:
- `backend/database/migration_add_approved_document_url.sql`
- `backend/database/supabase_storage_setup.md`
- `backend/OPERATIONS_WORKFLOW_GUIDE.md` (this file)

---

**Last Updated:** 2025-10-05
**Version:** 1.0
