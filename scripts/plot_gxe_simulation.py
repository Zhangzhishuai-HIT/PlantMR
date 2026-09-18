#!/usr/bin/env python3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT / "results/benchmarks/gxe_simulation/replicates.tsv", sep="\t", keep_default_na=False)
outdir = ROOT / "docs/figures"
outdir.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.7), constrained_layout=False)
fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.30, wspace=0.34)

order = ["null", "causal_gxe", "directional_pleiotropy"]
labels = ["Null", "Causal G×E", "Directional\npleiotropy"]
colors = {"environment": "#1f77b4", "diagonal": "#d95f02"}

ax = axes[0]
for i, scenario in enumerate(order):
    for j, covariance in enumerate(["environment", "diagonal"]):
        values = raw.loc[(raw.scenario == scenario) & (raw.covariance == covariance), "slope"]
        pos = i * 3 + j + 1
        bp = ax.boxplot(values, positions=[pos], widths=0.32, patch_artist=True, showfliers=False)
        bp["boxes"][0].set_facecolor(colors[covariance])
        bp["boxes"][0].set_alpha(0.75)
        for element in ("whiskers", "caps", "medians"):
            for item in bp[element]:
                item.set_color("#222222")
ax.axhline(0.0, color="#333333", lw=0.8)
ax.axhline(0.25, color="#777777", lw=0.8, ls="--")
ax.set_xticks([1.5, 4.5, 7.5])
ax.set_xticklabels(labels)
ax.set_ylim(-0.08, 0.36)
ax.set_ylabel("Estimated environment slope")
ax.set_title("A. Sampling distribution")
ax.legend(handles=[plt.Line2D([0], [0], color=colors["environment"], lw=6),
                   plt.Line2D([0], [0], color=colors["diagonal"], lw=6)],
          labels=["Covariance-aware", "Diagonal comparator"], frameon=False, fontsize=8,
          loc="upper left")

summary = pd.read_csv(ROOT / "results/benchmarks/gxe_simulation/summary.tsv", sep="\t", keep_default_na=False)
ax = axes[1]
metric_styles = {"rejection_p05_slope": ("o", "Rejection at α=0.05"),
                 "coverage_95_slope": ("s", "95% CI coverage")}
for j, covariance in enumerate(["environment", "diagonal"]):
    offset = -0.13 if j == 0 else 0.13
    for metric, (marker, label) in metric_styles.items():
        vals = []
        for scenario in order:
            row = summary[(summary.scenario == scenario) & (summary.covariance == covariance)]
            vals.append(float(row[metric].iloc[0]))
        x = [i + offset + (-0.045 if metric == "rejection_p05_slope" else 0.045) for i in range(len(order))]
        ax.plot(x, vals, marker=marker, lw=1.2, color=colors[covariance],
                label=("Cov-aware " if j == 0 else "Diagonal ") + ("reject" if metric == "rejection_p05_slope" else "coverage"))
        for xi, yi in zip(x, vals):
            extra = 0.025 if metric == "coverage_95_slope" else 0.0
            extra += 0.025 if (yi > 0.97 and covariance == "diagonal") else 0.0
            ax.text(xi, min(1.115, yi + 0.035 + extra), "%.2f" % yi, ha="center", va="bottom", fontsize=6.5,
                    color=colors[covariance])
ax.axhline(0.05, color="#777777", lw=0.8, ls=":")
ax.axhline(0.95, color="#777777", lw=0.8, ls="--")
ax.set_xticks(range(len(order)))
ax.set_xticklabels(labels)
ax.set_ylim(0, 1.13)
ax.set_ylabel("Proportion")
ax.set_title("B. Rejection and coverage")
handles, legend_labels = ax.get_legend_handles_labels()
fig.legend(handles, legend_labels, frameon=False, fontsize=6.5, ncol=4,
           loc="lower center", bbox_to_anchor=(0.5, 0.03), columnspacing=1.2)

fig.savefig(outdir / "gxe_simulation.png", dpi=300)
fig.savefig(outdir / "gxe_simulation.pdf")
print(outdir / "gxe_simulation.png")
print(outdir / "gxe_simulation.pdf")
