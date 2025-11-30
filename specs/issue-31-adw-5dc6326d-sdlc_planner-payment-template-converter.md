# Feature: Tesorería - Conversión de Historial de Pagos a Template de Aplicación de Pagos

## Feature Description
The Treasury (Tesorería) department needs a tool to convert payment history files ("Historial de Pagos") exported from the core system into a specific format required for payment application in NetSuite. This transformation converts each source row into multiple target rows (one per payment concept type with non-zero values). The feature supports both Colombia and México with country-specific transformation rules and catalog lookups.

Key capabilities:
- Upload and validate "Historial de Pagos" Excel files (53 columns)
- Country-specific transformation logic (Colombia vs México)
- Dynamic row expansion: Each source row generates multiple output rows based on concept types
- Catalog-based lookups for bank accounts and AR accounts
- Special handling for Operaciones Cedidas (NT column) in Colombia
- Spread calculations for FK, Supra, and PA payment types
- Download converted Excel file in NetSuite-compatible template format

## User Story
As a Treasury (Tesorería) department user
I want to upload payment history files and convert them to NetSuite payment application templates
So that I can efficiently apply payments in NetSuite with the correct account mappings and concept breakdowns

## Problem Statement
Treasury staff currently must manually transform payment history data from the core system into the specific format required by NetSuite. This process is:
- Time-consuming: Each payment row must be split into multiple concept rows manually
- Error-prone: Manual lookup of AR accounts and bank accounts leads to mistakes
- Country-specific: Colombia and México have different concept types and account mappings
- Complex: Special rules for Operaciones Cedidas, spread calculations, and adjustments

## Solution Statement
Build a web-based converter tool within the existing Treasury module that:
1. Provides separate interfaces for Colombia and México transformations
2. Automatically validates uploaded files for required columns
3. Applies country-specific transformation rules to expand rows by concept type
4. Looks up correct account and AR account IDs from embedded catalogs
5. Calculates adjustments for INTERESES and MORATORIOS concepts
6. Generates downloadable Excel files in the correct NetSuite template format

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Use RBAC dependency `require_roles(['tesoreria'])` which allows admin bypass by default
- Frontend Protection: Use `RoleProtectedRoute` with `allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}` for Treasury-specific routes

## Relevant Files
Use these files to implement the feature:

### Backend Files
- **`backend/src/adapter/rest/finance_routes.py`** - Reference for Excel upload patterns with FastAPI, file validation, and streaming responses
- **`backend/src/adapter/rest/rbac_dependencies.py`** - RBAC implementation for adding `require_tesoreria_role` dependency
- **`backend/src/core/servicios/excel_validation_service.py`** - Reference for Excel file processing with pandas
- **`backend/src/interface/finance_dtos.py`** - Reference for DTO patterns with Pydantic v2 validation
- **`backend/main.py`** - To register the new treasury routes

### Frontend Files
- **`frontend/src/pages/tesoreria/PlantillasNetSuite.tsx`** - Existing placeholder page to be replaced with the landing page
- **`frontend/src/components/ui/FKSidebarWithCollapse.tsx`** - Sidebar already has Treasury module configured; need to add sub-routes for Colombia and México
- **`frontend/src/App.tsx`** - Add new routes for Colombia and México converters
- **`frontend/src/services/financeService.ts`** - Reference for service patterns with file upload and blob download
- **`frontend/src/types/finance.ts`** - Reference for type definitions
- **`frontend/src/types/index.ts`** - Add TESORERIA role to UserRole enum if not present
- **`frontend/src/components/forms/FKExcelUploader.tsx`** - Reference for drag-drop Excel upload component

### Reference Files
- **`Example Files for Reqs/FIN_ Definicion Template para Aplicación de pagos.xlsx`** - Template definition with column mappings and catalogs (Catalogo CO, Catalogo MX)
- **`Example Files for Reqs/Historial_de_pagos_2025-11-25_2025-11-29.xlsx`** - Sample source file structure

### E2E Test References
- **`.claude/commands/test_e2e.md`** - E2E test runner instructions
- **`.claude/commands/e2e/test_login.md`** - Login E2E test pattern
- **`.claude/commands/e2e/test_excel_upload.md`** - Excel upload E2E test pattern

### New Files

