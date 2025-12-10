# E2E Test: Commission Export and Approval Flow

Test the commission Excel export and approval workflow for the Alianzas module.

## User Story

As an Alianzas department user
I want to export commissions to Excel and approve them for payment
So that I can generate reports and create broker payment records for the current period

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- Test user account with `alianzas` or `admin` role
- At least one active broker exists in the system

## Test Credentials

Use test account (configure in test environment):
- Email: test-alianzas@finkargo.com (or admin account)
- Password: [configured test password]
- Expected Role: alianzas or admin

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. Log in with test credentials (if not already authenticated)
3. Navigate to Alianzas > Cálculo Mensual in sidebar
4. **Verify** page title "Cálculo de Comisiones - Brokers" is displayed
5. Take a screenshot of the ComisionesCalculo page

6. Select current month and year in the period dropdowns
7. **Verify** exchange rate is loaded and displayed
8. Click "Agregar Comisión" button
9. **Verify** commission form dialog opens

10. Fill in the commission form:
    - Select a broker from the dropdown
    - Select "Apertura" as commission type
    - Enter cliente_nombre: "Test Client"
    - Enter linea_credito: "100000"
    - Enter porcentaje_comision_cliente: "2"
    - Enter cliente_pago_pct: "100"
11. Take a screenshot of the filled form
12. Click "Agregar" button in the dialog
13. **Verify** commission appears in the table

14. Click "Exportar Excel" button
15. **Verify** Excel file download starts (or success message appears)
16. Take a screenshot after export action

17. Click "Aprobar Comisiones" button
18. **Verify** confirmation dialog appears with:
    - Number of commissions to approve
    - Total USD amount
    - Total MXN amount
19. Take a screenshot of the confirmation dialog

20. Click "Confirmar" button in the dialog
21. **Verify** success message appears indicating commissions were approved
22. **Verify** commission status changes to "Aprobado" in the table
23. Take a screenshot of the approved commissions

24. Navigate to Alianzas > Historial de Pagos in sidebar
25. **Verify** page title "Historial de Pagos - Brokers" is displayed
26. **Verify** payment record appears in the table for the approved broker
27. Take a screenshot of the PagosHistorial page with the payment record

## Success Criteria

- ComisionesCalculo page loads without errors
- Commission can be added via form
- "Exportar Excel" button triggers download
- Approval dialog shows correct summary
- Approval creates payment records
- Payment appears in PagosHistorial page
- 7 screenshots are captured:
  1. Initial ComisionesCalculo page
  2. Filled commission form
  3. After export action
  4. Approval confirmation dialog
  5. Approved commissions in table
  6. PagosHistorial page with payment record
  7. (Optional) Error states if any

## Error Scenarios to Note

- No brokers available → Show appropriate message
- Exchange rate not available → Disable form submit
- Approval with no commissions → Show warning
- Already approved commissions → Skip or show message
- Network errors → Show error toast

## Expected API Calls

- `GET /api/alianzas/brokers` - Load brokers dropdown
- `GET /api/alianzas/tipo-cambio` - Get exchange rate
- `POST /api/alianzas/comisiones/calcular` - Preview commission
- `GET /api/alianzas/comisiones/export` - Export Excel (streaming response)
- `POST /api/alianzas/comisiones/aprobar` - Approve commissions
- `GET /api/alianzas/pagos` - List payment history
