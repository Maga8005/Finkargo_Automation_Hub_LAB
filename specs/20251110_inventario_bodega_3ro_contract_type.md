# Feature: GM - Inventario Bodega de 3ro Contract Type

## Feature Description
Implement support for a third contract type called "GM - Inventario Bodega de 3ro" (Third-Party Warehouse Inventory) in the Legal Contract Automation system. This contract type follows the same architectural patterns as the existing Activos and Otrosí contracts, providing Operations with the ability to request warehouse inventory contracts and Legal with the ability to review and approve them.

The feature adds:
- Database migration to support the new contract type
- New contract ID format: `INV-2025-001` (prefix: INV)
- Dedicated Word template for Inventario Bodega contracts
- New request form in Operations dashboard (Tab 4)
- Visual differentiation with green badges throughout the UI
- Full document generation and PDF conversion capabilities
- Integration with existing review queue and approved contracts list

## User Story
**As an Operations team member**
I want to request "Inventario Bodega de 3ro" contracts for clients who need third-party warehouse inventory agreements
So that Legal can review and approve them, enabling me to send them to clients for signature without manual document creation delays

**As a Legal team member**
I want to review Inventario Bodega contracts in my review queue alongside other contract types
So that I can ensure all contract types are processed efficiently with proper oversight and compliance

## Problem Statement
The current system supports two contract types (Activos and Otrosí), but the business requires a third contract type for third-party warehouse inventory agreements. Operations must currently request these contracts manually from Legal, creating the same bottleneck that the original automation solved for Activos contracts. This results in:

- Delays in processing warehouse inventory contracts (15 minutes per contract)
- Inconsistent Legal team workload
- No audit trail for warehouse inventory contracts
- Manual data entry errors
- Lack of visibility into contract status

## Solution Statement
Extend the existing multi-contract-type architecture to include "Inventario Bodega de 3ro" as a third contract type. This solution leverages the proven patterns established by the Otrosí implementation:

1. **Database Layer**: Update PostgreSQL schema to recognize "inventario_bodega" as a valid contract type with independent sequencing
2. **Backend Layer**: Add INVENTARIO_BODEGA enum value and update service/repository logic to handle the new type
3. **Document Layer**: Configure the existing template at `backend/templates/FK COL - GM - Inventario Bodega de 3ro.docx`
4. **Frontend Layer**: Create FKInventarioRequest component and add new tab to Operations dashboard
5. **Visual Design**: Use green badges to distinguish Inventario Bodega contracts from Activos (blue) and Otrosí (orange)

The implementation follows Clean Architecture principles and maintains backward compatibility with existing contracts.

## Relevant Files

### Backend - Database
- **`backend/database/schema.sql`** - Current database schema showing contract_id_sequence and contract_generations structure
- **`backend/database/migration_add_otrosi_support_CORRECTED.sql`** - Reference pattern for adding new contract type (will create similar migration for Inventario Bodega)

### Backend - DTOs and Models
- **`backend/src/interface/legal_dtos.py`** - Contains ContractType enum that needs INVENTARIO_BODEGA added
  - Currently: `ACTIVOS = "activos"` and `OTROSI = "otrosi"`
  - Will add: `INVENTARIO_BODEGA = "inventario_bodega"`
- **`backend/src/models/legal_models.py`** - SQLAlchemy models (no changes needed, already generic)

### Backend - Service Layer
- **`backend/src/core/servicios/contract_service.py`** - Business logic for contract generation and review
  - `generate_contract()` method already supports contract_type parameter
  - `review_contract()` method works generically for all types
- **`backend/src/core/servicios/document_service.py`** - Document generation service
  - Already handles template loading dynamically by contract_type

### Backend - Repository Layer
- **`backend/src/repositorio/contract_repository.py`** - Data access for contracts
  - `generate_contract_id()` method already supports contract_type parameter via DB function
  - `get_pending_review()` and `get_approved_contracts()` support optional contract_type filtering

### Backend - API Routes
- **`backend/src/adapter/rest/operations_routes.py`** - Operations endpoints
  - `/contracts/generate` endpoint already accepts contract_type in request body
  - `/contracts/approved` endpoint already supports contract_type query parameter
