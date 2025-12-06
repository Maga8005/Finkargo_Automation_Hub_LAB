# Chore: Connect Contrato de Crédito Paga Local PJ Template

## Chore Description
Connect the `FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx` template to the corresponding button in the Paga Local Colombia functionality. This follows the same pattern already implemented for the "No Aval" case (`pl_co_credito_no_aval`).

The frontend UI already has buttons for "K° Crédito (Aval PJ)" in the `FKPagaLocalCOCuentaCliente.tsx` component (lines 55-60), which uses contract type `pl_co_credito_aval_pj`. The backend contract type enum also already includes `PL_CO_CREDITO_AVAL_PJ = "pl_co_credito_aval_pj"`. What's missing is the document generation method in `document_service.py` that maps this contract type to the actual Word template file.

## Relevant Files
Use these files to resolve the chore:

### Backend Files
- **`backend/src/core/servicios/document_service.py`** - Core document generation service. Contains the routing logic in `generate_contract_document()` method (lines 49-62) and template-specific generation methods. Currently handles `pl_co_credito_no_aval` but needs new method for `pl_co_credito_aval_pj`.
- **`backend/templates/FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx`** - The Word template file that needs to be connected. Already exists in the templates directory.
- **`backend/src/interface/legal_dtos.py`** - Contains the `ContractType` enum (line 18: `PL_CO_CREDITO_AVAL_PJ = "pl_co_credito_aval_pj"`). Already configured - no changes needed.

### Frontend Files (Reference Only - No Changes Needed)
- **`frontend/src/components/forms/FKPagaLocalCOCuentaCliente.tsx`** - UI component with contract configuration. Lines 55-60 already define the `pl_co_credito_aval_pj` contract type with label "K° Crédito (Aval PJ)".
- **`frontend/src/types/legal.ts`** - TypeScript types. Line 114 already includes `'pl_co_credito_aval_pj'` in the union type for `ContractGenerationRequest.contract_type`.

## Step by Step Tasks

### Step 1: Add Routing Case in document_service.py
- Open `backend/src/core/servicios/document_service.py`
- In the `generate_contract_document()` method (around line 49-62), add a new `elif` case for `pl_co_credito_aval_pj`:
  ```python
  elif contract_type == 'pl_co_credito_aval_pj':
      return self.generate_paga_local_credito_aval_pj_document(contract_data)
  ```
- Place this case after the existing `pl_co_credito_no_aval` case (line 57-58)

### Step 2: Create New Generation Method for Aval PJ Crédito Template
- Add a new method `generate_paga_local_credito_aval_pj_document()` in `document_service.py`
- Follow the exact pattern of `generate_paga_local_credito_no_aval_document()` (lines 182-242)
- Key differences:
  - Template name: `"FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx"`
  - Method name: `generate_paga_local_credito_aval_pj_document`
  - Log messages should reference "Paga Local Crédito (Aval PJ)"
- Use the existing `_prepare_paga_local_replacements()` method for placeholder replacement (line 660)

### Step 3: Verify Template File Exists
- Confirm the template file exists at: `backend/templates/FK COL paga local - Fin. COP - K° Crédito (Aval PJ).docx`
- If the template has different placeholders than the No Aval version, may need to add additional replacements to `_prepare_paga_local_replacements()` or create a specific method

### Step 4: Run Validation Commands
- Execute all validation commands to ensure no regressions

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `cd backend && python -c "from src.core.servicios.document_service import DocumentService; print('Import successful')"` - Verify DocumentService imports without errors
- `cd backend && python -m pytest tests/ -v` - Run backend tests to validate with zero regressions
- `cd frontend && npm run lint` - Run frontend linting (no frontend changes expected, but verify)
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build

## Notes
- The `_prepare_paga_local_replacements()` method (lines 660-721) is already designed to handle all Paga Local contract types with the same set of placeholders. It should work for the Aval PJ template without modification unless the template has unique placeholders.
- If the Aval PJ template contains additional placeholders for guarantor (aval) information (e.g., `[nombre del aval]`, `[NIT del aval]`, `[CC del aval]`), a new method `_prepare_paga_local_aval_pj_replacements()` will need to be created, and the data snapshot in `contract_service.py` may need to capture additional aval data.
- The frontend UI and TypeScript types are already fully configured for `pl_co_credito_aval_pj`. Only backend document generation needs to be connected.
- This same pattern will need to be repeated for `pl_co_credito_aval_pn` (Aval PN template) in a separate task.
