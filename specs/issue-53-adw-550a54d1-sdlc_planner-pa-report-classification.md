# Feature: PA Report Classification for Finance Module

## Feature Description

Add a comprehensive "Reporte PA" (Patrimonio Autónomo Report) feature to the Finance module that enables:
1. **Rules Management** - Upload and manage classification rules via Excel files (PA Account Catalog, Classification Rules, Nexo Rules)
2. **Report Processing** - Process NetSuite movement files (~50k rows/month) to generate cleaned and classified PA reports with two-step workflow

This feature automates the classification of financial transactions for Patrimonio Autónomo (PA) accounts by:
- Filtering transactions to only PA accounts based on uploaded catalog
- Renaming and adding 8 new output columns (PA, Categoría, Subcategoría, Clasificación, Nexo, Comprobación saldos, Cuenta Homologación, Nombre Homologación)
- Applying business rules for classification based on transaction type, document type, account name, and date logic
- Validating balance consistency (Débito = Crédito)

## User Story

As a Finance user
I want to upload NetSuite movement files and have them automatically filtered and classified for PA accounts
So that I can generate accurate PA reports with proper categorization without manual Excel manipulation

As a Finance Administrator
I want to upload and manage PA classification rules
So that the classification logic can be updated without code changes

## Problem Statement

Currently, the Finance team manually processes NetSuite Excel files with ~50k rows to:
1. Filter only PA accounts from a catalog
2. Add 8 new classification columns
3. Apply complex business rules based on transaction type, document type, account names, and dates
4. Validate that balances match

This manual process is time-consuming, error-prone, and requires specialized knowledge of the classification rules.

## Solution Statement

Implement an automated PA Report Classification system with:
1. **Rules Upload Interface** - Admin-only pages to upload Excel files containing:
   - PA Account Catalog (which accounts are PA + homologation mapping)
   - Main Classification Rules (transaction type + document type → category)
   - Clasificación by Account Rules (account name patterns → clasificación)
   - Nexo Mapping Rules (account name patterns → nexo values)

2. **Two-Step Processing Workflow**:
   - **Step 1 (Clean)**: Upload NetSuite file → Filter PA accounts → Add homologation columns → Validate balances → Download cleaned file for review
   - **Step 2 (Classify)**: Apply classification rules → Fill all 8 output columns → Download final classified file

3. **Processing History** - Track all processing sessions with statistics and download links

## Access Control

- **Required Role(s)**:
  - Rules Management: `finance_admin` (new role), `admin`
  - Report Processing: `finance`, `finance_admin`, `admin`
- **Backend Protection**:
  - Rules endpoints: `require_roles(['finance_admin'])`
  - Processing endpoints: `require_roles(['finance', 'finance_admin'])`
- **Frontend Protection**:
  - Rules page: `<RoleProtectedRoute allowedRoles={[UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>`
  - Processing page: `<RoleProtectedRoute allowedRoles={[UserRole.FINANCE, UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>`

## Relevant Files

Use these files to understand existing patterns:

**Backend - Similar Finance Features:**
- `backend/src/adapter/rest/finance_routes.py` - Existing finance API routes pattern (CO/MX processing)
- `backend/src/core/servicios/excel_merge_service_co.py` - Excel processing patterns
- `backend/src/core/servicios/filter_service_co.py` - Filtering and data transformation
- `backend/src/interface/finance_dtos_co.py` - DTOs for finance features
- `backend/src/repositorio/finance_report_repository.py` - History tracking repository pattern
- `backend/database/migration_add_finance_reports.sql` - Database migration pattern

**Backend - Auth & RBAC:**
- `backend/src/adapter/rest/rbac_dependencies.py` - Role-based access control patterns
- `backend/src/adapter/rest/dependencies.py` - Authentication dependencies

**Frontend - Similar Finance Features:**
- `frontend/src/pages/finance/ReporteriaAutomaticaCO.tsx` - Finance page with tabs, upload, and processing
- `frontend/src/services/financeServiceCO.ts` - API service layer pattern
- `frontend/src/components/forms/FKExcelUploaderCO.tsx` - Excel upload component pattern

**Frontend - Types & Routing:**
- `frontend/src/types/index.ts` - User roles and types
- `frontend/src/App.tsx` - Route configuration
- `frontend/src/components/ui/FKSidebar.tsx` - Department navigation (may need menu items)

