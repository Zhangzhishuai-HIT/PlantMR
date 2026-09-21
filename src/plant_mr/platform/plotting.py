"""Publication-friendly non-interactive plots for PlantMR runs."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats


def _save(fig: plt.Figure, prefix: str | Path) -> list[Path]:
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    outputs = [prefix.with_suffix(".png"), prefix.with_suffix(".pdf")]
    fig.savefig(outputs[0], dpi=180, bbox_inches="tight")
    fig.savefig(outputs[1], bbox_inches="tight")
    plt.close(fig)
    return outputs


def plot_manhattan(gwas: pd.DataFrame, prefix: str | Path, *, p_threshold: float = 5e-8) -> list[Path]:
    if not {"pval"}.issubset(gwas.columns):
        raise ValueError("Manhattan plot requires pval")
    work = gwas.copy()
    work["pval"] = pd.to_numeric(work["pval"], errors="coerce").clip(lower=np.finfo(float).tiny, upper=1)
    if "chromosome" in work.columns and "position" in work.columns:
        work["chromosome"] = work["chromosome"].astype(str)
        work["position"] = pd.to_numeric(work["position"], errors="coerce")
        work = work.sort_values(["chromosome", "position"], kind="mergesort")
        chroms = list(dict.fromkeys(work["chromosome"]))
        offsets = {}
        offset = 0.0
        xs = []
        colors = []
        for index, chrom in enumerate(chroms):
            part = work.loc[work["chromosome"] == chrom]
            positions = part["position"].to_numpy(float) + offset
            xs.extend(positions)
            colors.extend(["#2c7fb8" if index % 2 == 0 else "#fdae61"] * len(part))
            offsets[chrom] = offset
            offset = float(positions.max() + 1) if len(positions) else offset
        y = -np.log10(work["pval"].to_numpy(float))
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.scatter(xs, y, c=colors, s=10, linewidths=0)
        ax.axhline(-np.log10(p_threshold), color="#d7301f", linestyle="--", linewidth=0.8)
        ax.set_xlabel("Genomic position")
    else:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.scatter(np.arange(len(work)), -np.log10(work["pval"]), s=10)
        ax.set_xlabel("Variant rank")
    ax.set_ylabel("-log10(P)")
    ax.set_title("PlantMR GWAS associations")
    return _save(fig, prefix)


def plot_qq(gwas: pd.DataFrame, prefix: str | Path) -> list[Path]:
    if "pval" not in gwas.columns:
        raise ValueError("QQ plot requires pval")
    p = pd.to_numeric(gwas["pval"], errors="coerce").dropna().clip(lower=np.finfo(float).tiny, upper=1).sort_values()
    observed = -np.log10(p.to_numpy(float))
    expected = -np.log10((np.arange(1, len(p) + 1) - 0.5) / len(p))
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(expected, observed, s=14)
    limit = max(float(expected.max(initial=1)), float(observed.max(initial=1)))
    ax.plot([0, limit], [0, limit], color="black", linewidth=0.8)
    ax.set_xlabel("Expected -log10(P)")
    ax.set_ylabel("Observed -log10(P)")
    ax.set_title("PlantMR Q-Q plot")
    return _save(fig, prefix)


def plot_mr_forest(methods: pd.DataFrame, prefix: str | Path) -> list[Path]:
    required = {"method", "beta", "se"}
    missing = sorted(required - set(methods.columns))
    if missing:
        raise ValueError(f"MR forest plot missing columns: {', '.join(missing)}")
    work = methods.copy().reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.45 * len(work) + 1)))
    y = np.arange(len(work))
    beta = pd.to_numeric(work["beta"], errors="coerce").to_numpy(float)
    se = pd.to_numeric(work["se"], errors="coerce").to_numpy(float)
    ax.errorbar(beta, y, xerr=1.96 * se, fmt="o", color="#2166ac", capsize=3)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(work["method"].astype(str))
    ax.set_xlabel("MR effect (95% CI)")
    ax.set_title("PlantMR MR estimates")
    return _save(fig, prefix)


def plot_network(network: pd.DataFrame, prefix: str | Path) -> list[Path]:
    required = {"source", "target"}
    missing = sorted(required - set(network.columns))
    if missing:
        raise ValueError(f"network plot missing columns: {', '.join(missing)}")
    import networkx as nx

    graph = nx.Graph()
    for row in network.itertuples(index=False):
        weight = float(getattr(row, "weight", 1.0))
        graph.add_edge(str(row.source), str(row.target), weight=weight)
    fig, ax = plt.subplots(figsize=(6, 5))
    if graph.number_of_nodes():
        position = nx.spring_layout(graph, seed=17, weight="weight")
        nx.draw_networkx_nodes(graph, position, node_color="#74add1", node_size=450, ax=ax)
        nx.draw_networkx_edges(graph, position, width=1.2, edge_color="#636363", ax=ax)
        nx.draw_networkx_labels(graph, position, font_size=8, ax=ax)
    ax.set_axis_off()
    ax.set_title("PlantMR evidence network")
    return _save(fig, prefix)
