"""v2.3: batch report and REST API."""
from pathlib import Path

from fastapi.testclient import TestClient

from klarschiff import batch, config

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = (ROOT / "mvp" / "sample_data" / "batch_sample.csv").read_text(encoding="utf-8")


def test_batch_report_and_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    rows, summary = batch.run_csv(SAMPLE)
    assert summary["shipments"] == 6 and len(rows) == 6
    assert summary["to_review"] + summary["passed_checks"] == 6
    assert summary["est_cost_usd_total"] == 0  # offline in tests
    assert "hs_code" in batch.to_csv(rows).splitlines()[0]


def test_api_check_health_and_key(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import api.main as m
    monkeypatch.setattr(m, "API_KEY", "secret")
    c = TestClient(m.app)
    assert c.get("/health").json()["status"] == "ok"
    body = {"description": "Portland cement CEM I 42.5 in bags", "origin": "TR", "destination": "DE"}
    assert c.post("/check", json=body).status_code == 401
    r = c.post("/check", json=body, headers={"X-API-Key": "secret"})
    assert r.status_code == 200 and r.json()["hs_code"] == "2523.29" and r.json()["manual_review"] is True
    r = c.post("/batch", files={"file": ("b.csv", SAMPLE, "text/csv")}, headers={"X-API-Key": "secret"})
    assert r.json()["summary"]["shipments"] == 6
