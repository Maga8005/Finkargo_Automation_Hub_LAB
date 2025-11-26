# Implementation Report: Persistent Slow Authentication Fix v2

**Date:** 2025-11-26
**Module:** Authentication
**Issue:** Authentication taking 25-30 seconds on login or page refresh
**Plan:** `specs/20251126_bug_fix_persistent_slow_authentication.md`

## Summary

Implemented aggressive profile caching and eliminated redundant network calls to fix the persistent 25-30 second authentication delay. The previous fix (v1) added basic caching but didn't address all sources of redundant fetches.

## Changes Made

### 1. AuthContext.tsx - Comprehensive Optimization

- **Added `currentProfileIdRef`**: New ref to track which user's profile is currently loaded, preventing redundant fetches
- **Added performance timing logs**: `console.time()`/`console.timeEnd()` around all critical operations for diagnosis:
  - `initializeAuth` total duration
  - `getSession` call
  - `fetchUserProfile` with user ID
  - `supabaseSignIn` call
  - `Total signIn` duration
- **Early exit in `fetchUserProfile`**: Skips fetch if `currentProfileIdRef.current === userId`
- **Cache usage in `onAuthStateChange`**:
  - Checks in-memory ref first (`currentProfileIdRef`)
  - Falls back to localStorage cache (`getCachedProfile`)
  - Only fetches from network if no cache exists
- **Optimized `handleSignIn`**:
  - Immediately sets session/user to unblock UI
  - Uses cached profile if available for instant login completion
  - Background refresh doesn't block UI
- **Explicit `SIGNED_OUT` handling**: Clears all state and refs properly
- **`TOKEN_REFRESHED` no longer triggers profile fetch**: Profile remains valid on token refresh

### 2. apiClient.ts - Removed Competing Session Call

- **Removed IIFE**: The immediate `getSession()` call on module load was competing with AuthContext
- **Increased cache TTL**: From 1 second to 5 seconds to reduce `getSession()` frequency
- **Simplified comments**: Clarified that `onAuthStateChange` is the primary cache population mechanism

### 3. supabase.ts - Connection Warmup

- **Added connection warmup**: Non-blocking `setTimeout(..., 0)` call to `getSession()`
- **Added timing logs**: Shows warmup duration and session status
- **Pre-establishes connection**: Reduces latency on first real auth call

## Files Changed

```
frontend/src/api/clients/apiClient.ts              |  24 ++--
frontend/src/contexts/AuthContext.tsx              | 158 ++++++++++++++++-----
frontend/src/services/supabase.ts                  |  18 +++
```

**Total: 3 files changed, 156 insertions(+), 49 deletions(-)**

## Validation

- TypeScript compilation: PASSED (`npx tsc --noEmit`)
- Production build: PASSED (`npm run build`)
- Dev server: Running on http://localhost:5173

## Expected Performance Improvements

| Scenario | Before | After (Expected) |
|----------|--------|------------------|
| Fresh login (no cache) | 25-30s | <3s |
| Login with cache | 25-30s | <500ms |
| Page refresh (cached) | 25-30s | <500ms |
| Page refresh (no cache) | 25-30s | <3s |

## Timing Diagnostics

The following console timers are now available for debugging:

- `[AuthContext] Total initialization` - Full init duration
- `[AuthContext] initializeAuth` - Auth init function duration
- `[AuthContext] getSession` - Supabase session fetch
- `[AuthContext] fetchUserProfile {userId}` - Profile fetch duration
- `[AuthContext] Total signIn` - Login flow duration
- `[AuthContext] supabaseSignIn` - Supabase auth call duration
- `[Supabase] Connection warmup` - Initial connection establishment

## Root Causes Addressed

1. **Profile fetch in `onAuthStateChange` ignoring cache** - Now checks ref and localStorage first
2. **No early exit for known user** - Added `currentProfileIdRef` check
3. **Competing `getSession()` in apiClient.ts** - Removed IIFE
4. **No connection warmup** - Added non-blocking warmup call
5. **Redundant profile fetch on `TOKEN_REFRESHED`** - Removed unnecessary fetch

## Testing Checklist

- [ ] Login with fresh browser (clear localStorage) - should be <3s
- [ ] Page refresh with valid session - should be <500ms
- [ ] Logout and re-login - cache should be cleared and rebuilt
- [ ] Check console timing logs for detailed breakdown
- [ ] Verify single profile fetch in Network tab (not multiple)

## Notes

If 25-30 second delays persist after this fix, the likely cause is:
1. **Render free tier cold start** - Backend server sleeping
2. **Supabase free tier cold start** - Auth server latency

In that case, consider:
- Implementing a keep-alive ping to prevent server sleep
- Upgrading to paid hosting tier
- Adding a loading indicator with progress feedback
