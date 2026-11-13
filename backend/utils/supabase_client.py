from functools import lru_cache

from supabase import create_client

from app.config import settings


@lru_cache(maxsize=1)
def create_supabase_client():
    if not settings.supabase_url:
        raise ValueError("SUPABASE_URL is missing.")
    if not settings.supabase_key:
        raise ValueError("SUPABASE_PUBLISHABLE_KEY (or SUPABASE_KEY) is missing.")
    return create_client(settings.supabase_url, settings.supabase_key)