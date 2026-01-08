"""
Supabase Client Configuration with Singleton Pattern
Provides both public (anon) and admin (service) clients
Based on proven architecture from Finkargo Pre-Approval System
"""
from supabase import create_client, Client
from typing import Optional
import logging
from functools import lru_cache
from .settings import get_settings
import jwt
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Singleton Supabase client manager.
    Maintains two client instances:
    - Public client (anon key): For standard operations, respects RLS
    - Admin client (service key): For privileged operations, bypasses RLS
    """

    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _admin_client: Optional[Client] = None

    def __new__(cls) -> 'SupabaseClient':
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Supabase clients if not already initialized"""
        if self._client is None or self._admin_client is None:
            self._initialize_clients()

    def _initialize_clients(self) -> None:
        """Initialize both public and admin Supabase clients"""
        settings = get_settings()

        if not settings.SUPABASE_URL:
            raise ValueError("SUPABASE_URL not configured in environment variables")

        if not settings.SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_ANON_KEY not configured in environment variables")

        if not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_SERVICE_KEY not configured in environment variables")

        try:
            # Public client (anon key) - Respects RLS policies
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase public client initialized successfully")

            # Admin client (service key) - Bypasses RLS policies
            self._admin_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase admin client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {str(e)}")
            raise

    @property
    def client(self) -> Client:
        """
        Get public Supabase client (anon key).
        Use for standard operations that should respect RLS.

        Returns:
            Client: Supabase client with anon key
        """
        if self._client is None:
            self._initialize_clients()
        return self._client

    @property
    def admin_client(self) -> Client:
        """
        Get admin Supabase client (service key).
        Use for privileged operations that bypass RLS.

        Returns:
            Client: Supabase client with service key
        """
        if self._admin_client is None:
            self._initialize_clients()
        return self._admin_client

    @property
    def auth(self):
        """
        Get auth instance for authentication operations.

        Returns:
            Auth client from public client
        """
        return self.client.auth

    @property
    def storage(self):
        """
        Get storage instance for file operations.
        Uses admin client for full access.

        Returns:
            Storage client from admin client
        """
        return self.admin_client.storage

    def get_user_from_token(self, token: str) -> Optional[dict]:
        """
        Validate JWT token and get user information.
        Uses local JWT verification for better performance.

        Args:
            token (str): JWT access token from Authorization header

        Returns:
            dict: User object if valid, None otherwise
        """
        try:
            settings = get_settings()

            # Decode and verify JWT locally
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )

            # Check if token is expired
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                logger.warning("Token is expired")
                return None

            # Create user object from JWT payload
            user = type('User', (), {
                'id': payload.get('sub'),
                'email': payload.get('email'),
                'user_metadata': payload.get('user_metadata', {}),
                'app_metadata': payload.get('app_metadata', {})
            })()

            return user

        except jwt.ExpiredSignatureError:
            logger.warning("Token is expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return None

    def verify_session(self, access_token: str) -> bool:
        """
        Verify if a session token is valid.

        Args:
            access_token (str): Session access token

        Returns:
            bool: True if valid, False otherwise
        """
        user = self.get_user_from_token(access_token)
        return user is not None


# Singleton instance
@lru_cache()
def get_supabase_client() -> SupabaseClient:
    """
    Get cached Supabase client singleton instance.

    Returns:
        SupabaseClient: Singleton instance with both public and admin clients
    """
    return SupabaseClient()


# Convenience instance for direct import
supabase_client = get_supabase_client()
