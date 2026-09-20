"""GO-term over-representation analysis with explicit universe handling."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


def _bh(pvalues: np.ndarray) -> np.ndarray:
    order = np.argsort(pvalues)
    ranked = pvalues[order]
    adjusted = np.minimum.accumulate((ranked * len(ranked) / np.arange(1, len(ranked) + 1))[::-1])[::-1]
    output = np.empty_like(adjusted)
    output[order] = np.minimum(adjusted, 1.0)
    return output


def go_enrichment(
    selected_features: Iterable[str],
    annotation: pd.DataFrame,
    *,
    universe: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Return one-sided hypergeometric GO enrichment with BH q-values.

    Annotation is one row per ``feature_id``/``go_term`` pair and may contain
    ``term_name``. If no universe is supplied, all annotated features are used;
    callers should provide the tested feature universe when only a subset was
    measured.
    """
    required = {"feature_id", "go_term"}
    missing = sorted(required - set(annotation.columns))
    if missing:
        raise ValueError(f"GO annotation missing required columns: {', '.join(missing)}")
    ann = annotation[[c for c in ["feature_id", "go_term", "term_name"] if c in annotation.columns]].copy()
    ann["feature_id"] = ann["feature_id"].astype(str)
    ann["go_term"] = ann["go_term"].astype(str)
    ann = ann.drop_duplicates(["feature_id", "go_term"])
    selected = {str(item) for item in selected_features}
    if not selected:
        raise ValueError("selected_features must not be empty")
    universe_set = {str(item) for item in universe} if universe is not None else set(ann["feature_id"])
    universe_set &= set(ann["feature_id"])
    selected_set = selected & universe_set
    if not selected_set or not universe_set:
        raise ValueError("selected features do not overlap the annotated universe")
    n = len(selected_set)
    N = len(universe_set)
    records = []
    for term, group in ann.groupby("go_term", sort=True):
        term_features = set(group["feature_id"]) & universe_set
        K = len(term_features)
        overlap = len(selected_set & term_features)
        if K == 0 or overlap == 0:
            continue
        pval = float(stats.hypergeom.sf(overlap - 1, N, K, n))
        records.append(
            {
                "go_term": term,
                "term_name": str(group["term_name"].iloc[0]) if "term_name" in group else term,
                "overlap": int(overlap),
                "selected_total": int(n),
                "term_size": int(K),
                "universe_size": int(N),
                "fold_enrichment": float((overlap / n) / (K / N)),
                "pval": pval,
            }
        )
    columns = [
        "go_term", "term_name", "overlap", "selected_total", "term_size", "universe_size",
        "fold_enrichment", "pval", "qval",
    ]
    if not records:
        return pd.DataFrame(columns=columns)
    result = pd.DataFrame(records)
    result["qval"] = _bh(result["pval"].to_numpy(dtype=float))
    return result.sort_values(["qval", "pval", "go_term"], kind="mergesort").reset_index(drop=True)[columns]
