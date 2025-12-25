# E2E Test: Tesorería Menu Navigation

Test the Treasury (Tesorería) department menu navigation in the Finkargo Automation Hub sidebar.

## User Story

As a Treasury department user (Tesorería role)
I want to access a dedicated Treasury section in the sidebar menu
So that I can navigate to Treasury-specific tools like NetSuite upload templates

## Prerequisites

- Backend server running at http://localhost:8000
- Frontend server running at http://localhost:5173
- User is authenticated (logged in)

## Test Steps

1. Navigate to the `Application URL` (http://localhost:5173)
2. Log in with valid credentials if not already authenticated
3. Wait for the main dashboard to load
4. **Verify** the sidebar is visible on the left side
5. Take a screenshot of the sidebar showing the department list
6. **Verify** "Tesorería" menu item appears in the sidebar with AccountBalance icon
7. Click on the "Tesorería" menu item
8. **Verify** the submenu expands showing nested items
9. Take a screenshot of the expanded Tesorería submenu
10. **Verify** "Plantillas para Cargar NetSuite" sub-item is visible
11. Click on "Plantillas para Cargar NetSuite" sub-item
12. **Verify** the URL changes to `/tesoreria/plantillas-netsuite`
13. **Verify** the page loads with the header "Plantillas para Cargar NetSuite"
14. Take a screenshot of the PlantillasNetSuite page
15. **Verify** the Tesorería menu remains expanded and the sub-item is highlighted
16. Navigate away to home page (click logo or home)
17. Navigate back to `/tesoreria/plantillas-netsuite` via URL
18. **Verify** the Tesorería menu auto-expands when navigating directly to a treasury route
19. Take a final screenshot showing auto-expanded menu state

## Success Criteria

- Tesorería appears in the sidebar menu with an AccountBalance icon
- Clicking Tesorería expands/collapses the submenu (toggle behavior)
- "Plantillas para Cargar NetSuite" sub-item is visible when expanded
- Clicking the sub-item navigates to `/tesoreria/plantillas-netsuite`
- The PlantillasNetSuite page loads with appropriate header and content
- Menu auto-expands when user navigates directly to a treasury route
- Visual styling matches Finance and Operations submenus exactly
- 4 screenshots are captured:
  1. Sidebar with department list (Tesorería visible)
  2. Expanded Tesorería submenu
  3. PlantillasNetSuite page loaded
  4. Auto-expanded menu state after direct navigation

## Error Scenarios to Note

- If Tesorería menu item is not visible, the sidebar component was not updated correctly
- If submenu doesn't expand, the toggle state is not working
- If navigation fails, the route was not added to App.tsx
- If page content is missing, the PlantillasNetSuite component was not created correctly
