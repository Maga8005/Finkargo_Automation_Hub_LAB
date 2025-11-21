/**
 * Authentication Context Provider
 * Manages global authentication state using Supabase Auth
 * Based on proven architecture from Finkargo Pre-Approval System
 */
import React, { createContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase, signIn as supabaseSignIn, signUp as supabaseSignUp, signOut as supabaseSignOut } from '../services/supabase';
import type { AuthContextType, UserProfile, UserRole } from '../types';

// Create context with default values
export const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  userProfile: null,
  loading: true,
  signIn: async () => {},
  signUp: async () => {},
  signOut: async () => {},
  isAuthenticated: false,
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
   * Fetch user profile from database with timeout and race condition prevention
   */
  const fetchUserProfile = async (userId: string): Promise<void> => {
    // Prevent concurrent fetches
    if (fetchingProfileRef.current) {
      console.log('[AuthContext] Profile fetch already in progress, skipping...');
      return;
    }

    fetchingProfileRef.current = true;
    console.log('[AuthContext] Starting profile fetch for user:', userId);

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

        // If profile doesn't exist, log detailed error
        if ('code' in error && error.code === 'PGRST116') {
          console.error('[AuthContext] User profile not found in database. User may need to complete registration.');
        }

        setUserProfile(null);
        return;
      }

      console.log('[AuthContext] Profile fetched successfully:', data);
      setUserProfile(data as UserProfile);
    } catch (error) {
      console.error('[AuthContext] Error fetching user profile:', error);
      setUserProfile(null);
    } finally {
      fetchingProfileRef.current = false;
      console.log('[AuthContext] Profile fetch completed');
    }
  };

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
        console.log('[AuthContext] Auth state changed:', event, newSession ? 'Has session' : 'No session');

        // Ignore INITIAL_SESSION event to prevent duplicate fetches
        if (event === 'INITIAL_SESSION') {
          console.log('[AuthContext] Ignoring INITIAL_SESSION event');
          return;
        }

        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (newSession?.user) {
          console.log('[AuthContext] Fetching profile for user:', newSession.user.id);
          await fetchUserProfile(newSession.user.id);
        } else {
          setUserProfile(null);
        }

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
  }, []);

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
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
