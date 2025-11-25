# Feature: Operations Department Contracts Submenu

## Feature Description
Transform the Operations department menu item from a single direct link to a collapsible submenu structure with country-specific contract request options. This change accommodates future expansion by organizing contract generation functionality by country (Colombia and Mexico), following the same pattern as the Finance department's country-based reporting submenu.

The submenu will feature:
- A collapsible Operations parent menu item that opens to reveal submenu options
- "Contratos Colombia - Solicitar" submenu item linking to the current Colombia contracts functionality
- "Contratos México - Solicitar" submenu item as a placeholder for future Mexico operations
- Visual hierarchy with indentation and connectors matching the Finance submenu pattern
- Auto-expansion when on an operations route
- Proper icon usage and active state indicators
- Consistent styling with the existing Finkargo design system

## User Story
As a **Finkargo operations team member**
I want to **access contract generation tools organized by country**
So that **I can efficiently request contracts for Colombia or Mexico operations without confusion**

## Problem Statement
Currently, the Operations department has a single menu item that directly navigates to the Colombia contracts dashboard. As Finkargo expands operations and plans to add Mexico contract generation functionality, the current flat menu structure is inadequate:

1. No visual organization by country/region for operations workflows
2. Future Mexico contracts would need a separate top-level menu item, cluttering the sidebar
3. Inconsistent with the Finance department's country-based submenu pattern
4. Limited scalability for additional country-specific operations features
5. Users cannot easily distinguish between country-specific operations
6. Navigation structure does not reflect the organizational hierarchy of regional operations

## Solution Statement
Implement a collapsible submenu for the Operations department that:

1. **Creates hierarchical navigation**: Transform Operations into a parent menu item with nested country-specific options
2. **Mirrors Finance pattern**: Apply the same collapsible submenu pattern used by Finance department with expand/collapse icons
3. **Organizes by country**: Separate "Contratos Colombia" and "Contratos México" as distinct submenu items
4. **Maintains current functionality**: Move existing Colombia contracts dashboard to "Contratos Colombia - Solicitar" route
5. **Enables future expansion**: Provides clear structure for adding Mexico contracts and other country-specific operations
6. **Preserves user experience**: Maintains familiar navigation patterns and visual design
7. **Ensures accessibility**: Keyboard navigation, proper focus management, and screen reader support
8. **Follows Clean Architecture**: Changes isolated to UI layer with proper routing updates

The implementation will follow the existing `FKSidebarWithCollapse` pattern used for Finance, ensuring consistency across the application.

## Relevant Files

### Existing Files to Modify

- **`frontend/src/components/ui/FKSidebarWithCollapse.tsx`** (lines 86-338)
  - Contains the sidebar navigation with Finance submenu implementation
  - Currently has hardcoded Finance submenu logic (lines 71-84, 180-291)
  - Needs to add Operations submenu structure similar to Finance
  - Will add `operationsOpen` state for collapse management
  - Will add operations modules array with Colombia and Mexico routes
  - Will add operations-specific click handlers
  - Finance submenu pattern (lines 180-291) serves as template for Operations implementation

- **`frontend/src/App.tsx`** (lines 1-82)
  - Contains route definitions for the application
  - Currently has Operations route at `/department/operations` (lines 64-70)
  - Needs to add new routes:
    - `/operations/contratos-colombia` - Colombia contracts (current functionality)
    - `/operations/contratos-mexico` - Mexico contracts (placeholder)
  - Will preserve existing role protection using `RoleProtectedRoute`
  - Maintains consistency with Finance routes pattern (lines 51-52)

- **`frontend/src/pages/operations/OperationsDashboard.tsx`** (lines 1-169)
  - Current Operations dashboard with tabs for different contract types
  - Will be moved to Colombia-specific route
  - No internal changes needed - just route relocation
  - Component serves Colombia operations exclusively

### New Files to Create

#### **`frontend/src/pages/operations/OperationsContractsColombia.tsx`**
- Colombia-specific contracts dashboard page
- Initially will be identical to current `OperationsDashboard.tsx`
- Contains tabs for:
  - Solicitar Contrato Activos
  - Solicitar Otrosí No. 1
  - Solicitar Inventario Bodega
  - Contratos Aprobados
- Imports existing form components: `FKContractRequest`, `FKOtrosiRequest`, `FKInventarioRequest`, `FKApprovedContracts`
- Uses Material-UI components for layout and tabs
- Follows existing page structure and styling patterns

#### **`frontend/src/pages/operations/OperationsContractsMexico.tsx`**
- Mexico-specific contracts dashboard page (placeholder)
- Similar structure to Colombia page but with:
  - "Próximamente" (Coming Soon) message
  - Information card explaining future functionality
  - Placeholder UI matching Finkargo design system
  - Same layout structure for easy future implementation
