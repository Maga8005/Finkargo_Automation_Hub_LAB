# Feature: Add Sorting to Contratos Aprobados Table

## Feature Description
Add comprehensive column sorting functionality to the "Contratos Aprobados" (Approved Contracts) table in the Operations department menu. Users will be able to click on column headers to sort the table in ascending or descending order, with descending order as the default for all sortable columns. This enhancement will improve the user experience by allowing Operations team members to efficiently organize and locate approved contracts based on different criteria such as contract ID, client name, approval date, and approved credit limit.

## User Story
As an Operations team member
I want to sort the approved contracts table by clicking on column headers
So that I can quickly find and download specific approved contracts based on various criteria (date, client name, amount, etc.)

## Problem Statement
Currently, the "Contratos Aprobados" table in the Operations dashboard displays approved contracts in a fixed order (by reviewed_at DESC from the backend). Users cannot reorganize the data based on their needs, making it difficult to:
- Find the latest approved contracts by approval date
- Locate contracts by client name alphabetically
- Sort by approved credit limit to prioritize high-value contracts
- Filter by contract type or contract ID

This limitation reduces productivity and forces users to manually scan through the list to find specific contracts.

## Solution Statement
Implement client-side table sorting using Material-UI's `TableSortLabel` component with backend support for query parameters. The solution will:

1. **Frontend (Client-side sorting)**: Add clickable sort indicators to table headers using `TableSortLabel`
2. **State Management**: Track current sort column and direction (asc/desc) using React hooks
3. **Backend Enhancement**: Extend the `/api/operations/contracts/approved` endpoint to accept `sort_by` and `sort_order` query parameters
4. **Repository Layer**: Update `contract_repository.py` to support dynamic sorting with Supabase queries
5. **Default Behavior**: Set descending order as default for all sortable columns
6. **Visual Feedback**: Display up/down arrow indicators to show current sort state

Sortable columns:
- **ID Contrato** (contract_id) - String sort
- **Tipo** (contract_type) - Enum sort
- **Cliente** (data_snapshot->nombre_importador) - String sort via JSONB
- **NIT** (client_nit) - String sort
- **Cupo Aprobado** (data_snapshot->cupo_plataforma) - Numeric sort via JSONB
- **Fecha Aprobación** (reviewed_at) - Date sort (DEFAULT)

## Relevant Files

### Frontend Files (Existing)
- **`frontend/src/components/forms/FKApprovedContracts.tsx`** (Lines 1-261)
  - Main component displaying the approved contracts table
  - Uses basic Material-UI Table components (Table, TableHead, TableBody, TableCell)
  - Currently has no sorting functionality - needs to add `TableSortLabel` to headers
  - Fetches data via `operationsService.getApprovedContracts()` with no sort parameters
  - **Changes needed**: Add sort state, implement column header click handlers, pass sort params to service

- **`frontend/src/services/operationsService.ts`** (Lines 39-46)
  - Contains `getApprovedContracts(contractType?: string)` method
  - Currently only accepts optional `contract_type` filter
  - **Changes needed**: Extend method signature to accept `sort_by` and `sort_order` parameters

- **`frontend/src/types/legal.ts`** (Lines 52-72)
  - Defines `ContractGeneration` interface with all sortable fields
  - Contains `ClientDataSnapshot` interface (lines 74-92) with nested sortable fields
  - **Changes needed**: Add new interface for sort parameters (OperationsSortParams)

### Backend Files (Existing)
- **`backend/src/adapter/rest/operations_routes.py`** (Lines 162-180)
  - Defines `GET /api/operations/contracts/approved` endpoint
  - Currently accepts only optional `contract_type` query parameter
  - Calls `contract_repo.get_approved_contracts(contract_type)`
  - **Changes needed**: Add `sort_by` and `sort_order` query parameters, pass to repository

- **`backend/src/repositorio/contract_repository.py`** (Lines 172-192)
  - Contains `get_approved_contracts(contract_type)` method
  - Currently hardcoded to sort by `reviewed_at` DESC (line 190)
  - Uses Supabase query builder
  - **Changes needed**: Add dynamic sorting based on parameters, handle JSONB field sorting

### Reference Files (For Pattern Guidance)
- **`frontend/src/components/declaraciones/FKMatchDetailsTable.tsx`**
  - Example of DataGrid with built-in sorting (more advanced pattern)
  - Shows how to handle sort state and pagination together

