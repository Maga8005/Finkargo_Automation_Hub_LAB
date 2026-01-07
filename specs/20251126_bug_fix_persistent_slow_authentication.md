# Bug: Persistent Slow Authentication (25-30 seconds)

## Bug Description
Despite a previous optimization attempt that added profile caching, authentication on login or page refresh still takes approximately 25-30 seconds. Users experience an extended loading spinner when logging in or refreshing an authenticated page. The previous fix (profile caching, reduced timeouts, non-blocking `last_login` update) did not sufficiently address the root cause.

**Symptoms:**
- Login button shows spinner for 25-30 seconds before redirect
- Page refresh with valid session shows loading spinner for 25-30 seconds
- Browser DevTools shows multiple sequential network requests to Supabase
- Console logs show profile being fetched multiple times

**Expected behavior:**
- Login should complete in <2 seconds
- Page refresh with cached session should render in <1 second
- Single profile fetch per authentication event

## Problem Statement
The authentication flow has multiple overlapping initialization patterns that cause redundant Supabase API calls and sequential blocking operations:

1. **Multiple `getSession()` calls competing on startup**: `apiClient.ts` IIFE and `AuthContext.tsx` `initializeAuth` both call `supabase.auth.getSession()` independently
2. **Profile fetch not using cache in `onAuthStateChange` handler**: When `SIGNED_IN` event fires, profile is fetched from database even if a valid cache exists
3. **`fetchUserProfile` called without checking existing `userProfile` state**: The `onAuthStateChange` handler always fetches profile on `SIGNED_IN`, ignoring any cached or in-memory profile
4. **Potential Supabase client cold start**: First request to Supabase after app load may have connection establishment overhead
5. **Render Hosting Cold Start**: If using Render free tier, backend may have 30-second cold start delay affecting profile fetch

## Solution Statement
Implement aggressive profile caching and eliminate redundant network calls:

1. **Use cached profile in `onAuthStateChange` handler**: Check localStorage cache before network fetch
2. **Skip profile re-fetch if already in memory**: If `userProfile` matches current user, skip fetch
3. **Parallelize session and profile loading**: Start profile cache check immediately, don't wait for session
4. **Add loading state debounce**: Prevent multiple loading state toggles causing re-renders
5. **Pre-warm Supabase connection**: Initialize Supabase client eagerly in service worker or early script
6. **Optimize `lastLoginTimestamp` ref access**: Ensure ref is read correctly in context value

## Steps to Reproduce
1. Clear browser localStorage and sessionStorage
2. Open the Finkargo Automation Hub login page (`/login`)
3. Open browser DevTools Network tab
4. Enter valid credentials and click "Iniciar sesion"
5. Observe network requests and timing:
   - Multiple `getSession()` calls
   - Sequential profile fetch requests
   - Total time: 25-30 seconds

Alternative reproduction (page refresh):
1. Log in to the application
2. With DevTools open, hard refresh the page (Cmd+Shift+R / Ctrl+Shift+R)
3. Observe loading spinner duration and network waterfall
4. Total time: 25-30 seconds

## Root Cause Analysis

### Primary Cause: Profile Fetch in `onAuthStateChange` Ignores Cache
**Location**: `frontend/src/contexts/AuthContext.tsx:400-406`

```typescript
if (newSession?.user) {
  console.log('[AuthContext] Fetching profile for user:', newSession.user.id);
  await fetchUserProfile(newSession.user.id); // Always fetches from network!
}
```

The `SIGNED_IN` event handler ALWAYS fetches profile from database, even when:
- A valid cached profile exists in localStorage
- The `userProfile` state already has the correct profile

This causes a full round-trip to Supabase database after EVERY successful login.

### Secondary Cause: `initializeAuth` and `onAuthStateChange` Race Condition
**Location**: `frontend/src/contexts/AuthContext.tsx:312-355` and `358-418`

