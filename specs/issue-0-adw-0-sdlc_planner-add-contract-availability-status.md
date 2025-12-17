# Feature: Add Contract Availability Status Column

## Feature Description
Add a new "Contract Status" (Estado del Contrato) column to the broker incentive extraction results that indicates whether a contract PDF was found and processed, or if the broker folder had no contract available. This helps users quickly identify which brokers have contracts on file versus those that don't.

The status will be determined by:
- **"Contrato Encontrado"** (Contract Found): When a valid contract PDF was found and successfully processed
- **"Sin Contrato"** (No Contract): When the broker folder exists but contains no valid contract PDF (even if other PDFs exist)
- **"Error de Extracción"** (Extraction Error): When a contract PDF exists but extraction failed with errors

### Contract PDF Identification
A PDF is considered a valid contract if its filename contains ANY of these patterns (case-insensitive):
- `Complete_con_Docusign` or `Completado_con_Docusign` (DocuSign completed contracts)
- `contrato` (contract)
- `corretaje` or `correta` (brokerage)
- `bono` (bonus)
- `incentivo` (incentive)
- `convenio` (agreement)
- `acuerdo` (agreement)

**Important**: Folders with PDFs that do NOT match any of these patterns will be marked as "Sin Contrato" - the presence of PDFs alone is not sufficient.

This status will appear in:
1. The Excel output file as a new column
2. The "Resultados de Extracción" screen in the frontend UI

## User Story
As an **Alianzas team member**
I want to see a clear indication of whether each broker has a contract available
So that I can quickly identify which brokers are missing contracts and need follow-up

## Problem Statement
Currently, when scanning broker directories:
1. Folders without PDF files are silently skipped
2. Folders with PDFs that are NOT contracts (e.g., invoices, reports) are processed anyway, leading to extraction failures
3. Users cannot easily distinguish between brokers with valid contracts vs those missing contracts

Many broker folders contain multiple PDFs, but not all are Finkargo incentive contracts. Valid contract files typically have identifying keywords in their filename (e.g., "Complete_con_Docusign", "contrato", "bono", "incentivo").

## Solution Statement
Add a `contract_status` field to the broker incentive extraction flow that:
1. Uses filename pattern matching to identify valid contract PDFs
2. Marks folders as "Sin Contrato" if no PDF matches contract patterns (even if other PDFs exist)
3. Only processes PDFs that look like contracts based on filename
4. Displays contract availability status in both Excel and UI

**Contract Filename Patterns (case-insensitive):**
- `complete_con_docusign`, `completado_con_docusign` (DocuSign)
- `contrato`, `contract`
- `corretaje`, `correta`
- `bono`
- `incentivo`
- `convenio`, `acuerdo`

This status will be displayed as a new column in both the Excel output and the frontend results grid, allowing users to filter and sort by contract availability.

## Access Control
- Required Role(s): `alianzas`, `admin`
- Backend Protection: Existing authentication from alianzas_routes.py
- Frontend Protection: Existing route protection for /alianzas pages

## Relevant Files
Use these files to implement the feature:

**Backend - DTOs:**
- `backend/src/interface/broker_incentive_dtos.py` - Add new `ContractStatus` enum and `contract_status` field to `BrokerIncentiveData`

**Backend - Services:**
- `backend/src/core/servicios/broker_contract_scanner.py` - Modify to track folders with no PDFs
- `backend/src/core/servicios/broker_incentive_extractor.py` - Add contract status determination logic
- `backend/src/core/servicios/broker_incentive_excel_generator.py` - Add contract status column to Excel output

**Frontend - Services:**
- `frontend/src/services/brokerIncentiveService.ts` - Add `ContractStatus` type and update `BrokerIncentiveData` interface

**Frontend - Components:**
- `frontend/src/components/alianzas/FKBrokerIncentiveResultsGrid.tsx` - Add contract status column with color-coded chips

**Tests:**
- `backend/tests/test_broker_incentive_extraction.py` - Add tests for new contract status functionality
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E testing patterns

### New Files
- `.claude/commands/e2e/test_broker_contract_status.md` - E2E test for contract status feature

## Pre-Implementation Verification

