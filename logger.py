import json
from datetime import datetime, timezone

from config import LOG_FILE


# --------------------------------
# Read Logs
# --------------------------------
def _read_logs():

    if not LOG_FILE.exists():
        return []

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                return data

    except (json.JSONDecodeError, OSError):
        pass

    return []


# --------------------------------
# Write Logs
# --------------------------------
def _write_logs(logs):

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            logs,
            f,
            indent=4
        )


# --------------------------------
# Log Request
# --------------------------------


def log_request(
    query,
    retrieval_confidence,
    tier_used,
    category,
    status,
    route=None,
    specialist="",
):

    status = status.strip()

    # Only "Resolved" means resolved
    resolved = (
        status.lower() == "resolved"
    )

    # Any Tier2 execution means escalation happened
    escalated = (
        tier_used == "Tier2"
    )

    resolved_by = None

    if resolved:

        resolved_by = tier_used

    entry = {

        "timestamp":
            datetime.now(timezone.utc).isoformat(),

        "query":
            query,

        "retrieval_confidence":
            round(float(retrieval_confidence), 2),

        "tier_used":
            tier_used,

        "specialist":
            specialist,

        "category":
            category,

        "status":
            status,

        "resolved":
            resolved,

        "resolved_by":
            resolved_by,

        "escalated":
            escalated,

        "route":
            route or []

    }

    logs = _read_logs()

    logs.append(entry)

    _write_logs(logs)

    return entry


# --------------------------------
# Return Raw Logs
# --------------------------------
def get_logs():

    return _read_logs()


# --------------------------------
# Dashboard Metrics
# --------------------------------
def get_metrics():

    logs = _read_logs()

    tier1_resolved = sum(

        1

        for item in logs

        if item.get("resolved_by") == "Tier1"

    )

    tier2_resolved = sum(

        1

        for item in logs

        if item.get("resolved_by") == "Tier2"

    )

    escalated = sum(

        1

        for item in logs

        if item.get("escalated")

    )

    unresolved = sum(

        1

        for item in logs

        if not item.get("resolved")

    )

    confidences = [

        float(item.get("retrieval_confidence", 0))

        for item in logs

    ]

    avg_confidence = (

        sum(confidences) / len(confidences)

        if confidences else 0

    )

    return {

        "total_queries":
            len(logs),

        "tier1_resolved":
            tier1_resolved,

        "tier2_resolved":
            tier2_resolved,

        "escalated":
            escalated,

        "unresolved":
            unresolved,

        "average_confidence":
            round(avg_confidence, 2)

    }
