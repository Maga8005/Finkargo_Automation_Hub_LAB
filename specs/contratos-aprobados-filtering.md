# Feature: Add Filtering to Contratos Aprobados Table

## Feature Description
Add comprehensive filtering functionality to the "Contratos Aprobados" (Approved Contracts) table in the Operations department dashboard. Users will be able to filter the table by multiple columns including contract type, client name, NIT, approval date range, and credit limit range. This enhancement will improve user experience by allowing Operations team members to quickly find specific approved contracts without having to scroll through the entire list or rely solely on sorting.

The filtering UI will be intuitive, using Material-UI components consistent with the existing Finkargo design system, and will work seamlessly with the existing sorting functionality.

## User Story
As an Operations team member
I want to filter the approved contracts table by various criteria (contract type, client name, NIT, date range, credit limit)
So that I can quickly find specific approved contracts I need to download for client signature without scrolling through the entire list

## Problem Statement
Currently, the Contratos Aprobados table in the Operations dashboard displays all approved contracts with sorting capabilities only. When the number of approved contracts grows, users must:
- Scroll through many rows to find specific contracts
- Use browser search (Ctrl+F) which is not intuitive
- Rely only on sorting which doesn't reduce the dataset

This becomes inefficient as the business grows and more contracts are approved. Users need a way to narrow down the displayed contracts based on specific criteria such as:
- Contract type (Activos, Otrosí, Inventario Bodega)
- Client name or NIT
- Approval date range
- Credit limit (cupo_plataforma) range

## Solution Statement
Implement a multi-criteria filtering system that:

1. **Backend Enhancement**: Extend the existing `/api/operations/contracts/approved` endpoint to accept additional optional query parameters for filtering:
   - `client_name` - Filter by client name (nombre_importador) using ILIKE pattern matching
   - `client_nit` - Filter by exact or partial NIT match
   - `date_from` - Filter contracts approved on or after this date
   - `date_to` - Filter contracts approved on or before this date
   - `cupo_min` - Filter contracts with credit limit >= this value
   - `cupo_max` - Filter contracts with credit limit <= this value
   - Keep existing `contract_type` filter

2. **Repository Layer**: Update `ContractRepository.get_approved_contracts()` to apply these filters using Supabase query builders with proper JSONB field access for data_snapshot fields.

3. **Frontend Filter UI**: Add a collapsible filter panel above the table with:
   - Contract type multi-select checkboxes (with Chip badges)
   - Client name text search field (debounced)
   - NIT text search field
   - Date range picker (from/to dates)
   - Credit limit range inputs (min/max)
   - "Apply Filters" and "Clear Filters" buttons
   - Filter count badge showing number of active filters

4. **State Management**: Use React useState hooks to manage filter state and sync with API calls, ensuring filters work seamlessly with existing sorting functionality.

5. **UX Enhancements**:
   - Show active filter count in the table header
   - Persist filter state during tab switches (optional localStorage)
   - Show "No results" message when filters yield empty results
   - Maintain filter state when sorting is changed

## Relevant Files

### Existing Files to Modify

- **`/Users/danielrestrepo/Finkargo_Automation_Hub/frontend/src/components/forms/FKApprovedContracts.tsx`** (340 lines)
  - Currently implements sorting functionality for the approved contracts table
  - Need to add: Filter UI components above the table
  - Need to add: Filter state management (useState hooks)
  - Need to add: Filter application logic that works with existing sorting
  - Need to update: API call to include filter parameters
  - Already has: Table display, PDF download, date/currency formatting, contract type badges

- **`/Users/danielrestrepo/Finkargo_Automation_Hub/frontend/src/services/operationsService.ts`** (147 lines)
  - `getApprovedContracts()` method currently accepts `contractType`, `sortBy`, `sortOrder`
  - Need to extend: Add filter parameters to method signature and params object
  - Already handles: Query parameter building for API calls

- **`/Users/danielrestrepo/Finkargo_Automation_Hub/backend/src/adapter/rest/operations_routes.py`** (280 lines)
  - `GET /api/operations/contracts/approved` endpoint (lines 162-193)
  - Currently accepts: `contract_type`, `sort_by`, `sort_order` query parameters
  - Need to add: New query parameters for filtering (client_name, client_nit, date_from, date_to, cupo_min, cupo_max)
  - Need to pass: New filter parameters to repository layer
  - Already has: Role-based access control with `require_operations_role`

