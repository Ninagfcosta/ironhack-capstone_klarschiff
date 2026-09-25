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


UPCOMING_DAYS = 180  # rules that start within this window are shown as "upcoming" (no documents yet)


def applicable_measures(hs_code: str, flags: dict, s: Shipment, today: date | None = None) -> list[MeasureHit]:
    today = today or date.today()
    dest, origin = region(s.destination), (s.origin or "").upper()
    digits = hs_code.replace(".", "")
    hits = []
    for m in load_measures()["measures"]:
        if m.get("direction") == "export_from_eu":
            if region(origin) != "EU" or dest == "EU":
                continue
        elif "*" not in m.get("applies_to_destination", []) and dest not in m.get("applies_to_destination", []):
            continue
        if m.get("applies_to_origin") and origin not in m["applies_to_origin"]:
            continue
        start = date.fromisoformat(m["effective_from"])
        upcoming = start > today
        if upcoming and (start - today).days > UPCOMING_DAYS:
            continue
        by_flag = m.get("flag") and flags.get(m["flag"])
        by_code = any(digits.startswith(p) for p in m.get("hs_prefixes", [])) \
            and not any(digits.startswith(p) for p in m.get("exclude_prefixes", []))
        if m.get("applies_to_origin") and not m.get("hs_prefixes") and not m.get("flag"):
            by_code = True  # origin-based measures apply to all goods from that origin
        if not (by_flag or by_code):
            continue
        age = (today - date.fromisoformat(m["last_verified"])).days
        hits.append(MeasureHit(id=m["id"], name=m["name"], effect=m["effect"], legal_ref=m["legal_ref"],
                               source_url=m["source_url"], last_verified=m["last_verified"],
                               stale=age > m.get("review_every_days", 90), volatility=m.get("volatility", "low"),
                               upcoming=upcoming, effective_from=m["effective_from"]))
    return hits


def required_documents(measures: list[MeasureHit], provided: list[str], stated_missing: list[str]) -> list[RequiredDocument]:
    by_id = {m["id"]: m for m in load_measures()["measures"]}
    docs = [RequiredDocument(name=n, reason=r, legal_ref=l) for n, r, l in BASE_DOCS]
    for hit in measures:
        if hit.upcoming:
            continue  # not in force yet: shown as a warning, no documents required
        for d in by_id[hit.id].get("documents", []):
            if not any(x.name == d["name"] for x in docs):
                docs.append(RequiredDocument(name=d["name"], reason=hit.name, legal_ref=hit.legal_ref, mandatory=d["mandatory"]))
    for d in docs:
        if d.name in stated_missing:
            d.status = "missing"
        elif d.name in provided:
            d.status = "provided"
    return docs


TRADE_IDS = ("EU_CBAM", "EU_STEEL_TRQ_2026", "EU_TRADE_DEFENCE", "US_SECTION_232")


def category(flags: dict, measures: list[MeasureHit]) -> tuple[int, list[str]]:
    """1 = standard goods, 2 = CE-marked product, 3 = additional trade or control measures (highest risk)."""
    by_id = {m["id"]: m for m in load_measures()["measures"]}
    active = [m for m in measures if not m.upcoming]
    reasons = []
    cat = 1
    if flags.get("cpr_hen"):
        cat = 2
        reasons.append(f"Construction product under a harmonised standard ({flags['cpr_hen']}): CE marking + DoP/DoPC.")
    ce = [m for m in active if by_id.get(m.id, {}).get("ce")]
    if ce:
        cat = 2
        reasons.append("CE-marked product (" + ", ".join(m.id for m in ce) + "): EU Declaration of Conformity + CE marking.")
    trade = [m for m in active if m.id in TRADE_IDS]
    if trade:
        cat = 3
        reasons.append("Additional trade measures apply: " + ", ".join(m.id for m in trade) + ".")
    control = [m for m in active if by_id.get(m.id, {}).get("control")]
    if control:
        cat = 3
        reasons.append("Special controls apply: " + ", ".join(m.id for m in control) + ".")
    for m in measures:
        if m.upcoming:
            reasons.append(f"Upcoming rule: {m.id} applies from {m.effective_from}.")
    if flags.get("national_approval"):
        reasons.append(flags["national_approval"])
    if cat == 1:
        reasons.append("No product-specific marking or trade measure found in the rule base: standard documents.")
    return cat, reasons
