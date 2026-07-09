import os
import sys
import json
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# -----------------------------
# Project Root
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from agents.router import route_query

# -----------------------------
# Gemini
# -----------------------------
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -----------------------------
# Tier 1 Agent
# -----------------------------
def tier1_response(query, documents, retrieval_confidence):

    kb = ""

    for doc in documents:
        kb += doc["text"]
        kb += "\n\n"

    kb_used = "\n".join(
        f"- {doc['file']}" for doc in documents
    )

    prompt = f"""
You are a Tier-1 Enterprise IT Support Engineer.

Use ONLY the provided Knowledge Base.

Do NOT invent information.

If the user asks a broad question:

- First provide general troubleshooting.
- Then mention what additional information is needed.

Do NOT immediately escalate simply because the question is broad.

Knowledge Base:

{kb}

Retrieved KB Files:

{kb_used}

User Query:

{query}

Return ONLY valid JSON.

{{
    "category":"",
    "answer":"",
    "status":"",
    "escalation_reason":"",
    "justification":"",
    "kb_articles_used":[]
}}

Rules:

category must be one of

Authentication
Network
Software
Hardware
Database
Security
Cloud
General

status must be one of

Resolved
Needs More Information
Escalated

Rules:

- If KB provides enough first-level troubleshooting,
  status = Resolved.

- If generic troubleshooting can be given but more
  information is required,
  status = Needs More Information.

- If KB cannot help OR specialist support is required,
  status = Escalated.

For "Needs More Information":

ALWAYS provide useful troubleshooting first,
then ask for additional information.

Never return markdown.
The troubleshooting output should be in bullet points.
Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    text = response.text.strip()

    # Remove markdown if Gemini adds it
    text = text.replace("```json", "")
    text = text.replace("```", "").strip()

    result = json.loads(text)

    # Add router confidence
    result["retrieval_confidence"] = int(
        retrieval_confidence * 100
    )

    return result


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":

    query = input("Ask: ")

    routing = route_query(query)

    print("\nRouter Decision")
    print("----------------")
    print("Tier:", routing["tier"])
    print("Retrieval Confidence:", int(routing["confidence"] * 100), "%")

    print("\nRunning Tier 1...\n")

    result = tier1_response(
        query,
        routing["documents"],
        routing["confidence"]
    )

    print("=" * 60)

    for key, value in result.items():
        print(f"{key}:")
        print(value)
        print()