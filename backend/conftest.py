"""
Pytest configuration and fixtures for backend tests.

This file sets up mock environment variables before any test modules are imported,
preventing collection errors from modules that require Supabase configuration.
"""
import os

# Set mock environment variables BEFORE any imports that might trigger Supabase client initialization
# This ensures test collection doesn't fail when modules import supabase_config.py
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key-for-pytest-collection")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key-for-pytest-collection")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-pytest-collection")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

# Google Drive mock config (for test_google_drive_integration.py)
os.environ.setdefault("GOOGLE_DRIVE_CREDENTIALS_PATH", "./credentials/drive-service-account.json")
os.environ.setdefault("GOOGLE_DRIVE_FOLDER_ID", "test-folder-id")

import pytest


@pytest.fixture
def mock_supabase_env(monkeypatch):
    """
    Fixture to provide mock Supabase environment variables for tests.

    Usage:
        def test_something(mock_supabase_env):
            # Test code here - env vars are set
            pass
    """
    monkeypatch.setenv("SUPABASE_URL", "https://test-project.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "test-jwt-secret")
