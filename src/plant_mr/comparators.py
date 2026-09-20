"""External summary-data MR-GxE comparator.

This module implements the summary-data, weighted-score form of MR-GxE
following Spiller et al. (2019): estimate score-exposure and score-outcome
associations across prespecified environment strata, then regress the latter
on the former with an intercept. It is a comparator for the PlantMR
environment-effect model, not a replacement for the full individual-level
MR-GxE framework.
"""

from dataclasses import dataclass
import math
from typing import Optional

import numpy as np
import pandas as pd


_REQUIRED = {
    "SNP", "environment", "environment_value", "exposure_beta", "exposure_se",
    "outcome_beta", "outcome_se",
}


@dataclass(frozen=True)
class MRGxEResult:
    method: str
    causal_slope: float
    causal_slope_se: float
    causal_slope_pval: float
    pleiotropy_intercept: float
    intercept_se: float
    intercept_pval: float
    n_snp: int
    n_environment: int
    covariance_source: str
    score_weights: tuple
    score_exposure: tuple
    score_outcome: tuple


def _p_value(z: float) -> float:
    return math.erfc(abs(float(z)) / math.sqrt(2.0))


def _validate_corr(correlation: Optional[pd.DataFrame], labels, name: str) -> np.ndarray:
    labels = [str(x) for x in labels]
    if correlation is None:
        return np.eye(len(labels), dtype=float)
    if not isinstance(correlation, pd.DataFrame) or correlation.empty:
        raise ValueError("%s must be a non-empty square DataFrame" % name)
    matrix = correlation.copy()
    matrix.index = matrix.index.astype(str)
    matrix.columns = matrix.columns.astype(str)
    if set(matrix.index) != set(labels) or set(matrix.columns) != set(labels):
        raise ValueError("%s identifiers must exactly match the input table" % name)
    values = matrix.loc[labels, labels].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    if not np.isfinite(values).all() or not np.allclose(values, values.T, atol=1e-10):
        raise ValueError("%s must be finite and symmetric" % name)
    if not np.allclose(np.diag(values), 1.0, atol=1e-8):
        raise ValueError("%s must have unit diagonal" % name)
    if np.linalg.eigvalsh(values).min() < -1e-8:
        raise ValueError("%s must be positive semidefinite" % name)
    return values


def _validate_table(table: pd.DataFrame) -> tuple[pd.DataFrame, list, list]:
    if not isinstance(table, pd.DataFrame):
        raise ValueError("summary MR-GxE requires a pandas DataFrame")
    missing = sorted(_REQUIRED.difference(table.columns))
    if missing:
        raise ValueError("summary MR-GxE missing columns: " + ", ".join(missing))
    work = table.copy()
    work["SNP"] = work["SNP"].astype(str)
    work["environment"] = work["environment"].astype(str)
    if work[["SNP", "environment"]].duplicated().any():
        raise ValueError("summary MR-GxE requires one row per SNP and environment")
    numeric = ["environment_value", "exposure_beta", "exposure_se", "outcome_beta", "outcome_se"]
    for col in numeric:
        work[col] = pd.to_numeric(work[col], errors="coerce")
    if work[numeric].isna().any().any() or not np.isfinite(work[numeric].to_numpy()).all():
        raise ValueError("summary MR-GxE requires finite numeric inputs")
    if (work["exposure_beta"] == 0).any() or (work["exposure_se"] <= 0).any() or (work["outcome_se"] <= 0).any():
        raise ValueError("summary MR-GxE requires nonzero exposure beta and positive standard errors")
    snps = sorted(work["SNP"].unique())
    environments = sorted(work["environment"].unique())
    counts = work.groupby("SNP")["environment"].nunique()
    if len(environments) < 2 or counts.nunique() != 1 or counts.iloc[0] != len(environments):
        raise ValueError("summary MR-GxE requires a complete environment grid for every SNP")
    if work["environment_value"].nunique() < 2:
        raise ValueError("summary MR-GxE requires at least two environment values")
    if (work.groupby("environment")["environment_value"].nunique() != 1).any():
        raise ValueError("environment_value must be constant within each environment")
    return work, snps, environments


def _score_covariance(weights, se, ld_corr, env_corr):
    # se is SNP x environment. The Kronecker structure is explicit: LD links
    # SNPs and env_corr links strata, matching the covariance contract used by
    # PlantMR. This is still a summary-data approximation.
    n_snp, n_env = se.shape
    out = np.zeros((n_env, n_env), dtype=float)
    for k in range(n_env):
        for m in range(n_env):
            out[k, m] = env_corr[k, m] * np.sum(
                (weights[:, None] * weights[None, :])
                * (se[:, k][:, None] * se[:, m][None, :])
                * ld_corr
            )
    return out


