# Feature: Dark Mode Toggle

## Feature Description
Add a dark mode theme option to the Finkargo Automation Hub application, allowing users to toggle between light and dark themes. The theme preference will be accessible from the user menu dropdown in the top-right corner of the application, providing an enhanced user experience with reduced eye strain in low-light environments while maintaining the Finkargo brand identity.

The dark mode will feature:
- A carefully designed dark color palette that maintains brand consistency with Finkargo's primary colors
- Proper contrast ratios for accessibility (WCAG AA compliance)
- Persistent theme preference stored in browser localStorage
- Smooth visual transitions between themes
- Consistent theming across all components and pages
- A toggle control in the user menu dropdown (FKUserMenu component)

## User Story
As a **Finkargo employee or client**
I want to **toggle between light and dark display modes**
So that **I can reduce eye strain when working in low-light environments and customize my viewing experience to my preferences**

## Problem Statement
Currently, the Finkargo Automation Hub only supports a light theme with a white/light gray background. Users who work extended hours, prefer dark interfaces, or work in low-light environments experience eye strain and fatigue. Many modern enterprise applications provide theme customization as a standard feature, and users have come to expect this functionality. Without dark mode:

1. Users experience increased eye strain during extended work sessions
2. The application cannot adapt to different lighting conditions
3. Users who prefer dark interfaces for accessibility or personal preference have no options
4. The application feels less modern compared to competitors with theme options
5. Battery life on OLED devices is not optimized (dark pixels consume less power)

## Solution Statement
Implement a comprehensive dark mode system using Material-UI's theming capabilities that:

1. **Creates a dual-theme system**: Extend the existing `theme.ts` to support both light and dark themes with Finkargo-branded color palettes
2. **Provides user control**: Add a theme toggle in the FKUserMenu dropdown component with a clear light/dark mode selector
3. **Persists preferences**: Store the user's theme choice in localStorage to maintain their preference across sessions
4. **Manages theme state globally**: Create a ThemeContext provider to manage theme state and make it accessible throughout the application
5. **Ensures brand consistency**: Maintain Finkargo's primary colors (blues, coral) while adapting backgrounds, text, and surfaces for dark mode
6. **Guarantees accessibility**: Ensure proper contrast ratios for text readability and WCAG AA compliance
7. **Provides smooth transitions**: Implement subtle transitions when switching between themes for a polished user experience

The implementation will follow Material-UI best practices and integrate seamlessly with the existing Clean Architecture pattern, requiring no changes to business logic or API layers.

## Relevant Files

### Existing Files to Modify

- **`frontend/src/theme/theme.ts`** (lines 1-222)
  - Currently defines only a light theme with Finkargo's design system
  - Needs to be extended to create both light and dark theme configurations
  - Will export a theme factory function that accepts a mode parameter
  - Dark theme will maintain primary brand colors while adjusting backgrounds, surfaces, and text colors

- **`frontend/src/App.tsx`** (lines 1-91)
  - Currently wraps the app with a static ThemeProvider
  - Needs to integrate the new ThemeContext provider
  - Will enable dynamic theme switching throughout the application

- **`frontend/src/components/ui/FKUserMenu.tsx`** (lines 1-318)
  - User menu dropdown component displayed in the top navbar
  - Needs to add a theme toggle control (light/dark mode selector)
  - Will integrate with ThemeContext to trigger theme changes
  - Should display the toggle above the "Mi Perfil" menu item with an appropriate icon

- **`frontend/src/components/ui/FKTopNavbar.tsx`** (lines 1-42)
  - Top navigation bar that contains the FKUserMenu
  - May need minor style adjustments to work well with dark mode
  - Should use theme colors dynamically rather than hardcoded values

- **`frontend/src/components/ui/FKMainLayout.tsx`**
  - Main layout component that wraps authenticated pages
  - May need to ensure proper background colors and borders work with dark mode
  - Should use theme-aware styling

### New Files to Create

#### **`frontend/src/contexts/ThemeContext.tsx`**
- New context provider for managing theme mode state (light/dark)
- Will handle:
  - Reading initial theme preference from localStorage
  - Storing current theme mode in state
  - Providing toggle function to switch between themes
  - Persisting theme preference to localStorage on change
