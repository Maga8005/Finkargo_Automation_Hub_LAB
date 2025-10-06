/**
 * Authentication Context Provider
 * Manages global authentication state using Supabase Auth
 * Based on proven architecture from Finkargo Pre-Approval System
 */
import React, { createContext, useState, useEffect, ReactNode } from 'react';
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

  /**
   * Initialize auth state and set up listener
   */
  useEffect(() => {
    console.log('[AuthContext] Initializing authentication...');

    // Set loading to false immediately - we'll rely on onAuthStateChange
    setLoading(false);

    // The session will be set by onAuthStateChange listener below

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('[AuthContext] Auth state changed:', event, newSession ? 'Has session' : 'No session');
        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (newSession?.user) {
          console.log('[AuthContext] Fetching profile for user:', newSession.user.id);
          await fetchUserProfile(newSession.user.id);
        } else {
          setUserProfile(null);
        }

        setLoading(false);
      }
    );

    // Cleanup subscription on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  /**
   * Fetch user profile from database
   */
  const fetchUserProfile = async (userId: string): Promise<void> => {
    try {
      const { data, error } = await supabase
        .from('user_profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('Error fetching user profile:', error);
        // Don't throw - just log the error and continue
        setUserProfile(null);
        return;
      }

      setUserProfile(data as UserProfile);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      // Ensure we don't block the UI on profile fetch errors
      setUserProfile(null);
    }
  };

  /**
   * Sign in handler
   */
  const handleSignIn = async (email: string, password: string): Promise<void> => {
    setLoading(true);
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

      // Update state immediately
      if (signedInUser && signedInSession) {
        setUser(signedInUser);
        setSession(signedInSession);
        console.log('[AuthContext] User and session set in state');

        // Update last login timestamp
        await supabase
          .from('user_profiles')
          .update({ last_login: new Date().toISOString() })
          .eq('id', signedInUser.id);

        await fetchUserProfile(signedInUser.id);
      }
    } catch (error) {
      console.error('[AuthContext] Sign in error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sign up handler
   */
  const handleSignUp = async (
    email: string,
    password: string,
    fullName: string,
    role: UserRole = 'user' as UserRole
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
        const { error: profileError } = await supabase
          .from('user_profiles')
          .insert({
            id: newUser.id,
            full_name: fullName,
            role: role,
            is_active: true,
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
