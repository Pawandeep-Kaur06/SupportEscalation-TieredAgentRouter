from rag.retrieve import retrieve_documents
from utils.confidence import calculate_confidence


THRESHOLD = 0.60


def route_query(query):

    docs, scores = retrieve_documents(query)

    confidence = calculate_confidence(scores)

    if confidence >= THRESHOLD:

        tier = "Tier1"

    else:

        tier = "Tier2"

    return {

        "tier": tier,

        "confidence": confidence,

        "documents": docs,

        "scores": scores

    }


if __name__ == "__main__":

    query = input("Ask something: ")

    result = route_query(query)

    print("\nRouting Decision")

    print(result["tier"])

    print(result["confidence"])