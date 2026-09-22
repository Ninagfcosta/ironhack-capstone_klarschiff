# KlarSchiff POC: n8n Workflow Documentation

**Project:** KlarSchiff, AI-assisted pre-shipment document check & HS code suggestion
**Round:** 1 (proof of concept) · **Author:** Janaina Hoffmann · **Last updated:** 2026-09-22

> *KlarSchiff* comes from the German "Klar Schiff": the ship is ready and everything is in order. *Klar* also means "clear": the tool's job is to make every suggestion clear and checkable by a human.

## 1. What the POC does

The Round 1 POC runs the **"Recommend"** step of the full KlarSchiff design on its own: it takes a short shipment description and returns, in plain language:

1. A suggested **HS code** (first 6 digits) and the **shipment category** (bulk material / CE-marked product / product under additional trade measures)
2. The **documents required** for that category
3. A flag if a required document **seems to be missing**
4. A flag if the shipment should go to **manual human review**
5. The **rule or source** the suggestion is based on, so a person can verify it in seconds

The AI **suggests**; it never decides and never files anything with customs.

## 2. The real workflow (3 nodes)

`workflow.json` in this folder is the exact export of the workflow that was built and run.

```
[Manual Trigger] ──► [Edit Fields (Set)] ──► [OpenAI: Message a model]
 "Execute workflow"     invoice_text            GPT-4o-mini + structured prompt
```

| # | Node (n8n name) | Type | What it does |
|---|---|---|---|
| 1 | When clicking 'Execute workflow' | Manual Trigger | Starts the run on demand (demo mode) |
| 2 | Edit Fields | Set | Holds the test input in a field called `invoice_text` (one of the 5 synthetic cases from `evaluation/eval_plan.md`) |
| 3 | Message a model | OpenAI (GPT-4o-mini) | Sends `invoice_text` inside a fixed 5-point prompt (see §3) and returns the answer |

## 3. The prompt (node 3)

```text
You are a customs pre-shipment assistant for a construction-materials import/export company.

Given the shipment description below:
1. Suggest the HS code (first 6 digits) and name which category it falls into: (1) Bulk/raw construction material, (2) CE-marked construction product, or (3) product under additional trade measures.
2. State which documents are required for that category (e.g., a Declaration of Performance for CE-marked items).
3. Explicitly flag if a required document appears to be missing from the description.
4. Flag if this shipment should go to manual human review (e.g., unusually high quantity, regulated material).
5. State the rule or source your suggestion is based on, so a human can verify it in seconds.

Shipment description: {{ $json.invoice_text }}
```

Each numbered instruction maps to one pass/fail criterion in `evaluation/eval_plan.md`, so the output can be scored directly.

## 4. Why these tools

| Tool | Why |
|---|---|
| **n8n** | Visual, low-code, inspectable: a non-technical stakeholder can see every step. Fits an SME with no in-house engineering team |
| **GPT-4o-mini** | Low cost per call, good enough for a first test of classification + document reasoning |
| **Manual Trigger + Set node** | The simplest way to run the same controlled test cases again and again |

## 5. POC vs. full design (honest scope)

The full consulting proposal is a five-step, human-supervised workflow:

**Intake → Validate → Recommend → Prepare → Monitor**

| Step | In the Round 1 POC? | Planned for |
|---|---|---|
| Intake (read PDF invoices / packing lists, OCR) | ❌ Text is typed into the Set node | Round 2 / pilot |
| Validate (cross-check invoice vs. packing list) | ❌ | Round 2 / pilot |
| **Recommend (HS code + documents + flags + source)** | ✅ **This is the POC** | — |
| Prepare (review pack for the customs broker) | ❌ | Pilot |
| Monitor (tariff/rule changes) | ❌ | Full deployment |

**Known limitations of this POC**

- The model answers from **general knowledge only**. There is no tariff database (RAG) yet, so fine-grained sub-codes can be imprecise (see case 5 in the eval plan).
- The input is **short synthetic text**, not real scanned documents.
- There is **no automatic logging or tracing** yet. That arrives in Round 2 with LangSmith.
- One case is run at a time, by hand.

## 6. How to reproduce

1. In n8n (cloud or self-hosted): **Workflows → Import from file** → select `n8n/workflow.json`.
2. Open the **Message a model** node and connect your own OpenAI credential (the export contains only a credential *reference*, never the API key).
3. Open **Edit Fields** and paste one of the 5 case inputs from `evaluation/eval_plan.md` into `invoice_text`.
4. Click **Execute workflow**.
5. Compare the answer with the "Expected result" column in the eval plan and score it against the 5 criteria.

## 7. Demo recording

_Link to the 2–5 minute demo recording (trigger → result, narrated) will be added here._