- **`frontend/src/types/matching_results_types.ts`**
  - Defines `MatchingResultsPagination` interface with sort parameters
  - Good reference for TypeScript sort parameter types

- **`frontend/src/services/matchingResultsService.ts`**
  - Shows how to pass sort parameters via query params
  - Reference for service layer implementation pattern

### New Files
None - all changes are modifications to existing files.

## Implementation Plan

### Phase 1: Foundation (Type Definitions & Backend Support)
Establish the data contracts and backend infrastructure to support sorting before making any UI changes.

1. **Define TypeScript interfaces** for sort parameters in `frontend/src/types/legal.ts`
2. **Extend backend repository** to accept and handle dynamic sort parameters
3. **Update API endpoint** to accept sort query parameters
4. **Add validation** for allowed sort fields (prevent SQL injection via invalid fields)

### Phase 2: Core Implementation (Frontend Sorting UI)
Implement the interactive sorting UI components and state management.

1. **Add sort state management** to `FKApprovedContracts.tsx` using React hooks
2. **Replace TableCell headers** with `TableSortLabel` components
3. **Implement column header click handlers** to toggle sort direction
4. **Update service call** to pass sort parameters to backend
5. **Add visual indicators** (arrows) for current sort state

### Phase 3: Integration (Testing & Polish)
Ensure the feature works correctly across all scenarios and integrates seamlessly with existing functionality.

1. **Test all sortable columns** with both ascending and descending order
2. **Verify default behavior** (descending order on first click)
3. **Test with empty states** and error scenarios
4. **Ensure no regressions** in existing download and refresh functionality
5. **Validate JSONB field sorting** for nested fields (cliente, cupo_aprobado)

## Step by Step Tasks

### Step 1: Define TypeScript Types for Sorting
- Add `OperationsSortField` type to `frontend/src/types/legal.ts` with allowed sort fields:
  - `'contract_id'`, `'contract_type'`, `'client_nit'`, `'reviewed_at'`, `'nombre_importador'`, `'cupo_plataforma'`
- Add `OperationsSortOrder` type: `'asc' | 'desc'`
- Add `OperationsSortParams` interface with optional `sort_by` and `sort_order` fields
- Export types for use in components and services

### Step 2: Update Backend Repository for Dynamic Sorting
- Modify `contract_repository.py` `get_approved_contracts()` method signature to accept `sort_by` and `sort_order` parameters
- Add allowed sort fields validation (whitelist: `contract_id`, `contract_type`, `client_nit`, `reviewed_at`)
- Implement conditional sorting logic using Supabase query builder's `.order()` method
- Handle JSONB field sorting for `nombre_importador` and `cupo_plataforma` using PostgREST syntax:
  - `data_snapshot->nombre_importador`
  - `data_snapshot->cupo_plataforma`
- Default to `reviewed_at DESC` if no sort parameters provided
- Add error handling for invalid sort fields

### Step 3: Update Backend API Endpoint
- Modify `operations_routes.py` `get_approved_contracts()` endpoint to accept query parameters:
  - `sort_by: Optional[str] = None`
  - `sort_order: Optional[str] = None`
- Validate `sort_order` is either `'asc'` or `'desc'` (default to `'desc'`)
- Pass parameters to `contract_repo.get_approved_contracts(contract_type, sort_by, sort_order)`
- Update endpoint docstring to document new query parameters
- Add logging for sort parameters (debugging)

### Step 4: Update Frontend Service Layer
- Modify `operationsService.ts` `getApprovedContracts()` method signature:
  - Add optional parameters: `sortBy?: string, sortOrder?: string`
- Build query params object conditionally including sort parameters
- Pass params to `apiClient.get()` call
- Update JSDoc comments to document new parameters

### Step 5: Add Sort State Management to Component
- In `FKApprovedContracts.tsx`, add state hooks:
  - `const [sortBy, setSortBy] = useState<string>('reviewed_at')` (default sort field)
  - `const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')` (default descending)
- Create `handleSortRequest(column: string)` function:
  - If clicking current sort column, toggle `sortOrder` between 'asc' and 'desc'
  - If clicking new column, set `sortBy` to new column and `sortOrder` to 'desc'
  - Call `loadApprovedContracts()` to refetch with new sort
- Add `sortBy` and `sortOrder` to dependency array of any useEffect that should trigger refetch

