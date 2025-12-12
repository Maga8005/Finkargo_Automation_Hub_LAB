# Bug: Departments Menu Slow Loading on Page Refresh/Login

## Bug Description
The departments menu in the sidebar takes a long time to load when refreshing the page or after logging in. Users see a loading spinner for several seconds before the department list appears, creating a poor user experience.

**Symptoms:**
- CircularProgress spinner displays for 2-5+ seconds on page load
- Noticeable delay between login completion and sidebar menu appearing
- Degraded perceived performance on every page refresh

**Expected Behavior:**
- Departments should appear instantly (< 100ms)
- No loading spinner should be visible for static data
- Sidebar should be ready immediately after page render

## Problem Statement
The departments menu makes an unnecessary API call (`GET /api/departments`) for static data that is hardcoded in the backend. This API call must wait for:
1. The auth session token to be validated/refreshed
2. The network round-trip to the backend
3. Response parsing and validation

This creates a waterfall of delays that blocks the UI from rendering the departments menu immediately.

## Solution Statement
Eliminate the unnecessary API call by using static departments data directly on the frontend. Since:
1. Departments are hardcoded in `backend/main.py` (line 82-98)
2. `FKSidebarWithCollapse` already has identical `mockDepartments` fallback data
3. Departments rarely change (requires code deployment to modify)

The solution is to:
1. Use the static `DEPARTMENTS` constant directly in both sidebar components
2. Remove the API call entirely from the sidebar initialization
3. Keep the `departmentService` for any future dynamic department needs
4. Add localStorage caching to `departmentService` for any components that still need it

## Steps to Reproduce
1. Navigate to http://localhost:5173
2. Login with valid credentials
3. After successful login, observe the sidebar
4. Notice the loading spinner displays for 2-5 seconds
5. Alternatively, refresh the page after logged in
6. Notice the same loading delay

## Root Cause Analysis
The performance bottleneck is caused by a waterfall of async operations:

```
1. Page/Component Mounts
2. FKSidebarWithCollapse.useEffect() triggers loadDepartments()
3. departmentService.getDepartments() called
4. apiClient request interceptor runs
5. apiClient checks session cache (stale after 5s TTL)
6. supabase.auth.getSession() called (network request)
7. Token retrieved, added to request headers
8. GET /api/departments request sent (network request)
9. Response received and parsed
10. Departments validated and filtered
11. State updated, spinner hidden, menu renders
```

The core issue is that **static data is being fetched via authenticated API call** when it could be rendered immediately from a constant.

Additionally:
- The `apiClient` has a 5-second cache TTL that frequently expires during login/refresh
- The `getSession()` call adds latency even when the session is valid
- The backend endpoint just returns hardcoded data anyway

## Affected Layer
- [ ] Backend: adapter/rest (API routes)
- [ ] Backend: core/servicios (business logic)
- [ ] Backend: repositorio (data access)
- [ ] Frontend: pages
- [x] Frontend: components
- [x] Frontend: services
- [ ] Frontend: types

## Relevant Files
Use these files to fix the bug:

- `frontend/src/components/ui/FKSidebar.tsx` - Original sidebar component that makes API calls
- `frontend/src/components/ui/FKSidebarWithCollapse.tsx` - Enhanced sidebar with submenus, also makes API calls but has mockDepartments fallback
- `frontend/src/services/departmentService.ts` - Service that makes the `/api/departments` API call
- `frontend/src/types/index.ts` - Contains Department type definition
- `.claude/commands/e2e/test_login.md` - Reference for E2E test format
- `backend/main.py` - Backend endpoint with hardcoded departments (for reference only, no changes needed)

### New Files
- `frontend/src/constants/departments.ts` - New file for static departments constant
- `.claude/commands/e2e/test_sidebar_performance.md` - E2E test for sidebar performance

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create Static Departments Constant
Create a new constants file with the static departments data:

- Create `frontend/src/constants/departments.ts`
- Export a `DEPARTMENTS` constant with the complete department list
- Match the exact structure from `backend/main.py` (lines 86-97)
- Export helper function `getDepartmentById(id: string)` for convenience

