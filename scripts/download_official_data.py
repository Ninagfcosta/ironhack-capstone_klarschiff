"""Download free official tariff data once (run on your own computer, it needs internet):

    python scripts/download_official_data.py            # CN 2026 (EU, 8 digits) + US HTS lines for known codes
    python scripts/download_official_data.py --cn-file ~/Downloads/ESTAT-CN2026.rdf   # if you downloaded it by hand

Sources (no account, no payment):
- CN 2026: Eurostat / Publications Office of the EU, SKOS RDF distribution of the dataset "Combined Nomenclature,
  2026 (CN 2026)" on data.europa.eu (European Commission reuse notice: reuse allowed with acknowledgement).
- US HTS: USITC REST search, the same free API the Monitor uses.
Result: klarschiff/knowledge/cn2026.json and data/hts_cache.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CN_URL = ("https://op.europa.eu/o/opportal-service/euvoc-download-handler?cellarURI=http%3A%2F%2Fpublications.europa.eu"
          "%2Fresource%2Fcellar%2F79c210b8-c4a3-11f0-8da2-01aa75ed71a1.0001.02%2FDOC_1&fileName=ESTAT-CN2026.rdf")
SKOS = "http://www.w3.org/2004/02/skos/core#"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _clean_label(t: str) -> str:
    return re.sub(r"^[\s\-–—]+", "", (t or "").strip())


def parse_cn_skos(path: Path) -> list[dict]:
    """Every concept with an 8-digit notation -> {code, title_en, title_de}. Tolerant to the exact RDF layout."""
    lines = {}
    for _, el in ET.iterparse(path, events=("end",)):
        notes = [n.text or "" for n in el.findall(f"{{{SKOS}}}notation")]
        if not notes:
            continue
        labels = {}
        for lab in el.findall(f"{{{SKOS}}}prefLabel") + el.findall(f"{{{SKOS}}}altLabel"):
            lang = (lab.get(XML_LANG) or "").lower()[:2]
            if lang in ("en", "de") and lang not in labels:
                labels[lang] = _clean_label(lab.text)
        for n in notes:
            digits = re.sub(r"\D", "", n)
            if len(digits) == 8 and digits not in lines:
                lines[digits] = {"code": digits, "title_en": labels.get("en", ""), "title_de": labels.get("de", "")}
        el.clear()
    return sorted(lines.values(), key=lambda x: x["code"])


def save_cn(lines: list[dict], source: str) -> Path:
    out = ROOT / "klarschiff" / "knowledge" / "cn2026.json"
    meta = {"name": "Combined Nomenclature 2026 (CN, 8 digits)", "source": source,
            "licence": "European Commission reuse notice (reuse allowed, source must be acknowledged)",
            "downloaded": date.today().isoformat(), "count": len(lines),
            "note": "Labels are the short CN texts (without the parent lines). Legal text: Commission Implementing "
                    "Regulation on the CN for 2026, Official Journal of the EU. Check TARIC for the shipment date."}
    out.write_text(json.dumps({"_meta": meta, "lines": lines}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out


def download_cn(dest: Path) -> Path:
    import requests
    r = requests.get(CN_URL, timeout=120, headers={"User-Agent": "KlarSchiff/2.3 (official data download)"})
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def prefetch_hts() -> int:
    from klarschiff import master_list, retrieval, tariff_lines
    codes = {h["code"] for h in retrieval.load_kb()["headings"]} | {p.hs_code for p in master_list.load() if p.hs_code}
    n = 0
    for c in sorted(codes):
        if tariff_lines.us_lines(c, live=True):
            n += 1
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cn-file", help="use an RDF file you downloaded yourself")
    ap.add_argument("--skip-hts", action="store_true")
    a = ap.parse_args()
    raw = ROOT / "data" / "ESTAT-CN2026.rdf"
    raw.parent.mkdir(exist_ok=True)
    try:
        src = Path(a.cn_file).expanduser() if a.cn_file else download_cn(raw)
        lines = parse_cn_skos(src)
        print(f"CN 2026: {len(lines)} eight-digit lines -> {save_cn(lines, CN_URL if not a.cn_file else str(src))}")
        if not lines:
            print("No 8-digit codes found: the file layout may have changed. Tell me and send the first lines of the file.")
    except Exception as e:  # never crash: the agent works with 6 digits too
        print(f"CN download/parse failed ({type(e).__name__}: {e}). The agent keeps working with 6-digit codes.")
    if not a.skip_hts:
        print(f"US HTS: lines cached for {prefetch_hts()} codes -> data/hts_cache.json")
