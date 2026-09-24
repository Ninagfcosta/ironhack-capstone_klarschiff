# Use case definition: KlarSchiff, AI pre-shipment co-pilot

**Client:** I&E LLC (fictional SME), construction-materials import/export, operating from Germany · **Decision-maker:** Chleo (CEO)
**Version:** Round 2, 25 September 2026 · **Author:** Janaina Hoffmann

## 1. Problem

Shipment documents (commercial invoice, packing list, product certificates) are checked by hand by one person, with no checklist and no second review. Errors are **created when the documents are prepared** but **found only when customs checks them**, when the goods are already at the border. The result is customs holds of 2+ days, an estimated ~€1,500 per delay, and 30-45 minutes of manual review per shipment (figures from the SilverTrust client interview, Sept 2026, illustrative).

Two things make the problem harder in 2026:

1. **Rules differ by product category.** Cement, insulation, precast concrete, steel and timber each need different documents under different laws (CPR, CBAM, the EU steel measure, REACH, timber due diligence).
2. **Tariffs change fast.** In 2026 alone: US IEEPA tariffs ended by the Supreme Court (20 Feb) and replaced by a temporary surcharge; US Section 232 calculated on full value from 6 Apr; the EU **CBAM** definitive regime from 1 Jan; a new **EU steel measure** with a 50% out-of-quota duty from 1 Jul. A person or an AI that "remembers" old rules becomes wrong without noticing.

## 2. Company profile

SME, single-digit number of routes, imports from Türkiye, Serbia, China and others into Germany, occasional exports (e.g. steel sections to the US). Works with an external customs broker (Zollagentur), who files the declaration in ATLAS and keeps the legal responsibility. No in-house IT team.

## 3. Solution and type of AI

**KlarSchiff is a human-supervised agent** that checks a shipment *before* it leaves and prepares a review pack for the broker.

| Step | What happens | Type of AI / technique |
|---|---|---|
| 1. Intake | Reads the description, CSV lines, text PDFs and structured e-invoices (XRechnung / ZUGFeRD) | Parsing; document-status detection (regex, DE + EN) |
| 2. Validate | Compares invoice and packing list (quantities, weights, descriptions) | Deterministic rules |
| 3. Recommend | Finds candidate tariff headings in a reviewed knowledge base, then the LLM chooses one with reasons, evidence and confidence | **Retrieval-augmented generation (RAG)**: BM25 retrieval + GPT-4o-mini with structured JSON output |
| Rules | Category (1/2/3), required documents, trade measures, review triggers | Versioned rule base with legal references (not the LLM) |
| 4. Prepare | Review pack for the broker (DE/EN labels) + decision log | Template |
| 5. Monitor | Watches the US Federal Register, the USITC HTS and official EU pages; opens alerts on change | API polling + change detection |

**Classification + extraction, not decision-making.** The agent never files anything with customs.

### The three categories (Round 2 definition)

| Category | Meaning | Examples | Extra documents | Legal basis |
|---|---|---|---|---|
| 1 · Standard goods | No product-specific marking or trade measure | Untreated logs, sealants | Invoice, packing list, origin proof if a preference is claimed; SDS or timber due diligence where flagged | Union Customs Code (Reg. (EU) 952/2013), Combined Nomenclature |
| 2 · CE-marked construction products | Covered by a harmonised standard | Mineral wool, plasterboard, precast concrete, clay roof tiles, OSB | **DoP / DoPC + CE marking** | Construction Products Regulation (EU) 2024/3110 (general application from 8 Jan 2026) |
| 3 · Goods under additional trade measures | Carbon, quota, anti-dumping or US duties apply | Cement and clinker, rebar, steel sections, aluminium windows, ceramic tiles from China | CBAM declarant status + emissions data; mill certificate (melt and pour); TARIC check | CBAM Reg. (EU) 2023/956; EU steel measure Reg. (EU) 2026/1384; anti-dumping basic Reg. (EU) 2016/1036; US Section 232 |

A product can trigger several rules; the highest category wins. Example: **Portland cement** needs DoP + CE (EN 197-1) **and** is a CBAM good, so it is Category 3.

### E-invoicing

Germany requires every business to **receive** EN 16931 e-invoices since 1 Jan 2025 and to **issue** them from 2027 (turnover > €800k) and 2028 (all). The EU ViDA package makes cross-border B2B digital reporting mandatory from 1 Jul 2030. KlarSchiff already reads e-invoice XML lines, so Intake needs no OCR for these invoices: fewer reading errors, more reliable validation.

## 4. Stakeholders

| Stakeholder | Role | What they need from KlarSchiff |
|---|---|---|
| Logistics team (2-3 people) | Daily users | Fast, clear checklist; fewer surprises at the border |
| Customs broker | Files the declaration; legal responsibility | A clean review pack with sources |
| Chleo (CEO) | Buys the pilot | Transparency, measurable value, low risk |
| Works council (if any) | Co-determination on tools that can monitor staff | Team-level metrics only (§87(1) no. 6 BetrVG) |
| Data protection officer | GDPR | DPA with the AI vendor, data minimisation |

## 5. Success metrics (measured in the pilot)

| Metric | Baseline (illustrative) | Pilot target |
|---|---|---|
| Customs holds caused by documentation errors | weekly | **-50%** |
| Manual review time per shipment | 30-45 min | **< 10 min** |
| HS code suggestions accepted without change (6-digit) | n/a | **≥ 90%** |
| False all-clears (a shipment that needed review was passed) | n/a | **0** (hard limit) |
| Documents complete at first submission | ~70% | **95%** |

## 6. Out of scope

- Filing customs declarations or talking to ATLAS. A person always files.
- Final legal classification advice (the broker and, where needed, a Binding Tariff Information / vZTA decide).
- Goods outside construction materials (the agent says so and routes them to a person).
- Scanned documents without text (OCR is a pilot extension).
- Duty-rate calculation: the agent links to the live TARIC / HTS for the shipment date instead of storing rates.

## 7. How the use case evolved from Round 1 to Round 2

| Topic | Round 1 | Round 2 |
|---|---|---|
| Build | n8n, 3 nodes, one prompt | Python agent (5 steps) + Streamlit MVP + n8n batch POC |
| Knowledge | Model memory only | Reviewed knowledge base (50 headings) + versioned rules with legal references and dates |
| Categories | Fixed by product type | Decided by rules; multiple rules per product |
| Tests | 5 cases, scored by hand | 20 cases (safety, German, mismatch, out-of-scope, US export), automated evaluators, LangSmith |
| Errors | "0 Fail" | Error analysis: wrong answer keys found in Round 1, real agent errors documented |
| Tariff changes | Not handled | Monitor step with alerts; answers show data date |
| Human control | Described | Built: approve / correct / reject + audit log + override rate |
