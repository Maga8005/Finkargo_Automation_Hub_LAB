# E2E Test: Legal Contract Review

Test the contract review and approval workflow for Legal users.

## User Story

As a Legal reviewer  
I want to review and approve pending contracts  
So that Operations can download the final approved documents

## Prerequisites

- User logged in with `legal` role
- Backend and frontend servers running
- At least one contract exists with status "under_review"

## Test Steps

1. **Login as Legal user** (or verify already logged in with legal role)
2. Navigate to `/department/legal`
3. Take a screenshot of the Legal dashboard
4. **Verify** dashboard loads with appropriate tabs:
   - Review Queue (FKReviewQueue)
   - Client Data Import (if applicable)
   - Statistics section

5. Click on "Revisión" or pending review tab
6. **Verify** contract review queue displays
7. **Verify** at least one contract appears in the queue with status "under_review"
8. Take a screenshot of the review queue

9. Click on a pending contract to view details
10. **Verify** contract details modal/page opens
11. **Verify** contract information is displayed:
    - Contract ID (format: ACT-2025-XXX or similar)
    - Client information (NIT, company name)
    - Contract type
    - Requested date
    - Requesting user
12. Take a screenshot of contract details

13. **Approve the contract:**
    - Click "Aprobar" (approve) button
    - Add optional review notes if field exists
    - Confirm the approval action

14. **Verify** approval succeeds:
    - Success message/toast appears
    - Contract status changes to "approved"
    - Contract moves out of pending queue

15. Take a screenshot showing approval confirmation

16. **Verify** approved contract is available for download:
    - Navigate to approved contracts section
    - Find the just-approved contract
    - **Verify** download options exist (DOCX, PDF)

## Success Criteria
- Legal dashboard loads for legal role user
- Review queue displays pending contracts
- Contract details are viewable
- Approval action completes successfully
- Contract status updates to "approved"
- Download options become available for approved contracts
- 4 screenshots are captured:
  1. Legal dashboard
  2. Review queue with pending contracts
  3. Contract details view
  4. Approval confirmation

## API Endpoints Exercised
- GET `/api/legal/contracts/pending-review`
- GET `/api/legal/contracts/{id}`
- POST `/api/legal/contracts/{id}/review`
