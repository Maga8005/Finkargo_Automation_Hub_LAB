# Bug: Authentication Token Lost Mid-Session

## Bug Description
Users experience intermittent authentication loss while actively using the application. After successful login, the user can access the platform normally, but at some point during the session, authentication state appears to be lost. This manifests as:

- Contract generation modules (e.g., Operations Contracts pages) suddenly disappear from the UI
- Department sidebar items may become inaccessible or hidden
- Role-protected routes may stop rendering their content
- User must manually refresh the browser to restore access

The symptoms suggest that while the Supabase session token remains valid in localStorage, the React application's AuthContext is losing its authentication state (user, session, or userProfile becoming null unexpectedly).

## Problem Statement
The authentication state management system has a critical bug where the in-memory AuthContext state (user, session, userProfile) can become desynchronized from the persisted Supabase session in localStorage. This causes components that depend on `useAuth()` (like ProtectedRoute, RoleProtectedRoute, FKSidebar, and page components) to suddenly believe the user is unauthenticated, even though a valid session exists.

The root cause is likely one or more of the following:
1. **Token expiry handling**: When Supabase auto-refreshes tokens, the AuthContext may not be properly updated with the new session
2. **Auth state change handler gaps**: The `onAuthStateChange` listener may be missing certain events or not properly propagating state updates
3. **API interceptor desynchronization**: The apiClient's cached session may become stale, causing 401 errors that trigger unnecessary sign-outs
4. **Race conditions**: Multiple components or listeners may be updating auth state concurrently, causing state to be overwritten
5. **Memory leak or unmount issue**: The auth state listener may be getting unsubscribed prematurely, stopping updates

## Solution Statement
Implement a comprehensive fix to ensure authentication state remains synchronized between Supabase session storage and React AuthContext throughout the user's session:

1. **Add proactive session refresh mechanism**: Periodically validate and refresh the session before token expiry to prevent gaps
2. **Enhance auth state change handling**: Ensure all Supabase auth events (TOKEN_REFRESHED, SIGNED_IN, USER_UPDATED) properly update React state
3. **Add session validation on critical operations**: Before API calls that require auth, validate session is still active
4. **Improve apiClient session synchronization**: Ensure the apiClient's cached session is always in sync with Supabase's actual session
5. **Add session persistence recovery**: On component mount, validate that React state matches localStorage session and recover if needed
6. **Add comprehensive logging**: Track auth state changes, token refreshes, and session validation to diagnose issues
7. **Add window focus listener**: Re-validate session when user returns to the tab (handles token expiry during inactivity)

## Steps to Reproduce
1. Log in to the platform with valid credentials
2. Navigate to Operations Contracts page (e.g., `/operations/contratos-colombia`)
3. Verify that contract request tabs are visible and functional
4. Wait for an extended period (10-30 minutes) while using the application
   - OR: Perform multiple API operations (generate contracts, review, etc.)
   - OR: Switch to another browser tab/app and return later
5. **Bug occurs**: Notice that contract generation modules disappear from the page
6. Components that rely on `userProfile` or `isAuthenticated` may show loading states or empty content
7. Refreshing the browser (F5) restores access immediately, proving the session token is still valid in localStorage

## Root Cause Analysis

### Primary Cause: Token Refresh Not Updating React State
**Location**: `frontend/src/contexts/AuthContext.tsx:135-158`

The `onAuthStateChange` listener explicitly ignores the `INITIAL_SESSION` event (line 140-142) to prevent duplicate fetches during initialization. However, this may also be preventing proper state updates during token refresh cycles.

Additionally, Supabase's `autoRefreshToken: true` configuration (in `frontend/src/services/supabase.ts:21`) automatically refreshes tokens before expiry, but if the AuthContext's `onAuthStateChange` handler doesn't catch the `TOKEN_REFRESHED` event, the React state won't update with the new session.

### Secondary Cause: API Interceptor Session Cache Staleness
**Location**: `frontend/src/api/clients/apiClient.ts:20-38`

