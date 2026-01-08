# Feature: Exchange Declaration to Historial de Pagos Matching

## Feature Description

Implement a Treasury module feature that automatically matches Exchange Declarations (Declaraciones de Cambio) from a local folder structure to Historial de Pagos (Payment History) records. The system uses fuzzy customer name matching, date tolerance (±7 days), and amount tolerance (±$2.00) to handle one-to-many payment-to-operation mappings.

The feature enables treasury users to:
1. Upload Historial de Pagos Excel files
2. Group payment rows by customer and date, summing capital amounts
3. Match payment groups to declarations using configurable tolerance
4. Review and manually override matches when needed
5. Download enriched Excel with "Declaracion de Cambio Numero" and "DC Nombre" columns populated

## User Story

As a **Treasury (tesoreria) team member**
I want to **automatically match exchange declarations to payment history records**
So that I can **efficiently populate declaration numbers in payment records without manual lookup**

## Problem Statement

Treasury users currently spend significant manual effort cross-referencing Exchange Declarations (PDF files organized in folders by customer/date/amount) with Historial de Pagos records. This process is error-prone and time-consuming because:
- Payments may span multiple rows that need to be grouped and summed
- Customer names may vary slightly between systems
- Declaration dates may not exactly match payment dates
- Manual lookup across 170+ customer folders is tedious

## Solution Statement

Build an automated matching system that:
1. **Parses Historial de Pagos Excel** - Extracts and validates all 20 columns
2. **Groups payments** - Aggregates rows by (customer, date) and sums capital amounts
3. **Matches declarations** - Uses fuzzy matching with configurable tolerance for customer names, dates, and amounts
4. **Provides review UI** - Shows match results with confidence scores and allows manual overrides
5. **Generates enriched Excel** - Outputs the original file with declaration columns populated

## Access Control

- **Required Role(s)**: `tesoreria`, `admin`
- **Backend Protection**: Use `require_roles(['tesoreria'])` from `rbac_dependencies.py`
- **Frontend Protection**: Use `<RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>` for the matching page route

## Relevant Files

Use these files to implement the feature:

### Backend (Existing - Reference Patterns)
- `backend/src/adapter/rest/tesoreria_routes.py` - Existing treasury routes pattern, add new router here or create separate file
- `backend/src/core/servicios/payment_template_service.py` - Reference for Excel processing patterns, column mapping, and validation
- `backend/src/interface/tesoreria_dtos.py` - Existing treasury DTOs, extend with matching DTOs
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Reference for column mappings and catalogs
- `backend/main.py` - Add new router registration
- `backend/requirements.txt` - Add rapidfuzz dependency

### Frontend (Existing - Reference Patterns)
- `frontend/src/components/forms/FKHistorialUploader.tsx` - File upload pattern with drag & drop, validation display
- `frontend/src/components/declaraciones/FKMatchingStatisticsCard.tsx` - Statistics display pattern
- `frontend/src/components/declaraciones/FKMatchDetailsTable.tsx` - Match results table pattern with sorting/pagination
- `frontend/src/components/declaraciones/FKManualMatchOverrideForm.tsx` - Manual override form pattern
- `frontend/src/pages/tesoreria/PlantillasNetSuiteCO.tsx` - Treasury page pattern with stepper workflow
- `frontend/src/services/treasuryService.ts` - Treasury API service pattern
- `frontend/src/types/tesoreria.ts` - Treasury types
- `frontend/src/types/matching_results_types.ts` - Matching results types (reusable patterns)
- `frontend/src/App.tsx` - Add route for new page
- `frontend/src/types/index.ts` - UserRole definitions

### E2E Test Pattern Reference
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - E2E test file format example

### New Files