- Prepared for future Mexico contracts implementation
- Uses Material-UI Alert or Card components for "coming soon" messaging

## Implementation Plan

### Phase 1: Foundation - Route Structure Setup
Create the new route structure and placeholder pages for country-specific operations. This phase establishes the foundation for the submenu navigation without affecting existing functionality.

**Key Activities:**
- Create Mexico contracts placeholder page with "coming soon" messaging
- Create Colombia contracts page (duplicate of current dashboard)
- Add new routes to App.tsx for both countries
- Verify route protection and role-based access control

**Deliverables:**
- Two new page components: `OperationsContractsColombia.tsx` and `OperationsContractsMexico.tsx`
- Updated routing configuration in `App.tsx`
- Routes properly protected with role guards
- Existing operations functionality accessible via new Colombia route

### Phase 2: Core Implementation - Submenu Navigation
Implement the collapsible submenu in the sidebar, following the Finance department pattern. This phase adds the visual navigation structure and collapse/expand functionality.

**Key Activities:**
- Add operations submenu state management to `FKSidebarWithCollapse`
- Create operations modules array with Colombia and Mexico options
- Implement operations menu item with collapse/expand behavior
- Add submenu items with proper styling and icons
- Configure auto-expansion when on operations routes

**Deliverables:**
- Operations parent menu item with expand/collapse icons
- Two submenu items: "Contratos Colombia - Solicitar" and "Contratos México - Solicitar"
- Visual hierarchy with indentation and connectors
- Working collapse/expand functionality
- Active state indicators for submenu items

### Phase 3: Integration - Cleanup and Verification
Remove or deprecate the old operations route, test all navigation paths, verify role-based access, and ensure consistent behavior across the application.

**Key Activities:**
- Test navigation from sidebar to both country-specific pages
- Verify role-based access control (operations role required)
- Test collapse/expand behavior and persistence
- Validate active state highlighting
- Ensure keyboard navigation and accessibility
- Cross-browser testing

**Deliverables:**
- Fully functional submenu navigation
- Removed or deprecated old operations route
- Verified role protection on all routes
- Accessibility validation passed
- Cross-browser compatibility confirmed

## Step by Step Tasks

### Task 1: Create Mexico Contracts Placeholder Page
- Create file `frontend/src/pages/operations/OperationsContractsMexico.tsx`
- Import necessary Material-UI components: `Box`, `Typography`, `Card`, `CardContent`, `Alert`
- Import icons: `Construction` or `Schedule` for "coming soon" indicator
- Implement component structure:
  - Header section with title "Contratos México - Solicitar"
  - Subtitle explaining this is for Mexico operations
  - Alert or Card component with "Próximamente" message
  - Information about planned functionality
- Add styling consistent with existing operations pages:
  - Use Finkargo color palette (info.50 background, info.main accent)
  - Match typography styles from other dashboard pages
  - Responsive layout with proper spacing
- Export component as default
- Add TypeScript type annotations

### Task 2: Create Colombia Contracts Page (Refactored)
- Create file `frontend/src/pages/operations/OperationsContractsColombia.tsx`
- Copy entire content from `frontend/src/pages/operations/OperationsDashboard.tsx`
- Update component name from `OperationsDashboard` to `OperationsContractsColombia`
- Update header title to "Contratos Colombia - Solicitar" (change from "Departamento de Operaciones")
- Update subtitle to "Solicitud de contratos para operaciones en Colombia"
- Keep all existing tabs and functionality:
  - Solicitar Contrato Activos
  - Solicitar Otrosí No. 1
  - Solicitar Inventario Bodega
  - Contratos Aprobados
- Maintain all imports and form component references
- Export component as default
- Verify TypeScript compilation

### Task 3: Add Operations Routes to App.tsx
- Open `frontend/src/App.tsx`
- Import new page components at top of file:
  ```typescript
  import OperationsContractsColombia from './pages/operations/OperationsContractsColombia';
  import OperationsContractsMexico from './pages/operations/OperationsContractsMexico';
  ```
- Add new routes after Finance routes (around line 53):
  ```typescript
  {/* Operations Routes - Country-specific contracts */}
  <Route path="operations/contratos-colombia" element={<OperationsContractsColombia />} />
  <Route path="operations/contratos-mexico" element={<OperationsContractsMexico />} />
  ```
- Note: Routes should NOT be wrapped in `RoleProtectedRoute` at this level since the parent `FKMainLayout` already handles authentication
- The existing `/department/operations` route (lines 64-70) can remain temporarily for backward compatibility
- Verify route paths match the structure used by Finance routes
- Save file and verify TypeScript compilation

