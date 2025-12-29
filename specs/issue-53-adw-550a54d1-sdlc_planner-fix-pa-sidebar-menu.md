# Bug: PA Report Classification Sidebar Menu Items Missing

## Bug Description
The PA Report Classification feature was documented and planned (ADW 550a54d1), including database migrations and E2E test specifications. However, the sidebar navigation menu is missing the two new menu items that should appear under the "Finanzas" department collapsible menu:
- "Reglas Clasificación PA" → `/finance/reglas-clasificacion-pa`
- "Reporte PA" → `/finance/reporte-pa`

Users cannot navigate to these pages through the UI because the sidebar does not display these options. The feature documentation at `app_docs/feature-550a54d1-pa-report-classification.md` specifies these pages should be accessible, but the `FKSidebarWithCollapse.tsx` component was not updated to include them.

## Problem Statement
The `financeModules` array in `FKSidebarWithCollapse.tsx` only contains two entries:
1. "Reportería Automática CO" → `/finance/reporteria-automatica-co`
2. "Reportería Automática MX" → `/finance/reporteria-automatica-mx`

The PA Report Classification pages are not included in this array, making them invisible in the sidebar navigation.

## Solution Statement
Add two new menu items to the `financeModules` array in `FKSidebarWithCollapse.tsx`:
1. "Reglas Clasificación PA" with route `/finance/reglas-clasificacion-pa` (for finance_admin role)
2. "Reporte PA" with route `/finance/reporte-pa` (for finance role)

Since these pages are planned but not yet implemented (as noted in the feature documentation), add a "Próximo" badge to indicate they are coming soon.

## Steps to Reproduce
1. Start the frontend server: `cd frontend && npm run dev -- --port 5173`
2. Start the backend server with correct CORS: `cd backend && CORS_ORIGINS='["http://localhost:5173"]' uv run uvicorn main:app --reload --port 8003`
3. Navigate to http://localhost:5173
4. Log in with any valid credentials
5. Click on "Finanzas" in the sidebar to expand the submenu
6. **Expected**: See "Reglas Clasificación PA" and "Reporte PA" menu items
7. **Actual**: Only see "Reportería Automática CO" and "Reportería Automática MX"

## Root Cause Analysis
The PA Report Classification feature planning phase created:
- Database migrations (`migration_pa_classification.sql`)
- Role documentation (`migration_add_finance_admin_role.sql`)
- E2E test specification (`test_pa_report_classification.md`)
- Feature documentation (`feature-550a54d1-pa-report-classification.md`)

However, the sidebar navigation component (`FKSidebarWithCollapse.tsx`) was not updated during the planning phase. The `financeModules` array at line 80-93 defines the Finance department submenu items, but the PA-related entries were never added.

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [ ] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- **`frontend/src/components/ui/FKSidebarWithCollapse.tsx`**: The main file to modify. Contains the `financeModules` array (lines 80-93) that defines Finance department submenu items. This is where the two PA menu items need to be added.
- **`app_docs/feature-550a54d1-pa-report-classification.md`**: Reference documentation specifying the expected routes and access control for PA features.
- **`.claude/commands/e2e/test_pa_report_classification.md`**: E2E test specification confirming the expected routes are `/finance/reglas-clasificacion-pa` and `/finance/reporte-pa`.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add PA Menu Items to financeModules Array
- Open `frontend/src/components/ui/FKSidebarWithCollapse.tsx`
- Locate the `financeModules` array (around line 80)
- Add two new entries after the existing entries:
  ```typescript
  {
    id: 'reglas-clasificacion-pa',
    name: 'Reglas Clasificación PA',
    route: '/finance/reglas-clasificacion-pa',
    icon: <Description fontSize="small" />,
    badge: 'Próximo',
  },
  {
    id: 'reporte-pa',
    name: 'Reporte PA',
    route: '/finance/reporte-pa',
    icon: <Description fontSize="small" />,
    badge: 'Próximo',
  },
  ```
- Note: The `badge: 'Próximo'` indicates these pages are planned but not yet fully implemented. This can be removed when the full implementation is complete.

### Step 2: Verify TypeScript Compilation
- Run TypeScript type check to ensure no type errors
- Run ESLint to ensure code style compliance
- Run frontend build to validate production compilation

### Step 3: Visual Verification
- Start the frontend and backend servers
- Navigate to the application
- Click on "Finanzas" in the sidebar
- Verify that "Reglas Clasificación PA" and "Reporte PA" menu items appear
- Verify the "Próximo" badge is visible on both items
- Verify clicking the menu items navigates to the correct routes (even if pages show 404 or placeholder)

### Step 4: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes
- The PA Report Classification pages themselves (ReglasClasificacionPA.tsx and ReportePA.tsx) are listed in the feature documentation as "pending implementation". This bug fix only addresses the sidebar navigation; the actual page implementations are a separate task.
- The `badge: 'Próximo'` can be removed once the full feature is implemented.
- Access control (role-based visibility) for these menu items is handled at the route level via `RoleProtectedRoute`, not in the sidebar. The sidebar shows all menu items to all authenticated users.
- The routes follow the existing pattern: Spanish names with kebab-case (e.g., `/finance/reporteria-automatica-co`).
