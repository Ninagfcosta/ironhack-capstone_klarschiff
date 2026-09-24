"""Step 5 - Monitor: watch official sources for tariff and regulation changes.

Why: tariffs change fast (US: IEEPA tariffs ended by the Supreme Court on 20 Feb 2026 and replaced by a
temporary surcharge; Section 232 base changed on 6 Apr 2026. EU: new steel measure on 1 Jul 2026, CBAM
definitive regime on 1 Jan 2026). A classifier that only "remembers" old rates becomes wrong silently.

What it does (run daily, e.g. GitHub Actions or an n8n schedule):
  1. US Federal Register API  -> new documents about Section 232 / 122 / HTS changes since the last run
  2. USITC HTS REST API       -> current US general duty rate for the products I&E sells; alert on change
  3. Official EU pages        -> content fingerprint; alert when the page changes
Every alert names the affected HS codes and stays "open" until a person reviews it.
While an alert is open, the agent sends affected shipments to manual review.

Run:  python -m klarschiff.monitor
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone

import requests

from .config import DATA_DIR
from .rules import load_measures

STATE_FILE = DATA_DIR / "monitor_state.json"
ALERTS_FILE = DATA_DIR / "alerts.json"
HEADERS = {"User-Agent": "KlarSchiff-monitor/1.0 (tariff watch; contact: project owner)"}
TIMEOUT = 20


def _load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_alerts() -> list[dict]:
    return _load(ALERTS_FILE, [])


def open_alerts_for(hs_code: str) -> list[dict]:
    digits = hs_code.replace(".", "")
    out = []
    for a in load_alerts():
        if a.get("status") != "open":
            continue
        affects = a.get("affects_hs_prefixes", [])
        if not affects or any(digits.startswith(p) for p in affects):
            out.append(a)
    return out


def mark_reviewed(alert_id: str, note: str = "") -> None:
    alerts = load_alerts()
    for a in alerts:
        if a["id"] == alert_id:
            a["status"] = "reviewed"
            a["reviewed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            a["review_note"] = note
    _save(ALERTS_FILE, alerts)


def _new_alert(alerts, source, title, url, affects, detail=""):
    aid = hashlib.sha1(f"{source}|{title}|{url}".encode()).hexdigest()[:10]
    if any(a["id"] == aid for a in alerts):
        return None
    a = {"id": aid, "created": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": source,
         "title": title, "url": url, "affects_hs_prefixes": affects, "detail": detail, "status": "open"}
    alerts.append(a)
    return a


def _measure_prefixes(measure_id):
    for m in load_measures()["measures"]:
        if m["id"] == measure_id:
            return [p for p in m.get("hs_prefixes", []) if p]
    return []


def check_federal_register(src, state, alerts):
    since = state.get("fedreg_since", (date.today().replace(day=1)).isoformat())
    found = []
    for term in src["terms"]:
        r = requests.get("https://www.federalregister.gov/api/v1/documents.json", headers=HEADERS, timeout=TIMEOUT, params={
            "conditions[term]": term, "conditions[publication_date][gte]": since,
            "order": "newest", "per_page": 20, "fields[]": ["title", "html_url", "publication_date", "type", "abstract"]})
        r.raise_for_status()
        for d in r.json().get("results", []):
            a = _new_alert(alerts, "US Federal Register", f"{d['publication_date']}: {d['title']}", d["html_url"],
                           _measure_prefixes(src["measure"]), (d.get("abstract") or "")[:400])
            if a:
                found.append(a)
    state["fedreg_since"] = date.today().isoformat()
    return found


def check_usitc_hts(src, state, alerts):
    found = []
    rates = state.setdefault("hts_rates", {})
    for hs in src["hs"]:
        r = requests.get("https://hts.usitc.gov/reststop/search", params={"keyword": hs}, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        rows = r.json() if isinstance(r.json(), list) else r.json().get("results", [])
        digits = hs.replace(".", "")
        snapshot = sorted({f"{row.get('htsno')}={row.get('general')}" for row in rows
                           if str(row.get("htsno", "")).replace(".", "").startswith(digits) and row.get("general")})
        if not snapshot:
            continue
        if hs in rates and rates[hs] != snapshot:
            a = _new_alert(alerts, "USITC HTS", f"US general duty rate changed for HS {hs}",
                           "https://hts.usitc.gov/search?query=" + digits, [digits],
                           f"before: {rates[hs][:3]} | now: {snapshot[:3]}")
            if a:
                found.append(a)
        rates[hs] = snapshot
    return found


def _fingerprint(html: str) -> str:
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(text.encode()).hexdigest()


def check_page(src, state, alerts):
    r = requests.get(src["url"], headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    fp = _fingerprint(r.text)
    pages = state.setdefault("pages", {})
    found = []
    if src["id"] in pages and pages[src["id"]] != fp:
        a = _new_alert(alerts, "EU official page", f"Official page changed: {src['id']} ({date.today().isoformat()})",
                       src["url"], _measure_prefixes(src["measure"]), "Content changed since the last check. A person must read it.")
        if a:
            found.append(a)
    pages[src["id"]] = fp
    return found


CHECKERS = {"federal_register": check_federal_register, "usitc_hts": check_usitc_hts, "page_hash": check_page}


def run() -> dict:
    state, alerts = _load(STATE_FILE, {}), load_alerts()
    report = {"run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "new_alerts": [], "errors": []}
    for src in load_measures()["watch_sources"]:
        try:
            report["new_alerts"] += CHECKERS[src["type"]](src, state, alerts)
        except Exception as e:  # one broken source must not stop the others
            report["errors"].append(f"{src['id']}: {type(e).__name__}: {e}"[:300])
    state["last_run"] = report["run_at"]
    state["last_errors"] = report["errors"]
    _save(STATE_FILE, state)
    _save(ALERTS_FILE, alerts)
    return report


def last_run() -> str:
    return _load(STATE_FILE, {}).get("last_run", "never")


if __name__ == "__main__":
    rep = run()
    print(f"Monitor run {rep['run_at']}: {len(rep['new_alerts'])} new alert(s), {len(rep['errors'])} source error(s).")
    for a in rep["new_alerts"]:
        print(" -", a["source"], "|", a["title"], "|", a["url"])
    for e in rep["errors"]:
        print(" ! ", e)
