import pickle
import faiss
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, MIN_SIMILARITY, TOP_K

BASE_DIR = Path(__file__).resolve().parent

INDEX_DIR = BASE_DIR / "index"

index = None
metadata = None
model = None


def _load_retriever():
    global index, metadata, model

    if index is None:
        index = faiss.read_index(
            str(INDEX_DIR / "faiss_index.bin")
        )

    if metadata is None:
        with open(INDEX_DIR / "metadata.pkl", "rb") as f:
            metadata = pickle.load(f)

    if model is None:
        model = SentenceTransformer(EMBEDDING_MODEL)

    return index, metadata, model


def retrieve_documents(query, k=TOP_K):
    if not query:
        return [], []

    try:
        loaded_index, loaded_metadata, loaded_model = _load_retriever()
    except Exception:
        return [], []

    try:
        query_embedding = loaded_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        faiss.normalize_L2(query_embedding)

        scores, indices = loaded_index.search(query_embedding, k)
    except Exception:
        return [], []

    docs = []
    seen_files = set()

    for idx, score in zip(indices[0], scores[0]):
        if idx < 0 or score < MIN_SIMILARITY:
            continue

        doc = loaded_metadata[idx]
        file_name = doc.get("file", str(idx))

        if file_name in seen_files:
            continue

        seen_files.add(file_name)
        docs.append(doc)

    return docs, scores[0]

