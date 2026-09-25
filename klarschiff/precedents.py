"""Rulings library: official classification decisions the team has looked up, used as evidence.

Sources (free, official):
- EU Binding Tariff Information (EBTI): https://ec.europa.eu/taxation_customs/dds2/ebti/ebti_consultation.jsp?Lang=en
- US CBP rulings (CROSS): https://rulings.cbp.gov/
A BTI is legally binding only for its holder, and it expires; for everyone else it is a strong hint.

How it works: a reviewer copies the reference, the code and the goods description of a relevant ruling into
the library (CSV import in the app). The agent then finds similar rulings with the same keyword search as the
RAG step, shows them to the reviewer and gives them to the model as context. No ruling is invented: the library
only contains what a person added.

CSV columns: reference, source, code, description, issued, valid_until, url
Storage: <DATA_DIR>/precedents.json (not in Git).
"""
from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter
from datetime import date

from . import config
from .retrieval import tokenize

FIELDS = ["reference", "source", "code", "description", "issued", "valid_until", "url"]


def _path():
    return config.DATA_DIR / "precedents.json"


def load() -> list[dict]:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def import_csv(text: str) -> dict:
    rows = []
    for r in csv.DictReader(io.StringIO(text.lstrip("﻿"))):
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if r.get("reference") and r.get("code") and r.get("description"):
            rows.append({f: r.get(f, "") for f in FIELDS})
    existing = {p["reference"]: p for p in load()}
    for r in rows:
        existing[r["reference"]] = r
    _path().write_text(json.dumps(list(existing.values()), indent=1, ensure_ascii=False), encoding="utf-8")
    return {"imported": len(rows), "total": len(existing)}


def search(description: str, k: int = 3, today: date | None = None) -> list[dict]:
    """Most similar rulings (BM25 over their goods descriptions). Expired BTIs are marked, not hidden."""
    items = load()
    if not items:
        return []
    today = today or date.today()
    docs = [Counter(tokenize(p["description"])) for p in items]
    df = Counter()
    for d in docs:
        df.update(d.keys())
    n, avg = len(docs), sum(sum(d.values()) for d in docs) / len(docs)
    q = set(tokenize(description))
    out = []
    for p, d in zip(items, docs):
        s = 0.0
        L = sum(d.values())
        for t in q:
            tf = d.get(t)
            if tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * L / avg))
        if s > 0:
            valid = not p.get("valid_until") or p["valid_until"] >= today.isoformat()
            out.append({**p, "score": round(s, 2), "valid": valid})
    return sorted(out, key=lambda x: -x["score"])[:k]