- **`/Users/danielrestrepo/Finkargo_Automation_Hub/backend/src/repositorio/contract_repository.py`** (321 lines)
  - `get_approved_contracts()` method (lines 172-220)
  - Currently filters by: status='approved', optional contract_type
  - Currently sorts by: Multiple fields including JSONB fields
  - Need to add: Additional filter conditions for new filter parameters
  - Need to handle: JSONB field filtering (data_snapshot->nombre_importador, data_snapshot->cupo_plataforma)
  - Need to handle: Date range filtering with proper timezone handling
  - Need to handle: Partial text matching with ILIKE for client name and NIT

- **`/Users/danielrestrepo/Finkargo_Automation_Hub/frontend/src/types/legal.ts`** (139 lines)
  - Contains `OperationsSortField` and `OperationsSortOrder` types
  - Need to add: New interface for filter parameters (OperationsFilterParams)
  - Need to add: Type definitions for filter state management

### New Files

No new files need to be created. All functionality will be added to existing files.

## Implementation Plan

### Phase 1: Foundation - Backend Filter Support
Set up the backend infrastructure to handle multiple filter parameters. This includes extending the API endpoint to accept new query parameters, validating them, and updating the repository layer to apply the filters in database queries.

**Key Tasks:**
- Add filter parameter types/interfaces
- Extend repository method with filter logic
- Update API endpoint to accept and validate filter parameters
- Test backend filtering in isolation

### Phase 2: Core Implementation - Frontend Filter UI
Build the user interface components for filtering. This includes creating a collapsible filter panel with appropriate input controls (checkboxes, text fields, date pickers, number inputs) following the Finkargo design system.

**Key Tasks:**
- Create filter state management hooks
- Build filter UI components (panel, inputs, buttons)
- Implement filter application and clearing logic
- Connect filter state to API service calls
- Ensure filters work with existing sorting

### Phase 3: Integration - End-to-End Testing
Integrate the filter functionality with the existing sorting and ensure all features work together seamlessly. Test edge cases, validate UX flow, and ensure proper error handling.

**Key Tasks:**
- Test filter + sort combinations
- Test empty states and error handling
- Validate filter persistence across tab switches
- Performance testing with large datasets
- Cross-browser testing

## Step by Step Tasks

### Step 1: Add Backend Filter Types and Validation
- Add filter parameter validation in `operations_routes.py`
- Create type hints for optional filter parameters in the endpoint
- Document the new query parameters in the endpoint docstring
- Add validation for date format (ISO 8601) and numeric ranges

### Step 2: Extend Repository Layer with Filter Logic
- Update `contract_repository.py` `get_approved_contracts()` method signature
- Add filter conditions for `client_name` using JSONB ILIKE query: `data_snapshot->>'nombre_importador' ILIKE '%{client_name}%'`
- Add filter condition for `client_nit` using ILIKE on regular column: `client_nit ILIKE '%{client_nit}%'`
- Add date range filters using `gte()` and `lte()` on `reviewed_at` field
- Add credit limit range filters using JSONB field access and numeric comparison
- Ensure all filters can be applied independently or in combination
- Add logging for applied filters to aid debugging

### Step 3: Update API Endpoint to Accept Filter Parameters
- Modify `GET /api/operations/contracts/approved` in `operations_routes.py`
- Add query parameters: `client_name`, `client_nit`, `date_from`, `date_to`, `cupo_min`, `cupo_max` (all Optional[str] or Optional[float])
- Validate date formats and convert to proper datetime objects
- Validate numeric ranges (min <= max)
- Pass filter parameters to repository method
- Update endpoint docstring with new parameters
- Test endpoint manually with various filter combinations using Swagger UI

### Step 4: Extend Frontend Type Definitions
- Open `frontend/src/types/legal.ts`
- Add `OperationsFilterParams` interface with fields:
  - `contract_types?: string[]` (array for multi-select)
  - `client_name?: string`
  - `client_nit?: string`
  - `date_from?: string`
  - `date_to?: string`
  - `cupo_min?: number`
  - `cupo_max?: number`