**E2E Testing:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_risk_dashboard.md` - Example E2E test file

### New Files

**Backend:**
- `backend/database/migration_pa_classification.sql` - Create PA tables (catalog, rules, history)
- `backend/database/migration_add_finance_admin_role.sql` - Add FINANCE_ADMIN role
- `backend/src/interface/pa_dtos.py` - DTOs for PA feature
- `backend/src/repositorio/pa_rules_repository.py` - CRUD for all PA rule tables
- `backend/src/core/servicios/pa_rules_service.py` - Excel upload parsing, rule storage
- `backend/src/core/servicios/pa_cleanup_service.py` - Step 1: Filter, clean, validate
- `backend/src/core/servicios/pa_classification_engine.py` - Classification logic engine
- `backend/src/core/servicios/pa_report_service.py` - Orchestrate full processing flow
- `backend/src/adapter/rest/pa_routes.py` - API endpoints for PA feature

**Frontend:**
- `frontend/src/types/financePA.ts` - TypeScript interfaces for PA feature
- `frontend/src/services/financeServicePA.ts` - API client functions
- `frontend/src/components/forms/FKPARulesUploader.tsx` - Multi-file rules uploader
- `frontend/src/components/forms/FKPARulesViewer.tsx` - View current rules tables
- `frontend/src/components/forms/FKPAFileUploader.tsx` - NetSuite file uploader
- `frontend/src/components/forms/FKPACleanedResults.tsx` - Step 1 results with validation stats
- `frontend/src/components/forms/FKPAClassifiedResults.tsx` - Step 2 final results
- `frontend/src/pages/finance/ReglasClasificacionPA.tsx` - Rules admin page
- `frontend/src/pages/finance/ReportePA.tsx` - Main processing page with tabs

**E2E Test:**
- `.claude/commands/e2e/test_pa_report_classification.md` - E2E test for PA feature

## Pre-Implementation Verification

### Feature Category
- [x] Excel Processing (treasury, finance) → Complete sections B, D

### A. Template Placeholder Inventory (Document Generation only)
Not applicable - this feature does not generate Word documents.

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (NetSuite "Movimiento Detallado por Cuenta"):**
| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| Cuenta (línea): Número | Yes | String | Account number, key for PA filtering |
| Cuenta (línea): Nombre | Yes | String | Account name, used for classification |
| Fecha | Yes | Date | Transaction date, used for date logic |
| Fecha de creación | No | Date | Creation timestamp |
| Tipo de Transacción | Yes | String | Transaction type (Asiento, Factura de venta, etc.) |
| Tipo de comprobante | Yes | String | Document type (Ajustes Contables, Provisión Ingresos, etc.) |
| Número de documento | Yes | String | Document number, pattern matching (GBA, PPR, TBA) |
| Débito | Yes | Decimal | Debit amount |
| Crédito | Yes | Decimal | Credit amount |
| Saldo | Yes | Decimal | Balance (rename to "Valor COP") |
| Moneda: Nombre | Yes | String | Currency name |
| Tipo de cambio | No | Decimal | Exchange rate |
| Importe (moneda extranjera) | No | Decimal | Foreign amount (rename to "Valor USD") |

**Output Columns to Add (AA-AH):**
| Column Name | Source | Transformation |
|-------------|--------|----------------|
| PA | Always | Static "X" for all PA records |
| Categoría | Classification rules | Match tipo_transaccion + tipo_comprobante |
| Subcategoría | Classification rules + date | Date logic for first-day-of-month rules |
| Clasificación | Account name rules | Pattern matching + hierarchy (Realizada/No Realizada) |
| Nexo | Nexo rules | Account name pattern → "1", "2", "3", "4", "13" |
| Comprobación saldos | Hardcoded accounts | "Cartera PA" for specific account numbers |
| Cuenta Homologación | Account catalog | Direct mapping from cuenta_finkargo |
| Nombre Homologación | Account catalog | Direct mapping from cuenta_finkargo |

**Catalog/Lookup Dependencies:**
- [x] PA Account Catalog: cuenta_finkargo → cuenta_homologacion, nombre_homologacion
- [x] Classification Rules: tipo_transaccion + tipo_comprobante → categoria, subcategoria
- [x] Clasificación Cuenta Rules: cuenta_nombre_patron → clasificacion
- [x] Nexo Rules: cuenta_nombre_patron → nexo

### C. File Format Specification (Import/Export only)
Not applicable - using standard Excel import/export.

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| pa_rules_repo.get_catalog() | List[dict] | data['cuenta_finkargo'] | Not data.cuenta_finkargo |
| pa_rules_repo.get_classification_rules() | List[dict] | data['tipo_transaccion'] | Not data.tipo_transaccion |
| pa_rules_repo.get_nexo_rules() | List[dict] | data['nexo'] | Not data.nexo |
| pa_history_repo.create() | dict | data['session_id'] | Not data.session_id |

### E. Database Dependencies Checklist (Document/CRUD only)
- [x] Required enums exist in DTOs (or will be added) - PAProcessingStatus enum
- [ ] Template file exists in `backend/templates/` (if applicable) - Not applicable
- [x] Database records exist (or migration created) - New migration for all PA tables
- [ ] Country-specific data handled (CO vs MX) - PA is Colombia-only feature

### F. External API Contract (Integration only)
Not applicable - no external API integration.

### G. Query Specification (Reporting only)
Not applicable - simple CRUD and processing, not complex reporting queries.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| session_id | session_id | string | Processing session identifier |
| cuenta_finkargo | cuenta_finkargo | string | Account number |
| cuenta_homologacion | cuenta_homologacion | string | Homologation account |
| nombre_homologacion | nombre_homologacion | string | Homologation name |
| tipo_transaccion | tipo_transaccion | string | Transaction type |
| tipo_comprobante | tipo_comprobante | string | Document type |
| categoria | categoria | string | Main category |
| subcategoria | subcategoria | string | Sub-category |
| clasificacion | clasificacion | string | Detailed classification |
| nexo | nexo | string | Link/connection value |
| total_rows | total_rows | number | Total source rows |
| pa_rows | pa_rows | number | Filtered PA rows |
| debito_sum | debito_sum | number | Sum of debits |
| credito_sum | credito_sum | number | Sum of credits |
| balance_valid | balance_valid | boolean | Validation result |

## Implementation Plan

### Phase 1: Foundation
1. **Database Setup**:
   - Create migration for PA tables (5 tables: catalog, classification_rules, clasificacion_cuenta_rules, nexo_rules, processing_history)
   - Create migration for FINANCE_ADMIN role
   - Add sequences and functions for history IDs

2. **Backend DTOs**:
   - Create `pa_dtos.py` with all request/response models
   - Define enums for status, rule types

3. **Repository Layer**:
   - Create `pa_rules_repository.py` with CRUD for all rule tables
   - Create history repository methods

### Phase 2: Core Implementation
1. **Rules Management Service**:
   - Excel parsing for each rule type
   - Bulk insert/replace logic
   - Validation of rule data

2. **Cleanup Service (Step 1)**:
   - Filter source data by PA accounts
   - Add homologation columns from catalog
   - Rename columns (Saldo → Valor COP, Importe → Valor USD)
   - Balance validation (sum debito = sum credito)

3. **Classification Engine (Step 2)**:
   - Rule matching by transaction type + document type
   - Date-based subcategoria logic (first day of month)
   - Account name pattern matching for clasificacion
   - Nexo lookup
   - Special business rules (Acreedores Fiduciarios override)

4. **API Endpoints**:
   - Rules upload endpoints (POST /rules/catalog/upload, etc.)
   - Rules retrieval endpoints (GET /rules/catalog, etc.)
   - Processing endpoints (POST /process/upload, GET /process/{id}/clean, etc.)
   - History endpoint (GET /history)

### Phase 3: Integration
1. **Frontend Types & Services**:
   - TypeScript interfaces matching backend DTOs
   - API client functions for all endpoints

2. **Rules Management Page**:
   - Multi-file uploader component
   - Rules viewer with tabs for each table
   - Upload status and validation feedback

3. **Report Processing Page**:
   - Two-tab layout (Process, History)
   - Step-by-step processing UI
   - Validation stats display
   - Download buttons for each step

4. **Routing & Navigation**:
   - Add routes to App.tsx
   - Add menu items to sidebar/department page
   - Apply role protection

## Step by Step Tasks

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` to understand E2E test format
- Read `.claude/commands/e2e/test_risk_dashboard.md` as example
- Create `.claude/commands/e2e/test_pa_report_classification.md` with:
  - User story and prerequisites
  - Test steps for rules upload (admin)
  - Test steps for report processing (finance user)
  - Success criteria and expected screenshots

