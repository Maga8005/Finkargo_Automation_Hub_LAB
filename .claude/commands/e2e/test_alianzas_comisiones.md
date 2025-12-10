# E2E Test: Alianzas Complete Workflow - Comisiones Brokers

This is a **comprehensive end-to-end test** that validates the complete Alianzas module workflow from broker creation through payment approval. It combines scenarios from individual E2E tests into a unified workflow test.

## User Story

As an Alianzas department user
I want to manage the complete broker commission lifecycle
So that I can track referral partners, calculate commissions, and process payments efficiently

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with `alianzas` or `admin` role
- `BANXICO_API_TOKEN` environment variable configured
- Database migration `migration_create_alianzas_tables.sql` has been applied

## Test Credentials

Use test account (configure in test environment):
- Email: test-alianzas@finkargo.com (or admin account)
- Password: [configured test password]
- Expected Role: alianzas or admin

## Test Data

### Master Broker Data
```json
{
  "nombre": "E2E Master Broker",
  "tipo_broker": "master_broker",
  "porcentaje_apertura": 60.00,
  "porcentaje_operativa": 0.10,
  "banco": "BBVA Mexico",
  "cuenta_bancaria": "012345678901234567",
  "rfc": "EMB010101ABC",
  "estado": "activo"
}
```

### Commission Calculation Data
**Apertura Commission:**
- linea_credito: $100,000 USD
- porcentaje_comision_cliente: 2.5%
- cliente_pago_pct: 100%
- Expected: monto_broker_usd = $1,500.00 (100000 * 0.025 * 0.60 * 1.0)

**Operativa Commission:**
- operaciones_mes: $500,000 USD
- Expected: monto_broker_usd = $500.00 (500000 * 0.001)

---

## Complete Workflow Test

### PHASE 1: Broker CRUD Flow

#### Step 1.1: Login and Navigate to Alianzas
1. Navigate to http://localhost:5173
2. Login with alianzas or admin role credentials
3. Wait for dashboard to load
4. **Verify** sidebar shows "Alianzas" department section
5. Click on "Alianzas" in the sidebar
6. Click on "Brokers" submenu item
7. **Verify** URL is `/alianzas/brokers`
8. **Verify** page title "Gestión de Brokers" is displayed
9. Take screenshot: `01_broker_list_initial.png`

#### Step 1.2: Create Master Broker
1. Click "Nuevo Broker" button
2. **Verify** dialog opens with form
3. Fill in the form:
   - Nombre: "E2E Master Broker"
   - Tipo de Broker: Select "Master Broker"
   - % Comisión Apertura: 60.00
   - % Comisión Operativa: 0.10
   - Banco: "BBVA Mexico"
   - Cuenta Bancaria: "012345678901234567"
   - RFC: "EMB010101ABC"
   - Estado: "Activo"
4. Take screenshot: `02_broker_form_filled.png`
5. Click "Crear Broker" button
6. **Verify** success message appears (snackbar/toast)
7. **Verify** broker appears in the data grid
8. Take screenshot: `03_broker_created.png`

#### Step 1.3: Edit Broker
1. Find "E2E Master Broker" row in the table
2. Click the Edit icon (pencil)
3. **Verify** dialog opens with pre-filled data
4. Update "Notas" field: "Created via E2E test - modified"
5. Click "Actualizar Broker" button
6. **Verify** success message appears
7. **Verify** broker shows in list with updated data
8. Take screenshot: `04_broker_updated.png`

#### Step 1.4: Verify Broker Search
1. Type "E2E Master" in the search field
2. Click "Buscar" button (or press Enter)
3. **Verify** only matching brokers are shown
4. Take screenshot: `05_broker_search_results.png`
5. Clear search field

---

### PHASE 2: Contract Extraction Flow (Optional)

**Note:** This phase requires a sample contract PDF file. Skip if not available.

#### Step 2.1: Access Contract Extraction
1. From broker list, click Edit on "E2E Master Broker"
2. Look for "Extracción de Contrato" section
3. **Verify** file upload field is visible

#### Step 2.2: Extract Contract Data
1. Upload a sample broker contract PDF
2. Select extraction method: "Extracción Estándar"
3. Click "Extraer Datos" button
4. **Verify** extracted fields populate the form (if found):
   - nombre_broker
   - porcentaje_comision_apertura
   - porcentaje_comision_operativa
   - fecha_contrato
   - cuenta_bancaria
   - banco
   - rfc_broker
5. Take screenshot: `06_contract_extraction.png`

---

### PHASE 3: Commission Calculation Flow

#### Step 3.1: Navigate to Commission Calculation
1. Click "Alianzas" > "Cálculo Mensual" in sidebar
2. **Verify** URL is `/alianzas/comisiones/calculo`
3. **Verify** page title "Cálculo de Comisiones - Brokers" is displayed
4. **Verify** period dropdowns show current month/year
5. Take screenshot: `07_comisiones_page_initial.png`

