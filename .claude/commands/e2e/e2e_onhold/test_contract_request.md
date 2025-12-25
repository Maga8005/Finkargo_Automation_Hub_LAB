# E2E Test: Operations Contract Request

Test the contract request workflow for Operations users in Colombia contracts.

## User Story

As an Operations team member  
I want to request a new Activos contract for a client  
So that Legal can review and approve it for final generation

## Prerequisites

- User logged in with `operations` role
- Backend and frontend servers running
- At least one client exists in the database (searchable by NIT)

## Test Steps

1. **Login as Operations user** (or verify already logged in with operations role)
2. Navigate to `/operations/contratos-colombia`
3. Take a screenshot of the Operations dashboard
4. **Verify** dashboard loads with contract tabs visible:
   - Activos tab
   - Otrosí tab (if applicable)

5. Click on "Nueva Solicitud" or the contract request section
6. **Verify** contract request form appears (FKContractRequest component)
7. Take a screenshot of empty contract request form

8. **Fill out contract request form:**
   - Search for client by NIT (use test NIT: 900123456)
   - **Verify** client autocomplete/search returns results
   - Select a client from results
   - **Verify** client information populates (company name, address, etc.)
   - Select contract type: "Activos"
   - Fill any additional required fields

9. Take a screenshot of the filled contract form
10. Click submit/request button
11. Wait for form submission to complete
12. **Verify** success message or toast appears
13. **Verify** new contract appears in pending list with status "under_review"
14. Take a screenshot showing the new contract in the list

## Success Criteria
- Operations dashboard loads correctly
- Client search functionality works
- Form validation prevents invalid submissions
- Contract is created with correct status ("under_review")
- Contract ID follows format: ACT-{YEAR}-{SEQUENCE} (e.g., ACT-2025-001)
- Success feedback is displayed to user
- 4 screenshots are captured:
  1. Operations dashboard
  2. Empty contract request form
  3. Filled contract form
  4. Contract list showing new entry

## Form Fields to Verify
- Client NIT (required)
- Client company name (auto-populated)
- Contract type selection
- Any additional required fields per contract type