**Backend:**
1. `backend/src/core/servicios/treasury/__init__.py` - Treasury services module init
2. `backend/src/core/servicios/treasury/historial_parser_service.py` - Parse Historial de Pagos Excel with column mapping
3. `backend/src/core/servicios/treasury/payment_group_aggregator.py` - Group payments by (customer, date) and sum capital
4. `backend/src/core/servicios/treasury/declaration_payment_matcher.py` - Fuzzy matching with tolerance configuration
5. `backend/src/core/servicios/treasury/enriched_excel_generator.py` - Generate output Excel with populated columns
6. `backend/src/adapter/rest/treasury_matching_routes.py` - New router for matching endpoints
7. `backend/src/interface/treasury_matching_dtos.py` - DTOs for matching feature

**Frontend:**
1. `frontend/src/pages/treasury/HistorialMatchingPage.tsx` - Main matching workflow page with MUI Stepper
2. `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx` - File upload with grouping preview
3. `frontend/src/components/treasury/FKMatchingConfigForm.tsx` - Tolerance configuration form
4. `frontend/src/components/treasury/FKMatchResultsTable.tsx` - Match results DataGrid
5. `frontend/src/components/treasury/FKManualMatchDialog.tsx` - Manual override modal
6. `frontend/src/components/treasury/FKMatchStatisticsCard.tsx` - Match statistics summary
7. `frontend/src/services/treasuryMatchingService.ts` - API client for matching endpoints
8. `frontend/src/types/treasuryMatching.ts` - TypeScript types for matching feature

**E2E Test:**
1. `.claude/commands/e2e/test_declaration_historial_matching.md` - E2E test for matching workflow

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs)
- [x] **Excel Processing (treasury, finance)** → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP)
- [ ] API Integration (external services)
- [ ] Reporting (queries, history)
- [ ] CRUD Operations (basic data management)

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (Historial de Pagos - 20 columns):**

| Column Name (exact) | Required | Data Type | Validation |
|--------------------|----------|-----------|------------|
| Cliente | Yes | String | Not empty |
| Identificacion del cliente | Yes | String | NIT format |
| Codigo de desembolso | Yes | String | Not empty |
| Codigo de recaudo | No | String | - |
| Numero de factura | No | String | - |
| Fecha de desembolso | Yes | Date | Valid date |
| Fecha de vencimiento | Yes | Date | Valid date |
| Valor del desembolso | Yes | Decimal | > 0 |
| Estado del desembolso | Yes | String | - |
| **Fecha de pago** | **KEY** | Date | Valid date |
| Total pagado | Yes | Decimal | - |
| Moneda | Yes | String | COP/USD |
| Medio de pago | Yes | String | Manual/Pago en linea |
| Tasa de cambio de FK/en linea | No | Decimal | - |
| Total pagado [USD] | Yes | Decimal | - |
| **Capital** | **KEY** | Decimal | Used for grouping sum |
| **Declaracion de Cambio Numero** | **OUTPUT** | String | Target column |
| **DC Nombre** | **OUTPUT** | String | Target column |
| DIM | No | String | - |
| Factura Final | No | String | - |

**Column Mappings (Handle Variations):**
```python
COLUMN_MAPPINGS = {
    'cliente': ['Cliente', 'CLIENTE', 'client', 'Cliente (Razón Social)'],
    'fecha_pago': ['Fecha de pago', 'Fecha Pago', 'FechaPago', 'Fecha Aplicacion'],
    'capital': ['Capital', 'CAPITAL', 'Monto Capital'],
    'identificacion_cliente': ['Identificacion del cliente', 'NIT', 'Identificación'],
    'declaracion_cambio_numero': ['Declaracion de Cambio Numero', 'Declaración de Cambio Número', 'DC Numero'],
    'dc_nombre': ['DC Nombre', 'Nombre DC', 'PDF Nombre'],
}
```

**Output Excel Structure:**
Original file with columns 17 (Declaracion de Cambio Numero) and 18 (DC Nombre) populated based on match results.

**Data Transformation Rules:**
- Multiple rows with same (cliente, fecha_pago) → grouped, capital summed
- One payment group can match one declaration
- Match result populates ALL rows in the group with same declaration info