- **`backend/src/adapter/rest/legal_routes.py`** - Legal endpoints
  - `/contracts/pending-review` endpoint already supports contract_type filtering
  - All review endpoints work generically with any contract type

### Frontend - Components
- **`frontend/src/components/forms/FKOtrosiRequest.tsx`** - Template for new FKInventarioRequest component
  - Will duplicate and modify for Inventario Bodega
  - Change button text, success messages, and API call
- **`frontend/src/components/forms/FKApprovedContracts.tsx`** - Approved contracts list
  - Already has `getContractTypeBadge()` helper function
  - Will add green badge case for 'inventario_bodega'
- **`frontend/src/components/forms/FKReviewQueue.tsx`** - Legal review queue
  - Already uses `getContractTypeBadge()` for visual differentiation
  - No changes needed, will automatically display new type

### Frontend - Pages
- **`frontend/src/pages/operations/OperationsDashboard.tsx`** - Operations main dashboard
  - Currently has 3 tabs (Activos, Otrosí, Approved)
  - Will add Tab 4 for Inventario Bodega request

### Frontend - Services
- **`frontend/src/services/operationsService.ts`** - Operations API client
  - Already has `requestOtrosiGeneration()` pattern
  - Will add `requestInventarioBodegaGeneration()` method
- **`frontend/src/services/legalService.ts`** - Legal API client
  - No changes needed, already generic

### Frontend - Types
- **`frontend/src/types/legal.ts`** - TypeScript type definitions
  - `ContractGenerationRequest` interface already has contract_type field
  - May need to update if type unions are too strict

### Templates
- **`backend/templates/FK COL - GM - Inventario Bodega de 3ro.docx`** - Contract template
  - Already exists in filesystem
  - Will be registered in database via migration

### New Files

#### Backend
- **`backend/database/migration_add_inventario_bodega_support.sql`** - New migration file
  - Insert Inventario Bodega template record
  - Update generate_contract_id() function to recognize 'inventario_bodega' type
  - Initialize sequence for current year
  - Add verification queries

#### Frontend
- **`frontend/src/components/forms/FKInventarioRequest.tsx`** - New component
  - Copy of FKOtrosiRequest with modifications:
    - Change all "Otrosí" text to "Inventario Bodega de 3ro"
    - Update success message and button text
    - Call `requestInventarioBodegaGeneration()` API method
    - Use green theme colors instead of orange

#### Documentation
- **`implementations/20251110_Inventario_Bodega_Contract_Type_Implementation.md`** - Implementation report
  - Detailed documentation of all changes
  - Testing checklist
  - Deployment instructions
  - User flows

## Implementation Plan

### Phase 1: Foundation - Database and Backend Types
**Objective**: Establish database support and type definitions for the new contract type

1. Create database migration script following Otrosí pattern
2. Add INVENTARIO_BODEGA enum value to backend DTOs
3. Update PostgreSQL generate_contract_id() function to recognize new type
4. Run migration on local Supabase instance
5. Verify database changes with SELECT queries

### Phase 2: Core Implementation - Frontend Components
**Objective**: Build UI components for requesting and displaying Inventario Bodega contracts

1. Create FKInventarioRequest component (copy and modify FKOtrosiRequest)
2. Add new tab to OperationsDashboard for Inventario Bodega requests
3. Update operationsService with new API method
4. Update badge helper functions in FKApprovedContracts and FKReviewQueue
5. Test component rendering and client search functionality

### Phase 3: Integration - End-to-End Testing
**Objective**: Validate complete workflow from request to approval to download

1. Test contract request flow in Operations dashboard
2. Verify contract appears in Legal review queue with correct badge
3. Test approval workflow and PDF generation
4. Verify approved contract appears in Operations approved list
5. Test PDF download functionality
6. Validate contract ID format (INV-2025-XXX)
7. Run backend tests to ensure no regressions

## Step by Step Tasks