Both `initializeAuth()` and the `onAuthStateChange` subscription attempt to:
1. Get session from Supabase
2. Fetch user profile

When the app loads with a valid session:
1. `initializeAuth()` runs and fetches session + profile
2. `onAuthStateChange` fires with `INITIAL_SESSION` (ignored)
3. But subsequent events like `TOKEN_REFRESHED` may trigger profile fetch again

### Tertiary Cause: No Early Exit for Known User
**Location**: `frontend/src/contexts/AuthContext.tsx:400-406`

The `onAuthStateChange` handler doesn't check if the incoming user ID matches the current `userProfile.id`. Even if we already have the profile for user X, signing in as user X triggers another profile fetch.

### Quaternary Cause: `apiClient.ts` IIFE Competing for Session
**Location**: `frontend/src/api/clients/apiClient.ts:27-36`

```typescript
(async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    // ...
  }
})();
```

This IIFE runs immediately on module load, competing with `AuthContext` for the session. While not directly causing the 25-30s delay, it adds unnecessary network calls.

### Quinary Cause: Backend Cold Start (Render Free Tier)
If deployed on Render free tier, the backend server sleeps after 15 minutes of inactivity. First request wakes it up, adding up to 30 seconds delay. The profile fetch goes through Supabase, but if any middleware or logging hits the backend, this delay manifests.

**Note**: Based on the 25-30 second specific timing, this is likely the PRIMARY cause. Supabase queries themselves are fast (<500ms), so a 25-30 second delay suggests external factor like Render cold start OR:

### Sexiary Cause: Supabase GoTrue Server Cold Start
Supabase's auth server (GoTrue) may also have cold start behavior for inactive projects on free tier, adding significant delay to `getSession()` and `signInWithPassword()` calls.

## Relevant Files
Use these files to fix the bug:

### Core Files to Modify

- **`frontend/src/contexts/AuthContext.tsx`**
  - Add cache check in `onAuthStateChange` handler before profile fetch
  - Add early exit if `userProfile.id` matches incoming user
  - Optimize initialization flow to avoid duplicate session calls
  - Add timing logs to diagnose where delay occurs

- **`frontend/src/api/clients/apiClient.ts`**
  - Remove or defer the IIFE that calls `getSession()` on module load
  - Let `AuthContext` be the single source of truth for session

- **`frontend/src/services/supabase.ts`**
  - Add timing logs to Supabase operations for diagnosis
  - Consider adding connection warmup

### New Files

- **`frontend/src/utils/performanceLogger.ts`** (optional)
  - Add performance timing utilities for diagnosis

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Performance Timing Logs

Add timestamp-based logging to identify the actual bottleneck:

- In `AuthContext.tsx`, add `console.time()` / `console.timeEnd()` around:
  - `supabase.auth.getSession()` call in `initializeAuth`
  - `supabase.auth.signInWithPassword()` call (in supabase.ts `signIn`)
  - `fetchUserProfile()` calls
  - Total `initializeAuth` duration
- This will identify whether delay is in Supabase auth, profile fetch, or elsewhere

### Step 2: Use Cached Profile in onAuthStateChange Handler

Modify the `onAuthStateChange` handler to check cache before fetching:

```typescript
// In SIGNED_IN and other events that need profile
if (newSession?.user) {
  const userId = newSession.user.id;

  // Check if we already have this user's profile in state
  if (userProfile && userProfile.id === userId) {
    console.log('[AuthContext] Profile already in memory, skipping fetch');
    setLoading(false);
    return;
  }

  // Check localStorage cache
  const cachedProfile = getCachedProfile(userId);
  if (cachedProfile) {
    console.log('[AuthContext] Using cached profile from onAuthStateChange');
    setUserProfile(cachedProfile);
    setLoading(false);
    // Background refresh
    fetchUserProfile(userId, 0, true).catch(console.warn);
    return;
  }

  // No cache, fetch from server
  await fetchUserProfile(userId);
}
```

### Step 3: Remove apiClient.ts IIFE Session Call

