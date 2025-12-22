# Feature: AI-Powered Document Cross-Validation for Fraud Detection

## Feature Description
Enhance the existing Fraud Detection Risk Module with AI-powered document extraction and cross-validation capabilities. This feature enables risk analysts to upload multiple documents (financial statements, legal representative ID, shareholder composition, RUT, and existence certificate) and automatically detect discrepancies between them using LandingAI's ADE (Agentic Document Extraction) API.

Based on the Azelis fraud case analysis, the system will cross-validate critical data points across documents to detect:
- Company name inconsistencies (e.g., "ROCSA COLOMBIA S.A." vs "AZELIS COLOMBIA S.A.S.")
- NIT mismatches across documents
- Legal representative identity inconsistencies
- Shareholder data discrepancies
- Email domain typosquatting (e.g., "acelis.com.co" vs "azelis.com")
- Financial statement anomalies between periods

## User Story
As a Risk Analyst
I want to upload multiple client documents and have them automatically analyzed for cross-document discrepancies
So that I can detect potential fraud attempts through document inconsistencies

## Problem Statement
The current fraud detection system evaluates clients based on data already in the database (NIT format, email domain, blacklist). It lacks the ability to:
1. Accept document uploads for fraud analysis
2. Extract data from different document types using AI
3. Cross-validate extracted data between documents
4. Identify discrepancies that may indicate document manipulation or fraud

The Azelis fraud case demonstrated that fraudsters combine legitimate and fake documents, making single-document verification insufficient. Cross-validation across multiple document types is essential for detecting sophisticated fraud attempts.

## Solution Statement
Implement a document-based fraud evaluation workflow that:
1. Allows uploading 5 document types: Financial Statements (2 years), Cedula, Composicion Accionaria, RUT, and Certificado de Existencia
2. Uses LandingAI ADE to extract structured data from each document
3. Compares extracted data across all documents to identify discrepancies
4. Generates a detailed cross-validation report with specific discrepancies highlighted
5. Integrates findings into the existing risk scoring system
6. Displays results in an enhanced evaluation detail view

## Access Control
- Required Role(s): `risk_analyst`, `risk_manager`, `admin`
- Backend Protection: `require_risk_role` dependency (existing in `rbac_dependencies.py`)
- Frontend Protection: Existing `RoleProtectedRoute` for `/risk/*` routes

## Relevant Files
Use these files to implement the feature:

**Backend - Existing Risk Services:**
- `backend/src/core/servicios/risk/fraud_detection_service.py` - Core fraud detection logic (add document analysis integration)
- `backend/src/core/servicios/risk/risk_scoring_service.py` - Risk scoring algorithm (extend for document discrepancies)
- `backend/src/core/servicios/risk/alert_service.py` - Alert generation (no changes needed)

**Backend - LandingAI Integration:**
- `backend/src/core/servicios/landingai_rut_parser_service.py` - Existing LandingAI integration pattern (reference)
- `backend/src/config/settings.py` - LandingAI API configuration (already configured)

**Backend - API Routes:**
- `backend/src/adapter/rest/risk_routes.py` - Risk API endpoints (add document upload and analysis endpoints)

**Backend - DTOs:**
- `backend/src/interface/risk_dtos.py` - Risk DTOs (add document extraction schemas)

**Backend - Repository:**
- `backend/src/repositorio/risk_repository.py` - Risk data access (add document extraction storage)

**Frontend - Pages:**
- `frontend/src/pages/risk/RiskDashboard.tsx` - Main dashboard (minor updates for new workflow)
- `frontend/src/pages/risk/RiskEvaluationDetail.tsx` - Evaluation detail view (add document discrepancy display)

**Frontend - Components:**
- `frontend/src/components/risk/FKRiskEvaluationForm.tsx` - Evaluation form (major updates for document upload)
- `frontend/src/components/risk/FKRiskScoreCard.tsx` - Score display (add document indicator)

**Frontend - Services:**
- `frontend/src/services/riskService.ts` - Risk API service (add document upload methods)

**Frontend - Types:**
- `frontend/src/types/risk.ts` - Risk TypeScript types (add document types)

