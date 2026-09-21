"""MR evidence networks and deterministic module summaries."""

from __future__ import annotations

import math
import numpy as np
import pandas as pd


def build_mr_network(edges: pd.DataFrame, *, p_threshold: float = 0.05) -> pd.DataFrame:
    """Combine reciprocal MR directions into undirected weighted relationships."""
    required = {"source", "target", "beta", "se", "pval"}
    missing = sorted(required - set(edges.columns))
    if missing:
        raise ValueError(f"MR network edges missing columns: {', '.join(missing)}")
    work = edges[list(required)].copy()
    work["source"] = work["source"].astype(str)
    work["target"] = work["target"].astype(str)
    for column in ("beta", "se", "pval"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
    if work.isna().any().any() or (work["se"] <= 0).any() or ((work["pval"] < 0) | (work["pval"] > 1)).any():
        raise ValueError("MR network edges contain invalid beta, se or pval values")
    work = work.loc[work["source"] != work["target"]].copy()
    work = work.loc[work["pval"] <= p_threshold].copy()
    records = []
    for (node_a, node_b), group in work.groupby(
        work.apply(lambda row: tuple(sorted((row["source"], row["target"]))), axis=1), sort=True
    ):
        forward = group.loc[(group["source"] == node_a) & (group["target"] == node_b)]
        reverse = group.loc[(group["source"] == node_b) & (group["target"] == node_a)]
        f = forward.sort_values("pval").iloc[0] if not forward.empty else None
        r = reverse.sort_values("pval").iloc[0] if not reverse.empty else None
        p_values = [float(row["pval"]) for row in (f, r) if row is not None]
        records.append(
            {
                "node_a": node_a,
                "node_b": node_b,
                "beta_ab": float(f["beta"]) if f is not None else np.nan,
                "se_ab": float(f["se"]) if f is not None else np.nan,
                "pval_ab": float(f["pval"]) if f is not None else np.nan,
                "beta_ba": float(r["beta"]) if r is not None else np.nan,
                "se_ba": float(r["se"]) if r is not None else np.nan,
                "pval_ba": float(r["pval"]) if r is not None else np.nan,
                "reciprocal": bool(f is not None and r is not None),
                "weight": float(np.mean([-math.log10(max(value, 1e-300)) for value in p_values])),
            }
        )
    columns = ["node_a", "node_b", "beta_ab", "se_ab", "pval_ab", "beta_ba", "se_ba", "pval_ba", "reciprocal", "weight"]
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(records, columns=columns).sort_values(["weight", "node_a", "node_b"], ascending=[False, True, True], kind="mergesort").reset_index(drop=True)


def identify_network_modules(network: pd.DataFrame, *, min_nodes: int = 5) -> pd.DataFrame:
    """Identify weighted communities and scaled degree hub scores.

    This is a deterministic greedy-modularity approximation to ClusterONE. It
    reports the algorithm name in the output instead of claiming method identity.
    """
    required = {"node_a", "node_b", "weight"}
    missing = sorted(required - set(network.columns))
    if missing:
        raise ValueError(f"network module input missing columns: {', '.join(missing)}")
    if min_nodes < 2:
        raise ValueError("min_nodes must be at least 2")
    try:
        import networkx as nx
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise ImportError("network module requires networkx") from exc
    graph = nx.Graph()
    for row in network.itertuples(index=False):
        graph.add_edge(str(row.node_a), str(row.node_b), weight=float(row.weight))
    if graph.number_of_nodes() == 0:
        return pd.DataFrame(columns=["module_id", "node", "module_size", "degree", "hub_score", "algorithm"])
    communities = list(nx.algorithms.community.greedy_modularity_communities(graph, weight="weight"))
    communities = sorted((sorted(group) for group in communities if len(group) >= min_nodes), key=lambda group: tuple(group))
    degree = dict(graph.degree(weight="weight"))
    records = []
    for index, community in enumerate(communities, start=1):
        maximum = max((degree[node] for node in community), default=0.0)
        for node in community:
            records.append(
                {
                    "module_id": f"M{index:04d}",
                    "node": node,
                    "module_size": len(community),
                    "degree": float(degree[node]),
                    "hub_score": float(degree[node] / maximum) if maximum else 0.0,
                    "algorithm": "greedy-modularity-approximation",
                }
            )
    if not records:
        return pd.DataFrame(columns=["module_id", "node", "module_size", "degree", "hub_score", "algorithm"])
    return pd.DataFrame(records).sort_values(["module_id", "hub_score", "node"], ascending=[True, False, True], kind="mergesort").reset_index(drop=True)


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
    """Filter supplied causal/associational edges and report FDR plus cycles."""
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
    from .enrichment import _bh

    work["qval"] = _bh(work["pval"].to_numpy(dtype=float))
    work["significant"] = True
    work = work.sort_values(["qval", "pval", "source", "target"], kind="mergesort").reset_index(drop=True)
    summary = {
        "n_significant_edges": int(len(work)),
        "n_nodes": int(len(set(work["source"]).union(work["target"]))),
        "has_cycle": bool(_has_cycle(work)),
    }
    return work, summary