- Export the new interface for use in components and services

### Step 5: Update Operations Service with Filter Parameters
- Open `frontend/src/services/operationsService.ts`
- Update `getApprovedContracts()` method signature to accept filter parameters
- Change signature from `(contractType?, sortBy?, sortOrder?)` to `(filters?: OperationsFilterParams, sortBy?, sortOrder?)`
- Build query parameters from filter object, handling array serialization for contract_types
- Ensure backward compatibility with existing calls
- Add JSDoc comments documenting the new filter parameters

### Step 6: Create Filter State Management in Component
- Open `frontend/src/components/forms/FKApprovedContracts.tsx`
- Add useState hooks for filter state:
  - `const [filters, setFilters] = useState<OperationsFilterParams>({})`
  - `const [showFilters, setShowFilters] = useState(false)` (for collapsible panel)
  - `const [activeFilterCount, setActiveFilterCount] = useState(0)`
- Create helper function `countActiveFilters()` to count non-empty filter values
- Update `loadApprovedContracts()` to include filter state in API call
- Update useEffect dependency array to include filters state

### Step 7: Build Filter UI Panel Component
- In `FKApprovedContracts.tsx`, create filter panel UI above the table
- Use Material-UI `Collapse` component for expandable filter panel
- Add "Filters" button with badge showing active filter count
- Create filter form layout using `Grid` with proper spacing
- Add contract type checkboxes (Activos, Otrosí, Inventario Bodega) with color-coded Chips
- Add client name TextField with debounced onChange (300ms delay)
- Add NIT TextField with debounced onChange
- Add date range pickers using Material-UI DatePicker or TextField with type="date"
- Add numeric inputs for credit limit range (min/max) with proper formatting
- Style filter panel with light background color (grey.50) and border

### Step 8: Implement Filter Action Handlers
- Create `handleFilterChange()` function to update individual filter values
- Create `handleApplyFilters()` function to trigger data reload with current filters
- Create `handleClearFilters()` function to reset all filters to default state and reload data
- Add validation for date ranges (from <= to) and credit limit ranges (min <= max)
- Show validation errors using Material-UI Alert or helper text
- Debounce text input filters to avoid excessive API calls

### Step 9: Integrate Filters with Table Header
- Update table header to show active filter indicator
- Modify "Contratos Aprobados ({contracts.length})" text to include filter status
- Add visual indicator (Chip or Badge) when filters are active
- Show "Filtered: X results" when filters are applied
- Ensure "Actualizar" button respects current filter state

### Step 10: Update Empty State Handling
- Modify empty state Alert to distinguish between "no approved contracts" vs "no results matching filters"
- When filters are active and no results, show message: "No se encontraron contratos con los filtros aplicados. Intenta ajustar los filtros."
- Add "Clear Filters" button in empty state when filters are active
- Maintain existing empty state when no filters are applied

### Step 11: Add Filter Persistence (Optional Enhancement)
- Implement localStorage persistence for filter state
- Save filters to localStorage on change: `localStorage.setItem('approved-contracts-filters', JSON.stringify(filters))`
- Load filters from localStorage on component mount
- Add "Reset to Defaults" option to clear persisted filters
- Handle localStorage errors gracefully

### Step 12: Write Backend Unit Tests
- Create test file `backend/tests/test_operations_filters.py`
- Test `get_approved_contracts()` with each filter parameter individually
- Test filter combinations (e.g., contract_type + date_range)
- Test edge cases: invalid dates, invalid ranges, empty strings
- Test JSONB field filtering for client name and credit limit
- Test partial matching for NIT and client name (ILIKE behavior)
- Ensure tests use test database with fixture data

### Step 13: Write Frontend Component Tests
- Add test file `frontend/src/components/forms/__tests__/FKApprovedContracts.test.tsx` (if testing framework exists)
- Test filter UI rendering
- Test filter state changes
- Test filter application and clearing
- Test API call with correct filter parameters
- Test empty state with filters active
- Mock `operationsService.getApprovedContracts()` for controlled testing

