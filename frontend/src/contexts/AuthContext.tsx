/**
 * Authentication Context Provider
 * Manages global authentication state using Supabase Auth
 * Based on proven architecture from Finkargo Pre-Approval System
 *
 * Bug fix: Added comprehensive session validation to prevent auth token loss mid-session
 * Performance fix: Added profile caching and optimized initialization flow
 */
import React, { createContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase, signIn as supabaseSignIn, signUp as supabaseSignUp, signOut as supabaseSignOut } from '../services/supabase';
import type { AuthContextType, UserProfile, UserRole } from '../types';

// Profile cache constants
const PROFILE_CACHE_PREFIX = 'finkargo_profile_cache_';
const PROFILE_CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

// Profile cache helper types
interface CachedProfile {
  profile: UserProfile;
  timestamp: number;
}

/**
 * Get cached profile from localStorage
 */
const getCachedProfile = (userId: string): UserProfile | null => {
  try {
    const cacheKey = `${PROFILE_CACHE_PREFIX}${userId}`;
    const cached = localStorage.getItem(cacheKey);
    if (!cached) return null;

    const { profile, timestamp }: CachedProfile = JSON.parse(cached);
    const now = Date.now();

    // Check if cache is still valid
    if (now - timestamp < PROFILE_CACHE_TTL) {
      console.log('[AuthContext] Using cached profile for user:', userId);
      return profile;
    }

    console.log('[AuthContext] Cached profile expired for user:', userId);
    return null;
  } catch (error) {
    console.warn('[AuthContext] Error reading cached profile:', error);
    return null;
  }
};

/**
 * Set cached profile in localStorage
 */
const setCachedProfile = (userId: string, profile: UserProfile): void => {
  try {
    const cacheKey = `${PROFILE_CACHE_PREFIX}${userId}`;
    const cacheData: CachedProfile = {
      profile,
      timestamp: Date.now(),
    };
    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    console.log('[AuthContext] Cached profile for user:', userId);
  } catch (error) {
    console.warn('[AuthContext] Error caching profile:', error);
  }
};

/**
 * Clear cached profile from localStorage
 */
const clearCachedProfile = (userId?: string): void => {
  try {
    if (userId) {
      const cacheKey = `${PROFILE_CACHE_PREFIX}${userId}`;
      localStorage.removeItem(cacheKey);
      console.log('[AuthContext] Cleared cached profile for user:', userId);
    } else {
      // Clear all profile caches
      const keysToRemove: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(PROFILE_CACHE_PREFIX)) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));
      console.log('[AuthContext] Cleared all cached profiles');
    }
  } catch (error) {
    console.warn('[AuthContext] Error clearing cached profile:', error);
  }
};