### Feature Category
- [x] CRUD Operations (basic data management) → Complete sections D, E

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| BrokerIncentiveData | Pydantic Model | data.contract_status | Uses dot notation |
| BrokerFolder | dataclass | folder.pdf_files | Uses dot notation |

### E. Database Dependencies Checklist
- [x] Required enums exist in DTOs (ContractStatus will be added)
- [ ] Template file exists in `backend/templates/` (N/A - no template)
- [ ] Database records exist (N/A - no database records needed)
- [ ] Country-specific data handled (N/A - not country-specific)

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| contract_status | contract_status | ContractStatus | Enum: 'found' / 'not_found' / 'error' |

## Implementation Plan

### Phase 1: Foundation
- Add `ContractStatus` enum to backend DTOs
- Add `contract_status` field to `BrokerIncentiveData` DTO
- Update frontend TypeScript types

### Phase 2: Core Implementation
- Modify scanner to track folders with no PDFs
- Update extractor to set contract status based on extraction outcome
- Update Excel generator to include new column with styling
- Update frontend grid to display contract status with color-coded chips

### Phase 3: Integration
- Update summary statistics to include contract status counts
- Add filtering capability by contract status
- Create E2E test file

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add ContractStatus Enum to Backend DTOs

- Edit `backend/src/interface/broker_incentive_dtos.py`
- Add new enum `ContractStatus` with values:
  - `FOUND = "found"` - Contract PDF was found and processed
  - `NOT_FOUND = "not_found"` - Folder exists but no PDF found
  - `ERROR = "error"` - PDF exists but extraction had critical errors
- Add `contract_status` field to `BrokerIncentiveData`:
  - Type: `ContractStatus`
  - Default: `ContractStatus.FOUND`
  - Description: "Status indicating whether contract was found and processed"

### Step 2: Add Contract Filename Pattern Matching to BrokerContractScanner

- Edit `backend/src/core/servicios/broker_contract_scanner.py`
- Add new class constant `CONTRACT_FILENAME_PATTERNS` with regex patterns (case-insensitive):
  ```python
  CONTRACT_FILENAME_PATTERNS = [
      r'complete.*con.*docusign',      # DocuSign completed
      r'completado.*con.*docusign',    # DocuSign completed (Spanish)
      r'contrato',                      # Contract
      r'contract',                      # Contract (English)
      r'corretaje',                     # Brokerage
      r'correta',                       # Brokerage (partial)
      r'bono',                          # Bonus
      r'incentivo',                     # Incentive
      r'convenio',                      # Agreement
      r'acuerdo',                       # Agreement
  ]
  ```
- Add new method `is_contract_pdf(self, filename: str) -> bool`:
  - Check if filename (lowercase) matches any CONTRACT_FILENAME_PATTERNS
  - Return True if any pattern matches, False otherwise
- Modify `find_contract_pdf` method:
  - First, filter PDFs to only those matching contract patterns using `is_contract_pdf`
  - If no PDFs match contract patterns, return None (even if folder has other PDFs)
  - If multiple contract PDFs exist, return the first one
- Modify `_scan_broker_folders` method:
  - Include ALL folders (even those without PDFs or without contract PDFs)
  - Mark folders with empty `pdf_files` if no PDFs exist
  - Log message when folder has PDFs but none match contract patterns
- Add new method `has_contract_pdf(self, folder: BrokerFolder) -> bool`:
  - Returns True if any PDF in folder matches contract filename patterns
  - Returns False otherwise (even if folder has non-contract PDFs)

### Step 3: Update BrokerIncentiveExtractor to Set Contract Status

- Edit `backend/src/core/servicios/broker_incentive_extractor.py`
- Import `ContractStatus` from DTOs
- Update `extract_from_folder` method:
  - Use scanner's `find_contract_pdf` method (which now filters by filename patterns)
  - If `find_contract_pdf` returns None:
    - Check if folder has any PDFs at all
    - If folder has PDFs but none are contracts: Set warning "Folder contains PDFs but no contract file found"
    - Set `contract_status = ContractStatus.NOT_FOUND`
  - If contract PDF found and extraction successful: Set `contract_status = ContractStatus.FOUND`
  - If contract PDF found but extraction confidence is 0: Set `contract_status = ContractStatus.ERROR`