**Testing & Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner documentation
- `.claude/commands/e2e/test_risk_dashboard.md` - Existing risk E2E test pattern
- `.claude/commands/e2e/test_inventario_bodega_ai_extraction.md` - LandingAI E2E test pattern
- `docs/20251127_landingai_ade_integration_guide.md` - LandingAI API documentation

### New Files
- `backend/src/core/servicios/risk/document_extraction_service.py` - LandingAI document extraction service for all document types
- `backend/src/core/servicios/risk/cross_validation_service.py` - Cross-validation logic comparing extracted data
- `backend/database/migration_add_document_extractions_table.sql` - Database migration for storing extracted document data
- `frontend/src/components/risk/FKDocumentUploader.tsx` - Multi-document upload component
- `frontend/src/components/risk/FKCrossValidationResults.tsx` - Display component for cross-validation findings
- `.claude/commands/e2e/test_fraud_document_cross_validation.md` - E2E test for document cross-validation

## Pre-Implementation Verification

### Feature Category
- [x] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [ ] Excel Processing (treasury, finance) → Complete sections B, D
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### A. Document Extraction Schemas (LandingAI)

**1. Financial Statements Schema:**
```json
{
  "type": "object",
  "properties": {
    "company_name": {"type": "string", "description": "Company legal name (Razón social)"},
    "nit": {"type": "string", "description": "Tax ID with verification digit (NIT-DV)"},
    "fiscal_year": {"type": "integer", "description": "Fiscal year of the statement"},
    "period_end_date": {"type": "string", "description": "Period end date (YYYY-MM-DD)"},
    "auditor_name": {"type": ["string", "null"], "description": "Auditor/accountant name"},
    "auditor_license": {"type": ["string", "null"], "description": "Professional license number"},
    "total_assets": {"type": "number", "description": "Total assets value"},
    "total_liabilities": {"type": "number", "description": "Total liabilities value"},
    "total_equity": {"type": "number", "description": "Total equity value"},
    "net_income": {"type": "number", "description": "Net income/profit"},
    "revenue": {"type": "number", "description": "Total revenue/sales"},
    "signatory_name": {"type": "string", "description": "Name of person who signed"},
    "signatory_id": {"type": ["string", "null"], "description": "ID of signatory"},
    "signatory_role": {"type": ["string", "null"], "description": "Role of signatory (Representante Legal, Contador, etc.)"}
  },
  "required": ["company_name", "nit", "fiscal_year"]
}
```

**2. Cedula (ID Document) Schema:**
```json
{
  "type": "object",
  "properties": {
    "full_name": {"type": "string", "description": "Full name as appears on ID"},
    "first_names": {"type": "string", "description": "First and middle names"},
    "last_names": {"type": "string", "description": "Surnames"},
    "document_number": {"type": "string", "description": "ID number (Cedula number)"},
    "document_type": {"type": "string", "description": "Document type (CC, CE, Pasaporte)"},
    "birth_date": {"type": ["string", "null"], "description": "Date of birth"},
    "birth_place": {"type": ["string", "null"], "description": "Place of birth"},
    "issue_date": {"type": ["string", "null"], "description": "ID issue date"},
    "issue_place": {"type": ["string", "null"], "description": "ID issue location"},
    "gender": {"type": ["string", "null"], "description": "Gender (M/F)"},
    "blood_type": {"type": ["string", "null"], "description": "Blood type if visible"},
    "associated_company": {"type": ["string", "null"], "description": "Company name if visible on document"}
  },
  "required": ["full_name", "document_number", "document_type"]
}
```

**3. Composicion Accionaria (Shareholders) Schema:**
```json
{
  "type": "object",
  "properties": {
    "company_name": {"type": "string", "description": "Company legal name"},
    "nit": {"type": "string", "description": "Company NIT"},
    "document_date": {"type": "string", "description": "Date of the shareholder composition document"},
    "total_shares": {"type": "number", "description": "Total number of shares"},
    "share_value": {"type": ["number", "null"], "description": "Nominal value per share"},
    "shareholders": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "id_number": {"type": ["string", "null"]},
          "shares": {"type": "number"},
          "percentage": {"type": "number"},
          "is_legal_representative": {"type": ["boolean", "null"]}
        }
      }
    },
    "majority_shareholder_name": {"type": "string", "description": "Name of majority shareholder"},
    "majority_shareholder_percentage": {"type": "number", "description": "Percentage of majority shareholder"}
  },
  "required": ["company_name", "nit", "shareholders"]
}
```

