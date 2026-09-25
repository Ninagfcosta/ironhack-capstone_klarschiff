"""v2.3: the agent works for any product (full HS 2022), with rule packs beyond construction."""
import os
import sys
from datetime import date
from pathlib import Path

os.environ["LANGSMITH_TRACING"] = "false"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from klarschiff import agent, config, retrieval, rules  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

TODAY = date(2026, 9, 25)


def test_full_hs_2022_is_loaded():
    assert retrieval.load_hs()["_meta"]["count"] == 5613


def test_every_reviewed_code_exists_in_hs_2022():
    """Found E10: the reviewed layer had 4418.62 (glulam), which does not exist in HS 2022 (correct: 4418.81)."""
    valid = {x["code"] for x in retrieval.load_hs()["subheadings"]}
    bad = [h["code"] for h in retrieval.load_kb()["headings"] if h["code"] not in valid]
    assert not bad, bad


def test_retrieval_outside_construction():
    assert retrieval.search("optical inspection system for semiconductor wafers")[0].code == "9031.41"
    assert retrieval.search("rechargeable lithium-ion battery")[0].code == "8507.60"


def test_unreviewed_code_always_goes_to_a_person(monkeypatch):
    monkeypatch.setattr(config, "llm_available", lambda: False)
    r = agent.run(Shipment(description="Rechargeable lithium-ion battery packs for notebook computers", origin="CN",
                           destination="DE", intended_use="other"), today=TODAY)
    assert r.hs_code == "8507.60" and r.category == 2
    assert any("not in the reviewed knowledge base" in x for x in r.review_reasons)


def test_dual_use_only_on_export_from_the_eu():
    imp = {m.id for m in rules.applicable_measures("9031.41", {}, Shipment(description="x", origin="JP", destination="DE"), TODAY)}
    exp = {m.id for m in rules.applicable_measures("9031.41", {}, Shipment(description="x", origin="DE", destination="CN"), TODAY)}
    assert "EU_DUAL_USE" not in imp and "EU_DUAL_USE" in exp


def test_us_origin_items_get_an_ear_check():
    ids = {m.id for m in rules.applicable_measures("9031.90", {}, Shipment(description="x", origin="US", destination="DE"), TODAY)}
    assert "US_EAR" in ids


def test_eudr_is_shown_as_upcoming_before_30_dec_2026():
    hits = {m.id: m for m in rules.applicable_measures("0901.21", {}, Shipment(description="x", origin="BR", destination="DE"), TODAY)}
    assert hits["EU_EUDR"].upcoming
    later = {m.id: m for m in rules.applicable_measures("0901.21", {}, Shipment(description="x", origin="BR", destination="DE"), date(2027, 1, 5))}
    assert not later["EU_EUDR"].upcoming
