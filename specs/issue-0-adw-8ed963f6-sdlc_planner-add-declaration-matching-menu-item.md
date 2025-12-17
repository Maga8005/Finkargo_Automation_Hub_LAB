# Bug: Declaration Matching Menu Item Missing from Treasury Sidebar

## Bug Description
The "Coincidencia Declaraciones - Historial de Pagos" (Declaration Matching) functionality is not visible as a menu option under the Tesorería (Treasury) department in the sidebar navigation. The page exists and is accessible via direct URL (`/treasury/declaration-matching`), but users cannot discover or navigate to it through the sidebar menu.

**Expected Behavior:** A menu item for "Coincidencia Declaraciones" should appear in the Tesorería submenu alongside "Plantillas NetSuite", "Aplicación Pagos CO", and "Aplicación Pagos MX".

**Actual Behavior:** The Tesorería submenu only shows 3 items and does not include the Declaration Matching option.

## Problem Statement
The `treasuryModules` array in `FKSidebarWithCollapse.tsx` does not include an entry for the Declaration Matching page, despite the route being properly configured in `App.tsx`. Additionally, the auto-expand logic checks for `/tesoreria/` paths but the Declaration Matching route uses `/treasury/` which is inconsistent.

## Solution Statement
1. Add a new entry to the `treasuryModules` array for the Declaration Matching functionality
2. Update the auto-expand logic to also detect `/treasury/` paths for treasury department auto-expansion
3. The route should be `/treasury/declaration-matching` to match the existing App.tsx configuration

## Steps to Reproduce
1. Log in as an Admin or Tesorería user
2. Click on "Tesorería" department in the sidebar to expand it
3. Observe only 3 submenu items are shown:
   - Plantillas NetSuite
   - Aplicación Pagos CO
   - Aplicación Pagos MX
4. Note that "Coincidencia Declaraciones" is missing
5. Manually navigate to `http://localhost:5173/treasury/declaration-matching` - page loads correctly

## Root Cause Analysis
The root cause is in `frontend/src/components/ui/FKSidebarWithCollapse.tsx`:

1. **Missing menu item (lines 133-152):** The `treasuryModules` array defines the submenu items for Tesorería but does not include the Declaration Matching page:
   ```typescript
   const treasuryModules: TreasuryModule[] = [
     { id: 'plantillas-netsuite', name: 'Plantillas NetSuite', route: '/tesoreria/plantillas-netsuite', ... },
     { id: 'plantillas-netsuite-co', name: 'Aplicación Pagos CO', route: '/tesoreria/plantillas-netsuite/colombia', ... },
     { id: 'plantillas-netsuite-mx', name: 'Aplicación Pagos MX', route: '/tesoreria/plantillas-netsuite/mexico', ... },
   ];
   // Missing: Declaration Matching entry
   ```

2. **Inconsistent route prefix (lines 209-212):** The auto-expand logic only checks for `/tesoreria/` but the Declaration Matching route uses `/treasury/`:
   ```typescript
   if (location.pathname.includes('/tesoreria/')) {
     setTreasuryOpen(true);
   }
   // Missing: check for '/treasury/' path
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

- `frontend/src/components/ui/FKSidebarWithCollapse.tsx` - The sidebar component that renders the department navigation with collapsible submenus. This is where the `treasuryModules` array needs to be updated to include the Declaration Matching menu item, and where the auto-expand logic needs to be updated.
- `frontend/src/App.tsx` - Contains the route definition for `/treasury/declaration-matching` to verify the correct route path.
- `frontend/src/pages/treasury/HistorialMatchingPage.tsx` - The actual page component to understand what icon and naming should be used.
- `.claude/commands/test_e2e.md` - Read to understand how to create an E2E test file.
- `.claude/commands/e2e/test_login.md` - Read as an example of E2E test format.

### New Files
- `.claude/commands/e2e/test_treasury_declaration_matching_menu.md` - E2E test to validate the menu item is visible and clickable.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Read existing files to understand context
- Read `frontend/src/components/ui/FKSidebarWithCollapse.tsx` to understand the current structure
- Read `frontend/src/pages/treasury/HistorialMatchingPage.tsx` to understand the page naming/description

### 2. Add Declaration Matching to treasuryModules array
- In `frontend/src/components/ui/FKSidebarWithCollapse.tsx`, add a new entry to the `treasuryModules` array after the existing entries:
  ```typescript
  {
    id: 'declaration-matching',
    name: 'Coincidencia Declaraciones',
    route: '/treasury/declaration-matching',
    icon: <Assessment fontSize="small" />,
  },
  ```
- Use the `Assessment` icon which is already imported and represents data matching/analysis

### 3. Update auto-expand logic for treasury routes
- In `frontend/src/components/ui/FKSidebarWithCollapse.tsx`, update the useEffect hook that handles auto-expansion to also check for `/treasury/` paths:
  ```typescript
  // Auto-expand treasury if on a treasury route
  if (location.pathname.includes('/tesoreria/') || location.pathname.includes('/treasury/')) {
    setTreasuryOpen(true);
  }
  ```

### 4. Update hasActiveSubmenu check for Treasury
- In the Treasury department section (around line 552), update the `hasActiveSubmenu` check to also include `/treasury/` routes:
  ```typescript
  const hasActiveSubmenu = treasuryModules.some(m => location.pathname === m.route) ||
                           location.pathname.includes('/treasury/');
  ```

### 5. Create E2E test file
- Read `.claude/commands/e2e/test_login.md` and `.claude/commands/test_e2e.md` to understand the E2E test format
- Create a new E2E test file at `.claude/commands/e2e/test_treasury_declaration_matching_menu.md` that:
  1. Logs in as admin user
  2. Expands the Tesorería menu
  3. Verifies "Coincidencia Declaraciones" menu item is visible
  4. Clicks on the menu item
  5. Verifies navigation to `/treasury/declaration-matching`
  6. Verifies the page title "Coincidencia Declaraciones - Historial de Pagos" is visible
  7. Takes screenshots at each key step

### 6. Run validation commands
- Execute all validation commands to ensure the fix works without regressions

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

### Pre-fix verification (to confirm bug exists)
```bash
# Search for 'declaration-matching' in treasuryModules - should return nothing before fix
grep -n "declaration-matching" frontend/src/components/ui/FKSidebarWithCollapse.tsx
```

### Post-fix verification
```bash
# Verify the new menu item was added
grep -n "declaration-matching" frontend/src/components/ui/FKSidebarWithCollapse.tsx

# Verify the auto-expand logic was updated
grep -n "treasury/" frontend/src/components/ui/FKSidebarWithCollapse.tsx
```

### Standard validation commands
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

### E2E Test validation
- Read `.claude/commands/test_e2e.md`, then read and execute the new E2E test `.claude/commands/e2e/test_treasury_declaration_matching_menu.md` to validate the menu item is visible and functional.

## Notes
- The route uses `/treasury/` instead of `/tesoreria/` for consistency with the English-named route pattern. This is intentional based on the existing App.tsx configuration.
- The `Assessment` icon is already imported in FKSidebarWithCollapse.tsx, so no new imports are needed.
- No backend changes are required - this is purely a frontend navigation fix.
- The page component `HistorialMatchingPage` already exists and is working correctly when accessed via direct URL.