**4. RUT (Tax Registration) Schema:**
```json
{
  "type": "object",
  "properties": {
    "company_name": {"type": "string", "description": "Company legal name (field 35)"},
    "nit": {"type": "string", "description": "NIT with verification digit (fields 5-6)"},
    "city": {"type": "string", "description": "City/Municipality (field 40)"},
    "address": {"type": ["string", "null"], "description": "Registered address"},
    "email": {"type": "string", "description": "Contact email (field 42)"},
    "phone": {"type": ["string", "null"], "description": "Contact phone"},
    "economic_activity": {"type": ["string", "null"], "description": "Economic activity code"},
    "legal_representative_name": {"type": "string", "description": "Legal rep full name (fields 104-107)"},
    "legal_representative_id": {"type": "string", "description": "Legal rep ID number (field 101)"},
    "legal_representative_id_type": {"type": "string", "description": "Legal rep ID type (field 100)"},
    "registration_date": {"type": ["string", "null"], "description": "RUT registration date"},
    "last_update_date": {"type": ["string", "null"], "description": "Last RUT update date"}
  },
  "required": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
}
```

**5. Certificado de Existencia y Representacion Legal Schema:**
```json
{
  "type": "object",
  "properties": {
    "company_name": {"type": "string", "description": "Company legal name"},
    "nit": {"type": "string", "description": "NIT with verification digit"},
    "entity_type": {"type": "string", "description": "Legal entity type (S.A.S., S.A., LTDA)"},
    "registration_number": {"type": ["string", "null"], "description": "Chamber of commerce registration number"},
    "constitution_date": {"type": ["string", "null"], "description": "Date company was constituted"},
    "registered_capital": {"type": ["number", "null"], "description": "Registered capital"},
    "legal_representative_name": {"type": "string", "description": "Legal representative name"},
    "legal_representative_id": {"type": "string", "description": "Legal representative ID number"},
    "legal_representative_id_type": {"type": "string", "description": "Legal rep ID type"},
    "legal_representative_authority": {"type": ["string", "null"], "description": "Authority limits description"},
    "registered_address": {"type": "string", "description": "Company registered address"},
    "city": {"type": "string", "description": "City of registration"},
    "certificate_date": {"type": "string", "description": "Certificate issue date"},
    "expiry_date": {"type": ["string", "null"], "description": "Certificate expiry date"},
    "chamber_of_commerce": {"type": ["string", "null"], "description": "Issuing chamber of commerce"},
    "board_members": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "id_number": {"type": ["string", "null"]},
          "position": {"type": "string"}
        }
      }
    }
  },
  "required": ["company_name", "nit", "legal_representative_name", "legal_representative_id"]
}
```

### C. File Format Specification (Document Import)

| Document Type | Accepted Formats | Max Size | Required Fields |
|--------------|------------------|----------|-----------------|
| Financial Statements (Current Year) | PDF | 50MB | company_name, nit, fiscal_year |
| Financial Statements (Prior Year) | PDF | 50MB | company_name, nit, fiscal_year |
| Cedula (Legal Rep ID) | PDF, PNG, JPG | 5MB | full_name, document_number |
| Composicion Accionaria | PDF | 10MB | company_name, nit, shareholders |
| RUT | PDF, PNG | 5MB | company_name, nit, legal_rep |
| Certificado de Existencia | PDF | 10MB | company_name, nit, legal_rep |

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| risk_repo.create() | dict | data['id'] | assessment['id'] |
| risk_repo.get() | dict | data['risk_score'] | assessment['risk_score'] |
| document_extraction_repo.create() | dict | data['extracted_data'] | extraction['extracted_data'] |
| document_extraction_repo.get_by_assessment() | List[dict] | doc['document_type'] | For each doc in list |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (RiskLevel, AssessmentStatus)
- [ ] New document_extractions table (migration to be created)
- [ ] Cross-validation results stored in assessment's validation_details
- [x] Existing risk_assessments table supports additional validation data (JSONB columns)

### F. External API Contract (LandingAI ADE)

