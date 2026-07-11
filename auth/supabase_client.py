"""
Thin singleton wrapper around the Supabase Python client.

Everything else in auth/ and database/ imports `get_client()` from here
instead of constructing its own client, so there is exactly one client
per Streamlit process.
"""

from supabase import Client, create_client

from config import SUPABASE_CONFIGURED, SUPABASE_KEY, SUPABASE_URL

_client: Client | None = None


def get_client() -> Client:
    global _client

    if not SUPABASE_CONFIGURED:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY "
            "as environment variables (see .env.example)."
        )

    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _client
