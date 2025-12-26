# E2E Test: Paga Local Colombia Sin Aval Contracts

## Test Overview
End-to-end test for the Paga Local Colombia "Sin Aval" contract generation workflow, validating both K° Crédito (No Aval) and K° Mandato contract types from request to approval.

## Prerequisites
- Backend server running on http://localhost:8000
- Frontend server running on http://localhost:5173
- Test user with `operations` role exists in database
- Test user with `legal` role exists in database
- Test client with NIT `900123456` exists in database
- Database migration executed for Paga Local templates

## Test Credentials
```
Operations User:
  Email: operations@test.com
  Password: test123

Legal User:
  Email: legal@test.com
  Password: test123
```

## Test Client Data
```
NIT: 900123456
Name: Test Client SA
Representative: Juan Perez
ID: 1234567890
City: Bogotá
```

## Test Steps

### Part 1: K° Crédito (No Aval) Contract Request

#### Step 1: Login as Operations User
1. Navigate to http://localhost:5173
2. Enter operations user credentials
3. Click "Iniciar Sesión"
4. **Expected**: Dashboard loads successfully

#### Step 2: Navigate to Paga Local Colombia
1. Click "Operaciones" in sidebar
2. Click "Paga Local Colombia" submenu item
3. **Expected**: Paga Local Colombia page loads with tabs

#### Step 3: Access Sin Aval Contract Section
1. Click "Contratos Cuenta Cliente" tab
2. Click "Sin Aval" subtab
3. **Expected**: Two contract cards displayed:
   - "K° Crédito (No Aval)"
   - "K° Mandato No Aval"

#### Step 4: Request K° Crédito (No Aval) Contract
1. Click "K° Crédito (No Aval)" card
2. Dialog opens with contract request form
3. Enter NIT: `900123456` in search field
4. Click "Buscar Cliente"
5. **Expected**: Client data populates in form
6. Review client data displayed
7. Click "Generar Contrato" button
8. **Expected**:
   - Success message displays
   - Contract ID generated (format varies)
   - Dialog closes
   - Contract appears in queue

#### Step 5: Verify Contract Created
1. Check browser console for no errors
2. Note the contract ID from success message
3. **Expected**: Status shows as "under_review"

### Part 2: K° Mandato (No Aval) Contract Request

#### Step 6: Request K° Mandato Contract
1. Return to "Sin Aval" subtab if navigated away
2. Click "K° Mandato No Aval" card
3. Dialog opens with contract request form
4. Enter NIT: `900123456` in search field
5. Click "Buscar Cliente"
6. Client data populates
7. Click "Generar Contrato" button
8. **Expected**:
   - Success message displays
   - Contract ID generated
   - Dialog closes

### Part 3: Legal Review and Approval

#### Step 7: Logout and Login as Legal User
1. Click user menu in top navigation
2. Click "Cerrar Sesión"
3. Return to login page
4. Enter legal user credentials
5. Click "Iniciar Sesión"
6. **Expected**: Dashboard loads for legal user

#### Step 8: Navigate to Pending Review Queue
1. Click "Legal" in sidebar
2. Click "Pending Review" submenu item
3. **Expected**: Pending contracts list displays
4. Verify both Paga Local contracts appear in queue

#### Step 9: Download and Review K° Crédito DOCX
1. Find K° Crédito (No Aval) contract in list
2. Click "Download DOCX" button
3. Open downloaded file in Microsoft Word or LibreOffice
4. **Expected**:
   - File opens without corruption
   - All placeholders replaced with actual data:
     - `[NOMBRE DEL CLIENTE]` → Test Client SA
     - `[NIT]` → 900123456
     - `[representante legal del Cliente]` → Juan Perez
     - `[número de documento del representante legal]` → 1234567890
     - `[nombre de la ciudad]` → Bogotá
     - Date placeholders filled
   - No `[...]` brackets remain
   - Formatting preserved

