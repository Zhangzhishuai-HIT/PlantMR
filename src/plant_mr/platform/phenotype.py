"""Plant phenotype cleaning and multi-environment summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class PhenotypeQCResult:
    matrix: pd.DataFrame
    audit: dict[str, Any]


def as_phenotype_matrix(data: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(data, pd.DataFrame):
        raise ValueError("phenotype must be a pandas DataFrame")
    if {"sample_id", "trait", "value"}.issubset(data.columns):
        if data.duplicated(["sample_id", "trait"]).any():
            raise ValueError("phenotype long table has duplicate sample_id/trait pairs")
        matrix = data.pivot(index="sample_id", columns="trait", values="value")
    elif "sample_id" in data.columns:
        matrix = data.set_index("sample_id").copy()
    elif not isinstance(data.index, pd.RangeIndex):
        matrix = data.copy()
    else:
        raise ValueError("phenotype requires sample_id, or long columns sample_id/trait/value")
    if matrix.index.duplicated().any():
        raise ValueError("phenotype sample_id values must be unique")
    if matrix.empty or matrix.shape[1] == 0:
        raise ValueError("phenotype matrix has no traits")
    matrix.index = matrix.index.astype(str)
    matrix.columns = matrix.columns.astype(str)
    matrix = matrix.apply(pd.to_numeric, errors="coerce")
    if np.isinf(matrix.to_numpy(dtype=float)).any():
        raise ValueError("phenotype contains infinite values")
    return matrix


def _impute(matrix: pd.DataFrame, method: str) -> pd.DataFrame:
    if method not in {"mean", "median", "most_frequent"}:
        raise ValueError("impute must be one of: mean, median, most_frequent")
    result = matrix.copy()
    for column in result.columns:
        values = result[column]
        if values.notna().sum() == 0:
            raise ValueError(f"cannot impute trait with no observed values: {column}")
        if method == "mean":
            fill = float(values.mean())
        elif method == "median":
            fill = float(values.median())
        else:
            fill = float(values.mode().iloc[0])
        result[column] = values.fillna(fill)
    return result


def qc_phenotype(
    matrix: pd.DataFrame,
    *,
    missing_threshold: float = 0.5,
    impute: str | None = None,
    transform: str = "none",
    outlier_z: float | None = 4.0,
    remove_outliers: bool = False,
) -> PhenotypeQCResult:
    if not 0 <= missing_threshold <= 1:
        raise ValueError("missing_threshold must be within [0, 1]")
    if outlier_z is not None and outlier_z <= 0:
        raise ValueError("outlier_z must be positive or None")
    work = as_phenotype_matrix(matrix)
    audit: dict[str, Any] = {
        "samples_input": int(work.shape[0]),
        "traits_input": int(work.shape[1]),
        "samples_removed_missingness": 0,
        "traits_removed_missingness": 0,
        "imputation": impute or "none",
        "transform": transform,
        "outliers_flagged": 0,
        "outliers_removed": 0,
    }
    sample_mask = work.isna().mean(axis=1) <= missing_threshold
    audit["samples_removed_missingness"] = int((~sample_mask).sum())
    work = work.loc[sample_mask].copy()
    trait_mask = work.isna().mean(axis=0) <= missing_threshold
    audit["traits_removed_missingness"] = int((~trait_mask).sum())
    work = work.loc[:, trait_mask].copy()
    if work.empty:
        raise ValueError("phenotype QC removed all samples or traits")
    if impute is not None:
        work = _impute(work, impute)
    if transform == "none":
        pass
    elif transform == "zscore":
        std = work.std(axis=0, ddof=1).replace(0, 1.0)
        work = (work - work.mean(axis=0)) / std
    elif transform == "log1p":
        if (work <= -1).any().any():
            raise ValueError("log1p transformation requires all values > -1")
        work = np.log1p(work)
    elif transform == "boxcox":
        transformed = {}
        for column in work.columns:
            values = work[column].to_numpy(dtype=float)
            if np.all(values <= 0):
                raise ValueError("boxcox transformation requires positive values")
            transformed[column] = stats.boxcox(values)[0]
        work = pd.DataFrame(transformed, index=work.index)
    else:
        raise ValueError("transform must be one of: none, zscore, log1p, boxcox")
    if outlier_z is not None:
        z = (work - work.mean(axis=0)) / work.std(axis=0, ddof=1).replace(0, 1.0)
        flags = z.abs() > outlier_z
        audit["outliers_flagged"] = int(flags.to_numpy().sum())
        if remove_outliers:
            work = work.mask(flags)
            audit["outliers_removed"] = int(flags.to_numpy().sum())
    audit["samples_output"] = int(work.shape[0])
    audit["traits_output"] = int(work.shape[1])
    return PhenotypeQCResult(work, audit)


def merge_environments(data: pd.DataFrame, *, method: str = "mean") -> pd.DataFrame:
    """Merge repeated environment records using mean, BLUE-like correction or BLUP shrinkage."""
    required = {"sample_id", "trait", "environment", "value"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"environment phenotype missing required columns: {', '.join(missing)}")
    method = method.lower()
    if method not in {"mean", "blue", "blup"}:
        raise ValueError("method must be one of: mean, blue, blup")
    work = data[list(required)].copy()
    work["value"] = pd.to_numeric(work["value"], errors="coerce")
    work = work.dropna(subset=["value"])
    if work.empty:
        raise ValueError("environment phenotype has no finite values")
    records = []
    for (trait, sample), group in work.groupby(["trait", "sample_id"], sort=True):
        n = len(group)
        raw_mean = float(group["value"].mean())
        if method == "mean":
            value = raw_mean
        else:
            trait_data = work.loc[work["trait"] == trait]
            grand = float(trait_data["value"].mean())
            env_means = trait_data.groupby("environment")["value"].mean()
            adjusted = group["value"].to_numpy(dtype=float) - group["environment"].map(env_means).to_numpy() + grand
            blue_value = float(np.mean(adjusted))
            if method == "blue":
                value = blue_value
            else:
                within = float(trait_data.groupby("sample_id")["value"].agg(lambda x: np.var(x, ddof=1) if len(x) > 1 else 0).mean())
                between = float(trait_data.groupby("sample_id")["value"].mean().var(ddof=1)) if trait_data["sample_id"].nunique() > 1 else 0.0
                lam = within / max(between, 1e-12)
                reliability = n / (n + lam) if lam > 0 else 1.0
                value = grand + reliability * (blue_value - grand)
        records.append(
            {
                "sample_id": str(sample),
                "trait": str(trait),
                "value": float(value),
                "n_environment": int(n),
                "method": method,
            }
        )
    return pd.DataFrame(records).sort_values(["trait", "sample_id"], kind="mergesort").reset_index(drop=True)