**ADE Parse API:**
| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `https://api.va.landing.ai/v1/ade/parse` | POST | Bearer Token | multipart/form-data | `{"markdown": "...", "chunks": [...]}` |

**ADE Extract API:**
| Endpoint | Method | Auth | Request Format | Response Format |
|----------|--------|------|----------------|-----------------|
| `https://api.va.landing.ai/v1/ade/extract` | POST | Bearer Token | form-data | `{"extraction": {...}}` |

**Error Handling Strategy:**
- HTTP 200: Full success, use extraction
- HTTP 206: Partial success, data usable with warnings
- HTTP 401: Invalid API key - raise auth error
- HTTP 429: Rate limit - raise retry error
- HTTP 5xx: Server error - retry with exponential backoff
- Timeout (120s): Show timeout error, allow retry

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| documentType | document_type | string (enum) | 'financial_statement_current', 'financial_statement_prior', 'cedula', 'composicion_accionaria', 'rut', 'certificado_existencia' |
| file | file | File (PDF/Image) | Uploaded document |
| clientNit | client_nit | string | Client identifier |
| assessmentId | assessment_id | UUID | Links extraction to assessment |
| extractedData | extracted_data | object | LandingAI extraction result |
| discrepancies | discrepancies | array | List of cross-validation findings |

## Implementation Plan

### Phase 1: Foundation
1. **Database Migration**: Create `document_extractions` table to store extracted data per document
2. **DTOs**: Add document extraction types and cross-validation result types
3. **Document Extraction Service**: Create LandingAI extraction service with schemas for all 5 document types

### Phase 2: Core Implementation
1. **Cross-Validation Service**: Implement logic to compare data across documents:
   - Company name matching across all documents
   - NIT consistency validation
   - Legal representative identity validation (name + ID)
   - Financial statement year-over-year sanity checks
   - Shareholder composition vs existence certificate alignment
2. **API Endpoints**: Add endpoints for document upload, extraction trigger, and cross-validation
3. **Frontend Components**: Create document uploader and discrepancy display components

### Phase 3: Integration
1. **Fraud Detection Integration**: Connect cross-validation results to existing fraud scoring
2. **UI Integration**: Add document cross-validation tab to evaluation detail page
3. **E2E Testing**: Create comprehensive E2E test for full workflow

## Step by Step Tasks

### Step 1: Create E2E Test Specification
- Read `.claude/commands/test_e2e.md` to understand E2E test runner format
- Read `.claude/commands/e2e/test_risk_dashboard.md` for existing risk test pattern
- Create `.claude/commands/e2e/test_fraud_document_cross_validation.md` with:
  - User story for document upload and cross-validation
  - Test steps for uploading multiple documents
  - Verification of extraction progress indicators
  - Validation of discrepancy display
  - Success criteria including processing time expectations

### Step 2: Create Database Migration
- Create `backend/database/migration_add_document_extractions_table.sql`
- Table structure:
  ```sql
  CREATE TABLE risk_document_extractions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      assessment_id UUID REFERENCES risk_assessments(id),
      document_type VARCHAR(50) NOT NULL,
      document_filename VARCHAR(255),
      document_storage_path TEXT,
      extracted_data JSONB,
      extraction_status VARCHAR(20) DEFAULT 'pending',
      extraction_method VARCHAR(20) DEFAULT 'landingai',
      extraction_confidence DECIMAL(3,2),
      extraction_errors JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE TABLE risk_cross_validation_results (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      assessment_id UUID REFERENCES risk_assessments(id),
      validation_type VARCHAR(50) NOT NULL,
      documents_compared TEXT[] NOT NULL,
      field_compared VARCHAR(100),
      values_found JSONB,
      is_discrepancy BOOLEAN DEFAULT false,
      severity VARCHAR(20),
      description TEXT,
      score_impact DECIMAL(5,2),
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE INDEX idx_doc_extractions_assessment ON risk_document_extractions(assessment_id);
  CREATE INDEX idx_cross_validation_assessment ON risk_cross_validation_results(assessment_id);
  ```

