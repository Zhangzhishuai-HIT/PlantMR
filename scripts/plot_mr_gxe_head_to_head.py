#!/usr/bin/env python3
"""Plot the shared-input PlantMR versus summary-data MR-GxE benchmark."""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
BASE = ROOT / "results" / "benchmarks" / "mr_gxe_head_to_head"
raw = pd.read_csv(BASE / "replicates.tsv", sep="\t")
summary = pd.read_csv(BASE / "summary.tsv", sep="\t")

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

METHOD_COLOR = {"PlantMR": "#2A6F97", "summary_MR_GxE": "#B5654D"}
METHOD_LABEL = {"PlantMR": "PlantMR", "summary_MR_GxE": "Summary-data MR-GxE"}
SCENARIO_LABEL = {
    "constant_null_directional_pleiotropy": "Null effect + pleiotropy",
    "constant_effect_no_pleiotropy": "Constant effect, no pleiotropy",
    "constant_effect_directional_pleiotropy": "Constant effect + pleiotropy",
    "environment_effect_heterogeneity": "Environment-effect heterogeneity",
}
SCENARIOS = list(SCENARIO_LABEL)


def clean_axis(ax):
    ax.tick_params(direction="out", length=3, width=0.7, colors="#333333")
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")
    ax.grid(False)


# Keep only target-defined method/scenario pairs for the forest panel.
target = summary[summary.target_defined.astype(str).str.lower().isin(["true", "1"])].copy()
target["label"] = target.apply(lambda r: f"{SCENARIO_LABEL[r.scenario]}\n{METHOD_LABEL[r.method]}", axis=1)

fig, axs = plt.subplots(1, 2, figsize=(8.2, 4.9),
                        gridspec_kw={"width_ratios": [1.45, 1]},
                        constrained_layout=False)
fig.subplots_adjust(left=0.10, right=0.97, bottom=0.16, top=0.86, wspace=0.42)

# a: target-defined estimates with the true target shown as a diamond.
ax = axs[0]
clean_axis(ax)
y = np.arange(len(target))[::-1]
for yi, (_, row) in zip(y, target.iterrows()):
    g = raw[(raw.scenario == row.scenario) & (raw.method == row.method) & (raw.failure == "")]
    mean = g.estimate.mean()
    ci = 1.96 * g.estimate.std(ddof=1) / np.sqrt(len(g))
    color = METHOD_COLOR[row.method]
    ax.errorbar(mean, yi, xerr=ci, fmt="o", color=color, ms=5, capsize=2.5, lw=1.1)
    ax.scatter([float(row.true_parameter)], [yi], marker="D", s=22, color="#333333", zorder=4)
ax.axvline(0, color="#777777", lw=0.7)
ax.set_yticks(y)
ax.set_yticklabels(target.label, fontsize=7)
ax.set_xlabel("Mean estimate (95% CI of simulation mean)")
ax.set_title("a  Estimates at the defined target", loc="left", fontweight="bold")
ax.text(0.02, 0.02, "● method mean   ◆ simulated target", transform=ax.transAxes,
        fontsize=7, color="#555555")

# b: compact coverage map; blank cells are deliberately not scored.
ax = axs[1]
clean_axis(ax)
coverage = np.full((len(SCENARIOS), 2), np.nan)
methods = ["PlantMR", "summary_MR_GxE"]
for i, scenario in enumerate(SCENARIOS):
    for j, method in enumerate(methods):
        row = summary[(summary.scenario == scenario) & (summary.method == method)].iloc[0]
        if str(row.target_defined).lower() in ("true", "1"):
            coverage[i, j] = float(row.coverage_95)
masked = np.ma.masked_invalid(coverage)
im = ax.imshow(masked, cmap="Blues", vmin=0.90, vmax=1.0, aspect="auto")
ax.imshow(np.ma.masked_where(~np.isnan(coverage), np.ones_like(coverage)),
          cmap=mpl.colors.ListedColormap(["#F0F1F1"]), aspect="auto", alpha=0.7)
for i in range(len(SCENARIOS)):
    for j in range(2):
        if np.isnan(coverage[i, j]):
            ax.text(j, i, "—", ha="center", va="center", fontsize=11, color="#777777")
        else:
            color = "white" if coverage[i, j] < 0.94 else NAVY if "NAVY" in globals() else "#17365D"
            ax.text(j, i, f"{coverage[i, j]:.3f}", ha="center", va="center", fontsize=8, color=color)
ax.set_xticks([0, 1])
ax.set_xticklabels(["PlantMR", "Summary-data\nMR-GxE"], fontsize=7)
ax.set_yticks(np.arange(len(SCENARIOS)))
ax.set_yticklabels([SCENARIO_LABEL[s] for s in SCENARIOS], fontsize=7)
ax.set_title("b  Coverage only for the defined estimand", loc="left", fontweight="bold")
cb = fig.colorbar(im, ax=ax, fraction=0.055, pad=0.04)
cb.set_label("95% coverage", fontsize=8)
cb.ax.tick_params(labelsize=7, length=2)
ax.text(0.0, -0.24, "Gray cells: target differs, so no performance score is reported.",
        transform=ax.transAxes, fontsize=7, color="#555555")

fig.suptitle("Shared-input comparison of PlantMR and summary-data MR-GxE",
             fontsize=12, fontweight="bold", color="#17365D", y=0.96)
fig.savefig(OUT / "mr_gxe_head_to_head.png", dpi=400, bbox_inches="tight")
fig.savefig(OUT / "mr_gxe_head_to_head.pdf", bbox_inches="tight")
print(OUT / "mr_gxe_head_to_head.png")
print(OUT / "mr_gxe_head_to_head.pdf")
