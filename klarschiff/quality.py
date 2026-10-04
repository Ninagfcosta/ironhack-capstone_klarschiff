"""Quality control in the pilot: weekly sample for a second look, and a simple dashboard summary.

Why (pilot need): the broker stays responsible, so a person re-checks a random 5-10% of the approved
decisions every week, and management sees a few numbers instead of guessing.
"""
from __future__ import annotations

import csv
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import report, review_queue


def decisions(days: int | None = None) -> list[dict]:
    if not report.LOG.exists():
        return []
    rows = list(csv.DictReader(report.LOG.open(encoding="utf-8")))
    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        rows = [r for r in rows if datetime.fromisoformat(r["timestamp"]) >= since]
    return rows


def weekly_sample(share: float = 0.1, seed: int | None = None) -> list[dict]:
    """Random share (default 10%, at least 1) of last week's approved decisions, for a second person to check."""
    rows = [r for r in decisions(days=7) if r["decision"] == "approved"]
    if not rows:
        return []
    k = max(1, round(len(rows) * share))
    return random.Random(seed).sample(rows, k)


def summary() -> dict:
    rows = decisions()
    q = review_queue.stats()
    reasons = Counter()
    for t in review_queue.load():
        for r in t.get("reasons", []):
            reasons[r.split(":")[0].split("(")[0].strip()[:60]] += 1
    by_decision = Counter(r["decision"] for r in rows)
    return {"decisions": len(rows), "by_decision": dict(by_decision), "override_rate": report.override_rate()["override_rate"],
            "queue": q, "top_reasons": reasons.most_common(6)}
