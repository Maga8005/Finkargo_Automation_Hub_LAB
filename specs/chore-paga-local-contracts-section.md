# Chore: Add Paga Local Colombia Contracts Section under Operations Module

## Chore Description
Add a new section for contract requests for the "Paga Local - Colombia" product under the Operations module. This section will be separate from "Contratos Colombia" and "Contratos México" and will contain three major tabs:

1. **Contratos Cuenta Cliente** - Contains subtabs for different client account contract categories:
   - **Contratos Marco - Aval Persona Jurídica** (2 contract types)
   - **Contratos Marco - Aval Persona Natural** (2 contract types)
   - **Contratos Marco - Sin Aval** (2 contract types)

2. **Documentos Operación** - Contains subtabs for operation documents:
   - Mandato (IM)
   - Solicitud de Desembolso
   - Template DIAN - Mandato (IM)

3. **Contratos Aprobados** - For tracking approved "Paga Local" documents

### Contract Types Detail

**Tab: Contratos Cuenta Cliente**

| Subtab | Contract Types |
|--------|----------------|
| Contratos Marco - Aval Persona Jurídica | `pl_co_credito_aval_pj`, `pl_co_mandato_pj` |
| Contratos Marco - Aval Persona Natural | `pl_co_credito_aval_pn`, `pl_co_mandato_pn` |
| Contratos Marco - Sin Aval | `pl_co_credito_no_aval`, `pl_co_mandato_no_aval` |

**Tab: Documentos Operación**

| Subtab | Contract Type |
|--------|---------------|
| Mandato (IM) | `pl_co_mandato_im` |
| Solicitud de Desembolso | `pl_co_solicitud_desembolso` |
| Template DIAN - Mandato (IM) | `pl_co_dian_mandato_im` |

## Relevant Files
Use these files to resolve the chore:

**Frontend - Routing & Layout:**
- `frontend/src/App.tsx` - Main application router; needs new route for Paga Local (line 78-79 shows existing operations routes pattern)
- `frontend/src/components/ui/FKSidebar.tsx` - Sidebar navigation; may need updates if department navigation changes

**Frontend - Existing Operations Pages (Reference):**
- `frontend/src/pages/operations/OperationsContractsColombia.tsx` - Reference implementation with tabs pattern (lines 47-166)
- `frontend/src/pages/operations/OperationsContractsMexico.tsx` - Simpler placeholder reference

**Frontend - Existing Form Components (Reference):**
- `frontend/src/components/forms/FKContractRequest.tsx` - Client search and contract request pattern (lines 26-301)
- `frontend/src/components/forms/FKApprovedContracts.tsx` - Approved contracts table pattern with filters (lines 52-555)

**Frontend - Services & Types:**
- `frontend/src/services/operationsService.ts` - Operations API calls; will need new methods for Paga Local (line 11 defines BASE_URL)
- `frontend/src/types/legal.ts` - Contract types; needs new Paga Local contract types (line 109)
- `frontend/src/types/index.ts` - Core types including UserRole

**Backend - Routes:**
- `backend/src/adapter/rest/operations_routes.py` - Operations endpoints; will need Paga Local endpoints (lines 62-325)

**Backend - Services:**
- `backend/src/core/servicios/contract_service.py` - Contract generation service; may need Paga Local logic

**Backend - DTOs:**
- `backend/src/interface/legal_dtos.py` - Contract DTOs; needs Paga Local contract types

**Database:**
- `backend/database/combined_schema.sql` - Schema reference; contract_generations table (lines 118-150) stores all contract types

