-- Migration: Fix user_profiles RLS policies to prevent infinite recursion
-- Date: 2025-10-06
-- Description: Removes problematic recursive policies since backend uses admin client

-- Drop all existing policies that cause recursion
DROP POLICY IF EXISTS "Users can view own profile" ON user_profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON user_profiles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON user_profiles;
DROP POLICY IF EXISTS "Admins can update all profiles" ON user_profiles;
DROP POLICY IF EXISTS "Service role has full access" ON user_profiles;

-- Simple policy: Users can view their own profile (no recursion)
CREATE POLICY "Users can view own profile"
ON user_profiles
FOR SELECT
USING (auth.uid() = id);

-- Simple policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
ON user_profiles
FOR UPDATE
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- Note: We don't need admin policies because the backend uses admin_client
-- which bypasses RLS. These policies are only for direct Supabase client access.

-- The frontend will use the backend API, which uses admin_client and bypasses RLS
-- So we only need basic user-level policies for direct database access

-- Grant permissions
GRANT SELECT, UPDATE ON user_profiles TO authenticated;
GRANT ALL ON user_profiles TO service_role;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'User profiles RLS policies fixed - removed recursive admin policies';
END $$;
