-- Migration: Add user_type, company_name, and client_id to user_profiles
-- Description: Adds support for dual access (funcionarios vs clientes)
-- Date: 2025-11-12

-- Add user_type column with default value 'funcionario' for existing users
ALTER TABLE user_profiles
ADD COLUMN user_type TEXT NOT NULL DEFAULT 'funcionario'
CHECK (user_type IN ('funcionario', 'cliente'));

-- Add company_name column for client users (nullable)
ALTER TABLE user_profiles
ADD COLUMN company_name TEXT;

-- Add client_id column for external client identification (nullable)
ALTER TABLE user_profiles
ADD COLUMN client_id TEXT;

-- Update the role check constraint to include 'cliente' role
ALTER TABLE user_profiles
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

ALTER TABLE user_profiles
ADD CONSTRAINT user_profiles_role_check
CHECK (role IN ('admin', 'commercial', 'analyst', 'mesa_control', 'manager', 'user', 'legal', 'operations', 'cliente'));

-- Create index on user_type for faster filtering
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_type ON user_profiles(user_type);

-- Create index on client_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_client_id ON user_profiles(client_id);

-- Update RLS policies to handle client access
-- Policy: Allow users to read their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
CREATE POLICY "Users can view own profile"
ON user_profiles FOR SELECT
USING (auth.uid() = id);

-- Policy: Allow users to update their own profile
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
CREATE POLICY "Users can update own profile"
ON user_profiles FOR UPDATE
USING (auth.uid() = id);

-- Policy: Allow funcionarios to view other funcionarios (for collaboration)
CREATE POLICY "Funcionarios can view other funcionarios"
ON user_profiles FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM user_profiles
    WHERE id = auth.uid()
    AND user_type = 'funcionario'
  )
  AND user_type = 'funcionario'
);

-- Comments for documentation
COMMENT ON COLUMN user_profiles.user_type IS 'Type of user: funcionario (internal employee) or cliente (external client)';
COMMENT ON COLUMN user_profiles.company_name IS 'Company name for client users (only applicable when user_type=cliente)';
COMMENT ON COLUMN user_profiles.client_id IS 'External client identifier for integration with client systems';

-- Migration verification query
-- Run this after migration to verify:
-- SELECT user_type, role, count(*)
-- FROM user_profiles
-- GROUP BY user_type, role;
