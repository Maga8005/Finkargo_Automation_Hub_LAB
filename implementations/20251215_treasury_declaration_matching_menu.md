# Implementation Report: Treasury Declaration Matching Menu Item

**Date:** 2025-12-15
**Module:** Treasury / Frontend
**Issue:** Declaration Matching menu item missing from Treasury sidebar

## Summary

Added the "Coincidencia Declaraciones" menu item to the Treasury (Tesoreria) sidebar submenu and updated the auto-expand logic to properly detect `/treasury/` routes.

## Changes Made

- Added new menu item entry to `treasuryModules` array in `FKSidebarWithCollapse.tsx`:
  - ID: `declaration-matching`
  - Name: `Coincidencia Declaraciones`
  - Route: `/treasury/declaration-matching`
  - Icon: `Assessment` (already imported)

- Updated auto-expand logic in the `useEffect` hook to detect both `/tesoreria/` and `/treasury/` paths

- Updated `hasActiveSubmenu` check for Treasury department to include `/treasury/` route detection

## Files Changed

| File | Lines Changed |
|------|---------------|
| `frontend/src/components/ui/FKSidebarWithCollapse.tsx` | +9, -2 |

**New Files:**
- `.claude/commands/e2e/test_treasury_declaration_matching_menu.md` - E2E test file for validating the fix

## Discrepancies Found

**None.** The plan was accurate:
- The `Assessment` icon was already imported as expected
- The `treasuryModules` array structure matched the plan
- The auto-expand logic location matched the specified line numbers
- The `hasActiveSubmenu` check was where expected

## Validation Results

| Command | Status |
|---------|--------|
| `npm run lint` | PASSED (0 errors, 4 pre-existing warnings in unrelated files) |
| `npx tsc --noEmit` | PASSED |
| `npm run build` | PASSED |
| Post-fix grep verification | PASSED |

## Code Changes Detail

### 1. Added new menu item (lines 152-157)
```typescript
{
  id: 'declaration-matching',
  name: 'Coincidencia Declaraciones',
  route: '/treasury/declaration-matching',
  icon: <Assessment fontSize="small" />,
},
```

### 2. Updated auto-expand logic (line 216)
```typescript
// Before:
if (location.pathname.includes('/tesoreria/')) {

// After:
if (location.pathname.includes('/tesoreria/') || location.pathname.includes('/treasury/')) {
```

### 3. Updated hasActiveSubmenu check (lines 558-559)
```typescript
// Before:
const hasActiveSubmenu = treasuryModules.some(m => location.pathname === m.route);

// After:
const hasActiveSubmenu = treasuryModules.some(m => location.pathname === m.route) ||
                         location.pathname.includes('/treasury/');
```

## Testing Notes

- E2E test file created at `.claude/commands/e2e/test_treasury_declaration_matching_menu.md`
- Manual E2E validation was attempted but blocked by lack of valid test credentials
- Code validation (lint, tsc, build) confirms the fix compiles and runs without errors

## Next Steps

1. Test with valid Supabase credentials to confirm menu item appears
2. Verify navigation to `/treasury/declaration-matching` works
3. Verify Treasury submenu auto-expands when on the declaration matching page
