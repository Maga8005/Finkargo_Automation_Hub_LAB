# E2E Test: Broker Commission Calculation

Test the broker commission calculation API endpoints for the Alianzas module.

## User Story

As an alianzas team member,
I want to calculate broker commissions automatically based on business rules,
So that I can accurately determine how much to pay each broker for referrals and ongoing operations.

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173 (for auth token if using UI login)
- Test user account with `alianzas` or `admin` role
- At least one broker exists in the database with `porcentaje_apertura` and `porcentaje_operativa` configured
- `BANXICO_API_TOKEN` environment variable configured (for exchange rate lookups)

## Test Credentials

Use test account with alianzas role:
- Email: test-alianzas@finkargo.com (or your configured test account)
- Password: [configured test password]
- Expected Role: alianzas

## API Endpoints Under Test

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/alianzas/comisiones/calcular` | Calculate single commission (preview) |
| POST | `/api/alianzas/comisiones/calcular-lote` | Calculate batch with optional save |
| GET | `/api/alianzas/comisiones/{anio}/{mes}` | List commissions by period |
| GET | `/api/alianzas/comisiones/broker/{broker_id}` | List commissions by broker |
| PATCH | `/api/alianzas/comisiones/{id}/estado` | Update commission status |

## Test Steps

### Setup: Get Authentication Token

1. Navigate to http://localhost:5173
2. Log in with alianzas role test credentials
3. Open browser DevTools > Application > Local Storage
4. Copy the `access_token` from Supabase auth storage
5. Set the token for API requests: `Authorization: Bearer <token>`

**Alternative (API login):**
```bash
# Get token via API (if available)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test-alianzas@finkargo.com", "password": "your-password"}'
```

### Test Case 1: Calculate Apertura Commission Preview

1. **Action**: Call POST `/api/alianzas/comisiones/calcular` with apertura commission data
2. **Request Body**:
```json
{
  "broker_id": "<existing-broker-uuid>",
  "tipo_comision": "apertura",
  "cliente_nombre": "Test Client S.A. de C.V.",
  "cliente_nit": "RFC123456ABC",
  "linea_credito": 100000,
  "porcentaje_comision_cliente": 2.5,
  "cliente_pago_pct": 100,
  "periodo_mes": 12,
  "periodo_anio": 2025
}
```
3. **Verify** response status is 200
4. **Verify** response contains:
   - `broker_id` matches input
   - `tipo_comision` is "apertura"
   - `monto_broker_usd` is calculated (should be > 0)
   - `monto_broker_mxn` is calculated (should be > 0)
   - `tipo_cambio` is present (from Banxico)
   - `estado` is "calculado"
   - `id` is NOT present (preview mode)
5. Take a screenshot of the API response

### Test Case 2: Validate Minimum Payment Rule

1. **Action**: Call POST `/api/alianzas/comisiones/calcular` with cliente_pago_pct < 50
2. **Request Body**:
```json
{
  "broker_id": "<existing-broker-uuid>",
  "tipo_comision": "apertura",
  "linea_credito": 100000,
  "porcentaje_comision_cliente": 2.5,
  "cliente_pago_pct": 49
}
```
3. **Verify** response status is 400 Bad Request
4. **Verify** error message mentions "50%" minimum payment requirement
5. Take a screenshot of the error response

### Test Case 3: Calculate Operativa Commission Preview

1. **Action**: Call POST `/api/alianzas/comisiones/calcular` with operativa commission data
2. **Request Body**:
```json
{
  "broker_id": "<existing-broker-uuid>",
  "tipo_comision": "operativa",
  "cliente_nombre": "Test Operations Client",
  "operaciones_mes": 500000,
  "periodo_mes": 12,
  "periodo_anio": 2025
}
```
3. **Verify** response status is 200
4. **Verify** response contains:
   - `tipo_comision` is "operativa"
   - `operaciones_mes` matches input
   - `monto_broker_usd` is calculated correctly
   - `monto_broker_mxn` is calculated correctly
   - `tipo_cambio` is present
5. Take a screenshot of the API response

### Test Case 4: Batch Calculation Without Save

1. **Action**: Call POST `/api/alianzas/comisiones/calcular-lote` with multiple commissions
2. **Request Body**:
```json
{
  "comisiones": [
    {
      "broker_id": "<existing-broker-uuid>",
      "tipo_comision": "apertura",
      "cliente_nombre": "Client 1",
      "linea_credito": 50000,
      "porcentaje_comision_cliente": 3.0,
      "cliente_pago_pct": 100
    },
    {
      "broker_id": "<existing-broker-uuid>",
      "tipo_comision": "operativa",
      "cliente_nombre": "Client 2",
      "operaciones_mes": 200000
    }
  ],
  "guardar": false
}
```
3. **Verify** response status is 200
4. **Verify** response contains:
   - `comisiones` array with 2 items
   - `total_usd` is sum of individual monto_broker_usd values
   - `total_mxn` is sum of individual monto_broker_mxn values
   - `guardadas` is false
   - Neither commission has an `id` (not saved)
5. Take a screenshot of the batch response

### Test Case 5: Batch Calculation With Save

1. **Action**: Call POST `/api/alianzas/comisiones/calcular-lote` with `guardar: true`
2. **Request Body**:
```json
{
  "comisiones": [
    {
      "broker_id": "<existing-broker-uuid>",
      "tipo_comision": "apertura",
      "cliente_nombre": "Saved Client 1",
      "cliente_nit": "NIT-001",
      "linea_credito": 75000,
      "porcentaje_comision_cliente": 2.5,
      "cliente_pago_pct": 75,
      "periodo_mes": 12,
      "periodo_anio": 2025
    }
  ],
  "guardar": true
}
```
3. **Verify** response status is 200
4. **Verify** response contains:
   - `guardadas` is true
   - Each commission has an `id` (UUID)
   - Each commission has `created_at` timestamp
5. **Note**: Save the returned commission `id` for later tests
6. Take a screenshot of the saved commission response

### Test Case 6: List Commissions by Period

1. **Action**: Call GET `/api/alianzas/comisiones/2025/12`
2. **Verify** response status is 200
3. **Verify** response contains:
   - `comisiones` array (may include commission from Test Case 5)
   - `total` count
   - `periodo_mes` is 12
   - `periodo_anio` is 2025
4. Take a screenshot of the period listing

### Test Case 7: List Commissions by Broker

1. **Action**: Call GET `/api/alianzas/comisiones/broker/<broker-uuid>`
2. **Verify** response status is 200
3. **Verify** response is an array of commissions for that broker
4. Take a screenshot of the broker commissions

### Test Case 8: Update Commission Status

1. **Action**: Call PATCH `/api/alianzas/comisiones/<comision-id>/estado`
2. **Request Body**:
```json
{
  "estado": "aprobado"
}
```
3. **Verify** response status is 200
4. **Verify** response shows updated `estado` as "aprobado"
5. Take a screenshot of the status update response

### Test Case 9: Verify Banxico Exchange Rate Integration

1. **Action**: Call GET `/api/alianzas/tipo-cambio` to verify Banxico integration
2. **Verify** response status is 200
3. **Verify** response contains:
   - `tipo_cambio` (numeric value > 0)
   - `fecha` (ISO date string)
   - `fuente` contains "Banxico"
4. Take a screenshot of the exchange rate response

### Test Case 10: Invalid Broker ID

1. **Action**: Call POST `/api/alianzas/comisiones/calcular` with non-existent broker
2. **Request Body**:
```json
{
  "broker_id": "00000000-0000-0000-0000-000000000000",
  "tipo_comision": "operativa",
  "operaciones_mes": 100000
}
```
3. **Verify** response status is 400 Bad Request
4. **Verify** error message indicates broker not found
5. Take a screenshot of the error response

## Success Criteria

- All 10 test cases pass with expected responses
- Apertura commission formula: `monto_comision_cliente * porcentaje_broker / 100 * cliente_pago_pct / 100`
- Operativa commission formula: `operaciones_mes * porcentaje_operativa / 100`
- Exchange rates are fetched from Banxico API
- Business rule enforced: cliente_pago_pct >= 50% for apertura
- Batch calculations aggregate totals correctly
- Saved commissions have UUIDs and timestamps
- Status updates work for commission workflow

## Screenshots Required

1. Apertura commission preview response
2. Minimum payment validation error
3. Operativa commission preview response
4. Batch calculation response (without save)
5. Batch calculation response (with save)
6. Period listing response
7. Broker commissions listing
8. Status update response
9. Banxico exchange rate response
10. Invalid broker error response

## Error Scenarios to Note

- 400 Bad Request: Missing required fields, validation failures
- 401 Unauthorized: Missing or invalid auth token
- 403 Forbidden: User lacks alianzas role
- 404 Not Found: Commission ID not found (for status update)
- 500 Internal Server Error: Banxico API unavailable or other server errors

## Notes for Manual Testing

To manually test via curl:

```bash
# Set your auth token
TOKEN="your-jwt-token-here"

# Calculate apertura commission
curl -X POST http://localhost:8000/api/alianzas/comisiones/calcular \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "broker_id": "your-broker-uuid",
    "tipo_comision": "apertura",
    "linea_credito": 100000,
    "porcentaje_comision_cliente": 2.5,
    "cliente_pago_pct": 100
  }'

# List commissions for December 2025
curl -X GET "http://localhost:8000/api/alianzas/comisiones/2025/12" \
  -H "Authorization: Bearer $TOKEN"

# Get current exchange rate
curl -X GET http://localhost:8000/api/alianzas/tipo-cambio \
  -H "Authorization: Bearer $TOKEN"
```
