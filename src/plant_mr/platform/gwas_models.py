"""Matrix-based GWAS models used by the PlantMR CLI."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .genotype import as_genotype_matrix
from .phenotype import as_phenotype_matrix


def _design_covariates(covariates: pd.DataFrame | None, samples: pd.Index) -> tuple[np.ndarray, int]:
    if covariates is None:
        return np.ones((len(samples), 1), dtype=float), 0
    cov = covariates.copy()
    if "sample_id" in cov.columns:
        cov = cov.set_index("sample_id")
    cov.index = cov.index.astype(str)
    missing = samples.difference(cov.index)
    if len(missing):
        raise ValueError(f"covariates are missing samples: {', '.join(missing[:5])}")
    cov = cov.loc[samples]
    cov = cov.apply(pd.to_numeric, errors="coerce")
    if cov.isna().any().any():
        raise ValueError("covariates contain missing or non-numeric values")
    return np.column_stack([np.ones(len(samples)), cov.to_numpy(dtype=float)]), int(cov.shape[1])


def _fit_one(y: np.ndarray, x: np.ndarray, base: np.ndarray, vinv: np.ndarray, model: str) -> tuple[float, float, float]:
    design = np.column_stack([base, x])
    xtv = design.T @ vinv
    information = xtv @ design
    inverse = np.linalg.pinv(information)
    beta = inverse @ xtv @ y
    residual = y - design @ beta
    df = max(1, len(y) - np.linalg.matrix_rank(design))
    sigma2 = float((residual.T @ vinv @ residual) / df)
    se = float(np.sqrt(max(0.0, sigma2 * inverse[-1, -1])))
    if se == 0:
        pval = 0.0 if beta[-1] != 0 else 1.0
    else:
        pval = float(2 * stats.t.sf(abs(beta[-1] / se), df=df))
    return float(beta[-1]), se, pval


def run_matrix_gwas(
    genotype: pd.DataFrame,
    phenotype: pd.DataFrame,
    *,
    trait: str,
    covariates: pd.DataFrame | None = None,
    kinship: pd.DataFrame | None = None,
    model: str = "ols",
    mlm_lambda: float = 1.0,
    ploidy: float = 2.0,
) -> pd.DataFrame:
    """Run OLS or kinship-aware GLS for a sample-by-variant genotype matrix."""
    if model not in {"ols", "mlm", "gemma_mlm"}:
        raise ValueError("model must be one of: ols, mlm, gemma_mlm")
    if mlm_lambda <= 0:
        raise ValueError("mlm_lambda must be positive")
    if ploidy <= 0:
        raise ValueError("ploidy must be positive")
    geno = as_genotype_matrix(genotype).astype(float)
    pheno = as_phenotype_matrix(phenotype)
    if trait not in pheno.columns:
        raise ValueError(f"phenotype trait not found: {trait}")
    y_series = pd.to_numeric(pheno[trait], errors="coerce")
    sample_ids = geno.index.intersection(pheno.index)
    if len(sample_ids) < 3:
        raise ValueError("genotype and phenotype have fewer than three overlapping samples")
    y_series = y_series.loc[sample_ids]
    valid_y = y_series.notna()
    sample_ids = sample_ids[valid_y.to_numpy()]
    if len(sample_ids) < 3:
        raise ValueError("fewer than three samples have a non-missing phenotype")
    y = y_series.loc[sample_ids].to_numpy(dtype=float)
    geno = geno.loc[sample_ids]
    base, n_covariates = _design_covariates(covariates, sample_ids)
    if model == "ols":
        vinv = np.eye(len(sample_ids))
    else:
        if kinship is None:
            raise ValueError("mlm/gemma_mlm requires a kinship matrix")
        k = kinship.copy()
        k.index = k.index.astype(str)
        k.columns = k.columns.astype(str)
        missing = sample_ids.difference(k.index)
        if len(missing):
            raise ValueError(f"kinship is missing samples: {', '.join(missing[:5])}")
        k = k.loc[sample_ids, sample_ids].to_numpy(dtype=float)
        k = (k + k.T) / 2.0
        v = k + mlm_lambda * np.eye(len(sample_ids))
        v += 1e-8 * np.eye(len(sample_ids))
        vinv = np.linalg.pinv(v)
    rows = []
    for variant_id in geno.columns:
        x = geno[variant_id].to_numpy(dtype=float)
        missing_x = ~np.isfinite(x)
        if missing_x.any():
            x[missing_x] = np.nanmean(x)
        if not np.isfinite(x).all() or np.std(x) == 0:
            continue
        beta, se, pval = _fit_one(y, x, base, vinv, model)
        af = float(np.mean(x) / ploidy)
        rows.append(
            {
                "variant_id": str(variant_id),
                "trait": str(trait),
                "beta": beta,
                "se": se,
                "pval": pval,
                "n": int(len(sample_ids)),
                "maf": float(min(af, 1 - af)),
                "model": model,
                "n_covariates": n_covariates,
            }
        )
    if not rows:
        raise ValueError("no variants had usable dosage variation")
    return pd.DataFrame(rows).sort_values(["pval", "variant_id"], kind="mergesort").reset_index(drop=True)
