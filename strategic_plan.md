# Strategic plan: from POC to pilot to product

**Version:** Round 2 · 25 September 2026 · Author: Janaina Hoffmann (Berlin)

## 1. Where we are

| Stage | Status |
|---|---|
| Round 1 POC | ✅ n8n, 1 step, 5 cases |
| Round 2 MVP | ✅ 5-step agent, tariff monitor, Streamlit app, 20-case evaluation, compliance files |
| **Next: paid pilot with I&E LLC** | Proposed: 3 months, 1 route, 1 product family |
| Product for the German market | After a successful pilot |

## 2. Roadmap

```
Oct 2026        Nov 2026 - Jan 2027 (pilot)                         Feb - Jun 2027              H2 2027
Round 2 ─────► Sprint 0  Sprint 1   Sprint 2    Sprint 3    Sprint 4 ─► Production at I&E ───► 2-3 more clients
               baseline  connect    blind test  live, all   decide      (subscription)          (via a customs broker)
                         data       (broker)    reviewed
```

| Milestone | When | Done when |
|---|---|---|
| M0 Pilot contract | Oct 2026 | Scope, price, DPA, liability clause signed |
| M1 Baseline measured (Sprint 0) | Month 1 | 20 shipments timed; 12 months of holds and broker corrections collected |
| M2 Blind test (Sprint 2) | Month 2 | 50-100 real, anonymised shipments, labelled by the broker, scored by the agent **before** anyone sees the answers |
| M3 Live pilot (Sprint 3) | Months 2-3 | Every live shipment checked; every result reviewed by a person |
| M4 Go / no-go (Sprint 4) | Month 3 | Pilot success criteria reviewed with Chleo and the broker |
| M5 Production | Month 4+ | Subscription tier chosen from measured value; monitor running daily |

## 3. Pilot success criteria (go / no-go)

| Criterion | Go if | Stop if |
|---|---|---|
| False all-clears reaching customs | 0 | ≥ 1 |
| HS suggestions accepted without change (blind test) | ≥ 90% at 6 digits | < 75% |
| Review time per shipment | < 10 min (from 30-45) | no measurable saving |
| Unnecessary review rate | ≤ 30% | > 40% after tuning |
| Documentation-related holds | -50% vs baseline (trend) | no reduction |
| User satisfaction (2 users) | "I would keep using it" | "slower than before" |
| Tariff monitor | every alert reviewed within 2 working days | alerts ignored |

## 4. Go-to-market (Germany first)

**Why Germany:** the founder is in Berlin; Germany is the EU's largest construction market and a large importer of construction materials; the German e-invoicing obligation (receive 2025, issue 2027/2028) and CBAM (2026) create a reason to act now.

| Segment | Why | How to reach |
|---|---|---|
| **Customs brokers (Zollagenturen)** with construction clients | One broker serves many importers: the best channel. They carry the classification work today | Direct outreach in Berlin/Brandenburg and Hamburg (port); partner model with revenue share |
| Construction-material importers/traders (SMEs) | The pain (holds, CBAM, steel quotas) is theirs | Through the broker; trade associations; LinkedIn case study from the I&E pilot |
| Precast and insulation manufacturers importing inputs | DoP/CE-heavy | Later |

**Positioning:** not another global trade-compliance suite (AEB, SAP GTS, Descartes, Thomson Reuters are large and expensive), but a **light pre-shipment co-pilot for construction materials**, with the human in control, sources on every answer, and a tariff monitor. German-language interface and review pack.

## 5. Offer and pricing

| Package | Price | Contents |
|---|---|---|
| Pilot | €10-15k one-off | 3 months, 1 route, 1 product family, baseline + blind test + training |
| Subscription S | €2,000 / month | up to ~150 checks/month, monitor, rule updates |
| Subscription M | €3,500 / month | up to ~500 checks/month, 2 routes, quarterly rule review with the broker |
| Custom | €25-60k | more categories, integration with the broker's software, OCR |

Price follows measured value (see the conservative scenario in `roi_risk_assessment.md`).

## 6. Communication plan

| Audience | Message | Channel | When |
|---|---|---|---|
| Chleo (CEO) | Value, risk, go/no-go | 1-page report + 30 min meeting | Monthly + Sprint 4 |
| Logistics team | "It prepares, you decide"; how to escalate | 2-day training, cheat sheet (DE) | Before go-live, weekly check-in |
| Customs broker | Review pack format, blind-test labelling | Workshop | Sprint 0 and 2 |
| Works council / DPO | Team-level metrics, data minimisation | Written note + meeting | Before go-live |

## 7. KPIs after go-live

Holds per month (documentation-related) · review minutes per shipment · acceptance rate at 6 digits · false all-clears (must be 0) · override rate (team) · unnecessary review rate · alert-to-review time · cost per check.

## 8. What the founder needs

- **Legal form** before the first paid contract (freelance *Freiberuflerin/Gewerbe* or UG), **terms (AGB)** with limitation of liability, **professional indemnity insurance**.
- **A customs expert** (licensed broker or customs consultant) as partner to verify rules each quarter.
- **Funding options to check:** Berlin support programmes (e.g. IBB, Investitionsbank Berlin), founder coaching programmes.
- **Product roadmap after the pilot:** OCR for scans, Turkish/Chinese invoices, Binding Tariff Information (vZTA) assistant, export to the broker's customs software, more product categories.
