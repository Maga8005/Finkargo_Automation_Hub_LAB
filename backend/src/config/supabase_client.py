"""
Supabase client configuration for backend
"""
from supabase import create_client, Client
from functools import lru_cache
from .settings import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client instance (cached)

    Returns:
        Client: Supabase client with service role key for full access
    """
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("Supabase credentials not configured. Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")

    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY  # Use service key for backend operations
    )

    return supabase


def get_supabase_anon_client() -> Client:
    """
    Get Supabase client with anon key (for user-level operations)

    Returns:
        Client: Supabase client with anon key
    """
    settings = get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("Supabase credentials not configured")

    supabase: Client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )

    return supabase
