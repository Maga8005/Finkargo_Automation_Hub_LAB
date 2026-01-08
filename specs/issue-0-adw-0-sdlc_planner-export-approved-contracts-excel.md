# Feature: Exportar Contratos Aprobados a Excel

## Feature Description
Agregar funcionalidad de exportación a Excel en la pestaña "Contratos Aprobados" del módulo de operaciones. Esta característica permitirá a los usuarios del departamento de operaciones descargar un archivo Excel con todos los contratos aprobados visibles en la tabla, respetando los filtros aplicados. El archivo Excel contendrá información relevante como ID del contrato, tipo, cliente, NIT, cupo aprobado y fecha de aprobación.

## User Story
As a **operations team member**
I want to **export the approved contracts list to an Excel file**
So that **I can share the data with stakeholders, create reports, or analyze contract information offline**

## Problem Statement
Actualmente, el equipo de operaciones puede ver los contratos aprobados en la interfaz web, pero no tiene una forma sencilla de exportar esta información para crear reportes, compartir con otros departamentos, o realizar análisis adicionales. Los usuarios necesitan copiar manualmente los datos o tomar capturas de pantalla, lo cual es ineficiente y propenso a errores.

## Solution Statement
Implementar un botón "Exportar Excel" en la sección de contratos aprobados que genere y descargue un archivo Excel (.xlsx) con todos los contratos visibles (respetando los filtros aplicados). El archivo incluirá columnas formateadas con los datos clave del contrato, fechas en formato legible y montos en formato de moneda colombiana.

## Access Control
- Required Role(s): `operations`, `admin`
- Backend Protection: Use `require_operations_role` from `rbac_dependencies.py` (already used in operations routes)
- Frontend Protection: Component is already within the operations module which requires operations role access

## Relevant Files
Use these files to implement the feature:

**Frontend:**
- `frontend/src/components/forms/FKApprovedContracts.tsx` - Main component showing approved contracts table. Add export button and export logic here.
- `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx` - Similar component for Paga Local CO contracts. Apply same export functionality.
- `frontend/src/services/operationsService.ts` - Add service method for export endpoint (if backend approach is chosen) or use frontend-only export.
- `frontend/src/types/legal.ts` - ContractGeneration interface defines the data structure that will be exported.

**Backend (optional - frontend-only approach recommended):**
- `backend/src/adapter/rest/operations_routes.py` - If backend export is needed, add endpoint here.
- `backend/src/core/servicios/` - If backend processing is needed for Excel generation.

**Dependencies:**
- `xlsx` npm package - Industry standard library for Excel file generation in JavaScript/TypeScript.

**E2E Test Reference:**
- `.claude/commands/test_e2e.md` - E2E test runner instructions
- `.claude/commands/e2e/test_login.md` - Example E2E test format

### New Files
- `frontend/src/utils/excelExport.ts` - Utility function for Excel generation to be reused across components
- `.claude/commands/e2e/test_export_approved_contracts_excel.md` - E2E test file for validating Excel export functionality

## Implementation Plan
### Phase 1: Foundation
- Install `xlsx` npm package in frontend
- Create reusable Excel export utility function in `frontend/src/utils/excelExport.ts`
- Define Excel column configuration matching ContractGeneration data

### Phase 2: Core Implementation
- Add "Exportar Excel" button to FKApprovedContracts component header (next to existing buttons)
- Implement export handler that:
  1. Takes current filtered contracts array
  2. Transforms data to Excel-friendly format (format dates, currency)
  3. Generates and downloads .xlsx file with descriptive filename
- Apply same implementation to FKPagaLocalCOApprovedContracts component

### Phase 3: Integration
- Ensure export respects current filters (exports what user sees)
- Add loading state during export generation
- Handle edge cases (empty list, large datasets)

## Step by Step Tasks

### Step 1: Create E2E Test File
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_login.md` to understand E2E test format
- Create `.claude/commands/e2e/test_export_approved_contracts_excel.md` with:
  - User story for operations user exporting contracts
  - Test steps: login, navigate to approved contracts, apply filter, click export, verify download
  - Success criteria for Excel file generation

### Step 2: Install xlsx Package
- Navigate to `frontend/` directory
- Run `npm install xlsx` to add Excel generation library
- Verify package.json and package-lock.json are updated

### Step 3: Create Excel Export Utility
- Create `frontend/src/utils/excelExport.ts`
- Implement `exportContractsToExcel(contracts, filename)` function
- Define column headers in Spanish: ID Contrato, Tipo, Cliente, NIT, Cupo Aprobado, Fecha Aprobación, Estado
- Format dates using `date-fns` (already in project)
- Format currency values for COP
- Generate descriptive filename with date: `contratos_aprobados_YYYY-MM-DD.xlsx`

### Step 4: Add Export Button to FKApprovedContracts
- Read `frontend/src/components/forms/FKApprovedContracts.tsx`
- Import xlsx utility and FileDownload icon from MUI
- Add "Exportar Excel" button in the header section next to "Filtros" and "Actualizar" buttons
- Implement `handleExportExcel` function that:
  1. Shows loading state
  2. Calls export utility with current `contracts` array
  3. Handles success/error feedback

### Step 5: Add Export Button to FKPagaLocalCOApprovedContracts
- Read `frontend/src/components/forms/FKPagaLocalCOApprovedContracts.tsx`
- Apply same pattern from Step 4
- Customize contract type labels for Paga Local CO types in export

### Step 6: Run Validation Commands
- Run all validation commands to ensure zero regressions
- Execute E2E test to validate export functionality

## Testing Strategy
### Unit Tests
- Test `exportContractsToExcel` utility with mock contract data
- Verify correct column mapping
- Verify date and currency formatting
- Test with empty array (should handle gracefully)
- Test with large dataset (performance)

### Edge Cases
- Empty contracts list (button should be disabled or show message)
- Large number of contracts (> 1000 rows)
- Contracts with missing optional fields (null values)
- Special characters in client names
- Very large cupo_plataforma values

## Acceptance Criteria
1. "Exportar Excel" button appears in both FKApprovedContracts and FKPagaLocalCOApprovedContracts components
2. Clicking the button downloads an .xlsx file
3. Excel file contains all contracts currently visible in the table (respecting active filters)
4. Excel columns are properly labeled in Spanish
5. Dates are formatted as DD/MM/YYYY HH:mm
6. Currency values are formatted with COP symbol and thousand separators
7. Filename includes current date for version tracking
8. Button shows loading state during file generation
9. Empty state shows disabled button or message when no contracts to export
10. No console errors during export process

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd frontend && npm install xlsx` - Install xlsx package
- `cd backend && python -m pytest` - Run backend tests (should pass, no backend changes)
- `cd backend && ruff check src/` - Run backend linting (should pass, no backend changes)
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_export_approved_contracts_excel.md` E2E test file to validate this functionality works

## Notes
- **Library Choice**: Using `xlsx` package (SheetJS) which is the most popular and well-maintained Excel library for JavaScript. It supports both .xlsx and .xls formats.
- **Frontend-only approach**: Generating Excel client-side avoids backend complexity and reduces server load. The data is already available in the frontend state.
- **Accessibility**: Consider adding aria-label to the export button for screen readers.
- **Future Enhancement**: Could add export format options (CSV, PDF) in future iterations.
- **Bundle Size**: xlsx adds ~300KB to bundle. Consider lazy loading if this becomes a concern.
- **Data Privacy**: Ensure exported data doesn't include sensitive fields not shown in the UI.
