"""
Thin singleton wrapper around the Supabase Python client.

Everything else in auth/ and database/ imports `get_client()` from here
instead of constructing its own client, so there is exactly one client
per Streamlit process.
"""

from config import SUPABASE_CONFIGURED, SUPABASE_KEY, SUPABASE_URL

_client = None


def get_client():
    global _client

    if not SUPABASE_CONFIGURED:
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY "
            "as environment variables (see .env.example)."
        )

    if _client is None:
        try:
            from supabase import create_client
        except ImportError as error:
            raise RuntimeError(
                "Supabase Python package is not installed. Run "
                "`pip install -r requirements.txt` in the project environment."
            ) from error

        _client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _client