- Exports:
  - `ThemeContext`: React context for theme state
  - `ThemeProvider`: Provider component with theme logic
  - `useTheme`: Custom hook for accessing theme context

#### **`frontend/src/hooks/useThemeMode.ts`**
- Custom hook for consuming theme context
- Provides clean API for components to:
  - Access current theme mode
  - Toggle between light/dark
  - Check if dark mode is active
- Simplifies theme integration in components

#### **`frontend/src/theme/darkTheme.ts`**
- Dark theme color palette configuration
- Defines Finkargo-branded dark mode colors:
  - Background colors (dark surfaces, paper)
  - Text colors (high contrast on dark backgrounds)
  - Primary/coral colors (adjusted for dark mode visibility)
  - Status colors (success, error, warning with dark mode variants)
  - Gray scale optimized for dark interfaces
- Ensures WCAG AA contrast ratios

#### **`frontend/src/types/theme.ts`**
- TypeScript type definitions for theme system
- Defines:
  - `ThemeMode`: 'light' | 'dark' type
  - `ThemeContextType`: Interface for theme context
  - `ThemeModePreference`: localStorage key and type

## Implementation Plan

### Phase 1: Foundation - Theme System Architecture
Create the core theme infrastructure with dual-theme support, theme context, and persistence layer. This phase establishes the foundation for dynamic theme switching without affecting existing functionality.

**Key Activities:**
- Design dark mode color palette maintaining Finkargo brand identity
- Create theme factory function that generates themes based on mode
- Implement theme context with localStorage persistence
- Set up type definitions for theme system

**Deliverables:**
- Complete dark theme color palette with accessibility compliance
- Theme factory function in refactored `theme.ts`
- ThemeContext provider with state management
- TypeScript types for theme system

### Phase 2: Core Implementation - Theme Toggle UI
Build the user-facing theme toggle control and integrate it with the theme system. This phase makes dark mode accessible to users through an intuitive interface.

**Key Activities:**
- Add theme toggle to FKUserMenu dropdown
- Implement toggle UI with light/dark icons
- Connect toggle to theme context
- Add visual feedback for current theme state

**Deliverables:**
- Theme toggle menu item in FKUserMenu
- Working theme switching mechanism
- Persistent theme preference across sessions
- Visual indicators for active theme

### Phase 3: Integration - Polish and Optimization
Ensure all components render correctly in both themes, fix any styling issues, optimize transitions, and validate accessibility standards are met across the application.

**Key Activities:**
- Test all pages and components in dark mode
- Fix any hardcoded colors or style issues
- Optimize theme transition performance
- Validate accessibility compliance
- Test on different screen sizes and devices

**Deliverables:**
- Fully functional dark mode across all pages
- Smooth theme transitions
- Accessibility audit passing WCAG AA
- Cross-browser compatibility verification

## Step by Step Tasks

### Task 1: Create TypeScript Type Definitions
- Create `frontend/src/types/theme.ts` file
- Define `ThemeMode` type as `'light' | 'dark'`
- Define `ThemeContextType` interface with properties:
  - `mode: ThemeMode`
  - `toggleTheme: () => void`
  - `setTheme: (mode: ThemeMode) => void`
  - `isDarkMode: boolean`
- Define `THEME_STORAGE_KEY` constant for localStorage
- Export all types and constants

### Task 2: Design Dark Mode Color Palette
- Create `frontend/src/theme/darkTheme.ts` file
- Define dark mode color palette object with:
  - Primary colors (adjusted for dark mode visibility)
  - Coral/CTA colors (maintain Finkargo brand)
  - Success/error/warning colors (dark variants)
  - Background colors:
    - `default`: '#121212' (Material Design standard)
    - `paper`: '#1E1E1E' (elevated surfaces)
  - Text colors:
    - `primary`: 'rgba(255, 255, 255, 0.87)' (high emphasis)
    - `secondary`: 'rgba(255, 255, 255, 0.60)' (medium emphasis)
    - `disabled`: 'rgba(255, 255, 255, 0.38)' (low emphasis)
  - Gray scale optimized for dark backgrounds
- Ensure all color combinations meet WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
- Export dark palette configuration

