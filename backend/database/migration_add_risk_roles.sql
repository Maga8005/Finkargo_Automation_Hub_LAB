-- Migration: Add Risk Analyst and Risk Manager roles to user_profiles
-- Date: 2025-12-21
-- Description: Updates the user_profiles table to support Risk department roles

-- Step 1: Update CHECK constraint to allow new roles
ALTER TABLE user_profiles
DROP CONSTRAINT IF EXISTS user_profiles_role_check;

ALTER TABLE user_profiles
ADD CONSTRAINT user_profiles_role_check
CHECK (role IN (
    'admin',
    'legal',
    'operations',
    'commercial',
    'analyst',
    'mesa_control',
    'manager',
    'user',
    'cliente',
    'tesoreria',
    'alianzas',
    'comercial_paga_local',
    'risk_analyst',      -- New: Risk department analyst role
    'risk_manager'       -- New: Risk department manager role
));

-- Step 2: Add index for risk role queries (performance optimization)
CREATE INDEX IF NOT EXISTS idx_user_profiles_role_risk
ON user_profiles(role)
WHERE role IN ('risk_analyst', 'risk_manager');

-- Verify the change
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profiles' AND column_name = 'role';

-- Show existing roles
SELECT role, COUNT(*) as user_count
FROM user_profiles
GROUP BY role
ORDER BY role;
