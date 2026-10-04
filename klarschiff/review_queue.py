"""Review queue: every shipment that needs a person gets a ticket, so nothing is forgotten.

Why (pilot need): reviews happen between other work. A list with owner, due date and status keeps them visible.
How:
- The queue is a small JSON file in the data folder (works offline, no extra service).
- Optional: if KLARSCHIFF_N8N_WEBHOOK is set, each new ticket is also sent to an n8n workflow
  (n8n/review_queue_workflow.json) that writes it to Airtable and posts an alert in the team's Telegram group.
  This is the same Trigger -> Set -> Airtable pattern as the course lab, plus a Telegram message.
Only goods data and codes are sent: no personal data.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone

from .config import DATA_DIR

QUEUE = DATA_DIR / "review_queue.json"
WEBHOOK = os.getenv("KLARSCHIFF_N8N_WEBHOOK", "")


def load() -> list[dict]:
    try:
        return json.loads(QUEUE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save(items: list[dict]) -> None:
    QUEUE.write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")


def next_working_day(d: date) -> date:
    d = d + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def add(result, description: str = "", today: date | None = None, notify: bool = True) -> dict:
    """Open a ticket for a result that needs a person. Returns the ticket (or the existing open one)."""
    items = load()
    for it in items:
        if it["shipment_id"] == result.shipment_id and it["status"] != "done":
            return it
    today = today or date.today()
    ticket = {
        "id": f"R-{len(items) + 1:04d}",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "shipment_id": result.shipment_id,
        "description": description[:200],
        "hs_code": result.hs_code,
        "category": result.category,
        "reasons": result.review_reasons[:5],
        "owner": "",
        "due": next_working_day(today).isoformat(),
        "status": "open",
        "closed": "",
    }
    items.append(ticket)
    save(items)
    if notify:
        send_to_n8n(ticket)
    return ticket


def update(ticket_id: str, status: str | None = None, owner: str | None = None) -> None:
    items = load()
    for it in items:
        if it["id"] == ticket_id:
            if owner is not None:
                it["owner"] = owner
            if status:
                it["status"] = status
                it["closed"] = datetime.now(timezone.utc).isoformat(timespec="seconds") if status == "done" else ""
    save(items)


def send_to_n8n(ticket: dict) -> bool:
    """POST the ticket to the n8n webhook (optional). Never breaks the app if n8n is not reachable."""
    if not WEBHOOK:
        return False
    try:
        import requests
        requests.post(WEBHOOK, json=ticket, timeout=8).raise_for_status()
        return True
    except Exception:
        return False


def stats() -> dict:
    items = load()
    open_ = [i for i in items if i["status"] != "done"]
    overdue = [i for i in open_ if i["due"] < date.today().isoformat()]
    hours = []
    for i in items:
        if i["status"] == "done" and i["closed"]:
            a = datetime.fromisoformat(i["created"]); b = datetime.fromisoformat(i["closed"])
            hours.append((b - a).total_seconds() / 3600)
    return {"total": len(items), "open": len(open_), "overdue": len(overdue),
            "avg_hours_to_close": round(sum(hours) / len(hours), 1) if hours else None}
