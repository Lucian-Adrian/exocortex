"""
Supabase client factory.

Provides a singleton-like access to the Supabase client
configured with environment variables.
"""

from functools import lru_cache

from supabase import Client, create_client

from exo.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """
    Get or create a Supabase client.

    Uses lru_cache to ensure we don't recreate the client
    unnecessarily, preserving connection pooling behavior.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
