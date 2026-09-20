#!/usr/bin/env python3
"""Create the PlantMR simulation figure from the frozen benchmark tables."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "legend.frameon": False,
})

raw = pd.read_csv(ROOT / "results/benchmarks/gxe_simulation/replicates.tsv", sep="\t", keep_default_na=False)
summary = pd.read_csv(ROOT / "results/benchmarks/gxe_simulation/summary.tsv", sep="\t", keep_default_na=False)

COV = {"environment": "#2A6F97", "diagonal": "#B5654D"}
SCENARIOS = ["null", "causal_gxe", "directional_pleiotropy"]
LABELS = ["Null", "True slope = 0.25", "Directional pleiotropy"]
TARGET = {"null": 0.0, "causal_gxe": 0.25, "directional_pleiotropy": 0.0}


def clean_axis(ax):
    ax.tick_params(direction="out", length=3, width=0.7, colors="#333333")
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")
    ax.grid(False)


fig = plt.figure(figsize=(7.25, 5.65))
gs = fig.add_gridspec(2, 2, left=0.09, right=0.98, bottom=0.10, top=0.89,
                      hspace=0.48, wspace=0.34)

# a: sampling distributions summarized by the mean and 95% CI of the simulation mean.
ax = fig.add_subplot(gs[0, 0])
clean_axis(ax)
x = np.arange(len(SCENARIOS))
for offset, cov in [(-0.14, "environment"), (0.14, "diagonal")]:
    means = []
    cis = []
    for scenario in SCENARIOS:
        g = raw[(raw.scenario == scenario) & (raw.covariance == cov)]
        means.append(g.slope.mean())
        cis.append(1.96 * g.slope.std(ddof=1) / np.sqrt(len(g)))
    ax.errorbar(x + offset, means, yerr=cis, fmt="o", ms=5, lw=1.2,
                capsize=3, color=COV[cov], label="Covariance-aware" if cov == "environment" else "Diagonal")
for i, scenario in enumerate(SCENARIOS):
    ax.plot([i - 0.30, i + 0.30], [TARGET[scenario], TARGET[scenario]],
            color="#777777", lw=0.8, ls="--", zorder=0)
ax.axhline(0, color="#444444", lw=0.6)
ax.set_xticks(x)
ax.set_xticklabels(LABELS, rotation=18, ha="right")
ax.set_ylabel("Estimated environment slope")
ax.set_title("a  Point estimates across simulations", loc="left", fontweight="bold")
ax.set_ylim(-0.08, 0.34)

# b: type-I error / power.
ax = fig.add_subplot(gs[0, 1])
clean_axis(ax)
for offset, cov in [(-0.14, "environment"), (0.14, "diagonal")]:
    vals = []
    for scenario in SCENARIOS:
        row = summary[(summary.scenario == scenario) & (summary.covariance == cov)].iloc[0]
        vals.append(float(row.rejection_p05_slope))
    ax.plot(x + offset, vals, "o-", ms=4.5, lw=1.1, color=COV[cov])
ax.axhline(0.05, color="#777777", lw=0.8, ls="--")
ax.text(2.45, 0.052, "nominal 0.05", ha="right", va="bottom", fontsize=7, color="#666666")
ax.set_xticks(x)
ax.set_xticklabels(LABELS, rotation=18, ha="right")
ax.set_ylabel("Rejection proportion")
ax.set_title("b  Null rejection and power", loc="left", fontweight="bold")
ax.set_ylim(0, 1.04)

# c: confidence-interval coverage.
ax = fig.add_subplot(gs[1, 0])
clean_axis(ax)
for offset, cov in [(-0.14, "environment"), (0.14, "diagonal")]:
    vals = []
    for scenario in SCENARIOS:
        row = summary[(summary.scenario == scenario) & (summary.covariance == cov)].iloc[0]
        vals.append(float(row.coverage_95_slope))
    ax.plot(x + offset, vals, "s-", ms=4.5, lw=1.1, color=COV[cov])
ax.axhline(0.95, color="#777777", lw=0.8, ls="--")
ax.text(2.45, 0.952, "nominal 0.95", ha="right", va="bottom", fontsize=7, color="#666666")
ax.set_xticks(x)
ax.set_xticklabels(LABELS, rotation=18, ha="right")
ax.set_ylabel("95% CI coverage")
ax.set_title("c  Interval calibration", loc="left", fontweight="bold")
ax.set_ylim(0.70, 1.03)

# d: directional pleiotropy makes the intercept move while the slope remains near zero.
ax = fig.add_subplot(gs[1, 1])
clean_axis(ax)
g = raw[raw.scenario == "directional_pleiotropy"]
for cov in ["environment", "diagonal"]:
    q = g[g.covariance == cov]
    ax.scatter(q.intercept, q.slope, s=8, alpha=0.14, color=COV[cov], edgecolors="none")
    mx, my = q.intercept.mean(), q.slope.mean()
    ax.scatter([mx], [my], s=32, color=COV[cov], edgecolors="white", linewidths=0.7, zorder=4)
    ax.text(mx + 0.012, my + 0.003, cov.replace("environment", "cov-aware"), fontsize=7, color=COV[cov])
ax.axvline(0.5, color="#777777", lw=0.8, ls="--")
ax.axhline(0, color="#777777", lw=0.8, ls="--")
ax.set_xlabel("Estimated intercept")
ax.set_ylabel("Estimated slope")
ax.set_title("d  Directional pleiotropy", loc="left", fontweight="bold")
ax.text(0.03, 0.94, "True intercept = 0.5\nTrue slope = 0", transform=ax.transAxes,
        fontsize=7, va="top", color="#555555")

handles = [Line2D([0], [0], marker="o", color=COV["environment"], lw=1.2, markersize=5, label="Covariance-aware"),
           Line2D([0], [0], marker="o", color=COV["diagonal"], lw=1.2, markersize=5, label="Diagonal comparator")]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.955), ncol=2, fontsize=8)
fig.savefig(OUT / "gxe_simulation.png", dpi=400, bbox_inches="tight")
fig.savefig(OUT / "gxe_simulation.pdf", bbox_inches="tight")
print(OUT / "gxe_simulation.png")
print(OUT / "gxe_simulation.pdf")
