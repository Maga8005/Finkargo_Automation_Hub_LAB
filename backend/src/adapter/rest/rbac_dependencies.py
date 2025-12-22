"""
Role-Based Access Control (RBAC) Dependencies
Provides role checking for protected endpoints with admin bypass
"""
from fastapi import HTTPException, Depends, status
from typing import List
from .dependencies import get_current_user


def require_roles(allowed_roles: List[str], allow_admin: bool = True):
    """
    Dependency factory for role-based access control.

    Args:
        allowed_roles: List of roles that can access the endpoint
        allow_admin: If True, admin users bypass role checks (default: True)

    Returns:
        Dependency function that validates user role

    Example:
        @router.get("/legal/contracts")
        async def get_contracts(user: dict = Depends(require_roles(['legal']))):
            # Only users with 'legal' role or admins can access
            pass
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        """
        Validate that current user has one of the allowed roles.
        Admin users bypass this check if allow_admin is True.

        Args:
            user: Current authenticated user from JWT token

        Returns:
            User dict if authorized

        Raises:
            HTTPException: 403 if user doesn't have required role
        """
        # Get user profile to check role
        from src.config.supabase_config import get_supabase_client
        import logging

        logger = logging.getLogger(__name__)

        supabase = get_supabase_client()

        # Get user ID - Supabase user object can be accessed via .id attribute or dict
        user_id = user.id if hasattr(user, 'id') else user.get('id')

        logger.info(f"RBAC check for user_id: {user_id}, allowed_roles: {allowed_roles}")

        # Fetch user profile with role
        response = supabase.admin_client.table('user_profiles') \
            .select('id, full_name, role, is_active') \
            .eq('id', user_id) \
            .single() \
            .execute()

        if not response.data:
            logger.error(f"User profile not found for user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User profile not found"
            )

        user_profile = response.data
        user_role = user_profile.get('role')
        is_active = user_profile.get('is_active', False)

        logger.info(f"User profile found: role={user_role}, is_active={is_active}")

        # Check if user is active
        if not is_active:
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create a standardized user dict with profile info
        # This ensures downstream code can access user.id, user.role, etc.
        user_with_profile = {
            'id': user_id,
            'email': user.email if hasattr(user, 'email') else user.get('email'),
            'role': user_role,
            'full_name': user_profile.get('full_name'),
            'is_active': is_active,
            '_original_user': user  # Keep original for any edge cases
        }

        # Admin bypass - admins have access to everything
        if allow_admin and user_role == 'admin':
            logger.info(f"Admin user {user_id} granted access (bypass)")
            return user_with_profile

        # Check if user has one of the allowed roles
        if user_role not in allowed_roles:
            logger.warning(f"Access denied for user {user_id}: role={user_role}, required={allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )

        logger.info(f"User {user_id} granted access with role {user_role}")
        return user_with_profile

    return role_checker


# Pre-configured role dependencies for convenience
require_legal_role = require_roles(['legal'])
require_operations_role = require_roles(['operations'])
require_tesoreria_role = require_roles(['tesoreria'])
require_alianzas_role = require_roles(['alianzas'])
require_admin_role = require_roles(['admin'], allow_admin=False)  # Only admins
require_legal_or_operations = require_roles(['legal', 'operations'])
require_paga_local_role = require_roles(['operations', 'comercial_paga_local'])  # Paga Local access for Operations and Commercial

# Risk department role dependencies
require_risk_analyst_role = require_roles(['risk_analyst'])  # Risk analysts only
require_risk_manager_role = require_roles(['risk_manager'])  # Risk managers only
require_risk_role = require_roles(['risk_analyst', 'risk_manager'])  # Any risk department role