### Step 2: Database Migrations
- Create `backend/database/migration_pa_classification.sql`:
  - `pa_account_catalog` table with cuenta_finkargo, cuenta_homologacion, nombre_homologacion
  - `pa_classification_rules` table with tipo_transaccion, tipo_comprobante, categoria, subcategoria_base, etc.
  - `pa_clasificacion_cuenta_rules` table with cuenta_nombre_patron, clasificacion
  - `pa_nexo_rules` table with cuenta_nombre_patron, nexo
  - `pa_processing_history` table with session_id, filename, stats JSONB, file URLs
  - Sequences for PA history IDs
  - RLS policies for authenticated users
- Create `backend/database/migration_add_finance_admin_role.sql`:
  - Document that finance_admin role should be added to user_profiles

### Step 3: Backend DTOs
- Create `backend/src/interface/pa_dtos.py`:
  - `PAAccountCatalogEntry` - account catalog record
  - `PAClassificationRule` - main classification rule
  - `PAClasificacionCuentaRule` - account name → classification
  - `PANexoRule` - account name → nexo
  - `PARulesUploadRequest` - file upload request
  - `PARulesUploadResponse` - upload result with counts
  - `PAProcessingRequest` - NetSuite file upload
  - `PACleanedResponse` - Step 1 result with validation stats
  - `PAClassifiedResponse` - Step 2 result
  - `PAProcessingStats` - statistics (total_rows, pa_rows, balance_valid, etc.)
  - `PAHistoryRecord` - history entry
  - `PAProcessingStatus` enum (uploading, cleaning, cleaned, classifying, classified, failed)