**Backend:**
- `backend/src/adapter/rest/tesoreria_routes.py` - New API routes for Treasury payment template conversion
- `backend/src/core/servicios/payment_template_service.py` - Core business logic for payment conversion
- `backend/src/interface/tesoreria_dtos.py` - DTOs for Treasury requests/responses
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Embedded catalog data for CO and MX lookups

**Frontend:**
- `frontend/src/pages/tesoreria/PlantillasNetSuiteLanding.tsx` - Landing page with Colombia/México selection cards
- `frontend/src/pages/tesoreria/PlantillasNetSuiteCO.tsx` - Colombia payment template converter
- `frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx` - México payment template converter
- `frontend/src/components/forms/FKHistorialUploader.tsx` - Specialized uploader for Historial de Pagos files
- `frontend/src/services/treasuryService.ts` - API service for Treasury operations
- `frontend/src/types/tesoreria.ts` - TypeScript types for Treasury module

**E2E Test:**
- `.claude/commands/e2e/test_payment_template_converter.md` - E2E test for payment template conversion

## Implementation Plan

### Phase 1: Foundation
1. **Backend DTOs and Catalogs**
   - Create `tesoreria_dtos.py` with Pydantic models for:
     - `HistorialPagosUploadResponse` - Validation results
     - `ConversionRequest` - Country and file reference
     - `ConversionResponse` - Statistics and download info
   - Create `payment_catalogs.py` with embedded catalog data:
     - Colombia AR account mappings by concept type (standard vs NT)
     - México AR account mappings by concept type
     - Bank account ID lookups (to be populated from catalog sheets)

2. **Frontend Types and Service**
   - Create `tesoreria.ts` with TypeScript interfaces
   - Create `treasuryService.ts` with upload and convert methods
   - Add `TESORERIA` to `UserRole` enum if not present

### Phase 2: Core Implementation
1. **Backend Payment Template Service**
   - Create `payment_template_service.py` with methods:
     - `validate_historial_file(file, country)` - Validate columns exist
     - `convert_to_template(file, country)` - Main conversion logic
     - `_process_colombia_row(row)` - Colombia-specific row expansion
     - `_process_mexico_row(row)` - México-specific row expansion
     - `_lookup_araccount(concept_type, country, is_nt)` - AR account lookup
     - `_calculate_spreads(row, country)` - Spread calculations

2. **Backend API Routes**
   - Create `tesoreria_routes.py` with endpoints:
     - `POST /api/tesoreria/validate` - Validate uploaded file
     - `POST /api/tesoreria/convert/{country}` - Convert and return Excel file
     - `GET /api/tesoreria/catalogs/{country}` - Get catalog data (optional)

3. **Frontend Pages**
   - Replace `PlantillasNetSuite.tsx` with landing page showing CO/MX cards
   - Create `PlantillasNetSuiteCO.tsx` with:
     - File upload area
     - Validation preview (row count, column status)
     - Convert button
     - Download result
   - Create `PlantillasNetSuiteMX.tsx` (same pattern as CO)

4. **Frontend Components**
   - Create `FKHistorialUploader.tsx` for drag-drop upload
   - Create `FKConversionPreview.tsx` for validation results display

### Phase 3: Integration
1. **Routing and Navigation**
   - Update `App.tsx` with new routes:
     - `/tesoreria/plantillas-netsuite` - Landing page
     - `/tesoreria/plantillas-netsuite/colombia` - Colombia converter
     - `/tesoreria/plantillas-netsuite/mexico` - México converter
   - Update `FKSidebarWithCollapse.tsx` treasury modules to include CO/MX sub-items

2. **Role Protection**
   - Add `require_tesoreria_role` to RBAC dependencies
   - Wrap treasury routes with `RoleProtectedRoute`

3. **E2E Testing**
   - Create E2E test file for payment template conversion workflow

## Step by Step Tasks

### Step 1: Create E2E Test File for Payment Template Converter
- Read `.claude/commands/test_e2e.md` to understand E2E test format
- Read `.claude/commands/e2e/test_excel_upload.md` for Excel upload test pattern
- Create `.claude/commands/e2e/test_payment_template_converter.md` with test steps to validate:
  - Landing page shows Colombia and México options
  - Colombia route loads correctly
  - File upload accepts .xlsx files
  - Validation preview displays correctly
  - Convert button generates downloadable file
  - Downloaded file has expected format

