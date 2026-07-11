"""HTML badge helpers used across the chat and dashboard pages."""

_STATUS_CLASS = {
    "resolved": "se-badge-resolved",
    "needs more information": "se-badge-needs-info",
    "escalated": "se-badge-escalated",
}


def status_badge(status: str) -> str:
    css_class = _STATUS_CLASS.get((status or "").strip().lower(), "se-badge-needs-info")
    return f'<span class="se-badge {css_class}">{status or "Unknown"}</span>'


def tier_badge(tier_used: str, specialist: str = "") -> str:
    if tier_used == "Tier2":
        label = f"Tier 2 - {specialist}" if specialist else "Tier 2"
        return f'<span class="se-badge se-badge-tier2">{label}</span>'
    return '<span class="se-badge se-badge-tier1">Tier 1</span>'


def admin_badge() -> str:
    return '<span class="se-badge se-badge-admin">Admin</span>'
