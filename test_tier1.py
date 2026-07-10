from agents.tier1.general_agent import tier1_response
from rag.retrieve import retrieve_documents

query = input("Ask: ")

docs, scores = retrieve_documents(query)

result = tier1_response(
    query,
    docs,
    0.75
)

print(result)