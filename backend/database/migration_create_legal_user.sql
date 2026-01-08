-- Migration: Create legal@finkargo.com user
-- Date: 2025-10-06
-- Description: Creates a Legal role user for testing RBAC

-- IMPORTANT: This script should be run in Supabase SQL Editor
-- It creates both the auth user and the user profile

-- Step 1: Create the auth user
-- Note: Replace 'SECURE_PASSWORD_HERE' with a secure password before running
INSERT INTO auth.users (
    id,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    role
)
VALUES (
    gen_random_uuid(),
    'legal@finkargo.com',
    crypt('SECURE_PASSWORD_HERE', gen_salt('bf')),  -- Change password before running
    NOW(),
    NOW(),
    NOW(),
    '{"provider":"email","providers":["email"]}',
    '{"full_name":"Legal Department"}',
    false,
    'authenticated'
)
ON CONFLICT (email) DO NOTHING;

-- Step 2: Create the user profile
-- This uses the auth.users id from the previous insert
INSERT INTO user_profiles (
    id,
    full_name,
    role,
    is_active,
    created_at
)
SELECT
    id,
    'Legal Department',
    'legal',
    true,
    NOW()
FROM auth.users
WHERE email = 'legal@finkargo.com'
ON CONFLICT (id) DO UPDATE
SET
    role = 'legal',
    is_active = true,
    updated_at = NOW();

-- Step 3: Verify the user was created
SELECT
    u.id,
    u.email,
    u.email_confirmed_at,
    p.full_name,
    p.role,
    p.is_active
FROM auth.users u
LEFT JOIN user_profiles p ON u.id = p.id
WHERE u.email = 'legal@finkargo.com';

-- Expected output:
-- id                                   | email                | email_confirmed_at          | full_name          | role  | is_active
-- ------------------------------------ | -------------------- | --------------------------- | ------------------ | ----- | ---------
-- [uuid]                               | legal@finkargo.com   | [timestamp]                 | Legal Department   | legal | true
