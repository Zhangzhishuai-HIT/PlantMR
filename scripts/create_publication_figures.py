#!/usr/bin/env python3
"""Generate publication figures from frozen PlantMR results.

The figure set follows plant MR papers: plant/environment context, calibration,
regional association plus LD, and a target-aware method comparison.
"""
from pathlib import Path
import json
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
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

NAVY = "#17365D"
BLUE = "#2A6F97"
GREEN = "#5C8D50"
GOLD = "#DDA15E"
RUST = "#B5654D"
PLUM = "#6D597A"
GREY = "#777777"
LIGHT = "#F3F5F5"


def clean_axis(ax):
    ax.tick_params(direction="out", length=3, width=0.7, colors="#333333")
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")
    ax.grid(False)


def panel_label(ax, label):
    ax.text(-0.08, 1.05, label, transform=ax.transAxes, fontsize=10,
            fontweight="bold", color=NAVY, va="bottom", ha="left")


def save(fig, stem):
    fig.savefig(OUT / f"{stem}.png", dpi=400, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


# Figure 3: covariance misspecification, shown as calibration diagnostics rather than bars.
ld = pd.read_csv(ROOT / "results/benchmarks/gxe_ld_stress/summary.tsv", sep="\t", keep_default_na=False)
ld_raw = pd.read_csv(ROOT / "results/benchmarks/gxe_ld_stress/replicates.tsv", sep="\t", keep_default_na=False)
fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.5),
                        gridspec_kw={"hspace": 0.48, "wspace": 0.38})

# a: empirical p-value calibration under the null.
ax = axs[0, 0]
clean_axis(ax)
for cov, color, label in [("correct_ld_environment", BLUE, "Correct covariance"),
                           ("diagonal_misspecified", RUST, "Independence misspecified")]:
    p = np.sort(ld_raw.loc[(ld_raw.scenario == "null") & (ld_raw.covariance == cov), "slope_pval"].to_numpy())
    y = np.arange(1, len(p) + 1) / len(p)
    ax.plot(p, y, color=color, lw=1.5, label=label)
ax.plot([0, 1], [0, 1], color="#888888", lw=0.8, ls="--")
ax.axvline(0.05, color="#888888", lw=0.8, ls=":")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Slope P value under the null")
ax.set_ylabel("Empirical cumulative proportion")
ax.set_title("a  Null P-value calibration", loc="left", fontweight="bold")
ax.legend(fontsize=7, loc="lower right")

# b: sampling distributions of slope estimates.
ax = axs[0, 1]
clean_axis(ax)
positions = [1, 2, 4, 5]
labels = ["Null\ncorrect", "Null\ndiagonal", "Causal\ncorrect", "Causal\ndiagonal"]
colors = [BLUE, RUST, BLUE, RUST]
for pos, scenario, cov, color in zip(
        positions,
        ["null", "null", "causal_gxe", "causal_gxe"],
        ["correct_ld_environment", "diagonal_misspecified"] * 2,
        colors):
    sname = scenario
    g = ld_raw[(ld_raw.scenario == sname) & (ld_raw.covariance == cov)]
    bp = ax.boxplot(g.slope, positions=[pos], widths=0.58, patch_artist=True,
                    showfliers=False, whis=(5, 95))
    bp["boxes"][0].set_facecolor(color)
    bp["boxes"][0].set_alpha(0.78)
    bp["boxes"][0].set_edgecolor("#333333")
    for element in ("whiskers", "caps", "medians"):
        for item in bp[element]:
            item.set_color("#333333")
            item.set_linewidth(0.8)
ax.axhline(0, color="#666666", lw=0.8, ls="--")
ax.axhline(0.25, color="#666666", lw=0.8, ls=":")
ax.set_xticks(positions)
ax.set_xticklabels(labels, fontsize=7)
ax.set_ylabel("Estimated slope")
ax.set_title("b  Sampling distribution", loc="left", fontweight="bold")
ax.set_xlim(0.3, 5.7)

# c: coverage with the nominal target.
ax = axs[1, 0]
clean_axis(ax)
scenarios = ["null", "causal_gxe"]
scenario_labels = ["Null slope", "True slope = 0.25"]
x = np.arange(2)
for offset, cov, color in [(-0.13, "correct_ld_environment", BLUE),
                           (0.13, "diagonal_misspecified", RUST)]:
    vals = []
    for scenario in scenarios:
        row = ld[(ld.scenario == scenario) & (ld.covariance == cov)].iloc[0]
        vals.append(float(row.coverage_95))
    ax.plot(x + offset, vals, "o", ms=5.5, color=color)
