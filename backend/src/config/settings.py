"""
Application settings and configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Settings
    APP_NAME: str = "Finkargo Automation Hub"
    DEBUG: bool = True
    PYTHON_VERSION: str = "3.11.9"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS (JSON array format required!)
    CORS_ORIGINS: str = '["http://localhost:5173"]'

    # Database
    DATABASE_URL: str = ""

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760
    SUPPORTED_FILE_TYPES: str = '[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]'

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
