"""Run the evaluation (core: 20 construction cases; --dataset universal: 17 cases from other industries).

  python evaluation/run_eval.py --local       # runs here, writes evaluation/results/<name>.json + .md (no LangSmith needed)
  python evaluation/run_eval.py --langsmith   # uploads the dataset and runs a LangSmith experiment (needs LANGSMITH_API_KEY)

Both modes use the same agent and the same evaluators.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evaluation"))

from klarschiff import agent, config  # noqa: E402
from klarschiff.models import Shipment  # noqa: E402
from evaluators import ALL  # noqa: E402

DATASET = ROOT / "evaluation" / "dataset.jsonl"
DATASET_NAME = "klarschiff-eval-v2"
DATASETS = {"core": ("dataset.jsonl", "klarschiff-eval-v2"), "universal": ("dataset_universal.jsonl", "klarschiff-eval-universal")}


def load_cases():
    return [json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()]


def target(inputs: dict) -> dict:
    r = agent.run(Shipment(**inputs))
    return json.loads(r.model_dump_json())


def run_local(label: str):
    cases, rows = load_cases(), []
    for c in cases:
        out = target(c["inputs"])
        scores = {e.__name__: e(out, c["reference"]) for e in ALL}
        rows.append({"id": c["id"], "description": c["inputs"]["description"], "reference": c["reference"], "meta": c["meta"],
                     "output": {k: out[k] for k in ("hs_code", "hs_title", "confidence", "category", "manual_review",
                                                   "missing_documents", "review_reasons", "reasoning", "mode")},
                     "scores": scores})
        print(f"{c['id']}: {out['hs_code']} conf={out['confidence']} cat={out['category']} review={out['manual_review']} | "
              + " ".join(f"{k.split('_')[0]}={v['score']}" for k, v in scores.items()))
    summary = {}
    for e in ALL:
        vals = [r["scores"][e.__name__]["score"] for r in rows if r["scores"][e.__name__]["score"] is not None]
        summary[e.__name__] = {"mean": round(sum(vals) / len(vals), 3) if vals else None, "n": len(vals)}
    res = {"label": label, "run_at": datetime.now().isoformat(timespec="seconds"), "model": config.MODEL,
           "llm": config.llm_available(), "summary": summary, "cases": rows}
    out_dir = ROOT / "evaluation" / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{label}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nSUMMARY", json.dumps(summary, indent=1))
    return res


def run_langsmith(label: str):
    from langsmith import Client
    client = Client()
    if not client.has_dataset(dataset_name=DATASET_NAME):
        client.create_dataset(DATASET_NAME, description="KlarSchiff evaluation cases")
        client.create_examples(dataset_name=DATASET_NAME, examples=[
            {"inputs": c["inputs"], "outputs": c["reference"], "metadata": {**c["meta"], "case_id": c["id"]}} for c in load_cases()])
    results = client.evaluate(target, data=DATASET_NAME, evaluators=ALL, experiment_prefix=label,
                              metadata={"model": config.MODEL, "kb": "2026-09-25"}, max_concurrency=2)
    print("Experiment:", results.experiment_name)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--langsmith", action="store_true")
    ap.add_argument("--label", default=None)
    ap.add_argument("--dataset", choices=list(DATASETS), default="core",
                    help="core = the 20 construction cases; universal = 17 cases from other industries (v2.3)")
    a = ap.parse_args()
    DATASET = ROOT / "evaluation" / DATASETS[a.dataset][0]
    DATASET_NAME = DATASETS[a.dataset][1]
    label = a.label or (("llm-" + config.MODEL if config.llm_available() else "offline-baseline") + ("" if a.dataset == "core" else "-" + a.dataset))
    if a.langsmith:
        run_langsmith(label)
    else:
        run_local(label)