### Task 4: Define Operations Submenu Structure
- Open `frontend/src/components/ui/FKSidebarWithCollapse.tsx`
- After the `financeModules` array definition (around line 84), add operations modules:
  ```typescript
  // Operations sub-modules (direct navigation, country-specific contracts)
  interface OperationsModule {
    id: string;
    name: string;
    route: string;
    icon: React.ReactElement;
    badge?: string;
  }

  const operationsModules: OperationsModule[] = [
    {
      id: 'contratos-colombia',
      name: 'Contratos Colombia - Solicitar',
      route: '/operations/contratos-colombia',
      icon: <Description fontSize="small" />,
    },
    {
      id: 'contratos-mexico',
      name: 'Contratos México - Solicitar',
      route: '/operations/contratos-mexico',
      icon: <Description fontSize="small" />,
      badge: 'Próximo',
    },
  ];
  ```
- Ensure `Description` icon is already imported (it is, line 30)
- Add TypeScript interface matching the pattern of `FinanceModule`

### Task 5: Add Operations Collapse State Management
- In `FKSidebarWithCollapse` component (around line 93, after `financeOpen` state):
  ```typescript
  const [operationsOpen, setOperationsOpen] = useState(false);
  ```
- Update the `useEffect` to auto-expand operations when on operations route (around line 100):
  ```typescript
  useEffect(() => {
    loadDepartments();

    // Auto-expand finance if on a finance route
    if (location.pathname.includes('/finance/')) {
      setFinanceOpen(true);
    }

    // Auto-expand operations if on an operations route
    if (location.pathname.includes('/operations/')) {
      setOperationsOpen(true);
    }
  }, [location.pathname]);
  ```
- Add operations toggle handler after `handleFinanceToggle` (around line 134):
  ```typescript
  const handleOperationsToggle = () => {
    setOperationsOpen(!operationsOpen);
  };
  ```
- Add operations module click handler after `handleFinanceModuleClick` (around line 138):
  ```typescript
  const handleOperationsModuleClick = (route: string) => {
    navigate(route);
  };
  ```

### Task 6: Implement Operations Submenu in Sidebar
- In the departments map loop (around line 178), add special handling for Operations similar to Finance
- Find where Finance special handling ends (around line 293)
- Add Operations special handling immediately after Finance and before regular departments:
  ```typescript
  // Special handling for Operations department (has submenu)
  if (department.id === 'operations') {
    const hasActiveSubmenu = operationsModules.some(m => location.pathname === m.route);
    return (
      <React.Fragment key={department.id}>
        <ListItem disablePadding sx={{ mb: 0.5 }}>
          <ListItemButton
            onClick={handleOperationsToggle}
            sx={{
              borderRadius: 2,
              py: 1.5,
              backgroundColor: 'transparent',
              color: hasActiveSubmenu ? 'primary.main' : 'text.primary',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          >
            <ListItemIcon
              sx={{
                color: hasActiveSubmenu ? 'primary.main' : 'primary.main',
                minWidth: 40,
              }}
            >
              {iconMap[department.icon] || <Settings />}
            </ListItemIcon>
            <ListItemText
              primary={department.name}
              primaryTypographyProps={{
                fontWeight: hasActiveSubmenu ? 600 : 500,
                fontSize: '0.95rem',
              }}
            />
            {operationsOpen ? (
              <ExpandLess sx={{ color: 'text.secondary' }} />
            ) : (
              <ExpandMore sx={{ color: 'text.secondary' }} />
            )}
          </ListItemButton>
        </ListItem>

        {/* Operations Modules Submenu */}
        <Collapse in={operationsOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding sx={{ position: 'relative' }}>
            {/* Visual separator/connector for hierarchy */}
            <Box
              sx={{
                position: 'absolute',
                left: 20,
                top: 0,
                bottom: 0,
                width: '2px',
                backgroundColor: 'divider',
              }}
            />
            {operationsModules.map((module) => {
              const isModuleActive = location.pathname === module.route;
              return (
                <ListItem key={module.id} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => handleOperationsModuleClick(module.route)}
                    sx={{
                      pl: 7,
                      pr: 2,
                      borderRadius: 2,
                      ml: 1,
                      py: 1,
                      backgroundColor: isModuleActive ? 'primary.main' : 'transparent',
                      color: isModuleActive ? 'white' : 'text.secondary',
                      '&:hover': {
                        backgroundColor: isModuleActive ? 'primary.dark' : 'action.hover',
                      },
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        color: isModuleActive ? 'white' : 'text.disabled',
                        minWidth: 32,
                      }}
                    >
                      {module.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={module.name}
                      primaryTypographyProps={{
                        fontWeight: isModuleActive ? 600 : 500,
                        fontSize: '0.8125rem',
                      }}
                    />
                    {module.badge && (
                      <Typography
                        variant="caption"
                        sx={{
                          backgroundColor: 'coral.main',
                          color: 'white',
                          px: 1,
                          py: 0.25,
                          borderRadius: 1,
                          fontSize: '0.625rem',
                          fontWeight: 600,
                        }}
                      >
                        {module.badge}
                      </Typography>
                    )}
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </Collapse>
      </React.Fragment>
    );
  }
  ```
