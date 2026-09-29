# KlarSchiff · One-pager

**AI pre-shipment co-pilot for customs teams: clear answers, human decisions.**
Janaina Hoffmann · AI Consultant · Berlin · capstone project, Ironhack AI Consulting & Integration (Oct 2026)
*Client: I&E LLC (fictional). All names and data in this project are fictional.*

## The problem
- **Errors are made at the desk and found at the border.** A wrong HS code or a missing document surfaces at customs, when the goods are already waiting (illustrative: 2+ days, ~€1,500 per hold).
- **The rules keep moving.** In 2026 alone: CBAM definitive regime (1 Jan), new Construction Products Regulation (8 Jan), US Supreme Court on IEEPA tariffs (20 Feb), Section 232 on full value (6 Apr), EU steel measure (1 Jul), EUDR from 30 Dec.
- **Part numbers change, the product does not.** Master lists keyed by part number lose the approved code when a revision or a new supplier creates a new number. The same product is classified again, sometimes with a different code: an audit risk.

## The solution
| Step | What KlarSchiff does |
|---|---|
| Intake | Reads text, PDFs, scans and photos, e-invoices (XRechnung/ZUGFeRD); translates Turkish or Chinese; ignores hidden instructions to the AI |
| Master list | Known product (even with a new part number) reuses its approved code and German description; conflicts in the old list are found on import |
| Recommend | Searches all 5,613 HS 2022 codes, suggests the 8-digit CN / US HTS line, shows similar official rulings; GPT-4o-mini picks with reasons |
| Rules | Versioned rule packs with legal references: CE (construction, machinery, electrical, batteries), CBAM, steel, trade defence, export control, food/plants, EUDR |
| Monitor | Watches US and EU official sources daily; an open alert sends affected shipments to a person |
| A person decides | Approve, correct or reject; every decision logged; nothing is filed automatically |

## Proof (honest numbers)
- 20 construction cases, real GPT-4o-mini runs (24 Sep 2026): 0.95 exact 6-digit codes; with two added review rules, every case that needed a person was sent to one. Tuned on the same cases, so optimistic.
- 17 cases from other industries: keyword-only baseline 0.75 exact codes; all routed to a person because none of those codes is reviewed yet.
- 10 errors found and documented (E1–E10), each with a fix and a test. 56 automated tests.
- Cost: about 2,000 tokens per check ≈ **$0.0005 per line** with GPT-4o-mini at list price (Sep 2026); measured per run in the batch report.

## What it is not
Not a customs declaration system, not a licensed broker, not an export-control decision. Decision support with an audit trail.

## Next step
A **4–6 week pilot** on one client's master list and one route: see `pilot_proposal.md`.
