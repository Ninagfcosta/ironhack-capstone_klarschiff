# ⚓ KlarSchiff: AI pre-shipment co-pilot

**HS code suggestion · document check · tariff monitor, for construction-materials import/export**
AI Consulting Capstone · Ironhack AI Consulting & Integration Bootcamp · **Author:** Janaina Hoffmann (Berlin)
**Status:** Round 1 presented 24 Sep 2026 · **Round 2 (final) 10 Oct 2026**

> **Why "KlarSchiff"?** In German, *"Klar Schiff"* means the ship is ready and everything is in order. *Klar* also means **clear**: every suggestion must be clear enough for a person to check it in seconds. That answers the client's biggest fear: *"AI is not transparent."*
>
> 🌱 **Origin:** born in **Project 4 · SilverTrust**, a pair consulting exercise with my classmate Asal (logistics client) → [`00_origin_silvertrust/`](00_origin_silvertrust/)
> 🧭 [Module 1](https://github.com/ninagfcosta/ironhack-module-1_ai-foundations_podcast-studio) → [Module 2](https://github.com/ninagfcosta/ironhack-module-2_python-apis_content-creator) → [Module 3](https://github.com/ninagfcosta/ironhack-module-3_rag-agents_company-research) → [Module 4 · SilverTrust](https://github.com/ninagfcosta/ironhack-module-4_evaluation-compliance_silvertrust) → **Capstone · KlarSchiff**

---

## 1. The problem

**I&E LLC** (fictional SME, construction materials) checks shipment documents by hand. Errors are **created when documents are prepared** but **found only at customs**, when the goods are already at the border: holds of 2+ days, ~€1,500 per delay, weekly (illustrative, SilverTrust interview, Sept 2026).

And the rules keep moving: EU **CBAM** since 1 Jan 2026, a new **EU steel measure** (50% out-of-quota duty) since 1 Jul 2026, US tariffs changed several times in 2025-2026 (IEEPA tariffs ended by the Supreme Court on 20 Feb 2026, Section 232 recalculated from 6 Apr 2026).

## 2. The solution

A **human-supervised agent** that checks a shipment before it leaves:

```mermaid
flowchart LR
    A[1 Intake<br/>text, CSV, PDF, e-invoice] --> B[2 Validate<br/>invoice vs packing list]
    B --> C[3 Recommend<br/>RAG + LLM]
    C --> R[Rules<br/>category, documents, measures]
    R --> D[4 Prepare<br/>review pack + log]
    M[5 Monitor<br/>US + EU sources] -. alerts .-> R
    D --> H{Person decides}
```

**The AI suggests; a person decides. Nothing is ever filed automatically.**

## 3. Try it (5 minutes)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add your own OPENAI_API_KEY and LANGSMITH_API_KEY (never commit .env)
python -m pytest -q             # 16 offline tests
streamlit run mvp/app.py        # the MVP (works offline too, in keyword mode)
python evaluation/run_eval.py --langsmith   # 20-case LangSmith experiment
python -m klarschiff.monitor    # tariff monitor (also runs daily via GitHub Actions)
```

## 4. Deliverables

### Round 2 (final)

| Deliverable | File | Highlights |
|---|---|---|
| Round 1 decision | [`feedback/round1_decision.md`](feedback/round1_decision.md) | KEEP the use case, 5 changes, 2 wrong Round 1 answer keys admitted |
| Use case definition | [`use_case_definition.md`](use_case_definition.md) | 3 categories with legal basis, e-invoicing, metrics, out of scope, R1 → R2 evolution |
| POC | [`poc/`](poc/) | n8n batch POC v2 (20 cases, prompt-only baseline) + agent architecture |
| **MVP** | [`mvp/`](mvp/) · [`klarschiff/`](klarschiff/) | Streamlit app, 5-step agent, RAG over 50 reviewed headings, versioned rules, tariff monitor, audit log |
| **LangSmith evaluation** | [`evaluation/langsmith.md`](evaluation/langsmith.md) | 20 cases, 6 evaluators, **error analysis (8 errors found, incl. a real LLM false all-clear)** |
| ROI & risks | [`roi_risk_assessment.md`](roi_risk_assessment.md) | 3 scenarios, break-even month 7 (base), 12 risks |
| EU AI Act | [`compliance/eu_ai_act_compliance.md`](compliance/eu_ai_act_compliance.md) | Minimal risk, reasoning step by step, Digital Omnibus 2026 dates |
| GDPR | [`compliance/gdpr_documentation.md`](compliance/gdpr_documentation.md) | Data flow, legal bases, DPIA screening, transfers, retention |
| Strategic plan | [`strategic_plan.md`](strategic_plan.md) | Pilot with go/no-go criteria, German go-to-market via customs brokers, pricing |

### Round 1

| Deliverable | File |
|---|---|
| Sector research, opportunities & risks, use cases | [`research/`](research/) |
| Charts (5 + ROI scenarios) | [`charts/`](charts/) |
| n8n POC (3 nodes) | [`n8n/`](n8n/) |
| Eval plan (5 cases) | [`evaluation/eval_plan.md`](evaluation/eval_plan.md) |
| Cost & timeline | [`cost_estimation/`](cost_estimation/) |

## 5. Repository structure

```
.
├── klarschiff/            # the agent: intake, validate, retrieval, recommend, rules, monitor, report
│   └── knowledge/         # hs_headings.json (50 headings), trade_measures.json (versioned rules + sources)
├── mvp/                   # Streamlit app + sample data + documentation
├── evaluation/            # dataset (20 cases), evaluators, runner, LangSmith doc, results
├── poc/                   # n8n batch POC v2
├── compliance/            # EU AI Act, GDPR
├── tests/                 # 16 unit tests (offline)
├── data/                  # decision log, monitor state, alerts (created at runtime)
├── .github/workflows/     # daily tariff monitor
├── research/ charts/ n8n/ cost_estimation/ feedback/ 00_origin_silvertrust/
└── use_case_definition.md · roi_risk_assessment.md · strategic_plan.md
```

## 6. Honesty notes

- Money figures are **illustrative** (client-interview exercise); the pilot replaces them with measured values.
- All test shipments are **synthetic**; no real client or personal data.
- The knowledge base covers **50 construction-material headings** and must be re-verified by a licensed customs professional. Duty rates are **linked live** (TARIC, EZT-online, HTS), not stored.
- The same author wrote the tests and the knowledge base, so scores are **likely optimistic**; the pilot includes a blind test labelled by the broker.
- **Change rule:** re-run `evaluation/run_eval.py` before changing the model, the prompt or the rules.