def summary_mr_gxe(
    table: pd.DataFrame,
    *,
    environment_correlation: Optional[pd.DataFrame] = None,
    ld_correlation: Optional[pd.DataFrame] = None,
    max_iter: int = 50,
) -> MRGxEResult:
    """Run the summary-data MR-GxE three-step comparator.

    A fixed weighted allele score is constructed from exposure associations
    averaged across environments; outcome associations never determine these
    weights. For each environment, score-outcome associations are regressed on
    score-exposure associations with an intercept. The slope is the MR-GxE
    causal estimate and the intercept is the constant-pleiotropy estimate.
    Exposure and outcome ratio-error covariance is approximated from supplied
    LD/environment correlations; if absent, diagonal independence is explicit.
    """
    work, snps, environments = _validate_table(table)
    ordered = work.set_index(["SNP", "environment"]).loc[
        pd.MultiIndex.from_product([snps, environments], names=["SNP", "environment"])
    ].reset_index()
    n_snp, n_env = len(snps), len(environments)
    bx = ordered["exposure_beta"].to_numpy(float).reshape(n_snp, n_env)
    sx = ordered["exposure_se"].to_numpy(float).reshape(n_snp, n_env)
    by = ordered["outcome_beta"].to_numpy(float).reshape(n_snp, n_env)
    sy = ordered["outcome_se"].to_numpy(float).reshape(n_snp, n_env)

    # External weights are exposure-only and normalized to sum to one. The
    # normalization makes the intercept interpretable as average pleiotropy in
    # the score scale rather than depending on arbitrary score units.
    reference_bx = bx.mean(axis=1)
    if not np.isfinite(reference_bx).all() or abs(reference_bx.sum()) < 1e-12:
        raise ValueError("exposure-only score weights cannot be normalized")
    weights = reference_bx / reference_bx.sum()
    score_x = weights @ bx
    score_y = weights @ by

    env_corr = _validate_corr(environment_correlation, environments, "environment_correlation")
    ld_corr = _validate_corr(ld_correlation, snps, "ld_correlation")
    cov_x = _score_covariance(weights, sx, ld_corr, env_corr)
    cov_y = _score_covariance(weights, sy, ld_corr, env_corr)
    design = np.column_stack([np.ones(n_env), score_x])

    # Iteratively account for uncertainty in both score-exposure and
    # score-outcome associations in the regression covariance.
    theta = np.linalg.pinv(design) @ score_y
    for _ in range(max_iter):
        covariance = cov_y + float(theta[1]) ** 2 * cov_x
        inverse = np.linalg.pinv(covariance, rcond=1e-10)
        information = design.T @ inverse @ design
        new_theta = np.linalg.pinv(information, rcond=1e-10) @ (design.T @ inverse @ score_y)
        if np.max(np.abs(new_theta - theta)) < 1e-12:
            theta = new_theta
            break
        theta = new_theta
    covariance = cov_y + float(theta[1]) ** 2 * cov_x
    inverse = np.linalg.pinv(covariance, rcond=1e-10)
    information = design.T @ inverse @ design
    parameter_cov = np.linalg.pinv(information, rcond=1e-10)
    standard_errors = np.sqrt(np.maximum(np.diag(parameter_cov), 0.0))
    source = "diagonal_score_covariance"
    if environment_correlation is not None and ld_correlation is not None:
        source = "environment_and_ld_score_covariance"
    elif environment_correlation is not None:
        source = "environment_score_covariance"
    elif ld_correlation is not None:
        source = "ld_score_covariance"
    return MRGxEResult(
        method="summary_mr_gxe",
        causal_slope=float(theta[1]),
        causal_slope_se=float(standard_errors[1]),
        causal_slope_pval=_p_value(theta[1] / standard_errors[1]) if standard_errors[1] > 0 else float("nan"),
        pleiotropy_intercept=float(theta[0]),
        intercept_se=float(standard_errors[0]),
        intercept_pval=_p_value(theta[0] / standard_errors[0]) if standard_errors[0] > 0 else float("nan"),
        n_snp=n_snp,
        n_environment=n_env,
        covariance_source=source,
        score_weights=tuple(float(x) for x in weights),
        score_exposure=tuple(float(x) for x in score_x),
        score_outcome=tuple(float(x) for x in score_y),
    )
