"""Significantly associated locus detection from normalized GWAS results."""

from __future__ import annotations

import numpy as np
import pandas as pd


_SAL_COLUMNS = [
    "sal_id", "chromosome", "start", "end", "lead_variant", "lead_pval", "n_variants", "variants"
]


def detect_sal(
    gwas: pd.DataFrame,
    *,
    ld_matrix: pd.DataFrame | None = None,
    p_lead: float = 5e-8,
    p_secondary: float = 1e-5,
    r2_threshold: float = 0.2,
    window: int = 500_000,
    min_neighbors: int = 0,
) -> pd.DataFrame:
    """Detect and merge lead-SNP loci using p-value, window and optional LD."""
    required = {"variant_id", "chromosome", "position", "pval"}
    missing = sorted(required - set(gwas.columns))
    if missing:
        raise ValueError(f"GWAS table missing SAL columns: {', '.join(missing)}")
    if not 0 < p_lead <= p_secondary <= 1:
        raise ValueError("SAL thresholds must satisfy 0 < p_lead <= p_secondary <= 1")
    if window < 0 or not 0 <= r2_threshold <= 1 or min_neighbors < 0:
        raise ValueError("invalid SAL window, r2_threshold or min_neighbors")
    work = gwas[["variant_id", "chromosome", "position", "pval"]].copy()
    work["variant_id"] = work["variant_id"].astype(str)
    work["chromosome"] = work["chromosome"].astype(str)
    work["position"] = pd.to_numeric(work["position"], errors="coerce")
    work["pval"] = pd.to_numeric(work["pval"], errors="coerce")
    if work.isna().any().any() or work["variant_id"].duplicated().any():
        raise ValueError("GWAS SAL input contains missing values or duplicate variants")
    candidates = work.loc[work["pval"] <= p_lead].sort_values(["pval", "chromosome", "position", "variant_id"])
    used: set[str] = set()
    records = []
    for lead in candidates.itertuples(index=False):
        if lead.variant_id in used:
            continue
        region = work.loc[
            (work["chromosome"] == lead.chromosome)
            & (work["position"] - float(lead.position)).abs().le(window)
            & (work["pval"] <= p_secondary)
        ].copy()
        if ld_matrix is not None:
            if lead.variant_id not in ld_matrix.index or lead.variant_id not in ld_matrix.columns:
                raise ValueError(f"LD matrix is missing SAL lead variant: {lead.variant_id}")
            keep = []
            for variant in region["variant_id"]:
                if variant == lead.variant_id:
                    keep.append(variant)
                elif variant not in ld_matrix.index or variant not in ld_matrix.columns:
                    raise ValueError(f"LD matrix is missing SAL variant: {variant}")
                elif float(ld_matrix.loc[lead.variant_id, variant]) ** 2 >= r2_threshold:
                    keep.append(variant)
            region = region.loc[region["variant_id"].isin(keep)]
        if len(region) - 1 < min_neighbors:
            continue
        region = region.sort_values(["position", "variant_id"], kind="mergesort")
        members = region["variant_id"].astype(str).tolist()
        used.update(members)
        records.append(
            {
                "sal_id": f"SAL{len(records) + 1:04d}",
                "chromosome": lead.chromosome,
                "start": int(region["position"].min()),
                "end": int(region["position"].max()),
                "lead_variant": lead.variant_id,
                "lead_pval": float(lead.pval),
                "n_variants": int(len(members)),
                "variants": ";".join(members),
            }
        )
    return pd.DataFrame(records, columns=_SAL_COLUMNS)