- This code mirrors the Finance submenu implementation for consistency
- Ensure proper indentation and formatting

### Task 7: Remove Old Operations Route (Optional Backward Compatibility)
- Open `frontend/src/App.tsx`
- Locate the old Operations route (lines 64-70):
  ```typescript
  <Route
    path="department/operations"
    element={
      <RoleProtectedRoute allowedRoles={[UserRole.OPERATIONS]}>
        <OperationsDashboard />
      </RoleProtectedRoute>
    }
  />
  ```
- Option 1 (Recommended for backward compatibility): Add redirect to Colombia route:
  ```typescript
  <Route
    path="department/operations"
    element={<Navigate to="/operations/contratos-colombia" replace />}
  />
  ```
- Option 2 (Clean removal): Delete the route entirely if no users are bookmarked or linked to old path
- If choosing Option 1, keep for 1-2 months then remove in future update
- Document the change in implementation notes

### Task 8: Update Operations Dashboard Export (Cleanup)
- Open `frontend/src/pages/operations/OperationsDashboard.tsx`
- This file is now deprecated since Colombia page replaces it
- Option 1: Keep file and add deprecation comment at top:
  ```typescript
  /**
   * @deprecated This component has been replaced by OperationsContractsColombia.tsx
   * Kept for backward compatibility. Will be removed in future version.
   * Operations Department Dashboard
   * Request contracts and download approved contracts for customer signature
   */
  ```
- Option 2: Delete file entirely (after verifying no imports remain)
- Recommended: Keep file with deprecation notice for one release cycle

### Task 9: Test Navigation and Routing
- Start development server: `cd frontend && npm run dev`
- Open browser to `http://localhost:5173`
- Log in with operations role credentials
- Manual testing checklist:
  - [ ] Click Operations menu item - should expand/collapse submenu
  - [ ] Verify expand/collapse icon changes (ExpandMore/ExpandLess)
  - [ ] Click "Contratos Colombia - Solicitar" - should navigate to Colombia page
  - [ ] Verify Colombia page displays all 4 tabs correctly
  - [ ] Verify active state highlighting on Colombia submenu item
  - [ ] Click "Contratos México - Solicitar" - should navigate to Mexico page
  - [ ] Verify Mexico page shows "Próximamente" message
  - [ ] Verify active state highlighting on Mexico submenu item
  - [ ] Navigate to another department, then back to Operations
  - [ ] Verify Operations submenu auto-expands when on operations route
  - [ ] Refresh page while on Colombia route - verify submenu stays expanded
  - [ ] Test keyboard navigation (Tab to menu items, Enter to activate)
- Document any issues found

### Task 10: Test Role-Based Access Control
- Test with different user roles:
  - **Operations role**: Should see Operations menu item and access all operations pages
  - **Admin role**: Should see all menu items including Operations
  - **Legal role**: Should NOT see Operations menu item (verify access control)
  - **Cliente role**: Should NOT see Operations menu item
- Verify direct URL access is properly protected:
  - Try accessing `/operations/contratos-colombia` with non-operations user
  - Should be blocked or redirected appropriately
- Test route protection on both Colombia and Mexico pages
- Verify console shows no access control errors

### Task 11: Visual and Styling Verification
- Compare Operations submenu styling with Finance submenu:
  - [ ] Indentation matches (pl: 7 for submenu items)
  - [ ] Icon size and color consistent
  - [ ] Active state colors match
  - [ ] Hover states work correctly
  - [ ] Badge styling matches (if applicable)
  - [ ] Vertical connector line displays properly
  - [ ] Font sizes consistent (0.8125rem for submenu items)
  - [ ] Spacing between items matches
- Test in both light and dark modes (if dark mode implemented)
- Verify on different screen sizes:
  - Desktop (1920px)
  - Tablet (768px)
  - Mobile (375px)
- Check for any text overflow or truncation issues

### Task 12: Accessibility Testing
- Test keyboard navigation:
  - [ ] Tab key navigates through menu items in correct order
  - [ ] Enter key expands/collapses Operations menu
  - [ ] Enter key navigates to submenu items
  - [ ] Focus indicators are clearly visible
  - [ ] Escape key closes submenu (if implemented)
- Test with screen reader (VoiceOver on Mac, NVDA on Windows):
  - [ ] Operations menu announces as expandable
  - [ ] Submenu items are announced correctly
  - [ ] Active state is announced
  - [ ] Badge text ("Próximo") is read by screen reader
- Verify ARIA attributes if present:
  - `aria-expanded` on Operations menu button
  - Proper role attributes on menu items
  - Accessible names for icon buttons