ax.axhline(0.95, color="#777777", lw=0.8, ls="--")
ax.set_xticks(x)
ax.set_xticklabels(scenario_labels, rotation=12, ha="right")
ax.set_ylim(0.82, 1.01)
ax.set_ylabel("95% CI coverage")
ax.set_title("c  Coverage loss under independence", loc="left", fontweight="bold")

# d: relative standard-error distortion.
ax = axs[1, 1]
clean_axis(ax)
ratios = []
for scenario in scenarios:
    correct = float(ld[(ld.scenario == scenario) & (ld.covariance == "correct_ld_environment")].mean_se.iloc[0])
    diagonal = float(ld[(ld.scenario == scenario) & (ld.covariance == "diagonal_misspecified")].mean_se.iloc[0])
    ratios.append(diagonal / correct)
ax.axhline(1, color="#777777", lw=0.8, ls="--")
ax.plot(x, ratios, "o-", color=RUST, lw=1.4, ms=5.5)
for i, value in enumerate(ratios):
    ax.text(i, value + 0.015, f"{value:.2f}", ha="center", fontsize=7)
ax.set_xticks(x)
ax.set_xticklabels(scenario_labels, rotation=12, ha="right")
ax.set_ylim(0.72, 1.08)
ax.set_ylabel("Mean SE / correct-covariance SE")
ax.set_title("d  Standard-error distortion", loc="left", fontweight="bold")
for ax, label in zip(axs.flat, "abcd"):
    panel_label(ax, label)
save(fig, "gxe_ld_stress")


# Figure 4: Arabidopsis plant-MR case, following regional SMR/eQTL + LD + forest-plot conventions.
harm = pd.read_csv(ROOT / "results/real/arabidopsis_baseline_AT1G11560_diag/gxe_harmonized.tsv", sep="\t")
strat = pd.read_csv(ROOT / "results/real/arabidopsis_baseline_AT1G11560_stratified_all/environment_results.tsv", sep="\t")
ld = pd.read_csv(ROOT / "data/real/arabidopsis_baseline_AT1G11560/ld_correlation.tsv", sep="\t", index_col=0)

harm["position"] = harm["SNP"].str.extract(r":(\d+)$").astype(float)
harm["pos_mb"] = harm["position"] / 1e6
snps = [s for s in ld.index if s in set(harm.SNP)]
ld_mat = ld.loc[snps, snps].to_numpy(dtype=float) ** 2

fig = plt.figure(figsize=(8.0, 6.3))
gs = fig.add_gridspec(2, 2, width_ratios=[1.38, 1], height_ratios=[1.18, 1],
                      left=0.08, right=0.97, bottom=0.09, top=0.95,
                      hspace=0.52, wspace=0.38)

# a: three aligned regional association tracks.
sub = gs[0, 0].subgridspec(3, 1, hspace=0.06)
tracks = [("exposure_pval", "Exposure eQTL", BLUE),
          ("outcome_pval", "Flowering time, 10°C", GREEN),
          ("outcome_pval", "Flowering time, 16°C", GOLD)]
for i, (column, title, color) in enumerate(tracks):
    ax = fig.add_subplot(sub[i, 0])
    clean_axis(ax)
    env = None if i == 0 else ("10C" if i == 1 else "16C")
    g = harm if env is None else harm[harm.environment == env]
    if env is None:
        g = g.drop_duplicates("SNP")
    y = -np.log10(np.clip(g[column].to_numpy(float), 1e-300, 1))
    ax.scatter(g.pos_mb, y, s=18, color=color, edgecolors="white", linewidths=0.25, alpha=0.9)
    ax.axhline(-np.log10(5e-8), color="#999999", lw=0.65, ls="--")
    if i == 0:
        ax.text(0.98, 0.90, "AT1G11560", transform=ax.transAxes, ha="right", va="top", fontsize=7, color=NAVY)
        panel_label(ax, "a")
    ax.set_ylabel("−log₁₀ P", fontsize=7)
    ax.set_title(title, loc="left", fontsize=8, color="#333333")
    ax.set_xlim(harm.pos_mb.min() - 0.0005, harm.pos_mb.max() + 0.0005)
    ax.tick_params(labelsize=7)
    if i < 2:
        ax.set_xticklabels([])
    else:
        ax.set_xlabel("Chromosome 1 position (Mb)")

