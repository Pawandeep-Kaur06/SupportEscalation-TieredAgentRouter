from config import GEMINI_MODEL
from utils.gemini_client import client
import json
import re


STATUSES = {
    "Resolved",
    "Needs More Information",
    "Escalated",
}


def _fallback_response(reason):
    return {
        "answer": (
            "Tier 2 could not safely generate a structured specialist response. "
            "Review the Tier 1 findings and retry with the specific error, affected system, "
            "recent changes, and business impact."
        ),
        "status": "Needs More Information",
        "advanced_diagnostics": "",
        "root_cause": "",
        "next_action": "Collect the missing details and retry the specialist analysis.",
        "justification": reason,
    }


def _strip_code_fences(text):
    text = (text or "").strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return text.replace("```json", "").replace("```", "").strip()


def _parse_json_response(text):
    text = _strip_code_fences(text)

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if not match:
            raise

        return json.loads(match.group(0))


def _has_actionable_specialist_guidance(result):
    answer = result.get("answer", "").strip()
    next_action = result.get("next_action", "").strip()

    return len(answer) >= 80 and bool(next_action)


def _normalise_result(result):
    status = result.get("status", "Needs More Information").strip()

    if status not in STATUSES:
        status = "Needs More Information"

    if status == "Needs More Information" and _has_actionable_specialist_guidance(result):
        status = "Resolved"

    return {
        "answer": result.get("answer", "Tier 2 needs more information to continue."),
        "status": status,
        "advanced_diagnostics": result.get("advanced_diagnostics", ""),
        "root_cause": result.get("root_cause", ""),
        "next_action": result.get("next_action", ""),
        "justification": result.get("justification", ""),
    }


def run_specialist_agent(
    specialty,
    handoff
):
    kb = ""

    for doc in handoff["retrieved_documents"]:
        kb += doc["text"] + "\n\n"

    prompt = f"""
You are a Tier-2 {specialty} Support Engineer.
Return ONLY one valid JSON object. Do not include markdown, prose, comments, or code fences.

If the issue is a common end-user problem,
continue the troubleshooting in plain language.

Do not overwhelm users with enterprise infrastructure concepts unless clearly relevant.
Do not invent enterprise technologies, products, protocols, databases, identity systems, or logs
that are not implied by the user question, Tier 1 response, or Knowledge Base.


Tier 1 has already attempted first-level troubleshooting.

Your role is to build upon Tier 1, not replace it.

Instead:

1. Read the user's actual question carefully.

2. If the issue is a common end-user problem
(browser cache, login, uploading files, printer, Outlook, WiFi, password, etc.)

→ Continue troubleshooting in plain English.

→ Do NOT introduce enterprise technologies unless they are directly relevant.

3. Only provide advanced diagnostics when:

- administrator access is required
- server investigation is required
- logs must be inspected
- infrastructure failure is suspected
- Tier 1 troubleshooting has clearly failed

4. Match the user's technical level.

If the user is asking a basic question,
give a basic answer.

If the user is asking an advanced engineering question,
give an advanced engineering answer.

Never make a simple issue unnecessarily complex.

Never mention technologies that were not implied by the user's question or the Knowledge Base.

Original Query:

{handoff["query"]}

Router Decision:

{handoff["router_decision"]}

Retrieval Confidence:

{handoff["retrieval_confidence"]}

Tier 1 Status:

{handoff["tier1_status"]}

Tier 1 Category:

{handoff["category"]}

Tier 1 Justification:

{handoff["justification"]}

Tier 1 Response:

{handoff["tier1"]["answer"]}

Knowledge Base:

{kb}

Required JSON schema:
{{
    "answer":"",
    "status":"",
    "advanced_diagnostics":"",
    "root_cause":"",
    "next_action":"",
    "justification":""
}}

status must be one of

Resolved
Needs More Information
Escalated

Rules:

- Use "Resolved" if you provided concrete specialist troubleshooting steps or a clear next action
  the user can perform now.

- Optional diagnostics, logs, command output, or follow-up details belong in next_action.
  They do NOT make the status "Needs More Information" when the answer already gives useful
  specialist troubleshooting.

- Use "Needs More Information" only if you cannot provide any meaningful specialist troubleshooting
  until the user supplies missing technical details.

- Use "Escalated" only if another team or administrator must take over.

- Keep advanced_diagnostics empty or brief for common end-user issues.

- For infrastructure issues such as directory replication, server outages, routing failures,
  or administrative failures, include focused diagnostics that match the issue.
"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        result = _parse_json_response(response.text)

        return _normalise_result(result)

    except Exception as error:
        return _fallback_response(
            f"Tier 2 Gemini/JSON error: {error}"
        )