The apiClient maintains a `cachedSession` that is initialized once and updated via `onAuthStateChange`. However:
1. If the auth state change listener in AuthContext misses an event, the apiClient's listener might also miss it
2. The cache is updated asynchronously, which could cause race conditions
3. There's no mechanism to validate that `cachedSession` matches the actual Supabase session

When `cachedSession` becomes stale (has an expired or revoked token), API requests will use the old token, receive 401 errors, and trigger the refresh logic in the response interceptor (lines 54-109). However, if the refresh fails or the state isn't propagated back to AuthContext, the user appears logged out.

### Tertiary Cause: No Session Validation on Component Mount
**Location**: `frontend/src/contexts/AuthContext.tsx:97-166`

The AuthContext initializes once when the app loads and sets up the auth state change listener. However, if the listener subscription is somehow lost or stops firing (e.g., due to React strict mode double-mounting, or a memory leak), the React state will never update again, even though the localStorage session remains valid.

There's no mechanism to:
- Periodically validate that React state matches localStorage session
- Recover from a desynchronized state
- Re-establish the listener if it's lost

### Quaternary Cause: Race Condition in Profile Fetching
**Location**: `frontend/src/contexts/AuthContext.tsx:45-92`

The `fetchUserProfile` function uses `fetchingProfileRef.current` to prevent concurrent fetches. However, if an error occurs during profile fetching (lines 71-80), the profile is set to `null`, which could cause components to think the user is unauthenticated even though the session is valid.

If this happens mid-session (e.g., due to a temporary network error or database connection issue), the user loses access without being explicitly signed out.

### Quinary Cause: Component Re-renders Without Auth State
**Location**: Various page components (e.g., `frontend/src/pages/operations/OperationsContractsColombia.tsx`, `frontend/src/components/ui/FKSidebar.tsx`)

Components use `const { userProfile, loading } = useAuth()` to determine what to render. If `userProfile` becomes `null` mid-session (due to any of the above causes), the components will hide role-protected content, even though the user should still have access.

The components have no mechanism to detect that this is an error state (vs. a legitimate sign-out) and attempt to recover.

## Relevant Files
Use these files to fix the bug:

### Core Authentication Files

- **`frontend/src/contexts/AuthContext.tsx`** (Lines 1-298)
  - Primary location for auth state management
  - Need to enhance `onAuthStateChange` handler to properly handle all auth events (especially TOKEN_REFRESHED)
  - Need to add periodic session validation to detect desynchronization
  - Need to add recovery mechanism when React state doesn't match localStorage session
  - Need to add window focus listener to re-validate session when user returns to tab
  - Need to improve error handling in `fetchUserProfile` to not clear `userProfile` on transient errors

- **`frontend/src/services/supabase.ts`** (Lines 1-132)
  - Supabase client configuration with `autoRefreshToken: true` and `persistSession: true`
  - Already configured correctly for automatic token refresh
  - May need to add manual session refresh helper function
  - May need to add session validation helper function

- **`frontend/src/api/clients/apiClient.ts`** (Lines 1-113)
  - Axios interceptor that manages request/response authentication
  - Need to ensure `cachedSession` stays synchronized with Supabase session
  - Need to improve the 401 error handling to properly update AuthContext
  - Consider removing the in-memory cache and always fetching session synchronously from Supabase

### Components Affected by Auth Loss

- **`frontend/src/components/ProtectedRoute.tsx`** (Lines 1-72)
  - Uses `isAuthenticated` and `loading` to determine routing
  - May need to add session recovery mechanism before redirecting to login

- **`frontend/src/components/RoleProtectedRoute.tsx`** (Lines 1-84)
  - Uses `userProfile` to check role access
  - If `userProfile` becomes null mid-session, user loses access to role-protected pages

- **`frontend/src/components/ui/FKSidebar.tsx`** (Lines 1-262)
  - Uses `userProfile` to determine which departments to show (line 83, 132)
  - If `userProfile` becomes null, sidebar shows "No departments available" message

