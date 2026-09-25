"""Retrieval (the "R" in RAG): find the most likely HS 2022 subheadings for any product.

v2.3: the index covers the whole Harmonized System (5,613 subheadings), not only construction materials.
A small reviewed layer (checked by a person, with trader keywords and rule flags) sits on top of it.

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
    # v2.3: general trade words, so German invoices work beyond construction (with an AI key, German is translated)
    "maschine": "machine", "maschinen": "machines", "ersatzteil": "spare part", "ersatzteile": "spare parts", "teile": "parts",
    "halbleiter": "semiconductor", "prüfgerät": "inspection apparatus", "pruefgeraet": "inspection apparatus",
    "messgerät": "measuring instrument", "messgeraet": "measuring instrument", "kabel": "cable", "schrauben": "screws",
    "pumpe": "pump", "ventil": "valve", "akku": "accumulator battery", "batterie": "battery", "kunststoff": "plastics",
    "gummi": "rubber", "kaffee": "coffee", "kakao": "cocoa", "möbel": "furniture", "moebel": "furniture", "stuhl": "chair",
    "tisch": "table", "bekleidung": "clothing apparel", "baumwolle": "cotton", "schuhe": "footwear", "spielzeug": "toys",
    "fahrrad": "bicycle", "fahrräder": "bicycles", "leuchte": "luminaire lamp", "leiterplatte": "printed circuit",
    "optisch": "optical", "optische": "optical", "linse": "lens", "linsen": "lenses",
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
    """Reviewed layer: headings checked by a person, with trader keywords and rule flags."""
    return json.loads((KNOWLEDGE_DIR / "hs_headings.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_hs() -> dict:
    """Universal layer: every HS 2022 subheading (5,613), public-domain UN reference texts."""
    return json.loads((KNOWLEDGE_DIR / "hs2022_subheadings.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _reviewed() -> dict[str, dict]:
    return {h["code"]: h for h in load_kb()["headings"]}


@lru_cache(maxsize=1)
def _index():
    """One BM25 index over ALL HS 2022 subheadings.

    Each document = subheading text (twice) + its heading + its chapter. Reviewed headings also get their
    trader keywords (twice), so words people really write on invoices ("rebar", "glulam") still match.
    """
    reviewed = _reviewed()
    items, docs = [], []
    for sh in load_hs()["subheadings"]:
        text = (sh["title"] + " ") * 2 + sh["heading"] + " " + sh["chapter"]
        r = reviewed.get(sh["code"])
        if r:
            text += " " + r["title"] + " " + (" ".join(r["keywords"]) + " ") * 2
        items.append((sh["code"], r["title"] if r else sh["title"], bool(r)))
        docs.append(Counter(tokenize(text)))
    df = Counter()
    for d in docs:
        df.update(d.keys())
    lens = [sum(d.values()) for d in docs]
    return items, docs, lens, df, sum(lens) / len(lens)


def search(query: str, k: int = 8) -> list[Candidate]:
    items, docs, lens, df, avgdl = _index()
    q = set(tokenize(query))
    n = len(docs)
    k1, b = 1.5, 0.75
    idf = {t: math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) for t in q if df[t]}
    scores = []
    for i, d in enumerate(docs):
        s = 0.0
        for t, w in idf.items():
            tf = d.get(t)
            if tf:
                s += w * tf * (k1 + 1) / (tf + k1 * (1 - b + b * lens[i] / avgdl))
        if s > 0:
            scores.append((s, i))
    scores.sort(reverse=True)
    return [Candidate(code=items[i][0], title=items[i][1], score=round(s, 3), reviewed=items[i][2]) for s, i in scores[:k]]


def get_heading(code: str) -> dict | None:
    """Reviewed heading (with flags), else the plain HS 2022 subheading (reviewed=False), else None (invalid code)."""
    r = _reviewed().get(code)
    if r:
        return {**r, "reviewed": True}
    for sh in load_hs()["subheadings"]:
        if sh["code"] == code:
            return {"code": code, "title": sh["title"], "keywords": [], "flags": {}, "reviewed": False}
    return None
