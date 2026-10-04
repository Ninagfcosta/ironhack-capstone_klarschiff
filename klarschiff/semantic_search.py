"""Search the master list by meaning (RAG idea from the course: embeddings + similarity).

Why (pilot need): the same product is written in many ways ("rock wool slab" / "Steinwolle-Platte"). A word match
misses these; a meaning search finds them, so the same product keeps the same approved code (consistency).
How: each approved product description becomes an embedding (OpenAI text-embedding-3-small). Vectors are cached
in data/master_vectors.json; the query is compared with cosine similarity. A vector database (Pinecone) is the
production option for large lists; for a pilot list a local file is enough.
Without an AI key it falls back to the word-based similarity of master_list.py.
"""
from __future__ import annotations

import json
import math

from . import config, master_list
from .config import DATA_DIR

CACHE = DATA_DIR / "master_vectors.json"
EMBED_MODEL = "text-embedding-3-small"


def _embed(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI
    kw = {"api_key": config.LLM_API_KEY, "timeout": 30}
    if config.LLM_BASE_URL:
        kw["base_url"] = config.LLM_BASE_URL
    resp = OpenAI(**kw).embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def _cos(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _vectors(products) -> dict:
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    todo = [p for p in products if p.description not in cache]
    if todo:
        for p, v in zip(todo, _embed([p.description for p in todo])):
            cache[p.description] = v
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
    return cache


def search(query: str, top: int = 5) -> list[dict]:
    """Return the closest approved products: [{product_id, hs_code, description, score, method}]."""
    products = master_list.load()
    if not query.strip() or not products:
        return []
    if config.llm_available():
        try:
            vecs = _vectors(products)
            q = _embed([query])[0]
            scored = [(_cos(q, vecs[p.description]), p) for p in products if p.description in vecs]
            method = "meaning (embeddings)"
        except Exception:
            scored, method = [], ""
    else:
        scored, method = [], ""
    if not scored:
        scored = [(master_list.similarity(query, p.description), p) for p in products]
        method = "words (offline)"
    scored.sort(key=lambda x: -x[0])
    return [{"product_id": p.product_id, "hs_code": p.hs_code or "-", "description": p.description,
             "score": round(s, 2), "method": method} for s, p in scored[:top]]
