"""EN/DE interface: every on-screen text has a German version, and the agent's reasons are translated."""
import ast
import json
import os
import sys
from pathlib import Path

os.environ["LANGSMITH_TRACING"] = "false"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "mvp"))

from i18n import UI, reason, t  # noqa: E402
from klarschiff import agent, config  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402


def _texts_passed_to_T():
    """All literal strings the app passes to T(...)."""
    tree = ast.parse((ROOT / "mvp" / "app.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "T" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                yield node.args[0].value


def test_every_interface_text_has_german():
    texts = list(_texts_passed_to_T())
    assert len(texts) > 60
    missing = [x for x in texts if x not in UI]
    assert not missing, missing


def test_english_is_default_and_unchanged():
    assert t("Check shipment") == "Check shipment"
    assert t("Check shipment", "de") == "Sendung prüfen"
    assert t("Something not in the list", "de") == "Something not in the list"  # never empty


def test_all_agent_reasons_translate(monkeypatch):
    monkeypatch.setattr(config, "llm_available", lambda: False)
    seen = set()
    lines = []
    for f in ("dataset.jsonl", "dataset_universal.jsonl"):
        lines += (ROOT / "evaluation" / f).read_text(encoding="utf-8").splitlines()
    for line in lines:
        inputs = json.loads(line)["inputs"]
        r = agent.run(Shipment(**{k: v for k, v in inputs.items() if k in Shipment.model_fields}))
        seen.update(r.review_reasons + r.category_reasons)
    untranslated = [x for x in seen if reason(x, "de") == x and "national" not in x.lower() and "zulassung" not in x.lower()]
    assert len(seen) > 8
    assert not untranslated, untranslated


def test_translation_reason_keeps_values():
    de = reason("Translated from 'tr': a person checks the translation. Uncertain terms: torba.", "de")
    assert de == "Übersetzt aus 'tr': ein Mensch prüft die Übersetzung. Unsichere Begriffe: torba."
    assert reason("Close call between 7214.20 and 7213.10: a person must choose.", "de").startswith("Knappe Entscheidung zwischen 7214.20 und 7213.10")


def test_master_list_reasons_translate(tmp_path, monkeypatch):
    from klarschiff import master_list
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "llm_available", lambda: False)
    master_list.import_csv((ROOT / "mvp" / "sample_data" / "master_list_sample.csv").read_text(encoding="utf-8"))
    cases = [("Wafer stage assembly, spare part for optical wafer inspection system", "0100-77777"),
             ("Linear motor 24 V for positioning stage", "0200-55120"),
             ("Hex bolt M16x40 stainless A2", "0400-99999"),
             ("Ceramic heater plate 230 V for vacuum chamber", "0400-10010")]
    reasons = set()
    for d, pn in cases:
        r = agent.run(Shipment(description=d, part_number=pn))
        reasons.update(x for x in r.review_reasons if "product KS-" in x or "part number" in x.lower())
    assert len(reasons) >= 4, reasons
    assert all(reason(x, "de") != x for x in reasons), [x for x in reasons if reason(x, "de") == x]