### New Files
- `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx` - Main page with 3 major tabs for Paga Local Colombia
- `frontend/src/components/forms/FKPagaLocalCOCuentaCliente.tsx` - Component with subtabs for Cuenta Cliente contracts
- `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx` - Component with subtabs for operation documents
- `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx` - Component for approved Paga Local Colombia contracts
- `frontend/src/components/forms/FKPagaLocalCOContractRequest.tsx` - Reusable contract request form for Paga Local Colombia (accepts contract type as prop)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Paga Local Colombia Contract Types to Backend DTOs
- Edit `backend/src/interface/legal_dtos.py` to add the following to the `ContractType` enum:
  ```python
  # Paga Local Colombia - Contratos Cuenta Cliente - Aval Persona Jurídica
  PL_CO_CREDITO_AVAL_PJ = "pl_co_credito_aval_pj"
  PL_CO_MANDATO_PJ = "pl_co_mandato_pj"

  # Paga Local Colombia - Contratos Cuenta Cliente - Aval Persona Natural
  PL_CO_CREDITO_AVAL_PN = "pl_co_credito_aval_pn"
  PL_CO_MANDATO_PN = "pl_co_mandato_pn"

  # Paga Local Colombia - Contratos Cuenta Cliente - Sin Aval
  PL_CO_CREDITO_NO_AVAL = "pl_co_credito_no_aval"
  PL_CO_MANDATO_NO_AVAL = "pl_co_mandato_no_aval"

  # Paga Local Colombia - Documentos Operación
  PL_CO_MANDATO_IM = "pl_co_mandato_im"
  PL_CO_SOLICITUD_DESEMBOLSO = "pl_co_solicitud_desembolso"
  PL_CO_DIAN_MANDATO_IM = "pl_co_dian_mandato_im"
  ```

### Step 2: Update Frontend Contract Types
- Edit `frontend/src/types/legal.ts` to add the new contract types to `ContractGenerationRequest` interface (line 109):
  ```typescript
  contract_type?:
    | 'activos'
    | 'otrosi'
    | 'inventario_bodega'
    // Paga Local Colombia - Cuenta Cliente - Aval PJ
    | 'pl_co_credito_aval_pj'
    | 'pl_co_mandato_pj'
    // Paga Local Colombia - Cuenta Cliente - Aval PN
    | 'pl_co_credito_aval_pn'
    | 'pl_co_mandato_pn'
    // Paga Local Colombia - Cuenta Cliente - Sin Aval
    | 'pl_co_credito_no_aval'
    | 'pl_co_mandato_no_aval'
    // Paga Local Colombia - Documentos Operación
    | 'pl_co_mandato_im'
    | 'pl_co_solicitud_desembolso'
    | 'pl_co_dian_mandato_im';
  ```

### Step 3: Create Reusable Paga Local Colombia Contract Request Component
- Create `frontend/src/components/forms/FKPagaLocalCOContractRequest.tsx`
- This is a reusable component that accepts `contractType` and `contractLabel` as props
- Follow the pattern from `FKContractRequest.tsx`:
  - Client search functionality using `legalService.searchClients()`
  - Contract request using `operationsService.requestContractGeneration()` with the provided contract_type
  - Success/error handling with Material-UI alerts
  - Client data preview before submission
- Props interface:
  ```typescript
  interface FKPagaLocalCOContractRequestProps {
    contractType: string;
    contractLabel: string;
    description?: string;
  }
  ```

### Step 4: Create Paga Local Colombia Cuenta Cliente Component with Subtabs
- Create `frontend/src/components/forms/FKPagaLocalCOCuentaCliente.tsx`
- Implement nested tabs structure using Material-UI Tabs:
  - **Top level**: 3 subtabs for contract categories (Aval PJ, Aval PN, Sin Aval)
  - **Each category**: 2 contract type buttons/cards to select which contract to request
- Structure:
  ```
  Subtab: Contratos Marco - Aval Persona Jurídica
    ├── K° Crédito (Aval PJ) → pl_co_credito_aval_pj
    └── K° Mandato PJ → pl_co_mandato_pj

  Subtab: Contratos Marco - Aval Persona Natural
    ├── K° Crédito (Aval PN) → pl_co_credito_aval_pn
    └── K° Mandato PN → pl_co_mandato_pn

  Subtab: Contratos Marco - Sin Aval
    ├── K° Crédito (No Aval) → pl_co_credito_no_aval
    └── K° Mandato No Aval → pl_co_mandato_no_aval
  ```
