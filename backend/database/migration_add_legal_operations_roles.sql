-- Migration: Add Legal and Operations roles to user_profiles
-- Date: 2025-10-06
-- Description: Updates the user_profiles table to support Legal and Operations roles

-- Step 1: Update CHECK constraint to allow new roles
ALTER TABLE user_profiles
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

ALTER TABLE user_profiles
ADD CONSTRAINT user_profiles_role_check
CHECK (role IN ('admin', 'legal', 'operations', 'commercial', 'analyst', 'mesa_control', 'manager', 'user'));

-- Step 2: Add indexes for role-based queries (performance optimization)
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles' AND column_name = 'role';

-- Show existing roles
SELECT role, COUNT(*) as user_count
FROM user_profiles
GROUP BY role
ORDER BY role;
