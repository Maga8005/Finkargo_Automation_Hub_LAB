# Feature: Mexico Tesorería Concept Type and Grouping Logic Update

## Feature Description
Update the Mexico payment template conversion logic in the Tesorería module to use the correct concept_type names and column mappings. This is a Mexico-only change - Colombia logic must remain unchanged. The update aligns Mexico's concept extraction with the new specification:

- **CAPITAL**: Column P (Capital)
- **SEGUROS**: Column T (Seguro + IVA)
- **COMISION DESEMBOLSO**: Column U (Comision del desembolso + IVA)
- **COMISION DISPOSICION**: Column V (Comision por disposicion de crédito + IVA)
- **COMISION SWIFT**: Column W (Comision swift)
- **COMISION ADMINISTRACION**: Column X (Comision administracion y manejo)
- **COMISION APERTURA**: Column Y (Comision de apertura)
- **COSTOS ADICIONALES**: Column AA (Costos adicionales)
- **INTERESES**: Column AB (Intereses corrientes)
- **MORATORIOS**: Sum of columns AC, AD, AE, AF (PAR 60/61 columns)

## User Story
As a Treasury (Tesorería) department user working with Mexico payment data
I want the payment template converter to produce concept types with the correct names and column mappings
So that the generated NetSuite template aligns with our finance team's requirements and naming conventions

## Problem Statement
The current Mexico concept_type output uses underscore-separated names (e.g., `COMISION_DESEMBOLSO`) instead of space-separated names (e.g., `COMISION DESEMBOLSO`). Additionally, the MORATORIOS calculation for Mexico needs to use the same PAR 60/61 column logic that Colombia uses, rather than the PAR 30/60/90/120+ columns currently configured.

## Solution Statement
Update the `MEXICO_CONCEPT_COLUMNS` dictionary in `payment_catalogs.py` and modify the `_process_concepts` method in `payment_template_service.py` to:
1. Use space-separated concept type names for Mexico (e.g., `COMISION DESEMBOLSO` instead of `COMISION_DESEMBOLSO`)
2. Update MORATORIOS calculation to use PAR 60/61 columns (same as Colombia)
3. Keep the concept_type output consistent with the specification
4. Ensure Colombia logic is completely unchanged

## Access Control
- Required Role(s): `tesoreria`, `admin`
- Backend Protection: Already protected via `require_roles(['tesoreria'])` in `tesoreria_routes.py`
- Frontend Protection: Already protected via `RoleProtectedRoute` for tesoreria pages

## Relevant Files
Use these files to implement the feature:

- **`backend/src/core/servicios/catalogs/payment_catalogs.py`** - Contains `MEXICO_CONCEPT_COLUMNS` and `MEXICO_AR_ACCOUNTS` dictionaries that define column mappings and AR accounts. **Primary file to modify for concept type naming and column mappings.**
- **`backend/src/core/servicios/payment_template_service.py`** - Contains `_process_concepts` method that processes concept columns and generates output rows. **Must be updated to handle space-separated concept type names for Mexico.**
- **`backend/src/interface/tesoreria_dtos.py`** - DTOs for tesoreria module (may need review for concept type validation)
- **`frontend/src/types/tesoreria.ts`** - TypeScript types for tesoreria (may need to update `ConceptType` union)
- **`frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx`** - Mexico converter page (instructions may need updating)
- **`.claude/commands/test_e2e.md`** - E2E test runner instructions (read for E2E test creation)
- **`.claude/commands/e2e/test_payment_template_converter.md`** - Existing E2E test (read for pattern reference)

### New Files
- **`.claude/commands/e2e/test_mexico_concept_type_mapping.md`** - E2E test file to validate Mexico concept type mapping changes

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [ ] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (Mexico Historial de Pagos):**

