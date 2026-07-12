import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent

# -----------------------------
# AI / RAG (unchanged from original project)
# -----------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-3.1-flash-lite"

TOP_K = 5
MIN_SIMILARITY = 0.20
ROUTER_THRESHOLD = 0.60

LOG_FILE = ROOT_DIR / "logs" / "requests.json"

CATEGORIES = {
    "Authentication",
    "Network",
    "Hardware",
    "Software",
    "General",
}

STATUSES = {
    "Resolved",
    "Needs More Information",
    "Escalated",
}

# -----------------------------
# Supabase / Auth
# -----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8501").rstrip("/")
AUTH_CALLBACK_URL = f"{APP_BASE_URL}/Auth_Callback"

# Don't crash on import (e.g. during local tooling/static analysis).
# The auth/db layer raises a clear error the first time it's actually used.
SUPABASE_CONFIGURED = bool(SUPABASE_URL and SUPABASE_KEY)