### Step 14: Manual Testing - Filter Functionality
- Start dev servers (frontend and backend)
- Navigate to Operations Dashboard → Contratos Aprobados tab
- Test each filter individually:
  - Filter by contract type (check/uncheck each type)
  - Filter by client name (partial text matching)
  - Filter by NIT (partial matching)
  - Filter by date range (past week, past month, custom range)
  - Filter by credit limit range
- Test filter combinations (2-3 filters at once)
- Verify filter count badge updates correctly
- Test clear filters functionality

### Step 15: Manual Testing - Integration with Sorting
- Apply a filter (e.g., contract_type = 'activos')
- Test sorting by each column while filter is active
- Verify filtered results remain filtered after sorting
- Change sort direction and verify filter persists
- Clear filter and verify all data returns
- Apply multiple filters and test sorting behavior

### Step 16: Manual Testing - Edge Cases
- Test with no approved contracts in database
- Test with filters that yield zero results
- Test with invalid date ranges (from > to)
- Test with invalid credit limit ranges (min > max)
- Test with special characters in text filters
- Test with very large numeric values
- Test rapid filter changes (debounce behavior)
- Test browser back/forward with active filters

### Step 17: Manual Testing - UX and Accessibility
- Test keyboard navigation through filter inputs
- Test filter panel expand/collapse animation
- Verify filter panel is responsive on tablet and mobile views
- Test screen reader compatibility (aria labels)
- Verify filter inputs have proper labels and placeholders
- Test focus management when opening/closing filter panel
- Verify error messages are clear and actionable

### Step 18: Performance Testing
- Load 100+ approved contracts into the database
- Test filter response time with large dataset
- Verify debouncing works correctly for text inputs (no lag)
- Test sorting + filtering performance
- Monitor network requests (should not duplicate calls)
- Check backend query performance with database indexes
- Verify no memory leaks with repeated filter applications

### Step 19: Run Full Validation Commands
- Execute all commands from the Validation Commands section below
- Ensure all backend tests pass with zero failures
- Ensure all TypeScript compilation succeeds with no errors
- Run linting and fix any style issues
- Verify production build succeeds
- Test production build locally with `npm run preview`

### Step 20: Create Implementation Documentation
- Document the new filter feature in a new implementation file: `implementations/YYYYMMDD_approved_contracts_filtering.md`
- Include screenshots of the filter UI (if possible)
- Document the filter parameters and their behavior
- Add troubleshooting section for common issues
- Update PROGRESS.md with feature completion status
- Update CLAUDE.md if any architectural patterns changed

## Testing Strategy

### Unit Tests

**Backend Tests** (`backend/tests/test_operations_filters.py`):
- `test_filter_by_contract_type_single()` - Filter by single contract type
- `test_filter_by_contract_type_multiple()` - Filter by multiple contract types
- `test_filter_by_client_name_exact_match()` - Exact client name match
- `test_filter_by_client_name_partial_match()` - Partial client name match (ILIKE)
- `test_filter_by_client_nit_exact()` - Exact NIT match
- `test_filter_by_client_nit_partial()` - Partial NIT match
- `test_filter_by_date_range_from_only()` - Filter with only date_from
- `test_filter_by_date_range_to_only()` - Filter with only date_to
- `test_filter_by_date_range_both()` - Filter with both date_from and date_to
- `test_filter_by_cupo_min_only()` - Filter with only cupo_min
- `test_filter_by_cupo_max_only()` - Filter with only cupo_max
- `test_filter_by_cupo_range()` - Filter with both cupo_min and cupo_max
- `test_multiple_filters_combined()` - Test 3+ filters at once
- `test_filters_with_sorting()` - Ensure filters work with sorting
- `test_empty_results_with_filters()` - Filters that yield no results
- `test_invalid_date_format()` - Should handle gracefully
- `test_invalid_numeric_range()` - Min > max should return appropriate response

**Frontend Tests** (if testing framework available):
- `test_filter_panel_renders()` - Filter UI renders correctly
- `test_filter_state_updates()` - State updates when inputs change
- `test_apply_filters_calls_api()` - Apply button triggers API call with correct params
- `test_clear_filters_resets_state()` - Clear button resets all filters
- `test_active_filter_count_updates()` - Badge shows correct count
- `test_empty_state_with_filters()` - Shows correct message when no results
- `test_debounced_text_inputs()` - Text inputs debounce correctly

### Integration Tests

