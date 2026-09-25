# Evaluation with LangSmith: 20 cases, 6 evaluators, and the errors we found

**Version:** Round 2 · 25 September 2026 · dataset `klarschiff-eval-v2` · project `klarschiff`

> Teaching-staff feedback after Round 1: *"A machine is never perfect: show at least one error."*
> This document shows the errors: in the agent, in our code, and in our own Round 1 answer key.

## 1. Setup

| Item | Value |
|---|---|
| Tracing | `LANGSMITH_TRACING=true`; every run is one trace: `klarschiff_agent` (chain) → `recommend_llm` → OpenAI call |
| Dataset | `evaluation/dataset.jsonl` → uploaded as `klarschiff-eval-v2` (inputs = shipment, outputs = reference answer, metadata = tags) |
| Experiment | `python evaluation/run_eval.py --langsmith` (uses `client.evaluate`, max concurrency 2) |
| Local runner | `python evaluation/run_eval.py --local` (same agent, same evaluators, JSON in `evaluation/results/`) |
| Model | `gpt-4o-mini`, temperature 0, pinned via `KLARSCHIFF_MODEL` |

## 2. Dataset: 20 shipments

| Group | Cases | What it tests |
|---|---|---|
| Round 1 cases (relabelled where the key was wrong) | TC01-TC05 | Continuity with Round 1 |
| Category 2, CE-marked products | TC03, TC06, TC08, TC09, TC19, TC17 | DoP/CE rules |
| Category 3, trade measures | TC01, TC05, TC07, TC12, TC16, TC18, TC20 | CBAM, EU steel measure, anti-dumping, US Section 232 |
| **Safety cases** (must go to a person) | TC04, TC08, TC11 (missing documents), TC14 (vague), TC15 (out of scope), TC17 (quantity mismatch) | The "no false all-clear" rule |
| Language and route | TC16 (German invoice), TC18 (export to the US) | Real-life variety |

## 3. Evaluators (the Round 1 criteria, automated)

| Evaluator | Round 1 criterion | Score |
|---|---|---|
| `hs_code_correct` | #1 correct code | 1 exact · 0.5 right 4-digit heading · 0 wrong (not scored for TC14) |
| `missing_document_flagged` | #2 missing documents flagged | share of expected missing documents flagged |
| `source_shown` | #3 traceable source | reason + evidence or KB title + live tariff links |
| `review_routing` | #4 uncertain cases to a person | 1 correct · 0.5 unnecessary review · **0 false all-clear** |
| `no_false_all_clear` | safety metric | 0 if a case that needed a person was passed |
| `category_correct` | new | category 1/2/3 matches the rules |

## 4. Results

| Experiment | HS code | Missing docs | Source | Routing | No false all-clear | Category |
|---|---|---|---|---|---|---|
| A · Offline baseline (keyword retrieval, no LLM) | 0.89 | 1.00 | 1.00 | 0.83 | 1.00 | 1.00 |
| C1 · Full agent v2.0, gpt-4o-mini | **0.95** | 1.00 | 1.00 | 0.95 | **0.95 (1 false all-clear: TC14)** | 1.00 |
| C2 · Full agent v2.1 (two new review triggers) · LangSmith experiment `klarschiff-v2.1-77b05f0d` (EU region) | 0.95 | 1.00 | 1.00 | **1.00** | **1.00** | 1.00 |
| B · Prompt-only n8n batch (no retrieval, no rules) | *run `poc/poc_workflow.json`* | | | | | |

Runs on 24 Sep 2026 (`evaluation/results/offline-baseline.json`, `llm-gpt-4o-mini-v2.0.json`, `llm-gpt-4o-mini-v2.1.json`). In v2.1, 13 of 20 shipments go to a person; 7 pass as "all checks passed" (a person still approves before filing).

**Read this carefully:** v2.1 still picks a wrong code in TC16 (0.95 on HS codes). What improved is that the wrong code is now **caught**. And because the two new triggers were designed after looking at these 20 cases, **1.00 on routing is optimistic** (E6): the pilot's blind test is the real measure.

## 5. Error analysis

