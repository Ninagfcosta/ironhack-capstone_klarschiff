"""Master list (Produktstamm): part numbers change, the product and its approved HS code stay."""
import os
import sys
from pathlib import Path

os.environ["LANGSMITH_TRACING"] = "false"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from klarschiff import agent, config, master_list  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402

SAMPLE = (ROOT / "mvp" / "sample_data" / "master_list_sample.csv").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def tmp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "llm_available", lambda: False)
    yield tmp_path


def test_part_numbers_and_revisions_do_not_change_the_fingerprint():
    a = master_list.fingerprint("Mineral wool insulation slab 100 mm, P/N INS-100-A Rev B")
    b = master_list.fingerprint("Mineral Wool Insulation Slab 100 mm INS-200-X rev. C")
    assert a == b == "mineral wool insulation slab 100 mm"


def test_import_merges_part_numbers_and_finds_conflicts():
    rep = master_list.import_csv(SAMPLE)
    assert rep["rows"] == 9
    # 3 part numbers of the insulation slab (one with "Rev C" in the text) become ONE product
    slab = [p for p in master_list.load() if "insulation slab" in p.description.lower()]
    assert len(slab) == 1 and set(slab[0].part_numbers) == {"INS-100-A", "INS-100-B", "INS-100-C"}
    # the window profile has two different codes in the client's list: reported, not merged silently
    assert any(c["hs_codes"] == ["7604.29", "7610.10"] for c in rep["conflicts"])
    # M10 A2 and M12 A4 bolts are different products (values differ), even with the same HS code
    assert sum(1 for p in master_list.load() if "hex bolt" in p.description.lower()) == 2


def test_new_part_number_same_description_reuses_the_approved_code():
    master_list.import_csv(SAMPLE)
    r = agent.run(Shipment(description="Mineral wool insulation slab 100 mm, 1200 x 600 mm",
                           part_number="INS-100-Z", origin="PL", destination="DE"))
    assert r.hs_code == "6806.10" and r.mode == "master list"
    assert any("New part number INS-100-Z matches product" in x for x in r.review_reasons)


def test_known_part_number_needs_no_new_classification():
    master_list.import_csv(SAMPLE)
    r = agent.run(Shipment(description="Hex bolt M10x40 stainless A2", part_number="BLT-1040", origin="DE", destination="DE"))
    assert r.hs_code == "7318.15" and r.mode == "master list"
    assert not any("reviewed knowledge base" in x for x in r.review_reasons)


def test_similar_but_different_product_goes_to_a_person_with_differences():
    master_list.import_csv(SAMPLE)
    r = agent.run(Shipment(description="Hex bolt M16x40 stainless A2", part_number="BLT-9999", origin="CN", destination="DE"))
    assert r.mode != "master list"
    assert any("Similar to product" in x and "m16x40" in x for x in r.review_reasons)


def test_conflict_in_the_list_is_never_used_automatically():
    master_list.import_csv(SAMPLE)
    r = agent.run(Shipment(description="Aluminium window profile, thermally broken", part_number="WIN-7001"))
    assert r.mode != "master list"
    assert any("Master list conflict" in x for x in r.review_reasons)


def test_approval_links_new_part_number_and_keeps_history():
    master_list.import_csv(SAMPLE)
    p = master_list.approve("Precast concrete wall element 3.0 x 2.5 m", "6810.91", part_number="PC-3025-B",
                            approved_by="broker")
    assert p.part_numbers == ["PC-3025", "PC-3025-B"]
    assert any("PC-3025-B linked" in h for h in p.history)
    assert master_list.lookup("PC-3025-B", "").kind == "part_number"
