"""
Authentication Data Transfer Objects (DTOs)
Request and response models for auth endpoints
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserLoginDTO(BaseModel):
    """Request model for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class UserRegisterDTO(BaseModel):
    """Request model for user registration"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    full_name: str = Field(..., min_length=2, max_length=100, description="User full name")
    role: str = Field(default="user", description="User role (admin, commercial, analyst, user)")


class TokenResponseDTO(BaseModel):
    """Response model for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")


class UserProfileDTO(BaseModel):
    """Response model for user profile"""
    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")


class UserResponseDTO(BaseModel):
    """Response model for user operations"""
    user: UserProfileDTO
    session: Optional[TokenResponseDTO] = None


class ErrorResponseDTO(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Specific error code")
