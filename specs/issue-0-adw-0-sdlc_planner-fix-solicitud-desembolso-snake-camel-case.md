# Bug: Solicitud de Desembolso Black Screen - Snake/Camel Case Field Mismatch

## Bug Description
When extracting data from a Cotización PDF in the Solicitud de Desembolso form, the application shows a black screen with a JavaScript error. The console shows:

```
Uncaught TypeError: Cannot read properties of undefined (reading 'length')
at FKSolicitudDesembolsoRequest (FKSolicitudDesembolsoRequest.tsx:401:71)
```

The expected behavior is that after clicking "Extraer Datos del PDF", the extracted data should populate the form fields and show "Datos extraídos exitosamente: X ítems encontrados".

## Problem Statement
There is a **naming convention mismatch** between the backend API response and the frontend TypeScript interface:

| Backend (snake_case) | Frontend (camelCase) |
|---------------------|---------------------|
| `numero_cotizacion` | `numeroCotizacion` |
| `fecha_cotizacion` | `fechaCotizacion` |
| `fecha_contrato_credito` | `fechaContratCredito` |
| `representante_legal` | `representanteLegal` |
| `tipo_id_representante` | `tipoIdRepresentante` |
| `numero_id_representante` | `numeroIdRepresentante` |
| `anexo_items` | `anexoItems` |
| `monto_total` | `montoTotal` |
| `numero_instrumento` (in AnexoItem) | `numeroInstrumento` |

When the API returns `anexo_items`, the frontend tries to access `anexoItems` which is `undefined`, causing the crash at line 401.

## Solution Statement
Convert the frontend TypeScript interface and component to use **snake_case** field names to match the backend API response. This is the minimal change approach that:
1. Aligns frontend types with the actual API response format
2. Avoids adding complexity with field transformation layers
3. Follows the pattern already used in `SolicitudDesembolsoRequest` (which already uses snake_case)

The fix requires updating:
1. `CotizacionData` interface to use snake_case field names
2. `AnexoItem` interface to use snake_case for `numero_instrumento`
3. `FKSolicitudDesembolsoRequest.tsx` to access fields with snake_case names

## Steps to Reproduce
1. Login as an Operations user
2. Navigate to `/operations/contratos-paga-local-colombia`
3. Click on the "Solicitud de Desembolso" tab
4. Search and select a client
5. Upload a valid Cotización PDF file
6. Click "Extraer Datos del PDF" button
7. **Result**: Black screen with console error `Cannot read properties of undefined (reading 'length')`
8. **Expected**: Form fields populated with extracted data

## Root Cause Analysis
The root cause is a naming convention mismatch:

1. **Backend** (`legal_dtos.py`): Pydantic models use Python's standard snake_case naming:
   - `CotizacionData.numero_cotizacion`, `anexo_items`, `monto_total`
   - `AnexoItem.numero_instrumento`

2. **FastAPI serialization**: By default, Pydantic serializes to JSON using the Python field names (snake_case)

3. **Frontend** (`types/legal.ts`): TypeScript interfaces incorrectly expect camelCase:
   - `CotizacionData.numeroCotizacion`, `anexoItems`, `montoTotal`
   - `AnexoItem.numeroInstrumento`

4. **Runtime crash**: When `operationsService.parseCotizacionPdf()` returns data with `anexo_items`, the component accesses `extractedData.anexoItems` which is `undefined`, and calling `.length` on `undefined` throws a TypeError.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [x] Frontend: types

## Relevant Files
Use these files to fix the bug:

**Primary files to modify:**

- `frontend/src/types/legal.ts` - Contains `CotizacionData` and `AnexoItem` interfaces that need field names changed from camelCase to snake_case to match the backend API response.

- `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx` - The form component that crashes. All references to extracted data fields need to be updated from camelCase (`extractedData.anexoItems`, `extractedData.numeroCotizacion`, etc.) to snake_case (`extractedData.anexo_items`, `extractedData.numero_cotizacion`, etc.).

**Reference files (read-only):**

- `backend/src/interface/legal_dtos.py` - Contains the authoritative Pydantic models (`CotizacionData`, `AnexoItem`) that define the actual API response format. The frontend must match these field names.

- `frontend/src/services/operationsService.ts` - Contains `parseCotizacionPdf()` and `generateSolicitudDesembolso()` methods. No changes needed, but useful to understand the data flow.

**E2E Test References:**

- `.claude/commands/test_e2e.md` - Instructions for creating and running E2E tests
- `.claude/commands/e2e/test_login.md` - Example E2E test structure
- `.claude/commands/e2e/test_contract_request.md` - Similar contract request E2E test pattern

### New Files
- `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` - E2E test to validate the PDF upload and data extraction workflow works correctly after the fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Task 1: Update TypeScript Interfaces to Use Snake Case
- Open `frontend/src/types/legal.ts`
- Update `AnexoItem` interface:
  - Change `numeroInstrumento` to `numero_instrumento`
