# POC documentation (Round 2)

The proof of concept has two parts that answer two different questions.

| Part | Question it answers | File |
|---|---|---|
| **n8n batch POC v2** | "How good is a plain prompt, on 20 shipments at once?" (the baseline) | `poc/poc_workflow.json` |
| **KlarSchiff agent** | "How much better is retrieval + rules + human review?" | `klarschiff/` (used by the MVP and the evaluation) |

The Round 1 workflow (3 nodes, one shipment at a time) stays in `n8n/` for history.

## 1. n8n batch POC v2

```
[Manual Trigger] → [Load 20 test cases] → [Message a model (GPT-4o-mini)] → [Score against expected] → [Summary]
                      Code node               one call per shipment            Code node                  Code node
```

| Node | What it does |
|---|---|
| Load 20 test cases | Returns the 20 shipments of `evaluation/dataset.jsonl` as 20 items, with the expected HS code and review decision |
| Message a model | Same prompt style as Round 1, now asking for JSON: `hs_code, required_documents, missing_documents, manual_review, source, confidence` |
| Score against expected | Reads the JSON answer, normalises the code, scores it (1 = exact, 0.5 = right 4-digit heading, 0 = wrong) and marks **false all-clears** |
| Summary | One line: HS accuracy, number of false all-clears and the list of wrong codes |

**How to run:** n8n → Workflows → Import from file → `poc/poc_workflow.json` → open *Message a model* and select your OpenAI credential → **Execute workflow** → open the *Summary* node output. Paste the summary into `evaluation/langsmith.md` §4 (baseline row).

**Why keep a prompt-only baseline?** It shows what the retrieval and rule layers add. Without a baseline, a good score means nothing.

## 2. The agent (what the MVP runs)

```
Shipment ─► Intake ─► Validate ─► Retrieve candidates (RAG) ─► LLM chooses code ─► Rules (category, documents, measures)
                                                                                     │
                   Monitor alerts ────────────────────────────────────────────────► Review triggers ─► Review pack + decision log
```

- **Retrieval (RAG):** BM25 over `klarschiff/knowledge/hs_headings.json` (50 reviewed headings with keywords in English and a German glossary). The LLM gets the top 5 real headings, so it chooses instead of inventing.
- **LLM:** GPT-4o-mini, temperature 0, JSON output, pinned model name (`KLARSCHIFF_MODEL`). If the API fails, the agent falls back to offline mode and **always** routes to a person.
- **Rules:** `klarschiff/knowledge/trade_measures.json` holds every measure with legal reference, effective date, source link, `last_verified` and a re-check interval. Rules older than their interval trigger a review.
- **Review triggers (13):** description too vague (< 3 meaningful words), close call between two headings, confidence < 0.75, code not in the knowledge base, missing information, missing mandatory document, invoice/packing mismatch, Category 3, shipment ≥ 100 t, CBAM goods ≥ 50 t in one shipment, stale rules, open monitor alert, offline mode.
- **Tracing:** every run is a LangSmith trace (`klarschiff_agent` → `recommend_llm` → OpenAI call).

## 3. Reproduce

```bash
cd capstone-round1-hoffmann
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # paste your own keys into .env
python evaluation/run_eval.py --local      # 20 cases, results in evaluation/results/
streamlit run mvp/app.py      # the MVP
```

## 4. Demo video

Round 1 demo (n8n, 2:10, AI narration with Kokoro TTS): [`KlarSchiff_POC_demo.mp4`](KlarSchiff_POC_demo.mp4) in this folder (also linked in `n8n/workflow_documentation.md` §7).
Round 2 demo (MVP, 2-5 min): see `mvp/mvp_documentation.md` §6.
