# Feature: Broker Contract Incentive Extraction

## Feature Description
Build a directory scanning and PDF extraction feature for the Alianzas (Alliances) department that scans a directory containing broker folders, extracts incentive percentages from PDF contracts using regex patterns, identifies broker name and RFC from signature sections, and outputs consolidated data to an Excel file. This feature is similar to the existing "Escaneo Directorio Local" in Tesoreria but tailored for broker contract analysis.

## User Story
As an **Alianzas department user**
I want to scan a directory of broker contracts and automatically extract incentive percentages
So that I can centralize broker incentive data for easy reference, reduce manual review time, and support compliance/auditing needs

## Problem Statement
The Alianzas department needs to extract and consolidate economic incentive information from multiple broker contracts stored in a local directory structure. Currently, this information is manually reviewed from PDFs, which is time-consuming and error-prone. There are two contract types to handle: "Bono" contracts (with credit line and operations bonuses in Anexo A) and older "Incentivos" contracts (in Artículo 3).

## Solution Statement
Implement a directory scanner with PDF text extraction that:
1. Scans broker folders following the naming convention `YYYYMMDD Broker Name`
2. Extracts text from PDF contracts using PyMuPDF (fitz)
3. Uses regex patterns to identify contract type (Bono vs Incentivos) and extract incentive percentages
4. Extracts signatory information (name, RFC) from signature sections
5. Generates a formatted Excel file with all extracted data
6. Provides a user-friendly UI under the Alianzas department menu

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Use `require_roles(['alianzas'])` from `rbac_dependencies.py` (admin bypass is default)
- Frontend Protection: Use `RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}`

## Relevant Files
Use these files to implement the feature:

**Backend - Reference Files (patterns to follow):**
- `backend/src/core/servicios/declaraciones/local_directory_scanner.py` - Pattern for directory scanning service
- `backend/src/core/servicios/declaraciones/inventory_excel_generator.py` - Pattern for Excel generation
- `backend/src/core/servicios/contract_extractor_service.py` - Pattern for PDF text extraction with regex
- `backend/src/adapter/rest/declaraciones/directory_scanner.py` - Pattern for scanner API endpoints
- `backend/src/interface/directory_scanner_dtos.py` - Pattern for DTOs
- `backend/src/adapter/rest/alianzas_routes.py` - Existing Alianzas routes to extend
- `backend/src/adapter/rest/rbac_dependencies.py` - RBAC dependencies

**Frontend - Reference Files (patterns to follow):**
- `frontend/src/pages/treasury/DirectoryScannerPage.tsx` - Pattern for scanner page
- `frontend/src/components/treasury/FKDirectoryScanForm.tsx` - Pattern for scan form
- `frontend/src/components/treasury/FKInventoryFilesTable.tsx` - Pattern for results table
- `frontend/src/services/directoryScannerService.ts` - Pattern for API service
- `frontend/src/components/ui/FKSidebarWithCollapse.tsx` - Add menu item here
- `frontend/src/App.tsx` - Add route here
- `frontend/src/types/index.ts` - TypeScript types

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test file

### New Files

**Backend:**
- `backend/src/core/servicios/broker_incentive_extractor.py` - PDF extraction service with regex patterns for broker contracts
- `backend/src/core/servicios/broker_contract_scanner.py` - Directory scanner service for broker folders
- `backend/src/core/servicios/broker_incentive_excel_generator.py` - Excel generator for broker incentive data
- `backend/src/interface/broker_incentive_dtos.py` - DTOs for broker incentive extraction

**Frontend:**
- `frontend/src/pages/alianzas/BrokerIncentiveExtractionPage.tsx` - Main page component
- `frontend/src/components/alianzas/FKBrokerContractScanForm.tsx` - Scan configuration form
- `frontend/src/components/alianzas/FKBrokerIncentiveResultsGrid.tsx` - Results data grid
- `frontend/src/services/brokerIncentiveService.ts` - API service for broker incentive extraction

**E2E Test:**
- `.claude/commands/e2e/test_broker_incentive_extraction.md` - E2E test file for this feature

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [x] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

Note: This feature combines directory scanning with PDF extraction and Excel export, similar to treasury's directory scanner.

### A. Template Placeholder Inventory (Document Generation only)
N/A - This feature reads PDFs, does not generate documents.

### B. Excel Column Mapping (Excel Processing only)

