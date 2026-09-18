from dataclasses import asdict, dataclass
import math
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import chi2


@dataclass(frozen=True)
class MRResult:
    method: str
    beta: float
    se: float
    pval: float
    nsnp: int
    q: Optional[float] = None
    q_pval: Optional[float] = None
    tau2: Optional[float] = None
    intercept: Optional[float] = None
    intercept_se: Optional[float] = None
    intercept_pval: Optional[float] = None

    def as_dict(self):
        return asdict(self)


def _normal_two_sided(z: float) -> float:
    return math.erfc(abs(float(z)) / math.sqrt(2.0))


def _result(method: str, beta: float, se: float, nsnp: int, q: Optional[float] = None,
            tau2: Optional[float] = None, intercept: Optional[float] = None,
            intercept_se: Optional[float] = None) -> MRResult:
    pval = _normal_two_sided(beta / se) if se > 0 and np.isfinite(se) else float("nan")
    q_pval = None if q is None or nsnp < 2 else float(chi2.sf(q, df=nsnp - 1))
    intercept_pval = None
    if intercept is not None and intercept_se is not None and intercept_se > 0:
        intercept_pval = _normal_two_sided(intercept / intercept_se)
    return MRResult(
        method=method, beta=float(beta), se=float(se), pval=float(pval), nsnp=int(nsnp),
        q=q, q_pval=q_pval, tau2=tau2, intercept=intercept,
        intercept_se=intercept_se, intercept_pval=intercept_pval,
    )


def _check_table(table: pd.DataFrame) -> None:
    required = {"exposure_beta", "exposure_se", "outcome_beta", "outcome_se"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError(f"missing estimator columns: {', '.join(sorted(missing))}")
    if len(table) == 0:
        raise ValueError("MR requires at least one instrument")


def _ratios_and_variances(table: pd.DataFrame):
    bx = table["exposure_beta"].to_numpy(dtype=float)
    by = table["outcome_beta"].to_numpy(dtype=float)
    sx = table["exposure_se"].to_numpy(dtype=float)
    sy = table["outcome_se"].to_numpy(dtype=float)
    if np.any(bx == 0) or np.any(sx <= 0) or np.any(sy <= 0):
        raise ValueError("MR requires nonzero exposure beta and positive standard errors")
    return by / bx, (sy ** 2 / bx ** 2) + (by ** 2 * sx ** 2 / bx ** 4)


def wald_ratio(beta_exposure: float, se_exposure: float, beta_outcome: float, se_outcome: float) -> MRResult:
    if beta_exposure == 0 or se_exposure <= 0 or se_outcome <= 0:
        raise ValueError("Wald ratio requires nonzero exposure beta and positive standard errors")
    beta = beta_outcome / beta_exposure
    variance = (se_outcome ** 2 / beta_exposure ** 2) + ((beta_outcome ** 2 * se_exposure ** 2) / beta_exposure ** 4)
    return _result("wald_ratio", beta, math.sqrt(variance), 1)


def ivw_fixed(table: pd.DataFrame) -> MRResult:
    _check_table(table)
    ratios, variances = _ratios_and_variances(table)
    weights = 1.0 / variances
    beta = float(np.sum(weights * ratios) / np.sum(weights))
    se = float(math.sqrt(1.0 / np.sum(weights)))
    q = float(np.sum(weights * (ratios - beta) ** 2)) if len(ratios) > 1 else None
    return _result("ivw_fixed", beta, se, len(ratios), q=q)


def ivw_random(table: pd.DataFrame) -> MRResult:
    _check_table(table)
    ratios, variances = _ratios_and_variances(table)
    fixed_weights = 1.0 / variances
    fixed_beta = float(np.sum(fixed_weights * ratios) / np.sum(fixed_weights))
    q = float(np.sum(fixed_weights * (ratios - fixed_beta) ** 2)) if len(ratios) > 1 else 0.0
    df = max(len(ratios) - 1, 1)
    denominator = float(np.sum(fixed_weights) - np.sum(fixed_weights ** 2) / np.sum(fixed_weights))
    tau2 = max(0.0, (q - df) / denominator) if denominator > 0 else 0.0
    weights = 1.0 / (variances + tau2)
    beta = float(np.sum(weights * ratios) / np.sum(weights))
    se = float(math.sqrt(1.0 / np.sum(weights)))
    return _result("ivw_random", beta, se, len(ratios), q=q, tau2=tau2)


def mr_egger(table: pd.DataFrame) -> MRResult:
    _check_table(table)
    if len(table) < 3:
        raise ValueError("MR-Egger requires at least three instruments")
    bx = table["exposure_beta"].to_numpy(dtype=float)
    by = table["outcome_beta"].to_numpy(dtype=float)
    sy = table["outcome_se"].to_numpy(dtype=float)
    if np.any(sy <= 0):
        raise ValueError("MR-Egger requires positive outcome se")
    design = np.column_stack([np.ones(len(table)), bx])
    weights = 1.0 / sy ** 2
    xtwx = design.T @ (weights[:, None] * design)
    covariance = np.linalg.inv(xtwx)
    params = covariance @ (design.T @ (weights * by))
    intercept, beta = params
    intercept_se = float(math.sqrt(covariance[0, 0]))
    beta_se = float(math.sqrt(covariance[1, 1]))
    return _result("mr_egger", beta, beta_se, len(table), intercept=intercept, intercept_se=intercept_se)


def leave_one_out(table: pd.DataFrame) -> pd.DataFrame:
    _check_table(table)
    if "SNP" not in table.columns:
        raise ValueError("leave-one-out analysis requires an SNP column")
    if len(table) < 2:
        raise ValueError("leave-one-out analysis requires at least two instruments")
    rows = []
    for index, snp in enumerate(table["SNP"].tolist()):
        result = ivw_fixed(table.drop(table.index[index]))
        rows.append({"removed_snp": snp, **result.as_dict()})
    return pd.DataFrame(rows)
