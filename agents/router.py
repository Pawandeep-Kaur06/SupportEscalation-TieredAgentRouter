from rag.retrieve import retrieve_documents
from utils.confidence import calculate_confidence
from utils.classifier import classify_category
from config import ROUTER_THRESHOLD


def route_query(query, documents=None, scores=None):

    if documents is None or scores is None:
        documents, scores = retrieve_documents(query)

    confidence = calculate_confidence(scores)

    if confidence >= ROUTER_THRESHOLD:

        tier = "Tier1"

    else:

        tier = "Tier2"

    return {

        "tier": tier,

        "confidence": confidence,

        "category": classify_category(query, documents),

        "documents": documents,

        "scores": scores

    }

