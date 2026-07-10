import re

from config import CATEGORIES


KEYWORDS = {
    "Authentication": (
        "password",
        "login",
        "sign in",
        "signin",
        "credential",
        "mfa",
        "account",
        "locked out",
    ),
    "Network": (
        "vpn",
        "wifi",
        "wi-fi",
        "network",
        "dns",
        "firewall",
        "internet",
        "internal resources",
        "connectivity",
    ),
    "Hardware": (
        "printer",
        "laptop",
        "keyboard",
        "mouse",
        "monitor",
        "scanner",
        "offline",
    ),
    "Software": (
        "docker",
        "daemon",
        "application",
        "app",
        "software",
        "browser",
        "cache",
        "upload",
        "document",
        "install",
        "crash",
        "error",
        "service",
    ),
}


def classify_category(query, documents=None):
    text = query or ""

    for doc in documents or []:
        text += " "
        text += doc.get("file", "")
        text += " "
        text += doc.get("text", "")

    text = text.lower()

    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                return category

    return "General"


def normalize_category(category):
    if category in CATEGORIES:
        return category

    return "General"
