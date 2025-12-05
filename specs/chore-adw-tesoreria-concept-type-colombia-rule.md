# Chore: Update Colombia concept_type Rules for Tesorería Template Output

## Chore Description

In the Tesorería department, for the Colombia template output, the `concept_type` field is currently following a different rule than required. The current implementation creates separate output rows for each individual concept column (CAPITAL, 4X1000, FONDO_GARANTIAS, etc.).

The new requirement is to consolidate certain concepts into broader categories:

| Output concept_type | Source Columns with Value |
|---------------------|---------------------------|
| `CAPITAL` | Capital column has a value |
| `COSTOS FIJOS` | ANY of: 4X1000 (Q), Fondo de garantía (R), IVA Fondo de Garantía (S), Servicio de Originación (U), Servicios de Giro + IVA (X), Costos Adicionales (Z) |
| `SEGUROS` | Seguro + IVA column (T) |
| `INTERESES` | Intereses Corrientes column (AA) |
| `MORATORIOS` | ANY of: Intereses de mora PAR 60 columns + PAR 61 columns (AB to AE) |

The key change is that instead of creating separate output rows for 4X1000, FONDO_GARANTIAS, IVA_FONDO_GARANTIAS, SERVICIO_ORIGINACION, SERVICIO_GIRO, and COSTOS_ADICIONALES, they should all be **summed together** into a single `COSTOS FIJOS` concept row.

## Relevant Files
Use these files to resolve the chore:

- **`backend/src/core/servicios/payment_template_service.py`** - Main service that processes rows and generates concept types. Contains the `_process_concepts` method that determines which concepts to output and their amounts. This is where the primary logic change needs to happen.

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** - Contains column mappings (`COLOMBIA_CONCEPT_COLUMNS`), AR account mappings (`COLOMBIA_AR_ACCOUNTS`, `COLOMBIA_NT_AR_ACCOUNTS`), and output template column definitions. May need to update concept mappings and ensure `COSTOS_FIJOS` AR account is correctly mapped.

- **`backend/src/interface/tesoreria_dtos.py`** - Contains DTOs and enums including `ConceptType` enum. Should verify that `COSTOS_FIJOS` is properly defined (it is not currently in the enum but is used in the AR accounts mapping).

### Files for Reference (Read-Only)
- **`backend/src/adapter/rest/tesoreria_routes.py`** - API routes for the Tesorería module (no changes needed, just for understanding the flow)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update ConceptType Enum in DTOs

Update `backend/src/interface/tesoreria_dtos.py` to add `COSTOS_FIJOS` to the `ConceptType` enum if not present:

- Add `COSTOS_FIJOS = "COSTOS_FIJOS"` to the Colombia-specific concepts section of the enum
- This ensures type consistency across the application

### Step 2: Update the _process_concepts Method for Colombia

Modify `backend/src/core/servicios/payment_template_service.py` in the `_process_concepts` method:

- For Colombia only, change the simple concepts processing to consolidate:
  - Keep `CAPITAL` as a standalone concept
  - Create a new `COSTOS_FIJOS` concept that **sums** the values from:
    - `4X1000` (4x1000)
    - `FONDO_GARANTIAS` (Fondo de garantías)
    - `IVA_FONDO_GARANTIAS` (IVA Fondo de garantías)
    - `SERVICIO_ORIGINACION` (Servicio de originación)
    - `SERVICIO_GIRO` (Servicio de giro + IVA)
    - `COSTOS_ADICIONALES` (Costos adicionales)
  - Keep `SEGUROS` as a standalone concept (unchanged)
  - Keep `INTERESES` calculation logic (unchanged)
  - Keep `MORATORIOS` calculation logic (unchanged)

The implementation should:
1. Detect when country is Colombia
2. Sum all "COSTOS_FIJOS" component columns into one value
3. Output a single `COSTOS_FIJOS` row if the sum is non-zero
4. NOT output individual rows for 4X1000, FONDO_GARANTIAS, etc.

### Step 3: Update the simple_concepts List Based on Country

Modify the `simple_concepts` list in `_process_concepts` to be country-aware:

- For Colombia: Only process `CAPITAL` and `SEGUROS` as direct simple concepts
- For México: Keep the existing behavior (no change needed as México has different concepts)
- Add a separate aggregation step for `COSTOS_FIJOS` components in Colombia

### Step 4: Verify AR Account Mapping for COSTOS_FIJOS

Verify in `backend/src/core/servicios/catalogs/payment_catalogs.py`:

- `COLOMBIA_AR_ACCOUNTS` already has `"COSTOS_FIJOS": 258` - this is correct
- `COLOMBIA_NT_AR_ACCOUNTS` already has `"COSTOS_FIJOS": 310` - this is correct
- No changes needed to the catalogs, but verify the mapping is used correctly

### Step 5: Run Tests to Verify No Regressions

Execute all tests to ensure the changes work correctly and don't break existing functionality for México.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

1. **México Behavior Unchanged**: This change only affects Colombia. México processing should remain exactly as-is with its own concept types (COMISION_DESEMBOLSO, COMISION_DISPOSICION, etc.).

2. **Backward Compatibility**: The output template columns remain the same (14 columns), only the values in the `concept_type` column change for Colombia.

3. **Summing Logic**: When creating the `COSTOS_FIJOS` row, the `payment_amount` should be the **sum** of all component columns (4X1000 + Fondo + IVA Fondo + Servicio Orig + Servicio Giro + Costos Adicionales).

4. **AR Account**: The `COSTOS_FIJOS` AR account (258 for non-NT, 310 for NT) should be used for the consolidated row.

5. **Testing Recommendation**: After implementation, test with a real Colombia "Historial de Pagos" file to verify:
   - CAPITAL rows appear when Capital column has value
   - A single COSTOS_FIJOS row appears (instead of multiple individual rows) with the summed amount
   - SEGUROS rows appear when Seguro + IVA has value
   - INTERESES rows appear correctly
   - MORATORIOS rows appear correctly
   - México files are unaffected by the change
