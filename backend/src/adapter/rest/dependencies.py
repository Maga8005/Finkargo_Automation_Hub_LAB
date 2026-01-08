"""
FastAPI Dependencies for Authentication
Provides reusable dependencies for protected endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from ...config.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    Use this dependency in protected endpoints.

    Args:
        credentials: HTTP Authorization credentials with Bearer token

    Returns:
        dict: User object with id, email, and metadata

    Raises:
        HTTPException: 401 if token is invalid or user not found

    Example:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"user_id": user.id, "email": user.email}
    """
    supabase_client = get_supabase_client()

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Validate token and get user
        user = supabase_client.get_user_from_token(token)

        if not user:
            logger.warning("Invalid or expired token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to get current active user (checks is_active in user_profiles).
    Use this for endpoints that require active user status.

    Args:
        user: Current user from get_current_user dependency

    Returns:
        dict: Active user object

    Raises:
        HTTPException: 403 if user is not active

    Example:
        @router.get("/admin")
        async def admin_endpoint(user: dict = Depends(get_current_active_user)):
            return {"message": "Admin access granted"}
    """
    supabase_client = get_supabase_client()

    try:
        # Fetch user profile to check active status
        response = supabase_client.admin_client.table('user_profiles') \
            .select('is_active') \
            .eq('id', user.id) \
            .single() \
            .execute()

        if not response.data or not response.data.get('is_active', False):
            logger.warning(f"Inactive user attempted access: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking user active status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not verify user status"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Dependency to get current user if token is provided, None otherwise.
    Use this for endpoints that work with or without authentication.

    Args:
        credentials: Optional HTTP Authorization credentials

    Returns:
        dict | None: User object if authenticated, None otherwise

    Example:
        @router.get("/public-or-private")
        async def flexible_endpoint(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                return {"message": "Authenticated content", "user_id": user.id}
            return {"message": "Public content"}
    """
    if not credentials:
        return None

    supabase_client = get_supabase_client()

    try:
        token = credentials.credentials
        user = supabase_client.get_user_from_token(token)
        return user
    except Exception as e:
        logger.debug(f"Optional auth failed: {str(e)}")
        return None