### Task 13: Browser Compatibility Testing
- Test in multiple browsers:
  - [ ] Chrome/Chromium (latest)
  - [ ] Firefox (latest)
  - [ ] Safari (latest)
  - [ ] Edge (latest)
- Verify on both desktop and mobile browsers:
  - [ ] iOS Safari
  - [ ] Chrome Mobile
  - [ ] Firefox Mobile
- Check for any browser-specific styling issues
- Verify collapse/expand animation works in all browsers
- Test navigation and routing in each browser

### Task 14: TypeScript Compilation and Linting
- Run TypeScript compiler to check for type errors:
  ```bash
  cd frontend && npx tsc --noEmit
  ```
- Fix any TypeScript errors that appear
- Run ESLint to check code quality:
  ```bash
  cd frontend && npm run lint
  ```
- Fix any linting errors or warnings
- Verify all new code follows existing patterns:
  - Proper type annotations
  - No `any` types used
  - Consistent naming conventions
  - JSDoc comments where appropriate

### Task 15: Production Build Verification
- Build frontend for production:
  ```bash
  cd frontend && npm run build
  ```
- Verify build completes with no errors
- Check bundle size hasn't increased significantly:
  ```bash
  du -sh frontend/dist/
  ```
- Preview production build:
  ```bash
  cd frontend && npm run preview
  ```
- Test navigation in production build preview
- Verify no console errors in production mode

### Task 16: Run Validation Commands
- Execute all validation commands listed in the Validation Commands section below
- Fix any errors or warnings that appear
- Re-run commands until all pass successfully
- Document any issues found during validation
- Verify zero regressions in existing functionality:
  - Finance submenu still works correctly
  - Legal department navigation unaffected
  - Login/logout functionality works
  - Theme toggle works (if implemented)
  - All other navigation paths function properly

## Testing Strategy

### Unit Tests
**Note**: The frontend currently has no testing framework configured. Unit tests are recommended for future work but are not part of this implementation.

Recommended unit tests for future implementation:
- **Operations Submenu Rendering**:
  - Test Operations menu item renders with correct icon and text
  - Test submenu items render when expanded
  - Test Colombia and Mexico submenu items have correct routes
  - Test badge renders on Mexico item with "Próximo" text

- **Collapse State Management**:
  - Test `operationsOpen` state toggles correctly on click
  - Test submenu auto-expands when on operations route
  - Test submenu closes when clicking parent again
  - Test state persists during navigation within operations

- **Route Navigation**:
  - Test clicking Colombia submenu navigates to correct route
  - Test clicking Mexico submenu navigates to correct route
  - Test active state highlights correct submenu item based on route
  - Test backward compatibility redirect from old route

### Integration Tests
**Note**: Integration tests are recommended for future work but are not part of this implementation.

Recommended integration tests for future implementation:
- **Full Navigation Flow**:
  - Test expanding Operations menu and navigating to Colombia page
  - Test Colombia page displays correct content and tabs
  - Test navigating from Colombia to Mexico page
  - Test Mexico page displays "coming soon" message
  - Test returning to Operations menu maintains submenu state

- **Role-Based Access**:
  - Test operations role can access Operations submenu
  - Test admin role can access Operations submenu
  - Test legal role cannot see Operations menu item
  - Test direct URL access is protected by role

- **Cross-Module Navigation**:
  - Test navigating between Operations and Finance submenus
  - Test collapsing one submenu doesn't affect the other
  - Test active states clear when navigating away from operations

### Manual Testing Checklist

**Functional Testing**:
- [ ] Operations menu item displays in sidebar
- [ ] Clicking Operations toggles expand/collapse
- [ ] Expand icon changes to collapse icon when open
- [ ] Colombia submenu item navigates to correct page
- [ ] Mexico submenu item navigates to correct page
- [ ] Colombia page displays all tabs and forms correctly
- [ ] Mexico page displays "coming soon" message
- [ ] Active state highlights correct submenu item
- [ ] Submenu auto-expands when on operations route
- [ ] Page refresh maintains submenu expanded state
- [ ] Keyboard navigation works (Tab, Enter)
- [ ] No console errors during navigation

**Visual Testing**:
- [ ] Submenu indentation matches Finance submenu
- [ ] Icons display correctly and are properly sized
- [ ] Text is readable and properly sized
- [ ] Badge on Mexico item displays correctly
- [ ] Vertical connector line displays properly
- [ ] Active state uses correct colors (primary.main background, white text)
- [ ] Hover states work on all menu items
- [ ] Focus indicators are visible
- [ ] Spacing between items is consistent
- [ ] Responsive design works on mobile/tablet/desktop
- [ ] Dark mode styling works (if implemented)