// Create context with default values
// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  userProfile: null,
  loading: true,
  isTransitioning: false,
  lastLoginTimestamp: 0,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  isAuthenticated: false,
  revalidateSession: async () => false,
});

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * AuthProvider component - Wrap app with this to provide auth state
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Track if we're currently fetching a profile to prevent concurrent fetches
  const fetchingProfileRef = React.useRef(false);
  // Track initialization to prevent duplicate fetches
  const initializedRef = React.useRef(false);
  // Track login timestamp to prevent redundant recovery attempts
  const lastLoginTimestampRef = React.useRef<number>(0);

  /**
   * Fetch user profile from database with timeout, retry logic, and improved error handling
   * Bug fix: Don't clear userProfile on transient errors (network/timeout), only on permanent errors
   * Performance fix: Added isInitialLoad parameter for shorter timeout on initial load
   */
  const fetchUserProfile = useCallback(async (
    userId: string,
    retryCount = 0,
    isInitialLoad = false
  ): Promise<void> => {
    const MAX_RETRIES = 1;
    const RETRY_DELAY = 1000; // 1 second
    // Use shorter timeout for initial load to improve perceived performance
    const TIMEOUT = isInitialLoad ? 3000 : 10000;

    // Prevent concurrent fetches
    if (fetchingProfileRef.current) {
      console.log('[AuthContext] Profile fetch already in progress, skipping...');
      return;
    }

    fetchingProfileRef.current = true;
    console.log('[AuthContext] Starting profile fetch for user:', userId, retryCount > 0 ? `(retry ${retryCount})` : '', isInitialLoad ? '(initial load)' : '');

    try {
      // Create a timeout promise
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Profile fetch timeout')), TIMEOUT);
      });

      // Race between fetch and timeout
      const fetchPromise = supabase
        .from('user_profiles')
        .select('*')
        .eq('id', userId)
        .single();

      const result = await Promise.race([fetchPromise, timeoutPromise]);
      const { data, error } = result as Awaited<typeof fetchPromise>;

      if (error) {
        console.error('[AuthContext] Error fetching user profile:', error);

        // Permanent error: profile doesn't exist
        if ('code' in error && error.code === 'PGRST116') {
          console.error('[AuthContext] User profile not found in database (PGRST116). User may need to complete registration.');
          setUserProfile(null);
          return;
        }

        // Transient error: network/timeout - retry once, but don't clear existing profile
        if (retryCount < MAX_RETRIES) {
          console.warn('[AuthContext] Transient error fetching profile, will retry in', RETRY_DELAY, 'ms');
          fetchingProfileRef.current = false;
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          return fetchUserProfile(userId, retryCount + 1, isInitialLoad);
        }

        // Max retries reached - log warning but keep existing userProfile
        console.warn('[AuthContext] Max retries reached for profile fetch. Keeping existing profile to prevent auth loss.');
        return;
      }

      console.log('[AuthContext] Profile fetched successfully:', data);
      const profileData = data as UserProfile;
      setUserProfile(profileData);
      // Cache the profile for future use (Step 9)
      setCachedProfile(userId, profileData);
    } catch (error) {
      console.error('[AuthContext] Error fetching user profile:', error);

      // On timeout or network error, try to retry
      if (retryCount < MAX_RETRIES) {
        console.warn('[AuthContext] Network/timeout error, will retry in', RETRY_DELAY, 'ms');
        fetchingProfileRef.current = false;
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return fetchUserProfile(userId, retryCount + 1, isInitialLoad);
      }

      // Max retries reached - log warning but don't clear existing profile
      console.warn('[AuthContext] Max retries reached after exception. Keeping existing profile to prevent auth loss.');
    } finally {
      fetchingProfileRef.current = false;
      console.log('[AuthContext] Profile fetch completed');
    }
  }, []); // Empty deps - function doesn't depend on any state

  /**
   * Revalidate session by fetching current session from Supabase
   * This method allows components to manually trigger session resync
   * Returns true if a valid session was found and state updated
   */
  const revalidateSession = useCallback(async (): Promise<boolean> => {
    console.log('[AuthContext] Manual session revalidation triggered');

    try {
      const { data: { session: currentSession }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('[AuthContext] Error during revalidation:', error);
        return false;
      }

      if (currentSession) {
        console.log('[AuthContext] Revalidation found valid session, updating state');
        setSession(currentSession);
        setUser(currentSession.user);

        // Fetch profile if we don't have it or user ID changed
        if (!userProfile || userProfile.id !== currentSession.user.id) {
          await fetchUserProfile(currentSession.user.id);
        }

        return true;
      } else {
        console.log('[AuthContext] Revalidation found no session');
        setSession(null);
        setUser(null);
        setUserProfile(null);
        return false;
      }
    } catch (error) {
      console.error('[AuthContext] Exception during revalidation:', error);
      return false;
    }
  }, [userProfile, fetchUserProfile]);

  /**
   * Validate session matches current Supabase session
   * Used by periodic validation and window focus handlers
   */
  const validateSession = useCallback(async (): Promise<void> => {
    try {
      const { data: { session: currentSession }, error } = await supabase.auth.getSession();

      if (error) {
        console.error('[SessionValidation] Error fetching session:', error);
        return;
      }

      // Compare current session with React state
      const hasSessionMismatch =
        (!!currentSession !== !!session) ||
        (currentSession?.access_token !== session?.access_token);

      if (hasSessionMismatch) {
        console.warn('[SessionValidation] Session mismatch detected! Updating React state...');
        console.log('[SessionValidation] Current session:', currentSession ? 'Has token' : 'No session');
        console.log('[SessionValidation] React state session:', session ? 'Has token' : 'No session');

        // Update state to match Supabase
        setSession(currentSession);
        setUser(currentSession?.user ?? null);

        if (currentSession?.user) {
          await fetchUserProfile(currentSession.user.id);
        } else {
          setUserProfile(null);
        }
      } else {
        console.log('[SessionValidation] Session validation passed - state is synchronized');
      }
    } catch (error) {
      console.error('[SessionValidation] Exception during validation:', error);
    }
  }, [session, fetchUserProfile]);

  /**
   * Initialize auth state and set up listener
   */
  useEffect(() => {
    // Prevent double initialization in development mode (React strict mode)
    if (initializedRef.current) {
      console.log('[AuthContext] Already initialized, skipping...');
      return;
    }

    initializedRef.current = true;
    console.log('[AuthContext] Initializing authentication...');

    // Get initial session - optimized with profile caching
    const initializeAuth = async () => {
      try {
        const { data: { session: initialSession }, error } = await supabase.auth.getSession();

        if (error) {
          console.error('[AuthContext] Error getting initial session:', error);
        }

        console.log('[AuthContext] Initial session:', initialSession ? 'Has session' : 'No session');
        setSession(initialSession);
        setUser(initialSession?.user ?? null);

        if (initialSession?.user) {
          const userId = initialSession.user.id;
          console.log('[AuthContext] Checking cached profile for user:', userId);

          // Step 2: Try to use cached profile for instant UI render
          const cachedProfile = getCachedProfile(userId);
          if (cachedProfile) {
            // Use cached profile immediately
            setUserProfile(cachedProfile);
            setLoading(false);
            console.log('[AuthContext] Using cached profile, loading complete');

            // Background refresh - don't await (Step 3 optimization)
            fetchUserProfile(userId, 0, true).catch(err => {
              console.warn('[AuthContext] Background profile refresh failed:', err);
            });
            return; // Exit early since we've already set loading to false
          }

          // No cache - fetch profile with initial load timeout
          console.log('[AuthContext] No cached profile, fetching from server...');
          await fetchUserProfile(userId, 0, true);
        }
      } catch (error) {
        console.error('[AuthContext] Error initializing auth:', error);
      } finally {
        console.log('[AuthContext] Initialization complete, setting loading to false');
        setLoading(false);
      }
    };

    initializeAuth();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        const timestamp = new Date().toISOString();
        console.log(`[AuthContext] ${timestamp} - Auth state changed:`, event);
        console.log('[AuthContext] New session:', newSession ? 'Has session' : 'No session');

        if (newSession) {
          const expiresAt = newSession.expires_at ? new Date(newSession.expires_at * 1000).toISOString() : 'Unknown';
          console.log('[AuthContext] Token expires at:', expiresAt);
        }

        // Ignore INITIAL_SESSION event to prevent duplicate fetches
        if (event === 'INITIAL_SESSION') {
          console.log('[AuthContext] Ignoring INITIAL_SESSION event');
          return;
        }

        // Handle TOKEN_REFRESHED event explicitly
        if (event === 'TOKEN_REFRESHED') {
          console.log('[AuthContext] TOKEN_REFRESHED event - updating session in React state');
          setSession(newSession);
          setUser(newSession?.user ?? null);

          // Profile should still be valid, but refresh if user changed
          if (newSession?.user && (!userProfile || userProfile.id !== newSession.user.id)) {
            console.log('[AuthContext] User changed during refresh, fetching new profile');
            await fetchUserProfile(newSession.user.id);
          } else {
            console.log('[AuthContext] Token refreshed, keeping existing profile');
          }

          setLoading(false);
          return;
        }

        // Handle other events (SIGNED_IN, SIGNED_OUT, USER_UPDATED)
        console.log('[AuthContext] Handling event:', event);
        console.log('[AuthContext] Before state update - user:', user ? user.id : 'null', ', profile:', userProfile ? userProfile.id : 'null');

        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (newSession?.user) {
          console.log('[AuthContext] Fetching profile for user:', newSession.user.id);
          await fetchUserProfile(newSession.user.id);
        } else {
          console.log('[AuthContext] No user in session, clearing profile');
          setUserProfile(null);
        }

        console.log('[AuthContext] After state update - user:', newSession?.user ? newSession.user.id : 'null');

        // Ensure loading is false after auth state change
        setLoading(false);

        // Reset transitioning flag after login completes
        if (event === 'SIGNED_IN') {
          setIsTransitioning(false);
        }
      }
    );

    // Cleanup subscription on unmount
    return () => {
      console.log('[AuthContext] Cleaning up subscription');
      subscription.unsubscribe();
      initializedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps array intentional - initialize once on mount

  /**
   * Periodic session validation (every 5 minutes)
   * Catches cases where onAuthStateChange missed an event
   */
  useEffect(() => {
    console.log('[SessionValidation] Setting up periodic validation (every 5 minutes)');

    const VALIDATION_INTERVAL = 5 * 60 * 1000; // 5 minutes

    const intervalId = setInterval(() => {
      console.log('[SessionValidation] Running periodic validation check...');
      validateSession();
    }, VALIDATION_INTERVAL);

    // Cleanup interval on unmount
    return () => {
      console.log('[SessionValidation] Cleaning up periodic validation');
      clearInterval(intervalId);
    };
  }, [validateSession]);

  /**
   * Window focus session validation
   * Re-validates session when user returns to the tab
   */
  useEffect(() => {
    console.log('[SessionValidation] Setting up window focus listener');

    const handleWindowFocus = async () => {
      console.log('[SessionValidation] Window gained focus, validating session...');

      // Check if session is close to expiry (within 5 minutes)
      if (session?.expires_at) {
        const expiresAt = session.expires_at * 1000; // Convert to milliseconds
        const now = Date.now();
        const timeUntilExpiry = expiresAt - now;
        const REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes

        if (timeUntilExpiry < REFRESH_THRESHOLD && timeUntilExpiry > 0) {
          console.log('[SessionValidation] Token close to expiry, refreshing...');
          try {
            const { error } = await supabase.auth.refreshSession();
            if (error) {
              console.error('[SessionValidation] Error refreshing session:', error);
            } else {
              console.log('[SessionValidation] Session refreshed successfully');
            }
          } catch (error) {
            console.error('[SessionValidation] Exception refreshing session:', error);
          }
        }
      }

      // Always validate to catch desynchronization
      await validateSession();
    };

    window.addEventListener('focus', handleWindowFocus);

    // Cleanup listener on unmount
    return () => {
      console.log('[SessionValidation] Cleaning up window focus listener');
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [session, validateSession]);

  /**
   * Sign in handler
   * Performance fix: Removed 100ms artificial delay and made last_login update non-blocking
   */
  const handleSignIn = async (email: string, password: string): Promise<void> => {
    console.log('[AuthContext] handleSignIn called for:', email);
    setIsTransitioning(true);
    lastLoginTimestampRef.current = Date.now();

    try {
      const { user: signedInUser, session: signedInSession, error } = await supabaseSignIn(email, password);

      console.log('[AuthContext] Sign in result:', {
        user: signedInUser ? 'User returned' : 'No user',
        session: signedInSession ? 'Session returned' : 'No session',
        error: error ? error.message : 'No error'
      });

      if (error) {
        setIsTransitioning(false);
        throw new Error(error.message);
      }

      // Don't set state here - let onAuthStateChange handle it
      // This prevents race conditions

      // Step 6: Update last login timestamp non-blocking (fire and forget)
      if (signedInUser) {
        supabase
          .from('user_profiles')
          .update({ last_login: new Date().toISOString() })
          .eq('id', signedInUser.id)
          .then(({ error: updateError }) => {
            if (updateError) {
              console.warn('[AuthContext] Failed to update last_login:', updateError);
            }
          });
      }

      // Step 5: Removed artificial 100ms delay
      // onAuthStateChange will fire and update the state automatically
    } catch (error) {
      console.error('[AuthContext] Sign in error:', error);
      setIsTransitioning(false);
      throw error;
    }
  };

  /**
   * Sign up handler
   */
  const handleSignUp = async (
    email: string,
    password: string,
    fullName: string,
    userType: 'funcionario' | 'cliente',
    role: UserRole = 'user' as UserRole,
    companyName?: string,
    clientId?: string
  ): Promise<void> => {
    setLoading(true);
    try {
      const { user: newUser, error } = await supabaseSignUp(email, password, {
        full_name: fullName,
      });

      if (error) {
        throw new Error(error.message);
      }

      // Create user profile record
      if (newUser) {
        // For clients, automatically set role to 'cliente'
        const finalRole = userType === 'cliente' ? ('cliente' as UserRole) : role;

        const { error: profileError } = await supabase
          .from('user_profiles')
          .insert({
            id: newUser.id,
            full_name: fullName,
            role: finalRole,
            user_type: userType,
            is_active: true,
            company_name: companyName || null,
            client_id: clientId || null,
          });

        if (profileError) {
          console.error('Error creating user profile:', profileError);
          throw new Error('Failed to create user profile');
        }

        await fetchUserProfile(newUser.id);
      }
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign out handler
   * Step 10: Added cache invalidation on logout
   */
  const handleSignOut = async (): Promise<void> => {
    setLoading(true);
    try {
      // Clear profile cache before signing out
      if (user?.id) {
        clearCachedProfile(user.id);
      } else {
        clearCachedProfile(); // Clear all cached profiles as fallback
      }

      const { error } = await supabaseSignOut();

      if (error) {
        throw new Error(error.message);
      }

      setUser(null);
      setSession(null);
      setUserProfile(null);
      setIsTransitioning(false);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Computed value for authentication status
  const isAuthenticated = !!user && !!session;

  const value: AuthContextType = {
    user,
    session,
    userProfile,
    loading,
    isTransitioning,
    lastLoginTimestamp: lastLoginTimestampRef.current,
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    isAuthenticated,
    revalidateSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
