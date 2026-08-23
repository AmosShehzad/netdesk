"""
One-time script: reads all .txt files in documents/, chunks them,
embeds them with sentence-transformers, and saves a FAISS index.

Run from ai-service root:
    python -m app.knowledge_base.build_kb

Why: The agent needs a searchable knowledge base to find relevant
troubleshooting guides before answering, instead of guessing.
"""

import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "kb.index")
META_PATH = os.path.join(os.path.dirname(__file__), "kb_meta.json")

# Small, fast model — runs locally, no API needed
model = SentenceTransformer("all-MiniLM-L6-v2")


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks so we don't lose context at boundaries."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks


def build():
    all_chunks = []
    metadata = []  # stores which file and position each chunk came from

    for filename in sorted(os.listdir(DOCS_DIR)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(DOCS_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            metadata.append({"source": filename, "chunk_index": i})

    print(f"Total chunks: {len(all_chunks)}")

    # Embed all chunks into vectors
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    # Build FAISS index (L2 distance — smaller = more similar)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save index and metadata
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump({"chunks": all_chunks, "metadata": metadata}, f)

    print(f"Index saved to {INDEX_PATH} ({index.ntotal} vectors, {dimension}d)")


if __name__ == "__main__":
    build()