**Accessibility Testing**:
- [ ] Screen reader announces Operations as expandable
- [ ] Submenu items are read correctly by screen reader
- [ ] Active state is announced
- [ ] Badge text is read by screen reader
- [ ] Focus indicators meet contrast requirements
- [ ] Keyboard navigation is logical and complete
- [ ] ARIA attributes are present and correct

**Role-Based Access Testing**:
- [ ] Operations role can access Operations submenu
- [ ] Admin role can access Operations submenu
- [ ] Legal role cannot see Operations menu item
- [ ] Cliente role cannot see Operations menu item
- [ ] Direct URL access to Colombia page is protected
- [ ] Direct URL access to Mexico page is protected

**Cross-Browser Testing**:
- [ ] Chrome: All features work correctly
- [ ] Firefox: All features work correctly
- [ ] Safari: All features work correctly
- [ ] Edge: All features work correctly
- [ ] Mobile Safari: All features work correctly
- [ ] Chrome Mobile: All features work correctly

### Edge Cases

1. **Direct URL Access to Old Route**:
   - **Scenario**: User has bookmarked old `/department/operations` URL
   - **Expected**: Redirects to `/operations/contratos-colombia` seamlessly
   - **Handling**: Use `<Navigate>` component for redirect

2. **Submenu Open State During Page Refresh**:
   - **Scenario**: User refreshes page while on Colombia contracts page
   - **Expected**: Operations submenu auto-expands on page load
   - **Handling**: `useEffect` checks `location.pathname` on mount

3. **Multiple Submenus Open Simultaneously**:
   - **Scenario**: User expands Operations submenu while Finance submenu is open
   - **Expected**: Both can be open simultaneously, independent state management
   - **Handling**: Separate state variables (`financeOpen`, `operationsOpen`)

4. **Navigation to Non-Existent Route**:
   - **Scenario**: User manually enters invalid operations route in URL
   - **Expected**: App redirects to home or 404 page
   - **Handling**: Catch-all route in App.tsx handles invalid paths

5. **Role Change During Active Session**:
   - **Scenario**: User's role is changed by admin while they're logged in
   - **Expected**: Sidebar updates on next navigation or page refresh
   - **Note**: Current implementation requires re-login for role changes to take effect

6. **Mexico Page Accessed Before Implementation**:
   - **Scenario**: User clicks Mexico submenu item (placeholder)
   - **Expected**: Clear "coming soon" message with expected timeline
   - **Handling**: OperationsContractsMexico.tsx displays informative placeholder

7. **Rapid Collapse/Expand Clicking**:
   - **Scenario**: User clicks Operations menu item multiple times quickly
   - **Expected**: Smooth animation, no visual glitches or state errors
   - **Handling**: Material-UI Collapse component handles animation queueing

8. **Deep Linking with Submenu Closed**:
   - **Scenario**: User receives link to `/operations/contratos-colombia` and opens it
   - **Expected**: Submenu auto-expands to show active route
   - **Handling**: `useEffect` dependency on `location.pathname` ensures auto-expansion

9. **Browser Back Button Navigation**:
   - **Scenario**: User navigates Colombia → Mexico → uses back button
   - **Expected**: Returns to Colombia with correct active state highlighting
   - **Handling**: React Router manages history, active state derives from location

10. **Accessibility with High Contrast Mode**:
    - **Scenario**: User has OS-level high contrast mode enabled
    - **Expected**: Menu items and submenu structure remain visible and usable
    - **Handling**: Use theme palette references, not hardcoded colors

## Acceptance Criteria

### Core Functionality
- [ ] **Submenu Structure**: Operations appears as collapsible parent menu item with two submenu items
- [ ] **Colombia Route**: "Contratos Colombia - Solicitar" navigates to Colombia contracts page with all existing functionality
- [ ] **Mexico Route**: "Contratos México - Solicitar" navigates to Mexico placeholder page with clear messaging
- [ ] **Expand/Collapse**: Clicking Operations menu item toggles submenu visibility with appropriate icon change
- [ ] **Auto-Expansion**: Submenu automatically expands when user is on any operations route

### Visual Quality
- [ ] **Consistent Styling**: Operations submenu matches Finance submenu visual pattern exactly
- [ ] **Proper Indentation**: Submenu items indented with pl: 7, consistent spacing
- [ ] **Icon Usage**: Description icons used for both submenu items, properly sized
- [ ] **Active State**: Current route highlighted with primary.main background and white text
- [ ] **Vertical Connector**: Subtle divider line connects submenu items to parent
- [ ] **Badge Display**: "Próximo" badge displays on Mexico item with coral background

### Accessibility
- [ ] **Keyboard Navigation**: Full keyboard control with Tab and Enter keys
- [ ] **Focus Indicators**: Clear focus states visible on all interactive elements
- [ ] **Screen Reader Support**: Proper announcement of expandable menu and submenu items
- [ ] **ARIA Attributes**: Correct aria-expanded state on collapsible menu item
- [ ] **Color Contrast**: All text meets WCAG AA contrast requirements (4.5:1)