### Step 1: Create Database Migration
- Create `backend/database/migration_add_inventario_bodega_support.sql`
- Follow structure of `migration_add_otrosi_support_CORRECTED.sql` as template
- Insert new template record with contract_type='inventario_bodega', version='1.0.0', template_content='FK COL - GM - Inventario Bodega de 3ro.docx'
- Update generate_contract_id() function to add 'inventario_bodega' case returning 'INV' prefix
- Initialize sequence record for current year
- Add verification queries to confirm migration success
- Include success messages at end of migration

### Step 2: Run Database Migration Locally
- Connect to local Supabase instance via SQL Editor
- Execute migration script
- Verify template inserted: `SELECT * FROM contract_templates WHERE contract_type = 'inventario_bodega'`
- Test ID generation: `SELECT generate_contract_id('inventario_bodega')`
- Confirm returns format like `INV-2025-001`
- Verify sequence initialized: `SELECT * FROM contract_id_sequence WHERE contract_type = 'inventario_bodega'`

### Step 3: Update Backend DTOs
- Open `backend/src/interface/legal_dtos.py`
- Add `INVENTARIO_BODEGA = "inventario_bodega"` to ContractType enum (after OTROSI line)
- Save file
- No other backend changes needed (architecture is already generic)

### Step 4: Create FKInventarioRequest Component
- Create new file `frontend/src/components/forms/FKInventarioRequest.tsx`
- Copy contents from `frontend/src/components/forms/FKOtrosiRequest.tsx`
- Replace all occurrences of "Otrosí No. 1" with "Inventario Bodega de 3ro"
- Replace all occurrences of "Otrosí" with "Inventario Bodega"
- Change button text from "Solicitar Otrosí No. 1" to "Solicitar Inventario Bodega de 3ro"
- Update API call from `operationsService.requestOtrosiGeneration()` to `operationsService.requestInventarioBodegaGeneration()`
- Update success message to mention "Inventario Bodega de 3ro"
- Change info card background color from warning (orange) to success (green) theme
- Keep all other logic identical (search, selection, validation)

### Step 5: Add API Method to Operations Service
- Open `frontend/src/services/operationsService.ts`
- Add new method `requestInventarioBodegaGeneration()` following the pattern of `requestOtrosiGeneration()`
- Method should accept `clientNit: string` parameter
- Create ContractGenerationRequest with `contract_type: 'inventario_bodega'`
- Call POST `/operations/contracts/generate` endpoint
- Return ContractGeneration promise
- Add JSDoc comment describing the method

### Step 6: Update Badge Helper Functions
- Open `frontend/src/components/forms/FKApprovedContracts.tsx`
- Locate `getContractTypeBadge()` helper function
- Add new case for 'inventario_bodega' contract type:
  ```typescript
  if (contractType === 'inventario_bodega') {
    return {
      label: 'Inventario Bodega 3ro',
      color: 'success' as const,
    };
  }
  ```
- Place this case before the default return (after otrosi case)
- Save file
- Note: FKReviewQueue.tsx will automatically pick up this function if it uses the same helper

### Step 7: Add New Tab to Operations Dashboard
- Open `frontend/src/pages/operations/OperationsDashboard.tsx`
- Import FKInventarioRequest component at top
- Add new Tab in Tabs component (after Otrosí tab, before Approved tab):
  ```tsx
  <Tab label="Solicitar Inventario Bodega" icon={<WarehouseIcon />} iconPosition="start" />
  ```
- Add corresponding TabPanel (index 2, shifting Approved to index 3):
  ```tsx
  <TabPanel value={currentTab} index={2}>
    <Box sx={{ mb: 3 }}>
      <Card elevation={0} sx={{ bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            <WarehouseIcon sx={{ color: 'success.main', mt: 0.5 }} />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'success.dark' }}>
                Solicitud de Inventario Bodega de 3ro
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Busca el cliente y solicita la generación de un contrato de inventario para bodegas de terceros.
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
    <FKInventarioRequest />
  </TabPanel>
  ```
- Update Approved Contracts TabPanel index from 2 to 3
- Import WarehouseIcon from @mui/icons-material or use alternative like Inventory icon

