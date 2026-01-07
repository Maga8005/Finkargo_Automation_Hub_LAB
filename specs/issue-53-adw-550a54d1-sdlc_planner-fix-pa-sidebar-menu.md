# Bug: PA Report Classification Options Missing from Sidebar Menu

## Bug Description
The newly implemented PA (Patrimonio Autónomo) Report Classification pages ("Reporte PA" and "Reglas Clasificación PA") are not visible in the collapsible sidebar menu under the Finance department. Users cannot navigate to these pages via the sidebar.

**Symptoms:**
- Finance department expands but only shows "Reportería Automática CO" and "Reportería Automática MX"
- The two new PA pages ("Reporte PA" and "Reglas Clasificación PA") are not listed
- Direct URL navigation to `/finance/reporte-pa` and `/finance/reglas-clasificacion-pa` works correctly

**Expected Behavior:**
- Finance department sidebar should show all 4 modules:
  1. Reportería Automática CO
  2. Reportería Automática MX
  3. Reporte PA (for finance, finance_admin, admin roles)
  4. Reglas Clasificación PA (for finance_admin, admin roles only)

**Actual Behavior:**
- Only 2 modules are shown (Reportería Automática CO/MX)
- PA classification pages are inaccessible via sidebar navigation

## Problem Statement
The `financeModules` array in `FKSidebarWithCollapse.tsx` only contains two entries:
1. "Reportería Automática CO" → `/finance/reporteria-automatica-co`
2. "Reportería Automática MX" → `/finance/reporteria-automatica-mx`

The PA Report Classification pages are not included in this array, making them invisible in the sidebar navigation. The pages and routes EXIST and are fully implemented (see `frontend/src/pages/finance/ReportePA.tsx` and `ReglasClasificacionPA.tsx`), only the sidebar menu items are missing.

## Solution Statement
Add two new menu items to the `financeModules` array in `FKSidebarWithCollapse.tsx`:
1. "Reporte PA" with route `/finance/reporte-pa`
2. "Reglas Clasificación PA" with route `/finance/reglas-clasificacion-pa`

This is a minimal surgical fix - only the `financeModules` array needs to be updated. No badge needed since pages are fully implemented.

## Steps to Reproduce
1. Start the frontend server: `cd frontend && npm run dev -- --port 5175`
2. Start the backend server: `cd backend && python -m uvicorn main:app --reload --port 8003`
3. Navigate to http://localhost:5175
4. Log in with a user that has `finance` or `finance_admin` role
5. Click on "Finanzas" in the sidebar to expand the submenu
6. **Expected**: See all 4 menu items including "Reporte PA" and "Reglas Clasificación PA"
7. **Actual**: Only see "Reportería Automática CO" and "Reportería Automática MX"

## Root Cause Analysis
During the PA Report Classification feature implementation:
- Routes were correctly added to `App.tsx` (lines 70-86)
- Pages were correctly created (`ReportePA.tsx`, `ReglasClasificacionPA.tsx`)
- Role access was correctly added to `FKSidebar.tsx` (line 166)
- **MISSED:** The `financeModules` array in `FKSidebarWithCollapse.tsx` (lines 80-93) was NOT updated

The main layout (`FKMainLayout.tsx`) uses `FKSidebarWithCollapse` (not `FKSidebar`), so the sidebar shows modules from the `financeModules` array. This array only contains the original two reporteria modules - the PA entries were never added.

```typescript
// Current financeModules array (lines 80-93)
const financeModules: FinanceModule[] = [
  { id: 'reporteria-co', name: 'Reportería Automática CO', route: '/finance/reporteria-automatica-co', ... },
  { id: 'reporteria-mx', name: 'Reportería Automática MX', route: '/finance/reporteria-automatica-mx', ... },
  // Missing: Reporte PA
  // Missing: Reglas Clasificación PA
];
```

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
- **`frontend/src/components/ui/FKMainLayout.tsx`**: Confirms that `FKSidebarWithCollapse` is the active sidebar component (line 8, 14).
- **`frontend/src/App.tsx`**: Contains the route definitions for reference (lines 70-86). Confirms the correct routes: `/finance/reporte-pa` and `/finance/reglas-clasificacion-pa`.
- **`app_docs/feature-550a54d1-pa-report-classification.md`**: Feature documentation for context on PA classification feature.
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_risk_dashboard.md` to understand E2E test format for creating a new E2E test file.

### New Files
- `.claude/commands/e2e/test_pa_sidebar_navigation.md` - E2E test to verify PA pages are accessible via sidebar

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update financeModules Array in FKSidebarWithCollapse.tsx
- Open `frontend/src/components/ui/FKSidebarWithCollapse.tsx`
- Locate the `financeModules` array (around line 80-93)
- Add two new entries after the existing entries:
  ```typescript
  {
    id: 'reporte-pa',
    name: 'Reporte PA',
    route: '/finance/reporte-pa',
    icon: <Assessment fontSize="small" />,
  },
  {
    id: 'reglas-clasificacion-pa',
    name: 'Reglas Clasificación PA',
    route: '/finance/reglas-clasificacion-pa',
    icon: <Settings fontSize="small" />,
  },
  ```
- Note: `Assessment` icon is already imported (line 27), and `Settings` icon is already imported (line 23)
- No badge needed since pages are fully implemented

### Step 2: Verify hasActiveSubmenu Detection
- In the Finance department section (around line 349), verify the `hasActiveSubmenu` check works with the new routes
- The existing code uses `financeModules.some(m => location.pathname === m.route)` which will automatically work with the new modules

### Step 3: Create E2E Test File
- Read `.claude/commands/e2e/test_risk_dashboard.md` for E2E test format reference
- Read `.claude/commands/test_e2e.md` for test runner instructions
- Create `.claude/commands/e2e/test_pa_sidebar_navigation.md` with the following test steps:
  1. Login as finance_admin user
  2. Expand Finance department in sidebar
  3. Verify "Reporte PA" and "Reglas Clasificación PA" menu items are visible
  4. Click "Reporte PA" and verify navigation to `/finance/reporte-pa`
  5. Verify page title "Reporte PA - Clasificación"
  6. Go back and click "Reglas Clasificación PA"
  7. Verify navigation to `/finance/reglas-clasificacion-pa`
  8. Verify page title "Reglas de Clasificación PA"
  9. Take screenshots of sidebar expanded and each page

### Step 4: Run Validation Commands
- Execute all validation commands listed below to ensure zero regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# Verify the file changes compile correctly
cd frontend && npx tsc --noEmit

# Run frontend linting
cd frontend && npm run lint

# Run frontend build to validate production compilation
cd frontend && npm run build

# Backend tests (ensure no regressions)
cd backend && python -m pytest

# Backend linting
cd backend && ruff check src/
```

After validation commands pass:
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_pa_sidebar_navigation.md` test file to validate sidebar navigation works correctly

## Notes
- This is a minimal surgical fix - only the `financeModules` array needs to be updated
- No new dependencies required
- The icons `Assessment` and `Settings` are already imported in `FKSidebarWithCollapse.tsx`
- Role-based access control is enforced at the route level in `App.tsx` via `RoleProtectedRoute`, not in the sidebar
- The sidebar shows all finance menu items to all authenticated users - unauthorized users will be redirected when they click
- **Pattern to remember:** When adding new pages to a department, always check BOTH `FKSidebar.tsx` (role access) AND `FKSidebarWithCollapse.tsx` (menu items)