### Technical Requirements
- [ ] **TypeScript Compliance**: All new code fully typed, no `any` types used
- [ ] **No Breaking Changes**: Existing functionality unaffected by changes
- [ ] **Role Protection**: Access control enforced for operations routes
- [ ] **Clean Architecture**: Changes isolated to UI layer (pages, components, routing)
- [ ] **No Console Errors**: No errors or warnings in browser console
- [ ] **Production Build**: Frontend builds successfully with no errors

### User Experience
- [ ] **Intuitive Navigation**: Operations submenu obvious and easy to use
- [ ] **Clear Country Labels**: "Colombia" and "México" clearly distinguished
- [ ] **Backward Compatibility**: Old operations route redirects gracefully
- [ ] **Placeholder Messaging**: Mexico page clearly indicates future functionality
- [ ] **Responsive Design**: Submenu works correctly on mobile, tablet, and desktop
- [ ] **Performance**: Navigation and collapse/expand animations are smooth

### Code Quality
- [ ] **Code Documentation**: All new components and functions have comments
- [ ] **Consistent Patterns**: Implementation follows existing sidebar pattern
- [ ] **Reusable Structure**: Easy to add future country-specific operations modules
- [ ] **Proper Imports**: All imports organized and unused imports removed
- [ ] **ESLint Compliance**: Code passes linting with no errors or warnings

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# TypeScript compilation check
npx tsc --noEmit
# Expected: No TypeScript errors

# ESLint code quality check
npm run lint
# Expected: No linting errors or warnings

# Production build validation
npm run build
# Expected: Build completes successfully with no errors

# Check bundle size
du -sh dist/
# Expected: Similar size to previous build (< 5% increase)

# Start development server
npm run dev
# Opens http://localhost:5173

# Manual end-to-end validation flow:
# 1. Open http://localhost:5173 in browser
# 2. Log in with operations role credentials
# 3. Locate Operations menu item in sidebar
# 4. Verify Operations menu displays with collapse icon (ExpandMore)
# 5. Click Operations menu item
# 6. Verify submenu expands with two items:
#    - "Contratos Colombia - Solicitar"
#    - "Contratos México - Solicitar" (with "Próximo" badge)
# 7. Verify expand icon changes to collapse icon (ExpandLess)
# 8. Click "Contratos Colombia - Solicitar"
# 9. Verify navigation to Colombia contracts page (/operations/contratos-colombia)
# 10. Verify all 4 tabs display correctly:
#     - Solicitar Contrato Activos
#     - Solicitar Otrosí No. 1
#     - Solicitar Inventario Bodega
#     - Contratos Aprobados
# 11. Verify Colombia submenu item has active state (blue background, white text)
# 12. Verify existing contract request functionality works
# 13. Click "Contratos México - Solicitar" in sidebar
# 14. Verify navigation to Mexico placeholder page (/operations/contratos-mexico)
# 15. Verify "Próximamente" message displays clearly
# 16. Verify Mexico submenu item has active state
# 17. Refresh page (Cmd/Ctrl+R)
# 18. Verify Operations submenu remains expanded
# 19. Verify Mexico item still shows active state
# 20. Click Operations menu item to collapse
# 21. Verify submenu collapses smoothly
# 22. Navigate to Finance department
# 23. Verify Finance submenu works independently
# 24. Navigate back to Operations
# 25. Verify Operations submenu works correctly
# 26. Test keyboard navigation:
#     - Tab to Operations menu item
#     - Press Enter to expand
#     - Tab to Colombia submenu item
#     - Press Enter to navigate
# 27. Verify no console errors during any navigation

# Accessibility validation using Lighthouse
# In Chrome DevTools:
# 1. Open DevTools (F12)
# 2. Go to Lighthouse tab
# 3. Select "Accessibility" category
# 4. Run audit on operations pages
# 5. Verify Accessibility score is 90+

# Cross-browser testing
# Repeat manual validation flow in:
# - Firefox (latest)
# - Safari (latest)
# - Edge (latest)

# Role-based access testing
# Test with different user roles:
# - Operations role: Should see and access Operations submenu
# - Admin role: Should see and access Operations submenu
# - Legal role: Should NOT see Operations menu item
# - Cliente role: Should NOT see Operations menu item

# Direct URL access testing
# While logged in as non-operations user:
# - Try accessing /operations/contratos-colombia directly
# - Verify appropriate access control (redirect or error)
# - Try accessing /operations/contratos-mexico directly
# - Verify appropriate access control

# Backward compatibility testing
# - Navigate to /department/operations (old route)
# - Verify redirect to /operations/contratos-colombia
# - Verify no console errors during redirect

