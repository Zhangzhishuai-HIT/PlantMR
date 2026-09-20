"""Causal-edge network summaries with transparent graph diagnostics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .enrichment import _bh


def _has_cycle(edges: pd.DataFrame) -> bool:
    adjacency: dict[str, set[str]] = {}
    for row in edges.itertuples(index=False):
        adjacency.setdefault(str(row.source), set()).add(str(row.target))
        adjacency.setdefault(str(row.target), set())
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in adjacency.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)


def summarize_causal_network(
    edges: pd.DataFrame,
    *,
    p_threshold: float = 0.05,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Filter causal/associational edges and report FDR plus cycle status.

    This function does not infer causality. It assumes the input edges were
    produced by a tested method and makes that edge table easier to inspect.
    Cycles are reported because they are a diagnostic for a claimed DAG, not
    because they invalidate all biological feedback models.
    """
    required = {"source", "target", "beta", "se", "pval"}
    missing = sorted(required - set(edges.columns))
    if missing:
        raise ValueError(f"network edges missing required columns: {', '.join(missing)}")
    if not 0 < p_threshold <= 1:
        raise ValueError("p_threshold must be within (0, 1]")
    work = edges[["source", "target", "beta", "se", "pval"]].copy()
    work["source"] = work["source"].astype(str)
    work["target"] = work["target"].astype(str)
    for column in ("beta", "se", "pval"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    if work.isna().any().any():
        raise ValueError("network edges contain missing or non-numeric values")
    if (work["se"] <= 0).any() or ((work["pval"] < 0) | (work["pval"] > 1)).any():
        raise ValueError("network se must be positive and pval must lie within [0, 1]")
    work = work.loc[work["pval"] <= p_threshold].copy()
    if work.empty:
        result = work.assign(qval=pd.Series(dtype=float))
        return result, {"n_significant_edges": 0, "n_nodes": 0, "has_cycle": False}
    work["qval"] = _bh(work["pval"].to_numpy(dtype=float))
    work["significant"] = True
    work = work.sort_values(["qval", "pval", "source", "target"], kind="mergesort").reset_index(drop=True)
    summary = {
        "n_significant_edges": int(len(work)),
        "n_nodes": int(len(set(work["source"]).union(work["target"]))),
        "has_cycle": bool(_has_cycle(work)),
    }
    return work, summary
