"""Learning loop: every correction by a person becomes a new test case (and, if approved, a master-list entry).

Why (pilot need): the agent should get better every week without training a model. When a reviewer corrects a code,
we keep the case in evaluation/dataset_learned.jsonl, the same format as the other test sets. The next evaluation run
(`python evaluation/run_eval.py --local --dataset learned`) checks that the agent now gets it right.
In LangSmith the same file becomes the dataset 'klarschiff-eval-learned' (run with --langsmith --dataset learned).
Only goods data is stored: no names, no addresses.
"""
from __future__ import annotations

import json
from datetime import date

from .config import ROOT

DATASET = ROOT / "evaluation" / "dataset_learned.jsonl"


def load() -> list[dict]:
    if not DATASET.exists():
        return []
    return [json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]


def record_correction(shipment, suggested_hs: str, final_hs: str, comment: str = "", today: date | None = None) -> dict | None:
    """Add a corrected case once (same description + same final code = no duplicate). Returns the case or None."""
    if not final_hs or final_hs == suggested_hs:
        return None
    cases = load()
    for c in cases:
        if c["inputs"]["description"] == shipment.description and final_hs in c["reference"]["accepted_hs"]:
            return None
    case = {"id": f"LC{len(cases) + 1:03d}",
            "inputs": {"shipment_id": f"LC{len(cases) + 1:03d}", "description": shipment.description,
                       "origin": shipment.origin, "destination": shipment.destination,
                       "invoice_lines": [], "packing_lines": []},
            "reference": {"accepted_hs": [final_hs], "category": None, "manual_review": True, "missing": []},
            "meta": {"note": f"Corrected by a reviewer on {(today or date.today()).isoformat()}: "
                             f"agent said {suggested_hs}. {comment}".strip(), "tags": ["learned"]}}
    with DATASET.open("a", encoding="utf-8") as f:
        f.write(json.dumps(case, ensure_ascii=False) + "\n")
    return case