# Preview production build
npm run preview
# Opens http://localhost:4173
# Repeat key manual tests in production build

# Visual regression testing
# Take screenshots of:
# - Operations menu collapsed
# - Operations menu expanded
# - Colombia page active state
# - Mexico page active state
# Compare with Finance submenu for consistency
```

## Notes

### Future Enhancements
1. **Mexico Contracts Implementation**: When ready to implement Mexico functionality, simply:
   - Update `OperationsContractsMexico.tsx` with actual contract forms
   - Remove "Próximo" badge from submenu
   - Add Mexico-specific backend routes and services
   - Update documentation

2. **Additional Countries**: Structure supports easy addition of more countries:
   - Add new route to `operationsModules` array
   - Create country-specific page component
   - Add route to `App.tsx`
   - No changes needed to collapse logic

3. **Country-Specific Features**: Future operations features can be nested under each country:
   - Add third level of nesting for specific workflow types
   - Example: Colombia → Contratos, Colombia → Manifiestos, etc.

4. **Cross-Country Reports**: Could add Operations submenu item for:
   - "Reportes Consolidados" - Combined reports across all countries
   - "Comparativa Regional" - Cross-country analytics

5. **Quick Access Links**: Add "Recently Used" section in Operations submenu showing last 3 accessed contracts

6. **Role-Based Submenu Filtering**: Show only country-specific options based on user's regional role

### Technical Considerations
- **No Backend Changes Needed**: This is purely a frontend routing and navigation change
- **No Database Changes Needed**: No new tables or migrations required
- **State Management**: Uses local component state, no global state needed
- **Performance**: Submenu collapse animations are CSS-based, very performant
- **Bundle Size**: Adds minimal code (~200 lines), negligible bundle size impact
- **Browser Support**: Collapse component works in all modern browsers
- **Accessibility**: Material-UI Collapse component has built-in accessibility support

### Design Decisions
- **Submenu Pattern**: Chose to mirror Finance department pattern for consistency and familiarity
- **Country Labels**: Used "Colombia" and "México" with country names to be explicit and clear
- **"Solicitar" Suffix**: Added "Solicitar" to clarify these are request/creation pages, not reports
- **Badge Text**: "Próximo" (not "Próximamente") for conciseness while maintaining clarity
- **Badge Color**: Used coral.main to match Finkargo's CTA/accent color for prominence
- **Route Structure**: `/operations/contratos-{country}` pattern is RESTful and scalable
- **Placeholder Approach**: Created full placeholder page (not just alert) for consistent layout
- **Backward Compatibility**: Kept old route with redirect to avoid breaking existing bookmarks/links

### Development Tips
- Use Firefox DevTools to inspect Material-UI theme values during development
- Test collapse animation timing in browser DevTools Performance tab if issues arise
- Verify TypeScript compilation frequently during development to catch type errors early
- Use React DevTools to inspect component state and props during navigation testing
- Test on actual mobile device, not just responsive mode, for best submenu UX validation

### Known Limitations
- **Mexico Functionality**: Mexico page is placeholder only, no actual functionality yet
- **Role Granularity**: Current role system doesn't distinguish between Colombia and Mexico operations roles
- **No Recent Items**: Submenu doesn't track or display recently accessed items
- **No Favorites**: Users cannot mark frequently used operations as favorites
- **Single Session**: Submenu open/closed state not persisted across sessions (could add localStorage)

### Dependencies
- No new npm packages required
- Uses existing Material-UI components (Collapse, List, ListItem, etc.)
- Leverages React Router for navigation
- Uses existing icon library (Material-UI Icons)

### Migration Notes
- This is a non-breaking change with backward compatibility redirect
- Existing users will see new submenu structure on next login
- Old bookmarks will redirect automatically to new Colombia route
- No user training needed - pattern already familiar from Finance department
- Can announce change with in-app notification: "Operaciones ahora organizado por país"

### Maintenance Considerations
- When adding Mexico functionality, remove "Próximo" badge and update placeholder page
- Consider removing backward compatibility redirect after 2-3 months
- Update any external documentation or training materials with new routes
- Monitor analytics to see if users prefer submenu structure over old flat navigation
- Review user feedback on submenu organization for future improvements

### Related Documentation
- See `CLAUDE.md` for overall project architecture and coding standards
- See `frontend/src/components/ui/FKSidebarWithCollapse.tsx` for Finance submenu reference
- See `frontend/src/App.tsx` for routing patterns
- See Finance department implementation (Reportería Automática) as pattern reference

### Testing Evidence
After implementation, capture screenshots for documentation:
1. Operations submenu collapsed (default state)
2. Operations submenu expanded (showing both items)
3. Colombia page active state
4. Mexico page with placeholder message
5. Mobile view of submenu
6. Dark mode submenu (if applicable)