### Step 4: Backend Repository
- Create `backend/src/repositorio/pa_rules_repository.py`:
  - `__init__` with Supabase client
  - `bulk_upsert_catalog(entries: List[dict])` - replace all catalog entries
  - `get_catalog()` - return all catalog entries
  - `get_catalog_entry(cuenta_finkargo: str)` - lookup single entry
  - `bulk_upsert_classification_rules(rules: List[dict])`
  - `get_classification_rules()`
  - `bulk_upsert_clasificacion_cuenta_rules(rules: List[dict])`
  - `get_clasificacion_cuenta_rules()`
  - `bulk_upsert_nexo_rules(rules: List[dict])`
  - `get_nexo_rules()`
  - `create_history_record(data: dict)`
  - `update_history_record(session_id: str, data: dict)`
  - `get_history(limit: int, offset: int)`
  - `get_history_by_session(session_id: str)`

### Step 5: Backend Rules Service
- Create `backend/src/core/servicios/pa_rules_service.py`:
  - `parse_catalog_excel(file: UploadFile)` - read Excel, extract cuenta_finkargo, cuenta_homologacion, nombre_homologacion
  - `parse_classification_rules_excel(file: UploadFile)` - read Excel, extract all classification rule fields
  - `parse_clasificacion_cuenta_rules_excel(file: UploadFile)`
  - `parse_nexo_rules_excel(file: UploadFile)`
  - `upload_catalog(file: UploadFile)` - parse + store
  - `upload_classification_rules(file: UploadFile)` - parse + store
  - `upload_clasificacion_cuenta_rules(file: UploadFile)`
  - `upload_nexo_rules(file: UploadFile)`
  - Validation for required columns, data types

### Step 6: Backend Cleanup Service (Step 1)
- Create `backend/src/core/servicios/pa_cleanup_service.py`:
  - `__init__` with repository dependency
  - `process_netsuite_file(file: UploadFile, session_id: str)`:
    - Read Excel into DataFrame
    - Get PA account catalog
    - Filter rows where "Cuenta (línea): Número" is in catalog
    - Add "PA" column with "X"
    - Rename "Saldo" → "Valor COP"
    - Rename "Importe (moneda extranjera)" → "Valor USD"
    - Lookup cuenta_homologacion and nombre_homologacion from catalog
    - Calculate validation stats (sum debito, sum credito, balance_valid)
    - Store intermediate file in memory or temp storage
    - Update history record
    - Return stats + cleaned DataFrame
  - `generate_cleaned_excel(session_id: str)` - create downloadable Excel from stored data

