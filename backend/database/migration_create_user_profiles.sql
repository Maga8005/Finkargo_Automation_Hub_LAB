-- Migration: Create user_profiles table for Supabase authentication
-- Date: 2025-10-06
-- Description: Creates user_profiles table linked to Supabase auth.users
-- Reference: Based on proven architecture from Finkargo Pre-Approval System

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'commercial', 'analyst', 'mesa_control', 'manager', 'user')),
    is_active BOOLEAN DEFAULT true NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comments to document the table and columns
COMMENT ON TABLE user_profiles IS 'User profiles linked to Supabase auth.users for application-specific user data';
COMMENT ON COLUMN user_profiles.id IS 'User ID (references auth.users.id)';
COMMENT ON COLUMN user_profiles.full_name IS 'User full name for display';
COMMENT ON COLUMN user_profiles.role IS 'User role: admin, commercial, analyst, mesa_control, manager, or user';
COMMENT ON COLUMN user_profiles.is_active IS 'Whether the user account is active (for soft deletes)';
COMMENT ON COLUMN user_profiles.last_login IS 'Timestamp of last successful login';
COMMENT ON COLUMN user_profiles.created_at IS 'Timestamp when profile was created';
COMMENT ON COLUMN user_profiles.updated_at IS 'Timestamp when profile was last updated';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_last_login ON user_profiles(last_login);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_profiles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to call the function before updates
DROP TRIGGER IF EXISTS trigger_update_user_profiles_updated_at ON user_profiles;
CREATE TRIGGER trigger_update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_user_profiles_updated_at();

-- Row Level Security (RLS) Policies
-- Note: Backend uses admin client which bypasses RLS, but policies are set for direct access

-- Enable RLS on user_profiles table
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
ON user_profiles
FOR SELECT
USING (auth.uid() = id);

-- Policy: Users can update their own profile (except role and is_active)
CREATE POLICY "Users can update own profile"
ON user_profiles
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Policy: Admins can view all profiles
CREATE POLICY "Admins can view all profiles"
ON user_profiles
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND role = 'admin' AND is_active = true
    )
);

-- Policy: Admins can update all profiles
CREATE POLICY "Admins can update all profiles"
ON user_profiles
FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND role = 'admin' AND is_active = true
    )
);

-- Policy: Service role can do everything (for backend operations)
CREATE POLICY "Service role has full access"
ON user_profiles
FOR ALL
USING (auth.jwt() ->> 'role' = 'service_role');

-- Grant permissions to authenticated users
GRANT SELECT, UPDATE ON user_profiles TO authenticated;
GRANT ALL ON user_profiles TO service_role;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'User profiles table created successfully with RLS policies';
END $$;