**Catalog Dependencies:**
- [ ] No AR account mappings needed (this is matching, not payment conversion)
- [ ] No country-specific variations (Colombia-only feature)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| No database persistence | N/A | N/A | Session-based in-memory cache |

**Note:** This feature uses in-memory session storage (dict) for match results during the workflow. No database persistence for match sessions.

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| cliente | cliente | string | Customer name |
| cliente_normalized | cliente_normalized | string | Normalized for matching |
| identificacion_cliente | identificacion_cliente | string | NIT |
| fecha_pago | fecha_pago | string (ISO date) | Key for grouping |
| capital | capital | number (Decimal) | Sum for grouping |
| group_id | group_id | string | UUID for payment group |
| total_capital | total_capital | number (Decimal) | Aggregated capital |
| record_row_numbers | record_row_numbers | number[] | Original Excel rows |
| declaration_id | declaration_id | string | UUID for declaration |
| declaration_number | declaration_number | string | From PDF extraction |
| pdf_file_name | pdf_file_name | string | e.g., "DC 8.111,43.pdf" |
| match_status | match_status | string | matched/partial/unmatched/conflict |
| match_confidence | match_confidence | number | 0.0 to 1.0 |
| date_tolerance_days | date_tolerance_days | number | Default: 7 |
| amount_tolerance | amount_tolerance | number | Default: 2.00 |

## Implementation Plan

### Phase 1: Foundation (Backend)
1. Create treasury services module structure
2. Implement DTOs for matching feature
3. Add rapidfuzz dependency to requirements.txt
4. Implement HistorialParserService for Excel parsing with column mapping

### Phase 2: Core Implementation (Backend)
5. Implement PaymentGroupAggregator for grouping logic
6. Implement DeclarationPaymentMatcher with fuzzy matching algorithm
7. Implement EnrichedExcelGenerator for output generation
8. Create treasury_matching_routes.py with all endpoints
9. Register new router in main.py

### Phase 3: Frontend Foundation
10. Create TypeScript types for matching feature
11. Create treasuryMatchingService API client
12. Create FKHistorialMatchingUploader component

### Phase 4: Frontend UI Components
13. Create FKMatchingConfigForm with tolerance sliders
14. Create FKMatchResultsTable with status chips and sorting
15. Create FKManualMatchDialog for overrides
16. Create FKMatchStatisticsCard for summary

### Phase 5: Integration
17. Create HistorialMatchingPage with MUI Stepper workflow
18. Add route to App.tsx
19. Create E2E test file

## Step by Step Tasks

### Step 1: Add rapidfuzz Dependency
- Add `rapidfuzz>=3.0.0` to `backend/requirements.txt`
- This library provides fast fuzzy string matching (faster than fuzzywuzzy)

### Step 2: Create Treasury Matching DTOs
- Create `backend/src/interface/treasury_matching_dtos.py`
- Define all Pydantic models:
  - `HistorialRecord` - Single row from Excel
  - `PaymentGroup` - Aggregated group with summed capital
  - `DeclarationItem` - Declaration info from inventory
  - `MatchConfig` - Tolerance configuration
  - `MatchResult` - Single match result
  - `HistorialUploadResponse` - Upload response with groups
  - `MatchingSessionResponse` - Full matching response
  - `ManualOverrideRequest` - Override request body

### Step 3: Create Treasury Services Module
- Create `backend/src/core/servicios/treasury/__init__.py`
- Export all services from the module

### Step 4: Implement HistorialParserService
- Create `backend/src/core/servicios/treasury/historial_parser_service.py`
- Parse Excel using pandas with column mapping variations
- Handle accented characters (UTF-8 encoding)
- Validate required columns: Cliente, Fecha de pago, Capital
- Extract and normalize dates to YYYY-MM-DD format
- Return list of HistorialRecord DTOs
- Include row number tracking for later assignment

