# Feature: Add Tesorería Department Menu

## Feature Description
Add a new "Tesorería" (Treasury) department to the sidebar navigation menu with a collapsible tree structure, similar to the existing Finance department. The Treasury department will initially have a single sub-menu item for "Plantillas para Cargar NetSuite" (NetSuite Upload Templates) functionality.

## User Story
As a Treasury department user (Tesorería role)
I want to access a dedicated Treasury section in the sidebar menu
So that I can navigate to Treasury-specific tools like NetSuite upload templates

## Problem Statement
The Finkargo Automation Hub currently lacks a dedicated Treasury department menu. Treasury users need a specific section in the navigation to access their tools, particularly for uploading templates to NetSuite. The current sidebar supports collapsible menus for Finance and Operations but has no Treasury option.

## Solution Statement
Extend the `FKSidebarWithCollapse` component to include a new "Tesorería" department with:
1. A collapsible parent menu item with an appropriate icon
2. A nested sub-menu item "Plantillas para Cargar NetSuite"
3. A corresponding page component for the NetSuite templates functionality
4. Proper routing in App.tsx to handle the new routes
5. Follow the same pattern as Finance modules for consistency

## Access Control
- Required Role(s): `admin`, `tesoreria` (new role to be added), or general `user` with treasury access
- Backend Protection: Use RBAC dependency `require_roles(['admin', 'tesoreria'])` for treasury-specific endpoints
- Frontend Protection: For now, all authenticated users can see the menu (access control at route level as per current pattern)

## Relevant Files
Use these files to implement the feature:

- **`frontend/src/components/ui/FKSidebarWithCollapse.tsx`** - Main sidebar component that needs to be extended with the new Treasury department menu and sub-menu. Contains the pattern for Finance and Operations collapsible menus that should be followed.

- **`frontend/src/App.tsx`** - Main routing configuration where the new Treasury routes need to be added.

- **`frontend/src/pages/finance/ReporteriaAutomaticaCO.tsx`** - Reference page component to understand the page structure and styling patterns for Treasury pages.

- **`frontend/src/types/index.ts`** - TypeScript types, may need a new role type if adding `tesoreria` role.

- **`.claude/commands/test_e2e.md`** - E2E test runner instructions for creating the new E2E test.

- **`.claude/commands/e2e/test_login.md`** - Example E2E test file to follow the format for the new Treasury menu test.

### New Files

- **`frontend/src/pages/tesoreria/PlantillasNetSuite.tsx`** - New page component for the NetSuite templates upload functionality

- **`.claude/commands/e2e/test_tesoreria_menu.md`** - E2E test file to validate the Treasury menu navigation works correctly

## Implementation Plan

### Phase 1: Foundation
- Add "Tesorería" department to the mock departments list in sidebar
- Add Treasury icon to the icon mapping (use `AccountBalance` for Treasury/Treasury theme)
- Define the Treasury modules interface and data structure

### Phase 2: Core Implementation
- Update `FKSidebarWithCollapse.tsx` to handle the new Treasury department with collapsible submenu
- Create the `PlantillasNetSuite.tsx` page component with placeholder content
- Add routes in `App.tsx` for the treasury paths

### Phase 3: Integration
- Add state management for treasury menu collapse/expand
- Ensure auto-expand behavior when navigating to treasury routes
- Test navigation flow and visual consistency with other departments

## Step by Step Tasks

### Step 1: Create the E2E test file for Treasury menu validation
- Read `.claude/commands/test_e2e.md` to understand the E2E test format
- Read `.claude/commands/e2e/test_login.md` for a reference E2E test file
- Create `.claude/commands/e2e/test_tesoreria_menu.md` with test steps to validate:
  - Treasury menu appears in sidebar
  - Treasury menu expands when clicked
  - Sub-menu item "Plantillas para Cargar NetSuite" is visible
  - Clicking sub-menu navigates to correct route
  - Page loads correctly

