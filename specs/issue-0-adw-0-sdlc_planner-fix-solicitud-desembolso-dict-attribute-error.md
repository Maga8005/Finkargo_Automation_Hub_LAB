# Bug: Solicitud de Desembolso - 'dict' object has no attribute 'nit' error

## Bug Description
When a user completes the Solicitud de Desembolso form (selects a customer, uploads a Cotización PDF, extracts data, and clicks submit), the backend returns a 500 Internal Server Error with the message: `'dict' object has no attribute 'nit'`.

**Symptoms:**
- Frontend displays error: "Error al generar solicitud: 'dict' object has no attribute 'nit'"
- Backend returns HTTP 500 Internal Server Error
- Console shows POST request to `/api/operations/contracts/solicitud-desembolso/generate` fails

**Expected behavior:**
- Contract should be generated successfully
- User should see success message with contract ID
- Contract should appear in legal review queue with status "under_review"

**Actual behavior:**
- Server error occurs during contract generation
- AttributeError is raised when accessing client data

## Problem Statement
The `generate_solicitud_desembolso` endpoint in `operations_routes.py` attempts to access client data using attribute notation (`client.nit`, `client.nombre_importador`, etc.) but the `ClientRepository.get_by_nit()` method returns a dictionary (`dict`), not an object with attributes.

## Solution Statement
Change the client data access pattern in the `generate_solicitud_desembolso` function from attribute notation to dictionary key access notation. Replace `client.nit` with `client['nit']`, `client.nombre_importador` with `client['nombre_importador']`, etc.

## Steps to Reproduce
1. Log in as an Operations user
2. Navigate to Paga Local Colombia > Solicitud de Desembolso
3. Search for and select a client by NIT
4. Upload a Cotización PDF document
5. Click "Extraer Datos del PDF" button
6. Verify extracted data is populated in the form
7. Click "Solicitar Documento" button
8. Observe the error: "Error al generar solicitud: 'dict' object has no attribute 'nit'"

## Root Cause Analysis
In `backend/src/adapter/rest/operations_routes.py` lines 277-284, the code accesses client data using object attribute notation:

```python
data_snapshot = {
    "nit": client.nit,  # ❌ AttributeError
    "nombre_importador": client.nombre_importador,  # ❌ AttributeError
    "representante_legal": client.representante_legal,  # ❌ AttributeError
    ...
}
```

However, `ClientRepository.get_by_nit()` (in `client_repository.py` line 43-59) returns a dictionary:

```python
async def get_by_nit(self, nit: str) -> Optional[dict]:
    """Returns dict, not object"""
    response = self.db.table('clients').select('*').eq('nit', nit).eq('is_active', True).execute()
    return response.data[0] if response.data else None  # Returns dict
```

The inconsistency between the return type (`dict`) and the access pattern (object attributes) causes the `AttributeError`.

## Affected Layer
- [x] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [ ] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `backend/src/adapter/rest/operations_routes.py` - **Primary file to fix**. Contains the `generate_solicitud_desembolso` endpoint where the bug occurs on lines 277-284. The client data access pattern needs to be changed from attribute notation to dictionary key access.
- `backend/src/repositorio/client_repository.py` - Reference file to understand the return type of `get_by_nit()` method which returns `Optional[dict]`, not an object.
- `backend/src/interface/legal_dtos.py` - Reference file for DTO definitions used in the endpoint.
- `.claude/commands/test_e2e.md` - Read this to understand how to create E2E test files.
- `.claude/commands/e2e/test_login.md` - Read this as an example of E2E test format.

### New Files
- `.claude/commands/e2e/test_solicitud_desembolso_generation.md` - E2E test file to validate the bug fix works correctly.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Fix client data access pattern in operations_routes.py
- Open `backend/src/adapter/rest/operations_routes.py`
- Locate the `generate_solicitud_desembolso` function (starts at line 233)
- Change all client data access from attribute notation to dictionary key access in lines 277-284:
  - Change `client.nit` to `client['nit']`
  - Change `client.nombre_importador` to `client['nombre_importador']`
  - Change `client.representante_legal` to `client['representante_legal']`
  - Change `client.cedula_representante` to `client['cedula_representante']`
  - Change `client.ciudad_domicilio` to `client['ciudad_domicilio']`
  - Change `client.cupo_plataforma` to `client['cupo_plataforma']`
  - Change `client.direccion_comercial` to `client.get('direccion_comercial')` (use `.get()` for optional fields)
  - Change `client.tipo_identificacion_representante` to `client.get('tipo_identificacion_representante')` (use `.get()` for optional fields)

### 2. Verify consistent access patterns in the same file
- Review other parts of `operations_routes.py` to ensure no other functions have the same issue
- Ensure all `client` dictionary accesses use dictionary key notation throughout the file

### 3. Create E2E test file for Solicitud de Desembolso generation
- Read `.claude/commands/test_e2e.md` to understand E2E test execution format
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/e2e/test_contract_request.md` for E2E test file format examples
- Create new E2E test file at `.claude/commands/e2e/test_solicitud_desembolso_generation.md` that validates:
  1. User can log in as Operations role
  2. Navigate to Solicitud de Desembolso form
  3. Search and select a client
  4. Upload Cotización PDF
  5. Extract data from PDF
  6. Submit form to generate contract
  7. **Verify** success message appears (proves bug is fixed)
  8. **Verify** contract ID is displayed
  9. Take screenshots at key steps

### 4. Run Validation Commands
- Execute all validation commands to ensure the bug is fixed with zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd backend && python -m pytest tests/ -v` - Run backend tests to validate bug fix with zero regressions
- `cd backend && ruff check src/` - Run backend linting to ensure code quality
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_solicitud_desembolso_generation.md` E2E test file to validate this functionality works

## Notes
- This is a simple fix that only requires changing the data access pattern in one file
- No new libraries are required
- The fix is minimal and surgical - only changing the lines that cause the AttributeError
- The repository layer correctly returns `dict` types, so the fix is in the adapter/rest layer where the data is accessed incorrectly
- Use `.get()` method for optional fields to avoid KeyError if the field doesn't exist