### Step 5: Implement PaymentGroupAggregator
- Create `backend/src/core/servicios/treasury/payment_group_aggregator.py`
- Group HistorialRecords by (cliente_normalized, fecha_pago)
- Sum Capital amounts per group
- Track original row numbers for each group
- Generate unique group_id (UUID)
- Return list of PaymentGroup DTOs

### Step 6: Implement Customer Name Normalizer
- Add name normalization logic to aggregator or separate utility
- Strip common suffixes: SAS, SA, LTDA, S.A.S., S.A., LIMITADA
- Uppercase, remove accents, trim whitespace
- This enables fuzzy matching across naming variations

### Step 7: Implement DeclarationPaymentMatcher
- Create `backend/src/core/servicios/treasury/declaration_payment_matcher.py`
- Accept inventory items (from existing scanner) and payment groups
- For each payment group:
  1. Filter declarations by customer name (fuzz.ratio >= threshold, default 85)
  2. Filter by date within tolerance (default ±7 days)
  3. Filter by amount within tolerance (default ±$2.00)
  4. Calculate confidence score combining all three factors
  5. Select best match or mark as unmatched/conflict
- Return list of MatchResult DTOs with status and confidence

### Step 8: Implement EnrichedExcelGenerator
- Create `backend/src/core/servicios/treasury/enriched_excel_generator.py`
- Accept original Excel data and match results
- Populate columns 17 (Declaracion de Cambio Numero) and 18 (DC Nombre)
- All rows in a matched group get same declaration info
- Apply Finkargo styling (primary colors in header)
- Create summary sheet with match statistics
- Create unmatched records sheet

### Step 9: Create Treasury Matching Routes
- Create `backend/src/adapter/rest/treasury_matching_routes.py`
- Implement endpoints:
  - `POST /api/treasury/declarations/match/upload-historial` - Upload and parse Excel
  - `POST /api/treasury/declarations/match/execute` - Run matching algorithm
  - `GET /api/treasury/declarations/match/results/{session_id}` - Get cached results
  - `POST /api/treasury/declarations/match/override` - Manual match override
  - `GET /api/treasury/declarations/match/download/{session_id}` - Download enriched Excel
- Use in-memory session storage (dict with session_id keys)
- Apply RBAC with require_roles(['tesoreria'])

### Step 10: Register Router in Main App
- Modify `backend/main.py`
- Import treasury_matching_routes
- Add router: `app.include_router(treasury_matching_routes.router)`

### Step 11: Create Frontend TypeScript Types
- Create `frontend/src/types/treasuryMatching.ts`
- Define interfaces matching backend DTOs:
  - `HistorialRecord`, `PaymentGroup`, `DeclarationItem`
  - `MatchConfig`, `MatchResult`, `HistorialUploadResponse`
  - `ColumnValidationStatus`, `ValidationError`

### Step 12: Create Treasury Matching Service
- Create `frontend/src/services/treasuryMatchingService.ts`
- Implement API methods:
  - `uploadHistorial(file: File): Promise<HistorialUploadResponse>`
  - `executeMatching(config: MatchConfig): Promise<MatchResult[]>`
  - `getResults(sessionId: string): Promise<MatchResult[]>`
  - `overrideMatch(groupId: string, declarationId: string): Promise<void>`
  - `downloadEnrichedExcel(sessionId: string): Promise<Blob>`
- Use apiClient with proper auth headers

### Step 13: Create FKHistorialMatchingUploader Component
- Create `frontend/src/components/treasury/FKHistorialMatchingUploader.tsx`
- Extend pattern from FKHistorialUploader
- Display column validation status
- Show parsed data preview (first 10 rows)
- Display grouping statistics (total groups, payments per group)

