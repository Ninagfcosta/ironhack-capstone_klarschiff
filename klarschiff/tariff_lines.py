"""National tariff lines under the 6-digit HS code: EU CN (8 digits) and US HTS (8/10 digits).

The HS is worldwide only up to 6 digits. Customs declarations need more:
- EU: Combined Nomenclature (CN, 8 digits), then TARIC (10 digits) for measures.
- US: Harmonized Tariff Schedule (HTS, 8 digits for the duty rate, 10 for statistics).

Free official sources (no paid service):
- CN 2026: Eurostat / Publications Office, SKOS/RDF file (EU reuse notice). Download once with
  `python scripts/download_official_data.py` -> klarschiff/knowledge/cn2026.json
- US HTS: USITC REST search (the same free source the Monitor uses). Looked up per code and cached in
  data/hts_cache.json. Duty rates shown are informative: always check the live HTS for the entry date.

The agent suggests the most likely line with a simple word match and shows all options; a person confirms.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from . import config

CN_FILE = config.KNOWLEDGE_DIR / "cn2026.json"
HTS_URL = "https://hts.usitc.gov/reststop/search"


@lru_cache(maxsize=1)
def load_cn() -> dict:
    if not CN_FILE.exists():
        return {"_meta": {}, "lines": []}
    return json.loads(CN_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _cn_by_hs6() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for ln in load_cn()["lines"]:
        out.setdefault(ln["code"][:6], []).append(ln)
    return out


def cn_available() -> bool:
    return bool(load_cn()["lines"])


def eu_lines(hs6: str) -> list[dict]:
    digits = re.sub(r"\D", "", hs6)[:6]
    return [{"code": f"{l['code'][:4]}.{l['code'][4:6]}.{l['code'][6:8]}", "title": l.get("title_en", ""),
             "title_de": l.get("title_de", "")} for l in _cn_by_hs6().get(digits, [])]


# ---------------------------------------------------------------- US HTS (free USITC API, cached)
def _cache_path():
    return config.DATA_DIR / "hts_cache.json"


def _load_cache() -> dict:
    try:
        return json.loads(_cache_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def us_lines(hs6: str, live: bool | None = None) -> list[dict]:
    digits = re.sub(r"\D", "", hs6)[:6]
    cache = _load_cache()
    if digits in cache:
        return cache[digits]
    if not (config.LIVE_TARIFF if live is None else live):
        return []
    try:
        import requests
        r = requests.get(HTS_URL, params={"keyword": digits}, timeout=8,
                         headers={"User-Agent": "KlarSchiff/2.3 (tariff lines; decision support)"})
        r.raise_for_status()
        rows = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
    except Exception:
        return []  # offline or blocked: the agent still works with 6 digits and the live link
    lines = []
    for row in rows:
        code = str(row.get("htsno", ""))
        if code.replace(".", "").startswith(digits) and len(code.replace(".", "")) >= 8:
            lines.append({"code": code, "title": re.sub(r"<[^>]+>", "", str(row.get("description", ""))).strip(),
                          "rate": str(row.get("general", "") or "")})
    cache[digits] = lines
    try:
        _cache_path().write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
    return lines


# ---------------------------------------------------------------- pick the most likely line
def _words(text: str) -> set[str]:
    stop = {"of", "the", "and", "or", "other", "for", "with", "not", "whether", "than", "n", "e", "c", "nesoi"}
    return {w for w in re.findall(r"[a-zäöüß]+", (text or "").lower()) if len(w) > 2 and w not in stop}


def suggest(description: str, lines: list[dict]) -> tuple[str, float]:
    """Return (code, share of matching words). One line only -> that line. No clear winner -> first 'other' line."""
    if not lines:
        return "", 0.0
    if len(lines) == 1:
        return lines[0]["code"], 1.0
    q = _words(description)
    scored = sorted(((len(q & _words(l["title"] + " " + l.get("title_de", ""))), i, l) for i, l in enumerate(lines)),
                    key=lambda x: (-x[0], x[1]))
    best, second = scored[0][0], scored[1][0]
    if best == 0 or best == second:
        return "", 0.0  # no clear winner: a person chooses
    return scored[0][2]["code"], round(best / max(1, len(q)), 2)


def national_lines(hs_code: str, destination_region: str, description: str) -> dict:
    """Lines for the destination: EU -> CN 2026, US -> HTS. Returns {} when no data is available."""
    if destination_region == "EU":
        lines, system = eu_lines(hs_code), "CN 2026 (EU, 8 digits)"
    elif destination_region == "US":
        lines, system = us_lines(hs_code), "HTS (US)"
    else:
        return {}
    if not lines:
        return {}
    code, share = suggest(description, lines)
    return {"system": system, "suggested": code, "match": share, "lines": lines[:25]}