| Column Name (exact) | Column Letter | Required | Data Type | Concept Type Output |
|---------------------|---------------|----------|-----------|---------------------|
| Capital | P | Yes | Number | CAPITAL |
| Seguro + IVA | T | No | Number | SEGUROS |
| Comision del desembolso + IVA | U | No | Number | COMISION DESEMBOLSO |
| Comision por disposicion de crédito + IVA | V | No | Number | COMISION DISPOSICION |
| Comision swift | W | No | Number | COMISION SWIFT |
| Comision administracion y manejo | X | No | Number | COMISION ADMINISTRACION |
| Comision de apertura | Y | No | Number | COMISION APERTURA |
| Costos adicionales | AA | No | Number | COSTOS ADICIONALES |
| Intereses Corrientes | AB | No | Number | INTERESES |
| Intereses de Mora (Tasa corriente) PAR 60 | AC | No | Number | MORATORIOS (aggregated) |
| Intereses de Mora (Tasa restante de mora) PAR 60 | AD | No | Number | MORATORIOS (aggregated) |
| Intereses de Mora (Tasa corriente) PAR 61 | AE | No | Number | MORATORIOS (aggregated) |
| Intereses de Mora (Tasa restante de mora) PAR 61 | AF | No | Number | MORATORIOS (aggregated) |

**Output Excel Structure:**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| concept_type | Derived from concept columns | Space-separated name (e.g., "COMISION DESEMBOLSO") |
| payment_amount | Value from concept column | Numeric, rounded to 2 decimals |

**Catalog Dependencies:**
- [x] AR account mappings documented - Must update keys in `MEXICO_AR_ACCOUNTS` to use space-separated names
- [x] Country-specific variations identified (CO vs MX) - Mexico uses space-separated names, Colombia uses underscore-separated

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| get_concept_columns('mexico') | Dict[str, str] | Direct dict access | `columns["COMISION DESEMBOLSO"]` |
| get_ar_account(concept_type, 'mexico') | Optional[int] | Function return | `get_ar_account("COMISION DESEMBOLSO", "mexico")` |

### Interface Mapping (Frontend ↔ Backend)

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| concept_type | concept_type | string | Space-separated for Mexico output |
| payment_amount | payment_amount | number | No change |

## Implementation Plan

### Phase 1: Foundation
- Update `MEXICO_CONCEPT_COLUMNS` dictionary to use correct column names for MORATORIOS calculation (PAR 60/61 columns)
- Update `MEXICO_AR_ACCOUNTS` dictionary to use space-separated concept type names as keys

### Phase 2: Core Implementation
- Modify `_process_concepts` method in `payment_template_service.py` to:
  - Use space-separated concept type names in output for Mexico
  - Calculate MORATORIOS using PAR 60/61 columns instead of PAR 30/60/90/120+
- Ensure the `mexico_simple_concepts` list uses the new space-separated names

### Phase 3: Integration
- Update frontend TypeScript types if needed
- Update frontend instructions display if needed
- Create E2E test for Mexico concept type validation

## Step by Step Tasks

### Task 1: Create E2E Test File for Mexico Concept Type Mapping
- Read `.claude/commands/test_e2e.md` to understand E2E test format
- Read `.claude/commands/e2e/test_payment_template_converter.md` for pattern reference
- Create `.claude/commands/e2e/test_mexico_concept_type_mapping.md` with:
  - User story for Mexico concept type validation
  - Test steps to upload Mexico test file
  - Verification of concept_type names in output
  - Success criteria for space-separated names

### Task 2: Update MEXICO_CONCEPT_COLUMNS in payment_catalogs.py
- Update the dictionary keys to use space-separated names
- Add the MORATORIOS-related columns (PAR 60/61) for Mexico:
  - `INTERESES_MORA_TASA_CORRIENTE_PAR_60`: "Intereses de Mora (Tasa corriente) PAR 60"
  - `INTERESES_MORA_TASA_RESTANTE_PAR_60`: "Intereses de Mora (Tasa restante de mora) PAR 60"
  - `INTERESES_MORA_TASA_CORRIENTE_PAR_61`: "Intereses de Mora (Tasa corriente) PAR 61"
  - `INTERESES_MORA_TASA_RESTANTE_PAR_61`: "Intereses de Mora (Tasa restante de mora) PAR 61"
- Remove the old PAR 30/60/90/120+ columns

