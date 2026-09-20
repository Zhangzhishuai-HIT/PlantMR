"""Transparent genotype-by-phenotype association for PlantMR projects."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def run_gwas(
    genotype: pd.DataFrame,
    phenotype: pd.DataFrame,
    *,
    trait: str,
    ploidy: float = 2.0,
) -> pd.DataFrame:
    """Run per-variant ordinary least-squares association for one trait.

    The input contract is long format: genotype has ``sample_id``,
    ``variant_id`` and numeric ``dosage``; phenotype has ``sample_id``,
    ``trait`` and numeric ``value``. No population structure or covariates are
    fitted here; the result is intended as a transparent baseline and as an
    input producer for downstream QTL/MR workflows.
    """
    required_g = {"sample_id", "variant_id", "dosage"}
    required_p = {"sample_id", "trait", "value"}
    missing_g = sorted(required_g - set(genotype.columns))
    missing_p = sorted(required_p - set(phenotype.columns))
    if missing_g:
        raise ValueError(f"genotype: missing required columns: {', '.join(missing_g)}")
    if missing_p:
        raise ValueError(f"phenotype: missing required columns: {', '.join(missing_p)}")
    if ploidy <= 0:
        raise ValueError("ploidy must be greater than zero")

    pheno = phenotype.loc[phenotype["trait"].astype(str) == str(trait), ["sample_id", "value"]].copy()
    if pheno.empty:
        raise ValueError(f"phenotype trait not found: {trait}")
    if pheno["sample_id"].duplicated().any():
        raise ValueError("phenotype: sample_id must be unique for a selected trait")
    pheno["value"] = pd.to_numeric(pheno["value"], errors="coerce")
    if pheno["value"].isna().any() or not np.isfinite(pheno["value"].to_numpy()).all():
        raise ValueError("phenotype: value contains non-finite values")

    geno = genotype[["sample_id", "variant_id", "dosage"]].copy()
    if geno.duplicated(["sample_id", "variant_id"]).any():
        raise ValueError("genotype: sample_id/variant_id pairs must be unique")
    geno["dosage"] = pd.to_numeric(geno["dosage"], errors="coerce")
    if geno["dosage"].isna().any() or not np.isfinite(geno["dosage"].to_numpy()).all():
        raise ValueError("genotype: dosage contains non-finite values")
    if (geno["dosage"] < 0).any() or (geno["dosage"] > ploidy).any():
        raise ValueError(f"genotype: dosage must lie within [0, {ploidy:g}]")

    merged = geno.merge(pheno, on="sample_id", how="inner")
    if merged.empty:
        raise ValueError("genotype and phenotype have no overlapping samples")
    rows = []
    for variant_id, group in merged.groupby("variant_id", sort=True):
        x = group["dosage"].to_numpy(dtype=float)
        y = group["value"].to_numpy(dtype=float)
        n = len(x)
        if n < 3:
            continue
        x_centered = x - x.mean()
        y_centered = y - y.mean()
        ssx = float(np.dot(x_centered, x_centered))
        if ssx <= 0:
            continue
        beta = float(np.dot(x_centered, y_centered) / ssx)
        residual = y - (y.mean() + beta * x_centered)
        sse = float(np.dot(residual, residual))
        se = float(np.sqrt((sse / (n - 2)) / ssx))
        if not np.isfinite(se) or se <= 0:
            pval = 0.0 if abs(beta) > 0 else 1.0
            se = float("nan")
        else:
            pval = float(2 * stats.t.sf(abs(beta / se), df=n - 2))
        mean_dosage = float(x.mean())
        maf = float(min(mean_dosage / ploidy, 1.0 - mean_dosage / ploidy))
        rows.append(
            {
                "variant_id": str(variant_id),
                "trait": str(trait),
                "beta": beta,
                "se": se,
                "pval": pval,
                "n": int(n),
                "maf": maf,
                "mean_dosage": mean_dosage,
            }
        )
    if not rows:
        raise ValueError("no variants had at least three samples and non-zero dosage variance")
    return pd.DataFrame(rows).sort_values(["pval", "variant_id"], kind="mergesort").reset_index(drop=True)
