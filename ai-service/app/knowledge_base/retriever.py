"""
Loads the pre-built FAISS index and provides a search function.

Why: The agent calls this before answering — it retrieves the most
relevant troubleshooting chunks so the reply is grounded in real
documentation, not hallucinated advice.
"""

import os
import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

INDEX_PATH = os.path.join(os.path.dirname(__file__), "kb.index")
META_PATH = os.path.join(os.path.dirname(__file__), "kb_meta.json")

# Load model once at import time (stays in memory)
_model = SentenceTransformer("all-MiniLM-L6-v2")
_index = None
_kb_data = None


def _load():
    """Lazy-load the index and metadata on first search."""
    global _index, _kb_data
    if _index is not None:
        return

    if not os.path.exists(INDEX_PATH):
        logger.warning("Knowledge base index not found. Run: python -m app.knowledge_base.build_kb")
        _index = None
        _kb_data = {"chunks": [], "metadata": []}
        return

    _index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "r") as f:
        _kb_data = json.load(f)

    logger.info(f"Knowledge base loaded: {_index.ntotal} vectors")


def search(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the knowledge base for chunks relevant to the query.
    Returns a list of {text, source, score} dicts, best match first.
    """
    _load()

    if _index is None or _index.ntotal == 0:
        return []

    query_vector = _model.encode([query])
    query_vector = np.array(query_vector, dtype="float32")

    distances, indices = _index.search(query_vector, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0:  # FAISS returns -1 for empty slots
            continue
        results.append({
            "text": _kb_data["chunks"][idx],
            "source": _kb_data["metadata"][idx]["source"],
            "score": float(dist),  # lower = better match
        })

    return results