### Step 8: Update TypeScript Types (if needed)
- Open `frontend/src/types/legal.ts`
- Check if ContractGenerationRequest type has strict union for contract_type
- If so, update to include 'inventario_bodega' as valid value
- Check ContractType type definition and ensure it's string or includes new type
- Most likely no changes needed if using string type

### Step 9: Local Testing - Request Contract
- Start backend server: `cd backend && python -m uvicorn main:app --reload`
- Start frontend server: `cd frontend && npm run dev`
- Navigate to Operations Dashboard
- Click "Solicitar Inventario Bodega" tab
- Search for existing test client (e.g., NIT: 900123456-1)
- Select client from results
- Click "Solicitar Inventario Bodega de 3ro" button
- Verify success message displays with contract ID like INV-2025-001
- Check browser console for no errors

### Step 10: Local Testing - Review Contract
- Navigate to Legal Dashboard
- Go to "Cola de Revisión" tab
- Verify Inventario Bodega contract appears in pending queue
- Confirm green badge displays with label "Inventario Bodega 3ro"
- Click "Aprobar" button
- Add review notes (optional)
- Submit approval
- Verify success message
- Confirm contract removed from pending queue

### Step 11: Local Testing - Download Approved Contract
- Navigate back to Operations Dashboard
- Click "Contratos Aprobados" tab
- Verify Inventario Bodega contract appears in table
- Check "Tipo" column shows green badge
- Click PDF download icon
- Verify PDF downloads successfully
- Open PDF and confirm it contains correct client data
- Verify PDF is populated from "FK COL - GM - Inventario Bodega de 3ro.docx" template

### Step 12: Create Implementation Documentation
- Create `implementations/20251110_Inventario_Bodega_Contract_Type_Implementation.md`
- Document all changes made (database, backend, frontend)
- Include testing checklist with all test cases
- Document deployment steps for production
- Add troubleshooting guide for common issues
- Include git commit history
- Add screenshots of new tab and badges (if available)

### Step 13: Run Backend Tests
- Execute backend test suite to ensure no regressions
- Run: `cd backend && pytest`
- Verify all existing tests pass
- If tests fail, investigate and fix issues
- Ensure contract generation tests cover new type

### Step 14: Validate End-to-End Workflow
- Execute complete user workflow from start to finish:
  1. Operations: Request Inventario Bodega contract
  2. Verify contract ID format (INV-2025-XXX)
  3. Legal: Review and approve contract
  4. Verify PDF generation succeeds
  5. Operations: Download approved PDF
  6. Verify PDF content matches template and client data
- Test with multiple clients to verify sequence increments correctly
- Test filtering in approved contracts list (if filter UI exists)
- Verify stats on Legal Dashboard include new contract type in counts

### Step 15: Prepare for Production Deployment
- Commit all changes with descriptive commit messages
- Push to GitHub repository
- Prepare migration script for production Supabase
- Document environment variables needed (none expected)
- Create deployment checklist
- Verify template file exists in backend/templates/ and will deploy with code

## Testing Strategy

### Unit Tests
**Backend Service Tests**:
- Test `ContractService.generate_contract()` with `contract_type='inventario_bodega'`
- Verify contract ID generation returns INV prefix
- Test template retrieval for inventario_bodega type
- Verify data snapshot includes contract_type field
- Test contract status workflow (under_review → approved)

**Backend Repository Tests**:
- Test `ContractRepository.generate_contract_id('inventario_bodega')` returns correct format
- Verify sequence increments correctly for inventario_bodega
- Test filtering pending reviews by contract_type
- Test approved contracts query with inventario_bodega filter

**Frontend Component Tests** (if test framework exists):
- Test FKInventarioRequest component renders without errors
- Test search functionality triggers API call
- Test client selection updates state correctly
- Test request button disabled when no client selected
- Test success message displays after contract creation
- Test badge helper function returns correct values for each contract type

### Integration Tests
**API Endpoint Tests**:
- POST `/operations/contracts/generate` with contract_type='inventario_bodega' returns 201
- Verify response includes contract_id with INV prefix
- GET `/operations/contracts/approved?contract_type=inventario_bodega` filters correctly
- GET `/legal/contracts/pending-review` includes inventario_bodega contracts
- POST `/legal/contracts/{id}/review` with action=approve generates PDF
- GET `/operations/contracts/{id}/download/pdf` returns valid PDF blob