#### Step 3.2: Verify Exchange Rate Loaded
1. Look for "Tipo de Cambio" display section
2. **Verify** exchange rate value is displayed (e.g., "17.50")
3. **Verify** exchange rate date is displayed (from Banxico)
4. Take screenshot: `08_exchange_rate_loaded.png`

#### Step 3.3: Add Apertura Commission
1. Click "Agregar Comisión" button
2. **Verify** dialog opens with commission form
3. Fill in the form:
   - Broker: Select "E2E Master Broker"
   - Tipo de Comisión: Select "Apertura"
   - Nombre Cliente: "Test Client Apertura"
   - NIT/RFC Cliente: "TCA123456ABC"
   - Línea de Crédito (USD): 100000
   - % Comisión Cliente: 2.5
   - % Pago Cliente: 100
4. Take screenshot: `09_apertura_form_filled.png`
5. Click "Agregar" button
6. **Verify** commission appears in the table
7. **Verify** calculated values:
   - Monto Comisión Cliente: ~$2,500.00 USD
   - Monto Broker USD: ~$1,500.00 USD
   - Monto Broker MXN: calculated with exchange rate
8. Take screenshot: `10_apertura_commission_added.png`

#### Step 3.4: Add Operativa Commission
1. Click "Agregar Comisión" button
2. Fill in the form:
   - Broker: Select "E2E Master Broker"
   - Tipo de Comisión: Select "Operativa"
   - Nombre Cliente: "Test Client Operativa"
   - Operaciones del Mes (USD): 500000
3. Click "Agregar" button
4. **Verify** operativa commission appears in table
5. **Verify** calculated values:
   - Monto Broker USD: ~$500.00 USD
   - Monto Broker MXN: calculated with exchange rate
6. Take screenshot: `11_operativa_commission_added.png`

#### Step 3.5: Verify Commission Summary
1. Look for "Resumen por Broker" section
2. **Verify** "E2E Master Broker" shows aggregated totals:
   - Total Apertura USD: ~$1,500.00
   - Total Operativa USD: ~$500.00
   - Total USD: ~$2,000.00
   - Total MXN: calculated amount
3. Take screenshot: `12_commission_summary.png`

#### Step 3.6: Validate Minimum Payment Rule
1. Click "Agregar Comisión" button
2. Fill in apertura form with cliente_pago_pct: 49 (below 50% minimum)
3. Click "Agregar" button
4. **Verify** error message appears: "El cliente debe haber pagado al menos 50%"
5. Take screenshot: `13_validation_error.png`
6. Click "Cancelar" to close dialog

---

### PHASE 4: Export and Approval Flow

#### Step 4.1: Export Excel
1. On ComisionesCalculo page, click "Exportar Excel" button
2. **Verify** file download starts (or success message appears)
3. **Verify** downloaded file name contains period (e.g., "comisiones_2025_12.xlsx")
4. Take screenshot: `14_export_initiated.png`

#### Step 4.2: Approve Commissions
1. Click "Aprobar Comisiones" button
2. **Verify** confirmation dialog appears with:
   - Number of commissions to approve (should be 2)
   - Total USD amount (~$2,000.00)
   - Total MXN amount
   - Warning about creating payment records
3. Take screenshot: `15_approval_dialog.png`
4. Click "Confirmar" button
5. **Verify** success message: "Se aprobaron X comisiones y se crearon Y registros de pago"
6. **Verify** commission status changes to "Aprobado" in the table
7. Take screenshot: `16_commissions_approved.png`

#### Step 4.3: Verify Payment Record Created
1. Navigate to "Alianzas" > "Historial de Pagos" in sidebar
2. **Verify** URL is `/alianzas/pagos`
3. **Verify** page title "Historial de Pagos - Brokers" is displayed
4. **Verify** payment record exists for "E2E Master Broker" with:
   - Periodo: Current month/year
   - Total USD: ~$2,000.00
   - Estado: "Pendiente"
5. Take screenshot: `17_payment_history.png`

---

### PHASE 5: Cleanup (Optional)

#### Step 5.1: Cleanup Test Data
1. Navigate back to "Alianzas" > "Brokers"
2. Find "E2E Master Broker" row
3. Click Delete icon (trash)
4. **Verify** confirmation dialog appears
5. Click "Eliminar" button
6. **Verify** broker is removed or status changed to "Inactivo"
7. Take screenshot: `18_cleanup_complete.png`

---

## Success Criteria

### Broker Management
- [ ] Alianzas section visible in sidebar for alianzas/admin users
- [ ] Navigation to /alianzas/brokers works
- [ ] Can create new broker with all required fields
- [ ] Can edit existing broker information
- [ ] Search and filter functionality works
- [ ] Can soft-delete (deactivate) broker

### Commission Calculation
- [ ] Exchange rate loaded from Banxico on page load
- [ ] Can add apertura commission with correct calculation
- [ ] Can add operativa commission with correct calculation
- [ ] Minimum 50% payment validation works for apertura
- [ ] Commission summary shows correct totals per broker
- [ ] Period selection filters commissions correctly

### Export and Approval
- [ ] Excel export downloads file successfully
- [ ] Approval dialog shows correct summary
- [ ] Approval creates payment records
- [ ] Commission status updates to "Aprobado"
- [ ] Payment record appears in history