- **`frontend/src/pages/operations/OperationsContractsColombia.tsx`** (Lines 1-169)
  - Contract generation modules that "disappear" as described in the bug
  - Page is protected by role-based access control
  - If auth state is lost, the page may render empty or redirect

- **`frontend/src/pages/legal/LegalDashboard.tsx`** (Lines 1-193)
  - Legal dashboard that loads contract stats via API
  - If auth is lost mid-session, API calls fail and page content disappears

### Hook Files

- **`frontend/src/hooks/useAuth.ts`** (Lines 1-28)
  - Simple hook that returns AuthContext
  - No changes needed, but used throughout the app

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Comprehensive Auth Event Logging
- Enhance logging in `AuthContext.tsx` to track all Supabase auth events with timestamps
- Add logging for TOKEN_REFRESHED, SIGNED_IN, SIGNED_OUT, USER_UPDATED events
- Log when auth state changes in React (user, session, userProfile) with before/after values
- Add logging for session validation checks (success/failure, token expiry time)
- This will help diagnose exactly when and why auth state is lost

### Step 2: Handle TOKEN_REFRESHED Event in AuthContext
- Modify `onAuthStateChange` handler in `AuthContext.tsx` (line 135-158)
- Currently ignores `INITIAL_SESSION` event - keep this behavior
- Add explicit handling for `TOKEN_REFRESHED` event to update session state
- Ensure that when Supabase auto-refreshes the token, React state is immediately updated
- Log the new token expiry time for debugging

### Step 3: Add Periodic Session Validation
- Add a `useEffect` in `AuthContext.tsx` that runs a validation check every 5 minutes
- Validation check should:
  - Call `supabase.auth.getSession()` to get the actual current session
  - Compare with React state's `session`
  - If they differ, update React state to match Supabase (recovery mechanism)
  - Log any discrepancies found
- This catches cases where `onAuthStateChange` missed an event

### Step 4: Add Window Focus Session Validation
- Add a window focus event listener in `AuthContext.tsx`
- When user returns to the tab (window gains focus), validate the session
- Call `supabase.auth.getSession()` and update state if needed
- This handles cases where the token expired while user was on another tab
- Refresh the session if it's close to expiry (within 5 minutes)

### Step 5: Improve Profile Fetch Error Handling
- Modify `fetchUserProfile` in `AuthContext.tsx` (lines 45-92)
- Currently sets `userProfile` to null on any error (line 79)
- Change behavior to:
  - Only set `userProfile` to null on permanent errors (user not found - PGRST116)
  - For transient errors (network, timeout), keep the existing `userProfile` and log warning
  - Add retry logic (1 retry with exponential backoff) for transient errors
- This prevents losing user access due to temporary network issues

### Step 6: Synchronize apiClient Session Cache with AuthContext
- Modify `apiClient.ts` to subscribe to AuthContext changes instead of maintaining separate cache
- Remove the separate `onAuthStateChange` listener in apiClient (lines 34-38)
- Change `cachedSession` to be updated by a function exported from AuthContext
- OR: Remove cached session entirely and make requests fetch from Supabase synchronously
- Ensure that when AuthContext updates, apiClient immediately gets the new session

### Step 7: Add Session Validation Before Critical Operations
- In `legalService.ts`, `operationsService.ts`, and other service files
- Before making API calls that require authentication (POST, PUT, DELETE operations)
- Add a call to validate/refresh session: `await supabase.auth.getSession()`
- This ensures the token is fresh before critical operations
- Prevents 401 errors mid-operation

### Step 8: Add Recovery Mechanism to ProtectedRoute
- Modify `ProtectedRoute.tsx` (lines 25-69)
- Before redirecting to `/login` when `!isAuthenticated` (line 63)
- Add a recovery check:
  - Call `supabase.auth.getSession()` to verify if a valid session exists in storage
  - If session exists but React state says not authenticated, this is a desynchronization bug
  - Trigger a manual state update in AuthContext (via a new `revalidateSession()` method)
  - Wait briefly for state to update, then re-check `isAuthenticated`
  - Only redirect to login if truly no valid session exists