- Use the `FKPagaLocalCOContractRequest` component for each contract type

### Step 5: Create Paga Local Colombia Documentos Operación Component with Subtabs
- Create `frontend/src/components/forms/FKPagaLocalCODocumentosOperacion.tsx`
- Implement tabs structure for 3 document types:
  ```
  Subtab: Mandato (IM) → pl_co_mandato_im
  Subtab: Solicitud de Desembolso → pl_co_solicitud_desembolso
  Subtab: Template DIAN - Mandato (IM) → pl_co_dian_mandato_im
  ```
- Each subtab renders `FKPagaLocalCOContractRequest` with the appropriate contract type

### Step 6: Create Paga Local Colombia Approved Contracts Component
- Create `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx`
- Follow the pattern from `FKApprovedContracts.tsx`:
  - Table display of approved contracts
  - Filter by all Paga Local Colombia contract types only
  - Sorting capabilities
  - PDF download functionality
  - Filter panel with type checkboxes (show all 9 Paga Local Colombia contract types), client name, NIT, date range
- Update `getContractTypeBadge()` function to handle all Paga Local Colombia types with appropriate labels and colors

### Step 7: Create Operations Paga Local Colombia Page
- Create `frontend/src/pages/operations/OperationsPagaLocalColombia.tsx`
- Follow the structure from `OperationsContractsColombia.tsx`:
  - Header with title "Paga Local Colombia - Solicitar"
  - Three major tabs using Material-UI Tabs component:
    1. "Contratos Cuenta Cliente" - renders `FKPagaLocalCOCuentaCliente`
    2. "Documentos Operación" - renders `FKPagaLocalCODocumentosOperacion`
    3. "Contratos Aprobados" - renders `FKPagaLocalCOApprovedContracts`
  - Each tab has an info card explaining its purpose
  - Use appropriate icons (AccountBalance, Assignment, CheckCircle)

### Step 8: Add Route for Paga Local Colombia Page
- Edit `frontend/src/App.tsx`:
  - Import `OperationsPagaLocalColombia` component at the top with other imports
  - Add route `/operations/paga-local-colombia` following the pattern at lines 78-79:
    ```tsx
    <Route path="operations/paga-local-colombia" element={<OperationsPagaLocalColombia />} />
    ```
  - Route should be under the protected layout similar to other operations routes

### Step 9: Update Operations Service for Paga Local Colombia
- Edit `frontend/src/services/operationsService.ts`:
  - Add method `getApprovedPagaLocalCOContracts(filters, sortBy, sortOrder)` that filters by all Paga Local Colombia contract types:
    ```typescript
    async getApprovedPagaLocalCOContracts(
      filters?: OperationsFilterParams,
      sortBy?: string,
      sortOrder?: string
    ): Promise<ContractGeneration[]> {
      const pagaLocalCOTypes = [
        'pl_co_credito_aval_pj', 'pl_co_mandato_pj',
        'pl_co_credito_aval_pn', 'pl_co_mandato_pn',
        'pl_co_credito_no_aval', 'pl_co_mandato_no_aval',
        'pl_co_mandato_im', 'pl_co_solicitud_desembolso', 'pl_co_dian_mandato_im'
      ];
      return this.getApprovedContracts(
        { ...filters, contract_types: pagaLocalCOTypes },
        sortBy,
        sortOrder
      );
    }
    ```
  - The existing `requestContractGeneration()` method already accepts contract_type, so no changes needed there

### Step 10: Update Backend to Support Multiple Contract Type Filtering
- Edit `backend/src/adapter/rest/operations_routes.py`:
  - Update the `get_approved_contracts` endpoint to accept multiple contract types as a comma-separated string or list
  - Example: `contract_types=pl_credito_aval_pj,pl_mandato_pj`