### Step 7: Backend Classification Engine
- Create `backend/src/core/servicios/pa_classification_engine.py`:
  - `PAAllRules` class to hold all rules loaded from repository
    - `get_catalog_entry(cuenta_numero)`
    - `find_classification_rule(tipo_transaccion, tipo_comprobante, numero_documento)`
    - `find_clasificacion_cuenta_rule(cuenta_nombre, categoria)`
    - `find_nexo(cuenta_nombre)`
  - `PAClassificationEngine` class:
    - `__init__(rules: PAAllRules)`
    - `classify_record(record: dict) -> dict`:
      - Get homologation from catalog
      - Find matching classification rule
      - Apply date logic for subcategoria
      - Determine clasificacion (hierarchy: account name keywords → rules → default)
      - Determine nexo
      - Determine comprobacion_saldos (hardcoded account list)
      - Apply special homologation override (3505 → 35051500101001)
      - Return dict with all 8 output columns
    - `_apply_date_logic(fecha, subcategoria_base)` - first day of month logic
    - `_determine_clasificacion(cuenta_nombre, categoria, rules, main_rule)`
    - `_determine_comprobacion_saldos(cuenta_numero, main_rule)`
  - Constants for hardcoded cartera_pa_accounts list

### Step 8: Backend Report Service
- Create `backend/src/core/servicios/pa_report_service.py`:
  - Orchestrate full processing flow
  - `upload_netsuite_file(file: UploadFile, user_id: str)`:
    - Generate session_id
    - Create history record (status=uploading)
    - Store original file temporarily
    - Return session_id
  - `run_cleanup(session_id: str)`:
    - Call cleanup service
    - Update history with cleaned stats
    - Store cleaned DataFrame
    - Return stats
  - `run_classification(session_id: str)`:
    - Load cleaned data
    - Load all rules
    - Classify each record
    - Generate classified Excel
    - Update history (status=classified)
    - Return stats
  - `get_cleaned_download(session_id: str)` - return cleaned Excel bytes
  - `get_classified_download(session_id: str)` - return classified Excel bytes
  - Session data storage (in-memory dict for MVP, consider Redis later)

### Step 9: Backend API Routes
- Create `backend/src/adapter/rest/pa_routes.py`:
  - `router = APIRouter(prefix="/api/finance/pa", tags=["Finance - Reporte PA"])`
  - Rules endpoints (require finance_admin role):
    - `POST /rules/catalog/upload` - upload PA account catalog Excel
    - `GET /rules/catalog` - get current catalog entries
    - `POST /rules/classification/upload` - upload main classification rules
    - `GET /rules/classification` - get classification rules
    - `POST /rules/clasificacion-cuenta/upload` - upload clasificacion cuenta rules
    - `GET /rules/clasificacion-cuenta` - get clasificacion cuenta rules
    - `POST /rules/nexo/upload` - upload nexo rules
    - `GET /rules/nexo` - get nexo rules
  - Processing endpoints (require finance role):
    - `POST /process/upload` - upload NetSuite file, return session_id
    - `POST /process/{session_id}/clean` - run cleanup step
    - `GET /process/{session_id}/clean/stats` - get cleanup stats
    - `GET /process/{session_id}/clean/download` - download cleaned Excel
    - `POST /process/{session_id}/classify` - run classification step
    - `GET /process/{session_id}/classify/stats` - get classification stats
    - `GET /process/{session_id}/classify/download` - download classified Excel
  - History endpoint:
    - `GET /history` - get processing history with pagination

### Step 10: Register Routes in main.py
- Edit `backend/main.py`:
  - Import `pa_routes` from `src.adapter.rest`
  - Add `app.include_router(pa_routes.router)`

### Step 11: Add RBAC Dependencies
- Edit `backend/src/adapter/rest/rbac_dependencies.py`:
  - Add `require_finance_role = require_roles(['finance', 'finance_admin'])`
  - Add `require_finance_admin_role = require_roles(['finance_admin'])`