#### Step 10: Approve K° Crédito Contract
1. Close Word document
2. Return to Pending Review page
3. Find K° Crédito contract
4. Click "Approve" button
5. Confirmation dialog appears
6. Click "Confirm"
7. **Expected**:
   - Success message displays
   - Contract disappears from pending queue
   - PDF generated and stored

#### Step 11: Verify K° Mandato Contract
1. Find K° Mandato contract in pending queue
2. Click "Download DOCX" button
3. Open downloaded file
4. **Expected**:
   - All placeholders replaced correctly:
     - `[NOMBRE DEL CLIENTE]` → Test Client SA
     - `[NIT]` → 900123456
     - `[nombre del representante legal]` → Juan Perez
     - `[tipo de identificación]` → CC
     - `[monto a transferir en números]` → formatted currency
     - `[monto a transferir en letras]` → Spanish words
     - `[consecutivo correspondiente]` → contract ID
     - Date placeholders filled
   - No brackets remain
   - Formatting intact

#### Step 12: Approve K° Mandato Contract
1. Close Word document
2. Return to Pending Review page
3. Find K° Mandato contract
4. Click "Approve" button
5. Confirm approval
6. **Expected**: Contract approved successfully

### Part 4: Verify Approved Contracts in Operations

#### Step 13: Logout and Login as Operations User
1. Click user menu
2. Logout
3. Login with operations credentials
4. **Expected**: Operations dashboard loads

#### Step 14: Navigate to Approved Contracts
1. Click "Operaciones" in sidebar
2. Click "Paga Local Colombia"
3. Click "Contratos Aprobados" tab
4. **Expected**: Approved contracts list displays

#### Step 15: Verify and Download Approved PDFs
1. Find both approved Paga Local contracts
2. For each contract:
   - Click "Download PDF" button
   - Open downloaded PDF
   - Verify content matches DOCX
   - Verify formatting preserved
3. **Expected**: Both PDFs download and open successfully

## Success Criteria
- [ ] K° Crédito (No Aval) contract request succeeds
- [ ] K° Mandato contract request succeeds
- [ ] Both contracts created with status "under_review"
- [ ] Contract IDs generated correctly
- [ ] DOCX files download without errors
- [ ] All placeholders replaced in K° Crédito template
- [ ] All placeholders replaced in K° Mandato template
- [ ] No bracketed placeholders remain
- [ ] Formatting preserved in both templates
- [ ] Both contracts approve successfully
- [ ] PDFs generated and stored
- [ ] Approved PDFs appear in Operations approved list
- [ ] No console errors throughout workflow
- [ ] No backend errors in logs

## Screenshots to Capture
1. Paga Local Colombia "Sin Aval" subtab with contract cards
2. K° Crédito contract request form with populated client data
3. Success message after K° Crédito contract generation
4. K° Mandato contract request form
5. Legal Pending Review queue with both contracts
6. Operations Approved Contracts list with both PDFs

## Error Scenarios to Test (Optional)

### Missing Template File
1. Temporarily rename template file
2. Request contract
3. **Expected**: Clear error message indicating missing template

### Invalid NIT
1. Enter non-existent NIT
2. **Expected**: "Client not found" error message

### Database Template Not Found
1. Set template record to `active=false` in database
2. Request contract
3. **Expected**: "No active template found" error

## Performance Benchmarks
- Contract generation: < 5 seconds
- DOCX download: < 2 seconds
- PDF conversion: < 5 seconds
- Total workflow: < 2 minutes

## Cleanup After Test
1. Delete test contracts from database (optional)
2. Reset template records if modified
3. Clear downloaded files from local machine

## Notes
- This test validates the complete workflow for 2 of 9 Paga Local contract types
- Remaining 7 contract types will need similar tests when implemented
- LibreOffice must be installed for PDF conversion
- Test can be automated using Playwright for CI/CD pipeline
