from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END

from agents.router import route_query
from agents.tier1.general_agent import tier1_response
from agents.tier2.dispatcher import dispatch
from logger import log_request
from rag.retrieve import retrieve_documents
from utils.classifier import normalize_category


# -----------------------------
# Graph State
# -----------------------------

class AgentState(TypedDict):
    query: str
    documents: list
    scores: Any
    routing: dict
    tier1: dict
    handoff: dict
    tier2: dict
    final_answer: str
    log_entry: dict


# -----------------------------
# Node 1
# -----------------------------

def retrieve_node(state):

    documents, scores = retrieve_documents(
        state["query"]
    )

    state["documents"] = documents
    state["scores"] = scores

    return state


# -----------------------------
# Node 2
# -----------------------------

def router_node(state):

    routing = route_query(
        state["query"],
        state.get("documents", []),
        state.get("scores", [])
    )

    state["routing"] = routing

    return state


# -----------------------------
# Node 3
# -----------------------------

def tier1_node(state):

    routing = state["routing"]

    tier1 = tier1_response(

        state["query"],

        routing["documents"],

        routing["confidence"]

    )

    state["tier1"] = tier1

    return state


# -----------------------------
# Node 4
# -----------------------------

def tier2_node(state):
    tier1_category = state["tier1"].get("category", "General")
    routing_category = state["routing"].get("category", "General")
    category = normalize_category(
        tier1_category if tier1_category != "General" else routing_category
    )

    handoff = {

        "query":
            state["query"],

        "retrieved_documents":
            state["routing"]["documents"],

        "retrieval_confidence":
            state["routing"]["confidence"],

        "router_decision":
            state["routing"]["tier"],

        "tier1":
            state["tier1"],

        "tier1_status":
            state["tier1"].get("status", "Needs More Information"),

        "category":
            category,

        "justification":
            state["tier1"].get("justification", "")

    }

    state["handoff"] = handoff

    result = dispatch(handoff)

    state["tier2"] = result

    state["final_answer"] = result["answer"]

    return state


# -----------------------------
# Node 5
# -----------------------------

def finish_node(state):

    if state["tier1"]["status"] == "Resolved":

        state["final_answer"] = state["tier1"]["answer"]

    elif state["tier1"]["status"] == "Needs More Information":

        state["final_answer"] = state["tier1"]["answer"]

    return state


# -----------------------------
# Node 6
# -----------------------------

def logger_node(state):

    used_tier2 = bool(state.get("tier2"))

    if used_tier2:

        final_status = state["tier2"]["status"]

    else:

        final_status = state["tier1"]["status"]

    tier_used = "Tier2" if used_tier2 else "Tier1"
    specialist = state.get("tier2", {}).get("specialist", "")

    route = [
        "Router",
        "Tier1"
    ]

    if tier_used == "Tier2":
        route.append("Tier2")

    category = (
        state.get("handoff", {}).get("category")
        if used_tier2
        else state["tier1"].get("category", "General")
    )

    try:
        state["log_entry"] = log_request(
            query=state["query"],
            retrieval_confidence=state["routing"].get("confidence", 0.0),
            tier_used=tier_used,
            category=category,
            status=final_status,
            route=route,
            specialist=specialist,
        )

    except Exception as error:

        state["log_entry"] = {
            "error": str(error)
        }

    return state


# -----------------------------
# Conditional Edge
# -----------------------------

def should_escalate(state):

    status = state["tier1"]["status"].strip().lower()

    if status == "escalated":
        return "tier2"

    return "finish"


# -----------------------------
# Build Graph
# -----------------------------

builder = StateGraph(AgentState)

builder.add_node(
    "retrieve",
    retrieve_node
)

builder.add_node(
    "router",
    router_node
)

builder.add_node(
    "tier1",
    tier1_node
)

builder.add_node(
    "tier2",
    tier2_node
)

builder.add_node(
    "finish",
    finish_node
)

builder.add_node(
    "logger",
    logger_node
)

builder.add_edge(
    START,
    "retrieve"
)

builder.add_edge(
    "retrieve",
    "router",
)

builder.add_edge(
    "router",
    "tier1"
)

builder.add_conditional_edges(

    "tier1",

    should_escalate,

    {

        "tier2": "tier2",

        "finish": "finish"

    }

)

builder.add_edge(
    "tier2",
    "logger"
)

builder.add_edge(
    "finish",
    "logger"
)

builder.add_edge(
    "logger",
    END
)

graph = builder.compile()