- Update `extract_from_pdf` method:
  - Add `contract_status` to returned `BrokerIncentiveData`
  - On success: `ContractStatus.FOUND`
  - On exception: `ContractStatus.ERROR`

### Step 4: Update Excel Generator with Contract Status Column

- Edit `backend/src/core/servicios/broker_incentive_excel_generator.py`
- Add 'contract_status' to `COLUMN_MAPPING`:
  - Key: `'contract_status'`
  - Value: `'Estado Contrato'`
- Update `_create_dataframe` method:
  - Add new column "Estado Contrato" with formatted status values
  - Use display values: "Encontrado", "Sin Contrato", "Error"
- Update `_format_contract_status` method (new):
  - FOUND → "Encontrado"
  - NOT_FOUND → "Sin Contrato"
  - ERROR → "Error"
- Update `_calculate_statistics` method:
  - Add `contracts_found`, `contracts_not_found`, `contracts_error` counts
- Update `_create_summary_sheet` method:
  - Add "Estado de Contratos" section with counts
- Update `_style_data_sheet` method:
  - Add conditional formatting for contract status column:
    - "Encontrado" → Green background (SUCCESS_BG_COLOR)
    - "Sin Contrato" → Orange/warning background (WARNING_BG_COLOR)
    - "Error" → Red background (ERROR_BG_COLOR)
- Update `column_widths` list to include new column

### Step 5: Update Frontend TypeScript Types

- Edit `frontend/src/services/brokerIncentiveService.ts`
- Add `ContractStatus` type: `'found' | 'not_found' | 'error'`
- Update `BrokerIncentiveData` interface:
  - Add field: `contract_status: ContractStatus`
- Add `formatContractStatus` function:
  - 'found' → 'Encontrado'
  - 'not_found' → 'Sin Contrato'
  - 'error' → 'Error'
- Add `getContractStatusColor` function:
  - 'found' → 'success'
  - 'not_found' → 'warning'
  - 'error' → 'error'

### Step 6: Update Frontend Results Grid

- Edit `frontend/src/components/alianzas/FKBrokerIncentiveResultsGrid.tsx`
- Import `formatContractStatus` and `getContractStatusColor` from service
- Add new column definition for `contract_status`:
  - Field: `'contract_status'`
  - Header: `'Estado Contrato'`
  - Width: 140
  - Use Chip component with color based on status
- Add `renderContractStatusCell` function:
  - Returns a `<Chip>` with appropriate label and color
- Update summary statistics section:
  - Add counts for "Encontrados", "Sin Contrato", "Errores"

### Step 7: Add Backend Unit Tests

- Edit `backend/tests/test_broker_incentive_extraction.py`

**Contract Filename Pattern Tests:**
- Add test `test_is_contract_pdf_docusign`:
  - Assert `is_contract_pdf("Complete_con_Docusign_contract.pdf")` returns True
  - Assert `is_contract_pdf("Completado_con_Docusign.pdf")` returns True
- Add test `test_is_contract_pdf_contrato`:
  - Assert `is_contract_pdf("contrato_broker.pdf")` returns True
  - Assert `is_contract_pdf("CONTRATO_INCENTIVOS.pdf")` returns True
- Add test `test_is_contract_pdf_bono`:
  - Assert `is_contract_pdf("Bono_alianza.pdf")` returns True
- Add test `test_is_contract_pdf_corretaje`:
  - Assert `is_contract_pdf("corretaje_comercial.pdf")` returns True
  - Assert `is_contract_pdf("correta_docs.pdf")` returns True
- Add test `test_is_contract_pdf_non_contract`:
  - Assert `is_contract_pdf("factura_enero_2024.pdf")` returns False
  - Assert `is_contract_pdf("reporte_ventas.pdf")` returns False
  - Assert `is_contract_pdf("random_document.pdf")` returns False

**Contract Status Tests:**
- Add test `test_contract_status_found`:
  - Mock extraction with valid PDF text
  - Assert `contract_status == ContractStatus.FOUND`
- Add test `test_contract_status_not_found_no_pdfs`:
  - Mock folder with no PDF files
  - Assert `contract_status == ContractStatus.NOT_FOUND`
