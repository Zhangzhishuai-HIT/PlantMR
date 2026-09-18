from dataclasses import asdict, dataclass
import math
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import chi2


_REQUIRED = {
    "SNP", "environment", "environment_value", "exposure_beta", "exposure_se",
    "outcome_beta", "outcome_se",
}


@dataclass(frozen=True)
class GxEResult:
    """Summary-statistics GLS estimate for a linear environment interaction."""

    method: str
    intercept: float
    intercept_se: float
    intercept_pval: float
    slope: float
    slope_se: float
    slope_pval: float
    n_observation: int
    n_snp: int
    n_environment: int
    q: float
    q_pval: float
    q_df: int
    covariance_source: str
    covariance_rank: int

    def as_dict(self):
        return asdict(self)


def _two_sided_p(z: float) -> float:
    return math.erfc(abs(float(z)) / math.sqrt(2.0))


def _validate_long_table(table: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(table, pd.DataFrame):
        raise ValueError("GxE MR requires a pandas DataFrame")
    missing = sorted(_REQUIRED.difference(table.columns))
    if missing:
        raise ValueError("GxE MR missing columns: " + ", ".join(missing))
    if table.empty:
        raise ValueError("GxE MR requires at least one SNP-by-environment row")
    work = table.copy()
    work["SNP"] = work["SNP"].astype(str)
    work["environment"] = work["environment"].astype(str)
    if work[["SNP", "environment"]].duplicated().any():
        raise ValueError("GxE MR requires one row per SNP and environment")
    numeric = [
        "environment_value", "exposure_beta", "exposure_se", "outcome_beta", "outcome_se",
    ]
    for column in numeric:
        work[column] = pd.to_numeric(work[column], errors="coerce")
        if work[column].isna().any() or not np.isfinite(work[column].to_numpy()).all():
            raise ValueError("GxE MR column %s contains non-finite values" % column)
    if (work["exposure_beta"] == 0).any():
        raise ValueError("GxE MR requires nonzero exposure beta")
    if (work["exposure_se"] <= 0).any() or (work["outcome_se"] <= 0).any():
        raise ValueError("GxE MR requires positive standard errors")
    counts = work.groupby("SNP")["environment"].nunique()
    if counts.nunique() != 1 or counts.iloc[0] != work["environment"].nunique():
        raise ValueError("GxE MR requires a complete environment grid for every SNP")
    env_per_snp = {
        snp: frozenset(group["environment"])
        for snp, group in work.groupby("SNP", sort=False)
    }
    if len(set(env_per_snp.values())) != 1:
        raise ValueError("GxE MR requires the same environment set for every SNP")
    if work["environment"].nunique() < 2:
        raise ValueError("GxE MR requires at least two environments")
    if work["environment_value"].nunique() < 2:
        raise ValueError("GxE MR requires at least two distinct environment values")
    env_values = work.groupby("environment")["environment_value"].nunique()
    if (env_values != 1).any():
        raise ValueError("environment_value must be constant within each environment")
    return work


def _correlation_matrix(correlation: Optional[pd.DataFrame], labels, name: str) -> np.ndarray:
    labels = [str(label) for label in labels]
    if correlation is None:
        return np.eye(len(labels), dtype=float)
    if not isinstance(correlation, pd.DataFrame) or correlation.empty:
        raise ValueError("%s must be a non-empty square DataFrame" % name)
    matrix = correlation.copy()
    matrix.index = matrix.index.astype(str)
    matrix.columns = matrix.columns.astype(str)
    if matrix.index.duplicated().any() or matrix.columns.duplicated().any():
        raise ValueError("%s identifiers must be unique" % name)
    if set(matrix.index) != set(labels) or set(matrix.columns) != set(labels):
        raise ValueError("%s identifiers must exactly match the GxE table" % name)
    matrix = matrix.loc[labels, labels].apply(pd.to_numeric, errors="coerce")
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("%s contains non-finite values" % name)
    if not np.allclose(values, values.T, atol=1e-10):
        raise ValueError("%s must be symmetric" % name)
    if not np.allclose(np.diag(values), 1.0, atol=1e-8):
        raise ValueError("%s must have unit diagonal" % name)
    if np.linalg.eigvalsh(values).min() < -1e-8:
        raise ValueError("%s must be positive semidefinite" % name)
    return values


def select_gxe_instruments(
    table: pd.DataFrame,
    p_threshold: float = 5e-8,
    f_threshold: float = 10.0,
    maf_threshold: float = 0.01,
) -> Tuple[pd.DataFrame, dict]:
    """Select instruments that pass QC in every environment.

    Requiring complete-grid passage prevents the environment slope from being
    identified by different SNP sets in different environments.
    """
    required = {"SNP", "exposure_pval", "exposure_beta", "exposure_se", "eaf"}
    missing = sorted(required.difference(table.columns))
    if missing:
        raise ValueError("GxE instrument selection missing columns: " + ", ".join(missing))
    work = _validate_long_table(table)
    work["exposure_pval"] = pd.to_numeric(work["exposure_pval"], errors="coerce")
    work["eaf"] = pd.to_numeric(work["eaf"], errors="coerce")
    if work[["exposure_pval", "eaf"]].isna().any().any():
        raise ValueError("GxE instrument selection requires finite pval and eaf")
    if ((work["exposure_pval"] < 0) | (work["exposure_pval"] > 1)).any():
        raise ValueError("exposure_pval must be within [0, 1]")
    if ((work["eaf"] <= 0) | (work["eaf"] >= 1)).any():
        raise ValueError("eaf must be within (0, 1)")
    work["f_stat"] = (work["exposure_beta"] / work["exposure_se"]) ** 2
    maf = np.minimum(work["eaf"], 1.0 - work["eaf"])
    pass_p = work["exposure_pval"] <= p_threshold
    pass_f = work["f_stat"] >= f_threshold
    pass_maf = maf >= maf_threshold
    per_snp = pd.DataFrame({"p": pass_p, "f": pass_f, "maf": pass_maf}, index=work.index).groupby(work["SNP"])
    pass_all = per_snp.all()
    bad_p = int((~per_snp["p"].all()).sum())
    bad_f = int((~per_snp["f"].all()).sum())
    bad_maf = int((~per_snp["maf"].all()).sum())
    keep_snps = pass_all.index[pass_all.all(axis=1)].tolist()
    selected = work[work["SNP"].isin(keep_snps)].sort_values(["SNP", "environment"]).reset_index(drop=True)
    audit = {
        "input_rows": int(len(work)),
        "input_snps": int(work["SNP"].nunique()),
        "excluded_pval": bad_p,
        "excluded_f": bad_f,
        "excluded_maf": bad_maf,
        "excluded_incomplete_qc": int(work["SNP"].nunique() - len(keep_snps)),
        "selected": int(len(keep_snps)),
        "selected_rows": int(len(selected)),
    }
    return selected, audit


def gxe_ivw(
    table: pd.DataFrame,
    *,
    environment_correlation: Optional[pd.DataFrame] = None,
    ld_correlation: Optional[pd.DataFrame] = None,
) -> GxEResult:
    """Estimate a pooled and environment-modified MR effect by GLS.

    For each SNP/environment cell, the ratio is ``beta_y / beta_x``. The
    two-column design is ``[1, environment_value]``. The diagonal ratio
    variance uses the first-order delta method. Optional environment and LD
    correlation matrices turn those standard errors into a block covariance;
    no correlation is silently assumed when they are omitted.
    """
    work = _validate_long_table(table)
    snps = sorted(work["SNP"].unique())
    environments = sorted(work["environment"].unique())
    work = work.set_index(["SNP", "environment"]).loc[
        pd.MultiIndex.from_product([snps, environments], names=["SNP", "environment"])
    ].reset_index()
    bx = work["exposure_beta"].to_numpy(dtype=float)
    sx = work["exposure_se"].to_numpy(dtype=float)
    by = work["outcome_beta"].to_numpy(dtype=float)
    sy = work["outcome_se"].to_numpy(dtype=float)
    ratios = by / bx
    variances = sy ** 2 / bx ** 2 + (by ** 2 * sx ** 2 / bx ** 4)
    if np.any(~np.isfinite(variances)) or np.any(variances <= 0):
        raise ValueError("GxE MR produced invalid ratio variances")
    ratio_se = np.sqrt(variances)
    env_corr = _correlation_matrix(environment_correlation, environments, "environment_correlation")
    ld_corr = _correlation_matrix(ld_correlation, snps, "ld_correlation")
    base_corr = np.kron(ld_corr, env_corr)
    covariance = ratio_se[:, None] * base_corr * ratio_se[None, :]
    covariance_rank = int(np.linalg.matrix_rank(covariance, tol=1e-10))
    covariance_inverse = np.linalg.pinv(covariance, rcond=1e-10)
    z = work["environment_value"].to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(work)), z])
    information = design.T @ covariance_inverse @ design
    if np.linalg.matrix_rank(information) < 2:
        raise ValueError("GxE design is rank deficient")
    information_inverse = np.linalg.pinv(information, rcond=1e-10)
    params = information_inverse @ (design.T @ covariance_inverse @ ratios)
    residual = ratios - design @ params
    q = float(residual.T @ covariance_inverse @ residual)
    q_df = max(int(len(ratios) - 2), 1)
    covariance_source = "diagonal_ratio_variance"
    if environment_correlation is not None and ld_correlation is not None:
        covariance_source = "environment_and_ld_correlation"
    elif environment_correlation is not None:
        covariance_source = "environment_correlation"
    elif ld_correlation is not None:
        covariance_source = "ld_correlation"
    se = np.sqrt(np.maximum(np.diag(information_inverse), 0.0))
    return GxEResult(
        method="gxe_ivw",
        intercept=float(params[0]),
        intercept_se=float(se[0]),
        intercept_pval=_two_sided_p(params[0] / se[0]) if se[0] > 0 else float("nan"),
        slope=float(params[1]),
        slope_se=float(se[1]),
        slope_pval=_two_sided_p(params[1] / se[1]) if se[1] > 0 else float("nan"),
        n_observation=int(len(work)),
        n_snp=len(snps),
        n_environment=len(environments),
        q=q,
        q_pval=float(chi2.sf(q, df=q_df)),
        q_df=q_df,
        covariance_source=covariance_source,
        covariance_rank=covariance_rank,
    )