- Edit `backend/src/repositorio/contract_repository.py`:
  - Update `get_approved_contracts` method to filter by multiple contract types using SQL `IN` clause

### Step 11: Run Validation Commands
Execute every command to validate the chore is complete with zero regressions:
- Run backend tests
- Run backend linting
- Run frontend linting
- Run TypeScript type check
- Run frontend build

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes

### Contract Type Naming Convention
All Paga Local Colombia contract types use the `pl_co_` prefix for easy identification and filtering:
- `pl_` = Paga Local
- `co_` = Colombia (allows for future Mexico expansion with `mx_`)
- `credito` / `mandato` = Contract category
- `aval_pj` / `aval_pn` / `no_aval` = Guarantee type (Persona Jurídica, Persona Natural, No Guarantee)
- `im` = Importación Mandato
- `dian` = DIAN template

### UI Structure
```
OperationsPagaLocalColombia (Page)
├── Tab 1: Contratos Cuenta Cliente
│   ├── Subtab: Aval Persona Jurídica
│   │   ├── K° Crédito (Aval PJ) [pl_co_credito_aval_pj]
│   │   └── K° Mandato PJ [pl_co_mandato_pj]
│   ├── Subtab: Aval Persona Natural
│   │   ├── K° Crédito (Aval PN) [pl_co_credito_aval_pn]
│   │   └── K° Mandato PN [pl_co_mandato_pn]
│   └── Subtab: Sin Aval
│       ├── K° Crédito (No Aval) [pl_co_credito_no_aval]
│       └── K° Mandato No Aval [pl_co_mandato_no_aval]
├── Tab 2: Documentos Operación
│   ├── Subtab: Mandato (IM) [pl_co_mandato_im]
│   ├── Subtab: Solicitud de Desembolso [pl_co_solicitud_desembolso]
│   └── Subtab: Template DIAN - Mandato (IM) [pl_co_dian_mandato_im]
└── Tab 3: Contratos Aprobados
    └── Table with all approved Paga Local Colombia contracts
```

### Database Considerations
- No database migration is needed - the existing `contract_generations` table stores all contract types using the `contract_type` column
- The new contract types will be stored as string values (e.g., `'pl_co_credito_aval_pj'`)
- The approved contracts filtering uses the `contract_types` parameter which the backend already supports

### Template Files Reference
The contract type values map to these template files:
| Contract Type | Template File |
|---------------|---------------|
| `pl_co_credito_aval_pj` | FK COL - Fin. COP - K° Crédito (Aval PJ).docx |
| `pl_co_mandato_pj` | FK COL - Fin. COP - K° Mandato PJ.docx |
| `pl_co_credito_aval_pn` | FK COL - Fin. COP - K° Crédito (Aval PN).docx |
| `pl_co_mandato_pn` | FK COL - Fin. COP - K° Mandato PN.docx |
| `pl_co_credito_no_aval` | FK COL - Fin. COP - K° Crédito (No Aval).docx |
| `pl_co_mandato_no_aval` | FK COL - Fin. COP - K° Mandato No Aval.docx |
| `pl_co_mandato_im` | FK COL - Fin. COP - Mandato (IM).docx |
| `pl_co_solicitud_desembolso` | FK COL - Fin. COP - Solicitud de Desembolso.docx |
| `pl_co_dian_mandato_im` | FK COL - Fin. COP - Template DIAN - Mandato (IM).docx |

### Future Considerations
- Contract templates will need to be uploaded to the `contract_templates` table with the corresponding `contract_type` values
- Consider adding the Paga Local Colombia option to the sidebar navigation or Operations department menu for discoverability
- Spanish labels should be used for all UI text following existing patterns
- The `pl_co_` prefix allows for future expansion to Paga Local Mexico (`pl_mx_`) without naming conflicts