**Full Stack Integration**:
- `test_filter_and_sort_together()` - Apply filters then sort, verify both work
- `test_filter_across_all_contract_types()` - Filter each contract type
- `test_complex_filter_scenario()` - Use all filters at once with sorting
- `test_filter_persistence_across_tab_switches()` - If persistence implemented
- `test_clear_filters_with_sort_active()` - Clearing filters maintains sort

### Edge Cases

**Data Edge Cases**:
- No approved contracts exist in database
- All approved contracts are filtered out (empty result)
- Only one contract matches filters
- Very large credit limit values (> 1 billion)
- Contracts with null data_snapshot fields
- Contracts with missing nombre_importador or cupo_plataforma

**Input Edge Cases**:
- Empty string in text filters
- Whitespace-only in text filters
- Special characters in client name (accents, ñ, punctuation)
- Invalid date formats (not ISO 8601)
- Date range where from > to
- Credit limit range where min > max
- Negative credit limit values
- Zero values for credit limits

**UX Edge Cases**:
- Rapid clicking of Apply Filters button
- Changing filters while API call in progress
- Network error during filter application
- Session timeout during filtering
- Browser back/forward with active filters
- Multiple tabs with different filters (localStorage conflict)

**Performance Edge Cases**:
- Filtering 500+ contracts
- Text filter matching 100+ contracts
- Extremely long client names (> 100 characters)
- Rapid typing in debounced text inputs
- Applying all filters simultaneously

## Acceptance Criteria

1. **Filter UI Rendering**:
   - [ ] Filter panel is collapsible and starts collapsed by default
   - [ ] Filter button shows active filter count badge when filters are applied
   - [ ] All filter inputs are clearly labeled and have appropriate placeholders
   - [ ] Filter panel uses Finkargo design system (colors, spacing, typography)
   - [ ] Filter panel is responsive on mobile, tablet, and desktop views

2. **Contract Type Filter**:
   - [ ] Users can select multiple contract types via checkboxes
   - [ ] Contract type chips display with correct colors (Activos: info, Otrosí: warning, Inventario: success)
   - [ ] Selecting no contract types shows all contracts
   - [ ] Backend filters correctly by single or multiple contract types

3. **Text Filters (Client Name and NIT)**:
   - [ ] Client name filter supports partial matching (case-insensitive)
   - [ ] NIT filter supports partial matching
   - [ ] Text filters are debounced (300ms) to avoid excessive API calls
   - [ ] Empty or whitespace-only input is treated as "no filter"
   - [ ] Special characters (accents, ñ) are handled correctly

4. **Date Range Filter**:
   - [ ] Users can filter by "from date" only, "to date" only, or both
   - [ ] Date inputs use appropriate UI (date picker or type="date" input)
   - [ ] Invalid date ranges (from > to) show validation error and prevent filter application
   - [ ] Date filtering uses proper timezone handling (UTC or local)
   - [ ] Dates are formatted consistently with the rest of the application

5. **Credit Limit Range Filter**:
   - [ ] Users can filter by minimum credit limit, maximum credit limit, or both
   - [ ] Numeric inputs have proper formatting (thousands separator)
   - [ ] Invalid ranges (min > max) show validation error
   - [ ] Zero values are valid filter inputs
   - [ ] Negative values are rejected or ignored

6. **Filter Application**:
   - [ ] "Apply Filters" button triggers data reload with all active filters
   - [ ] Filters work independently (each filter can be used alone)
   - [ ] Filters work in combination (multiple filters narrow results correctly)
   - [ ] Filter state persists when sorting is changed
   - [ ] Loading indicator shows while filtered data is being fetched

7. **Clear Filters**:
   - [ ] "Clear Filters" button resets all filters to default state
   - [ ] Clearing filters reloads data to show all approved contracts
   - [ ] Active filter count badge updates to 0 after clearing
   - [ ] Clear button is visible whenever any filter is active

8. **Empty States**:
   - [ ] When no approved contracts exist, appropriate message is shown
   - [ ] When filters yield no results, distinct message is shown ("No results with current filters")
   - [ ] Empty state with active filters includes "Clear Filters" quick action
   - [ ] Empty state messages are in Spanish and user-friendly