### Step 12: Frontend TypeScript Types
- Create `frontend/src/types/financePA.ts`:
  - `PAAccountCatalogEntry` interface
  - `PAClassificationRule` interface
  - `PAClasificacionCuentaRule` interface
  - `PANexoRule` interface
  - `PAProcessingStats` interface
  - `PACleanedResponse` interface
  - `PAClassifiedResponse` interface
  - `PAHistoryRecord` interface
  - `PARulesUploadResponse` interface
  - `PAProcessingStatus` enum/type

### Step 13: Frontend Types - Add UserRole
- Edit `frontend/src/types/index.ts`:
  - Add `FINANCE = 'finance'` to UserRole type
  - Add `FINANCE_ADMIN = 'finance_admin'` to UserRole type
  - Add to UserRole const object

### Step 14: Frontend API Service
- Create `frontend/src/services/financeServicePA.ts`:
  - Import apiClient from existing pattern
  - `uploadCatalog(file: File)` - POST /api/finance/pa/rules/catalog/upload
  - `getCatalog()` - GET /api/finance/pa/rules/catalog
  - `uploadClassificationRules(file: File)`
  - `getClassificationRules()`
  - `uploadClasificacionCuentaRules(file: File)`
  - `getClasificacionCuentaRules()`
  - `uploadNexoRules(file: File)`
  - `getNexoRules()`
  - `uploadNetsuiteFile(file: File)` - returns session_id
  - `runCleanup(sessionId: string)` - returns stats
  - `downloadCleanedFile(sessionId: string)` - returns Blob
  - `runClassification(sessionId: string)` - returns stats
  - `downloadClassifiedFile(sessionId: string)` - returns Blob
  - `getHistory()` - returns PAHistoryRecord[]
  - `triggerDownload(blob: Blob, filename: string)` - utility function

### Step 15: Frontend Rules Uploader Component
- Create `frontend/src/components/forms/FKPARulesUploader.tsx`:
  - Four file upload sections (Catalog, Classification, Clasificación Cuenta, Nexo)
  - Use react-hook-form pattern
  - MUI FileUpload components
  - Upload status indicators
  - Error handling and display
  - Call financeServicePA upload functions

### Step 16: Frontend Rules Viewer Component
- Create `frontend/src/components/forms/FKPARulesViewer.tsx`:
  - Tabs for each rule type
  - MUI DataGrid for displaying rules
  - Refresh button to reload data
  - Row count indicators
  - Loading states

### Step 17: Frontend Cleaned Results Component
- Create `frontend/src/components/forms/FKPACleanedResults.tsx`:
  - Display validation stats (total rows, PA rows, debito sum, credito sum)
  - Balance validation indicator (green check or red warning)
  - Download Cleaned File button
  - Proceed to Classification button
  - Loading/processing states

### Step 18: Frontend Classified Results Component
- Create `frontend/src/components/forms/FKPAClassifiedResults.tsx`:
  - Display classification stats (records classified, unclassified count)
  - Warnings for unclassified records
  - Download Final Report button
  - Success message
  - Loading states

### Step 19: Frontend NetSuite File Uploader
- Create `frontend/src/components/forms/FKPAFileUploader.tsx`:
  - Single Excel file upload
  - File validation (.xlsx, .xls)
  - Upload progress indicator
  - File name display
  - Clear/remove functionality

### Step 20: Frontend Rules Admin Page
- Create `frontend/src/pages/finance/ReglasClasificacionPA.tsx`:
  - Page header with title "Reglas de Clasificación PA"
  - Two main sections: Upload Rules, View Current Rules
  - Use FKPARulesUploader component
  - Use FKPARulesViewer component
  - Instructions/help text

### Step 21: Frontend Report Processing Page
- Create `frontend/src/pages/finance/ReportePA.tsx`:
  - Page header with title "Reporte PA"
  - Two tabs: "Procesar Reporte", "Historial"
  - Tab 0 - Process:
    - Step 1: File upload with FKPAFileUploader
    - Step 2: Show FKPACleanedResults after cleanup
    - Step 3: Show FKPAClassifiedResults after classification
  - Tab 1 - History:
    - DataGrid with processing history
    - Download buttons for each session
  - Follow ReporteriaAutomaticaCO.tsx patterns