# b: LD among the 48 retained instruments.
ax = fig.add_subplot(gs[0, 1])
clean_axis(ax)
im = ax.imshow(ld_mat, cmap="YlOrBr", vmin=0, vmax=1, interpolation="nearest", aspect="equal")
ax.set_xticks([])
ax.set_yticks([])
ax.set_title("b  LD among retained instruments", loc="left", fontweight="bold")
cb = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
cb.set_label("LD r²", fontsize=8)
cb.ax.tick_params(labelsize=7, length=2)

# c: environment-stratified forest plot.
ax = fig.add_subplot(gs[1, 0])
clean_axis(ax)
methods = [("ivw_fixed", "Fixed IVW", BLUE), ("ivw_random", "Random IVW", RUST), ("mr_egger", "MR-Egger", PLUM)]
rows = []
y = 0
for env in ["10C", "16C"]:
    for method, label, color in methods:
        row = strat[(strat.environment == env) & (strat.method == method)].iloc[0]
        rows.append((y, env, label, color, float(row.beta), float(row.se)))
        y += 1
    y += 0.45
for pos, env, label, color, beta, se in rows:
    ax.errorbar(beta, pos, xerr=1.96 * se, fmt="o", color=color, ms=4.5, capsize=2.5, lw=1.0)
ax.axvline(0, color="#777777", lw=0.75)
ax.set_yticks([r[0] for r in rows])
ax.set_yticklabels([f"{r[1]} {r[2]}" for r in rows], fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("Environment-stratified MR estimate (95% CI)")
ax.set_title("c  Stratified estimates", loc="left", fontweight="bold")

# d: primary and proxy environment slopes.
ax = fig.add_subplot(gs[1, 1])
clean_axis(ax)
results = []
for label, path, color in [
    ("Primary\nLD covariance", "results/real/arabidopsis_baseline_AT1G11560_diag/results.json", BLUE),
    ("Sensitivity\nphenotype proxy", "results/real/arabidopsis_baseline_AT1G11560_envproxy/results.json", RUST),
]:
    d = json.loads((ROOT / path).read_text())['result']
    results.append((label, float(d['slope']), float(d['slope_se']), color, float(d['slope_pval'])))
for i, (label, beta, se, color, pval) in enumerate(results):
    ax.errorbar(beta, i, xerr=1.96 * se, fmt="o", ms=5, color=color, capsize=3, lw=1.1)
    ax.text(0.02, i + 0.14, f"P={pval:.3f}", transform=ax.get_yaxis_transform(), fontsize=7, color=color)
ax.axvline(0, color="#777777", lw=0.75)
ax.set_yticks(range(len(results)))
ax.set_yticklabels([r[0] for r in results], fontsize=7)
ax.set_xlabel("Environment slope (95% CI)")
ax.set_title("d  Environment-effect estimate", loc="left", fontweight="bold")
ax.set_xlim(-0.45, 0.35)
for ax, label in zip([fig.axes[0], fig.axes[3], fig.axes[4], fig.axes[5]], "abcd"):
    # Labels are already drawn for a/b/c/d where needed; this keeps the layout stable.
    pass
save(fig, "arabidopsis_case")


# Figure 1: plant-specific workflow schematic, with the scientific data structure visible.
fig = plt.figure(figsize=(7.4, 4.5))
gs = fig.add_gridspec(2, 2, left=0.06, right=0.97, bottom=0.08, top=0.94,
                      wspace=0.30, hspace=0.45)

# a: accession and environment context.
ax = fig.add_subplot(gs[0, 0])
ax.axis("off")
panel_label(ax, "a")
ax.set_title("Plant context", loc="left", fontsize=9, fontweight="bold", color=NAVY)
ax.text(0.02, 0.78, "same accession panel", transform=ax.transAxes, fontsize=7, color="#555555")
for i, (label, color) in enumerate([("control", GREEN), ("stress 1", GOLD), ("stress 2", RUST)]):
    y = 0.58 - i * 0.22
    ax.text(0.02, y, label, transform=ax.transAxes, fontsize=7, va="center")
    for j in range(8):
        ax.add_patch(Circle((0.42 + j * 0.065, y), 0.022, transform=ax.transAxes,
                            facecolor=color, edgecolor="white", lw=0.5))
ax.text(0.42, 0.08, "accessions measured across environments", transform=ax.transAxes,
        fontsize=7, color="#555555")

# b: common SNP-by-environment grid.
ax = fig.add_subplot(gs[0, 1])
ax.axis("off")
panel_label(ax, "b")
ax.set_title("Common SNP × environment grid", loc="left", fontsize=9, fontweight="bold", color=NAVY)
mat = np.array([[0, 1, 1, 0], [1, 1, 0, 1], [0, 1, 0, 1], [1, 0, 1, 1], [1, 1, 1, 0], [0, 0, 1, 1]])
colors = np.where(mat == 1, BLUE, "#E7ECEC")
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.add_patch(Rectangle((0.22 + j * 0.12, 0.24 + (mat.shape[0] - 1 - i) * 0.085),
                               0.10, 0.065, transform=ax.transAxes, facecolor=colors[i, j],
                               edgecolor="white", lw=0.8))
for j, label in enumerate(["E1", "E2", "E3", "E4"]):
    ax.text(0.27 + j * 0.12, 0.80, label, transform=ax.transAxes, ha="center", fontsize=7)
ax.add_patch(Rectangle((0.67, 0.66), 0.045, 0.045, transform=ax.transAxes,
                       facecolor=BLUE, edgecolor="white", lw=0.4))
ax.text(0.73, 0.682, "retained", transform=ax.transAxes, fontsize=6.5, va="center")
ax.add_patch(Rectangle((0.67, 0.57), 0.045, 0.045, transform=ax.transAxes,
                       facecolor="#E7ECEC", edgecolor="white", lw=0.4))
ax.text(0.73, 0.592, "not retained", transform=ax.transAxes, fontsize=6.5, va="center")
ax.text(0.08, 0.52, "SNPs", transform=ax.transAxes, rotation=90, va="center", fontsize=7)
ax.text(0.22, 0.10, "complete rows prevent instrument-composition changes between environments",
        transform=ax.transAxes, fontsize=7, color="#555555")

# c: covariance-aware model.
ax = fig.add_subplot(gs[1, 0])
ax.axis("off")
panel_label(ax, "c")
ax.set_title("Covariance-aware estimation", loc="left", fontsize=9, fontweight="bold", color=NAVY)
ax.text(0.03, 0.70, r"$r_{jk}=\theta_0+\theta_1 z_k+\varepsilon_{jk}$", transform=ax.transAxes,
        fontsize=13, color=NAVY)
ax.text(0.03, 0.48, "signed LD", transform=ax.transAxes, fontsize=7, color=BLUE)
ax.text(0.03, 0.30, "environment correlation", transform=ax.transAxes, fontsize=7, color=GREEN)
for y, color in [(0.50, BLUE), (0.32, GREEN)]:
    for j in range(4):
        for i in range(4):
            val = 0.25 + 0.12 * ((i + j) % 3)
            ax.add_patch(Rectangle((0.57 + j * 0.055, y + i * 0.032), 0.045, 0.025,
                                   transform=ax.transAxes, facecolor=mpl.colors.to_rgba(color, val + 0.25),
                                   edgecolor="white", lw=0.3))
ax.text(0.57, 0.13, "GLS + rank-aware Q", transform=ax.transAxes, fontsize=7, color="#555555")

# d: results and audit trail.
ax = fig.add_subplot(gs[1, 1])
ax.axis("off")
panel_label(ax, "d")
ax.set_title("Plant MR report", loc="left", fontsize=9, fontweight="bold", color=NAVY)
for y, (head, body, color) in zip([0.80, 0.50, 0.20], [
    ("Primary estimates", "IVW / Wald / Egger\nEnvironment slope", BLUE),
    ("Diagnostics", "LD, heterogeneity\nPleiotropy sensitivity", RUST),
    ("Traceability", "JSON + TSV +\nMarkdown report", PLUM),
]):
    ax.add_patch(Rectangle((0.04, y - 0.045), 0.07, 0.12, transform=ax.transAxes,
                           facecolor=color, edgecolor="none"))
    ax.text(0.15, y + 0.015, head, transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="center", color=NAVY)
    ax.text(0.15, y - 0.085, body, transform=ax.transAxes, fontsize=7,
            va="top", color="#555555", linespacing=1.2)

save(fig, "plantmr_workflow")
print("generated gxe_ld_stress, arabidopsis_case and plantmr_workflow")
