from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

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