**Source Data (Extracted from PDFs):**
| Field | Data Type | Source | Required |
|-------|-----------|--------|----------|
| broker_name | String | Folder name (extract after YYYYMMDD prefix) | Yes |
| contract_date | Date | Folder name YYYYMMDD prefix | Yes |
| rfc | String | Signature section regex extraction | No |
| signatory_name | String | Signature section regex extraction | No |
| credit_line_incentive_pct | Float | Contract body (Bono apertura clause) | No |
| operations_incentive_pct | Float | Contract body (Operations clause) | No |
| contract_type | Enum | Contract body analysis (Bono/Incentivos) | Yes |
| pdf_path | String | Full path to PDF file | Yes |

**Output Excel Structure:**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| Nombre Broker | broker_name | Direct copy |
| RFC | rfc | Direct copy or "N/A" |
| Nombre Firmante | signatory_name | Direct copy or "N/A" |
| Incentivo Línea Crédito (%) | credit_line_incentive_pct | Format as percentage or "N/A" |
| Incentivo Operaciones (%) | operations_incentive_pct | Format as percentage or "N/A" |
| Tipo Contrato | contract_type | "Bono" or "Incentivos" or "Desconocido" |
| Archivo Fuente | pdf_path | Direct copy |
| Fecha Extracción | extraction_date | Current timestamp |
| Notas | warnings | Join warnings with semicolon |

**Catalog Dependencies:**
- [x] No external catalogs needed - extraction is pattern-based

### C. File Format Specification (Import/Export only)

**Input:**
| Format | Source | Structure | Validation Rules |
|--------|--------|-----------|------------------|
| Directory | Local filesystem | `YYYYMMDD Broker Name/` folders containing PDFs | Must be readable, must contain subfolders |
| PDF | Local filesystem | Broker contracts | Must be readable, max 50MB per file |

**Output:**
| Format | Max Size | Columns | Notes |
|--------|----------|---------|-------|
| XLSX | ~10MB | 9 columns as defined above | Styled with headers, filters |

### D. Data Contract Verification (ALL features)

**Repository Methods Used:**
N/A - This feature does not use database repositories. It's a file-based extraction service.

**Service Methods - Return Types:**
| Service Method | Return Type | Access Pattern | Example |
|----------------|-------------|----------------|---------|
| BrokerContractScanner.scan_directory() | List[BrokerFolder] | data.broker_name | Not dict access |
| BrokerIncentiveExtractor.extract_from_pdf() | BrokerIncentiveData | result.credit_line_incentive_pct | Pydantic model |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] No database dependencies - file-based extraction only
- [x] No migrations needed
- [x] No template files needed

### F. External API Contract (Integration only)
N/A - No external APIs used.

### G. Query Specification (Reporting only)
N/A - No database queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| directory_path | directory_path | string | Full path to scan |
| include_subfolders | include_subfolders | boolean | Recursive scan flag |
| broker_name | broker_name | string | From folder name |
| rfc | rfc | string | nullable |
| signatory_name | signatory_name | string | nullable |
| credit_line_incentive_pct | credit_line_incentive_pct | number | nullable |
| operations_incentive_pct | operations_incentive_pct | number | nullable |
| contract_type | contract_type | string | "bono", "incentivos", "unknown" |
| pdf_path | pdf_path | string | Full file path |
| extraction_date | extraction_date | string | ISO datetime |
| warnings | warnings | string[] | List of warnings |

## Implementation Plan

### Phase 1: Foundation
1. Create DTOs for broker incentive extraction (Pydantic models)
2. Create broker contract scanner service (directory scanning, folder name parsing)
3. Create broker incentive extractor service (PDF text extraction, regex patterns)
4. Create Excel generator service for broker incentive data

### Phase 2: Core Implementation
5. Add API endpoints to alianzas_routes.py
6. Create frontend service for API integration
7. Create scan form component
8. Create results grid component
9. Create main page component

### Phase 3: Integration
10. Add menu item to sidebar under Alianzas
11. Add route to App.tsx with role protection
12. Create E2E test file
13. Test and validate end-to-end

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Backend DTOs
Create `backend/src/interface/broker_incentive_dtos.py` with Pydantic models:
- `ContractType` enum (BONO, INCENTIVOS, UNKNOWN)
- `SignatoryInfo` model (name, rfc)
- `BrokerIncentiveData` model (all extraction fields)
- `BrokerContractScanConfigDTO` (directory_path, include_subfolders)
- `BrokerContractScanResultDTO` (totals, output_file_path, statistics)

### Step 2: Create Broker Contract Scanner Service
Create `backend/src/core/servicios/broker_contract_scanner.py`:
- Follow pattern from `local_directory_scanner.py`
- `BrokerFolder` class to represent a broker folder with metadata
- `BrokerContractScanner` class with methods:
  - `scan_directory(path: str, include_subfolders: bool)` - returns List[BrokerFolder]
  - `parse_folder_name(name: str)` - extracts date and broker name from `YYYYMMDD Name` format
  - `find_contract_pdf(folder: BrokerFolder)` - locates contract PDF in folder