### Step 2: Add TESORERIA Role to Frontend Types
- Open `frontend/src/types/index.ts`
- Add `TESORERIA = 'tesoreria'` to `UserRole` enum if not present
- Verify role string matches backend expectations

### Step 3: Create Backend DTOs for Treasury
- Create `backend/src/interface/tesoreria_dtos.py`
- Define Pydantic models:
  - `HistorialValidationError` - Row/column/message
  - `HistorialValidationResponse` - success, row counts, errors, preview data
  - `ConversionStats` - rows processed, output rows, errors
  - `ConceptType` enum for payment concepts
- Follow patterns from `finance_dtos.py`

### Step 4: Create Payment Catalogs Module
- Create `backend/src/core/servicios/catalogs/` directory
- Create `backend/src/core/servicios/catalogs/__init__.py`
- Create `backend/src/core/servicios/catalogs/payment_catalogs.py`
- Define catalog data structures:
  - `COLOMBIA_AR_ACCOUNTS` dict mapping (concept_type, is_nt) → araccount_id
  - `MEXICO_AR_ACCOUNTS` dict mapping concept_type → araccount_id
  - `COLOMBIA_BANK_ACCOUNTS` dict for bank name → account_id lookup
  - `MEXICO_BANK_ACCOUNTS` dict for bank name → account_id lookup
- Populate from catalog sheets in reference Excel file

### Step 5: Create Payment Template Service
- Create `backend/src/core/servicios/payment_template_service.py`
- Implement class `PaymentTemplateService`:
  - `__init__(self)` - Initialize catalogs
  - `async validate_historial(self, file: UploadFile, country: str) -> HistorialValidationResponse`
    - Read Excel with pandas
    - Check required columns exist based on country
    - Return validation results with preview
  - `async convert_to_netsuite_template(self, file: UploadFile, country: str) -> bytes`
    - Parse source Excel
    - For each row, call country-specific processor
    - Collect all output rows
    - Generate output Excel with correct columns
    - Return bytes
  - `_process_colombia_row(self, row: dict) -> List[dict]`
    - Check each concept column for non-zero values
    - Generate output row for each non-zero concept
    - Apply INTERESES/MORATORIOS adjustment calculations
    - Lookup AR accounts (check NT column for Operaciones Cedidas)
  - `_process_mexico_row(self, row: dict) -> List[dict]`
    - Handle México-specific concept columns
    - Apply adjustment calculations
    - Lookup AR accounts from México catalog
  - `_get_araccount(self, concept_type: str, country: str, is_nt: bool) -> int`
  - `_calculate_payment_amount(self, concept_type: str, row: dict, country: str) -> float`
- Use openpyxl for Excel generation

### Step 6: Create Treasury API Routes
- Create `backend/src/adapter/rest/tesoreria_routes.py`
- Define router with prefix `/api/tesoreria`
- Add RBAC dependency: `require_tesoreria_role = require_roles(['tesoreria'])`
- Implement endpoints:
  - `POST /validate/{country}` - Upload and validate file
    - Accept UploadFile, country path param
    - Return validation response
  - `POST /convert/{country}` - Convert and download
    - Accept UploadFile, country path param
    - Return StreamingResponse with Excel file
- Register router in `backend/main.py`

### Step 7: Create Frontend Treasury Service
- Create `frontend/src/services/treasuryService.ts`
- Implement service object with methods:
  - `validateHistorial(file: File, country: string): Promise<HistorialValidationResponse>`
  - `convertToNetsuiteTemplate(file: File, country: string): Promise<Blob>`
- Follow patterns from `financeService.ts`
- Use appropriate timeouts for file processing

### Step 8: Create Frontend Treasury Types
- Create `frontend/src/types/tesoreria.ts`
- Define interfaces:
  - `HistorialValidationError`
  - `HistorialValidationResponse`
  - `ConversionStats`
  - `ConceptTypeStats` - counts per concept type
- Export all types

### Step 9: Create Historial Uploader Component
- Create `frontend/src/components/forms/FKHistorialUploader.tsx`
- Props: `onUploadSuccess`, `onUploadError`, `country`, `disabled`
- Features:
  - Drag-drop zone with MUI styling
  - File type validation (.xlsx only)
  - Upload progress indicator
  - Validation result display