### Step 3: Add Document Extraction DTOs
- Edit `backend/src/interface/risk_dtos.py`
- Add document type enum:
  ```python
  class DocumentType(str, Enum):
      FINANCIAL_STATEMENT_CURRENT = "financial_statement_current"
      FINANCIAL_STATEMENT_PRIOR = "financial_statement_prior"
      CEDULA = "cedula"
      COMPOSICION_ACCIONARIA = "composicion_accionaria"
      RUT = "rut"
      CERTIFICADO_EXISTENCIA = "certificado_existencia"
  ```
- Add extraction request/response DTOs
- Add cross-validation result DTOs
- Add discrepancy severity enum

### Step 4: Create Document Extraction Service
- Create `backend/src/core/servicios/risk/document_extraction_service.py`
- Implement `DocumentExtractionService` class with:
  - `__init__`: Load LandingAI settings
  - `extract_document(document_type, pdf_bytes)`: Main extraction method
  - Document-specific schemas (FINANCIAL_SCHEMA, CEDULA_SCHEMA, etc.)
  - `_call_parse_api()` and `_call_extract_api()` (similar to landingai_rut_parser_service.py)
  - `_validate_extraction(document_type, data)`: Validate required fields
  - Error handling for API failures
- Total estimated: ~400 lines

### Step 5: Create Cross-Validation Service
- Create `backend/src/core/servicios/risk/cross_validation_service.py`
- Implement `CrossValidationService` class with:
  - `validate_documents(extractions: Dict[DocumentType, dict])`: Main cross-validation
  - `_compare_company_names()`: Check company name consistency
  - `_compare_nit()`: Check NIT across all documents
  - `_validate_legal_representative()`: Compare rep name and ID
  - `_validate_shareholders_vs_certificate()`: Cross-check shareholder data
  - `_validate_financial_statements()`: Year-over-year sanity checks
  - `_check_email_domain()`: Validate email against company domain
  - `calculate_discrepancy_score()`: Generate score impact
- Return list of `CrossValidationResult` objects

### Step 6: Update Risk Repository
- Edit `backend/src/repositorio/risk_repository.py`
- Add `DocumentExtractionRepository` class:
  - `create(extraction_data)`: Store extraction
  - `get_by_assessment(assessment_id)`: Get all extractions for assessment
  - `update_status(id, status, errors)`: Update extraction status
- Add `CrossValidationRepository` class:
  - `create_batch(results)`: Store validation results
  - `get_by_assessment(assessment_id)`: Get results for assessment

### Step 7: Add API Endpoints
- Edit `backend/src/adapter/rest/risk_routes.py`
- Add new endpoints:
  ```python
  @router.post("/evaluations/{id}/documents")
  async def upload_document(
      id: str,
      document_type: DocumentType,
      file: UploadFile,
      current_user = Depends(require_risk_role)
  ):
      """Upload a document for extraction"""

  @router.post("/evaluations/{id}/extract")
  async def trigger_extraction(
      id: str,
      current_user = Depends(require_risk_role)
  ):
      """Trigger AI extraction for all uploaded documents"""

  @router.post("/evaluations/{id}/cross-validate")
  async def trigger_cross_validation(
      id: str,
      current_user = Depends(require_risk_role)
  ):
      """Run cross-validation on extracted data"""

  @router.get("/evaluations/{id}/extractions")
  async def get_extractions(
      id: str,
      current_user = Depends(require_risk_role)
  ):
      """Get all document extractions for an assessment"""

  @router.get("/evaluations/{id}/discrepancies")
  async def get_discrepancies(
      id: str,
      current_user = Depends(require_risk_role)
  ):
      """Get cross-validation discrepancies"""
  ```

### Step 8: Update Frontend Types
- Edit `frontend/src/types/risk.ts`
- Add TypeScript types:
  ```typescript
  export type DocumentType =
    | 'financial_statement_current'
    | 'financial_statement_prior'
    | 'cedula'
    | 'composicion_accionaria'
    | 'rut'
    | 'certificado_existencia';

  export interface DocumentExtraction {
    id: string;
    document_type: DocumentType;
    document_filename: string;
    extraction_status: 'pending' | 'processing' | 'completed' | 'failed';
    extracted_data: Record<string, unknown>;
    extraction_errors?: string[];
  }

  export interface CrossValidationDiscrepancy {
    validation_type: string;
    documents_compared: string[];
    field_compared: string;
    values_found: Record<string, string>;
    severity: 'low' | 'medium' | 'high' | 'critical';
    description: string;
    score_impact: number;
  }
  ```

