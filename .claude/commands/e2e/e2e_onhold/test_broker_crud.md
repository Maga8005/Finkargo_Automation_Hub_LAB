# E2E Test: Broker CRUD Management

## User Story
As an alianzas team member, I want to manage broker partners through a complete CRUD interface so that I can maintain broker information, commission rates, contract details, and master/sub-broker relationships.

## Prerequisites
- Backend server running on http://localhost:8000
- Frontend dev server running on http://localhost:5173
- Test user with `alianzas` role OR `admin` role exists
- Database migration `migration_create_alianzas_tables.sql` has been applied

## Test Data
Use the following test data for creating brokers:

**Master Broker:**
- nombre: "Test Master Broker E2E"
- tipo_broker: "master_broker"
- porcentaje_apertura: 60.00
- porcentaje_operativa: 0.10
- banco: "BBVA Mexico"
- cuenta_bancaria: "0123456789"
- rfc: "TMB010101ABC"
- estado: "activo"

**Sub Broker:**
- nombre: "Test Sub Broker E2E"
- tipo_broker: "independiente"
- master_broker_id: (select the master broker created above)
- porcentaje_apertura: 30.00
- porcentaje_operativa: 0.05
- banco: "Santander"
- cuenta_bancaria: "9876543210"
- rfc: "TSB020202XYZ"
- estado: "activo"

## Test Steps

### Step 1: Navigate and Login
1. Navigate to http://localhost:5173
2. Login with alianzas or admin role user
3. Wait for dashboard to load

### Step 2: Navigate to Alianzas/Brokers
1. Click on "Alianzas" in the sidebar navigation
2. Verify URL changes to /alianzas/brokers
3. Verify "Gestión de Brokers" page title is visible
4. Verify empty state message is shown if no brokers exist
5. Take screenshot: `broker_list_initial.png`

### Step 3: Create Master Broker
1. Click "Nuevo Broker" button
2. Verify dialog opens with form
3. Fill in the form:
   - Nombre: "Test Master Broker E2E"
   - Tipo de Broker: Select "Master Broker"
   - % Comisión Apertura: 60.00
   - % Comisión Operativa: 0.10
   - Banco: "BBVA Mexico"
   - Cuenta Bancaria: "0123456789"
   - RFC: "TMB010101ABC"
   - Estado: "Activo"
4. Click "Crear Broker" button
5. Verify success message appears
6. Verify broker appears in the list
7. Take screenshot: `broker_created_master.png`

### Step 4: Create Sub Broker
1. Click "Nuevo Broker" button
2. Fill in the form:
   - Nombre: "Test Sub Broker E2E"
   - Tipo de Broker: Select "Independiente"
   - Master Broker: Select "Test Master Broker E2E"
   - % Comisión Apertura: 30.00
   - % Comisión Operativa: 0.05
   - Banco: "Santander"
   - Cuenta Bancaria: "9876543210"
   - RFC: "TSB020202XYZ"
   - Estado: "Activo"
3. Click "Crear Broker" button
4. Verify success message appears
5. Verify both brokers appear in the list
6. Take screenshot: `broker_created_sub.png`

### Step 5: Search and Filter
1. Type "Master" in the search box
2. Click "Buscar" button
3. Verify only master broker is shown
4. Clear search
5. Select "Independiente" from Tipo filter
6. Click "Buscar"
7. Verify only sub broker is shown
8. Clear filters
9. Take screenshot: `broker_filtered.png`

### Step 6: Edit Broker
1. Click Edit icon on "Test Sub Broker E2E" row
2. Verify dialog opens with broker data pre-filled
3. Update "Notas" field: "Updated via E2E test"
4. Click "Actualizar Broker" button
5. Verify success message appears
6. Take screenshot: `broker_updated.png`

### Step 7: Delete Broker
1. Click Delete icon on "Test Sub Broker E2E" row
2. Verify confirmation dialog appears
3. Click "Eliminar" button
4. Verify success message appears
5. Verify broker status changes to "Inactivo" or is removed from list
6. Take screenshot: `broker_deleted.png`

### Step 8: Cleanup
1. Delete "Test Master Broker E2E" as well (follow Step 7)
2. Verify both test brokers are removed/inactive

## Success Criteria
- [ ] Alianzas section appears in sidebar for alianzas/admin users
- [ ] Navigation to /alianzas/brokers works correctly
- [ ] Can list all brokers with filtering by estado and tipo_broker
- [ ] Can create a new broker with all fields populated
- [ ] Master broker dropdown only shows brokers with tipo_broker='master_broker'
- [ ] Can edit an existing broker's information
- [ ] Can soft-delete (deactivate) a broker
- [ ] Search works by nombre
- [ ] Form validation prevents invalid data submission
- [ ] Error messages display appropriately
- [ ] Success messages confirm operations completed
- [ ] Role protection works (non-alianzas/admin users cannot access)

## Expected Screenshots
- `broker_list_initial.png` - Initial brokers page state
- `broker_created_master.png` - After creating master broker
- `broker_created_sub.png` - After creating sub broker
- `broker_filtered.png` - After applying filters
- `broker_updated.png` - After editing broker
- `broker_deleted.png` - After deleting broker

## Notes
- If using admin role, the sidebar should show Alianzas department
- If using alianzas role, only Alianzas department should be visible
- Commission percentages should be displayed with 2 decimal places
- Estado should be displayed with color-coded Chips (green=activo, red=inactivo, yellow=pendiente)
