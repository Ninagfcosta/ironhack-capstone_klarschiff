"""Master list (Produktstamm): one product, many part numbers.

The problem (fictional client scenario, I&E LLC; a common pattern in trade): the master list is keyed by PART NUMBER.
Part numbers change (new revision, new supplier, new ERP), the description stays the same, and the lookup
by part number finds nothing, so the approved HS code and the approved German description are lost.
People classify again, and sometimes the SAME product gets a DIFFERENT code (an audit risk).

The fix:
- Every product gets a stable KlarSchiff ID (KS-00001). The approved HS code and German description belong
  to the PRODUCT, not to the part number.
- Part numbers are aliases of a product. A new part number is linked, not re-classified.
- Lookup order: 1) known part number, 2) same description (fingerprint), 3) similar description.
  Same description = reuse, a person confirms the link. Similar = a person decides (differences are shown).
- Importing an existing list finds CONFLICTS: the same description with different HS codes.

Storage: <DATA_DIR>/master_list.json (not in Git: it is client data).
"""
from __future__ import annotations

import csv
import io
import json
import re
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

from pydantic import BaseModel, Field

from . import config

STORE_NAME = "master_list.json"
SIMILAR = 0.80  # description similarity (0-1) from which we suggest a product

# part-number-like tokens: letters+digits with dashes or long digit runs (INS-100-A, PN12345-A, 740-613520-00)
_PN = re.compile(r"\b(?:p/?n|part\s*(?:no|number)|art(?:ikel)?[.\s-]*nr)\b[:.\s]*\S+|\b(?=[a-z0-9-]*\d)[a-z0-9]+(?:-[a-z0-9]+){1,}\b|\b\d{7,}\b", re.I)
_REV = re.compile(r"\brev(?:ision)?\.?\s*[a-z0-9]{1,3}\b", re.I)
_UNITS = {"millimeter": "mm", "millimetre": "mm", "centimeter": "cm", "centimetre": "cm", "kilogram": "kg", "kilo": "kg",
          "stück": "pcs", "stueck": "pcs", "pieces": "pcs", "piece": "pcs", "pc": "pcs"}
_STOP = {"the", "a", "an", "of", "for", "with", "and", "new", "assy", "assembly", "kit", "und", "für", "fuer", "mit"}


class Product(BaseModel):
    product_id: str
    description: str
    description_de: str = ""
    hs_code: str = ""
    part_numbers: list[str] = Field(default_factory=list)
    approved_by: str = ""
    approved_on: str = ""
    history: list[str] = Field(default_factory=list)


class Match(BaseModel):
    kind: str  # "part_number" | "same_description" | "similar" | "none"
    product: Product | None = None
    score: float = 0.0
    differences: list[str] = Field(default_factory=list)


def fingerprint(description: str) -> str:
    """Normalised description: no part numbers, no revision marks, unified units, lower case."""
    t = _REV.sub(" ", _PN.sub(" ", description.lower()))
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)
    words = re.findall(r"[a-zäöüß0-9]+(?:\.\d+)?", t)
    return " ".join(_UNITS.get(w, w) for w in words if w not in _STOP)


def _numbers(fp: str) -> set[str]:
    return {w for w in fp.split() if any(ch.isdigit() for ch in w)}


def _differences(a: str, b: str) -> list[str]:
    """What changed between two fingerprints: numbers (dimensions, ratings) and words (material, form)."""
    out = []
    na, nb = _numbers(a), _numbers(b)
    if na != nb:
        out.append(f"values differ: {', '.join(sorted(na - nb)) or '-'} → {', '.join(sorted(nb - na)) or '-'}")
    wa = {w for w in a.split() if not any(ch.isdigit() for ch in w)}
    wb = {w for w in b.split() if not any(ch.isdigit() for ch in w)}
    if wa != wb:
        out.append(f"words differ: {', '.join(sorted(wa - wb)) or '-'} → {', '.join(sorted(wb - wa)) or '-'}")
    return out


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, fingerprint(a), fingerprint(b)).ratio()


def describe_differences(old: str, new: str) -> list[str]:
    return _differences(fingerprint(old), fingerprint(new))


def normalise_pn(pn: str) -> str:
    return re.sub(r"[\s_]", "", (pn or "").upper())


# ---------------------------------------------------------------- storage
def store() -> Path:
    return config.DATA_DIR / STORE_NAME


def load(path: Path | None = None) -> list[Product]:
    path = path or store()
    if not path.exists():
        return []
    return [Product(**p) for p in json.loads(path.read_text(encoding="utf-8"))]