### Task 3: Update MEXICO_AR_ACCOUNTS in payment_catalogs.py
- Change keys from underscore-separated to space-separated:
  - `"COMISION_DESEMBOLSO"` → `"COMISION DESEMBOLSO"`
  - `"COMISION_DISPOSICION"` → `"COMISION DISPOSICION"`
  - `"COMISION_SWIFT"` → `"COMISION SWIFT"`
  - `"COMISION_ADMINISTRACION"` → `"COMISION ADMINISTRACION"`
  - `"COMISION_APERTURA"` → `"COMISION APERTURA"`
  - `"COSTOS_ADICIONALES"` → `"COSTOS ADICIONALES"`
- Keep AR account values (2114, 2115, 2117) unchanged

### Task 4: Update _process_concepts Method in payment_template_service.py
- Modify the `mexico_simple_concepts` list to use space-separated names:
  ```python
  mexico_simple_concepts = [
      "CAPITAL", "SEGUROS", "COSTOS ADICIONALES",
      "COMISION DESEMBOLSO", "COMISION DISPOSICION", "COMISION SWIFT",
      "COMISION ADMINISTRACION", "COMISION APERTURA"
  ]
  ```
- Update the Mexico MORATORIOS calculation to use PAR 60/61 columns (same logic as Colombia)
- Ensure the INTERESES calculation for Mexico uses the same pattern (Intereses Corrientes only, since Mexico doesn't have the same discount/condonation columns)

### Task 5: Update Frontend TypeScript Types (if needed)
- Review `frontend/src/types/tesoreria.ts`
- Update `ConceptType` union type if it lists Mexico concept types
- Use space-separated names to match backend output

### Task 6: Update Frontend Instructions (if needed)
- Review `frontend/src/pages/tesoreria/PlantillasNetSuiteMX.tsx`
- Update the instructions text to reflect the correct concept columns
- Ensure the displayed column requirements match the actual column mappings

### Task 7: Run Validation Commands
- Run backend tests to ensure no regressions
- Run backend linting
- Run frontend linting
- Run TypeScript type check
- Run frontend build
- Execute E2E test for Mexico concept type mapping

## Testing Strategy

### Unit Tests
- Add unit test for `_process_concepts` with Mexico country code
- Verify output concept_type names are space-separated
- Verify MORATORIOS calculation uses PAR 60/61 columns
- Verify Colombia logic remains unchanged

### Edge Cases
- Empty values in concept columns (should be skipped)
- Zero values in concept columns (should be skipped)
- All MORATORIOS columns empty (no MORATORIOS row generated)
- All MORATORIOS columns have values (sum correctly)
- Mixed empty/non-empty concept columns

## Acceptance Criteria
1. Mexico concept_type output uses space-separated names (e.g., "COMISION DESEMBOLSO")
2. Mexico MORATORIOS is calculated as sum of PAR 60/61 columns (AC+AD+AE+AF)
3. Colombia output remains completely unchanged (underscore names, COSTOS_FIJOS aggregation)
4. AR account lookups work correctly with new concept type names
5. E2E test validates the Mexico conversion produces correct concept_type values
6. All existing backend tests pass
7. Frontend builds without TypeScript errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_mexico_concept_type_mapping.md` to validate the Mexico concept type mapping functionality
- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- **CRITICAL**: Colombia logic must NOT be modified. The underscore-separated concept types and COSTOS_FIJOS aggregation are correct for Colombia.
- The change from underscore to space separation is intentional for Mexico to match the finance team's NetSuite template naming convention.
- The MORATORIOS column change from PAR 30/60/90/120+ to PAR 60/61 aligns Mexico with the same source data structure as Colombia.
- No new npm or pip packages required for this change.

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (N/A - no DB changes)
- [x] E2E test file task included (if UI feature)
- [x] All external dependencies (npm/pip packages) listed in Notes (none needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented (if applicable)
- [x] Data transformation rules specified (1:1 or 1:N)
- [x] Catalog/lookup dependencies identified

### Consistency (ALL features)
- [x] Data types match between frontend and backend
- [x] Field naming conventions documented (space-separated for Mexico concept_type)
- [x] Access patterns (dict vs object) verified for repository methods
- [x] Country-specific variations handled (CO vs MX) - Mexico only changes

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [x] E2E test covers happy path with screenshots (if UI feature)