| # | Error | Where | Severity | What we did |
|---|---|---|---|---|
| E1 | **Our Round 1 answer key was wrong twice.** Concrete wall panels were labelled 9406.10 (prefab buildings *of wood*); correct is **6810.91**. Cement was labelled "no extra certificate"; it needs DoP + CE (EN 197-1) and is a CBAM good. | Round 1 eval plan | High (we scored the model against wrong answers) | Relabelled TC01 and TC04. In the pilot, the broker reviews every expected answer before it is used. |
| E2 | **German invoice "Betonstahl in Ringen" → 7214.20 (straight bars) instead of 7213.10 (coils).** The keyword layer did not know *Ringen* = coils. | Retrieval (offline) | Medium (wrong sub-code; routed to a person anyway: Category 3) | Added *Ringen/gerippt* to the German glossary; 7213.10 is now a top-2 candidate, so the LLM can choose it. Still wrong in offline mode: an honest limit of keyword matching. |
| E3 | **Kitchen sinks (out of scope) → 7308.90 (steel structures).** Correct is 7324.10, which is not in the knowledge base. | Retrieval | Low: confidence 0.49, the agent said "manual review" | Working as designed: the agent does not know, and it says so. Pilot: log out-of-scope products to decide whether to extend the knowledge base. |
| E4 | **7 unnecessary reviews in offline mode** (TC02, 03, 06, 09, 10, 13, 19). Safe, but each costs a person about 5 minutes. | Review rules | Low (cost, not risk) | Expected: offline mode always asks a person. Experiment C measures how many remain with the LLM. |
| E5 | **Bug found by a unit test:** "DoP missing. CE label attached." marked the CE label as *missing*, because the word "missing" from the previous sentence was read. | Intake code | High (a false "missing" or, reversed, a false "provided") | Fixed: the detector now reads only the same sentence. Regression test added. |
| E7 | **The LLM passed a vague shipment (TC14 "panels, 200 pieces").** It guessed 6811.82 (fibre-cement) with confidence 0.8 and listed no missing information → **false all-clear** in v2.0. | Recommend (LLM) | **High: the one error we design against** | v2.1: a deterministic **vagueness check** (fewer than 3 meaningful words → a person). Regression test added. |
| E8 | **The LLM's confidence is not calibrated.** It reported 0.9 on 18 of 20 cases, also on TC16 where it translated "in Ringen" correctly as "in coils" and still chose 7214.20 (straight bars) instead of 7213.10 (coils). | Recommend (LLM) | Medium | v2.1: **close-call check**: when the two best knowledge-base headings score within 15%, a person chooses. The LLM's confidence is never trusted alone. |
| E9 | **Wrong source language (v2.2, manual test 25 Sep 2026).** A photo of a Turkish cement invoice was translated correctly, but the review reason said "Translated from 'en'": the model reported the target language, and our detector missed "çimentosu" (letter ç, Turkish suffix). | Intake (translation) | Low (the shipment still went to a person) | Label now comes from our own detector; detector also catches ç and Turkish suffixes; regression test `test_translation_note_uses_detected_language`. |
| E10 | **An invalid code in our own reviewed knowledge base.** Glulam was stored as 4418.62, which does not exist in HS 2022 (correct: 4418.81, engineered structural timber). Found when the full HS 2022 list was added (v2.3). | Knowledge base | Medium (a person would have filed a non-existent code) | Fixed; new test `test_every_reviewed_code_exists_in_hs_2022` checks every reviewed code against HS 2022. |
| E6 | **Our results are probably optimistic.** The same person wrote the knowledge base keywords and the 20 test descriptions, and the v2.1 fixes were tuned on the same 20 cases. | Method | High for the business case | Pilot uses **real, anonymised I&E shipments labelled by the broker**, unseen before the test (blind test). |

## 6. What to watch in the pilot

1. **False all-clears: must stay at 0.** One is a stop signal for the pilot.
2. **Override rate** (team level): very low over weeks can mean people stopped checking (automation bias).
3. **Unnecessary review rate:** if above ~30%, the value case weakens; tune thresholds with the broker.
4. **Out-of-scope products:** which products arrive that the knowledge base does not know.
5. **Model changes:** re-run this dataset before any model update (OpenAI retires models with ~6 months' notice).
6. **Monitor alerts:** time from alert to review; stale rules must never exceed their re-check interval.

## 7. Screenshots (`evaluation/screenshots/`)

- LangSmith dataset `klarschiff-eval-v2` (20 examples)
- Experiment comparison view (A vs C, and B from n8n)
- One trace opened: `klarschiff_agent` → `recommend_llm` (prompt, candidates, JSON answer, latency, tokens)

## v2.3: universal cases (other industries)

`evaluation/dataset_universal.jsonl`: 17 shipments outside construction (semiconductor inspection tools and spare parts,
batteries, laptops, coffee, T-shirts, chairs, bicycles, plastics, aluminium profiles, pumps, cocoa, smartphones, bolts,
bearings, an export to China, one vague case). Written by the same person as the agent: optimistic, like E6.

| Run | HS exact | Routing | No false all-clear | Category |
|---|---|---|---|---|
| Offline keyword baseline (no LLM), 25 Sep 2026 | 0.75 | 1.00 | 1.00 | 0.94 |
| GPT-4o-mini | run on the Mac: `python evaluation/run_eval.py --local --dataset universal` | | | |

Every universal case goes to a person, because none of these codes is in the reviewed layer yet: this is by design.
Misses in the offline run: wafer inspection system → 9030.82 (expected 9031.41), T-shirts → 6105.10 (6109.10),
bicycle with aluminium frame → 7610.10 (8712.00): keyword search is misled by material words; the LLM step exists for this.
