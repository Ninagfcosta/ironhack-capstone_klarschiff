# Opportunity & Risk Mapping

## 1. Opportunity mapping

| Opportunity | Description | Evidence |
|---|---|---|
| Pre-shipment validation | Catch document mismatches before the shipment leaves, not after it is held at customs | Client interview: manual checks only catch mismatches "too late" (SilverTrust exercise) |
| HS code assistance with traceable sourcing | Suggest a classification and show its source, so a human reviewer can confirm quickly instead of researching from scratch | Matches the "closest competitor" pattern (GingerControl) at a fraction of the engagement cost |
| Structured-data readiness | Position the tool to consume structured e-invoice data as ViDA-driven e-invoicing mandates phase in (from 2025, mandatory cross-border B2B from 2030) | European Commission, ViDA (2025) |
| Category-aware processing | Route CE-marked / regulated-construction-product shipments (Category 2, `use_cases.md`) into a stricter documentation checklist automatically | EU Construction Products Regulation, Reg. (EU) 2024/3110 (applies from 8 Jan 2026) |
| SME-sized entry point | Serve a company too small for enterprise trade-compliance suites (Thomson Reuters, SAP GTS, Descartes) | Competitive landscape, `sector_research.md` §3 |

## 2. Risk mapping

Risks are grouped into the four categories the Round 2 rubric will ultimately require (regulatory, technical, ethical, operational) so this doubles as a head start on that later deliverable.

| # | Risk | Category | Likelihood (1-5) | Impact (1-5) | Level | Mitigation |
|---|---|---|---|---|---|---|
| 1 | Model misclassifies a rare/edge-case HS code | Technical | 3 | 4 | 12 – High | Human approves every classification before filing (already built into the 5-step workflow); low-confidence cases are flagged, not guessed |
| 2 | Regulatory uncertainty — EU AI Act classification could shift as guidance matures | Regulatory | 2 | 4 | 8 – Medium | Re-check classification against Article 6 guidance at each project milestone; document reasoning, not just the label |
| 3 | Automation bias — reviewers start rubber-stamping AI suggestions without real scrutiny | Ethical | 3 | 4 | 12 – High | Track override/correction rate per reviewer; periodic spot-audits of approved classifications |
| 4 | Model/data drift as tariff schedules or supplier mix change over time | Technical | 3 | 3 | 9 – Medium | Scheduled review of tariff source freshness; re-validate the eval set periodically, not just at launch |
| 5 | Disconnected data sources (invoice, packing list, product data in separate files) reintroduce manual reconciliation | Operational | 3 | 3 | 9 – Medium | Pilot scope intentionally starts with one route/product family to prove the integration before scaling |
| 6 | Personal data exposure in shipping documents (names, addresses, IDs) mishandled by the AI pipeline | Regulatory / Ethical | 2 | 4 | 8 – Medium | Data processing agreement with any AI vendor; extract only the fields needed for the check; retention limits |
| 7 | Over-reliance on illustrative research numbers if not replaced with real client data before scaling | Operational | 3 | 2 | 6 – Low | Flag all illustrative figures explicitly (done throughout this repo); replace with real records before the Round 2 business case |

**Prioritization logic:** risks #1 and #3 (both scoring 12) are the two to lead with in the Round 1 pitch — they are the ones a CEO or ops lead would ask about first ("what if the AI is wrong?" and "will my team actually still check it?"). Both already have a structural mitigation (human-in-the-loop, tracked override rate) rather than a vague promise.

## 3. Note on scope

This mapping intentionally excludes filing-automation risk (e.g., liability for an incorrect customs declaration) because the proposed solution never files anything automatically — a human always reviews and files. That boundary is documented explicitly in `use_cases.md` under "Out of scope."