- Follow patterns from `FKExcelUploader.tsx`

### Step 10: Update PlantillasNetSuite as Landing Page
- Modify `frontend/src/pages/tesoreria/PlantillasNetSuite.tsx`
- Replace current placeholder with landing page design:
  - Header: "Plantillas para Cargar NetSuite"
  - Two cards: Colombia (flag + description) and México (flag + description)
  - Each card links to respective converter route
  - Use MUI Grid, Card, CardContent, Button components
- Add navigation to `/tesoreria/plantillas-netsuite/colombia` and `/tesoreria/plantillas-netsuite/mexico`

### Step 11: Create Colombia Converter Page
- Create `frontend/src/pages/tesoreria/PlantillasNetSuiteCO.tsx`
- Implement full converter workflow:
  - Header with back button and title "Aplicación de Pagos - Colombia"
  - Section 1: File upload (FKHistorialUploader)
  - Section 2: Validation preview (row counts, column status, estimated output rows)
  - Section 3: Convert button + download result
- State management:
  - `file: File | null`
  - `validationResult: HistorialValidationResponse | null`
  - `isConverting: boolean`
  - `downloadUrl: string | null`
- Use treasuryService for API calls

### Step 12: Create México Converter Page
- Create `frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx`
- Follow same pattern as Colombia page
- Change header to "Aplicación de Pagos - México"
- Pass 'mexico' as country parameter to service calls

### Step 13: Update App.tsx with New Routes
- Open `frontend/src/App.tsx`
- Import new page components:
  - `PlantillasNetSuiteLanding` (renamed from PlantillasNetSuite)
  - `PlantillasNetSuiteCO`
  - `PlantillasNetSuiteMX`
- Add routes inside protected section:
  ```tsx
  {/* Treasury Routes */}
  <Route path="tesoreria/plantillas-netsuite" element={<PlantillasNetSuiteLanding />} />
  <Route path="tesoreria/plantillas-netsuite/colombia" element={
    <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
      <PlantillasNetSuiteCO />
    </RoleProtectedRoute>
  } />
  <Route path="tesoreria/plantillas-netsuite/mexico" element={
    <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
      <PlantillasNetSuiteMX />
    </RoleProtectedRoute>
  } />
  ```

### Step 14: Update Sidebar with Colombia/México Sub-items
- Open `frontend/src/components/ui/FKSidebarWithCollapse.tsx`
- Update `treasuryModules` array to include Colombia and México sub-items:
  ```typescript
  const treasuryModules: TreasuryModule[] = [
    {
      id: 'plantillas-netsuite',
      name: 'Plantillas para Cargar NetSuite',
      route: '/tesoreria/plantillas-netsuite',
      icon: <Description fontSize="small" />,
    },
    {
      id: 'plantillas-co',
      name: 'Aplicación Pagos CO',
      route: '/tesoreria/plantillas-netsuite/colombia',
      icon: <Flag fontSize="small" />,
    },
    {
      id: 'plantillas-mx',
      name: 'Aplicación Pagos MX',
      route: '/tesoreria/plantillas-netsuite/mexico',
      icon: <Flag fontSize="small" />,
    },
  ];
  ```
- Import `Flag` icon from `@mui/icons-material`

### Step 15: Add RBAC Dependency for Treasury
- Open `backend/src/adapter/rest/rbac_dependencies.py`
- Add pre-configured treasury role dependency:
  ```python
  require_tesoreria_role = require_roles(['tesoreria'])
  ```

### Step 16: Register Treasury Routes in Main App
- Open `backend/main.py`
- Import treasury routes: `from src.adapter.rest import tesoreria_routes`
- Register router: `app.include_router(tesoreria_routes.router)`