### Step 22: Add Routes to App.tsx
- Edit `frontend/src/App.tsx`:
  - Import ReportePA and ReglasClasificacionPA pages
  - Add route `/finance/reporte-pa` with RoleProtectedRoute (finance, finance_admin, admin)
  - Add route `/finance/reglas-clasificacion-pa` with RoleProtectedRoute (finance_admin, admin)

### Step 23: Add Menu Navigation
- Edit `frontend/src/pages/DepartmentPage.tsx` or appropriate navigation:
  - Add menu item for "Reporte PA" pointing to `/finance/reporte-pa`
  - Add menu item for "Reglas Clasificación PA" pointing to `/finance/reglas-clasificacion-pa`
  - Apply role-based visibility (finance_admin for rules, finance for processing)

### Step 24: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy

### Unit Tests
- `test_pa_rules_service.py`:
  - Test Excel parsing for each rule type
  - Test validation errors for missing columns
  - Test bulk insert operations
- `test_pa_cleanup_service.py`:
  - Test filtering by PA accounts
  - Test column renaming
  - Test balance validation (valid and invalid cases)
- `test_pa_classification_engine.py`:
  - Test rule matching by transaction type
  - Test date logic (first day vs other days)
  - Test clasificacion hierarchy
  - Test special homologation override
  - Test nexo lookup

### Edge Cases
1. Empty NetSuite file (no rows)
2. No matching PA accounts (all filtered out)
3. Balance mismatch (debito ≠ credito)
4. Unclassified records (no matching rules)
5. Missing catalog entries (accounts in data but not in catalog)
6. Multiple rules matching same record (priority handling)
7. Large file processing (~50k rows)
8. Special characters in account names
9. Invalid date formats
10. Concurrent processing sessions

## Acceptance Criteria

1. **Rules Upload**: Finance admin can upload Excel files for each rule type (catalog, classification, clasificacion cuenta, nexo)
2. **Rules Viewing**: Admin can view current rules in tabular format
3. **File Upload**: Finance user can upload NetSuite Excel file
4. **Cleanup Step**: System filters PA accounts, adds homologation columns, validates balance
5. **Cleanup Download**: User can download cleaned file after Step 1
6. **Classification Step**: System applies all classification rules
7. **Classification Download**: User can download final classified file
8. **8 Output Columns**: All 8 new columns are populated correctly (PA, Categoría, Subcategoría, Clasificación, Nexo, Comprobación saldos, Cuenta Homologación, Nombre Homologación)
9. **Balance Validation**: System correctly validates sum(debito) = sum(credito)
10. **Date Logic**: Subcategoria correctly applies first-day-of-month logic
11. **Special Rules**: Acreedores Fiduciarios override works correctly
12. **History Tracking**: All processing sessions are logged with stats
13. **Role Protection**: Only authorized roles can access each feature
14. **Performance**: Handles 50k rows within reasonable time (<2 minutes)

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run backend tests
cd backend && python -m pytest tests/ -v

# Run backend linting
cd backend && ruff check src/

# Run frontend linting
cd frontend && npm run lint

# Run TypeScript type check
cd frontend && npx tsc --noEmit

# Run frontend build
cd frontend && npm run build
```

**E2E Test Validation:**
Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_report_classification.md` to validate the PA Report Classification feature works end-to-end.

## Notes

### Dependencies
**Backend (already in requirements.txt):**
- `pandas` - Excel processing (already used by other finance features)
- `openpyxl` - Excel read/write (already used)
- No new dependencies required

**Frontend (already in package.json):**
- `@mui/x-data-grid` - Data display (already used)
- `react-hook-form` - Form handling (already used)
- No new dependencies required

### Future Considerations
1. **Redis Session Storage**: Replace in-memory session storage with Redis for multi-instance deployment
2. **Rule Versioning**: Track changes to rules over time, allow rollback
3. **Scheduled Processing**: Add ability to schedule automatic processing
4. **Email Notifications**: Notify users when processing completes
5. **Bulk History Download**: Allow downloading multiple historical reports as ZIP

### Country Specificity
This feature is Colombia-specific. If needed for other countries, the architecture supports extension by adding country-specific rule tables and services.

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created
- [x] E2E test file task included (Step 1)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness

**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented
- [x] Data transformation rules specified (filtering, renaming, adding columns)
- [x] Catalog/lookup dependencies identified (4 rule tables)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (Colombia-only feature)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
