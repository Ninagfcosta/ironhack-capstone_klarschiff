"""Read scanned invoices and photos with a vision-capable model (Intake step, v2.2).

Why a vision model instead of classic OCR: it reads crooked phone photos, stamps and mixed languages,
and returns structured lines directly. It also says when a page is NOT readable, so we never guess.

Privacy: the whole image goes to the model provider. Crop or blur names, signatures and addresses before
uploading, or use an EU provider (see llm.py and compliance/gdpr_documentation.md).
"""
from __future__ import annotations

import io

from langsmith import traceable

from . import config
from .models import Line

VISION_PROMPT = """You read shipping documents (commercial invoices, packing lists, delivery notes) for a customs check.
Transcribe ONLY what you can read. Never guess missing characters or numbers.
Reply with JSON only:
{"document_type": "invoice | packing_list | delivery_note | certificate | other",
 "language": "ISO 639-1 code of the document language",
 "legible": true or false (false if important parts cannot be read),
 "unreadable_parts": ["short description of what could not be read"],
 "text": "the goods description exactly as written",
 "lines": [{"description": "...", "quantity": number or null, "unit": "...", "gross_weight_kg": number or null, "value_eur": number or null}],
 "documents_mentioned": ["e.g. Declaration of Performance attached"]}
Do not include names of people, signatures, phone numbers or e-mail addresses in the output."""


class VisionResult(dict):
    @property
    def lines(self) -> list[Line]:
        out = []
        for l in self.get("lines") or []:
            try:
                out.append(Line(**{k: l.get(k) for k in ("description", "quantity", "unit", "gross_weight_kg", "value_eur")}))
            except Exception:
                continue
        return out


@traceable(name="read_document_vision", run_type="chain")
def read_image(image_bytes: bytes, mime: str = "image/png") -> VisionResult:
    from . import llm

    if not config.llm_available():
        raise RuntimeError("Reading scans and photos needs the AI model (no API key found). Please type the description.")
    data = llm.chat_json(VISION_PROMPT, [{"type": "text", "text": "Read this document."}, llm.image_part(image_bytes, mime)],
                         model=config.VISION_MODEL)
    data.setdefault("legible", False)
    data.setdefault("text", "")
    return VisionResult(data)


def pdf_pages_as_png(pdf_bytes: bytes, max_pages: int = 3, resolution: int = 150) -> list[bytes]:
    """Render the first pages of a scanned PDF as PNG images (pdfplumber / pypdfium2, no extra install)."""
    import pdfplumber

    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages[:max_pages]:
            img = page.to_image(resolution=resolution).original
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            pages.append(buf.getvalue())
    return pages


def read_scanned_pdf(pdf_bytes: bytes) -> VisionResult:
    merged = VisionResult({"legible": True, "text": "", "lines": [], "documents_mentioned": [], "unreadable_parts": []})
    for png in pdf_pages_as_png(pdf_bytes):
        r = read_image(png, "image/png")
        merged["legible"] = merged["legible"] and bool(r.get("legible"))
        merged["text"] = (merged["text"] + "\n" + (r.get("text") or "")).strip()
        merged["lines"] += r.get("lines") or []
        merged["documents_mentioned"] += r.get("documents_mentioned") or []
        merged["unreadable_parts"] += r.get("unreadable_parts") or []
        merged.setdefault("language", r.get("language"))
        merged.setdefault("document_type", r.get("document_type"))
    return merged