### Step 6: Update Data Fetching to Include Sort Parameters
- Modify `loadApprovedContracts()` function in `FKApprovedContracts.tsx`
- Pass `sortBy` and `sortOrder` to `operationsService.getApprovedContracts(undefined, sortBy, sortOrder)`
- Ensure error handling still works correctly
- Consider adding loading state management to prevent duplicate requests

### Step 7: Replace Table Headers with TableSortLabel
- Import `TableSortLabel` from `@mui/material`
- Replace each sortable `<TableCell>` header with `<TableCell>` containing `<TableSortLabel>`
- Configure `TableSortLabel` props:
  - `active={sortBy === 'column_name'}` - highlight active sort column
  - `direction={sortBy === 'column_name' ? sortOrder : 'desc'}` - show arrow direction
  - `onClick={() => handleSortRequest('column_name')}` - handle clicks
- Apply to columns: `contract_id`, `contract_type`, `nombre_importador`, `client_nit`, `cupo_plataforma`, `reviewed_at`
- Leave "Estado" and "Acciones" columns as non-sortable (no TableSortLabel)

### Step 8: Map Frontend Sort Fields to Backend Database Fields
- Create a mapping object in `FKApprovedContracts.tsx`:
  ```typescript
  const SORT_FIELD_MAP: Record<string, string> = {
    'contract_id': 'contract_id',
    'contract_type': 'contract_type',
    'nombre_importador': 'data_snapshot->nombre_importador',
    'client_nit': 'client_nit',
    'cupo_plataforma': 'data_snapshot->cupo_plataforma',
    'reviewed_at': 'reviewed_at'
  };
  ```
- Update `handleSortRequest()` to use mapped field names when calling backend
- Update `loadApprovedContracts()` to pass mapped field name to service

### Step 9: Add Visual Styling for Sort Indicators
- Apply consistent styling to `TableSortLabel` components to match Finkargo design system
- Ensure active sort column is visually distinct (use theme primary color)
- Add hover effects for better UX (cursor pointer, slight color change)
- Test with different theme modes if applicable

### Step 10: Test Individual Column Sorting
- Manually test each sortable column:
  - **ID Contrato**: Verify alphanumeric sort (ACT-2025-001, ACT-2025-002, etc.)
  - **Tipo**: Verify enum sort (activos, inventario_bodega, otrosi)
  - **Cliente**: Verify alphabetical sort of company names
  - **NIT**: Verify numeric/string sort of tax IDs
  - **Cupo Aprobado**: Verify numeric sort of currency amounts
  - **Fecha Aprobación**: Verify chronological date sort
- Test both ascending and descending for each column
- Verify default descending behavior on first click

### Step 11: Test Sort Direction Toggle
- Click a column header once → verify descending order (↓)
- Click the same column header again → verify ascending order (↑)
- Click a different column → verify it becomes active with descending order
- Verify previous column becomes inactive (no arrow or inactive arrow)

### Step 12: Test Edge Cases
- Test with empty table (no approved contracts) - should show empty state without errors
- Test with single row - sorting should work without errors
- Test with duplicate values in sort column - verify secondary sort behavior
- Test rapid clicking on headers - verify no race conditions or state conflicts
- Test after using "Actualizar" (refresh) button - verify sort persists or resets appropriately

### Step 13: Test Backend Sort Parameter Validation
- Use browser DevTools Network tab to verify correct query params sent
- Test invalid sort field names - backend should fallback to default or return error
- Test invalid sort order values - backend should default to 'desc'
- Test JSONB field sorting (nombre_importador, cupo_plataforma) - verify correct SQL generated

### Step 14: Test Integration with Existing Features
- Verify PDF download functionality still works correctly
- Verify "Actualizar" button refreshes with current sort applied
- Verify contract type badge display still works
- Verify currency formatting still works after sorting
- Verify date formatting still works after sorting
- Verify authentication/authorization still enforced

### Step 15: Add Unit Tests for Sort Logic (Frontend)
- Create test file: `frontend/src/components/forms/__tests__/FKApprovedContracts.test.tsx`
- Test `handleSortRequest()` function:
  - Test toggling sort direction on same column
  - Test switching to different column resets to descending
  - Test state updates correctly
- Test `loadApprovedContracts()` passes correct parameters to service
- Mock `operationsService.getApprovedContracts()` to verify call arguments

### Step 16: Add Unit Tests for Sort Logic (Backend)
- Create test file: `backend/tests/test_contract_repository_sorting.py`
- Test `get_approved_contracts()` with different sort parameters:
  - Test each valid sort field
  - Test ascending and descending order
  - Test default behavior (no params → reviewed_at DESC)
  - Test invalid sort fields are rejected/default applied
  - Test JSONB field sorting generates correct PostgREST query