**Database Integration**:
- Insert test client via API
- Generate inventario_bodega contract
- Verify record in contract_generations table has correct contract_type
- Verify contract_id matches format INV-YYYY-NNN
- Test concurrent contract generation (multiple requests) maintains sequence integrity
- Verify data_snapshot JSONB field stores correct client data

**Document Generation**:
- Test template file loads correctly from filesystem
- Verify all placeholders are replaced with client data
- Test DOCX generation completes without errors
- Test PDF conversion via LibreOffice succeeds
- Verify PDF uploaded to Supabase Storage
- Test approved_document_url is accessible and immutable

### Edge Cases
**Contract ID Sequencing**:
- Test first contract of year generates INV-2025-001
- Test 999th contract generates INV-2025-999
- Test 1000th contract behavior (verify if pagination/format handles 4 digits)
- Test concurrent requests don't create duplicate IDs (database locking)
- Test cross-year boundary (Dec 31 → Jan 1 resets sequence)

**Template Missing**:
- Test behavior when template file doesn't exist at filesystem path
- Verify error message is clear and actionable
- Test when template_content in database points to wrong filename

**Client Data Missing/Invalid**:
- Test contract generation when client has NULL cupo_plataforma
- Test with missing optional fields (direccion_comercial, kam_nombre, etc.)
- Verify contract generates successfully with empty placeholders
- Test with special characters in client name (accents, ñ, etc.)

**API Error Handling**:
- Test 404 response when client NIT not found
- Test 400 response when contract_type is invalid string
- Test 500 response handling in frontend (display error message)
- Test network timeout during contract generation
- Test large PDF download (>10MB) doesn't timeout

**UI Edge Cases**:
- Test search with empty query returns all clients
- Test search with no results displays proper message
- Test selecting client then searching again resets selection
- Test rapid clicking of "Solicitar" button (debouncing/loading state)
- Test tab switching while request is in progress
- Test browser back button doesn't break application state

**Multi-User Scenarios**:
- Test Operations user A requests contract, Legal user B approves it
- Test two Legal users viewing same pending queue simultaneously
- Test approved contract appears immediately in Operations dashboard (no caching issues)
- Test contract statistics update correctly after new type generated

## Acceptance Criteria
1. **Database Migration**: Migration script runs without errors on Supabase and creates inventario_bodega template record with active=true
2. **Contract ID Format**: Generated contracts have format INV-2025-XXX with sequential numbering independent of other contract types
3. **Operations Request Tab**: New tab "Solicitar Inventario Bodega" appears in Operations Dashboard between Otrosí and Approved tabs
4. **Request Form**: FKInventarioRequest component allows searching clients and requesting contracts with proper success/error messages
5. **API Integration**: Backend accepts contract_type='inventario_bodega' and generates contracts with correct template
6. **Legal Review Queue**: Inventario Bodega contracts appear in pending review with green badge labeled "Inventario Bodega 3ro"
7. **Approval Workflow**: Legal can approve/reject Inventario Bodega contracts, triggering PDF generation and storage
8. **Approved Contracts List**: Approved Inventario Bodega contracts appear in Operations dashboard with green badge and Tipo column
9. **PDF Download**: Operations can download approved PDFs that are correctly populated with client data from template
10. **Visual Consistency**: Green badges (success color) used consistently across all UI components for Inventario Bodega type
11. **Backward Compatibility**: Existing Activos and Otrosí contracts continue to work without any changes or regressions
12. **Statistics**: Legal Dashboard statistics cards include counts for Inventario Bodega contracts
13. **Audit Trail**: All contract_generations records have correct contract_type='inventario_bodega' for tracking
14. **No Errors**: Application runs without console errors, backend logs show no exceptions
15. **Sequence Independence**: Inventario Bodega sequence counter (001, 002, 003) is independent from Activos and Otrosí counters

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

### Backend Validation
- `cd backend && python -m pytest tests/ -v` - Run all backend tests with verbose output to ensure zero regressions
- `cd backend && python -m uvicorn main:app --reload` - Start backend server and verify no startup errors

