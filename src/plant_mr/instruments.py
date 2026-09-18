from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def clump_instruments(table: pd.DataFrame, ld_matrix: pd.DataFrame, r2_threshold: float = 0.01) -> Tuple[pd.DataFrame, List[str]]:
    """Greedy LD clumping, retaining the most significant exposure SNP first."""
    if not 0 <= r2_threshold <= 1:
        raise ValueError("r2_threshold must be within [0, 1]")
    required = {"SNP", "exposure_pval"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"missing clumping columns: {', '.join(sorted(missing))}")
    if not isinstance(ld_matrix, pd.DataFrame) or ld_matrix.empty:
        raise ValueError("LD matrix must be a non-empty square DataFrame")
    if ld_matrix.index.duplicated().any() or ld_matrix.columns.duplicated().any():
        raise ValueError("LD matrix row and column identifiers must be unique")
    if set(ld_matrix.index) != set(ld_matrix.columns):
        raise ValueError("LD matrix row and column identifiers must match")
    snps = table["SNP"].astype(str).tolist()
    missing_ld = sorted(set(snps).difference(ld_matrix.index))
    if missing_ld:
        raise ValueError(f"LD matrix is missing SNPs: {', '.join(missing_ld)}")
    ordered = table.sort_values(["exposure_pval", "SNP"], kind="mergesort").reset_index(drop=True)
    kept = []
    removed = []
    for row in ordered.itertuples(index=False):
        snp = str(row.SNP)
        if not kept:
            kept.append(snp)
            continue
        correlations = pd.to_numeric(ld_matrix.loc[snp, kept], errors="coerce").to_numpy(dtype=float)
        if np.any(~np.isfinite(correlations)):
            raise ValueError(f"LD matrix contains non-finite values for {snp}")
        if np.any(correlations ** 2 > r2_threshold):
            removed.append(snp)
        else:
            kept.append(snp)
    return ordered[ordered["SNP"].isin(kept)].reset_index(drop=True), removed


def select_instruments(table: pd.DataFrame, p_threshold: float = 5e-8,
                       f_threshold: float = 10.0, maf_threshold: float = 0.01) -> Tuple[pd.DataFrame, Dict[str, int]]:
    required = {"SNP", "exposure_beta", "exposure_se", "exposure_pval", "eaf"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"missing instrument columns: {', '.join(sorted(missing))}")
    work = table.copy()
    work["f_stat"] = (work["exposure_beta"] / work["exposure_se"]) ** 2
    audit = {"input": int(len(work)), "excluded_pval": 0, "excluded_f": 0, "excluded_maf": 0, "excluded_ld": 0, "selected": 0}
    p_mask = work["exposure_pval"] <= p_threshold
    audit["excluded_pval"] = int((~p_mask).sum())
    work = work.loc[p_mask].copy()
    f_mask = work["f_stat"] >= f_threshold
    audit["excluded_f"] = int((~f_mask).sum())
    work = work.loc[f_mask].copy()
    maf = np.minimum(work["eaf"], 1 - work["eaf"])
    maf_mask = maf >= maf_threshold
    audit["excluded_maf"] = int((~maf_mask).sum())
    work = work.loc[maf_mask].copy()
    work = work.sort_values("SNP").reset_index(drop=True)
    audit["selected"] = int(len(work))
    return work, audit