### Step 17: Add Integration Tests
- Create test file: `backend/tests/test_operations_routes_sorting.py`
- Test full API endpoint with sort parameters:
  - Test `GET /api/operations/contracts/approved?sort_by=contract_id&sort_order=asc`
  - Test `GET /api/operations/contracts/approved?sort_by=reviewed_at&sort_order=desc`
  - Test with authentication token
  - Test with invalid sort parameters return appropriate response
  - Test response data is correctly sorted

### Step 18: Run All Validation Commands
- Execute all validation commands listed in "Validation Commands" section
- Verify zero errors, zero warnings, zero regressions
- Manually test in browser with real data
- Test with different user roles (operations, admin)
- Verify feature works in both development and production builds

## Testing Strategy

### Unit Tests
**Frontend Component Tests:**
- Test `handleSortRequest()` function logic:
  - Same column click toggles direction
  - Different column click sets to descending
- Test sort state management:
  - `sortBy` and `sortOrder` state updates correctly
  - Component re-renders with new sort params
- Mock `operationsService` calls:
  - Verify correct parameters passed to service
  - Verify loading/error states handled

**Frontend Service Tests:**
- Test `getApprovedContracts()` builds correct query params
- Test parameters are properly encoded in URL
- Mock axios client to verify request structure

**Backend Repository Tests:**
- Test `get_approved_contracts()` with various sort parameters
- Test sort field validation (allowed vs. disallowed fields)
- Test JSONB field sorting syntax is correct
- Test default sort behavior when no params provided
- Mock Supabase client to verify query construction

**Backend Route Tests:**
- Test endpoint accepts and validates query parameters
- Test parameter type conversion (string to enum)
- Test error handling for invalid parameters
- Mock repository to verify correct params passed down

### Integration Tests
**Frontend-Backend Integration:**
- Test complete flow from button click to rendered sorted data
- Test with real backend API (integration test environment)
- Verify authentication headers passed correctly
- Test error scenarios (network failure, 401, 500)

**Database Query Tests:**
- Test actual Supabase queries with real database
- Verify JSONB field sorting works with PostgreSQL
- Test query performance with large datasets (100+ contracts)
- Verify indexes are used correctly (check query plan)

**End-to-End Tests:**
- Test in browser with full application running
- Test user workflow: Login → Navigate to Operations → Click sort headers
- Test across different browsers (Chrome, Firefox, Safari)
- Test responsive behavior (mobile, tablet, desktop)

### Edge Cases
1. **Empty Table**: No approved contracts → verify no errors, empty state shows correctly
2. **Single Row**: Only one contract → sorting works without errors
3. **Duplicate Values**: Multiple contracts with same sort value → verify stable sort, secondary sort by another field
4. **Null/Undefined Values**: Missing `reviewed_at` or other optional fields → verify sort handles nulls (nulls last)
5. **Very Long Client Names**: Sorting with long strings → verify UI doesn't break, text truncation works
6. **Large Datasets**: 100+ contracts → verify performance is acceptable, consider pagination later
7. **Special Characters**: Client names with accents, ñ, etc. → verify locale-aware sorting works
8. **Rapid Clicking**: Click headers quickly → verify no race conditions, only latest request rendered
9. **Concurrent Users**: Multiple users sorting same table → verify no conflicts (stateless design)
10. **Authentication Expiry**: Token expires during sort → verify re-authentication flow works
11. **Network Errors**: API call fails → verify error message shown, retry option available
12. **Invalid Backend Data**: Malformed contract data → verify graceful degradation, no crashes

## Acceptance Criteria
✅ **AC1**: All six sortable column headers display a clickable sort indicator (up/down arrow)

✅ **AC2**: Clicking a column header for the first time sorts the table in descending order by that column

✅ **AC3**: Clicking the same column header again toggles the sort order to ascending

✅ **AC4**: Clicking a different column header sorts by that column in descending order (resets previous column)

✅ **AC5**: The active sort column is visually distinct (highlighted with color and visible arrow)

✅ **AC6**: Contract ID sorting works correctly (alphanumeric: ACT-2025-001 before ACT-2025-010)

✅ **AC7**: Contract Type sorting works correctly (enum: activos, inventario_bodega, otrosi)

✅ **AC8**: Cliente (client name) sorting works correctly (alphabetical, locale-aware for Spanish)

