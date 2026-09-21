"""Summary-statistic colocalization and multivariable MR."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import logsumexp


def _log_abf(beta: np.ndarray, se: np.ndarray, prior_var: float) -> np.ndarray:
    if prior_var <= 0:
        raise ValueError("prior_var must be positive")
    variance = se**2
    return 0.5 * (np.log(variance / (variance + prior_var)) + beta**2 * prior_var / (variance * (variance + prior_var)))


def coloc_abf(
    exposure: pd.DataFrame,
    outcome: pd.DataFrame,
    *,
    prior1: float = 1e-4,
    prior2: float = 1e-4,
    prior12: float = 1e-5,
    prior_var: float = 0.04,
) -> dict[str, float | int | str]:
    """Compute Wakefield approximate-BF colocalization posterior probabilities."""
    required = {"variant_id", "beta", "se"}
    for label, data in (("exposure", exposure), ("outcome", outcome)):
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError(f"{label} missing colocalization columns: {', '.join(missing)}")
    if not (0 < prior1 < 1 and 0 < prior2 < 1 and 0 < prior12 < 1):
        raise ValueError("colocalization priors must be within (0, 1)")
    exp = exposure[["variant_id", "beta", "se"]].copy()
    out = outcome[["variant_id", "beta", "se"]].copy()
    exp["variant_id"] = exp["variant_id"].astype(str)
    out["variant_id"] = out["variant_id"].astype(str)
    merged = exp.merge(out, on="variant_id", suffixes=("_1", "_2"))
    if merged.empty:
        raise ValueError("colocalization has no shared variants")
    b1 = pd.to_numeric(merged["beta_1"], errors="coerce").to_numpy(float)
    s1 = pd.to_numeric(merged["se_1"], errors="coerce").to_numpy(float)
    b2 = pd.to_numeric(merged["beta_2"], errors="coerce").to_numpy(float)
    s2 = pd.to_numeric(merged["se_2"], errors="coerce").to_numpy(float)
    if not np.isfinite(np.r_[b1, s1, b2, s2]).all() or (np.r_[s1, s2] <= 0).any():
        raise ValueError("colocalization beta/se values must be finite and se positive")
    l1 = _log_abf(b1, s1, prior_var)
    l2 = _log_abf(b2, s2, prior_var)
    n = len(merged)
    log_h0 = 0.0
    log_h1 = np.log(prior1) + logsumexp(l1)
    log_h2 = np.log(prior2) + logsumexp(l2)
    pair_values = (l1[:, None] + l2[None, :]).ravel()
    pair_values = pair_values[~np.eye(n, dtype=bool).ravel()]
    log_h3 = np.log(prior1 * prior2) + logsumexp(pair_values) if len(pair_values) else -np.inf
    log_h4 = np.log(prior12) + logsumexp(l1 + l2)
    logs = np.asarray([log_h0, log_h1, log_h2, log_h3, log_h4], dtype=float)
    posterior = np.exp(logs - logsumexp(logs))
    lead_index = int(np.argmax(l1 + l2))
    return {
        "nsnp": int(n),
        "lead_variant": str(merged.iloc[lead_index]["variant_id"]),
        "PP0": float(posterior[0]),
        "PP1": float(posterior[1]),
        "PP2": float(posterior[2]),
        "PP3": float(posterior[3]),
        "PP4": float(posterior[4]),
    }


def run_mvmr(
    exposures: pd.DataFrame,
    outcome: pd.DataFrame,
    *,
    min_snps: int = 3,
) -> pd.DataFrame:
    """Run inverse-variance weighted multivariable MR from long exposure data."""
    required_exp = {"variant_id", "exposure_id", "beta", "se"}
    required_out = {"variant_id", "beta", "se"}
    missing_exp = sorted(required_exp - set(exposures.columns))
    missing_out = sorted(required_out - set(outcome.columns))
    if missing_exp:
        raise ValueError(f"MVMR exposures missing columns: {', '.join(missing_exp)}")
    if missing_out:
        raise ValueError(f"MVMR outcome missing columns: {', '.join(missing_out)}")
    exp = exposures[["variant_id", "exposure_id", "beta", "se"]].copy()
    if exp.duplicated(["variant_id", "exposure_id"]).any():
        raise ValueError("MVMR exposure variant_id/exposure_id pairs must be unique")
    exp["variant_id"] = exp["variant_id"].astype(str)
    out = outcome[["variant_id", "beta", "se"]].copy()
    out["variant_id"] = out["variant_id"].astype(str)
    pivot = exp.pivot(index="variant_id", columns="exposure_id", values="beta")
    merged = pivot.join(out.set_index("variant_id").rename(columns={"beta": "outcome_beta", "se": "outcome_se"}), how="inner").dropna()
    if len(merged) < max(min_snps, len(pivot.columns) + 1):
        raise ValueError("MVMR has too few complete shared variants")
    exposure_ids = list(pivot.columns)
    x = merged[exposure_ids].to_numpy(dtype=float)
    y = merged["outcome_beta"].to_numpy(dtype=float)
    se_y = merged["outcome_se"].to_numpy(dtype=float)
    if (se_y <= 0).any() or not (np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(se_y).all()):
        raise ValueError("MVMR beta/se values must be finite and outcome se positive")
    weights = 1.0 / (se_y**2)
    information = x.T @ (weights[:, None] * x)
    covariance = np.linalg.pinv(information)
    beta = covariance @ (x.T @ (weights * y))
    residual = y - x @ beta
    q = float(np.sum(weights * residual**2))
    df = max(1, len(y) - len(exposure_ids))
    se = np.sqrt(np.maximum(0.0, np.diag(covariance)))
    records = []
    for index, exposure_id in enumerate(exposure_ids):
        pval = float(2 * stats.t.sf(abs(beta[index] / se[index]), df=df)) if se[index] > 0 else np.nan
        records.append(
            {
                "exposure_id": str(exposure_id),
                "beta": float(beta[index]),
                "se": float(se[index]),
                "pval": pval,
                "nsnp": int(len(merged)),
                "q": q,
                "q_df": int(df),
            }
        )
    return pd.DataFrame(records)
