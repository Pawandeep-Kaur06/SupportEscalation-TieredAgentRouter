import json
import re

from config import CATEGORIES, GEMINI_MODEL, STATUSES
from utils.classifier import classify_category
from utils.gemini_client import client


def _contains_any(text, terms):
    text = (text or "").lower()
    return any(term in text for term in terms)


def _has_words(text, words):
    text = (text or "").lower()
    return all(re.search(rf"\b{re.escape(word)}\b", text) for word in words)


def _known_tier1_response(query, documents, retrieval_confidence):
    query_text = (query or "").lower()
    kb_used = [doc.get("file", "") for doc in documents or [] if doc.get("file")]

    if _contains_any(query_text, ("clear browser cache", "clear cache", "browser cache")):
        return {
            "category": "Software",
            "answer": (
                "Open your browser settings, search for 'cache' or 'clear browsing data', "
                "select cached images/files, and clear it. Then close and reopen the browser "
                "and try the page again. If the issue continues, try an incognito/private window "
                "or a different browser to confirm whether the problem is browser-specific."
            ),
            "status": "Resolved",
            "escalation_reason": "",
            "justification": "Common browser cache issue with safe Tier 1 troubleshooting steps.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    if _contains_any(query_text, ("upload document", "upload documents", "upload file", "upload files")):
        return {
            "category": "Software",
            "answer": (
                "Use the application's upload or attachment button, choose the document, "
                "wait for the upload progress to finish, and save or submit the form. "
                "If it fails, check that the file type is allowed, the file is within the size limit, "
                "rename the file without special characters, and retry with a stable connection."
            ),
            "status": "Resolved",
            "escalation_reason": "",
            "justification": "Document upload requests usually have actionable Tier 1 checks.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    if (
        _contains_any(query_text, ("forgot password", "password reset"))
        or _has_words(query_text, ("reset", "password"))
    ):
        return {
            "category": "Authentication",
            "answer": (
                "Use the 'Forgot password' or password reset link on the sign-in page, "
                "verify your identity, create a new password that meets the policy, and then "
                "sign in again. If the reset email does not arrive, check spam/junk folders, "
                "confirm you used the correct account email, and request a new reset link."
            ),
            "status": "Resolved",
            "escalation_reason": "",
            "justification": "Password reset is a standard Tier 1 support workflow.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    if _contains_any(query_text, ("printer offline", "printer is offline")):
        return {
            "category": "Hardware",
            "answer": (
                "Confirm the printer is powered on, connected to WiFi or Ethernet, and has no paper "
                "or toner errors. On your computer, remove any paused jobs, set the correct printer "
                "as default, and restart both the printer and the print spooler or computer. "
                "Try printing a test page after it shows online."
            ),
            "status": "Resolved",
            "escalation_reason": "",
            "justification": "Printer offline issues usually have safe first-level hardware checks.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    if _contains_any(query_text, ("docker daemon", "docker won't start", "docker wont start")):
        return {
            "category": "Software",
            "answer": (
                "Docker daemon startup failures usually need specialist review because the cause may "
                "be the Docker service state, container runtime, permissions, or host resource limits."
            ),
            "status": "Escalated",
            "escalation_reason": "Docker daemon startup failure requires software specialist diagnostics.",
            "justification": "The issue is beyond basic Tier 1 guidance and maps to Software Tier 2.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    if _contains_any(query_text, ("vpn connected", "cannot access internal resources", "can't access internal resources")):
        return {
            "category": "Network",
            "answer": (
                "VPN is connected but internal resources are unreachable, so a network specialist "
                "should verify routing, DNS resolution, split-tunnel rules, and access policy."
            ),
            "status": "Escalated",
            "escalation_reason": "Connected VPN with failed internal access requires Network Tier 2 review.",
            "justification": "The symptom points to a network routing or access issue after basic connection succeeds.",
            "kb_articles_used": kb_used,
            "retrieval_confidence": int(retrieval_confidence * 100),
        }

    return None


def _fallback_response(query, retrieval_confidence, reason):
    return {
        "category": "General",
        "answer": (
            "I could not safely generate a structured Tier 1 answer. "
            "Please review the retrieved knowledge base context and provide "
            "the affected system, error message, recent changes, and urgency."
        ),
        "status": "Needs More Information",
        "escalation_reason": reason,
        "justification": "A safe fallback was returned to avoid terminating the application.",
        "kb_articles_used": [],
        "retrieval_confidence": int(retrieval_confidence * 100),
    }


def _strip_code_fences(text):
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text.replace("```json", "").replace("```", "").strip()


def _parse_json_response(text):
    text = _strip_code_fences(text or "")

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise

        return json.loads(match.group(0))


def _normalise_result(result, retrieval_confidence):
    category = result.get("category", "General").strip()
    status = result.get("status", "Needs More Information").strip()

    if category not in CATEGORIES:
        category = "General"

    if status not in STATUSES:
        status = "Needs More Information"

    return {
        "category": category,
        "answer": result.get("answer", "More information is required to continue troubleshooting."),
        "status": status,
        "escalation_reason": result.get("escalation_reason", ""),
        "justification": result.get("justification", ""),
        "kb_articles_used": result.get("kb_articles_used", []),
        "retrieval_confidence": int(retrieval_confidence * 100),
    }


# -----------------------------
# Tier 1 Agent
# -----------------------------
def tier1_response(query, documents, retrieval_confidence):
    known_response = _known_tier1_response(query, documents, retrieval_confidence)

    if known_response:
        return known_response

    if not documents:
        category = classify_category(query)
        return _fallback_response(
            query,
            retrieval_confidence,
            "No relevant knowledge base documents were retrieved.",
        ) | {"category": category}

    kb = ""

    for doc in documents:
        kb += doc["text"]
        kb += "\n\n"

    kb_used = [
        doc["file"] for doc in documents
    ]

    kb_articles = "\n".join(
        f"- {file}" for file in kb_used
    )

    prompt = f"""
You are the Tier 1 General Support Agent in a tiered IT support router.

Use the user's question and retrieved Knowledge Base context below.
Return ONLY one valid JSON object. Do not include markdown, prose, comments, or code fences.

User Question:
{query}

Retrieved Knowledge Base Articles:
{kb_articles}

Knowledge Base Context:
{kb}

Required JSON schema:
{{
    "category": "",
    "answer": "",
    "status": "",
    "escalation_reason": "",
    "justification": "",
    "kb_articles_used": []
}}

Rules:

category must be one of

Authentication
Network
Software
Hardware
General

status must be one of

Resolved
Needs More Information
Escalated

Decision Policy:

1. If the Knowledge Base contains troubleshooting steps that the user can perform immediately,
   return:

   status = Resolved

   even if additional information could improve the diagnosis.

2. Use Needs More Information ONLY when troubleshooting cannot continue without a missing detail
   such as a specific error message, affected product, exact failure point, or environment.

   Example:
   - "My application shows error 0x80070005."
   - "Docker build fails." (Need error output.)

3. Use Escalated ONLY if

   - the KB has no relevant solution,
   OR
   - administrator privileges are required,
   OR
   - specialist investigation is clearly needed.

4. Never choose Needs More Information if you can provide useful first-level troubleshooting.

5. Prefer Resolved over Needs More Information whenever the KB contains applicable troubleshooting.

6. The Answer should always contain:
   • Immediate troubleshooting steps formatted as a clean bulleted list (using `-` or `*`), NOT a single dense paragraph or a numbered inline list.
   • Expected outcome
   • Only then request any optional additional information


IMPORTANT:

Tier 1 is expected to resolve most common IT support requests.

If the Knowledge Base contains relevant troubleshooting steps,
return:

status = "Resolved"

even if additional information might help later.

Only use:

status = "Needs More Information"

when troubleshooting cannot continue without the missing information.

Examples:

Question:
How do I clear browser cache?

Status:
Resolved

Question:
How do I upload documents?

Status:
Resolved

Question:
Forgot password

Status:
Resolved

Question:
Docker build fails with error.

Status:
Needs More Information

Question:
Docker won't start.

Status:
Escalated

Question:
Active Directory replication failure.

Status:
Escalated

For kb_articles_used, include only file names from Retrieved Knowledge Base Articles that you used.
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        result = _parse_json_response(response.text)

    except Exception as error:
        return _fallback_response(
            query,
            retrieval_confidence,
            f"Tier 1 Gemini/JSON error: {error}",
        )

    return _normalise_result(result, retrieval_confidence)