✅ **AC9**: NIT sorting works correctly (string/numeric)

✅ **AC10**: Cupo Aprobado (approved limit) sorting works correctly (numeric, highest to lowest in DESC)

✅ **AC11**: Fecha Aprobación (approval date) sorting works correctly (chronological, most recent first in DESC)

✅ **AC12**: Sorting persists correctly when using the "Actualizar" (refresh) button

✅ **AC13**: PDF download functionality continues to work correctly after sorting

✅ **AC14**: No errors in browser console during any sorting operation

✅ **AC15**: Backend API returns correctly sorted data matching frontend request

✅ **AC16**: Invalid sort parameters are handled gracefully (fallback to default sort)

✅ **AC17**: All existing unit tests pass with zero regressions

✅ **AC18**: New unit tests for sorting logic pass with 100% coverage

✅ **AC19**: Integration tests verify end-to-end sorting functionality

✅ **AC20**: Feature works correctly for all authorized user roles (operations, admin)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

### Backend Validation
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# Run all backend tests including new sorting tests
pytest tests/ -v

# Run specific sorting tests
pytest tests/test_contract_repository_sorting.py -v
pytest tests/test_operations_routes_sorting.py -v

# Check test coverage
pytest tests/ --cov=src --cov-report=html

# Run backend linting
flake8 src/

# Start backend server for manual testing
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Validation
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# Run TypeScript type checking
npm run build  # Runs: tsc -b && vite build

# Run linting
npm run lint

# Run frontend unit tests (once configured)
npm run test  # Note: Currently no testing framework configured

# Start frontend dev server for manual testing
npm run dev  # http://localhost:5173
```

### Integration Testing
```bash
# Terminal 1: Start backend
cd backend && source venv/bin/activate && python -m uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend && npm run dev

# Manual Browser Testing Checklist:
# 1. Navigate to http://localhost:5173
# 2. Login with operations or admin role
# 3. Navigate to Operations → Contratos Aprobados tab
# 4. Click each column header and verify sort order
# 5. Toggle each column between ASC/DESC
# 6. Download a PDF to verify functionality still works
# 7. Click "Actualizar" button to verify refresh works
# 8. Open browser DevTools Network tab:
#    - Verify query params in request: ?sort_by=reviewed_at&sort_order=desc
#    - Verify response data is correctly sorted
# 9. Test with different user roles (operations, admin)
# 10. Test error scenarios (network offline, invalid token)
```

### API Testing (Manual with curl)
```bash
# Get approved contracts sorted by contract_id ascending
curl -X GET "http://localhost:8000/api/operations/contracts/approved?sort_by=contract_id&sort_order=asc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Get approved contracts sorted by reviewed_at descending (default)
curl -X GET "http://localhost:8000/api/operations/contracts/approved?sort_by=reviewed_at&sort_order=desc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Get approved contracts sorted by cupo_plataforma descending
curl -X GET "http://localhost:8000/api/operations/contracts/approved?sort_by=cupo_plataforma&sort_order=desc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Test invalid sort field (should fallback to default)
curl -X GET "http://localhost:8000/api/operations/contracts/approved?sort_by=invalid_field&sort_order=asc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### Database Query Verification (Supabase SQL Editor)
```sql
-- Verify contracts exist in database
SELECT contract_id, contract_type, client_nit, reviewed_at, status,
       data_snapshot->>'nombre_importador' as cliente,
       (data_snapshot->>'cupo_plataforma')::numeric as cupo
FROM contract_generations
WHERE status = 'approved'
ORDER BY reviewed_at DESC;

-- Test JSONB field sorting (nombre_importador)
SELECT contract_id, data_snapshot->>'nombre_importador' as cliente
FROM contract_generations
WHERE status = 'approved'
ORDER BY data_snapshot->>'nombre_importador' ASC;

-- Test JSONB field sorting (cupo_plataforma)
SELECT contract_id, (data_snapshot->>'cupo_plataforma')::numeric as cupo
FROM contract_generations
WHERE status = 'approved'
ORDER BY (data_snapshot->>'cupo_plataforma')::numeric DESC;
```

