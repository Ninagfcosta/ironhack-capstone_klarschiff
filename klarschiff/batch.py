"""Batch check: many shipments (or a whole master list) in one run -> one report.

Input CSV columns (only `description` is required):
    shipment_id, description, origin, destination, part_number, documents_provided (separated by ;), intended_use
Run:
    python -m klarschiff.batch input.csv -o report.csv
The report has one row per shipment: code, national line, category, review yes/no and why, missing documents,
master-list match, tokens and estimated AI cost. The summary gives the totals a manager needs.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import time

from . import agent
from .models import Shipment

REPORT_FIELDS = ["shipment_id", "part_number", "description", "hs_code", "national_code", "category", "manual_review",
                 "review_reasons", "missing_documents", "master_list", "confidence", "mode", "tokens", "est_cost_usd"]


def _split(v: str) -> list[str]:
    return [x.strip() for x in (v or "").split(";") if x.strip()]


def run_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    out, t0 = [], time.time()
    for i, r in enumerate(rows, 1):
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not r.get("description"):
            continue
        s = Shipment(shipment_id=r.get("shipment_id") or f"row{i}", description=r["description"],
                     origin=(r.get("origin") or "").upper(), destination=(r.get("destination") or "DE").upper(),
                     part_number=r.get("part_number", ""), documents_provided=_split(r.get("documents_provided", "")),
                     intended_use=r.get("intended_use") or "other")
        res = agent.run(s)
        out.append({"shipment_id": s.shipment_id, "part_number": s.part_number, "description": s.description[:200],
                    "hs_code": res.hs_code, "national_code": (res.national or {}).get("suggested", ""),
                    "category": res.category, "manual_review": "yes" if res.manual_review else "no",
                    "review_reasons": " | ".join(res.review_reasons), "missing_documents": " | ".join(res.missing_documents),
                    "master_list": (res.master or {}).get("kind", ""), "confidence": res.confidence, "mode": res.mode,
                    "tokens": res.usage.get("prompt_tokens", 0) + res.usage.get("completion_tokens", 0),
                    "est_cost_usd": res.usage.get("est_cost_usd", 0)})
    n = len(out)
    summary = {
        "shipments": n,
        "to_review": sum(1 for o in out if o["manual_review"] == "yes"),
        "passed_checks": sum(1 for o in out if o["manual_review"] == "no"),
        "by_category": {c: sum(1 for o in out if o["category"] == c) for c in (1, 2, 3)},
        "master_list_hits": sum(1 for o in out if o["master_list"] in ("part_number", "same_description")),
        "with_missing_documents": sum(1 for o in out if any(not d.startswith("(not stated)")
                                                            for d in o["missing_documents"].split(" | ") if d)),
        "est_cost_usd_total": round(sum(o["est_cost_usd"] for o in out), 4),
        "est_cost_usd_per_line": round(sum(o["est_cost_usd"] for o in out) / n, 6) if n else 0,
        "seconds": round(time.time() - t0, 1),
    }
    return out, summary


def run_csv(text: str) -> tuple[list[dict], dict]:
    return run_rows(list(csv.DictReader(io.StringIO(text.lstrip("﻿")))))


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=REPORT_FIELDS)
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default="batch_report.csv")
    a = ap.parse_args()
    with open(a.input, encoding="utf-8-sig") as f:
        rows, summary = run_csv(f.read())
    with open(a.output, "w", encoding="utf-8", newline="") as f:
        f.write(to_csv(rows))
    print(json.dumps(summary, indent=2))
    print(f"Report: {a.output}")