```typescript
// Structure to implement:
export const DEPARTMENTS: Department[] = [
  { id: 'operations', name: 'Operaciones', icon: 'Settings' },
  { id: 'sales', name: 'Ventas', icon: 'TrendingUp' },
  // ... rest of departments
];
```

### Step 2: Update FKSidebarWithCollapse to Use Static Data
Modify `frontend/src/components/ui/FKSidebarWithCollapse.tsx`:

- Import `DEPARTMENTS` from the new constants file
- Remove the `mockDepartments` variable (now redundant)
- Remove the `loadDepartments` async function
- Remove the `loading` state variable
- Initialize departments state directly with `DEPARTMENTS`
- Remove the `CircularProgress` loading spinner
- Keep the `useEffect` for auto-expanding menus based on route

### Step 3: Update FKSidebar to Use Static Data
Modify `frontend/src/components/ui/FKSidebar.tsx`:

- Import `DEPARTMENTS` from the new constants file
- Remove the `loadDepartments` async function
- Remove the `loading` state variable
- Remove the `error` state variable
- Initialize departments state directly with `DEPARTMENTS`
- Remove the `CircularProgress` loading spinner and error handling UI
- Keep the `isValidDepartment` type guard for safety
- Keep the `hasAccessToDepartment` function for role-based filtering

### Step 4: Add Caching to Department Service (Optional Enhancement)
Update `frontend/src/services/departmentService.ts` for any future uses:

- Add localStorage caching with 24-hour TTL
- Return cached data immediately if available
- Fetch in background to update cache
- This keeps the service functional for any other components

### Step 5: Create E2E Test for Sidebar Performance
Read `.claude/commands/e2e/test_login.md` and create a new E2E test file in `.claude/commands/e2e/test_sidebar_performance.md`:

- Test that sidebar renders immediately after login
- Verify no loading spinner is visible
- Verify all departments appear in < 500ms
- Verify role-based filtering works correctly
- Take screenshots at key moments

### Step 6: Run Validation Commands
Execute all validation commands to ensure zero regressions:

- Run frontend linting
- Run TypeScript type check
- Run frontend build
- Manual test: login and verify sidebar appears immediately
- Manual test: refresh page and verify sidebar appears immediately

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

Before fix - Reproduce the bug:
```bash
# 1. Start the dev servers if not running
cd frontend && npm run dev &
cd backend && source venv/bin/activate && python -m uvicorn main:app --reload &

# 2. Open http://localhost:5173 and observe:
#    - Login and watch the sidebar loading spinner
#    - Note the delay before departments appear (2-5+ seconds)
#    - Refresh the page and observe the same delay
```

After fix - Verify the improvement:
```bash
# 1. Ensure dev servers are running
# 2. Open http://localhost:5173 and verify:
#    - Login and sidebar appears instantly (no loading spinner)
#    - Departments visible within 100ms of page render
#    - Refresh the page - sidebar appears instantly
#    - No console errors related to departments
```

Read `.claude/commands/test_e2e.md`, then read and execute your new E2E `.claude/commands/e2e/test_sidebar_performance.md` test file to validate this functionality works.

- `cd frontend && npm run lint` - Run frontend linting
- `cd frontend && npx tsc --noEmit` - Run TypeScript type check
- `cd frontend && npm run build` - Run frontend build to validate production compilation

## Notes

1. **No backend changes required**: The `/api/departments` endpoint can remain for backwards compatibility or future use cases, but the sidebar will no longer call it.

2. **Trade-off**: By using static data, department changes now require a frontend deployment. This is acceptable because:
   - Departments are organizational structure, rarely changing
   - Backend already hardcodes them (no database involved)
   - Performance improvement is significant (2-5 seconds → instant)

3. **Future consideration**: If departments ever need to be dynamic (from database), the cached `departmentService` can be used, and the sidebar can implement a "stale-while-revalidate" pattern:
   - Show cached/static data immediately
   - Fetch fresh data in background
   - Update UI only if data changed

4. **Both sidebars need updating**: Both `FKSidebar.tsx` and `FKSidebarWithCollapse.tsx` have the same issue. The fix should be applied to both for consistency.
