"""
Authentication Routes
Endpoints for user authentication and profile management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict
import logging

from ...config.supabase_config import get_supabase_client
from ...interface.auth_dtos import (
    UserLoginDTO,
    UserRegisterDTO,
    TokenResponseDTO,
    UserProfileDTO,
    UserResponseDTO,
    ErrorResponseDTO
)
from .dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponseDTO,
    responses={
        401: {"model": ErrorResponseDTO, "description": "Invalid credentials"},
        500: {"model": ErrorResponseDTO, "description": "Server error"}
    }
)
async def login(credentials: UserLoginDTO) -> TokenResponseDTO:
    """
    Login with email and password.

    Args:
        credentials: User login credentials (email, password)

    Returns:
        TokenResponseDTO: Access token and session info

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    supabase_client = get_supabase_client()

    try:
        # Authenticate with Supabase
        response = supabase_client.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })

        if not response or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Return token response
        return TokenResponseDTO(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in or 3600,
            refresh_token=response.session.refresh_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post(
    "/register",
    response_model=UserResponseDTO,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponseDTO, "description": "Invalid input or user already exists"},
        500: {"model": ErrorResponseDTO, "description": "Server error"}
    }
)
async def register(user_data: UserRegisterDTO) -> UserResponseDTO:
    """
    Register a new user account.

    Args:
        user_data: User registration data (email, password, full_name, role)

    Returns:
        UserResponseDTO: Created user profile and session info

    Raises:
        HTTPException: 400 if user already exists or invalid data
    """
    supabase_client = get_supabase_client()

    try:
        # Create user in Supabase Auth
        response = supabase_client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "role": user_data.role
                }
            }
        })

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )

        user = response.user

        # Determine final role - clients automatically get 'cliente' role
        final_role = "cliente" if user_data.user_type == "cliente" else user_data.role

        # Create user profile in database
        profile_data = {
            "id": user.id,
            "full_name": user_data.full_name,
            "role": final_role,
            "user_type": user_data.user_type,
            "is_active": True,
            "company_name": user_data.company_name,
            "client_id": user_data.client_id
        }

        profile_response = supabase_client.admin_client.table("user_profiles") \
            .insert(profile_data) \
            .execute()

        if not profile_response.data:
            logger.error(f"Failed to create user profile for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )

        # Build response
        created_profile = profile_response.data[0]
        user_profile = UserProfileDTO(
            id=user.id,
            email=user.email,
            full_name=user_data.full_name,
            role=final_role,
            user_type=user_data.user_type,
            is_active=True,
            last_login=None,
            created_at=created_profile.get("created_at"),
            company_name=user_data.company_name,
            client_id=user_data.client_id
        )

        session_token = None
        if response.session:
            session_token = TokenResponseDTO(
                access_token=response.session.access_token,
                token_type="bearer",
                expires_in=response.session.expires_in or 3600,
                refresh_token=response.session.refresh_token
            )

        return UserResponseDTO(
            user=user_profile,
            session=session_token
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)) -> Dict[str, str]:
    """
    Logout current user (invalidate session).

    Args:
        user: Current authenticated user from dependency

    Returns:
        dict: Success message
    """
    supabase_client = get_supabase_client()

    try:
        # Sign out from Supabase
        supabase_client.auth.sign_out()

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.get(
    "/me",
    response_model=UserProfileDTO,
    responses={
        401: {"model": ErrorResponseDTO, "description": "Unauthorized"},
        404: {"model": ErrorResponseDTO, "description": "User profile not found"}
    }
)
async def get_current_user_profile(user: dict = Depends(get_current_user)) -> UserProfileDTO:
    """
    Get current authenticated user's profile.

    Args:
        user: Current authenticated user from dependency

    Returns:
        UserProfileDTO: User profile information

    Raises:
        HTTPException: 404 if profile not found
    """
    supabase_client = get_supabase_client()

    try:
        # Fetch user profile from database
        response = supabase_client.admin_client.table("user_profiles") \
            .select("*") \
            .eq("id", user.id) \
            .single() \
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        profile = response.data

        return UserProfileDTO(
            id=profile["id"],
            email=user.email,
            full_name=profile["full_name"],
            role=profile["role"],
            user_type=profile.get("user_type", "funcionario"),  # Default to funcionario for backward compatibility
            is_active=profile["is_active"],
            last_login=profile.get("last_login"),
            created_at=profile["created_at"],
            company_name=profile.get("company_name"),
            client_id=profile.get("client_id")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching user profile"
        )


@router.get("/health")
async def auth_health_check() -> Dict[str, str]:
    """
    Health check endpoint for auth service.

    Returns:
        dict: Health status
    """
    return {"status": "healthy", "service": "authentication"}
