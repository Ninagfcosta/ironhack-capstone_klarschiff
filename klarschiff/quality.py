"""Quality control in the pilot: weekly sample for a second look, and a simple dashboard summary.

Why (pilot need): the broker stays responsible, so a person re-checks a random 5-10% of the approved
decisions every week, and management sees a few numbers instead of guessing.
"""
from __future__ import annotations

import csv
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import learning, report, review_queue
from .config import DATA_DIR

TIMES = DATA_DIR / "review_times.csv"


def log_review_time(seconds: float, decision: str) -> None:
    """Real review time per shipment (from result on screen to saved decision): turns the illustrative ROI into a measured one."""
    new = not TIMES.exists()
    with TIMES.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "seconds", "decision"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), round(seconds), decision])


def median_review_minutes():
    if not TIMES.exists():
        return None
    vals = sorted(float(r["seconds"]) for r in csv.DictReader(TIMES.open(encoding="utf-8")))
    if not vals:
        return None
    mid = len(vals) // 2
    med = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2
    return round(med / 60, 1)


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
            "queue": q, "top_reasons": reasons.most_common(6),
            "learned_cases": len(learning.load()), "median_review_minutes": median_review_minutes()}
