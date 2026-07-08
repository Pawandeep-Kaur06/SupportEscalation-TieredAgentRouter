import pickle
import faiss
from pathlib import Path
import numpy as np
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
from utils.confidence import calculate_confidence
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent

INDEX_DIR = BASE_DIR / "index"

# Load FAISS index
index = faiss.read_index(
    str(INDEX_DIR / "faiss_index.bin")
)


# Load metadata
with open(INDEX_DIR / "metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

query = input("Ask something: ")

query_embedding = model.encode([query])

query_embedding = np.array(query_embedding).astype("float32")

# Normalize BEFORE searching
faiss.normalize_L2(query_embedding)

k = 3

distances, indices = index.search(
    query_embedding,
    k
)
faiss.normalize_L2(query_embedding)
print("\nTop Results:\n")

for i in indices[0]:

    print("=" * 60)

    print(metadata[i]["file"])

    print()

    print(metadata[i]["text"][:500])

    print()
for rank, (idx, dist) in enumerate(
    zip(indices[0], distances[0]),
    start=1
):
    scores = distances[0]

    confidence = calculate_confidence(scores)

    print(f"\nResult {rank}")
    print(f"Similarity: {dist:.4f}")
    print(metadata[idx]["file"])
    print(metadata[idx]["text"][:400])
    print(f"\nConfidence: {confidence:.2f}")