-- Migration: Create tesoreria@finkargo.com user
-- Date: 2025-12-02
-- Description: Creates a Tesoreria role user for treasury module access

-- IMPORTANT: This script should be run in Supabase SQL Editor
-- It creates both the auth user and the user profile

-- Step 1: Check if user already exists and create if not
DO $$
DECLARE
    user_exists BOOLEAN;
    new_user_id UUID;
BEGIN
    -- Check if user already exists
    SELECT EXISTS(SELECT 1 FROM auth.users WHERE email = 'tesoreria@finkargo.com') INTO user_exists;

    IF NOT user_exists THEN
        -- Generate a new UUID for the user
        new_user_id := gen_random_uuid();

        -- Create the auth user
        -- Note: Replace 'SECURE_PASSWORD_HERE' with a secure password before running
        INSERT INTO auth.users (
            id,
            instance_id,
            email,
            encrypted_password,
            email_confirmed_at,
            created_at,
            updated_at,
            raw_app_meta_data,
            raw_user_meta_data,
            is_super_admin,
            role,
            aud,
            confirmation_token,
            recovery_token,
            email_change_token_new,
            email_change
        )
        VALUES (
            new_user_id,
            '00000000-0000-0000-0000-000000000000',
            'tesoreria@finkargo.com',
            crypt('SECURE_PASSWORD_HERE', gen_salt('bf')),  -- Change password before running
            NOW(),
            NOW(),
            NOW(),
            '{"provider":"email","providers":["email"]}',
            '{"full_name":"Tesorería Department"}',
            false,
            'authenticated',
            'authenticated',
            '',
            '',
            '',
            ''
        );

        RAISE NOTICE 'Created auth user: tesoreria@finkargo.com with id %', new_user_id;
    ELSE
        RAISE NOTICE 'User tesoreria@finkargo.com already exists, skipping auth.users insert';
    END IF;
END $$;

-- Step 2: Create or update the user profile
INSERT INTO user_profiles (
    id,
    full_name,
    role,
    is_active,
    user_type,
    created_at
)
SELECT
    id,
    'Tesorería Department',
    'tesoreria',
    true,
    'funcionario',
    NOW()
FROM auth.users
WHERE email = 'tesoreria@finkargo.com'
ON CONFLICT (id) DO UPDATE
SET
    role = 'tesoreria',
    is_active = true,
    updated_at = NOW();

-- Step 3: Verify the user was created
SELECT
    u.id,
    u.email,
    u.email_confirmed_at,
    p.full_name,
    p.role,
    p.is_active,
    p.user_type
FROM auth.users u
LEFT JOIN user_profiles p ON u.id = p.id
WHERE u.email = 'tesoreria@finkargo.com';

-- Expected output:
-- id                                   | email                    | email_confirmed_at | full_name             | role      | is_active | user_type
-- ------------------------------------ | ------------------------ | ------------------ | --------------------- | --------- | --------- | ----------
-- [uuid]                               | tesoreria@finkargo.com   | [timestamp]        | Tesorería Department  | tesoreria | true      | funcionario
