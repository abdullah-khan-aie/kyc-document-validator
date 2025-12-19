from app.core import get_settings
from supabase import create_client, Client
from functools import lru_cache

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    return create_client(
        get_settings().supabase_url.get_secret_value(),
        get_settings().supabase_key.get_secret_value()
    )