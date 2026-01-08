-- Migration: Add Tesoreria role to user_profiles
-- Date: 2025-12-02
-- Description: Updates the user_profiles table to support the Tesoreria role

-- Step 1: Update CHECK constraint to allow tesoreria role
ALTER TABLE user_profiles
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

ALTER TABLE user_profiles
ADD CONSTRAINT user_profiles_role_check
CHECK (role IN ('admin', 'legal', 'operations', 'tesoreria', 'commercial', 'analyst', 'mesa_control', 'manager', 'user', 'cliente'));

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles' AND column_name = 'role';

-- Show existing roles
SELECT role, COUNT(*) as user_count
FROM user_profiles
GROUP BY role
ORDER BY role;