- Update `CotizacionData` interface:
  - Change `numeroCotizacion` to `numero_cotizacion`
  - Change `fechaCotizacion` to `fecha_cotizacion`
  - Change `fechaContratCredito` to `fecha_contrato_credito`
  - Change `representanteLegal` to `representante_legal`
  - Change `tipoIdRepresentante` to `tipo_id_representante`
  - Change `numeroIdRepresentante` to `numero_id_representante`
  - Change `anexoItems` to `anexo_items`
  - Change `montoTotal` to `monto_total`
- Note: `SolicitudDesembolsoRequest` already uses snake_case, no changes needed

### Task 2: Update FKSolicitudDesembolsoRequest Component Field Accesses
- Open `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx`
- Update all references to `extractedData` fields:
  - `extractedData.anexoItems` → `extractedData.anexo_items`
  - `extractedData.numeroCotizacion` → `extractedData.numero_cotizacion`
  - `extractedData.fechaContratCredito` → `extractedData.fecha_contrato_credito`
- Update all references to `AnexoItem` fields in state and handlers:
  - `item.numeroInstrumento` → `item.numero_instrumento`
  - `handleAnexoItemChange(index, 'numeroInstrumento', ...)` → `handleAnexoItemChange(index, 'numero_instrumento', ...)`
- Update the initial empty AnexoItem object:
  - `{ acreedor: '', numeroInstrumento: '', monto: 0 }` → `{ acreedor: '', numero_instrumento: '', monto: 0 }`

### Task 3: Run TypeScript Type Check
- Execute: `cd frontend && npx tsc --noEmit`
- Verify zero TypeScript errors
- If errors found, fix any remaining field name mismatches

### Task 4: Run Frontend Linting
- Execute: `cd frontend && npm run lint`
- Fix any linting errors that arise

### Task 5: Run Frontend Build
- Execute: `cd frontend && npm run build`
- Verify production build completes without errors

### Task 6: Create E2E Test File
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` to understand E2E test structure
- Create `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` with the following test:
  - **User Story**: As an Operations user, I want to upload a Cotización PDF and extract data for Solicitud de Desembolso
  - **Prerequisites**: User logged in with operations role, backend and frontend servers running
  - **Test Steps**:
    1. Login as operations user
    2. Navigate to `/operations/contratos-paga-local-colombia`
    3. Click "Solicitud de Desembolso" tab
    4. Screenshot: Empty form
    5. Search for client by NIT (e.g., 900436389)
    6. Select client from results
    7. Upload a test Cotización PDF
    8. Click "Extraer Datos del PDF" button
    9. Wait for extraction to complete
    10. Screenshot: Form with extracted data populated
    11. Verify numero cotizacion field is populated
    12. Verify Anexo I table has items
    13. Verify monto total is displayed
  - **Success Criteria**:
    - No black screen or console errors
    - Extracted data populates form fields
    - Anexo I table displays extracted items
    - "Datos extraídos exitosamente" message appears

### Task 7: Run Validation Commands
- Execute all validation commands listed below to confirm the bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Frontend type checking - must pass with zero errors
cd frontend && npx tsc --noEmit

# Frontend linting - must pass with zero ESLint errors
cd frontend && npm run lint

# Frontend production build - must complete successfully
cd frontend && npm run build

# Backend tests - ensure no regressions
cd backend && python -m pytest

# Backend linting - must pass
cd backend && ruff check src/
```

**Manual verification steps:**
1. Start development servers: `./scripts/start-dev.sh`
2. Login as operations user
3. Navigate to Solicitud de Desembolso tab
4. Upload a Cotización PDF and click "Extraer Datos del PDF"
5. **Verify**: Form populates with extracted data (no black screen)
6. **Verify**: Anexo I table shows extracted items
7. **Verify**: Console has no TypeError errors

**E2E Test validation:**
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` to validate this functionality works end-to-end.

## Notes

### Technical Context
- The bug was introduced when the `FKSolicitudDesembolsoRequest` component and `CotizacionData` type were created with camelCase field names, but the backend Pydantic model uses Python's standard snake_case naming.
- FastAPI/Pydantic by default serializes using the Python field names, not aliases.
- This is a common issue when frontend and backend are developed separately without a shared API contract.

### Alternative Solutions Considered
1. **Add Pydantic aliases (backend change)**: Configure `CotizacionData` to serialize with camelCase using `alias` and `by_alias=True`. Rejected because it adds complexity and the existing `SolicitudDesembolsoRequest` already uses snake_case.
2. **Add transformation layer in operationsService (frontend change)**: Transform API response from snake_case to camelCase. Rejected because it adds unnecessary complexity and maintenance burden.
3. **Chosen solution**: Update frontend types and component to use snake_case. This is the minimal change that aligns with the existing pattern in `SolicitudDesembolsoRequest`.

### Files Changed Summary
- `frontend/src/types/legal.ts` - 2 interfaces updated
- `frontend/src/components/forms/FKSolicitudDesembolsoRequest.tsx` - Multiple field references updated
- `.claude/commands/e2e/test_solicitud_desembolso_pdf_upload.md` - New E2E test file