### Task 3: Refactor Theme Configuration
- Update `frontend/src/theme/theme.ts` to support theme modes
- Create `createAppTheme(mode: ThemeMode)` factory function that:
  - Accepts 'light' or 'dark' as parameter
  - Returns configured Material-UI theme based on mode
  - Merges mode-specific palette with common configuration
- Extract common theme settings (typography, shape, breakpoints, components) into shared configuration
- Implement conditional palette selection based on mode:
  - If mode is 'light': use existing light palette
  - If mode is 'dark': use dark palette from darkTheme.ts
- Update component style overrides to use theme values instead of hardcoded colors:
  - Replace hardcoded colors with theme palette references
  - Ensure MuiButton, MuiCard, MuiTextField, MuiDrawer use theme-aware colors
  - Update shadow definitions to work on both light and dark backgrounds
- Export `createAppTheme` function as default export
- Maintain backward compatibility with existing theme usage

### Task 4: Create Theme Context Provider
- Create `frontend/src/contexts/ThemeContext.tsx` file
- Implement `ThemeContext` with React.createContext:
  - Default value should match `ThemeContextType` interface
  - Include helpful error messages for consumers outside provider
- Implement `ThemeProvider` component that:
  - Manages theme mode state with useState
  - Reads initial theme from localStorage on mount
  - Provides `toggleTheme` function to switch between modes
  - Provides `setTheme` function for direct mode setting
  - Persists theme changes to localStorage
  - Wraps children with Material-UI ThemeProvider using dynamic theme
- Create theme instance using `createAppTheme(mode)` that updates when mode changes
- Implement context value object with all required properties
- Export `ThemeContext` and `ThemeProvider`

### Task 5: Create useThemeMode Custom Hook
- Create `frontend/src/hooks/useThemeMode.ts` file
- Implement custom hook that:
  - Consumes ThemeContext using useContext
  - Throws error if used outside ThemeProvider
  - Returns theme context value
- Add TypeScript return type annotation
- Export as default

### Task 6: Integrate Theme Provider in App
- Update `frontend/src/App.tsx` imports:
  - Remove static theme import from `./theme/theme`
  - Import `ThemeProvider` from `./contexts/ThemeContext`
- Wrap existing application structure with new ThemeProvider:
  - Place ThemeProvider outside Router but inside CssBaseline
  - Structure: `<ThemeProvider><CssBaseline /><AuthProvider><Router>...</Router></AuthProvider></ThemeProvider>`
- Remove old Material-UI ThemeProvider (now handled by ThemeContext)
- Verify no breaking changes to existing routing or authentication

### Task 7: Add Theme Toggle to User Menu
- Update `frontend/src/components/ui/FKUserMenu.tsx`:
  - Import useThemeMode hook
  - Import Material-UI icons: `Brightness4` (dark), `Brightness7` (light)
  - Add theme mode state from hook: `const { isDarkMode, toggleTheme } = useThemeMode()`
  - Add new MenuItem in the dropdown menu structure:
    - Position: After user info header, before "Mi Perfil" menu item
    - Add Divider before theme toggle section
    - MenuItem should display:
      - Icon: Light/dark icon based on current mode
      - Text: "Modo Oscuro" / "Modo Claro" based on current mode
      - Include ListItemIcon wrapper for icon
    - onClick handler calls `toggleTheme()`
    - Add visual styling consistent with existing menu items
- Ensure toggle is accessible (keyboard navigation, screen readers)
- Add hover states and focus indicators

### Task 8: Update Top Navbar for Dark Mode Compatibility
- Review `frontend/src/components/ui/FKTopNavbar.tsx`:
  - Check if AppBar uses hardcoded colors
  - Replace any hardcoded background colors with theme palette references
  - Ensure text colors use theme values
  - Update box shadows to work on both light and dark backgrounds
- Test navbar appearance in both themes
- Verify user menu contrast is sufficient in both modes

### Task 9: Update Main Layout for Theme Support
- Review `frontend/src/components/ui/FKMainLayout.tsx`:
  - Identify any hardcoded background colors
  - Replace with theme-aware values (e.g., `theme.palette.background.default`)
  - Check sidebar background colors
  - Ensure borders and dividers use theme values
  - Verify proper contrast for all text elements
- Test layout in both light and dark modes
- Ensure drawer shadows work correctly in both themes

