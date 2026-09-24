"""Retrieval (the "R" in RAG): find the most likely tariff headings in the curated knowledge base.

Uses BM25, a classic keyword-ranking method. It is transparent (you can see why a heading matched),
free, runs offline and gives the LLM a short list of real candidate codes instead of letting it guess.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache

from .config import KNOWLEDGE_DIR
from .models import Candidate

# Small German/English glossary, so German invoices also match (Lieferschein, Rechnung ...).
GLOSSARY = {
    "zement": "cement", "portlandzement": "portland cement", "klinker": "clinker", "betonstahl": "rebar reinforcing steel",
    "bewehrungsstahl": "reinforcing steel rebar", "stahl": "steel", "mineralwolle": "mineral wool", "steinwolle": "stone wool rock wool",
    "dämmung": "insulation", "daemmung": "insulation", "gipskarton": "plasterboard gypsum board", "gipsplatte": "plasterboard",
    "schnittholz": "sawn timber", "holz": "wood", "rundholz": "roundwood logs", "balken": "beams", "fliesen": "tiles",
    "ziegel": "bricks", "dachziegel": "roof tiles", "fenster": "window", "tür": "door", "tuer": "door", "beton": "concrete",
    "betonfertigteile": "precast concrete", "fertigteil": "prefabricated", "wandelemente": "wall elements panels",
    "mörtel": "mortar", "moertel": "mortar", "kies": "gravel", "sand": "sand", "glas": "glass", "kalk": "lime",
    "aluminium": "aluminium", "profile": "profiles", "matten": "mesh", "baustahlmatten": "reinforcing mesh",
    # added after error analysis of TC16 (v2.0 missed "in Ringen" = in coils):
    "ringen": "coils", "ring": "coil", "coils": "coils", "gerippt": "ribbed", "gerippter": "ribbed",
}

STOP = {"of", "the", "and", "a", "an", "in", "for", "with", "to", "from", "or", "on", "by", "per", "other", "invoice",
        "shipment", "bags", "tons", "tonnes", "kg", "pcs", "pieces", "attached", "missing", "packing", "list",
        "rechnung", "anbei", "lieferschein", "werkszeugnis", "beiliegend", "fehlt", "ohne", "mit"}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    words = re.findall(r"[a-zäöüß0-9]+", text)
    out: list[str] = []
    for w in words:
        if w in GLOSSARY:
            out.extend(GLOSSARY[w].split())
        elif w not in STOP and not w.isdigit():
            out.append(w)
    # light stemming: plural "s"
    return [w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w for w in out]


@lru_cache(maxsize=1)
def load_kb() -> dict:
    return json.loads((KNOWLEDGE_DIR / "hs_headings.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _index():
    kb = load_kb()["headings"]
    docs = []
    for h in kb:
        # keywords count twice: they are the words traders actually use
        text = h["title"] + " " + (" ".join(h["keywords"]) + " ") * 2
        docs.append(tokenize(text))
    df = Counter()
    for d in docs:
        df.update(set(d))
    avgdl = sum(len(d) for d in docs) / len(docs)
    return kb, docs, df, avgdl


def search(query: str, k: int = 5) -> list[Candidate]:
    kb, docs, df, avgdl = _index()
    q = tokenize(query)
    n = len(docs)
    k1, b = 1.5, 0.75
    scores = []
    for h, d in zip(kb, docs):
        tf = Counter(d)
        s = 0.0
        for t in set(q):
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        scores.append(s)
    ranked = sorted(zip(kb, scores), key=lambda x: -x[1])[:k]
    return [Candidate(code=h["code"], title=h["title"], score=round(s, 3)) for h, s in ranked if s > 0]


def get_heading(code: str) -> dict | None:
    for h in load_kb()["headings"]:
        if h["code"] == code:
            return h
    return None
