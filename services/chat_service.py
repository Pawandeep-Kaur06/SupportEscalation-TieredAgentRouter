"""
Bridges the UI to the existing, untouched LangGraph pipeline
(`graph.py`) and persists the exchange to Supabase.

This is the ONLY new code that calls graph.invoke(). The backend
(retriever, router, tier1/tier2 agents, langgraph wiring) is unmodified.
"""

import time
import json

from config import GEMINI_MODEL
from database import db_service
from graph import graph
from utils.gemini_client import client


def detect_intent_and_reply(query: str) -> dict:
    """
    Sends the user query to Gemini to classify whether it is:
    1. conversational (greetings, small talk)
    2. out_of_scope (not related to IT support helpdesk)
    3. support (genuine IT issue / troubleshooting)
    
    Returns a dict with intent and generated reply.
    """
    prompt = f"""
You are an intent classifier and guardrail system for an enterprise IT support assistant.
Your job is to classify the user's query into one of three categories:
1. "conversational": Greetings, salutations, farewells, gratitude, or basic small talk (e.g., "hi", "hello", "thanks", "bye", "who are you?", "how are you?").
2. "out_of_scope": Any query that is completely unrelated to IT support, troubleshooting, system administration, hardware, or software (e.g., "how to bake a cake", "what is the recipe for cookies", "who won the world cup", "write a poem", "solve 2+2").
3. "support": A genuine IT support request, system troubleshooting issue, technical question, or helpdesk ticket (e.g., "reset my password", "VPN is dropping connection", "Docker daemon is not running", "printer offline").

You must return a single JSON object. Do not include markdown formatting, backticks (like ```json), or any commentary outside the JSON.
JSON format:
{{
    "intent": "conversational" | "out_of_scope" | "support",
    "reply": "For 'conversational', write a brief, friendly, natural reply (e.g., 'Hello! How can I assist you with your IT issues today?'). For 'out_of_scope', write a polite canned reply stating you are only programmed for IT support (e.g., 'I am sorry, but I am only programmed to assist with IT support and helpdesk queries. How can I help you with your technical issues?'). For 'support', keep this field empty."
}}

Query: "{query}"
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        text = response.text.strip()
        # Clean up any potential markdown formatting code blocks
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(text)
        intent = data.get("intent", "support")
        if intent not in ["conversational", "out_of_scope", "support"]:
            intent = "support"
        reply = data.get("reply", "")
        return {"intent": intent, "reply": reply}
    except Exception:
        # Fallback to support in case of LLM error to avoid interrupting the workflow
        return {"intent": "support", "reply": ""}


def run_query(user_id: str, conversation_id: str, query: str) -> dict:
    """
    Runs the query through the existing graph, stores the user + assistant
    messages, and writes a query_log row. Returns the raw graph result so
    the UI can render tier/status/confidence/technical details exactly as
    the original Streamlit app did.
    """
    db_service.add_message(conversation_id, "user", query)

    # Detect intent
    intent_res = detect_intent_and_reply(query)
    intent = intent_res.get("intent", "support")

    if intent in ("conversational", "out_of_scope"):
        reply = intent_res.get("reply", "Hello! How can I help you today?")
        db_service.add_message(
            conversation_id,
            "assistant",
            reply,
            metadata={
                "is_conversational": True,
            },
        )
        return {
            "final_answer": reply,
            "is_conversational": True,
            "routing": {},
            "tier1": {},
            "tier2": {},
            "log_entry": {},
        }

    # For genuine IT issues, run the full RAG and escalation pipeline
    start = time.perf_counter()
    result = graph.invoke({"query": query})
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    routing = result.get("routing", {})
    tier1 = result.get("tier1", {})
    tier2 = result.get("tier2") or {}
    used_tier2 = bool(tier2)

    final_status = tier2.get("status") if used_tier2 else tier1.get("status")
    final_category = (
        result.get("handoff", {}).get("category")
        if used_tier2
        else tier1.get("category", routing.get("category", "General"))
    )
    specialist = tier2.get("specialist", "")
    tier_used = "Tier2" if used_tier2 else "Tier1"
    route = result.get("log_entry", {}).get("route", [])

    db_service.add_message(
        conversation_id,
        "assistant",
        result.get("final_answer", ""),
        metadata={
            "tier_used": tier_used,
            "status": final_status,
            "category": final_category,
            "specialist": specialist,
            "confidence": routing.get("confidence", 0.0),
            "route": route,
            "tier1": tier1,
            "tier2": tier2,
            "documents": routing.get("documents", []),
            "response_time_ms": elapsed_ms,
        },
    )

    db_service.log_query(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query,
        retrieval_confidence=routing.get("confidence", 0.0),
        tier_used=tier_used,
        category=final_category,
        status=final_status or "Needs More Information",
        route=route,
        specialist=specialist,
        response_time_ms=elapsed_ms,
    )

    return result

