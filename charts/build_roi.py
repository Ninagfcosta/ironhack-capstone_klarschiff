"""ROI model for roi_risk_assessment.md (all inputs illustrative until the pilot measures real values)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PILOT_FEE = 12_500          # mid-point of EUR 10-15k, paid in month 1
TRAINING = 1_300            # AI-literacy training + change management (2 people x 16 h x EUR 40)
SUBSCRIPTION = 3_500        # mid-point of EUR 2-5k per month, from month 4
TECH = 150                  # hosting + LangSmith seat + LLM tokens + backups per month
RAMP = {1: 0.0, 2: 0.25, 3: 0.5}   # share of full value reached during the pilot months
SCENARIOS = {"Conservative": 3_200, "Base": 6_400, "Optimistic": 9_600}   # monthly value


def model(value, months=36):
    rows, cost_c, val_c, breakeven = [], 0, 0, None
    for m in range(1, months + 1):
        cost = TECH + (PILOT_FEE + TRAINING if m == 1 else 0) + (SUBSCRIPTION if m >= 4 else 0)
        val = value * RAMP.get(m, 1.0)
        cost_c += cost; val_c += val
        if breakeven is None and val_c >= cost_c:
            breakeven = m
        rows.append((m, cost_c, val_c))
    return rows, breakeven


def roi(rows, m):
    c, v = rows[m - 1][1], rows[m - 1][2]
    return round((v - c) / c * 100), round(c), round(v)


out = {}
# Colours: the same palette as the presentation (deep plum background, cream text, sunset accents)
BG, INK, MUTED = "#231640", "#FFF4EA", "#CDBBD6"
plt.rcParams.update({"text.color": INK, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": MUTED})
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)
colors = {"Conservative": "#CDBBD6", "Base": "#FF8A3D", "Optimistic": "#FFC857"}
for name, v in SCENARIOS.items():
    rows, be = model(v)
    out[name] = {"monthly_value": v, "breakeven_month": be, "roi_12": roi(rows, 12), "roi_36": roi(rows, 36)}
    ax.plot([r[0] for r in rows], [(r[2] - r[1]) / 1000 for r in rows], lw=2.6, color=colors[name], label=f"{name} (€{v:,}/month)")
ax.axhline(0, color=MUTED, lw=1)
ax.set_xlabel("Month"); ax.set_ylabel("Cumulative net value (€ thousand)")
ax.set_title("KlarSchiff: cumulative net value by scenario (illustrative)", loc="left", fontsize=13, color=INK, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", alpha=.25); ax.legend(frameon=False, labelcolor=INK)
plt.tight_layout(); plt.savefig("charts/06_roi_scenarios.png", facecolor=BG)
json.dump(out, open("charts/roi_results.json", "w"), indent=2)
print(json.dumps(out, indent=1))
