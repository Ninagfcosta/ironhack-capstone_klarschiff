# Round 1 decision: KEEP the use case, CHANGE how it is proven

**Date:** 25 September 2026 · **Author:** Janaina Hoffmann · **Decision:** **KEEP** (same client, same use case), with five changes.

## 1. Feedback received

| When | From | Feedback (summary) |
|---|---|---|
| 19 Sep 2026 (1:1) | Teaching staff | Go deeper on **2-3 shipment categories**: what each needs, how they differ, **legal references**, and how **e-invoicing** affects the process. |
| 19 Sep 2026 (1:1) | Teaching staff | Show the **data source and the year** of every number. |
| 19 Sep 2026 (1:1) | Teaching staff | On testing: **the more test cases, the better.** |
| 24 Sep 2026 (Round 1 presentation) | Teaching staff | **A machine is never perfect: show at least one error.** A result with zero failures is not credible. |
| 24 Sep 2026 (own analysis) | Janaina | **Tariffs change fast** (US tariff changes, new EU steel measure, CBAM). The Round 1 POC had no way to notice. |

## 2. Decision

**KEEP** the pre-shipment document check + HS code suggestion for I&E LLC. The Round 1 evidence supports it: the two safety cases (missing DoP, oversized steel shipment) worked, and the client's main fear, *"AI is not transparent"*, is still best answered by a human-in-the-loop co-pilot that shows its sources.

## 3. What changes in Round 2

| # | Change | Why | Where |
|---|---|---|---|
| 1 | From a 3-node prompt to a **real agent**: retrieval over a reviewed tariff knowledge base (RAG), rule engine with legal references, invoice vs packing-list check, LLM with structured output, offline fallback | The Round 1 POC answered from model memory; fine sub-codes were wrong (2 Partial) | `klarschiff/` |
| 2 | **Categories are now decided by rules**, and a product can trigger several (e.g. cement = CE-marked product **and** CBAM good) | Teacher feedback + research: Round 1 treated cement as "no extra document"; it is covered by EN 197-1 and CBAM | `klarschiff/knowledge/`, `use_case_definition.md` |
| 3 | **5 → 20 test cases**, automated evaluators, LangSmith experiment, **error analysis** | "The more tests the better" + "show at least one error" | `evaluation/` |
| 4 | New **Monitor** step: watches official US and EU sources and raises alerts; every answer shows its data date | Tariff volatility | `klarschiff/monitor.py` |
| 5 | A working **MVP** (Streamlit) with approve / correct / reject and an audit log | Round 2 requirement; makes the human decision visible | `mvp/` |

## 4. What Round 1 got wrong (and we now say so)

- **Two Round 1 "expected answers" were wrong, not the model.** Case 4 expected HS 9406.10 (prefabricated buildings *of wood*) for concrete wall panels; the correct code is **6810.91**. Case 1 expected "no extra certificate" for cement; cement needs **DoP + CE** (EN 197-1) and falls under **CBAM**. The Round 1 model flagged a missing certificate and was closer to right than our answer key.
- **Lesson:** the answer key itself needs review by a customs professional. In the pilot, every expected answer is checked by the broker before it is used to score the agent.

## 5. What stays the same

Client (I&E LLC, CEO Chleo), sector (construction-materials import/export), the five-step workflow (Intake → Validate → Recommend → Prepare → Monitor), the rule that **the AI suggests and a person decides**, and the pilot scope (one route, one product family, three months).
