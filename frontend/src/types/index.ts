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
 * User type - distinguishes between internal employees and external clients
 */
export type UserType = 'funcionario' | 'cliente';

export const UserType = {
  FUNCIONARIO: 'funcionario' as const,
  CLIENTE: 'cliente' as const,
};

/**
 * User profile stored in database (linked to Supabase auth.users)
 */
export interface UserProfile {
  id: string;
  full_name: string;
  role: UserRole;
  user_type: UserType;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at?: string;
  // Client-specific fields (only for user_type='cliente')
  company_name?: string;
  client_id?: string;
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
  | 'user'
  | 'cliente'; // Special role for external clients

export const UserRole = {
  ADMIN: 'admin' as const,
  LEGAL: 'legal' as const,
  OPERATIONS: 'operations' as const,
  COMMERCIAL: 'commercial' as const,
  ANALYST: 'analyst' as const,
  MESA_CONTROL: 'mesa_control' as const,
  MANAGER: 'manager' as const,
  USER: 'user' as const,
  CLIENTE: 'cliente' as const, // Special role for external clients
};

/**
 * Authentication context type
 */
export interface AuthContextType {
  user: SupabaseUser | null;
  session: Session | null;
  userProfile: UserProfile | null;
  loading: boolean;
  isTransitioning: boolean;
  lastLoginTimestamp: number;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (
    email: string,
    password: string,
    fullName: string,
    userType: UserType,
    role?: UserRole,
    companyName?: string,
    clientId?: string
  ) => Promise<void>;
  signOut: () => Promise<void>;
  isAuthenticated: boolean;
  revalidateSession: () => Promise<boolean>;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
