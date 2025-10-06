/**
 * Supabase Client Configuration and Auth Helper Functions
 * Based on proven architecture from Finkargo Pre-Approval System
 */
import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient, Session, User, AuthError } from '@supabase/supabase-js';

// Environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables. Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env');
}

/**
 * Supabase client instance with auto-refresh and session persistence
 */
export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,      // Auto-refresh tokens before expiry
    persistSession: true,         // Persist session in localStorage
    detectSessionInUrl: true,     // Handle OAuth callbacks
    storage: window.localStorage, // Store session data
  },
  global: {
    headers: {
      'x-application-name': 'Finkargo Automation Hub',
    },
  },
});

/**
 * Sign in with email and password
 */
export const signIn = async (
  email: string,
  password: string
): Promise<{ user: User | null; session: Session | null; error: AuthError | null }> => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    console.error('Sign in error:', error.message);
    return { user: null, session: null, error };
  }

  return { user: data.user, session: data.session, error: null };
};

/**
 * Register new user with email and password
 */
export const signUp = async (
  email: string,
  password: string,
  metadata?: Record<string, any>
): Promise<{ user: User | null; session: Session | null; error: AuthError | null }> => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata || {},
    },
  });

  if (error) {
    console.error('Sign up error:', error.message);
    return { user: null, session: null, error };
  }

  return { user: data.user, session: data.session, error: null };
};

/**
 * Sign out current user
 */
export const signOut = async (): Promise<{ error: AuthError | null }> => {
  const { error } = await supabase.auth.signOut();

  if (error) {
    console.error('Sign out error:', error.message);
    return { error };
  }

  return { error: null };
};

/**
 * Get current authenticated user
 */
export const getCurrentUser = async (): Promise<User | null> => {
  const { data: { user }, error } = await supabase.auth.getUser();

  if (error) {
    console.error('Get user error:', error.message);
    return null;
  }

  return user;
};

/**
 * Get active session
 */
export const getSession = async (): Promise<Session | null> => {
  const { data: { session }, error } = await supabase.auth.getSession();

  if (error) {
    console.error('Get session error:', error.message);
    return null;
  }

  return session;
};

/**
 * Refresh session
 */
export const refreshSession = async (): Promise<{ session: Session | null; error: AuthError | null }> => {
  const { data, error } = await supabase.auth.refreshSession();

  if (error) {
    console.error('Refresh session error:', error.message);
    return { session: null, error };
  }

  return { session: data.session, error: null };
};