### Step 17: Run All Validation Commands
- Execute all validation commands to ensure zero regressions:
  - Backend pytest
  - Backend linting
  - Frontend linting
  - TypeScript type check
  - Frontend build
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_payment_template_converter.md` E2E test

## Testing Strategy

### Unit Tests
- `backend/tests/test_payment_template_service.py`:
  - Test `validate_historial` with valid/invalid files
  - Test `convert_to_netsuite_template` with sample Colombia data
  - Test `convert_to_netsuite_template` with sample México data
  - Test `_process_colombia_row` row expansion logic
  - Test `_process_mexico_row` row expansion logic
  - Test AR account lookups for each concept type
  - Test INTERESES/MORATORIOS adjustment calculations
  - Test NT (Operaciones Cedidas) handling for Colombia

### Edge Cases
- File with zero values in all concept columns (should generate no output rows)
- File with negative adjustment values (INTERESES = Corrientes - Descuento - Condonación)
- File with NT column populated (should use Operaciones Cedidas AR accounts)
- File with missing optional columns (should handle gracefully)
- File with very large row count (100+ rows)
- File with mixed currency values
- File with empty rows (should skip)
- File with special characters in client names

## Acceptance Criteria
1. Navigation to Tesorería → Plantillas para Cargar NetSuite shows landing page with Colombia/México options
2. Landing page cards navigate to correct country-specific routes
3. Each country route loads correctly with upload interface
4. Upload accepts only .xlsx files (rejects other formats)
5. Validates source file has required columns for selected country
6. Displays validation preview with:
   - Source row count
   - Column validation status
   - Estimated output rows
7. Convert button triggers transformation
8. Generates correct number of output rows (one per non-zero concept)
9. Correctly calculates payment_amount with adjustments for INTERESES and MORATORIOS
10. Correctly looks up araccount from country-specific catalogs
11. Colombia correctly differentiates between standard and Operaciones Cedidas (NT column check)
12. México correctly handles all commission types (COMISION DESEMBOLSO, DISPOSICION, SWIFT, etc.)
13. Output file downloads in correct NetSuite template format with all required columns
14. Handles files with 100+ rows efficiently (< 10 seconds)
15. Displays meaningful error messages for invalid data
16. Role protection works correctly - only tesoreria and admin roles can access
17. All validation commands pass with zero regressions

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_payment_template_converter.md` E2E test file to validate the payment template conversion workflow works correctly

## Notes

### Column Mappings (from Template Definition)

**Colombia Source Columns (Historial de Pagos):**
- A: Cliente
- B: Identificación del cliente → customer_external_id
- C: Código de desembolso → invoice_core_id
- D: Código de recaudo → payment_ref
- J: Fecha de pago → payment_date
- L: Moneda → currency
- N: Tasa de cambio FK/en línea → exchangerate (for SUPRA/PA only)
- P: Capital
- Q: 4x1000
- R: Fondo de garantías
- S: IVA Fondo de garantías
- T: Seguro + IVA
- U: Servicio de originación
- X: Servicio de giro + IVA
- Z: Costos adicionales
- AA: Intereses Corrientes
- AB-AE: Intereses de Mora PAR columns
- AF: Descuento aplicado
- AH: Condonación intereses corrientes
- AI-AL: Condonación mora columns
- AM: Banco remitente
- AW: NT (Operaciones Cedidas flag)

**México Source Columns (Historial de Pagos):**
- Similar structure with different column positions for commissions
- U: Comision del desembolso + IVA
- V: Comision por disposicion de crédito + IVA
- W: Comision swift
- X: Comision administracion y manejo
- Y: Comision de apertura

### Catalog Data to Embed

**Colombia AR Accounts:**
| concept_type | Standard | Operaciones Cedidas (NT) |
|--------------|----------|--------------------------|
| CAPITAL | 302 | 304 |
| COSTOS FIJOS | 258 | 310 |
| SEGUROS | 1387 | 1474 |
| INTERESES | 258 | 259 |
| MORATORIOS | 258 | 259 |

**México AR Accounts:**
| concept_type | araccount_id |
|--------------|--------------|
| CAPITAL | 2114 |
| SEGUROS | 2114 |
| COMISION DESEMBOLSO | 2114 |
| COMISION DISPOSICION | 2114 |
| COMISION SWIFT | 2114 |
| COMISION ADMINISTRACION | 2114 |
| COMISION APERTURA | 2114 |
| COSTOS ADICIONALES | 2114 |
| INTERESES | 2115 |
| MORATORIOS | 2117 |

### Future Enhancements
- Database-backed catalogs for easier updates
- Transformation audit log with row-by-row details
- Batch processing for multiple files
- Preview of transformed data before download
- Integration with NetSuite API for direct upload
- Bank account catalog population (currently uses placeholder values)
- Spread calculations implementation (requires Tasa BanRep data source)