- This prevents false redirects when session exists but state is stale

### Step 9: Add AuthContext revalidateSession Method
- Add a new method `revalidateSession` to `AuthContext.tsx`
- Method should:
  - Fetch current session from `supabase.auth.getSession()`
  - Update all React state (user, session, userProfile) based on the fetched session
  - Call `fetchUserProfile` if session is valid
  - Return a boolean indicating if a valid session was found
- Export this method in `AuthContextType` interface
- This allows components to manually trigger a state resync when they detect issues

### Step 10: Add Auth State Debugging UI (Development Only)
- Add a debug panel in `FKTopNavbar.tsx` (or create a new debug component)
- Only visible in development mode (`import.meta.env.DEV`)
- Shows:
  - Current auth state (isAuthenticated, user.id, userProfile.role)
  - Session expiry time (countdown timer)
  - Last auth event received
  - Button to manually trigger revalidation
- Helps developers quickly identify auth state issues during testing

### Step 11: Test Session Persistence Across Token Refresh
- Start the app locally: `cd frontend && npm run dev`
- Log in with valid credentials
- Use browser DevTools Application tab → Local Storage → Supabase keys
- Find the session object and note the `expires_at` timestamp
- Wait for token to approach expiry (Supabase typically refreshes 60 seconds before)
- Verify that:
  - TOKEN_REFRESHED event is logged in console
  - React state updates with new session (check auth debug panel or logs)
  - User remains authenticated without interruption
  - No components lose their content

### Step 12: Test Session Recovery After Desynchronization
- Log in to the app
- Open browser DevTools → Application → Local Storage
- Manually edit the Supabase session key to add 1 hour to `expires_at` (simulate drift)
- Observe that within 5 minutes, the periodic validation detects the mismatch
- Verify that React state updates to match the actual session
- Verify no user-visible disruption occurs

### Step 13: Test Session Validation on Window Focus
- Log in to the app
- Switch to another browser tab or application for 10+ minutes
- Return to the Finkargo app tab (window gains focus)
- Verify that session validation is triggered (check console logs)
- Verify that if token is expired or near expiry, it's refreshed
- Verify user remains authenticated and can continue working

### Step 14: Test Profile Fetch Error Resilience
- Log in to the app
- Simulate a network error during profile fetch:
  - Use browser DevTools → Network → Throttling → Offline
  - Trigger a component remount (navigate between pages)
  - Set back to Online
- Verify that `userProfile` is not set to null
- Verify that user still has access to role-protected content
- Verify that retry logic eventually fetches the profile

### Step 15: Run Validation Commands
- Execute all validation commands below to ensure the bug is fixed with zero regressions
- Verify TypeScript compilation succeeds
- Verify no new console errors or warnings
- Verify build succeeds
- Test on production (Vercel) deployment

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

```bash
# 1. TypeScript type checking - must pass with no errors
cd frontend && npx tsc --noEmit

# 2. Lint the modified files - must pass with no errors
cd frontend && npx eslint src/contexts/AuthContext.tsx src/api/clients/apiClient.ts src/services/supabase.ts src/components/ProtectedRoute.tsx

# 3. Build the frontend - must succeed without errors
cd frontend && npm run build

# 4. Run development server and test authentication flow
cd frontend && npm run dev
# Then manually test:
# - Log in with valid credentials
# - Wait 10+ minutes while using the app (simulate token refresh)
# - Switch browser tabs and return (test window focus validation)
# - Refresh the page (test session recovery on mount)
# - Verify contract modules remain visible throughout
# - Check console for auth event logs (should see TOKEN_REFRESHED events)

# 5. Test with network disruption
# - While logged in, open DevTools → Network → Offline
# - Navigate between pages
# - Set back to Online
# - Verify user remains authenticated
# - Verify profile is not lost

# 6. Test token expiry simulation
# - Log in and note the token expiry time from console logs
# - Use browser DevTools to manually edit localStorage session expiry
# - Verify that periodic validation catches the issue
# - Verify that state is resynchronized automatically

# 7. Backend server tests (if applicable)
cd backend && pytest tests/ -v
```