def save(products: list[Product], path: Path | None = None) -> None:
    path = path or store()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([p.model_dump() for p in products], indent=1, ensure_ascii=False), encoding="utf-8")


def _next_id(products: list[Product]) -> str:
    n = max((int(p.product_id.split("-")[1]) for p in products), default=0) + 1
    return f"KS-{n:05d}"


# ---------------------------------------------------------------- lookup
def lookup(part_number: str, description: str, products: list[Product] | None = None) -> Match:
    products = load() if products is None else products
    pn = normalise_pn(part_number)
    if pn:
        for p in products:
            if pn in p.part_numbers:
                return Match(kind="part_number", product=p, score=1.0)
    fp = fingerprint(description)
    if not fp:
        return Match(kind="none")
    best, best_s = None, 0.0
    for p in products:
        pfp = fingerprint(p.description)
        if pfp == fp:
            return Match(kind="same_description", product=p, score=1.0)
        s = SequenceMatcher(None, pfp, fp).ratio()
        if s > best_s:
            best, best_s = p, s
    if best and best_s >= SIMILAR:
        return Match(kind="similar", product=best, score=round(best_s, 2), differences=_differences(fingerprint(best.description), fp))
    return Match(kind="none", score=round(best_s, 2))


def approve(description: str, hs_code: str, part_number: str = "", description_de: str = "", approved_by: str = "",
            product_id: str = "", path: Path | None = None, today: date | None = None) -> Product:
    """A person approved a code: link the part number to the product (or create the product)."""
    today = today or date.today()
    products = load(path)
    pn = normalise_pn(part_number)
    target = next((p for p in products if p.product_id == product_id), None) if product_id else None
    if target is None:
        m = lookup(pn, description, products)
        target = m.product if m.kind in ("part_number", "same_description") else None
    if target is None:
        target = Product(product_id=_next_id(products), description=description, description_de=description_de,
                         hs_code=hs_code, approved_by=approved_by, approved_on=today.isoformat())
        target.history.append(f"{today}: created with HS {hs_code} by {approved_by or 'reviewer'}")
        products.append(target)
    else:
        if hs_code and hs_code != target.hs_code:
            target.history.append(f"{today}: HS changed {target.hs_code} → {hs_code} by {approved_by or 'reviewer'}")
            target.hs_code = hs_code
        if description_de and not target.description_de:
            target.description_de = description_de
    if pn and pn not in target.part_numbers:
        target.part_numbers.append(pn)
        target.history.append(f"{today}: part number {pn} linked")
    save(products, path)
    return target


# ---------------------------------------------------------------- import an existing list
def import_csv(text: str, path: Path | None = None, today: date | None = None, write: bool = True) -> dict:
    """Import the client's list (columns: part_number, description, description_de, hs_code).

    Rows with the same description are merged into ONE product with several part numbers.
    Conflicts (same description, different HS codes) are reported and NOT merged silently: a person decides.
    """
    today = today or date.today()
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    groups: dict[str, list[dict]] = {}
    for r in rows:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("description"):
            continue
        groups.setdefault(fingerprint(r["description"]), []).append(r)
    products, conflicts = [], []
    for fp, rs in groups.items():
        codes = sorted({r.get("hs_code", "") for r in rs if r.get("hs_code")})
        p = Product(product_id=f"KS-{len(products) + 1:05d}", description=rs[0]["description"],
                    description_de=next((r["description_de"] for r in rs if r.get("description_de")), ""),
                    hs_code=codes[0] if len(codes) == 1 else "",
                    part_numbers=list(dict.fromkeys(normalise_pn(r.get("part_number", "")) for r in rs if r.get("part_number"))),
                    approved_on=today.isoformat() if len(codes) == 1 else "")
        p.history.append(f"{today}: imported from {len(rs)} row(s)")
        if len(codes) > 1:
            conflicts.append({"product_id": p.product_id, "description": p.description, "hs_codes": codes,
                              "part_numbers": p.part_numbers})
            p.history.append(f"{today}: CONFLICT, codes {', '.join(codes)}: a person must decide")
        products.append(p)
    if write:
        save(products, path)
    return {"rows": len(rows), "products": len(products),
            "merged_part_numbers": sum(max(0, len(p.part_numbers) - 1) for p in products),
            "conflicts": conflicts, "without_hs": sum(1 for p in products if not p.hs_code)}


def to_csv(products: list[Product]) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["product_id", "hs_code", "description", "description_de", "part_numbers", "approved_by", "approved_on"])
    for p in products:
        w.writerow([p.product_id, p.hs_code, p.description, p.description_de, " | ".join(p.part_numbers), p.approved_by, p.approved_on])
    return out.getvalue()
