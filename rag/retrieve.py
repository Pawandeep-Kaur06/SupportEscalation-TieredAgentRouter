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


def retrieve_documents(query, k=5):

    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    faiss.normalize_L2(query_embedding)

    scores, indices = index.search(query_embedding, k)

    docs = []

    for idx, score in zip(indices[0], scores[0]):
        if score >= 0.20:
            docs.append(metadata[idx])

    print("\nRetrieved Documents:\n")

    for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):

        docs.append(metadata[idx])

        print(f"{rank}. {metadata[idx]['file']}")
        print(f"Similarity: {score:.3f}")

    return docs, scores[0]


if __name__ == "__main__":

    query = input("Ask something: ")

    docs, scores = retrieve_documents(query)

    confidence = calculate_confidence(scores)

    print(f"\nConfidence: {confidence:.2f}")