## Notes

### Supabase Token Lifecycle
- **Access Token**: JWT token with 1 hour default expiry
- **Refresh Token**: Long-lived token used to get new access tokens
- **Auto Refresh**: Supabase client refreshes ~60 seconds before expiry when `autoRefreshToken: true`
- **Refresh Event**: Fires `TOKEN_REFRESHED` event via `onAuthStateChange` listener

### Auth State Change Events
Supabase fires these events that we must handle:
- `INITIAL_SESSION` - First load (currently ignored to prevent duplicate fetches)
- `SIGNED_IN` - User signs in (handled)
- `SIGNED_OUT` - User signs out (handled)
- `TOKEN_REFRESHED` - Token auto-refreshed (NEEDS TO BE HANDLED)
- `USER_UPDATED` - User metadata changed (currently may not be handled)
- `PASSWORD_RECOVERY` - Password reset flow (not relevant for this bug)

### Critical Configuration (Already Correct)
**In `frontend/src/services/supabase.ts`:**
```typescript
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,      // ✅ Automatic token refresh enabled
    persistSession: true,         // ✅ Session saved to localStorage
    detectSessionInUrl: true,     // ✅ OAuth callback handling
    storage: window.localStorage, // ✅ Explicit storage location
  },
});
```

### Session Validation Best Practices
1. **Proactive**: Validate before token expires, not after
2. **Periodic**: Check every 5 minutes to catch missed events
3. **On Focus**: Validate when user returns to tab (they may have been away for hours)
4. **On Critical Operations**: Validate before important API calls
5. **Defensive**: Don't trust that state is always synchronized

### Testing Token Refresh Locally
To test token refresh without waiting 1 hour:
1. Modify Supabase project settings (if you have access) to set token expiry to 5 minutes
2. OR: Use browser DevTools to manually change the `expires_at` in localStorage
3. OR: Wait for the default 1-hour expiry (use a timer)

### Logging Strategy
All auth-related logs should be prefixed for easy filtering:
- `[AuthContext]` - React state management
- `[apiClient]` - API request/response handling
- `[supabase]` - Supabase client operations
- `[SessionValidation]` - Periodic validation checks

Example console filter in DevTools: `/\[(AuthContext|apiClient|SessionValidation)\]/`

### Production Monitoring Recommendations
After deploying this fix, monitor production for:
1. Frequency of `TOKEN_REFRESHED` events (should happen every ~55 minutes per user)
2. Frequency of session validation discrepancies (should be zero or very rare)
3. Frequency of profile fetch errors (should be very rare)
4. User reports of "token lost mid-session" (should stop after this fix)

Consider adding error tracking (e.g., Sentry) to capture:
- Cases where periodic validation finds mismatched state
- Cases where window focus triggers a session refresh
- Cases where profile fetch fails multiple times

### Performance Considerations
- Periodic validation (every 5 minutes) has minimal performance impact
- Window focus validation only runs when user returns to tab (user-initiated)
- Session checks are fast (reading from localStorage, not network calls)
- Profile fetch retries add latency only when errors occur (rare)

### Related Issues
This fix should also resolve:
- Users getting unexpectedly redirected to login after period of inactivity
- "Access Denied" pages appearing for users who should have access
- Sidebar showing "No departments available" when user has valid role
- API calls failing with 401 despite user being logged in

### Future Enhancements (Not in Scope)
1. Implement a global "session expired" modal instead of silent redirects
2. Add a "keep me logged in" option with longer session duration
3. Implement refresh token rotation for enhanced security
4. Add biometric/WebAuthn re-authentication for sensitive operations
5. Add session analytics dashboard for admins
6. Implement concurrent session detection (same user on multiple devices)
