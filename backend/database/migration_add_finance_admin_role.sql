-- Migration: Add finance_admin role
-- Date: 2024-12-29
-- Description: Documents the finance_admin role for PA classification management
--
-- This migration serves as documentation for adding the finance_admin role.
-- The role should be added to user_profiles for users who need to:
-- - Upload and manage PA classification rules
-- - Manage finance department configurations
--
-- To add finance_admin role to a user:
-- UPDATE user_profiles SET role = 'finance_admin' WHERE id = '<user_uuid>';
--
-- Alternatively, add the role via Supabase dashboard.

-- ============================================================================
-- ROLE DOCUMENTATION
-- ============================================================================
--
-- Role: finance_admin
-- Description: Finance Administrator role for managing classification rules
--
-- Permissions:
-- - Upload PA Account Catalog
-- - Upload PA Classification Rules
-- - Upload PA Clasificación Cuenta Rules
-- - Upload PA Nexo Rules
-- - View all uploaded rules
-- - All permissions of 'finance' role (process reports)
--
-- Access Level: Department Admin
--
-- Backend RBAC Usage:
-- require_roles(['finance_admin'])           # Only finance_admin
-- require_roles(['finance', 'finance_admin']) # Both roles
--
-- Frontend RoleProtectedRoute Usage:
-- <RoleProtectedRoute allowedRoles={[UserRole.FINANCE_ADMIN, UserRole.ADMIN]}>
--   <ReglasClasificacionPA />
-- </RoleProtectedRoute>

-- ============================================================================
-- EXECUTABLE MIGRATION
-- ============================================================================

-- Step 1: Verify current roles in the system
SELECT DISTINCT role FROM user_profiles ORDER BY role;

-- Step 2: View all users to find the one you want to update
SELECT id, email, full_name, role FROM user_profiles ORDER BY email;

-- Step 3: Assign finance_admin role to a specific user (replace the email)
-- Uncomment and modify the following line with the target user's email:

-- UPDATE user_profiles
-- SET role = 'finance_admin', updated_at = NOW()
-- WHERE email = 'user@example.com';

-- Or by user ID:
-- UPDATE user_profiles
-- SET role = 'finance_admin', updated_at = NOW()
-- WHERE id = 'your-user-uuid-here';

-- Step 4: Verify the update
-- SELECT id, email, full_name, role FROM user_profiles WHERE role = 'finance_admin';

-- ============================================================================
-- NOTE
-- ============================================================================
-- The 'finance' role should already exist for basic finance users.
-- The 'finance_admin' role is a new role specifically for rule management.
-- Admin users bypass role checks and have access to all features.