### Step 3: Create Broker Incentive Extractor Service
Create `backend/src/core/servicios/broker_incentive_extractor.py`:
- Follow pattern from `contract_extractor_service.py`
- Define regex patterns for:
  - Bono credit line: `un bono equivalente al X% del monto colocado...bono de apertura`
  - Bono operations: `un bono equivalente al X%...operaciones elegibles`
  - Incentivos: `Finkargo reconocerá un incentivo de X%`
  - RFC: `RFC[:\s]*([A-Z&Ñ]{3,4}\d{6}[A-Z\d]{3})`
  - Signatory name (near signature line)
- `BrokerIncentiveExtractor` class with methods:
  - `extract_from_pdf(pdf_path: str)` - full extraction pipeline
  - `identify_contract_type(text: str)` - returns ContractType
  - `extract_credit_line_incentive(text: str)` - returns Optional[float]
  - `extract_operations_incentive(text: str)` - returns Optional[float]
  - `extract_signatory_info(text: str)` - returns SignatoryInfo

### Step 4: Create Excel Generator Service
Create `backend/src/core/servicios/broker_incentive_excel_generator.py`:
- Follow pattern from `inventory_excel_generator.py`
- `BrokerIncentiveExcelGenerator` class with methods:
  - `generate_excel(records: List[BrokerIncentiveData], output_path: str)` - creates styled Excel
  - `_create_dataframe(records)` - converts records to DataFrame
  - `_calculate_statistics(records)` - calculates summary stats
  - `_apply_styling(file_path)` - applies Finkargo brand styling

### Step 5: Add API Endpoints
Extend `backend/src/adapter/rest/alianzas_routes.py`:
- `POST /api/alianzas/broker-contracts/scan` - Trigger directory scan
  - Body: `BrokerContractScanConfigDTO`
  - Response: `BrokerContractScanResultDTO`
- `GET /api/alianzas/broker-contracts/results` - Get scan results (in-memory or file-based)
- `GET /api/alianzas/broker-contracts/export` - Download Excel file
- All endpoints protected with `require_alianzas_role`

### Step 6: Create Frontend Service
Create `frontend/src/services/brokerIncentiveService.ts`:
- Follow pattern from `directoryScannerService.ts`
- Define TypeScript interfaces matching backend DTOs
- Implement API methods:
  - `scanBrokerContracts(config)` - POST to scan endpoint
  - `exportBrokerIncentives()` - GET to export endpoint

### Step 7: Create Scan Form Component
Create `frontend/src/components/alianzas/FKBrokerContractScanForm.tsx`:
- Follow pattern from `FKDirectoryScanForm.tsx`
- Form fields:
  - Directory path input (required)
  - Include subfolders checkbox (default: true)
  - Scan button with loading state
- Form validation
- Error display
- Pass config to parent on submit

### Step 8: Create Results Grid Component
Create `frontend/src/components/alianzas/FKBrokerIncentiveResultsGrid.tsx`:
- Use MUI DataGrid
- Columns: Broker Name, RFC, Signatory, Credit Line %, Operations %, Contract Type, Source File, Notes
- Row highlighting for missing data (e.g., no RFC)
- Sortable and filterable columns
- Export button integration

### Step 9: Create Main Page Component
Create `frontend/src/pages/alianzas/BrokerIncentiveExtractionPage.tsx`:
- Follow pattern from `DirectoryScannerPage.tsx`
- Layout:
  - Title: "Extracción Incentivos Brokers"
  - Description text
  - Scan form component
  - Results grid component (shown after scan)
  - Success/error snackbar notifications
- State management for scan results
- Handle scan start and completion

### Step 10: Add Menu Item to Sidebar
Update `frontend/src/components/ui/FKSidebarWithCollapse.tsx`:
- Add new item to `alianzasModules` array:
  ```typescript
  {
    id: 'incentivos-brokers',
    name: 'Extracción Incentivos',
    route: '/alianzas/incentivos-brokers',
    icon: <Assessment fontSize="small" />,
  }
  ```

### Step 11: Add Route to App.tsx
Update `frontend/src/App.tsx`:
- Import `BrokerIncentiveExtractionPage`
- Add route:
  ```typescript
  <Route
    path="alianzas/incentivos-brokers"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.ALIANZAS, UserRole.ADMIN]}>
        <BrokerIncentiveExtractionPage />
      </RoleProtectedRoute>
    }
  />
  ```