### Role Protection
- [ ] Non-alianzas/admin users cannot access /alianzas/* routes
- [ ] Unauthorized users see redirect or error message

---

## Expected Screenshots

| # | Filename | Description |
|---|----------|-------------|
| 1 | `01_broker_list_initial.png` | Initial broker list page |
| 2 | `02_broker_form_filled.png` | Broker creation form filled |
| 3 | `03_broker_created.png` | After broker created successfully |
| 4 | `04_broker_updated.png` | After broker edited |
| 5 | `05_broker_search_results.png` | Search results |
| 6 | `06_contract_extraction.png` | Contract extraction results (optional) |
| 7 | `07_comisiones_page_initial.png` | Commission calculation page |
| 8 | `08_exchange_rate_loaded.png` | Exchange rate display |
| 9 | `09_apertura_form_filled.png` | Apertura commission form |
| 10 | `10_apertura_commission_added.png` | Apertura commission in table |
| 11 | `11_operativa_commission_added.png` | Operativa commission in table |
| 12 | `12_commission_summary.png` | Summary by broker |
| 13 | `13_validation_error.png` | Minimum payment validation error |
| 14 | `14_export_initiated.png` | After Excel export |
| 15 | `15_approval_dialog.png` | Approval confirmation dialog |
| 16 | `16_commissions_approved.png` | Approved commissions |
| 17 | `17_payment_history.png` | Payment history with record |
| 18 | `18_cleanup_complete.png` | After cleanup (optional) |

---

## Error Scenarios to Test

| Scenario | Expected Behavior |
|----------|-------------------|
| Missing broker fields | Form validation prevents submission |
| Duplicate broker name | Error: "Ya existe un broker con el nombre..." |
| cliente_pago_pct < 50% | Error: "El cliente debe haber pagado al menos 50%" |
| Invalid broker ID | Error: "Broker no encontrado" |
| Banxico API unavailable | Graceful fallback or error message |
| Already approved commissions | Skip or show informative message |
| No commissions to approve | Message: "No hay comisiones pendientes" |
| Network errors | Toast/snackbar with error message |
| Unauthorized access | Redirect to login or 403 page |

---

## Commission Calculation Formulas Reference

### Apertura Commission
```
monto_comision_cliente = linea_credito * (porcentaje_comision_cliente / 100)
monto_broker_usd = monto_comision_cliente * (porcentaje_broker / 100) * (cliente_pago_pct / 100)
monto_broker_mxn = monto_broker_usd * tipo_cambio
```

### Operativa Commission
```
monto_broker_usd = operaciones_mes * (porcentaje_operativa / 100)
monto_broker_mxn = monto_broker_usd * tipo_cambio
```

### Example with Test Data
**Apertura:**
- linea_credito: $100,000
- porcentaje_comision_cliente: 2.5%
- porcentaje_broker (apertura): 60%
- cliente_pago_pct: 100%
- tipo_cambio: 17.50

```
monto_comision_cliente = 100000 * 0.025 = $2,500.00
monto_broker_usd = 2500 * 0.60 * 1.0 = $1,500.00
monto_broker_mxn = 1500 * 17.50 = $26,250.00
```

**Operativa:**
- operaciones_mes: $500,000
- porcentaje_broker (operativa): 0.10%
- tipo_cambio: 17.50

```
monto_broker_usd = 500000 * 0.001 = $500.00
monto_broker_mxn = 500 * 17.50 = $8,750.00
```

---

## API Endpoints Covered

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alianzas/brokers` | List all brokers |
| POST | `/api/alianzas/brokers` | Create broker |
| PUT | `/api/alianzas/brokers/{id}` | Update broker |
| DELETE | `/api/alianzas/brokers/{id}` | Soft delete broker |
| GET | `/api/alianzas/tipo-cambio` | Get current exchange rate |
| POST | `/api/alianzas/comisiones/calcular` | Calculate commission (preview) |
| POST | `/api/alianzas/comisiones/calcular-lote` | Batch calculate |
| GET | `/api/alianzas/comisiones/{anio}/{mes}` | List by period |
| GET | `/api/alianzas/comisiones/export` | Export Excel |
| POST | `/api/alianzas/comisiones/aprobar` | Approve commissions |
| GET | `/api/alianzas/pagos` | List payment history |

---

## Related E2E Tests

This comprehensive test covers scenarios from:
- `test_broker_crud.md` - Phase 1: Broker CRUD Flow
- `test_broker_contract_extraction.md` - Phase 2: Contract Extraction
- `test_broker_commission_calculation.md` - Phase 3: Commission Calculation
- `test_banxico_exchange_rate.md` - Phase 3.2: Exchange Rate
- `test_commission_export_approval.md` - Phase 4: Export and Approval

---

## Notes

- Test duration: ~15-20 minutes for complete workflow
- Screenshots should be saved to a test output directory
- Run with fresh database for consistent results
- Cleanup phase is optional but recommended for test repeatability
- If Banxico API is unavailable, skip exchange rate verification steps
