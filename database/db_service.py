"""
All Supabase PostgREST reads/writes for conversations, messages, and
query_logs live here. Callers never touch the Supabase client directly.

Every function assumes auth.auth_service.restore_session() has already
been called this run, so the Supabase client is scoped to the current
user's JWT and RLS enforces ownership automatically.
"""

from auth.supabase_client import get_client


class DatabaseError(RuntimeError):
    """Raised when Supabase returns an unexpected database response."""


def _first_row(resp, action: str) -> dict:
    data = getattr(resp, "data", None) or []
    if not data:
        raise DatabaseError(f"Supabase returned no rows while trying to {action}.")
    return data[0]


# -----------------------------
# Conversations
# -----------------------------

def create_conversation(user_id: str, title: str = "New Chat") -> dict:
    client = get_client()
    resp = (
        client.table("conversations")
        .insert({"user_id": user_id, "title": title})
        .execute()
    )
    return _first_row(resp, "create a conversation")


def list_conversations(user_id: str) -> list[dict]:
    client = get_client()
    resp = (
        client.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return resp.data or []


def rename_conversation(conversation_id: str, title: str) -> None:
    client = get_client()
    client.table("conversations").update({"title": title}).eq(
        "id", conversation_id
    ).execute()


def delete_conversation(conversation_id: str) -> None:
    client = get_client()
    client.table("conversations").delete().eq("id", conversation_id).execute()


def generate_title(first_message: str, max_len: int = 48) -> str:
    text = " ".join((first_message or "New Chat").split())
    return text[:max_len] + ("..." if len(text) > max_len else "")


# -----------------------------
# Messages
# -----------------------------

def add_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    client = get_client()
    resp = (
        client.table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
            }
        )
        .execute()
    )
    return _first_row(resp, "add a message")


def list_messages(conversation_id: str) -> list[dict]:
    client = get_client()
    resp = (
        client.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return resp.data or []


# -----------------------------
# Query logs
# -----------------------------

def log_query(
    user_id: str,
    conversation_id: str,
    query: str,
    retrieval_confidence: float,
    tier_used: str,
    category: str,
    status: str,
    route: list | None = None,
    specialist: str = "",
    response_time_ms: int | None = None,
) -> dict:
    status = (status or "").strip()
    resolved = status.lower() == "resolved"
    escalated = tier_used == "Tier2"

    client = get_client()
    resp = (
        client.table("query_logs")
        .insert(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "query": query,
                "retrieval_confidence": round(float(retrieval_confidence), 2),
                "tier_used": tier_used,
                "specialist": specialist,
                "category": category,
                "status": status,
                "resolved": resolved,
                "resolved_by": tier_used if resolved else None,
                "escalated": escalated,
                "route": route or [],
                "response_time_ms": response_time_ms,
            }
        )
        .execute()
    )
    return _first_row(resp, "log a query")


def list_recent_logs(limit: int = 100) -> list[dict]:
    """Admin only (RLS enforces this) - most recent queries across all users."""
    client = get_client()
    resp = (
        client.table("query_logs")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


def get_metrics() -> dict:
    """Admin dashboard metrics, computed client-side from query_logs.

    For larger datasets, replace this with a Postgres view or RPC.
    This is fine for a dashboard read every few seconds at prototype scale.
    """
    logs = list_recent_logs(limit=5000)

    total = len(logs)
    tier1_resolved = sum(1 for l in logs if l.get("resolved_by") == "Tier1")
    tier2_resolved = sum(1 for l in logs if l.get("resolved_by") == "Tier2")
    escalated = sum(1 for l in logs if l.get("escalated"))
    unresolved = sum(1 for l in logs if not l.get("resolved"))
    confidences = [float(l.get("retrieval_confidence", 0)) for l in logs]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    categories: dict[str, int] = {}
    for l in logs:
        cat = l.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1

    response_times = [
        l["response_time_ms"] for l in logs if l.get("response_time_ms") is not None
    ]
    avg_response_ms = sum(response_times) / len(response_times) if response_times else 0

    return {
        "total_queries": total,
        "tier1_resolved": tier1_resolved,
        "tier2_resolved": tier2_resolved,
        "escalated": escalated,
        "unresolved": unresolved,
        "average_confidence": round(avg_confidence, 2),
        "categories": categories,
        "average_response_ms": round(avg_response_ms, 1),
        "recent_escalations": [l for l in logs if l.get("escalated")][:10],
    }


def count_conversations(user_id: str) -> int:
    client = get_client()
    resp = (
        client.table("conversations")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .execute()
    )
    return resp.count or 0


def count_users() -> int:
    """Admin only."""
    client = get_client()
    resp = client.table("profiles").select("id", count="exact").execute()
    return resp.count or 0
