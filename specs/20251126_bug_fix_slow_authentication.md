# Bug: Slow Authentication

## Bug Description
When logging in to the Finkargo Automation Hub, the authentication process takes several seconds to complete. The site displays a loading spinner for an extended period before finally allowing the user to access the application modules. This delay impacts user experience, particularly for admin users who need quick access to contract generation or finance invoicing functionalities.

The authentication process feels sluggish compared to modern web application standards. Users expect near-instantaneous login with immediate access to protected content, but currently experience noticeable delays during:
1. Initial page load when already authenticated (checking session + fetching profile)
2. Login form submission (authenticating + fetching profile + redundant state updates)
3. Navigation to protected routes (session recovery attempts)

## Problem Statement
The authentication flow has multiple performance bottlenecks that cause unnecessary delays:

1. **Sequential Network Calls**: Session validation and profile fetching happen sequentially instead of being optimized
2. **Redundant Profile Fetches**: The profile is fetched multiple times during login (once in `handleSignIn` indirectly via `onAuthStateChange`, once on `last_login` update)
3. **Unnecessary Session Recovery**: `ProtectedRoute` triggers session revalidation even when the user just logged in, adding another round of network calls
4. **Excessive Timeout**: Profile fetch has a 10-second timeout which, while defensive, doesn't help with the common case of slow initial loads
5. **Synchronous State Updates**: Multiple `setState` calls cause re-renders before the user can see content
6. **100ms Artificial Delay**: The `handleSignIn` function has a hardcoded 100ms `await` to wait for `onAuthStateChange`

## Solution Statement
Optimize the authentication flow to reduce the time between login/page load and content display:

1. **Parallelize Operations**: Where possible, run session validation and profile fetching concurrently
2. **Cache Profile in LocalStorage**: Store the user profile in localStorage alongside the Supabase session to enable instant display on subsequent visits
3. **Skip Redundant Recovery**: Don't trigger session recovery in `ProtectedRoute` when auth state is still initializing
4. **Optimize Profile Fetch**: Reduce timeout for initial load (3 seconds), use cached profile while fetching fresh data
5. **Batch State Updates**: Use React 18's automatic batching or explicit batching to reduce re-renders
6. **Remove Artificial Delays**: Remove the 100ms wait in `handleSignIn`
7. **Lazy Load Non-Critical Data**: Fetch `last_login` update asynchronously without blocking login

## Steps to Reproduce
1. Open the Finkargo Automation Hub login page (`/login`)
2. Enter valid credentials (e.g., admin user)
3. Click "Iniciar sesion" button
4. Observe the loading spinner duration before being redirected to the home page
5. Expected: Near-instant redirect (<1 second)
6. Actual: 2-5 seconds of loading before redirect

Alternative reproduction:
1. Log in to the application
2. Close and reopen the browser (or clear in-memory state without clearing localStorage)
3. Navigate to the application URL
4. Observe loading duration before seeing the authenticated content
5. Expected: Near-instant content display (<1 second)
6. Actual: 2-4 seconds of loading before content appears

## Root Cause Analysis

### Primary Cause: Sequential Profile Fetch After Session Validation
**Location**: `frontend/src/contexts/AuthContext.tsx:217-238`

The initialization flow is:
```typescript
const initializeAuth = async () => {
  const { data: { session: initialSession } } = await supabase.auth.getSession(); // Network call 1
  setSession(initialSession);
  setUser(initialSession?.user ?? null);

  if (initialSession?.user) {
    await fetchUserProfile(initialSession.user.id); // Network call 2 (sequential)
  }
  setLoading(false);
};
```

These two network calls happen sequentially. The profile fetch only starts after the session is retrieved, adding latency.

### Secondary Cause: Profile Fetch Timeout and Retry Logic
**Location**: `frontend/src/contexts/AuthContext.tsx:50-121`

The `fetchUserProfile` function has:
- 10-second timeout (generous but adds perceived latency when server is slow)
- 1 retry with 1-second delay between attempts
- This means worst-case profile fetch can take 22+ seconds (10s timeout + 1s delay + 10s retry + error handling)

For typical cases, the profile fetch is fast, but the perceived slowness comes from:
1. Waiting for session validation first
2. Then starting the profile fetch
3. Then updating state multiple times