Remove or comment out the IIFE in `apiClient.ts` that calls `getSession()` on module load:

```typescript
// REMOVED: Competing session call
// (async () => {
//   try {
//     const { data: { session } } = await supabase.auth.getSession();
//     cachedSession = session;
//     lastCacheUpdate = Date.now();
//   } catch (error) {}
// })();
```

Instead, let the `onAuthStateChange` listener handle session caching.

### Step 4: Optimize handleSignIn to Set Profile from Cache

After successful sign-in, immediately check cache and set profile:

```typescript
const handleSignIn = async (email: string, password: string): Promise<void> => {
  console.time('[AuthContext] Total signIn');
  setIsTransitioning(true);
  lastLoginTimestampRef.current = Date.now();

  try {
    console.time('[AuthContext] supabaseSignIn');
    const { user: signedInUser, session: signedInSession, error } = await supabaseSignIn(email, password);
    console.timeEnd('[AuthContext] supabaseSignIn');

    if (error) {
      setIsTransitioning(false);
      throw new Error(error.message);
    }

    // Immediately set session and user to unblock UI
    if (signedInSession && signedInUser) {
      setSession(signedInSession);
      setUser(signedInUser);

      // Try to use cached profile immediately
      const cachedProfile = getCachedProfile(signedInUser.id);
      if (cachedProfile) {
        setUserProfile(cachedProfile);
        setLoading(false);
        setIsTransitioning(false);
        console.log('[AuthContext] Login complete with cached profile');
        console.timeEnd('[AuthContext] Total signIn');

        // Background refresh
        fetchUserProfile(signedInUser.id, 0, true).catch(console.warn);

        // Non-blocking last_login update
        supabase.from('user_profiles')
          .update({ last_login: new Date().toISOString() })
          .eq('id', signedInUser.id)
          .then(({ error }) => { if (error) console.warn('[AuthContext] last_login update failed:', error); });

        return;
      }
    }

    // No cache - let onAuthStateChange handle profile fetch
    // Non-blocking last_login update
    if (signedInUser) {
      supabase.from('user_profiles')
        .update({ last_login: new Date().toISOString() })
        .eq('id', signedInUser.id)
        .then(({ error }) => { if (error) console.warn('[AuthContext] last_login update failed:', error); });
    }

    console.timeEnd('[AuthContext] Total signIn');
  } catch (error) {
    console.timeEnd('[AuthContext] Total signIn');
    console.error('[AuthContext] Sign in error:', error);
    setIsTransitioning(false);
    throw error;
  }
};
```

### Step 5: Add Supabase Connection Warmup

Add an early, non-blocking call to warm up Supabase connection:

In `frontend/src/services/supabase.ts`, add after client creation:

```typescript
// Warm up connection (non-blocking)
setTimeout(() => {
  supabase.auth.getSession().then(() => {
    console.log('[Supabase] Connection warmed up');
  }).catch(() => {
    console.log('[Supabase] Warmup call completed (may have failed)');
  });
}, 0);
```

### Step 6: Implement Session-Based Early Exit in initializeAuth

Optimize `initializeAuth` to set loading=false earlier when cache is used:

```typescript
const initializeAuth = async () => {
  console.time('[AuthContext] initializeAuth');
  try {
    console.time('[AuthContext] getSession');
    const { data: { session: initialSession }, error } = await supabase.auth.getSession();
    console.timeEnd('[AuthContext] getSession');

    if (error) {
      console.error('[AuthContext] Error getting initial session:', error);
    }

    setSession(initialSession);
    setUser(initialSession?.user ?? null);

    if (initialSession?.user) {
      const userId = initialSession.user.id;
      const cachedProfile = getCachedProfile(userId);

      if (cachedProfile) {
        setUserProfile(cachedProfile);
        setLoading(false); // CRITICAL: Set loading false BEFORE background fetch
        console.log('[AuthContext] Loaded from cache, loading=false');
        console.timeEnd('[AuthContext] initializeAuth');

        // Background refresh (don't await)
        fetchUserProfile(userId, 0, true).catch(err => {
          console.warn('[AuthContext] Background refresh failed:', err);
        });
        return;
      }

      // No cache - must wait for profile
      console.time('[AuthContext] fetchUserProfile (no cache)');
      await fetchUserProfile(userId, 0, true);
      console.timeEnd('[AuthContext] fetchUserProfile (no cache)');
    }
  } catch (error) {
    console.error('[AuthContext] Error initializing auth:', error);
  } finally {
    setLoading(false);
    console.timeEnd('[AuthContext] initializeAuth');
  }
};
```