### Step 2: Update the Sidebar with Treasury Department
- Open `frontend/src/components/ui/FKSidebarWithCollapse.tsx`
- Add `AccountBalance` icon import from `@mui/icons-material`
- Add `'tesoreria'` to the mockDepartments array with name "Tesorería" and icon "AccountBalance"
- Add `AccountBalance` to the iconMap
- Create `TreasuryModule` interface (copy from `FinanceModule`)
- Create `treasuryModules` array with the sub-menu item:
  ```typescript
  {
    id: 'plantillas-netsuite',
    name: 'Plantillas para Cargar NetSuite',
    route: '/tesoreria/plantillas-netsuite',
    icon: <Description fontSize="small" />,
  }
  ```
- Add `treasuryOpen` state variable for collapse control
- Add `handleTreasuryToggle` function
- Add `handleTreasuryModuleClick` function
- Update useEffect to auto-expand treasury menu when on `/tesoreria/` routes
- Add special handling block for `department.id === 'tesoreria'` (follow the Finance pattern exactly)

### Step 3: Create the PlantillasNetSuite Page Component
- Create directory `frontend/src/pages/tesoreria/` if it doesn't exist
- Create `frontend/src/pages/tesoreria/PlantillasNetSuite.tsx`
- Use `ReporteriaAutomaticaCO.tsx` as a template for structure and styling
- Include:
  - Header with Treasury icon and title "Plantillas para Cargar NetSuite"
  - Subtitle: "Gestión de plantillas para carga masiva en NetSuite"
  - Placeholder card for upload functionality (future implementation)
  - Placeholder card for template history/list (future implementation)

### Step 4: Update App.tsx with Treasury Routes
- Open `frontend/src/App.tsx`
- Add import for the new `PlantillasNetSuite` component
- Add route inside the protected routes section:
  ```tsx
  {/* Treasury Routes - Plantillas NetSuite */}
  <Route path="tesoreria/plantillas-netsuite" element={<PlantillasNetSuite />} />
  ```

### Step 5: Run Validation Commands
- Execute all validation commands to ensure zero regressions:
  - Backend pytest
  - Backend linting
  - Frontend linting
  - TypeScript type check
  - Frontend build
  - E2E test for treasury menu

## Testing Strategy

### Unit Tests
- No backend changes required for this feature, so no new backend tests needed
- Frontend: Manual testing via E2E test file

### Edge Cases
- Ensure treasury menu collapses when clicking other department menus
- Verify treasury menu expands when directly navigating to a treasury route
- Test that menu styling is consistent with Finance and Operations menus

## Acceptance Criteria
1. "Tesorería" appears in the sidebar menu with an appropriate icon (AccountBalance)
2. Clicking "Tesorería" expands/collapses the submenu (toggle behavior)
3. "Plantillas para Cargar NetSuite" sub-item is visible when expanded
4. Clicking the sub-item navigates to `/tesoreria/plantillas-netsuite`
5. The PlantillasNetSuite page loads with appropriate header and placeholder content
6. Menu auto-expands when user is on a treasury route
7. Visual styling matches Finance and Operations submenus exactly
8. All existing functionality remains working (zero regressions)
9. All linting and TypeScript checks pass
10. Production build succeeds

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `cd backend && python -m pytest` - Run backend tests to validate with zero regressions
- `cd backend && ruff check src/` - Run backend linting
- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_tesoreria_menu.md` E2E test file to validate the Treasury menu navigation works correctly

## Notes
- The Treasury department follows the exact same pattern as Finance and Operations departments in the sidebar
- The `AccountBalance` icon from Material UI is appropriate for Treasury/financial department theming
- Future enhancements may include:
  - Adding more sub-menu items under Tesorería
  - Implementing actual NetSuite template upload functionality
  - Adding role-based access control with a dedicated `tesoreria` role
- The placeholder page provides a foundation for future Treasury module development
