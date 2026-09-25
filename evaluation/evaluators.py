"""Evaluators: the same 5 business criteria as the Round 1 eval plan, now automated.

Each evaluator takes the agent output and the reference answer and returns {"key", "score", "comment"}.
They work in LangSmith (client.evaluate) and in the local runner.
"""
from __future__ import annotations


def hs_code_correct(outputs: dict, reference_outputs: dict) -> dict:
    """Criterion 1: the 6-digit code matches one of the accepted codes. Half point for the right 4-digit heading."""
    ok = reference_outputs.get("accepted_hs") or []
    if not ok:
        return {"key": "hs_code_correct", "score": None, "comment": "No single correct code (ambiguous case): not scored."}
    got = outputs.get("hs_code", "")
    if got in ok:
        return {"key": "hs_code_correct", "score": 1.0, "comment": f"{got} is correct."}
    if any(got[:4] == c[:4] for c in ok):
        return {"key": "hs_code_correct", "score": 0.5, "comment": f"Right heading, wrong subheading: {got} vs {ok}."}
    return {"key": "hs_code_correct", "score": 0.0, "comment": f"Wrong code: {got} vs {ok}."}


def missing_document_flagged(outputs: dict, reference_outputs: dict) -> dict:
    """Criterion 2: every document the reference says is missing is flagged as missing."""
    expected = reference_outputs.get("missing") or []
    got = outputs.get("missing_documents") or []
    if not expected:
        return {"key": "missing_document_flagged", "score": None, "comment": "No missing document in this case."}
    hit = [d for d in expected if d in got]
    return {"key": "missing_document_flagged", "score": len(hit) / len(expected),
            "comment": f"Flagged {len(hit)}/{len(expected)}: {expected}"}


def source_shown(outputs: dict, reference_outputs: dict) -> dict:
    """Criterion 3: the answer is traceable: a reason, evidence words or a knowledge-base title, and live tariff links."""
    has_reason = len(outputs.get("reasoning", "")) > 30
    has_trace = bool(outputs.get("evidence")) or outputs.get("hs_title", "") not in ("", "Not in knowledge base", "Not a valid HS 2022 code")
    has_links = bool(outputs.get("links"))
    score = 1.0 if (has_reason and has_trace and has_links) else 0.0
    return {"key": "source_shown", "score": score, "comment": f"reason={has_reason} trace={has_trace} links={has_links}"}


def review_routing(outputs: dict, reference_outputs: dict) -> dict:
    """Criterion 4: cases that need a person go to a person. Also reports unnecessary reviews (lower priority)."""
    exp, got = reference_outputs.get("manual_review"), outputs.get("manual_review")
    if exp == got:
        return {"key": "review_routing", "score": 1.0, "comment": "Correct routing."}
    if exp and not got:
        return {"key": "review_routing", "score": 0.0, "comment": "FALSE ALL-CLEAR: needed a person but was passed."}
    return {"key": "review_routing", "score": 0.5, "comment": "Unnecessary review (safe, but costs time)."}


def no_false_all_clear(outputs: dict, reference_outputs: dict) -> dict:
    """Safety metric: the one error we cannot accept."""
    bad = reference_outputs.get("manual_review") and not outputs.get("manual_review")
    return {"key": "no_false_all_clear", "score": 0.0 if bad else 1.0, "comment": "FALSE ALL-CLEAR" if bad else "ok"}


def category_correct(outputs: dict, reference_outputs: dict) -> dict:
    exp = reference_outputs.get("category")
    if exp is None:
        return {"key": "category_correct", "score": None, "comment": "Not scored."}
    got = outputs.get("category")
    return {"key": "category_correct", "score": 1.0 if got == exp else 0.0, "comment": f"got {got}, expected {exp}"}


ALL = [hs_code_correct, missing_document_flagged, source_shown, review_routing, no_false_all_clear, category_correct]
