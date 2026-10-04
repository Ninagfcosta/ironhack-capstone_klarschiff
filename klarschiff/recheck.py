"""Re-check after a rule change: which approved products are affected by an open alert?

Why (pilot need): when a tariff or rule changes, earlier classifications can become wrong without anyone noticing.
How: every open monitor alert names HS prefixes. We list the master-list products whose approved code starts with
one of them, so a person can review them. (Run the batch check on this list to get fresh results.)
"""
from __future__ import annotations

from . import master_list, monitor


def affected_products() -> list[dict]:
    rows = []
    open_alerts = [a for a in monitor.load_alerts() if a.get("status") == "open"]
    for p in master_list.load():
        code = (p.hs_code or "").replace(".", "")
        if not code:
            continue
        for a in open_alerts:
            prefixes = [x.replace(".", "") for x in a.get("affects_hs_prefixes") or []]
            if not prefixes or any(code.startswith(x) for x in prefixes):
                rows.append({"product_id": p.product_id, "hs_code": p.hs_code, "description": p.description,
                             "alert": a.get("title", "")[:90], "source": a.get("source", ""), "action": "re-check"})
                break
    return rows
