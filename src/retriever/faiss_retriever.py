"""Dense passage retrieval using a prebuilt FAISS index."""

from __future__ import annotations

import json
import os
import warnings
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "data" / "index" / "faiss_index.index"
CHUNKS_PATH = ROOT / "data" / "chunks" / "chunks.json"
@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def _load_chunks() -> list[str]:
    if not CHUNKS_PATH.exists():
        return []
    payload = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("chunks", payload.get("items", []))
    else:
        items = []

    texts: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("content") or ""
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
        elif isinstance(item, str):
            value = item.strip()
            if value:
                texts.append(value)
    return texts


def _query_keywords(query: str) -> list[str]:
    return [word.lower() for word in query.split() if len(word) > 3]


def get_passage_context(query: str, top_k: int = 5) -> str:
    """Return the strongest retrieved text chunks for a query.

    The FAISS index is constructed offline and reused at query time. Any keyword
    filtering is applied only to the retrieved candidates, never by re-encoding the
    corpus on the fly.
    """
    if not query or not INDEX_PATH.exists():
        return ""

    chunks = _load_chunks()
    if not chunks:
        return ""

    index = faiss.read_index(str(INDEX_PATH))
    if index is None or index.ntotal == 0:
        return ""
    if index.ntotal == 0:
        return ""

    vector = _load_model().encode([query], convert_to_numpy=True, normalize_embeddings=True)
    search_limit = min(max(top_k * 4, 20), index.ntotal)
    _, indices = index.search(np.asarray(vector, dtype=np.float32), search_limit)
    ranked = [chunks[int(i)] for i in indices[0] if 0 <= i < len(chunks)]

    keywords = _query_keywords(query)
    if keywords:
        filtered = [chunk for chunk in ranked if any(keyword in chunk.lower() for keyword in keywords)]
        ranked = filtered or ranked

    cleaned = [chunk.strip() for chunk in ranked if chunk.strip()]
    return "\n\n".join(cleaned[:top_k]).strip()


if __name__ == "__main__":
    print(get_passage_context("What is ISRO?"))