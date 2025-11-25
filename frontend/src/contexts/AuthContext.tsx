/**
 * Authentication Context Provider
 * Manages global authentication state using Supabase Auth
 * Based on proven architecture from Finkargo Pre-Approval System
 *
 * Bug fix: Added comprehensive session validation to prevent auth token loss mid-session
 */
import React, { createContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase, signIn as supabaseSignIn, signUp as supabaseSignUp, signOut as supabaseSignOut } from '../services/supabase';
import type { AuthContextType, UserProfile, UserRole } from '../types';

// Create context with default values
// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  userProfile: null,
  loading: true,
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

  // Track if we're currently fetching a profile to prevent concurrent fetches
  const fetchingProfileRef = React.useRef(false);
  // Track initialization to prevent duplicate fetches
  const initializedRef = React.useRef(false);

  /**
   * Fetch user profile from database with timeout, retry logic, and improved error handling
   * Bug fix: Don't clear userProfile on transient errors (network/timeout), only on permanent errors
   */
  const fetchUserProfile = useCallback(async (userId: string, retryCount = 0): Promise<void> => {
    const MAX_RETRIES = 1;
    const RETRY_DELAY = 1000; // 1 second

    // Prevent concurrent fetches
    if (fetchingProfileRef.current) {
      console.log('[AuthContext] Profile fetch already in progress, skipping...');
      return;
    }

    fetchingProfileRef.current = true;
    console.log('[AuthContext] Starting profile fetch for user:', userId, retryCount > 0 ? `(retry ${retryCount})` : '');

    try {
      // Create a timeout promise (10 seconds)
      const timeoutPromise = new Promise<never>((_, reject) => {
        setTimeout(() => reject(new Error('Profile fetch timeout')), 10000);
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
          return fetchUserProfile(userId, retryCount + 1);
        }

        // Max retries reached - log warning but keep existing userProfile
        console.warn('[AuthContext] Max retries reached for profile fetch. Keeping existing profile to prevent auth loss.');
        return;
      }

      console.log('[AuthContext] Profile fetched successfully:', data);
      setUserProfile(data as UserProfile);
    } catch (error) {
      console.error('[AuthContext] Error fetching user profile:', error);

      // On timeout or network error, try to retry
      if (retryCount < MAX_RETRIES) {
        console.warn('[AuthContext] Network/timeout error, will retry in', RETRY_DELAY, 'ms');
        fetchingProfileRef.current = false;
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return fetchUserProfile(userId, retryCount + 1);
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

    // Get initial session
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
          console.log('[AuthContext] Fetching profile for user:', initialSession.user.id);
          await fetchUserProfile(initialSession.user.id);
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
   */
  const handleSignIn = async (email: string, password: string): Promise<void> => {
    console.log('[AuthContext] handleSignIn called for:', email);
    try {
      const { user: signedInUser, session: signedInSession, error } = await supabaseSignIn(email, password);

      console.log('[AuthContext] Sign in result:', {
        user: signedInUser ? 'User returned' : 'No user',
        session: signedInSession ? 'Session returned' : 'No session',
        error: error ? error.message : 'No error'
      });

      if (error) {
        throw new Error(error.message);
      }

      // Don't set state here - let onAuthStateChange handle it
      // This prevents race conditions

      // Update last login timestamp
      if (signedInUser) {
        await supabase
          .from('user_profiles')
          .update({ last_login: new Date().toISOString() })
          .eq('id', signedInUser.id);
      }

      // onAuthStateChange will fire and update the state
      // Wait a bit for it to process
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
      console.error('[AuthContext] Sign in error:', error);
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
   */
  const handleSignOut = async (): Promise<void> => {
    setLoading(true);
    try {
      const { error } = await supabaseSignOut();

      if (error) {
        throw new Error(error.message);
      }

      setUser(null);
      setSession(null);
      setUserProfile(null);
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
    signIn: handleSignIn,
    signUp: handleSignUp,
    signOut: handleSignOut,
    isAuthenticated,
    revalidateSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