### Task 10: Add Theme Transitions for Smooth Switching
- Update `frontend/src/theme/theme.ts`:
  - Add transitions configuration to common theme settings
  - Configure transition for background-color, color properties:
    - Duration: 0.3s
    - Easing: theme.transitions.easing.easeInOut
- Update global CssBaseline component overrides:
  - Add smooth transition to body element
  - Apply to all major layout elements
- Test transition smoothness when toggling theme

### Task 11: Audit and Fix Hardcoded Colors
- Search codebase for hardcoded color values:
  - Use grep/search for hex colors (#FFFFFF, #000000, etc.)
  - Search for rgb/rgba values
  - Check for string color names ('white', 'black', etc.)
- For each hardcoded color found:
  - Replace with appropriate theme palette reference
  - Ensure component receives theme via sx prop or styled-components
  - Test in both light and dark modes
- Focus on high-usage components first:
  - All FK-prefixed components (FKSidebar, FKMainLayout, etc.)
  - Form components (FKContractRequest, FKClientDataImport, etc.)
  - Page components (LegalDashboard, OperationsDashboard, etc.)

### Task 12: Test Dark Mode Across All Pages
- Systematically test dark mode on all pages:
  - Login page (`/login`)
  - Home page (`/`)
  - Legal dashboard (`/department/legal`)
  - Operations dashboard (`/department/operations`)
  - Client dashboard (`/client`)
  - Finance pages (`/finance/*`)
  - Department pages
- For each page verify:
  - Background colors are appropriate
  - Text is readable (sufficient contrast)
  - Buttons and controls are visible
  - Forms are styled correctly
  - Tables and data grids work in dark mode
  - Cards and elevated surfaces have proper styling
  - No white flashes or unexpected light elements
  - Images and logos display correctly
- Document any issues found for fixing

### Task 13: Fix Component-Specific Dark Mode Issues
- Based on testing results, fix any component-specific issues:
  - Update MUI DataGrid theming if needed
  - Fix form input field backgrounds
  - Adjust modal and dialog backgrounds
  - Update chart colors if present
  - Fix any contrast issues with icons
  - Adjust hover and focus states for dark mode
- Verify fixes don't break light mode
- Re-test affected components in both themes

### Task 14: Accessibility Validation
- Run accessibility audit using browser dev tools:
  - Check color contrast ratios (WCAG AA: 4.5:1 for normal text)
  - Verify keyboard navigation works with theme toggle
  - Test screen reader compatibility
  - Ensure focus indicators are visible in both themes
- Use axe DevTools or Lighthouse for automated checks
- Test with actual screen reader (VoiceOver on Mac, NVDA on Windows)
- Fix any accessibility issues found:
  - Increase contrast where needed
  - Add aria-labels if missing
  - Ensure proper focus management

### Task 15: Cross-Browser Testing
- Test dark mode functionality in:
  - Chrome/Chromium (latest)
  - Firefox (latest)
  - Safari (latest)
  - Edge (latest)
- Verify localStorage persistence works across browsers
- Check CSS compatibility (some older browsers may not support certain features)
- Test on mobile browsers:
  - iOS Safari
  - Chrome Mobile
  - Firefox Mobile
- Document and fix any browser-specific issues

### Task 16: Performance Optimization
- Measure theme toggle performance:
  - Time to switch themes should be < 300ms
  - No layout shifts or flickering
  - Smooth transitions
- Optimize theme creation:
  - Memoize theme object creation if needed
  - Avoid unnecessary re-renders on theme change
- Test on slower devices to ensure good performance
- Profile with React DevTools to identify bottlenecks

### Task 17: Documentation and Code Comments
- Add JSDoc comments to:
  - `createAppTheme` function explaining parameters and return value
  - ThemeContext provider explaining state management
  - useThemeMode hook explaining usage
  - Dark theme palette explaining color choices
- Update component comments where theme integration added
- Add inline comments for complex theme logic
- Ensure code is well-documented for future maintenance

### Task 18: Run Validation Commands
- Execute all validation commands listed below
- Fix any errors or warnings that appear
- Re-run commands until all pass successfully
- Verify zero regressions in existing functionality
- Confirm theme toggle works end-to-end:
  1. Open application in browser
  2. Log in with valid credentials
  3. Open user menu in top-right corner
  4. Click theme toggle
  5. Verify theme switches to dark mode
  6. Refresh page and verify theme persists
  7. Click toggle again to return to light mode
  8. Navigate to different pages and verify theme is consistent
  9. Log out and log back in, verify theme preference is maintained

## Testing Strategy

### Unit Tests
**Note**: The frontend currently has no testing framework configured. Unit tests are recommended for future work but are not part of this implementation.

Recommended unit tests for future implementation:
- **ThemeContext Provider**:
  - Test initial theme loads from localStorage
  - Test toggleTheme function switches mode
  - Test setTheme function sets specific mode
  - Test theme persistence to localStorage
  - Test default to light mode if no preference stored

- **useThemeMode Hook**:
  - Test hook returns correct theme mode
  - Test hook throws error when used outside provider
  - Test isDarkMode computed value is correct

- **createAppTheme Function**:
  - Test light mode returns correct palette
  - Test dark mode returns correct palette
  - Test typography and shape settings are consistent
  - Test component overrides apply correctly

### Integration Tests
**Note**: Integration tests are recommended for future work but are not part of this implementation.

Recommended integration tests for future implementation:
- **Theme Toggle in User Menu**:
  - Test clicking toggle updates theme mode
  - Test theme persists across route navigation
  - Test theme persists after page refresh
  - Test theme toggle icon updates based on current mode

- **Theme Application Across Components**:
  - Test all FK-prefixed components render in both themes
  - Test forms display correctly in dark mode
  - Test navigation components adapt to theme
  - Test no white flashes during theme switch

### Manual Testing Checklist

**Functional Testing**:
- [ ] Theme toggle appears in user menu dropdown
- [ ] Clicking toggle switches between light and dark mode
- [ ] Theme preference persists after page refresh
- [ ] Theme preference persists after logout/login
- [ ] Theme applies consistently across all pages
- [ ] No console errors when toggling theme
- [ ] Theme icon updates based on current mode

**Visual Testing**:
- [ ] All text is readable in both themes (contrast check)
- [ ] Buttons and controls are visible in both themes
- [ ] Forms render correctly in both themes
- [ ] Tables and data grids display properly in dark mode
- [ ] Cards and elevated surfaces have appropriate shadows
- [ ] Navigation sidebar works in both themes
- [ ] Top navbar displays correctly in both themes
- [ ] No white flashes or unexpected light elements in dark mode
- [ ] Theme transitions are smooth and not jarring

**Accessibility Testing**:
- [ ] Color contrast ratios meet WCAG AA standards (4.5:1 minimum)
- [ ] Theme toggle is keyboard accessible (Tab navigation)
- [ ] Theme toggle has proper focus indicator
- [ ] Screen readers announce theme change
- [ ] Focus management works correctly after theme switch

**Cross-Browser Testing**:
- [ ] Theme works in Chrome/Chromium
- [ ] Theme works in Firefox
- [ ] Theme works in Safari
- [ ] Theme works in Edge
- [ ] localStorage works across all browsers
- [ ] Mobile browsers support theme (iOS Safari, Chrome Mobile)

### Edge Cases

1. **No localStorage Support**:
   - **Scenario**: User's browser has localStorage disabled or unavailable
   - **Expected**: App defaults to light mode, theme toggle still works for session
   - **Handling**: Wrap localStorage calls in try-catch, fall back to session state only

2. **Corrupted localStorage Data**:
   - **Scenario**: localStorage has invalid theme value (not 'light' or 'dark')
   - **Expected**: App defaults to light mode and overwrites invalid data
   - **Handling**: Validate theme value from localStorage, use default if invalid

3. **Theme Toggle During Page Transition**:
   - **Scenario**: User toggles theme while navigating to another page
   - **Expected**: New page renders with updated theme, no flash of wrong theme
   - **Handling**: Theme state managed globally, persisted immediately on change

4. **Multiple Tabs Open**:
   - **Scenario**: User has multiple tabs of app open, changes theme in one tab
   - **Expected**: Other tabs do not automatically sync (expected behavior)
   - **Note**: Cross-tab syncing could be added with localStorage events in future

5. **System Preference Changes**:
   - **Scenario**: User's OS switches between light/dark mode
   - **Expected**: App respects user's explicit choice, does not auto-switch with OS
   - **Note**: Future enhancement could add "System" option to follow OS preference

6. **Rapid Theme Toggling**:
   - **Scenario**: User clicks theme toggle multiple times quickly
   - **Expected**: App handles gracefully without crashes or visual glitches
   - **Handling**: Debounce or throttle toggle handler if needed, test performance

7. **Theme Toggle While Forms Are Open**:
   - **Scenario**: User toggles theme while filling out a form
   - **Expected**: Form data is preserved, no loss of user input
   - **Handling**: Theme change is purely visual, does not affect component state

8. **Third-Party Components**:
   - **Scenario**: MUI DataGrid or other third-party components may not fully support dark mode
   - **Expected**: Components receive theme via Material-UI context and adapt
   - **Handling**: Test all third-party components, add custom styles if needed

9. **Print Styles**:
   - **Scenario**: User tries to print page while in dark mode
   - **Expected**: Print version uses light theme for better readability and ink efficiency
   - **Note**: Future enhancement could add @media print styles forcing light theme

10. **Initial Load Flash**:
    - **Scenario**: Page briefly shows light theme before applying dark theme on load
    - **Expected**: No flash of wrong theme on initial load
    - **Handling**: Read theme from localStorage synchronously before first render, or use CSS variable approach

## Acceptance Criteria

### Core Functionality
- [ ] **Theme Toggle Accessible**: Users can access theme toggle from user menu dropdown in top-right corner
- [ ] **Theme Switching Works**: Clicking toggle switches between light and dark mode instantly (< 300ms)
- [ ] **Theme Persists**: Selected theme persists across page refreshes and browser sessions via localStorage
- [ ] **Theme Applies Globally**: Theme change affects all pages and components consistently

### Visual Quality
- [ ] **Dark Mode Design**: Dark theme uses appropriate color palette with:
  - Dark backgrounds (#121212 for default, #1E1E1E for paper)
  - High contrast text (rgba(255, 255, 255, 0.87) for primary text)
  - Finkargo brand colors maintained (blues, coral)
  - Proper shadows and elevation for depth
- [ ] **No Visual Glitches**: No white flashes, color mismatches, or broken layouts in either theme
- [ ] **Smooth Transitions**: Theme switches with smooth 300ms transition, not jarring instant change
- [ ] **Consistent Branding**: Finkargo logo, primary colors, and brand identity maintained in both themes

### Accessibility
- [ ] **WCAG AA Compliance**: All text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
- [ ] **Keyboard Accessible**: Theme toggle is fully keyboard navigable (Tab, Enter/Space to activate)
- [ ] **Screen Reader Support**: Theme toggle announces current mode and change to screen readers
- [ ] **Focus Indicators**: Focus states are clearly visible in both light and dark modes

### Technical Requirements
- [ ] **No Breaking Changes**: Existing functionality unaffected by theme implementation
- [ ] **TypeScript Coverage**: All new code fully typed, no `any` types used
- [ ] **Clean Architecture**: Theme logic separated into appropriate layers (context, hooks, theme config)
- [ ] **No Console Errors**: No errors or warnings in browser console related to theme system
- [ ] **localStorage Handling**: Graceful fallback if localStorage is unavailable
- [ ] **Performance**: Theme toggle does not cause performance degradation or slow renders

### User Experience
- [ ] **Intuitive UI**: Theme toggle is easy to find and understand
- [ ] **Clear Indication**: User can clearly see which theme is currently active
- [ ] **Works on All Pages**: Theme functions correctly on login, dashboards, forms, and all other pages
- [ ] **Mobile Friendly**: Theme toggle works on mobile devices and responsive layouts

### Code Quality
- [ ] **Code Documentation**: All new functions, components, and hooks have JSDoc comments
- [ ] **Consistent Patterns**: Theme implementation follows existing codebase patterns and conventions
- [ ] **No Hardcoded Colors**: All color values use theme palette references, not hardcoded hex/rgb
- [ ] **Reusable Components**: Theme system is extensible for future theme variations

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Frontend build validation - ensures TypeScript compiles with no errors
cd frontend && npm run build

# Frontend linting - ensures code quality and no ESLint errors
cd frontend && npm run lint

# Start development server - manual testing
cd frontend && npm run dev
# Then open http://localhost:5173 in browser
# Perform manual testing checklist above

# Validate theme persistence in localStorage
# In browser console after toggling theme:
localStorage.getItem('finkargo_theme_mode')
# Should return 'light' or 'dark'

# Check for TypeScript errors specifically
cd frontend && npx tsc --noEmit

# Check bundle size impact (ensure theme addition doesn't significantly increase bundle)
cd frontend && npm run build && du -sh dist/
# Compare with pre-implementation bundle size

# Accessibility validation - run Lighthouse audit
# In Chrome DevTools:
# 1. Open DevTools (F12)
# 2. Go to Lighthouse tab
# 3. Run audit on both light and dark modes
# 4. Ensure Accessibility score is 90+ for both themes

# Visual regression testing - manual
# 1. Take screenshots of key pages in light mode
# 2. Toggle to dark mode
# 3. Take screenshots of same pages in dark mode
# 4. Compare for consistency and proper theming

# End-to-end validation flow:
# 1. Open http://localhost:5173 (should default to light mode)
# 2. Log in with valid credentials
# 3. Navigate to /department/legal
# 4. Open user menu (top-right corner)
# 5. Verify theme toggle shows "Modo Oscuro" option
# 6. Click toggle, verify immediate switch to dark mode
# 7. Refresh page (Cmd/Ctrl+R)
# 8. Verify dark mode persists after refresh
# 9. Navigate to different pages (/department/operations, /finance/reporteria-automatica-co)
# 10. Verify dark mode is consistent across all pages
# 11. Open user menu again
# 12. Verify toggle now shows "Modo Claro" option
# 13. Click toggle to return to light mode
# 14. Log out, log back in
# 15. Verify theme preference was maintained
```

## Notes

### Future Enhancements
1. **System Theme Detection**: Add "System" option to automatically follow OS light/dark mode preference using `prefers-color-scheme` media query
2. **Custom Theme Options**: Allow users to create custom color schemes or choose from multiple theme variants
3. **Cross-Tab Syncing**: Sync theme changes across multiple open tabs using localStorage events
4. **Print Styles**: Force light theme for printing to save ink and improve readability
5. **Scheduled Theme Switching**: Auto-switch to dark mode at sunset/night hours based on user location
6. **High Contrast Mode**: Add accessibility option for high contrast theme for visually impaired users

### Technical Considerations
- **Material-UI Version**: The app uses MUI v7.3.4, which has excellent dark mode support out of the box
- **No Backend Changes Needed**: Theme preference stored client-side only; could be extended to store in user_profiles table for cross-device sync
- **Bundle Size Impact**: Theme addition should add < 10KB to bundle (minimal color definitions and context)
- **Performance**: Theme switching is CPU-light; uses CSS custom properties and Material-UI's optimized theming
- **Browser Support**: localStorage is supported in all modern browsers; graceful degradation for edge cases

### Design Decisions
- **Toggle Location**: Placed in user menu for easy access without cluttering navbar
- **Persistence Strategy**: localStorage chosen over cookies for simplicity and no server overhead
- **Default Theme**: Light mode is default to match most users' expectations and current behavior
- **Transition Duration**: 300ms chosen as sweet spot between responsiveness and smoothness
- **Dark Background Color**: #121212 follows Material Design guidelines for optimal dark mode experience
- **Brand Colors**: Finkargo primary blues and coral maintained to preserve brand identity

### Development Tips
- Test theme on actual devices, not just dev tools responsive mode
- Use browser dark mode extensions to verify theme looks good when OS is in dark mode
- Check theme in different lighting conditions (bright room, dark room) for real-world usability
- Verify theme works with browser zoom levels (100%, 125%, 150%)
- Test with users who have color blindness or visual impairments if possible

### Known Limitations
- Theme preference not synced across devices (requires backend implementation)
- No automatic switching based on time of day (future enhancement)
- Print styles not optimized for dark mode (prints as-is)
- Third-party embeds (iframes, external widgets) may not respect theme

### Dependencies
- No new npm packages required
- Uses existing Material-UI theming system
- Leverages browser localStorage API
- React Context API for state management (already used for auth)

### Migration Notes
- This is a non-breaking change - existing users will default to light mode
- No database migrations required
- No API changes required
- Frontend-only change, backend unaffected