9. **Integration with Sorting**:
   - [ ] Sorting works correctly when filters are active
   - [ ] Changing sort column/direction does not clear active filters
   - [ ] Filter + sort combinations produce correct results (filtered AND sorted)
   - [ ] Sort state persists when filters are changed

10. **Backend Functionality**:
    - [ ] API endpoint accepts all new filter parameters as optional query params
    - [ ] Repository layer applies filters using correct SQL/Supabase queries
    - [ ] JSONB fields (nombre_importador, cupo_plataforma) are filtered correctly
    - [ ] Filter parameters are properly validated on backend
    - [ ] API returns 400 error with clear message for invalid filter inputs

11. **Performance**:
    - [ ] Filter application completes in < 1 second for datasets up to 500 contracts
    - [ ] Debouncing prevents excessive API calls during typing
    - [ ] No memory leaks with repeated filter applications
    - [ ] Backend queries use appropriate indexes (if needed)

12. **Error Handling**:
    - [ ] Network errors during filter application show user-friendly error message
    - [ ] Invalid filter inputs show validation errors inline
    - [ ] Backend errors (500) are caught and displayed appropriately
    - [ ] User can recover from errors without page reload

13. **Accessibility**:
    - [ ] All filter inputs are keyboard navigable
    - [ ] Filter inputs have proper ARIA labels
    - [ ] Error messages are announced to screen readers
    - [ ] Focus management works correctly when opening/closing filter panel

14. **Documentation**:
    - [ ] Filter feature is documented in implementation notes
    - [ ] API endpoint documentation includes new filter parameters
    - [ ] Code includes comments explaining complex filter logic
    - [ ] README or CLAUDE.md updated if needed

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

### Backend Tests
```bash
cd backend
pytest tests/ -v
```
This command runs all backend tests including the new filter tests to ensure:
- Filter logic works correctly in the repository layer
- API endpoint accepts and validates filter parameters properly
- All existing tests still pass (no regressions)

### Backend Linting
```bash
cd backend
python -m flake8 src/ --max-line-length=120
```
Validates Python code style and catches potential issues.

### Frontend TypeScript Compilation
```bash
cd frontend
npm run build
```
Ensures all TypeScript code compiles without errors, including:
- New filter types are correctly defined
- Component props and state are properly typed
- No type errors introduced by filter changes

### Frontend Linting
```bash
cd frontend
npm run lint
```
Validates TypeScript/React code style and catches common issues.

### Frontend Development Server Test
```bash
cd frontend
npm run dev
```
Start the development server and manually verify:
1. Navigate to Operations Dashboard → Contratos Aprobados tab
2. Expand filter panel
3. Apply various filter combinations
4. Verify results are correctly filtered
5. Test filter + sort combinations
6. Test clear filters functionality
7. Check console for errors (should be none)

