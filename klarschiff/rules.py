"""Rules engine: category, required documents, applicable trade measures and review triggers.

Legal requirements come from versioned rule files, not from the LLM. The LLM suggests the code;
these rules decide what that code means for documents and risk. This keeps the legal part checkable.
"""
from __future__ import annotations

import json
from datetime import date
from functools import lru_cache

from . import config
from .config import KNOWLEDGE_DIR
from .models import MeasureHit, RequiredDocument, Shipment

BASE_DOCS = [
    ("Commercial invoice", "Needed for every customs declaration (value, parties, goods).", "Union Customs Code, Reg. (EU) 952/2013"),
    ("Packing list", "Needed to check quantities, weights and packages against the invoice.", "Carrier / broker requirement"),
]


@lru_cache(maxsize=1)
def load_measures() -> dict:
    return json.loads((KNOWLEDGE_DIR / "trade_measures.json").read_text(encoding="utf-8"))


def region(country: str) -> str:
    c = (country or "").upper()
    return "EU" if c in config.EU_COUNTRIES else c


def applicable_measures(hs_code: str, flags: dict, s: Shipment, today: date | None = None) -> list[MeasureHit]:
    today = today or date.today()
    dest, origin = region(s.destination), (s.origin or "").upper()
    digits = hs_code.replace(".", "")
    hits = []
    for m in load_measures()["measures"]:
        if dest not in m.get("applies_to_destination", []):
            continue
        if m.get("applies_to_origin") and origin not in m["applies_to_origin"]:
            continue
        if date.fromisoformat(m["effective_from"]) > today:
            continue
        by_flag = m.get("flag") and flags.get(m["flag"])
        by_code = any(digits.startswith(p) for p in m.get("hs_prefixes", []))
        if m.get("applies_to_origin") and not m.get("hs_prefixes") and not m.get("flag"):
            by_code = True  # origin-based measures apply to all goods from that origin
        if not (by_flag or by_code):
            continue
        age = (today - date.fromisoformat(m["last_verified"])).days
        hits.append(MeasureHit(id=m["id"], name=m["name"], effect=m["effect"], legal_ref=m["legal_ref"],
                               source_url=m["source_url"], last_verified=m["last_verified"],
                               stale=age > m.get("review_every_days", 90), volatility=m.get("volatility", "low")))
    return hits


def required_documents(measures: list[MeasureHit], provided: list[str], stated_missing: list[str]) -> list[RequiredDocument]:
    by_id = {m["id"]: m for m in load_measures()["measures"]}
    docs = [RequiredDocument(name=n, reason=r, legal_ref=l) for n, r, l in BASE_DOCS]
    for hit in measures:
        for d in by_id[hit.id].get("documents", []):
            if not any(x.name == d["name"] for x in docs):
                docs.append(RequiredDocument(name=d["name"], reason=hit.name, legal_ref=hit.legal_ref, mandatory=d["mandatory"]))
    for d in docs:
        if d.name in stated_missing:
            d.status = "missing"
        elif d.name in provided:
            d.status = "provided"
    return docs


def category(flags: dict, measures: list[MeasureHit]) -> tuple[int, list[str]]:
    """1 = standard goods, 2 = CE-marked construction product, 3 = additional trade measures (highest risk)."""
    reasons = []
    cat = 1
    if flags.get("cpr_hen"):
        cat = 2
        reasons.append(f"Construction product under a harmonised standard ({flags['cpr_hen']}): CE marking + DoP/DoPC.")
    trade = [m for m in measures if m.id in ("EU_CBAM", "EU_STEEL_TRQ_2026", "EU_TRADE_DEFENCE", "US_SECTION_232")]
    if trade:
        cat = 3
        reasons.append("Additional trade measures apply: " + ", ".join(m.id for m in trade) + ".")
    if flags.get("national_approval"):
        reasons.append(flags["national_approval"])
    if cat == 1:
        reasons.append("No product-specific marking or trade measure found in the rule base: standard documents.")
    return cat, reasons
