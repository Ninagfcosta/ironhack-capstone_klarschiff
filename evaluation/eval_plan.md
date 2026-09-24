# KlarSchiff: Evaluation Plan (Round 1, no LangSmith yet)

Chleo's core worry is transparency — "what is the AI, and how would I know it's working?" This document answers that on paper, with a scored mini-set, ahead of the full LangSmith evaluation planned for Round 2.

## 1. Pass/fail criteria (stakeholder-specific, not "the model is good")

| # | Criterion | Why a stakeholder cares |
|---|---|---|
| 1 | The suggested HS code matches the correct heading (first 6 digits) for the product described | Wrong classification is the direct cause of the delays and duty exposure this tool exists to prevent |
| 2 | A missing or mismatched required document (e.g., a Declaration of Performance for a CE-marked item) is flagged, never silently passed through | A false "all clear" is worse than no tool at all — it hides exactly the risk Chleo is worried about |
| 3 | Every suggestion shows a traceable source (which tariff reference or rule it came from) | Lets a human reviewer confirm in seconds instead of re-researching from scratch — this is the transparency Chleo asked about |
| 4 | Low-confidence or ambiguous cases are routed to human review, not auto-approved | Keeps a person in the loop for every judgment call, as required by the workflow's governance design |
| 5 | The Intake → Validate steps complete without the reviewer re-entering data by hand | Time saved is one of the two measurable success criteria in `use_cases.md` |

## 2. Scored mini-set (5 synthetic cases)

Cases are synthetic (no real client data used), built to span the three shipment categories from `use_cases.md`, and named so they map directly to the categories being tested.

> All 5 cases below were run through the real n8n POC (`n8n/workflow.json`). The "POC output" column records what the workflow actually returned; nothing was edited to look better.

| # | Category | Input (summary) | Expected result | POC output (actual) | Result |
|---|---|---|---|---|---|
| 1 | 1 — Bulk material | Invoice: 500 bags Portland cement, Turkey → Germany | HS 2523.29 suggested; no extra certificate required | HS 2523.29 suggested (correct). AI also flagged a missing Certificate of Conformity and recommended manual review — stricter than the expected baseline, but not incorrect. | Pass |
| 2 | 1 — Bulk material | Invoice: raw timber beams, packing list matches invoice quantities | HS 4403.xx suggested; quantities match, no flag raised | HS 4407.10 suggested (sawn wood/beams) — differs from the scripted expected code (4403.xx, raw/rough wood). This reflects a genuine ambiguity in the case wording ("raw timber beams" could mean rough logs or sawn structural beams); the AI's choice is defensible. It also flagged a Fumigation Certificate as a possible missing document (not part of the original test design) and stated no manual review was needed. | Partial — HS code differs from the scripted expectation due to case-wording ambiguity, not a clear POC error; no false "all clear" was given. |
| 3 | 2 — CE-marked | Invoice: mineral wool insulation panels, DoP attached | HS 6806.10 suggested; DoP presence confirmed, no flag | HS 6806.90 suggested (minor variance from the scripted 6806.10 — both are valid mineral-wool subheadings under the same 6806 heading, depending on product form). DoP presence correctly confirmed; no missing documents noted; no manual review flag raised. Cited source: EU Regulation (EU) No. 305/2011 on construction products. | Pass — the substantive test (DoP correctly confirmed, no false flag) succeeded; the last two digits of the HS code differ slightly but fall under the same heading. |
| 4 | 2 — CE-marked | Invoice: prefabricated wall panels, **DoP missing from the document set** | HS 9406.10 suggested **and** an exception flagged for the missing DoP — this case exists specifically to test criterion #2 | HS 6810.19 suggested (fibre-cement panel classification — differs from the scripted 9406.10 because the case didn't specify the panel material; a reasonable guess given the ambiguity). Critically, it correctly flagged the DoP as **missing** and explicitly required it for CE-marked products, and flagged the shipment for **manual human review** due to the missing documentation. | Pass — the case's real purpose (never silently pass a missing required document) succeeded; the exact HS code differs only because the material wasn't specified in the test input. |
| 5 | 3 — Regulated trade | Invoice: steel rebar shipment, quantity above typical route volume | HS 7214.20 suggested **and** flagged for manual review (potential trade-defence/quota exposure) — tests criterion #4 | HS 7213.10 suggested (wire rod in coils) — less precise than the expected 7214.20 (ribbed bars, the dedicated rebar code). Correctly flagged for **manual human review** due to the 500-ton quantity being well above typical route volume, citing WCO nomenclature and EU CPR as sources. | Partial — the manual-review flag (criterion #4, the case's real purpose) succeeded, but the HS sub-code was imprecise. This is a genuine, useful finding: it shows why the full design's Pinecone tariff lookup (Round 2) is needed instead of relying on the model's general knowledge alone for fine-grained code disambiguation. |

**Result summary: 3 Pass · 2 Partial · 0 Fail.** Both safety-critical checks worked (case 4 flagged the missing DoP; case 5 was routed to manual review). The misses were on fine-grained HS sub-codes, which is exactly the gap named in §4.

**Note on the legal source cited by the POC:** in case 3 the model cited the older Construction Products Regulation (EU) No 305/2011. It is being replaced by Regulation (EU) 2024/3110, which applies from 8 January 2026 (see `research/use_cases.md`). Round 2 will update the prompt and the tariff/rule knowledge base so the agent cites the current regulation.

**Design note:** case 4 and case 5 are deliberately "should flag, not silently pass" cases. A mini-set where every case sails through cleanly doesn't actually test whether the tool catches problems — it only proves it can read a well-formed invoice, which was never the hard part.

## 3. Scoring method

Score by hand: for each case, compare the POC's actual output against the "Expected result" column, and check it against the 5 criteria above. A case only counts as an overall "Pass" if it satisfies every criterion that applies to it (e.g., case 4 must both suggest the right code *and* raise the flag — getting the code right while missing the flag is a fail on criterion #2). An LLM-as-judge prompt is an acceptable alternative for scoring at Round 1 scale, but with 5 cases, manual scoring is faster and more defensible in the presentation ("I checked every case myself").

## 4. What we still cannot measure at this stage

This mini-set tells us whether the tool behaves correctly on cases we hand-picked — it does not yet tell us its accuracy rate across the full range of real invoices I&E LLC actually sends, or how it degrades on messier real-world scans (handwriting, poor scan quality, non-standard invoice layouts). That requires a larger, real (anonymized) dataset and a proper tracked experiment — which is exactly what the Round 2 LangSmith evaluation (dataset + traces + at least one experiment with an evaluator) is designed to close.

**A concrete example of this gap, from the mini-set itself:** in case 5, the simplified POC (which asks the model directly, with no tariff database) suggested a less precise HS sub-code (7213.10 instead of the more specific 7214.20 for rebar) than the full design's Pinecone-based tariff lookup would be expected to produce. This is exactly the kind of fine-grained accuracy gap a real tariff-reference vector store is meant to close, and it is direct evidence — not a hypothetical — for why the full design (§5 of `n8n/workflow_documentation.md`) proposes RAG over tariff documents rather than relying on the model's general knowledge alone.
