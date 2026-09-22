# -*- coding: utf-8 -*-
"""
Builds the 5 Round 1 stakeholder charts for the Pre-Shipment Document Check
& HS Code Suggestion pitch (I&E LLC / SilverTrust Brief scenario).

Palette + form choices follow the dataviz skill's reference palette
(references/palette.md) and form rules (references/choosing-a-form.md):
- categorical slots used in fixed order (blue, orange, aqua, yellow, magenta)
- sequential/ordinal use is avoided here; all charts are categorical or
  part-to-whole / before-after, per the job each chart does
- chart chrome (surface, ink, gridlines) taken from the palette's "Chart
  chrome & ink" table, light mode
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))  # saves the PNGs next to this script

# ---- palette (light mode) ----
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"

BLUE_LIGHT = "#86b6ef"   # sequential step 250, for "before" shade
BLUE_DARK = "#184f95"    # sequential step 600, for "after" shade

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "text.color": INK_PRIMARY,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": INK_SECONDARY,
    "xtick.color": INK_MUTED,
    "ytick.color": INK_MUTED,
    "axes.grid": False,
})


def savefig(fig, name):
    fig.savefig(os.path.join(OUT_DIR, name), dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Chart 1 — "The problem in 3 numbers" (KPI stat-tile row)
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
stats = [
    ("2+ days", "average customs hold\nwhen a document is wrong", BLUE),
    ("~€1,500", "estimated cost of a single\ndelay event (illustrative)", ORANGE),
    ("Weekly", "how often the team says\nthis issue comes up", AQUA),
]
for ax, (value, label, color) in zip(axes, stats):
    ax.axis("off")
    ax.text(0.5, 0.62, value, ha="center", va="center", fontsize=30, fontweight="bold", color=INK_PRIMARY)
    ax.text(0.5, 0.30, label, ha="center", va="center", fontsize=10.5, color=INK_SECONDARY, linespacing=1.4)
    ax.add_patch(plt.Rectangle((0.30, 0.80), 0.40, 0.045, color=color, transform=ax.transAxes, clip_on=False))
fig.suptitle("The problem in 3 numbers", fontsize=14, fontweight="bold", color=INK_PRIMARY, y=1.05)
savefig(fig, "01_problem_kpi.png")

# ---------------------------------------------------------------------------
# Chart 2 — Expected monthly value breakdown (part-to-whole, horizontal stacked bar)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 2.6))
segments = [
    ("Staff hours saved\n(60 hrs @ €40/hr)", 2400, BLUE),
    ("Avoided delays\n(2 @ ~€1,500)", 3000, ORANGE),
    ("Fewer correction\n/ broker fees", 1000, AQUA),
]
left = 0
for label, value, color in segments:
    ax.barh(0, value, left=left, height=0.5, color=color, edgecolor=SURFACE, linewidth=2)
    ax.text(left + value / 2, 0, f"€{value:,}", ha="center", va="center",
            color="white", fontsize=11, fontweight="bold")
    ax.text(left + value / 2, -0.62, label, ha="center", va="top", fontsize=9, color=INK_SECONDARY, linespacing=1.3)
    left += value
ax.text(left + 150, 0, f"Total: ~€{left:,}/month", va="center", ha="left",
        fontsize=12, fontweight="bold", color=INK_PRIMARY)
ax.set_xlim(0, left + 1800)
ax.set_ylim(-1.3, 0.6)
ax.axis("off")
ax.set_title("Expected monthly value (illustrative)", fontsize=14, fontweight="bold", color=INK_PRIMARY, loc="left")
savefig(fig, "02_expected_value_breakdown.png")

# ---------------------------------------------------------------------------
# Chart 3 — Success measures, before vs after (dumbbell, 1 hue 2 shades)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 3.2))
metrics = [
    ("Processing time\n(minutes/shipment)", 38, 10, "min"),
    ("First-pass completeness\n(% accepted, no follow-up)", 70, 95, "%"),
]
y_pos = np.arange(len(metrics))
for i, (label, before, after, unit) in enumerate(metrics):
    ax.plot([before, after], [i, i], color=BASELINE, linewidth=2, zorder=1)
    ax.scatter([before], [i], s=220, color=BLUE_LIGHT, zorder=2, edgecolor=SURFACE, linewidth=1.5)
    ax.scatter([after], [i], s=220, color=BLUE_DARK, zorder=2, edgecolor=SURFACE, linewidth=1.5)
    ax.text(before, i + 0.28, f"Before: {before}{unit}", ha="center", fontsize=9.5, color=INK_SECONDARY)
    ax.text(after, i - 0.30, f"Target: {after}{unit}", ha="center", fontsize=9.5, color=INK_PRIMARY, fontweight="bold")
ax.set_yticks(y_pos)
ax.set_yticklabels([m[0] for m in metrics], fontsize=10.5, color=INK_PRIMARY)
ax.set_xlabel("")
ax.set_xlim(0, 105)
ax.set_ylim(-0.6, len(metrics) - 1 + 0.75)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(BASELINE)
ax.tick_params(axis="x", colors=INK_MUTED)
ax.set_title("Success measures: before vs. pilot target", fontsize=14, fontweight="bold",
             color=INK_PRIMARY, loc="left", pad=18)
savefig(fig, "03_success_measures_before_after.png")

# ---------------------------------------------------------------------------
# Chart 4 — Investment options (range bars, one axis, all in EUR)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 3.0))
options = [
    ("Paid pilot\n(one-time)", 10000, 15000, BLUE),
    ("Operational subscription\n(per month)", 2000, 5000, AQUA),
    ("Custom implementation\n(one-time)", 25000, 60000, ORANGE),
]
y_pos = np.arange(len(options))
for i, (label, lo, hi, color) in enumerate(options):
    ax.barh(i, hi - lo, left=lo, height=0.4, color=color)
    ax.text((lo + hi) / 2, i + 0.34, f"€{lo:,} – €{hi:,}", ha="center", va="bottom",
            fontsize=9.5, color=INK_SECONDARY, fontweight="bold")
ax.set_yticks(y_pos)
ax.set_yticklabels([o[0] for o in options], fontsize=10, color=INK_PRIMARY)
ax.set_xlim(0, 65000)
ax.set_ylim(-0.6, len(options) - 1 + 0.75)
ax.set_xlabel("EUR (indicative range)", fontsize=9.5, color=INK_MUTED)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(BASELINE)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_title("Investment options", fontsize=14, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14)
savefig(fig, "04_investment_options.png")

# ---------------------------------------------------------------------------
# Chart 5 — Delivery timeline (Sprint 0-4 across Months 1-3, categorical)
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9.5, 3.6))
phases = [
    ("Sprint 0: Discovery", 0, 1, BLUE),
    ("Sprint 1: Build", 1, 1, ORANGE),
    ("Sprint 2: Prototype test", 2, 1, AQUA),
    ("Sprint 3: Live pilot", 2.7, 1.3, YELLOW),
    ("Sprint 4: Review", 3.7, 0.6, MAGENTA),
]
y_positions = [len(phases) - i - 1 for i in range(len(phases))]
for (label, start, dur, color), y in zip(phases, y_positions):
    ax.barh(y, dur, left=start, height=0.5, color=color)
    ax.text(start + dur + 0.06, y, f"{dur:.1f} mo", ha="left", va="center",
            fontsize=8.5, color=INK_MUTED)
ax.set_yticks(y_positions)
ax.set_yticklabels([p[0] for p in phases], fontsize=10, color=INK_PRIMARY)
ax.set_xlim(0, 5.0)
ax.set_xticks([0, 1, 2, 3, 4])
ax.set_xticklabels(["Month 1", "", "Month 2", "", "Month 3"], fontsize=9.5, color=INK_MUTED)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.spines["bottom"].set_color(BASELINE)
ax.set_title("Pilot delivery timeline (1–3 months)", fontsize=14, fontweight="bold",
             color=INK_PRIMARY, loc="left", pad=14)
savefig(fig, "05_delivery_timeline.png")

print("All 5 charts written to", OUT_DIR)
