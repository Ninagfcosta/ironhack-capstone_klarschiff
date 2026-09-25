"""Blind test for the pilot (Sprint 2): real, anonymised shipments labelled by the customs broker.

Why: our 20 test cases were written by the same person who built the knowledge base, and the v2.1 fixes were
tuned on them, so their scores are optimistic. The blind test uses shipments the agent has never seen,
with the correct answers decided by a licensed broker BEFORE the agent runs.

How:
  1. The broker fills evaluation/blind_test_template.csv (one row per real shipment, anonymised:
     no names, addresses or signatures). Save it as e.g. data/blind_test_2026-11.csv (data/ is not in Git).
  2. python evaluation/blind_test.py data/blind_test_2026-11.csv
  3. Read the summary it prints and evaluation/results/blind_<file>.csv, then review every miss with the broker.

Go / no-go (strategic_plan.md): no risky shipment passes without a person; >= 90% of codes accepted at 6 digits.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

from klarschiff import agent, config  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402
from evaluators import ALL  # noqa: E402

YES = {"yes", "y", "true", "1", "ja", "sim"}


def split(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(";") if x.strip()]


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if (r.get("description") or "").strip()]


def run(path: Path, out_dir: Path | None = None) -> dict:
    rows, out = load(path), []
    for r in rows:
        s = Shipment(shipment_id=r["shipment_id"], description=r["description"], origin=r.get("origin", ""),
                     destination=r.get("destination") or "DE", documents_provided=split(r.get("documents_provided", "")),
                     documents_list_complete=True)
        res = json.loads(agent.run(s).model_dump_json())
        ref = {"accepted_hs": split(r.get("broker_hs", "")), "manual_review": (r.get("broker_needs_review", "").lower() in YES),
               "missing": split(r.get("broker_missing_docs", "")), "category": None}
        scores = {e.__name__: e(res, ref)["score"] for e in ALL}
        out.append({"shipment_id": r["shipment_id"], "broker_hs": r.get("broker_hs", ""), "agent_hs": res["hs_code"],
                    "agent_confidence": res["confidence"], "broker_review": ref["manual_review"], "agent_review": res["manual_review"],
                    "false_all_clear": ref["manual_review"] and not res["manual_review"],
                    "agent_reasons": " | ".join(res["review_reasons"]), **scores})
    n = len(out)
    hs = [o["hs_code_correct"] for o in out if o["hs_code_correct"] is not None]
    summary = {"file": path.name, "run_at": datetime.now().isoformat(timespec="seconds"), "model": config.MODEL,
               "llm": config.llm_available(), "shipments": n,
               "hs_exact_6digit": round(sum(1 for x in hs if x == 1.0) / len(hs), 3) if hs else None,
               "false_all_clears": sum(1 for o in out if o["false_all_clear"]),
               "unnecessary_reviews": sum(1 for o in out if o["agent_review"] and not o["broker_review"]),
               "go_no_go": None}
    summary["go_no_go"] = ("NO-GO: a risky shipment passed without a person" if summary["false_all_clears"]
                           else "GO criteria met on this sample" if (summary["hs_exact_6digit"] or 0) >= 0.9
                           else "REVIEW: codes accepted below 90%")
    dest = (out_dir or ROOT / "evaluation" / "results") / f"blind_{path.stem}.csv"
    dest.parent.mkdir(exist_ok=True)
    if out:
        with dest.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
    summary["details_file"] = str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else str(dest)
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python evaluation/blind_test.py <broker-labelled CSV>")
    print(json.dumps(run(Path(sys.argv[1])), indent=2, ensure_ascii=False))