### Database Validation
Execute these SQL queries in Supabase SQL Editor:
- `SELECT * FROM contract_templates WHERE contract_type = 'inventario_bodega'` - Verify template exists and is active
- `SELECT generate_contract_id('inventario_bodega')` - Test ID generation returns INV-2025-XXX format
- `SELECT generate_contract_id('activos')` - Verify existing types still work (returns ACT-2025-XXX)
- `SELECT generate_contract_id('otrosi')` - Verify existing types still work (returns OTRO-2025-XXX)
- `SELECT year, contract_type, last_sequence FROM contract_id_sequence ORDER BY year DESC, contract_type` - Verify all three sequences exist

### Frontend Validation
- `cd frontend && npm run dev` - Start frontend development server
- Navigate to `http://localhost:5173/department/operations` - Verify Operations Dashboard loads
- Click through all 4 tabs - Verify all tabs render without errors
- Check browser console - Should have zero errors or warnings

### End-to-End Workflow Validation
Execute this complete user flow to validate the feature:

1. **Request Inventario Bodega Contract** (Operations):
   - Navigate to Operations Dashboard → "Solicitar Inventario Bodega" tab
   - Search for client: "900123456-1"
   - Select client from results
   - Click "Solicitar Inventario Bodega de 3ro"
   - Verify success alert displays with contract ID format INV-2025-XXX
   - Copy contract ID for later steps

2. **Review Contract** (Legal):
   - Navigate to Legal Dashboard → "Cola de Revisión" tab
   - Verify Inventario Bodega contract appears in pending list
   - Verify green badge displays with "Inventario Bodega 3ro" label
   - Click "Aprobar" button
   - Enter review notes: "Approved for testing"
   - Submit approval
   - Verify success message displays
   - Verify contract disappears from pending queue

3. **Download Approved Contract** (Operations):
   - Navigate to Operations Dashboard → "Contratos Aprobados" tab
   - Verify Inventario Bodega contract appears in table
   - Verify "Tipo" column shows green badge
   - Verify contract ID matches format INV-2025-XXX
   - Click PDF download icon
   - Verify PDF downloads successfully (file size > 50KB)
   - Open PDF in viewer and verify:
     - Client name appears correctly
     - NIT appears correctly
     - All placeholders are replaced (no {{}} visible)
     - Document is properly formatted

4. **Verify Statistics** (Legal):
   - Navigate to Legal Dashboard
   - Verify "Total Generados" count increased by 1
   - Verify "Aprobados" count increased by 1
   - Verify "Hoy" count shows correct number

5. **Test All Contract Types** (Regression):
   - Request Activos contract - Verify returns ACT-YYYY-XXX
   - Request Otrosí contract - Verify returns OTRO-YYYY-XXX
   - Request Inventario Bodega contract - Verify returns INV-YYYY-XXX
   - Verify all three types appear in Legal review queue with correct badges (blue, orange, green)
   - Approve all three types
   - Verify all three appear in approved contracts list with correct badges
   - Download PDFs for all three types - Verify all succeed

### Regression Testing
- Test existing Activos contract workflow end-to-end - Should work identically to before
- Test existing Otrosí contract workflow end-to-end - Should work identically to before
- Verify CSV client import still works - Import test file with 5 clients
- Verify Legal Dashboard stats are accurate - Check counts match database records
- Test with different user roles (if RBAC implemented) - Verify permissions still work
- Check API documentation at `/api/docs` - Verify new contract type appears in enum options

## Notes

### Design Decisions
**Contract ID Prefix**: Chose "INV" (Inventario) as prefix instead of "BODEGA" or "BODE3" for:
- Brevity (3 characters like ACT, matches OTRO length)
- Clear meaning (Inventario = Inventory)
- Easy to distinguish from other prefixes
- Spanish naming convention (consistent with "Otrosí")

**Badge Color**: Selected green (success theme) for visual differentiation:
- Blue = Activos (primary contract type)
- Orange = Otrosí (amendments/modifications)
- Green = Inventario Bodega (inventory/warehouse - associated with storage/green for "good stock")
- Creates clear visual hierarchy and easy scanning