### Step 14: Create FKMatchingConfigForm Component
- Create `frontend/src/components/treasury/FKMatchingConfigForm.tsx`
- Use react-hook-form with MUI components
- Date tolerance slider: 1-14 days, default 7, step 1
- Amount tolerance slider: $0.50-$5.00, default $2.00, step $0.50
- Customer match strictness: radio buttons (Exact/Fuzzy)
- Display current inventory status

### Step 15: Create FKMatchResultsTable Component
- Create `frontend/src/components/treasury/FKMatchResultsTable.tsx`
- MUI DataGrid with columns:
  - Customer Name, Payment Date, Total Capital, Declaration Number
  - Status chip (green/yellow/red for matched/partial/unmatched)
  - Confidence percentage with progress bar
  - Amount/Date differences
  - Actions (View, Override, Clear)
- Support filtering by status
- Support sorting by confidence/date/amount
- Expandable row to see grouped payment records

### Step 16: Create FKManualMatchDialog Component
- Create `frontend/src/components/treasury/FKManualMatchDialog.tsx`
- MUI Dialog modal for manual matching
- Display unmatched payment group details (customer, date, amount)
- Autocomplete dropdown of available declarations
- Filter declarations by customer name similarity
- Show match preview with confidence score
- Confirm/Cancel buttons

### Step 17: Create FKMatchStatisticsCard Component
- Create `frontend/src/components/treasury/FKMatchStatisticsCard.tsx`
- Summary grid layout (follow FKMatchingStatisticsCard pattern)
- Display: total groups, matched, partial, unmatched, conflicts
- Match rate percentage with color indicator
- Average confidence score
- Unassigned declarations count

### Step 18: Create HistorialMatchingPage
- Create `frontend/src/pages/treasury/HistorialMatchingPage.tsx`
- MUI Stepper with 4 steps:
  1. Upload Historial de Pagos (FKHistorialMatchingUploader)
  2. Configure Matching Parameters (FKMatchingConfigForm)
  3. Review Match Results (FKMatchResultsTable + FKMatchStatisticsCard)
  4. Download Output (Download button + success message)
- Manage workflow state across steps
- Show loading indicators during processing
- Handle errors with Spanish messages

### Step 19: Add Route to App.tsx
- Modify `frontend/src/App.tsx`
- Add import for HistorialMatchingPage
- Add route with role protection:
  ```tsx
  <Route
    path="treasury/declaration-matching"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.TESORERIA, UserRole.ADMIN]}>
        <HistorialMatchingPage />
      </RoleProtectedRoute>
    }
  />
  ```

### Step 20: Create E2E Test File
- Create `.claude/commands/e2e/test_declaration_historial_matching.md`
- Document test prerequisites (servers running, test file available)
- Define test steps:
  1. Navigate to treasury matching page
  2. Upload test Historial de Pagos file
  3. Configure matching parameters
  4. Verify match results display
  5. Perform manual override
  6. Download enriched Excel
- Define success criteria and screenshots

### Step 21: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Fix any issues found during validation

## Testing Strategy

### Unit Tests
- `test_historial_parser_service.py`:
  - Test column mapping with variations
  - Test date parsing with different formats
  - Test handling of missing columns
  - Test encoding handling (accented characters)

- `test_payment_group_aggregator.py`:
  - Test grouping by (customer, date)
  - Test capital sum calculation
  - Test row number tracking
  - Test customer name normalization

- `test_declaration_payment_matcher.py`:
  - Test fuzzy name matching with various similarities
  - Test date tolerance (exact, within range, outside range)
  - Test amount tolerance (exact, within range, outside range)
  - Test confidence score calculation
  - Test conflict detection (multiple declarations match)

### Edge Cases
1. **Encoding issues**: Accented characters in customer names (ñ, á, é, í, ó, ú)
2. **Date format variations**: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY
3. **Amount formats**: European (8.111,43) vs US (8,111.43)
4. **Empty rows**: Rows with null/empty capital values
5. **Duplicate declarations**: Same amount on same date for same customer
6. **No matches**: Payment groups with no matching declaration
7. **Multiple candidates**: Payment group matching multiple declarations (conflict)
8. **Customer name variations**: "DIVECO SAS" vs "Diveco" vs "DIVECO S.A.S."