### Production Deployment Validation
```bash
# After deploying to Vercel/Render, test production URLs:

# Test production frontend
# Navigate to: https://finkargo-automation-hub.vercel.app/
# Perform full manual testing checklist above

# Test production backend API
curl -X GET "https://finkargo-automation-hub.onrender.com/api/operations/contracts/approved?sort_by=reviewed_at&sort_order=desc" \
  -H "Authorization: Bearer PRODUCTION_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Monitor error logs
# Vercel: Check deployment logs in Vercel dashboard
# Render: Check logs in Render dashboard
# Supabase: Check logs in Supabase dashboard
```

## Notes

### Implementation Considerations

**JSONB Field Sorting (Critical)**:
- Supabase/PostgREST uses special syntax for JSONB field sorting: `data_snapshot->>'nombre_importador'`
- The repository layer must construct this correctly: `.order('data_snapshot->>nombre_importador', desc=True)`
- Numeric JSONB fields require casting: `(data_snapshot->>'cupo_plataforma')::numeric`
- Frontend should map friendly names to database JSONB paths

**Performance Optimization**:
- Current implementation uses client-side sorting (all data fetched, sorted in memory)
- For future enhancement with 1000+ contracts, consider:
  - Server-side pagination with sorting
  - Database indexes on frequently sorted columns
  - Lazy loading / infinite scroll
- Current dataset size (<100 contracts) performs well with client-side approach

**State Management Pattern**:
- Using React hooks (`useState`) for sort state is sufficient for this component
- No need for global state management (Context API, Redux) as sort state is local to table
- Sort state resets on component unmount (expected behavior)

**Sorting Algorithm**:
- Backend: PostgreSQL native sorting (highly efficient)
- Frontend: If implementing client-side as fallback, use `.sort()` with locale-aware comparator for strings

**Accessibility (a11y)**:
- `TableSortLabel` provides built-in ARIA labels for screen readers
- Ensure keyboard navigation works (Tab to header, Enter/Space to sort)
- Test with screen reader (VoiceOver on Mac, NVDA on Windows)

**Internationalization (i18n)**:
- Spanish locale already used for date/currency formatting
- String sorting should use Spanish locale rules for accented characters
- Consider using `Intl.Collator` for locale-aware sorting if implementing client-side

**Future Enhancements** (Out of Scope for Current Feature):
- Multi-column sorting (primary + secondary sort)
- Persistent sort preferences (saved in user profile or localStorage)
- Export sorted data to CSV/Excel
- Filter + sort combinations
- Pagination (limit/offset) with sort
- Real-time updates (WebSocket) with sort preservation

**Known Limitations**:
- No sorting on "Estado" column (always "Aprobado" - single value)
- No sorting on "Acciones" column (non-sortable action buttons)
- Null values in sort column will sort to end (PostgreSQL default behavior)
- Rapid clicking may trigger multiple API calls (consider debouncing if performance issue)

**Security Considerations**:
- Sort field names are validated against whitelist (prevent SQL injection)
- User must have valid JWT token and operations/admin role
- RLS (Row Level Security) policies still enforced on database level
- No sensitive data exposed in sort parameters (only field names)

**Error Handling Strategy**:
- Invalid sort field → fallback to default sort (reviewed_at DESC)
- Invalid sort order → fallback to 'desc'
- Network error → show error message, allow retry via "Actualizar" button
- Empty result → show existing empty state message
- Authentication error → redirect to login page (handled by global auth interceptor)

**Dependencies**:
- No new npm packages required (Material-UI already includes `TableSortLabel`)
- No new Python packages required (Supabase client already supports `.order()`)
- TypeScript 5.9.3 and React 19.1.1 fully support required features

**Testing Data Requirements**:
- Need at least 10 approved contracts with varied data for meaningful testing
- Test data should include:
  - Different contract types (activos, otrosi, inventario_bodega)
  - Different client names (A-Z, with accents)
  - Different NITs
  - Different cupo_plataforma values (range: $1M - $50M)
  - Different reviewed_at dates (last 3 months)
- Can use Supabase SQL Editor to create test data if needed

**Rollback Plan**:
- If feature causes issues, can quickly revert by:
  1. Reverting commit on GitHub
  2. Vercel/Render will auto-deploy previous working version
  3. Database schema unchanged (no migrations to rollback)
- Feature is additive (no breaking changes to existing functionality)

**Documentation Updates Needed After Implementation**:
- Update `CLAUDE.md` with sorting feature description
- Add entry to `PROGRESS.md` documenting feature completion date
- Create implementation note: `implementations/YYYYMMDD_contratos_aprobados_sorting.md`
- Update API documentation in `operations_routes.py` docstrings
- Consider adding user guide screenshot to `README.md` or wiki
