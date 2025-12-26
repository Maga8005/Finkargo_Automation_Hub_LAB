# E2E Test: Paga Local Colombia - K Credito (Aval PJ) Template Validation

Test that the K Credito (Aval PJ) contract uses the correct template instead of the default Activos template.

## User Story

As an Operations team member
I want to request a K Credito (Aval PJ) contract for Paga Local Colombia
So that the generated document uses the correct Paga Local template, not the Activos template

## Bug Being Validated

This test validates the fix for: **pl_co_credito_aval_pj using wrong template (FK COL - GM - Activos.docx)**

The system was incorrectly using the Activos template instead of `FK COL paga local - Fin. COP - K Credito (Aval PJ).docx`.

## Prerequisites

- User logged in with `operations` role
- Backend and frontend servers running
- At least one client exists in the database (searchable by NIT)
- Legal user credentials available for approval step

## Test Steps

### Part 1: Request K Credito (Aval PJ) Contract

1. **Login as Operations user** (or verify already logged in with operations role)
2. Navigate to `/operations/paga-local-colombia`
3. Take a screenshot of the Paga Local Colombia dashboard
4. **Verify** dashboard loads with tabs:
   - Contratos Cuenta Cliente
   - Documentos Operacion
   - Contratos Aprobados

5. Click on "Contratos Cuenta Cliente" tab (should be default)
6. Click on "Aval Persona Juridica" subtab
7. Take a screenshot showing the Aval PJ contract options
8. **Verify** two contract options are visible:
   - K Credito (Aval PJ)
   - K Mandato PJ

9. Click on "K Credito (Aval PJ)" card/button
10. **Verify** contract request form appears (FKPagaLocalCOContractRequest component)
11. Take a screenshot of the contract request form

12. **Fill out contract request form:**
    - Search for client by NIT (use any test client NIT)
    - **Verify** client search returns results
    - Select a client from results
    - **Verify** client information displays correctly

13. Take a screenshot of the filled form with selected client
14. Click "Solicitar K Credito (Aval PJ)" button
15. Wait for form submission to complete
16. **Verify** success message appears showing contract ID (format: PLCR-{YEAR}-{SEQUENCE})
17. Take a screenshot of the success message
18. Note the contract ID for Part 2

### Part 2: Verify Template in Legal Review

19. **Logout and login as Legal user**
20. Navigate to `/department/legal`
21. **Verify** Legal dashboard loads
22. Find the contract from Part 1 in the pending review queue
    - Look for the contract ID noted in step 18
    - Filter by contract type if available
23. Take a screenshot showing the contract in the review queue

24. Click on the contract to view details
25. **Download the DOCX file** using the download button
26. Take a screenshot of the download action

### Part 3: Validate Correct Template Was Used

27. **Open the downloaded DOCX file**
28. **Verify** the document content:
    - Should contain "PAGA LOCAL" or "Paga Local" text
    - Should contain "CONTRATO DE CREDITO" or credit contract specific text
    - Should contain "Aval" references for corporate guarantee
    - Should NOT contain "GARANTIA MOBILIARIA" (Activos-specific text)
    - Should NOT contain "GM - Activos" references

29. Take a screenshot of the document showing correct template content
30. **Verify** document header/footer matches Paga Local template format

## Success Criteria

- Paga Local Colombia dashboard loads correctly at `/operations/paga-local-colombia`
- Aval Persona Juridica subtab shows correct contract options
- K Credito (Aval PJ) contract can be requested successfully
- Contract ID follows Paga Local format: PLCR-{YEAR}-{SEQUENCE}
- Contract appears in Legal review queue with correct type
- Downloaded DOCX uses the Paga Local K Credito (Aval PJ) template
- Document does NOT use Activos template content
- 8+ screenshots captured documenting the workflow

## Screenshots Required

1. Paga Local Colombia dashboard
2. Aval Persona Juridica subtab with contract options
3. Empty contract request form
4. Filled form with selected client
5. Success message with contract ID
6. Legal review queue showing the contract
7. Download action/button
8. Downloaded document content showing correct template

## Template Identification

**Correct Template:** `FK COL paga local - Fin. COP - K Credito (Aval PJ).docx`
- Contains Paga Local specific language
- Contains credit contract with corporate guarantee terms

**Wrong Template (Bug):** `FK COL - GM - Activos.docx`
- Contains "Garantia Mobiliaria" language
- Contains asset-based financing terms
- Does NOT reference Paga Local product

## Notes

- If the document contains "Garantia Mobiliaria" or "GM - Activos", the bug is NOT fixed
- The contract_type in the database should be `pl_co_credito_aval_pj`
- Check backend logs for the message: "Generating document for contract type: pl_co_credito_aval_pj"