### Tertiary Cause: Redundant Session Recovery in ProtectedRoute
**Location**: `frontend/src/components/ProtectedRoute.tsx:45-68`

When the user navigates to a protected route:
```typescript
useEffect(() => {
  const attemptRecovery = async () => {
    if (!isAuthenticated && !loading && !recoveryAttempted && !isRecovering) {
      // This triggers even right after login when state is still propagating
      const recovered = await revalidateSession(); // Another network call
    }
  };
  attemptRecovery();
}, [isAuthenticated, loading, recoveryAttempted, isRecovering, revalidateSession]);
```

This recovery mechanism is valuable for mid-session auth loss but causes unnecessary delays during normal login flow. After `handleSignIn` completes, there's a brief moment where `isAuthenticated` might be `false` while React state is updating, triggering a redundant recovery attempt.

### Quaternary Cause: Artificial 100ms Delay in handleSignIn
**Location**: `frontend/src/contexts/AuthContext.tsx:405-407`

```typescript
// Wait a bit for it to process
await new Promise(resolve => setTimeout(resolve, 100));
```

This 100ms delay was added to wait for `onAuthStateChange` to fire, but it adds unnecessary latency. The login flow should complete without artificial delays.

### Quinary Cause: last_login Update Blocking Login
**Location**: `frontend/src/contexts/AuthContext.tsx:397-403`

```typescript
// Update last login timestamp
if (signedInUser) {
  await supabase
    .from('user_profiles')
    .update({ last_login: new Date().toISOString() })
    .eq('id', signedInUser.id);
}
```

This database update happens synchronously during login, adding another network round-trip before the user can access the app.

## Relevant Files
Use these files to fix the bug:

### Core Files to Modify

- **`frontend/src/contexts/AuthContext.tsx`**
  - Primary file for auth state management
  - Need to optimize initialization flow (`initializeAuth` function)
  - Need to implement profile caching in localStorage
  - Need to remove 100ms artificial delay
  - Need to make `last_login` update non-blocking
  - Need to reduce profile fetch timeout for initial load

- **`frontend/src/components/ProtectedRoute.tsx`**
  - Need to add logic to skip recovery when auth is initializing
  - Need to distinguish between "just logged in" vs "mid-session auth loss"

- **`frontend/src/services/supabase.ts`**
  - May need to add helper functions for profile caching

### Supporting Files (Read-Only Reference)

- **`frontend/src/pages/LoginPage.tsx`**
  - Uses `signIn` from AuthContext - no changes needed
  - Shows loading state while `isSubmitting || loading` is true

- **`frontend/src/hooks/useAuth.ts`**
  - Simple hook wrapper - no changes needed

- **`frontend/src/types/index.ts`**
  - May need to add types for cached profile if not already present

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Implement Profile Caching in localStorage

- Add constants for cache key and TTL at the top of `AuthContext.tsx`
- Create helper functions `getCachedProfile()` and `setCachedProfile()`
- Cache key should include user ID to support multiple accounts
- Set cache TTL to 5 minutes (profile data changes infrequently)
- Format: `finkargo_profile_cache_${userId}`

### Step 2: Optimize Initialization with Cached Profile

