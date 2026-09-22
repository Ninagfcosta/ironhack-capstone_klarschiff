# Use Case Proposals

**Client:** I&E LLC — mid-sized import-export company, construction materials sector, multiple international shipping routes, works routinely with customs brokers and carriers.

**Client's stated fear (the "Chleo" framing):** AI is not transparent — "what is the AI, and how would I even sign up for it?"

Per teaching-staff guidance from the Round 1 check-in, this document leads with the primary use case in depth, then covers two alternatives that were considered and explicitly ruled out — rather than developing three full use cases in parallel.

---

## Primary use case: Pre-Shipment Document Check & HS Code Suggestion

### Problem
Shipment documents (invoice, packing list, product data) are checked by hand, one person at a time, with no systematic pre-validation. Mismatches and misclassifications are typically caught only after the shipment is already moving — at which point the fix is a customs hold, not a quick edit.

### Company profile
I&E LLC — SME, construction materials import/export, multiple routes, routine coordination with customs brokers and carriers. Cross-border compliance is part of daily operations, not a rare event.

### Proposed AI solution
A five-step, human-supervised workflow: **Intake → Validate → Recommend → Prepare → Monitor**. The AI reads and cross-checks documents, flags mismatches, and suggests an HS code with its source — a human approves every step before anything moves forward. This is a **classification + extraction** capability (document parsing via OCR/LLM, semantic search for tariff matching), not a decision-making or filing system.

### Shipment categories (per teaching-staff feedback: understand what each category needs and how they differ)

| Category | What it needs | How it differs | Legal basis |
|---|---|---|---|
| **1. Bulk / raw construction materials** (e.g., sand, aggregate, raw timber) | Commercial invoice + packing list + correct HS/CN code | Lowest documentation complexity; main risk is code misclassification, not missing paperwork | General EU Customs Code / Combined Nomenclature classification rules |
| **2. CE-marked construction products** (e.g., prefabricated panels, insulation, fixtures) | Declaration of Performance (DoP) + CE marking evidence + technical-specification compliance | Substantially higher documentation burden; a missing DoP blocks clearance regardless of correct HS code | EU Construction Products Regulation, Regulation (EU) 2024/3110 (published 18 Dec 2024; general application from 8 Jan 2026) |
| **3. Products under additional trade measures** (e.g., steel/aluminum content, REACH-regulated substances) | Extra certificates; possible quota or anti-dumping duty checks | Highest customs-hold risk; needs the most careful human review, not more automation | EU trade-defence measures / REACH Regulation (EC) 1907/2006 |

### Electronic invoice (e-invoicing) impact on this process
Under the EU's ViDA package (adopted 11 March 2025, in force 14 April 2025), structured e-invoicing is being phased in, becoming mandatory for cross-border B2B digital reporting from **1 July 2030**. Once I&E LLC's invoices arrive as structured e-invoices rather than PDFs, the "Intake" step of this workflow can consume the invoice fields directly instead of relying on OCR — reducing extraction error and making the "Validate" step more reliable over time. This is noted here as a forward-looking design consideration and will be developed further as a Strategic Plan milestone in Round 2.

### Key stakeholders
- Logistics/operations team (daily users, resolve flagged exceptions)
- Customs broker (receives the review pack; retains legal filing responsibility)
- Company leadership / Chleo-equivalent decision-maker (funds the pilot, wants transparency)
- Regulatory/compliance function (EU AI Act + GDPR obligations)

### Success criteria (measurable)
1. Reduce customs-hold incidents linked to documentation errors by **≥50%** during the pilot, compared to the pre-pilot baseline.
2. Reduce manual document-review time from an estimated **30–45 minutes** to **under 10 minutes** per shipment.
3. (Secondary) Reach **≥90% HS-code suggestion accuracy** at the pilot's product family scope, benchmarked against approved past classifications.

### Out of scope
- Not filing customs paperwork automatically — a person always sends it.
- Not replacing the customs broker relationship or the team's judgment.
- Not covering every route or product category on day one — the pilot starts with one route and one product family.
- Not going live with real filings before the pilot review.

---

## Alternative 1 (considered, ruled out): Automated Customs Filing Agent
**Idea:** extend the tool to file customs declarations directly, removing the human step entirely.
**Why ruled out:** shifts legal filing responsibility onto an AI system with no clear liability model; EU AI Act and GDPR exposure both increase sharply; the client's stated fear is specifically about *trust and transparency* — full automation is the opposite of the reassurance needed at this stage. Kept for a possible Round 2/pilot-plus-one phase only if the human-supervised version proves reliable first.

## Alternative 2 (considered, ruled out): Predictive Customs-Delay Forecasting
**Idea:** an AI model that predicts, before a shipment leaves, the probability it will be held at customs.
**Why ruled out:** harder to validate honestly in a short pilot (needs historical outcome data I&E LLC doesn't yet have structured), and it treats the symptom (predicting delay) rather than the root cause (bad documentation) the client actually described in the interview. The document-check use case directly addresses what the client told us was happening; forecasting would require an assumption leap we can't yet support with real data.

---

## Data sources used in this document

| Claim | Source | Year |
|---|---|---|
| CPR requirements & CE-marking obligation | Official Journal of the EU / prodlaw.eu | Published 2024, applies from 2026 |
| ViDA e-invoicing mandate & dates | European Commission, Taxation and Customs Union | Adopted 2025, phased through 2030 |
| Manual review time (30–45 min), delay cost (~€1,500), frequency (weekly) | SilverTrust Brief Project client interview exercise (illustrative — see `cost_estimation/cost_analysis.md`) | Sept 2026 |
