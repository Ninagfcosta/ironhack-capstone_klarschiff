"""Step 3 - Recommend: choose the HS code.

The LLM only chooses among real candidate headings found by retrieval (RAG), and must explain why.
If no API key is set (or the API fails), an offline fallback uses the best retrieval match and says so.
"""
from __future__ import annotations

import re

from langsmith import traceable

from . import config
from .models import Candidate, Classification, Shipment

SYSTEM_PROMPT = """You are KlarSchiff, a pre-shipment customs classification assistant for a construction-materials
importer/exporter. You help a human reviewer; you never make the final decision.

Rules:
1. Choose the 6-digit HS code (format 0000.00) for the goods described. Prefer one of the CANDIDATE headings
   from the knowledge base. Only propose a code outside the list if none fits; then say so in the reasoning
   and set confidence below 0.6.
2. Base the choice on material, processing state and function (General Interpretative Rules 1 and 6).
3. If the description is too vague to decide (e.g. material or form missing), set confidence below 0.6 and
   list the missing information. Never invent facts that are not in the description.
4. evidence = the exact words from the description that support your choice.
5. Reply with JSON only, with keys: hs_code, confidence, reasoning, evidence, alternatives, missing_information."""


def _user_prompt(s: Shipment, candidates: list[Candidate]) -> str:
    cand = "\n".join(f"- {c.code}: {c.title}" for c in candidates) or "- (no candidate found)"
    return (f"Shipment description:\n{s.description}\n\nOrigin: {s.origin or 'unknown'}  Destination: {s.destination}\n"
            f"Intended use: {s.intended_use}\n\nCANDIDATE headings (knowledge base):\n{cand}")


_CODE = re.compile(r"^\d{4}\.\d{2}$")


def _normalise_code(code: str) -> str:
    digits = re.sub(r"\D", "", code or "")
    return f"{digits[:4]}.{digits[4:6]}" if len(digits) >= 6 else code


@traceable(name="recommend_llm", run_type="chain")
def _call_llm(s: Shipment, candidates: list[Candidate]) -> Classification:
    from . import llm

    data = llm.chat_json(SYSTEM_PROMPT, _user_prompt(s, candidates))
    data["hs_code"] = _normalise_code(str(data.get("hs_code", "")))
    data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0))))
    data["reasoning"] = str(data.get("reasoning", ""))
    for k in ("evidence", "alternatives", "missing_information"):
        v = data.get(k) or []
        data[k] = [str(x) for x in v] if isinstance(v, list) else [str(v)]
    return Classification(**{k: data[k] for k in ("hs_code", "confidence", "reasoning", "evidence", "alternatives", "missing_information")})


def _offline(s: Shipment, candidates: list[Candidate]) -> Classification:
    if not candidates:
        return Classification(hs_code="0000.00", confidence=0.0,
                               reasoning="Offline mode: no heading in the knowledge base matches this description.",
                               missing_information=["Material, form and use of the goods"])
    top = candidates[0]
    second = candidates[1].score if len(candidates) > 1 else 0.0
    margin = (top.score - second) / top.score if top.score else 0
    conf = round(min(0.85, 0.45 + 0.5 * margin), 2)
    return Classification(hs_code=top.code, confidence=conf,
                          reasoning=f"Offline mode (no LLM): best keyword match in the knowledge base is {top.code} "
                                    f"'{top.title}'. Confidence is based on how clearly it beats the next match.",
                          alternatives=[c.code for c in candidates[1:3]])


def classify(s: Shipment, candidates: list[Candidate]) -> tuple[Classification, str]:
    """Returns (classification, mode). mode is 'llm' or 'offline'."""
    if config.llm_available():
        try:
            c = _call_llm(s, candidates)
            if not _CODE.match(c.hs_code):
                c.confidence = min(c.confidence, 0.4)
                c.reasoning += " [Format check failed: code is not a valid 6-digit HS code.]"
            return c, "llm"
        except Exception as e:  # network error, quota, bad JSON ... -> never crash the review
            off = _offline(s, candidates)
            off.reasoning = f"LLM unavailable ({type(e).__name__}); fell back to offline mode. " + off.reasoning
            off.confidence = min(off.confidence, 0.6)
            return off, "offline"
    return _offline(s, candidates), "offline"
