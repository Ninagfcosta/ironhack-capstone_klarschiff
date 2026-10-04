"""LLM-as-judge (course lab: LLM judges): a second model checks that the reasoning is grounded.

Question to the judge: does the agent's reasoning match the chosen code's official title and the words in the
description, without inventing facts? Score 1 = grounded, 0.5 = partly, 0 = not grounded.
Use it in the weekly quality check, next to the rule-based evaluators. A judge is also an AI: we read its comments,
and we compare it with the broker's labels in the blind test before trusting it.
Run:  python evaluation/run_eval.py --local --judge
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from klarschiff import config, llm  # noqa: E402
from klarschiff.guard import DATA_RULE  # noqa: E402

PROMPT = ("You are a strict reviewer of customs classification answers. Compare the REASONING with the CODE TITLE and the "
          "GOODS DESCRIPTION. Grounded means: the reasoning only uses facts from the description and the title, and the "
          "title fits the goods. Answer as JSON: {\"score\": 1 or 0.5 or 0, \"comment\": \"one sentence\"}. " + DATA_RULE)


def reasoning_grounded(outputs: dict, reference_outputs: dict, inputs: dict | None = None) -> dict:
    if not config.llm_available():
        return {"key": "reasoning_grounded", "score": None, "comment": "No AI key: judge skipped."}
    desc = (inputs or {}).get("description", "")
    user = (f"<document>\nGOODS DESCRIPTION: {desc}\nCODE: {outputs.get('hs_code')} - {outputs.get('hs_title')}\n"
            f"REASONING: {outputs.get('reasoning', '')}\n</document>")
    try:
        out = llm.chat_json(PROMPT, user)
        return {"key": "reasoning_grounded", "score": float(out.get("score", 0)), "comment": str(out.get("comment", ""))}
    except Exception as e:
        return {"key": "reasoning_grounded", "score": None, "comment": f"Judge error: {type(e).__name__}"}
