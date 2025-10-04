/**
 * Core types and interfaces for Finkargo Automation Hub
 */

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

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  departments: string[];
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}
