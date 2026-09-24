"""Unit tests (offline, no API key needed):  python -m pytest -q"""
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["OPENAI_API_KEY"] = ""          # force offline mode in tests
os.environ.setdefault("KLARSCHIFF_DATA_DIR", str(ROOT / "data" / "_test"))

from klarschiff import agent, config, intake, recommend, retrieval, rules, validate  # noqa: E402
from klarschiff.models import Classification, Line, Shipment  # noqa: E402

config.OPENAI_API_KEY = ""


def test_retrieval_finds_cement():
    assert retrieval.search("Portland cement CEM I in bags")[0].code == "2523.29"


def test_german_glossary():
    assert retrieval.search("Mineralwolle Dämmplatten")[0].code == "6806.10"


def test_detect_missing_and_provided_documents():
    provided, missing = intake.detect_documents("Invoice: wall panels. DoP missing. CE label attached.")
    assert "Declaration of Performance (DoP / DoPC)" in missing
    assert "CE marking evidence (label or photo)" in provided


def test_extract_tonnes():
    assert intake.extract_tonnes("500 bags of 25 kg") == 12.5
    assert intake.extract_tonnes("steel rebar, 500 t") == 500
    assert intake.extract_tonnes("24,000 kg") == 24


def test_validate_quantity_mismatch():
    issues = validate.compare([Line(description="OSB 18 mm", quantity=500)], [Line(description="OSB 18 mm", quantity=450)])
    assert any("quantity" in i.field for i in issues)


def test_missing_dop_always_goes_to_review():
    r = agent.run(Shipment(description="Invoice: precast concrete wall elements, DoP missing", origin="RS"))
    assert r.hs_code == "6810.91"
    assert "Declaration of Performance (DoP / DoPC)" in r.missing_documents
    assert r.manual_review


def test_cbam_and_steel_measure_for_rebar():
    r = agent.run(Shipment(description="hot-rolled ribbed reinforcing steel bars, 500 t", origin="TR", destination="DE"))
    ids = {m.id for m in r.measures}
    assert {"EU_CBAM", "EU_STEEL_TRQ_2026"} <= ids and r.category == 3 and r.manual_review


def test_us_export_gets_section_232():
    r = agent.run(Shipment(description="steel H-beams HEB 300, 40 t", origin="DE", destination="US"))
    assert "US_SECTION_232" in {m.id for m in r.measures}


def test_measure_not_active_before_effective_date():
    s = Shipment(description="rebar", origin="TR", destination="DE")
    hits = rules.applicable_measures("7214.20", {}, s, today=date(2026, 6, 1))
    assert "EU_STEEL_TRQ_2026" not in {m.id for m in hits}


def test_stale_rule_data_triggers_review():
    s = Shipment(description="hot-rolled ribbed reinforcing steel bars", origin="TR", destination="DE")
    r = agent.run(s, today=date(2027, 6, 1))
    assert any("older than its review interval" in x for x in r.review_reasons)


def test_llm_failure_falls_back_safely(monkeypatch):
    monkeypatch.setattr(config, "llm_available", lambda: True)
    def boom(*a, **k):
        raise ConnectionError("no network")
    monkeypatch.setattr(recommend, "_call_llm", boom)
    c, mode = recommend.classify(Shipment(description="Portland cement"), retrieval.search("Portland cement"))
    assert mode == "offline" and c.confidence <= 0.6


def test_invalid_llm_code_is_penalised(monkeypatch):
    monkeypatch.setattr(config, "llm_available", lambda: True)
    monkeypatch.setattr(recommend, "_call_llm", lambda s, c: Classification(hs_code="25232", confidence=0.95, reasoning="x" * 40))
    c, mode = recommend.classify(Shipment(description="cement"), [])
    assert c.confidence <= 0.4


def test_knowledge_base_codes_are_well_formed():
    kb = json.loads((ROOT / "klarschiff" / "knowledge" / "hs_headings.json").read_text())
    import re
    assert all(re.fullmatch(r"\d{4}\.\d{2}", h["code"]) for h in kb["headings"])


def test_monitor_creates_alerts_and_routes_to_review(monkeypatch, tmp_path):
    """Simulated sources: a new Federal Register notice, a changed US rate and a changed EU page."""
    from klarschiff import monitor

    monkeypatch.setattr(monitor, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(monitor, "ALERTS_FILE", tmp_path / "alerts.json")
    calls = {"hts": 0, "page": 0}

    class R:
        def __init__(self, data=None, text=""):
            self._d, self.text = data, text
        def raise_for_status(self):
            pass
        def json(self):
            return self._d

    def fake_get(url, params=None, headers=None, timeout=None):
        if "federalregister" in url:
            return R({"results": [{"title": "Adjusting imports of steel into the United States", "publication_date": "2026-09-20",
                                   "html_url": "https://www.federalregister.gov/d/2026-12345", "abstract": "Section 232"}]})
        if "usitc" in url:
            calls["hts"] += 1
            rate = "Free" if calls["hts"] <= 6 else "25%"
            return R([{"htsno": params["keyword"].replace(".", "") + ".00", "general": rate}])
        calls["page"] += 1
        return R(text=f"<html><body>version {calls['page'] > 3}</body></html>")

    monkeypatch.setattr(monitor.requests, "get", fake_get)
    monitor.run()                      # first run: baseline + Federal Register notice
    rep = monitor.run()                # second run: US rates and EU pages changed
    alerts = monitor.load_alerts()
    assert any(a["source"] == "US Federal Register" for a in alerts)
    assert any(a["source"] == "USITC HTS" for a in rep["new_alerts"])
    assert any(a["source"] == "EU official page" for a in rep["new_alerts"])
    assert monitor.open_alerts_for("7214.20")
