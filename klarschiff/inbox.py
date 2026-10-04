"""E-mail inbox (v2.6): supplier documents arrive by e-mail and are checked without copy-paste.

Why (pilot need): most shipment documents reach the team as e-mail attachments. Downloading, renaming and
re-typing them takes time and causes mistakes.
How (course tools): the n8n workflow n8n/email_inbox_workflow.json watches the mailbox (Gmail Trigger), saves each
attachment into the inbox folder (data/inbox/) with a small .meta.json file (sender, subject, date) and alerts the team
on Telegram. Here the agent reads each file (PDF text, CSV lines, e-invoice XML or plain text), checks it, opens a
review ticket when a person must look, and moves the file to data/inbox/done/. Nothing is sent to the supplier.
Scanned PDFs (images) are not read automatically here: they are flagged, and a person opens them in the Check tab.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from . import agent, config, intake, review_queue
from .models import Shipment

TYPES = {".pdf", ".csv", ".xml", ".txt"}


def folder() -> Path:
    p = Path(config.INBOX_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def log_file() -> Path:
    return config.DATA_DIR / "inbox_log.jsonl"


def pending() -> list[Path]:
    """Files waiting in the inbox (oldest first)."""
    return sorted((f for f in folder().iterdir() if f.is_file() and f.suffix.lower() in TYPES),
                  key=lambda f: f.stat().st_mtime)


def _meta(path: Path) -> dict:
    m = path.with_name(path.name + ".meta.json")
    try:
        return json.loads(m.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def shipment_from_file(path: Path) -> Shipment:
    """Turn one inbox file into a shipment for the agent."""
    meta, suffix, data = _meta(path), path.suffix.lower(), path.read_bytes()
    text, lines, legible, unreadable, source = "", [], True, [], "e-mail"
    if suffix == ".pdf":
        try:
            text, source = intake.text_from_pdf(data), "e-mail (text PDF)"
        except ValueError:
            legible, unreadable, source = False, ["scanned PDF: open it in the Check tab"], "e-mail (scanned PDF)"
    elif suffix == ".csv":
        lines = intake.lines_from_csv(data.decode("utf-8-sig"))
        text = "; ".join(l.description for l in lines)
    elif suffix == ".xml":
        lines = intake.lines_from_einvoice(data)
        text = "; ".join(l.description for l in lines)
    else:
        text = data.decode("utf-8", errors="replace")
    subject = meta.get("subject", "")
    full = (subject + "\n" + text).strip() or f"Attachment {path.name} (no readable text)"
    provided, _missing = intake.detect_documents(full)
    return Shipment(shipment_id=f"mail-{path.stem[:30]}", description=full[:6000],
                    origin=(meta.get("origin") or "").upper()[:2], destination=(meta.get("destination") or "DE").upper()[:2],
                    documents_provided=provided, invoice_lines=lines, legible=legible, unreadable_parts=unreadable,
                    source=source, intended_use=meta.get("intended_use", "construction"))


def check(path: Path) -> dict:
    """Check one file, open a review ticket if needed, move it to done/ and log the result."""
    s = shipment_from_file(path)
    res = agent.run(s)
    ticket = review_queue.add(res, s.description) if res.manual_review else None
    meta = _meta(path)
    row = {"file": path.name, "from": meta.get("from", ""), "subject": meta.get("subject", ""),
           "received": meta.get("received", ""), "checked_at": datetime.now().isoformat(timespec="seconds"),
           "hs_code": res.hs_code, "category": res.category, "manual_review": res.manual_review,
           "reasons": res.review_reasons[:3], "missing_documents": res.missing_documents,
           "ticket": ticket["id"] if ticket else ""}
    done = folder() / "done"
    done.mkdir(exist_ok=True)
    for f in (path, path.with_name(path.name + ".meta.json")):
        if f.exists():
            shutil.move(str(f), str(done / f.name))
    with log_file().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def check_all() -> list[dict]:
    return [check(p) for p in pending()]


def history(limit: int = 50) -> list[dict]:
    try:
        rows = [json.loads(x) for x in log_file().read_text(encoding="utf-8").splitlines() if x.strip()]
    except FileNotFoundError:
        rows = []
    return rows[::-1][:limit]
