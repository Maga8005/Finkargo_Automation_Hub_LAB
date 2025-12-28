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
    CORS_ORIGINS: str = '["http://localhost:5175","https://fkhub.finkargo.com.co"]'

    # Database
    DATABASE_URL: str = ""

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760
    SUPPORTED_FILE_TYPES: str = '[".pdf",".jpg",".jpeg",".png",".xlsx",".xls"]'

    # Google Drive Configuration (shared credentials)
    # For production (Render): Use GOOGLE_DRIVE_CREDENTIALS_JSON with base64-encoded or raw JSON
    # For local dev: Use GOOGLE_DRIVE_CREDENTIALS_PATH with path to JSON file
    GOOGLE_DRIVE_CREDENTIALS_JSON: str = ""  # Base64-encoded or raw JSON service account credentials
    GOOGLE_DRIVE_CREDENTIALS_PATH: str = "./credentials/drive-service-account.json"
    GOOGLE_DRIVE_SCOPES: str = '["https://www.googleapis.com/auth/drive"]'

    # Google Drive Configuration - Mexico (MX)
    GOOGLE_DRIVE_FOLDER_ID: str = ""  # MX folder ID
    GOOGLE_DRIVE_MASTER_EXCEL_NAME: str = "Facturación MX 2025.xlsx"

    # Google Drive Configuration - Colombia (CO)
    GOOGLE_DRIVE_CO_FOLDER_ID: str = "1l3zOaD7Qt-KOHz97FLib4HwSEQqwjN2y"  # CO folder ID
    GOOGLE_DRIVE_CO_MASTER_EXCEL_NAME: str = "Reporte_Facturacion_CO.xlsx"
    GOOGLE_DRIVE_CO_HISTORICAL_EXCEL_NAME: str = "Archivo control facturacion mensual Finkargo Def.xlsx"

    # Session Cache Configuration
    SESSION_CACHE_TTL_MINUTES: int = 30
    MAX_ZIP_SIZE_MB: int = 50

    # Invoice Processing
    SUPPORTED_INVOICE_FORMATS: str = '[".xlsx",".xls"]'

    # LandingAI ADE (Agentic Document Extraction) Configuration
    LANDINGAI_API_KEY: str = ""
    LANDINGAI_PARSE_ENDPOINT: str = "https://api.va.landing.ai/v1/ade/parse"
    LANDINGAI_EXTRACT_ENDPOINT: str = "https://api.va.landing.ai/v1/ade/extract"

    # Banxico API Configuration (Mexico exchange rates)
    BANXICO_API_TOKEN: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
