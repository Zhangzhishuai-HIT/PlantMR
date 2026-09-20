"""Unified eQTL, mQTL and pQTL association interface."""

from __future__ import annotations

import pandas as pd

from .gwas import run_gwas


_ALLOWED_TYPES = {"expression", "metabolite", "protein"}


def run_qtl(
    genotype: pd.DataFrame,
    molecular: pd.DataFrame,
    *,
    feature_id: str,
    molecular_type: str,
    ploidy: float = 2.0,
) -> pd.DataFrame:
    """Associate one molecular feature with genotype using the GWAS baseline.

    The molecular table uses ``sample_id``, ``feature_id`` and ``value``.
    Results intentionally share the GWAS effect/SE/P-value definitions so they
    can be used as exposure summary statistics after explicit conversion.
    """
    if molecular_type not in _ALLOWED_TYPES:
        allowed = ", ".join(sorted(_ALLOWED_TYPES))
        raise ValueError(f"molecular_type must be one of: {allowed}")
    if "feature_id" not in molecular.columns:
        raise ValueError("molecular: missing required column: feature_id")
    selected = molecular.loc[molecular["feature_id"].astype(str) == str(feature_id)].copy()
    if selected.empty:
        raise ValueError(f"molecular feature not found: {feature_id}")
    selected = selected.rename(columns={"feature_id": "trait"})
    result = run_gwas(genotype, selected, trait=str(feature_id), ploidy=ploidy)
    result = result.rename(columns={"trait": "feature_id"})
    result.insert(2, "molecular_type", molecular_type)
    return result[
        ["variant_id", "feature_id", "molecular_type", "beta", "se", "pval", "n", "maf", "mean_dosage"]
    ]
