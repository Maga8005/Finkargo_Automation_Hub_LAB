/**
 * Core types and interfaces for Finkargo Automation Hub
 */
import type { User as SupabaseUser, Session } from '@supabase/supabase-js';

// Re-export Supabase types for convenience
export type { User as SupabaseUser, Session } from '@supabase/supabase-js';

export interface Department {
  id: string;
  name: string;
  icon: string;
}

export interface AutomationModule {
  id: string;
  departmentId: string;
  name: string;
  description: string;
  icon: string;
}

export interface AutomationFeature {
  id: string;
  moduleId: string;
  name: string;
  description: string;
  route: string;
  enabled: boolean;
}

/**
 * User profile stored in database (linked to Supabase auth.users)
 */
export interface UserProfile {
  id: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Combined user data (Supabase user + profile)
 */
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  departments: string[];
}

export type UserRole =
  | 'admin'
  | 'legal'
  | 'operations'
  | 'commercial'
  | 'analyst'
  | 'mesa_control'
  | 'manager'
  | 'user';

export const UserRole = {
  ADMIN: 'admin' as const,
  LEGAL: 'legal' as const,
  OPERATIONS: 'operations' as const,
  COMMERCIAL: 'commercial' as const,
  ANALYST: 'analyst' as const,
  MESA_CONTROL: 'mesa_control' as const,
  MANAGER: 'manager' as const,
  USER: 'user' as const,
};

/**
 * Authentication context type
 */
export interface AuthContextType {
  user: SupabaseUser | null;
  session: Session | null;
  userProfile: UserProfile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, fullName: string, role?: UserRole) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
