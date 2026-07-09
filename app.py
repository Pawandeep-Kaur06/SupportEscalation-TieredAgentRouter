from agents.router import route_query
from agents.tier1.general_agent import tier1_response

query = input("Ask: ")

# -------------------
# Router
# -------------------

routing = route_query(query)

print("\nRouter")
print("-------------------")

print("Tier:", routing["tier"])
print(
    "Retrieval Confidence:",
    int(routing["confidence"]*100),
    "%"
)

# -------------------
# Tier 1
# -------------------

tier1 = tier1_response(

    query,

    routing["documents"],

    routing["confidence"]

)

print("\nTier 1 Response")
print("-------------------")

print(tier1["answer"])

print()

print("Status:", tier1["status"])

# -------------------
# Route Further
# -------------------

if tier1["status"] == "Escalated":

    print("\nEscalating to Tier 2...")

elif tier1["status"] == "Needs More Information":

    print("\nNeed more information from user.")

else:

    print("\nIssue Resolved by Tier 1.")