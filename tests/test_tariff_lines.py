"""v2.3: 8-digit CN (EU) and HTS (US) lines, rulings library, cost estimate. Test data below is SYNTHETIC."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from klarschiff import agent, config, precedents, tariff_lines  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

SKOS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:skos="http://www.w3.org/2004/02/skos/core#">
  <skos:Concept rdf:about="http://example.org/cn/252329"><skos:notation>2523 29</skos:notation>
    <skos:prefLabel xml:lang="en">- - Other</skos:prefLabel></skos:Concept>
  <skos:Concept rdf:about="http://example.org/cn/25232900"><skos:notation>2523 29 00</skos:notation>
    <skos:prefLabel xml:lang="en">- - Other</skos:prefLabel><skos:prefLabel xml:lang="de">- - anderer</skos:prefLabel></skos:Concept>
  <rdf:Description rdf:about="http://example.org/cn/84561100"><skos:notation>8456 11 00</skos:notation>
    <skos:prefLabel xml:lang="en">- - Operated by laser</skos:prefLabel></rdf:Description>
</rdf:RDF>"""


def test_parse_cn_skos_is_tolerant(tmp_path):
    import download_official_data as d
    f = tmp_path / "cn.rdf"
    f.write_text(SKOS_SAMPLE, encoding="utf-8")
    lines = d.parse_cn_skos(f)
    assert [l["code"] for l in lines] == ["25232900", "84561100"]
    assert lines[0]["title_de"] == "anderer" and lines[1]["title_en"] == "Operated by laser"


def test_suggest_picks_by_words_or_asks_a_person():
    lines = [{"code": "7318.15.10", "title": "Screws for wood"}, {"code": "7318.15.90", "title": "Hexagon bolts with nuts"}]
    assert tariff_lines.suggest("stainless hexagon bolts M10 with nuts", lines)[0] == "7318.15.90"
    assert tariff_lines.suggest("steel parts", lines)[0] == ""  # no clear winner -> a person chooses


def test_us_lines_from_cache_without_network(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    (tmp_path / "hts_cache.json").write_text(json.dumps({"845611": [{"code": "8456.11.10", "title": "Operated by laser, for cutting", "rate": "SYNTHETIC"}]}))
    r = agent.run(Shipment(description="Laser cutting machine for metal sheets", origin="JP", destination="US"))
    assert r.national["system"].startswith("HTS") and r.national["suggested"] == "8456.11.10"


def test_rulings_library_is_used_as_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    precedents.import_csv("reference,source,code,description,issued,valid_until,url\n"
                          "TEST-0001,synthetic test,8456.11,Laser cutting machine for metal sheets,2024-01-01,2027-01-01,\n"
                          "TEST-0002,synthetic test,2523.29,Portland cement in bags,2019-01-01,2022-01-01,\n")
    r = agent.run(Shipment(description="Laser cutting machine", origin="JP", destination="DE"))
    assert r.precedents and r.precedents[0]["reference"] == "TEST-0001" and r.precedents[0]["valid"]
    old = precedents.search("Portland cement bags")[0]
    assert old["reference"] == "TEST-0002" and not old["valid"]  # expired BTI is shown, marked expired


def test_cost_estimate_from_token_usage(monkeypatch):
    from klarschiff import llm
    llm.reset_usage()
    llm.USAGE.update(prompt_tokens=1_000_000, completion_tokens=100_000, calls=1)
    monkeypatch.setattr(config, "PRICE_IN_PER_M", 0.15)
    monkeypatch.setattr(config, "PRICE_OUT_PER_M", 0.60)
    assert llm.usage_with_cost()["est_cost_usd"] == 0.21
    llm.reset_usage()
    r = agent.run(Shipment(description="Portland cement CEM I in bags"))
    assert r.usage["est_cost_usd"] == 0  # offline: no AI cost
