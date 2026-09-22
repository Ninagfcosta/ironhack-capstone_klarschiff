# Charts Documentation

All 5 charts were built with `build_charts.py` (matplotlib, 200dpi PNG). Colors and chart forms follow a validated categorical/sequential palette so hue always means the same thing across every chart (a color never gets reused for a different meaning), and every value that matters is labeled directly on the chart rather than left for the viewer to estimate.

## 1. `01_problem_kpi.png` — The problem in 3 numbers

**Form:** stat-tile row (three headline numbers, not a plotted chart — the right choice when the point is a single value per idea, not a comparison).

**What it shows:** the customs-hold pattern I&E LLC reported — average delay length, an illustrative cost per delay event, and how often the client says it happens.

**Why it matters to Chleo:** this is the opening slide. Before proposing a tool, the pitch has to establish that the problem is real, recurring, and has a cost — in the client's own words and numbers, not ours.

**Source:** client-interview exercise (SilverTrust Brief Project), Ironhack Capstone course material, 2026. Illustrative, not an external published statistic — flagged as such in `research/sector_research.md` and again on the slide itself.

## 2. `02_expected_value_breakdown.png` — Expected monthly value (part-to-whole)

**Form:** horizontal stacked bar (one whole broken into its contributing parts — the right form when the parts must visibly sum to a labeled total).

**What it shows:** where the €6,400/month expected value comes from: staff hours saved, avoided delay costs, and fewer correction/broker fees.

**Why it matters to Chleo:** turns one abstract ROI number into three defensible, separately-arguable components — if a client questions one part, the other two still stand.

**Source:** hoffmann_consultant_solutions deck (Google Drive), SilverTrust Brief exercise, 2026. Illustrative — same caveat as Chart 1.

## 3. `03_success_measures_before_after.png` — Before vs. pilot target (dumbbell)

**Form:** dumbbell / paired-dot plot (the right form for exactly two time points per category — before and target — without implying a continuous trend line between them).

**What it shows:** processing time per shipment (38 → 10 minutes) and first-pass document completeness (70% → 95%).

**Why it matters to Chleo:** these are the two numbers the pilot will actually be measured against — this chart is the direct visual bridge into `evaluation/eval_plan.md`.

**Source:** SilverTrust Brief exercise targets, 2026. Targets are proposed, not yet validated by a live pilot — flagged in `evaluation/eval_plan.md`.

## 4. `04_investment_options.png` — Investment options (range bars)

**Form:** floating/range bar, one shared EUR axis (the right form for comparing three ranges on a single scale without implying a false precision on either end).

**What it shows:** three ways to engage — a one-time paid pilot, an ongoing monthly subscription, or a larger custom build — each as a low–high range.

**Why it matters to Chleo:** gives the client a menu, not a single take-it-or-leave-it price — consistent with the "AI consultant proposing options" framing the brief asks for.

**Source:** SilverTrust Brief exercise, 2026. Indicative ranges, not quoted prices.

## 5. `05_delivery_timeline.png` — Pilot delivery timeline (Gantt-style)

**Form:** horizontal timeline bars, one row per phase, duration labeled at each bar's end (the right form for sequential phases with different durations across a shared time axis).

**What it shows:** the 5-sprint delivery plan (Discovery → Build → Prototype test → Live pilot → Review) mapped across a 1–3 month window.

**Why it matters to Chleo:** answers the "how long until this is real" question with a concrete, checkpointed plan rather than a vague promise — each sprint is something Chleo's team can track.

**Source:** SilverTrust Brief exercise sprint plan, 2026.

## Regenerating these charts

If any underlying number changes (e.g., after the real POC run gives you actual timing data), edit the relevant value in `build_charts.py` and re-run:

```
python3 build_charts.py
```

All 5 PNGs regenerate in place with the same styling.