**Tab Position**: Placed new tab third (after Activos and Otrosí, before Approved Contracts) because:
- Groups all request forms together before the results list
- Maintains logical flow: Activos → Otrosí → Inventario → Results
- Keeps "Contratos Aprobados" as final tab (destination for all workflows)

### Future Enhancements
**Phase 2 Considerations**:
- Add contract type filter tabs in Legal review queue (separate Activos/Otrosí/Inventario)
- Implement separate stats cards per contract type on Legal Dashboard
- Add bulk request capability for Inventario Bodega (CSV upload of multiple warehouses)
- Create warehouse-specific fields in client data model (warehouse_address, warehouse_capacity)
- Link Inventario contracts to parent Activos contract (FK relationship)

**Template Evolution**:
- Version control for Inventario Bodega template (v1.0.0 → v1.1.0)
- Admin UI for uploading new template versions
- Template comparison view (show what changed between versions)
- Placeholder validation (warn if required fields missing in template)

**Analytics**:
- Track time-to-approval by contract type
- Compare volume trends (Activos vs Otrosí vs Inventario)
- Identify bottlenecks (which type takes longest to approve)
- Client analysis (which clients use multiple contract types)

### Technical Debt Avoided
**Why Not Add 4th Contract Type Right Away?**
While the architecture supports unlimited contract types, we're implementing one at a time to:
- Validate pattern works consistently across multiple types
- Test scalability of UI (tab overflow behavior)
- Gather user feedback on whether more types are needed
- Avoid premature optimization (YAGNI principle)

**Why Not Create Abstracted "RequestContractForm" Component?**
FKInventarioRequest is copied from FKOtrosiRequest because:
- Each form may evolve differently (warehouse-specific fields later)
- Copy-paste-modify is faster than premature abstraction
- Clear separation makes debugging easier
- If 5+ contract types emerge, we'll refactor to shared component then

**Why Modify generate_contract_id() Instead of Generic Mapping Table?**
Using PostgreSQL function with if/else logic instead of mapping table because:
- Simpler for small number of contract types (3-5 types)
- Function is faster than JOIN for every contract generation
- Easier to version control (function in migration files)
- If types grow beyond 10, we'll migrate to mapping table approach

### Dependencies
**No New Libraries Required**:
- All dependencies already installed (python-docx, LibreOffice, MUI, React, etc.)
- No npm install or pip install needed
- Template file already exists in backend/templates/

**Production Deployment Requirements**:
- Supabase access to run migration script
- Render.com deployment will auto-deploy from GitHub push
- Vercel deployment will auto-deploy from GitHub push
- Verify LibreOffice is installed on Render.com backend (already confirmed from Otrosí implementation)
- Ensure backend/templates/ directory deploys with application code

### Reference Implementation
**Otrosí Contract Type** serves as the exact template for this implementation:
- Database migration: `backend/database/migration_add_otrosi_support_CORRECTED.sql`
- Frontend component: `frontend/src/components/forms/FKOtrosiRequest.tsx`
- Badge implementation: `getContractTypeBadge()` function in FKApprovedContracts.tsx
- Service method: `requestOtrosiGeneration()` in operationsService.ts
- Documentation: `implementations/20251106_Otrosi_Contract_Type_Implementation.md`

Follow these files line-by-line, replacing "otrosi" with "inventario_bodega" and "Otrosí No. 1" with "Inventario Bodega de 3ro". The architecture is proven and battle-tested.

### Success Metrics
**Key Performance Indicators (Post-Deployment)**:
- Time to generate Inventario Bodega contract: < 1 minute (vs 15 minutes manual)
- Legal review time: < 3 minutes per contract
- Zero errors in production for first 100 contracts
- User satisfaction: Operations and Legal teams report no issues
- Adoption rate: 10+ Inventario Bodega contracts requested in first week
- Sequence integrity: No duplicate contract IDs generated

**Measurement Plan**:
- Week 1: Monitor error logs daily
- Week 2: Collect user feedback via Slack/email
- Week 3: Analyze contract generation statistics
- Week 4: Document lessons learned for next contract type
