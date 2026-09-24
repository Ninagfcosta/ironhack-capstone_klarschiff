"""Step 4 - Prepare: the review pack for the customs broker, and the decision log (audit trail)."""
from __future__ import annotations

import csv
from datetime import datetime, timezone

from .config import DATA_DIR
from .models import AgentResult

LOG = DATA_DIR / "decision_log.csv"
LOG_FIELDS = ["timestamp", "shipment_id", "suggested_hs", "final_hs", "decision", "team", "comment", "model", "kb_version"]


def review_pack(r: AgentResult, decision: str = "pending", final_hs: str | None = None, comment: str = "") -> str:
    ok = lambda b: "YES" if b else "no"
    docs = "\n".join(f"| {d.name} | {'required' if d.mandatory else 'recommended'} | {d.status} | {d.legal_ref} |" for d in r.required_documents)
    meas = "\n".join(f"- **{m.name}** ({m.legal_ref}), verified {m.last_verified}{' - RE-VERIFY' if m.stale else ''}: {m.effect}" for m in r.measures) or "- none found"
    issues = "\n".join(f"- [{i.severity}] {i.field}: {i.detail}" for i in r.validation_issues) or "- none"
    reasons = "\n".join(f"- {x}" for x in r.review_reasons) or "- none"
    links = "\n".join(f"- {k}: {v}" for k, v in r.links.items())
    return f"""# KlarSchiff review pack · Prüfpaket für die Zollanmeldung

**Shipment:** {r.shipment_id}  ·  **Generated:** {r.generated_at}  ·  **Mode:** {r.mode} ({r.model})

## Suggestion (Vorschlag)
- **HS code (Zolltarifnummer, 6-digit):** {r.hs_code} - {r.hs_title}
- **Confidence:** {r.confidence:.2f}  ·  **Category:** {r.category}
- **Reasoning:** {r.reasoning}
- **Evidence:** {", ".join(r.evidence) or "-"}
- **Alternatives considered:** {", ".join(r.alternatives) or "-"}

## Documents (Unterlagen)
| Document | Type | Status | Legal basis |
|---|---|---|---|
{docs}

## Trade measures and rules
{meas}

## Invoice vs packing list (Rechnung vs Lieferschein)
{issues}

## Manual review needed: {ok(r.manual_review)}
{reasons}

## Check live before filing
{links}

## Decision (Entscheidung)
- Decision: **{decision}**  ·  Final HS code: **{final_hs or '-'}**  ·  Comment: {comment or '-'}

_Data: knowledge base {r.kb_version}; {r.tariff_data_as_of}._
_{r.disclaimer}_
"""


def log_decision(r: AgentResult, decision: str, final_hs: str, team: str = "logistics", comment: str = "") -> None:
    """Team-level log only (no personal names): performance monitoring of individuals would need
    a works-council agreement in Germany (Section 87(1) no. 6 BetrVG)."""
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow({"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "shipment_id": r.shipment_id,
                    "suggested_hs": r.hs_code, "final_hs": final_hs, "decision": decision, "team": team,
                    "comment": comment, "model": r.model, "kb_version": r.kb_version})


def override_rate() -> dict:
    """Share of suggestions a person changed or rejected: the early-warning sign for automation bias."""
    if not LOG.exists():
        return {"decisions": 0, "override_rate": None}
    rows = list(csv.DictReader(LOG.open(encoding="utf-8")))
    n = len(rows)
    changed = sum(1 for r in rows if r["decision"] in ("corrected", "rejected"))
    return {"decisions": n, "override_rate": round(changed / n, 2) if n else None}