### Step 9: Update Frontend Risk Service
- Edit `frontend/src/services/riskService.ts`
- Add new methods:
  ```typescript
  uploadDocument(assessmentId: string, documentType: DocumentType, file: File): Promise<DocumentExtraction>
  triggerExtraction(assessmentId: string): Promise<{status: string}>
  triggerCrossValidation(assessmentId: string): Promise<{discrepancies: CrossValidationDiscrepancy[]}>
  getExtractions(assessmentId: string): Promise<DocumentExtraction[]>
  getDiscrepancies(assessmentId: string): Promise<CrossValidationDiscrepancy[]>
  ```

### Step 10: Create Document Uploader Component
- Create `frontend/src/components/risk/FKDocumentUploader.tsx`
- Implement multi-document upload with:
  - 6 upload slots (one per document type)
  - Spanish labels matching document types
  - File type validation (PDF, PNG, JPG based on document type)
  - File size validation (5MB for Cedula/RUT, 10MB for Composicion/Certificado, 50MB for Financial Statements)
  - Upload progress indicators
  - Extraction status badges (pending, processing, completed, failed)
  - Retry capability for failed extractions
  - "Extract All" button to trigger batch extraction
- Follow existing FK component patterns

### Step 11: Create Cross-Validation Results Component
- Create `frontend/src/components/risk/FKCrossValidationResults.tsx`
- Implement discrepancy display with:
  - Summary card showing total discrepancies by severity
  - List of discrepancies with:
    - Icon indicating severity (error/warning/info)
    - Description of the discrepancy
    - Values found in each document
    - Score impact
  - Color coding: critical=red, high=orange, medium=yellow, low=gray
  - Expandable details showing source documents
  - "Run Validation" button if not yet run

### Step 12: Update Evaluation Detail Page
- Edit `frontend/src/pages/risk/RiskEvaluationDetail.tsx`
- Add new tabs or sections:
  - "Documentos" tab with FKDocumentUploader
  - "Validación Cruzada" tab with FKCrossValidationResults
  - Show extraction and validation status in header
- Add handlers for document upload and validation triggers
- Show document-based discrepancies in FKRiskScoreCard

### Step 13: Update Risk Evaluation Form
- Edit `frontend/src/components/risk/FKRiskEvaluationForm.tsx`
- Add new assessment type option: "comprehensive_with_documents"
- Add explanatory text about document-based evaluation
- After evaluation creation, redirect to detail page for document upload

### Step 14: Integrate with Fraud Detection Scoring
- Edit `backend/src/core/servicios/risk/fraud_detection_service.py`
- Add method to incorporate document cross-validation results:
  ```python
  async def include_document_validation(
      self,
      assessment_id: str,
      discrepancies: List[CrossValidationResult]
  ) -> List[FraudIndicator]:
      """Convert document discrepancies to fraud indicators"""
  ```
- Update risk score calculation to include document-based indicators

### Step 15: Run Validation Commands
- Execute all validation commands listed below
- Verify zero regressions in existing functionality
- Test document upload and extraction with sample files

## Testing Strategy

### Unit Tests
- `test_document_extraction_service.py`:
  - Test each document schema extraction
  - Test LandingAI API error handling
  - Test partial extraction (HTTP 206) handling
  - Mock API responses
- `test_cross_validation_service.py`:
  - Test company name comparison (exact match, fuzzy match)
  - Test NIT consistency across documents
  - Test legal representative validation
  - Test discrepancy scoring
  - Test with Azelis fraud case data

### Edge Cases
1. **Missing Documents**: Some document types not uploaded - validation should proceed with available documents
2. **Partial Extraction**: LandingAI returns HTTP 206 - should still compare available fields
3. **Conflicting Data**: 3+ documents with 3 different values - should flag as high severity
4. **OCR Errors**: Minor spelling differences - should use fuzzy matching with configurable threshold
5. **Empty Documents**: Uploaded PDF is blank or corrupted - should mark as failed, not block other documents
6. **Duplicate Uploads**: Same document uploaded twice - should overwrite previous
7. **Large Documents**: Up to 50MB financial statement PDFs - should handle without timeout
8. **Mixed Languages**: Documents in Spanish and English - extraction should handle both
9. **Old Documents**: Financial statements from wrong year - should flag date mismatch
10. **Name Variations**: "S.A.S." vs "S.A.S" vs "SAS" - normalization needed