- Modify `initializeAuth` in `AuthContext.tsx`
- After getting session, immediately check for cached profile
- If cached profile exists and matches user ID, use it instantly
- Set `userProfile` from cache, then set `loading` to false
- Start background fetch to refresh the cached profile (don't await)
- This allows instant UI rendering while fresh data loads

### Step 3: Parallelize Session and Profile Fetch for Uncached Case

- If no cached profile exists, still optimize the flow
- Start profile fetch immediately after getting user ID from session
- Don't wait for full session state update before starting profile fetch
- Use Promise.all where appropriate to parallelize independent operations

### Step 4: Reduce Profile Fetch Timeout for Initial Load

- Create a new parameter for `fetchUserProfile`: `isInitialLoad: boolean`
- For initial load, use 3-second timeout instead of 10 seconds
- For background refreshes, keep 10-second timeout
- This reduces worst-case initial load time significantly

### Step 5: Remove Artificial Delay in handleSignIn

- Remove the `await new Promise(resolve => setTimeout(resolve, 100))` line
- The `onAuthStateChange` handler will update state when Supabase fires the event
- No artificial delay is needed - React will batch updates appropriately

### Step 6: Make last_login Update Non-Blocking

- Change the `last_login` update in `handleSignIn` to not use `await`
- Fire the update asynchronously using `.then()` or without awaiting
- Log any errors but don't block the login flow
- The user doesn't need to wait for this metadata update

### Step 7: Skip Redundant Recovery in ProtectedRoute

- Add a timestamp or flag to track when login just completed
- In `ProtectedRoute`, check if we're within 2 seconds of a login event
- If so, skip the recovery attempt and wait for state propagation
- Add a short delay (500ms) before checking auth state after login
- This prevents redundant network calls right after login

### Step 8: Add Auth State Transition Flag

- Add a new state variable `isTransitioning` in AuthContext
- Set `isTransitioning = true` when login starts, `false` when complete
- Export this flag in the context value
- Use it in ProtectedRoute to skip recovery during transitions

### Step 9: Update Profile Cache on Successful Fetch

- After `fetchUserProfile` succeeds, call `setCachedProfile(data)`
- Ensure cache is updated both on login and on background refresh
- Clear cache on logout (`handleSignOut`)

### Step 10: Add Cache Invalidation on Logout

- In `handleSignOut`, clear the profile cache from localStorage
- Clear cache for all users or use a pattern to clear current user's cache
- Ensure no stale profile data persists after logout

### Step 11: Validate Changes with Manual Testing

- Start development server: `npm run dev`
- Test login flow timing with browser DevTools Network tab
- Verify profile cache is being used on subsequent page loads
- Verify fresh data is fetched in background
- Verify no regression in session validation or recovery

### Step 12: Run Validation Commands

- Execute all validation commands to ensure zero regressions
- Verify TypeScript compilation succeeds
- Verify build succeeds
- Test authentication flow end-to-end

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd frontend && npx tsc --noEmit` - TypeScript type checking must pass with no errors
- `cd frontend && npm run build` - Production build must succeed without errors
- `cd frontend && npm run dev` - Start dev server and manually test:
  - Login timing: Should complete in <1.5 seconds
  - Subsequent page loads: Should show content in <500ms with cached profile
  - Logout and login: Should clear cache and work correctly
  - Tab switch and return: Should not trigger redundant fetches
- `cd backend && python -m pytest tests/ -v` - Run backend tests if applicable

## Notes

### Expected Performance Improvement

| Scenario | Before | After |
|----------|--------|-------|
| Initial login | 2-5 seconds | <1.5 seconds |
| Page reload (authenticated) | 2-4 seconds | <500ms |
| Navigation between protected routes | 500ms-2s | <100ms |

### Cache Strategy

The profile caching strategy uses localStorage for several reasons:
1. **Persistence**: Survives page reloads and browser restarts
2. **Synchronous access**: Can be read instantly without async operations
3. **Consistency with Supabase**: Supabase also uses localStorage for session
4. **Size**: Profile data is small (<1KB), well within localStorage limits

### TTL Considerations

The 5-minute TTL for profile cache balances:
- **Freshness**: Profile changes (role updates, name changes) are rare
- **Performance**: Avoids unnecessary network calls
- **Consistency**: Background refresh ensures data is updated

If profile data needs to be more real-time (e.g., for permission changes), the TTL can be reduced or cache can be invalidated on specific events.

### Race Condition Prevention

The optimization must handle these race conditions:
1. **Concurrent fetches**: Use `fetchingProfileRef` to prevent duplicate requests
2. **Stale cache**: Always do background refresh, even with valid cache
3. **Login during initialization**: The `isTransitioning` flag prevents conflicts

### Backward Compatibility

These changes are backward compatible:
- Cache is additive; if not present, falls back to network fetch
- No API changes required
- No database schema changes
- No changes to Supabase configuration

### Browser Support

localStorage is supported in all modern browsers. The caching implementation should:
- Gracefully handle localStorage being unavailable (private browsing)
- Not throw errors if cache is corrupted (use try-catch)
- Fall back to network-only mode if caching fails
