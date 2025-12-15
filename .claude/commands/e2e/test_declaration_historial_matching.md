# E2E Test: Declaration-Historial Matching

## Prerequisites

1. **Servers Running**:
   - Backend: `cd backend && python -m uvicorn main:app --reload --port 8000`
   - Frontend: `cd frontend && npm run dev` (http://localhost:5173)

2. **Test User**: A user with `tesoreria` or `admin` role must be available

3. **Test Files**: Prepare two Excel files:
   - `test_historial.xlsx` - Historial de Pagos with columns: Cliente, Fecha de pago, Capital, Identificacion del cliente
   - `test_declarations.xlsx` - Declaration inventory with columns: Cliente, Fecha, Monto, Numero (declaration number)

## Test Steps

### Step 1: Navigate to Declaration Matching Page

1. Open browser to http://localhost:5173
2. Login with a user that has `tesoreria` or `admin` role
3. Navigate to `/treasury/declaration-matching`
4. **Expected**: Page displays with stepper showing 4 steps

### Step 2: Upload Historial de Pagos

1. On Step 1 "Cargar Archivos", drag and drop or select `test_historial.xlsx`
2. **Expected**:
   - File uploads and parses successfully
   - Shows validation status for required columns (cliente, fecha_pago, capital, identificacion_cliente)
   - Shows number of rows and payment groups
   - Session ID is created

### Step 3: Upload Declaration Inventory

1. After historial upload succeeds, drag and drop or select `test_declarations.xlsx`
2. **Expected**:
   - File uploads and parses successfully
   - Shows number of declarations loaded
   - "Siguiente" button becomes enabled

### Step 4: Configure Matching Parameters

1. Click "Siguiente" to go to Step 2
2. Adjust parameters:
   - Date tolerance: Slide to 7 days
   - Amount tolerance: Slide to $2.00
   - Customer match threshold: 85%
3. **Expected**: Configuration summary updates to reflect selections

### Step 5: Execute Matching Algorithm

1. Click "Ejecutar Coincidencias" button
2. **Expected**:
   - Loading indicator appears
   - After processing, page advances to Step 3
   - Statistics card shows match results:
     - Total payment groups
     - Matched groups
     - Unmatched groups
     - Match percentage
     - Average confidence

### Step 6: Review Match Results

1. In the results table:
   - Verify status chips show correctly (green for matched, red for unmatched)
   - Verify confidence percentages display with progress bars
   - Use status filter dropdown to filter by match status
   - Use search to find specific customers
2. **Expected**: All UI elements render correctly and filtering works

### Step 7: Perform Manual Override

1. Find an unmatched payment group in the table
2. Click the edit (pencil) icon
3. In the dialog:
   - Select a declaration from the autocomplete dropdown
   - Review the differences shown
   - Click "Confirmar Asignacion"
4. **Expected**:
   - Dialog closes
   - Table updates to show the group as matched
   - Statistics update to reflect the new match

### Step 8: Clear a Match

1. Find a matched payment group
2. Click the clear (X) icon
3. **Expected**: Group status changes to unmatched, statistics update

### Step 9: Download Enriched Excel

1. Click "Siguiente" to go to Step 4
2. Click "Descargar Excel Enriquecido"
3. **Expected**:
   - Excel file downloads
   - File contains original data with "Declaracion de Cambio Numero" and "DC Nombre" columns populated
   - Summary sheet shows statistics
   - Unmatched records sheet lists groups without matches

## Success Criteria

- [ ] Page loads without errors
- [ ] File uploads work with drag & drop and file selector
- [ ] Column validation shows correct status
- [ ] Payment groups are correctly aggregated
- [ ] Matching algorithm finds expected matches
- [ ] Statistics display accurately
- [ ] Manual override works correctly
- [ ] Clear match works correctly
- [ ] Downloaded Excel has correct data
- [ ] All Spanish labels display correctly

## Error Scenarios to Test

1. Upload non-Excel file → Should show error
2. Upload Excel missing required columns → Should show column validation errors
3. Upload with invalid data (bad dates, non-numeric capital) → Should show row-level errors
4. Session timeout → Should show "session expired" error

## Screenshot Locations

Take screenshots at these key points:
1. Initial page load with stepper
2. After historial upload with validation results
3. After declarations upload
4. Configuration form with adjusted parameters
5. Match results statistics card
6. Match results table with filters
7. Manual override dialog
8. Download step completion

## Notes

- Session expires after 30 minutes of inactivity
- Large files (>10MB) may take longer to process
- Matching confidence depends on data quality
