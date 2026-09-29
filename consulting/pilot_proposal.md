# Pilot proposal: master-list continuity and pre-shipment checks (fictional scenario)

**For:** I&E LLC (fictional client) and its customs broker · **By:** Janaina Hoffmann
**Status:** proposal for discussion · all data in this document is fictional

## 1. Why a pilot
Technology can assist the customs process; it cannot replace compliance judgment. KlarSchiff is built that way. This module pilot is part of the 3-month pilot in `strategic_plan.md` and proves value on I&E's own (anonymised) data before any subscription.

## 2. Scope (4–6 weeks)
| In scope | Out of scope |
|---|---|
| One client's product master list (anonymised export, e.g. 2,000–10,000 lines) | Filing declarations, connecting to ATLAS / ACE |
| One route (e.g. US → DE) and one product family | Export-control determinations (flagged only) |
| Batch check + master-list import, run by the consultant on an EU server | Access to personal data (not needed) |

## 3. Plan
| Week | Activity | Output |
|---|---|---|
| 0 | NDA and data-processing agreement; data export defined with the team | signed documents, field list |
| 1 | Import the master list; conflict report (same product, different codes; missing German descriptions) | conflict list for the team |
| 2 | Blind test: 100–200 lines labelled by your broker **before** the agent runs | accuracy at 6 and 8 digits, false all-clears |
| 3–4 | Shadow mode: the team works as usual; KlarSchiff runs in parallel on new part numbers | time per line, re-classifications avoided |
| 5–6 | Results, go / no-go, recommendation | report + workshop |

## 4. Success criteria (go / no-go)
- **No risky line passes without a person** (zero tolerance for false all-clears in the blind test; any case found → no-go until fixed).
- ≥ 90 % of suggested codes accepted at 6 digits; 8-digit line accepted or correctly marked "person chooses".
- ≥ 30 % of new part numbers matched to an existing product (no re-classification needed).
- Every conflict in the imported list reviewed and resolved by the team.

## 5. Data and security
- Only product data (part number, description, code). No personal data. EU hosting, password or API key, daily backup.
- AI provider under a data-processing agreement; an EU provider (e.g. Mistral) can be switched on and re-tested.
- Hidden instructions in documents are detected and ignored (prompt-injection guard); rules and review triggers sit outside the AI.

## 6. Price (indicative)
| Item | Price |
|---|---|
| Pilot (4–6 weeks, one master list, one route) | €10,000–15,000 one-off |
| After a "go": subscription S / M | €2,000 / €3,500 per month (by volume), incl. rule updates and monitor |
| AI tokens | at cost, ≈ $0.0005 per checked line (GPT-4o-mini, Sep 2026 list price) |

## 7. Risks and how the pilot handles them
| Risk | Handling |
|---|---|
| Scores in the capstone are optimistic | Blind test on your labelled lines is week 2, before any claim |
| Descriptions too vague ("parts") | Flagged as vague → person; report shows which clients send poor descriptions |
| Rules change during the pilot | Daily monitor; every rule has a last-verified date |
| People stop checking (automation bias) | Override rate tracked per team, not per person (§87 BetrVG) |

## 8. What we need from you
A contact in customs / trade compliance, an anonymised master-list export, 2 hours of a licensed broker for the blind-test labels, and a 30-minute weekly check-in.