### Backend Development Server Test
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Start the backend server and test via Swagger UI (http://localhost:8000/docs):
1. Navigate to GET /api/operations/contracts/approved
2. Test with various filter parameter combinations
3. Verify response data is correctly filtered
4. Test invalid inputs (date ranges, numeric ranges)
5. Verify proper error responses

### API Integration Test (using curl)
```bash
# Test filter by contract type
curl -X GET "http://localhost:8000/api/operations/contracts/approved?contract_type=activos" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test filter by client name
curl -X GET "http://localhost:8000/api/operations/contracts/approved?client_name=test" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test filter by date range
curl -X GET "http://localhost:8000/api/operations/contracts/approved?date_from=2025-01-01&date_to=2025-12-31" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test multiple filters
curl -X GET "http://localhost:8000/api/operations/contracts/approved?contract_type=activos&cupo_min=1000000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
Replace YOUR_TOKEN with actual JWT token from Supabase auth.

### End-to-End Manual Test Checklist
**Prerequisites**: Both frontend and backend servers running, test user logged in with Operations or Admin role.

1. **Basic Filter Tests**:
   - [ ] Apply single contract type filter
   - [ ] Apply multiple contract type filters
   - [ ] Apply client name filter (partial text)
   - [ ] Apply NIT filter
   - [ ] Apply date range filter (from and to)
   - [ ] Apply credit limit range filter
   - [ ] Verify active filter count badge updates correctly

2. **Combined Filter Tests**:
   - [ ] Apply contract type + date range
   - [ ] Apply client name + credit limit range
   - [ ] Apply all filters simultaneously
   - [ ] Verify results match all filter criteria

3. **Filter + Sort Tests**:
   - [ ] Apply filter, then sort by different columns
   - [ ] Sort, then apply filter
   - [ ] Change sort direction with filters active
   - [ ] Verify filtered results remain filtered after sorting

4. **Clear Filters Tests**:
   - [ ] Clear all filters with "Clear Filters" button
   - [ ] Verify all inputs reset to default
   - [ ] Verify all contracts display after clearing
   - [ ] Verify filter count badge shows 0

5. **Edge Case Tests**:
   - [ ] Apply filter that yields zero results
   - [ ] Apply invalid date range (from > to)
   - [ ] Apply invalid credit range (min > max)
   - [ ] Type rapidly in text filters (test debounce)
   - [ ] Leave text filter with whitespace only

6. **Regression Tests**:
   - [ ] Download PDF with filter active
   - [ ] Refresh button works with filters active
   - [ ] Switch to other tabs and back, verify state
   - [ ] Test with no approved contracts in database
   - [ ] Verify existing sorting still works without filters

### Performance Validation
```bash
# Backend query performance (run in database console)
EXPLAIN ANALYZE
SELECT * FROM contract_generations
WHERE status = 'approved'
  AND contract_type = 'activos'
  AND data_snapshot->>'nombre_importador' ILIKE '%test%'
  AND (data_snapshot->>'cupo_plataforma')::bigint >= 1000000
ORDER BY reviewed_at DESC;
```
Verify query execution time is < 100ms for typical dataset sizes.

## Notes

### Future Enhancements
- **Export Filtered Results**: Add button to export filtered contracts to CSV/Excel
- **Saved Filter Presets**: Allow users to save commonly used filter combinations
- **Advanced Date Filters**: Add quick filters like "Last 7 days", "Last 30 days", "This month"
- **Filter by Reviewer**: Add filter to show contracts approved by specific legal team member
- **Filter History**: Show recently used filters for quick reapplication

### Technical Considerations
- **JSONB Field Indexing**: If filter performance becomes an issue with large datasets, consider adding GIN indexes on JSONB fields in PostgreSQL:
  ```sql
  CREATE INDEX idx_contract_generations_data_snapshot_nombre
  ON contract_generations USING gin ((data_snapshot->'nombre_importador'));
  ```
- **Date Timezone Handling**: Ensure consistent timezone handling (UTC) across frontend and backend for date filters
- **Filter Parameter Serialization**: For contract_types array, use comma-separated string or repeated query params
- **Debounce Implementation**: Use lodash debounce or custom hook to avoid excessive API calls
- **State Persistence**: If localStorage is used, implement versioning to handle schema changes

### Dependencies
- No new npm packages required (using existing Material-UI components)
- No new Python packages required (using existing Supabase query builders)
- Feature builds on existing sorting functionality implemented in feature-5

### Backend Security
- Ensure all filter inputs are properly sanitized to prevent SQL injection
- Use parameterized queries (Supabase query builder handles this)
- Validate filter parameter types and ranges on backend
- RBAC already in place via `require_operations_role` decorator

### UX Patterns Followed
- Filter panel follows established collapsible pattern used elsewhere in the app
- Filter inputs use Material-UI components consistent with Finkargo design system
- Active filter count badge follows same pattern as notification badges
- Error messages are in Spanish and user-friendly
- Loading states use consistent CircularProgress component

### Related Features
- This feature builds directly on the sorting feature implemented in feature-5 (PR #6)
- Complements the contract generation workflow (Operations → Legal → Approved)
- Prepares foundation for future analytics/reporting features

### Accessibility Notes
- All filter inputs should have proper labels (not just placeholders)
- Date pickers should be keyboard accessible
- Error messages should have appropriate ARIA roles
- Filter panel should have aria-expanded attribute
- Active filters should be announced to screen readers

### Browser Compatibility
- Ensure date input type="date" fallback for older browsers
- Test filter panel collapse/expand animation in Safari, Firefox, Chrome
- Verify number input formatting works cross-browser
- Test on iOS and Android mobile browsers