### Step 7: Diagnose Render Cold Start

If timing logs show the delay is in the first `getSession()` call or first Supabase query:

- Check Render dashboard for cold start metrics
- Consider upgrading to paid tier to avoid cold starts
- Or implement a keep-alive ping to prevent sleep

Add a diagnostic log:

```typescript
// In AuthContext.tsx initialization
console.log('[AuthContext] Init started at:', new Date().toISOString());
```

### Step 8: Test and Validate

- Clear localStorage and test fresh login
- Test with cached profile (page refresh)
- Test logout and re-login
- Check console timing logs to identify remaining bottlenecks

### Step 9: Run Validation Commands

Execute all validation commands to ensure the fix works.

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cd frontend && npx tsc --noEmit` - TypeScript type checking must pass
- `cd frontend && npm run build` - Production build must succeed
- `cd frontend && npm run dev` - Start dev server and test:
  - **Fresh login timing**: Clear localStorage, login, measure time from click to home page
  - **Cached login timing**: Refresh page, measure time from load to content visible
  - **Console timing**: Check `console.time` outputs for breakdown
  - **Network tab**: Verify reduced number of Supabase calls
- **Expected results**:
  - Fresh login (no cache): <3 seconds (limited by Supabase auth)
  - Cached login (page refresh): <1 second
  - No duplicate profile fetch requests in Network tab

## Notes

### Diagnosing the 25-30 Second Delay

The specific 25-30 second timing strongly suggests one of:

1. **Render Free Tier Cold Start**: Backend sleeps after inactivity, wakes on first request
2. **Supabase Free Tier Cold Start**: Auth server may have similar behavior
3. **Network timeout + retry**: Some operation timing out and retrying

To diagnose:
1. Add `console.time()` logs as described in Step 1
2. Check which specific operation takes 25+ seconds
3. If it's `getSession()` or `signInWithPassword()`, the issue is Supabase/Render cold start
4. If it's `fetchUserProfile()`, the issue is database query cold start

### Mitigation for Cold Start (If Confirmed)

If cold start is confirmed as the cause:

1. **Keep-alive ping**: Add a cron job or client-side interval that pings the backend every 10 minutes
2. **Upgrade Render tier**: Paid tier keeps servers warm
3. **Edge functions**: Move auth to edge for lower latency
4. **Optimistic UI**: Show cached content immediately, update when fresh data arrives

### Profile Cache TTL

Current TTL is 5 minutes. This is appropriate because:
- User profile data (name, role) changes rarely
- Background refresh ensures eventual consistency
- 5 minutes prevents stale data for role changes

### Race Condition Prevention

The optimized flow handles these race conditions:
- `handleSignIn` completing before `onAuthStateChange` fires
- Multiple `onAuthStateChange` events for single login
- Concurrent `fetchUserProfile` calls (existing `fetchingProfileRef` handles this)

### Testing Checklist

- [ ] Login with fresh browser (no cache) - should be <3s
- [ ] Page refresh with valid session - should be <1s
- [ ] Logout and re-login - cache should be cleared and rebuilt
- [ ] Multiple rapid logins - no duplicate profile fetches
- [ ] Token refresh (wait 55 minutes) - should use cached profile
- [ ] Network offline then online - should recover gracefully