### Step 12: Create E2E Test File
Create `.claude/commands/e2e/test_broker_incentive_extraction.md`:
- User story for Alianzas user extracting broker incentives
- Prerequisites (servers running, test directory with PDFs)
- Test steps:
  1. Navigate to application
  2. Login with alianzas role
  3. Navigate to Alianzas → Extracción Incentivos
  4. Verify page loads with form
  5. Enter test directory path
  6. Click scan button
  7. Verify progress/loading state
  8. Verify results appear in grid
  9. Verify export button works
  10. Take screenshots at key steps
- Success criteria

### Step 13: Run Validation Commands
Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests
Backend (`backend/tests/test_broker_incentive_extractor.py`):
- Test regex patterns for Bono credit line incentive extraction
- Test regex patterns for Bono operations incentive extraction
- Test regex patterns for Incentivos contract style
- Test RFC pattern matching
- Test signatory name extraction
- Test folder name parsing (`YYYYMMDD Broker Name` format)
- Test contract type identification
- Test percentage parsing (handle comma vs period decimals)

### Edge Cases
- No PDF in folder → Log warning, include in results with null values
- Multiple PDFs in folder → Process first matching contract, log others
- Missing RFC in signature → Set RFC to null, include signatory name if found
- Incentive not found → Set to null, add warning message
- Unrecognized contract type → Mark as "unknown", attempt extraction anyway
- Corrupted PDF → Log error, skip folder, continue processing
- Empty folder → Skip, do not include in results
- Special characters in folder name → Handle UTF-8 encoding properly
- Scanned/image-based PDF → Low text extraction, warn user
- Very large directory (1000+ folders) → Ensure reasonable processing time
- Permission denied on folder/file → Log error, continue with accessible files

## Acceptance Criteria
1. User can navigate to "Extracción Incentivos Brokers" under Alianzas menu
2. User can enter a directory path and initiate a scan
3. System scans all subfolders following `YYYYMMDD Broker Name` convention
4. System extracts incentive percentages from both "Bono" and "Incentivos" contract types
5. System extracts RFC and signatory name when available
6. Results are displayed in a sortable/filterable data grid
7. Rows with missing data are visually highlighted
8. User can export results to a formatted Excel file
9. Excel file includes all extracted data plus extraction date and warnings
10. Feature is accessible only to users with `alianzas` or `admin` role
11. All backend tests pass with zero regressions
12. Frontend builds successfully with no TypeScript errors
13. Feature works end-to-end as validated by E2E test

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_incentive_extraction.md` to validate this functionality works

## Notes

### Dependencies
- No new npm packages required for frontend
- No new pip packages required for backend (PyMuPDF, pandas, openpyxl already in requirements.txt)

### Regex Pattern Details
The regex patterns should be flexible to handle variations in contract text:

**Bono Contract - Credit Line:**
```python
BONO_CREDIT_LINE_PATTERNS = [
    r"un bono equivalente al?\s*([\d.,]+)\s*%?\s*(?:por\s*ciento)?\s*del monto (?:colocado|a cliente).*bono de apertura",
    r"bono de apertura.*equivalente al?\s*([\d.,]+)\s*%",
]
```

**Bono Contract - Operations:**
```python
BONO_OPERATIONS_PATTERNS = [
    r"un bono equivalente al?\s*([\d.,]+)\s*%?\s*(?:por\s*ciento)?.*operaciones elegibles",
    r"operaciones elegibles.*equivalente al?\s*([\d.,]+)\s*%",
]
```

**Incentivos Contract:**
```python
INCENTIVOS_PATTERNS = [
    r"(?:Finkargo|finkargo)\s*reconocer[áa]\s*(?:un\s*)?incentivo\s*(?:de\s*)?([\d.,]+)\s*%",
]
```

### Security Considerations
- Sanitize directory paths to prevent path traversal attacks (reject `..` in paths)
- Limit max PDF file size to 50MB
- Only process files with `.pdf` extension
- Log all file access for audit trail

### Future Enhancements (Out of Scope)
- Automatic contract classification using ML
- Integration with broker database (save to Supabase)
- Historical tracking of incentive changes
- Batch processing scheduling
- Email notifications on completion

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [x] E2E test file task included (Step 12)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented
- [x] Data transformation rules specified
- [x] Catalog/lookup dependencies identified (none needed)

**Data Import/Export:**
- [x] File format specifications documented
- [x] Field mapping table complete
- [x] Error handling strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for service methods
- [x] Country-specific variations handled (N/A - Mexico only for brokers)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
