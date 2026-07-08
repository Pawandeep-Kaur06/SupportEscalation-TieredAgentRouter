import os
from pathlib import Path
folder = "../KnowledgeBaseGenerator/knowledge_base"

documents = []

for file in os.listdir(folder):

    if file.endswith(".txt"):

        with open(
            os.path.join(folder, file),
            "r",
            encoding="utf-8"
        ) as f:

            documents.append({
                "file": file,
                "text": f.read()
            })

print("Documents:", len(documents))
print(documents[0]["file"])
print(documents[0]["text"][:200])

from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)
texts = [doc["text"] for doc in documents]

embeddings = model.encode(
    texts,
    show_progress_bar=True
)
print(embeddings.shape)

import faiss
import numpy as np

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(
    np.array(embeddings).astype("float32")
)

print(index.ntotal)

import pickle
BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "index"
INDEX_DIR.mkdir(exist_ok=True)

faiss.write_index(
    index,
    str(INDEX_DIR / "faiss_index.bin")
)

with open(INDEX_DIR / "metadata.pkl", "wb") as f:
    pickle.dump(documents, f)