## Acceptance Criteria

1. [ ] User can upload Historial de Pagos Excel and see validation results
2. [ ] System correctly identifies all 20 columns from actual file structure
3. [ ] System groups rows by (cliente, fecha_pago) and sums Capital correctly
4. [ ] User can configure date tolerance (1-14 days) via slider
5. [ ] User can configure amount tolerance ($0.50-$5.00) via slider
6. [ ] Matching finds correct declarations within configured tolerance
7. [ ] Results show match status with confidence scores (0-100%)
8. [ ] User can manually override/assign matches for unmatched groups
9. [ ] Downloaded Excel has columns 17 and 18 populated correctly
10. [ ] All rows in a matched group receive same declaration info
11. [ ] Match rate exceeds 85% on Diveco test data
12. [ ] E2E test passes demonstrating full workflow

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions:

```bash
# Backend validation
cd backend && pip install -r requirements.txt  # Install new dependencies
cd backend && python -m pytest tests/ -v  # Run backend tests
cd backend && ruff check src/  # Run backend linting

# Frontend validation
cd frontend && npm run lint  # Run frontend linting
cd frontend && npx tsc --noEmit  # Run TypeScript type check
cd frontend && npm run build  # Run frontend build

# E2E validation (manual or via test runner)
# Read .claude/commands/test_e2e.md
# Execute .claude/commands/e2e/test_declaration_historial_matching.md
```

## Notes

### New Dependencies
- **Backend**: `rapidfuzz>=3.0.0` - Fast fuzzy string matching library (alternative to fuzzywuzzy)
  - Already installed via fuzzywuzzy alternative
  - Provides `fuzz.ratio()`, `fuzz.partial_ratio()`, `process.extractOne()`

### Reuse from Existing Code
1. **FKHistorialUploader** - Reuse drag & drop, validation display patterns
2. **FKMatchingStatisticsCard** - Reuse grid layout, color coding patterns
3. **FKMatchDetailsTable** - Reuse table structure, sorting, pagination
4. **payment_template_service.py** - Reuse Excel parsing, column mapping patterns
5. **matching_results_types.ts** - Reuse type patterns for match results

### Colombian Format Considerations
1. **Dates in folders**: DD-MM-YYYY (e.g., "26-03-2025") primary, YYYYMMDD alternative
2. **Amounts**: European format "8.111,43" (periods for thousands, comma for decimal)
3. **Declaration numbers**: Simple numeric (e.g., "28756")

### Matching Algorithm Priority
1. Customer name match first (filter to candidates with similarity >= threshold)
2. Date proximity (within tolerance days)
3. Amount proximity (within tolerance USD)
4. Confidence = weighted average of all three factors

### Session-Based Storage
- Match results stored in-memory with session_id
- Sessions expire after 30 minutes of inactivity
- No database persistence (stateless workflow)

### Future Enhancements (Out of Scope)
- Integration with declaration scanner (currently reads from Excel inventory)
- Batch processing multiple Historial files
- Historical match audit trail
- Real-time progress websocket updates

## Plan Quality Checklist

Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified (N/A - no DB changes)
- [x] E2E test file task included (Step 20)
- [x] All external dependencies (npm/pip packages) listed in Notes

### Category-Specific Completeness (Excel Processing)
- [x] Source Excel columns documented with exact names (20 columns)
- [x] Output Excel structure documented (columns 17, 18 populated)
- [x] Data transformation rules specified (grouping, summing, propagation)
- [x] No catalog/lookup dependencies (matching feature, not payment conversion)

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified (in-memory dict, no database)
- [x] Country-specific handling documented (Colombia-only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy (8 cases)
- [x] E2E test covers happy path with screenshots (Step 20)
