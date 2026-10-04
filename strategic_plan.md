# Strategic plan: from POC to pilot to product

**Version:** Round 2 · 25 September 2026 · Author: Janaina Hoffmann (Berlin)

## 1. Where we are

| Stage | Status |
|---|---|
| Round 1 POC | ✅ n8n, 1 step, 5 cases |
| Round 2 MVP | ✅ 5-step agent, tariff monitor, Streamlit app, 20-case evaluation, compliance files |
| **Next: paid pilot with I&E LLC** | Proposed: 3 months, 1 route, 1 product family |
| Product for the German market | After a successful pilot |

## 2. Roadmap (realistic: about 12 months to full production, Scrum with 2-week sprints)

Updated 4 Oct 2026 to match the presentation (slide 14). Benchmarks: AI pilots in customs brokerage run 10-12 weeks; enterprise AI rollouts take 6-18 months; many AI projects stop after the proof of concept (Gartner). So each phase ends with a go / no-go gate.

| Phase | When | Sprints | Main work | Gate |
|---|---|---|---|---|
| Done: POC + MVP | Bootcamp, Sep-Oct 2026 | - | n8n POC, Python agent, Streamlit app, LangSmith evaluation | Ironhack + IHK review |
| 1 · Pilot | Months 1-3 | 6 | Baseline, client data, blind test, shadow mode, live pilot with review, decide | Go / no-go (section 3) |
| 2 · Production readiness | Months 4-7 | 8 | Security, EU hosting, ERP / TMS link, 10-digit TARIC, training, ATLAS-ready export for the broker | Security and data-protection sign-off |
| 3 · Go-live and scale | Months 8-12 | 10 | Second route and product family, then customs brokers (one broker serves many importers) | Measured KPIs (section 7) |

Pilot sprints (2 weeks each): 1 Baseline · 2 Client data · 3 Blind test · 4 Shadow mode · 5 Live pilot · 6 Decide.

| Milestone | When | Done when |
|---|---|---|
| M0 Pilot contract | Month 0 | Scope, price, DPA, liability clause signed |
| M1 Baseline measured | Sprint 1 | 20 shipments timed; 12 months of holds and broker corrections collected |
| M2 Blind test | Sprint 3 | 50-100 real, anonymised shipments, labelled by the broker, scored by the agent **before** anyone sees the answers |
| M3 Live pilot | Sprints 4-5 | Shadow mode first, then every live shipment checked and reviewed by a person |
| M4 Go / no-go | Sprint 6 (month 3) | Pilot success criteria reviewed with Chleo and the broker |
| M5 Production ready | Month 7 | Security, hosting and integration accepted |
| M6 Scale | Months 8-12 | Second route live; first customs broker signed |

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