- Add test `test_contract_status_not_found_non_contract_pdfs`:
  - Mock folder with PDFs that don't match contract patterns
  - Assert `contract_status == ContractStatus.NOT_FOUND`
  - Assert warning contains "no contract file found"
- Add test `test_contract_status_error`:
  - Mock extraction that raises exception
  - Assert `contract_status == ContractStatus.ERROR`
- Add test `test_format_contract_status`:
  - Test Excel generator formatting function
- Add test `test_statistics_includes_contract_status`:
  - Verify statistics include contract status counts

### Step 8: Create E2E Test File

- Create `.claude/commands/e2e/test_broker_contract_status.md`
- Include steps to:
  1. Navigate to Alianzas → Extracción de Incentivos page
  2. Enter a directory path with mixed brokers (some with contracts, some without)
  3. Click "Escanear Directorio"
  4. Verify results grid shows "Estado Contrato" column
  5. Verify correct status chips appear (green for found, orange for not found)
  6. Take screenshot of results showing different statuses
  7. Click "Exportar Excel"
  8. Verify Excel file contains "Estado Contrato" column

### Step 9: Run Validation Commands

- Run all validation commands to ensure zero regressions
- Fix any linting or type errors that arise
- Ensure all tests pass

## Testing Strategy

### Unit Tests
- Test `ContractStatus` enum values are correct
- Test `is_contract_pdf` method with various filename patterns
- Test `find_contract_pdf` returns None when no contract PDFs exist
- Test `extract_from_folder` returns correct status for folders with/without contract PDFs
- Test `extract_from_pdf` returns correct status on success/error
- Test Excel generator formats status values correctly
- Test Excel generator applies correct styling to status column
- Test statistics calculation includes status counts

### Edge Cases
- Folder with empty PDF files (0 bytes) - should be ERROR if contract PDF
- Folder with non-PDF files only - should be NOT_FOUND
- Folder with multiple PDFs but NONE match contract patterns - should be NOT_FOUND
- Folder with multiple PDFs, only ONE matches contract pattern - should process only that one
- Multiple contract PDFs in folder - should use first matching one
- PDF with unreadable/scanned content - should be FOUND (but with warnings)
- Case variations in filename: "CONTRATO.pdf", "Contrato.PDF", "contrato.pdf" - all should match
- Partial matches: "correta" should match, "cor" should not
- DocuSign variations: "Complete_con_Docusign", "Completado_Con_DocuSign" - both should match

## Acceptance Criteria
1. New `contract_status` field appears in API response for each broker record
2. Excel output contains "Estado Contrato" column with values "Encontrado", "Sin Contrato", or "Error"
3. Excel column has conditional formatting (green/orange/red backgrounds)
4. Frontend results grid displays contract status with color-coded chips
5. Summary statistics include contract status counts
6. Folders without PDFs are now included in results (previously skipped)
7. Folders with PDFs that don't match contract filename patterns are marked as "Sin Contrato"
8. Contract filename patterns are case-insensitive (CONTRATO, Contrato, contrato all match)
9. All existing tests continue to pass

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest tests/test_broker_incentive_extraction.py -v` - Run broker incentive tests specifically
- `cd backend && python -m pytest` - Run all backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_broker_contract_status.md` to validate this functionality works

## Notes

1. **Backwards Compatibility**: The `contract_status` field defaults to `FOUND` for existing records, ensuring backwards compatibility with any stored data.

2. **Folder Inclusion Change**: Currently, folders without PDFs are silently skipped. After this change, they will be included in results with `NOT_FOUND` status. This is a deliberate behavior change that provides more visibility.

3. **Column Order**: The new "Estado Contrato" column should appear after "Tipo Contrato" in both Excel and UI grid for logical grouping of contract metadata.

4. **Color Coding Consistency**:
   - Green (success) = Contract found and processed
   - Orange (warning) = No contract available in folder
   - Red (error) = Contract exists but extraction failed

5. **Statistics Impact**: The summary statistics will now include:
   - Total Contratos Encontrados
   - Total Sin Contrato
   - Total con Error

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A)
- [x] E2E test file task included (Step 8)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**CRUD Operations:**
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns (dict vs object) verified for repository methods

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for repository methods
- [x] Country-specific variations handled (N/A)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots
