"""Step 1 - Intake: turn what the user gives us (free text, CSV lines, a PDF, an e-invoice) into a Shipment.

Round 2 scope: free text + structured lines + text PDFs. Structured e-invoices (XRechnung / ZUGFeRD,
mandatory to receive in Germany since 1 Jan 2025) are read as XML when provided.
"""
from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET

from .models import Line

# Canonical document names the rules engine uses, with the words people write on invoices.
DOC_PATTERNS = {
    "Commercial invoice": [r"\binvoice\b", r"\brechnung\b"],
    "Packing list": [r"packing list", r"lieferschein", r"packliste"],
    "Declaration of Performance (DoP / DoPC)": [r"\bdopc?\b", r"declaration of performance", r"leistungserkl"],
    "CE marking evidence (label or photo)": [r"\bce[- ]mark", r"\bce label", r"ce-kennzeichnung"],
    "Mill certificate showing the country of melt and pour": [r"mill cert", r"melt and pour", r"werkszeugnis", r"inspection certificate 3\.1"],
    "Safety Data Sheet (SDS, in German for the German market)": [r"\bsds\b", r"safety data sheet", r"sicherheitsdatenblatt"],
    "Timber due-diligence statement / supplier evidence": [r"due diligence", r"\beudr\b", r"\beutr\b", r"flegt"],
    "A.TR movement certificate (or EUR.1 for steel products) to claim preferential treatment": [r"\ba\.?tr\b", r"\beur\.?1\b"],
    "Authorised CBAM declarant number (if > 50 t of CBAM goods per year)": [r"cbam (declarant|authori[sz])", r"cbam number", r"cbam account"],
    "Embedded-emissions data from the producer/installation": [r"emission(s)? data", r"embedded emissions"],
    "Country of melt and pour / smelt and cast declaration": [r"melt and pour", r"smelt and cast"],
}
NEGATIVE = r"(missing|not (included|attached|provided|available)|without|no\b|absent|fehlt|ohne)"
POSITIVE = r"(attached|included|enclosed|provided|available|with|beiliegend|vorhanden|anbei)"


def detect_documents(text: str) -> tuple[list[str], list[str]]:
    """Find documents the text says are present or missing.

    Returns (provided, stated_missing). A document mentioned without a clear word is treated as provided
    only if it is the invoice or packing list itself (the text usually IS the invoice).
    """
    t = text.lower()
    provided, missing = [], []
    for name, pats in DOC_PATTERNS.items():
        for p in pats:
            for m in re.finditer(p, t):
                # look only inside the same sentence/clause ("DoP missing. CE label attached." = two facts)
                window_before = re.split(r"[.;:\n,]", t[max(0, m.start() - 40): m.start()])[-1]
                window_after = re.split(r"[.;:\n,]", t[m.end(): m.end() + 40])[0]
                if re.search(NEGATIVE, window_before[-25:]) or re.search(r"^\W*" + NEGATIVE, window_after) or re.search(r"\b(is|are)\s+" + NEGATIVE, window_after):
                    missing.append(name)
                elif re.search(POSITIVE, window_before[-15:] + " " + window_after[:25]):
                    provided.append(name)
                elif name in ("Commercial invoice", "Packing list"):
                    provided.append(name)
    missing = list(dict.fromkeys(missing))
    provided = [d for d in dict.fromkeys(provided) if d not in missing]
    return provided, missing


QTY = re.compile(r"(\d[\d.,]*)\s*(t|tons?|tonnes?|mt|kg|bags?|m3|m²|m2|pcs|pieces|units|pallets?)\b", re.I)


def extract_tonnes(text: str) -> float | None:
    """Best-effort weight in tonnes from free text (e.g. '500 t', '24,000 kg', '500 bags of 25 kg')."""
    t = text.lower()
    bags = re.search(r"(\d[\d.,]*)\s*bags?\s*(?:of|x|à)?\s*(\d+)\s*kg", t)
    if bags:
        return _num(bags.group(1)) * _num(bags.group(2)) / 1000
    for m in QTY.finditer(t):
        n, u = _num(m.group(1)), m.group(2).lower()
        if u in ("t", "ton", "tons", "tonne", "tonnes", "mt"):
            return n
        if u == "kg":
            return n / 1000
    return None


def _num(s: str) -> float:
    s = s.strip()
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", s):  # 24,000 or 24.000
        return float(re.sub(r"[.,]", "", s))
    return float(s.replace(",", "."))


def lines_from_csv(text: str) -> list[Line]:
    """CSV with columns: description, quantity, unit, gross_weight_kg, value_eur (extra columns ignored)."""
    rows = csv.DictReader(io.StringIO(text))
    out = []
    for r in rows:
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        out.append(Line(
            description=r.get("description", ""),
            quantity=_safe(r.get("quantity")),
            unit=r.get("unit") or None,
            gross_weight_kg=_safe(r.get("gross_weight_kg")),
            value_eur=_safe(r.get("value_eur")),
        ))
    return out


def _safe(v):
    try:
        return _num(v) if v not in (None, "") else None
    except ValueError:
        return None


def text_from_pdf(file_bytes: bytes) -> str:
    """Text PDFs only. Scanned images need OCR (planned for the pilot) - we say so instead of guessing."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    if len(text.strip()) < 20:
        raise ValueError("This PDF has no readable text (probably a scan). OCR is planned for the pilot; please type the description.")
    return text


def lines_from_einvoice(xml_bytes: bytes) -> list[Line]:
    """Read invoice lines from an EN 16931 e-invoice (UBL/XRechnung or CII/ZUGFeRD). Structured data, no OCR."""
    root = ET.fromstring(xml_bytes)
    lines = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("InvoiceLine", "IncludedSupplyChainTradeLineItem"):
            name = qty = amount = None
            unit = None
            for c in el.iter():
                ct = c.tag.split("}")[-1]
                if ct == "Name" and name is None:
                    name = (c.text or "").strip()
                elif ct in ("InvoicedQuantity", "BilledQuantity"):
                    qty = _safe(c.text)
                    unit = c.attrib.get("unitCode")
                elif ct in ("LineExtensionAmount", "LineTotalAmount"):
                    amount = _safe(c.text)
            lines.append(Line(description=name or "", quantity=qty, unit=unit, value_eur=amount))
    return lines