## Acceptance Criteria
1. Risk analyst can upload 6 different document types for an assessment
2. Each document is processed by LandingAI with appropriate schema
3. Extraction progress is visible in the UI (pending/processing/completed/failed)
4. Cross-validation runs automatically after all extractions complete
5. Discrepancies are displayed with severity levels and descriptions
6. Document-based discrepancies contribute to overall risk score
7. Failed extractions can be retried without affecting other documents
8. Existing NIT-based evaluations continue to work unchanged
9. Risk managers can make decisions based on document validation results
10. Processing time expectations are clearly communicated (30-60s per document)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Backend validation
cd backend && python -m pytest tests/ -v

# Backend linting
cd backend && ruff check src/

# Frontend linting
cd frontend && npm run lint

# TypeScript type check
cd frontend && npx tsc --noEmit

# Frontend production build
cd frontend && npm run build

# E2E Test (after starting dev servers)
# Read .claude/commands/test_e2e.md
# Execute .claude/commands/e2e/test_fraud_document_cross_validation.md
```

## Notes

### New Dependencies
- **Backend**: No new dependencies - uses existing `httpx` for LandingAI API calls
- **Frontend**: No new dependencies - uses existing MUI components

### Environment Variables
Existing LandingAI configuration is sufficient:
```bash
LANDINGAI_API_KEY=your_api_key_here
```

### Cost Considerations
- LandingAI ADE charges ~$0.30-$4.00 per document
- Full evaluation with 6 documents: ~$2-$24 per client
- Recommend using document-based evaluation only for high-value or suspicious clients
- Consider caching extractions to avoid re-processing on retries

### Cross-Validation Rules Matrix
Based on Azelis fraud case analysis:

| Validation Rule | Documents Compared | Fields Checked | Severity if Mismatch |
|----------------|-------------------|----------------|---------------------|
| Company Name | All | company_name | CRITICAL |
| NIT | All | nit | CRITICAL |
| Legal Rep Name | Cedula, RUT, Certificado | full_name / legal_rep_name | HIGH |
| Legal Rep ID | Cedula, RUT, Certificado | document_number / legal_rep_id | HIGH |
| Shareholders vs Board | Composicion, Certificado | majority_shareholder vs board | MEDIUM |
| Financial Continuity | EEFF Current, EEFF Prior | revenue, assets YoY change | MEDIUM |
| Email Domain | RUT | email domain vs company domain | HIGH |
| Address Consistency | RUT, Certificado | address, city | MEDIUM |
| Registration Dates | Certificado, EEFF | constitution_date vs fiscal_year | LOW |

### Fraud Detection Scenarios
1. **Identity Swap** (Azelis case): Company name on Cedula doesn't match RUT → CRITICAL
2. **Typosquatting**: Email domain similar but different from legitimate company → HIGH
3. **Financial Manipulation**: Revenue grows >500% year-over-year → MEDIUM (flag for review)
4. **Ghost Shareholders**: Majority shareholder not on board of directors → MEDIUM
5. **Expired Certificate**: Existence certificate older than 30 days → LOW

### Future Enhancements
1. **Automatic Document Classification**: Use LandingAI to identify document type from content
2. **Batch Processing**: Upload ZIP file with all documents at once
3. **Document Storage**: Store documents in Supabase Storage for audit trail
4. **DIAN API Integration**: Verify NIT directly with Colombian tax authority
5. **Chamber of Commerce API**: Validate existence certificate authenticity
6. **ML Pattern Detection**: Train model on detected fraud cases

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness
**Document Processing:**
- [x] All 5 document schemas documented with field descriptions
- [x] Required vs optional fields clearly marked
- [x] File format and size limits specified

**API Integration:**
- [x] LandingAI API contract documented
- [x] Auth method specified (Bearer token)
- [x] Error/retry strategy defined

**Data Import:**
- [x] File format specifications documented
- [x] Field mapping complete (extraction schema to cross-validation)
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for repository methods
- [x] Country-specific requirements handled (Colombia documents)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers document upload and cross-validation workflow
