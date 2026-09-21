"""Normalization of external GWAS/QTL summary statistics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .contracts import read_table


_ASSOCIATION_COLUMNS = [
    "variant_id", "trait", "feature_id", "tissue", "stage", "environment",
    "beta", "se", "pval", "eaf", "n", "species", "assembly", "source", "source_method",
]


def normalize_association(
    data: pd.DataFrame,
    *,
    trait: str | None = None,
    feature_id: str | None = None,
    tissue: str | None = None,
    stage: str | None = None,
    environment: str | None = None,
    species: str,
    assembly: str,
    source: str,
    source_method: str,
) -> pd.DataFrame:
    """Map common GWAS/QTL column names into one auditable summary contract."""
    work = data.copy()
    variant_column = "variant_id" if "variant_id" in work.columns else "SNP" if "SNP" in work.columns else None
    if variant_column is None:
        raise ValueError("association data require variant_id or SNP")
    missing = sorted({"beta", "se", "pval"} - set(work.columns))
    if missing:
        raise ValueError(f"association data missing required columns: {', '.join(missing)}")
    result = pd.DataFrame(index=work.index)
    result["variant_id"] = work[variant_column].astype(str)
    if result["variant_id"].eq("").any() or result["variant_id"].duplicated().any():
        raise ValueError("association variant identifiers must be non-empty and unique")
    def optional_column(name: str, override: str | None) -> object:
        if override is not None:
            return override
        return work[name].astype(str) if name in work.columns else ""

    result["trait"] = optional_column("trait", trait)
    result["feature_id"] = optional_column("feature_id", feature_id)
    for column, value in (("tissue", tissue), ("stage", stage), ("environment", environment)):
        result[column] = optional_column(column, value)
    for column in ("beta", "se", "pval"):
        result[column] = pd.to_numeric(work[column], errors="coerce")
    result["eaf"] = pd.to_numeric(work["eaf"], errors="coerce") if "eaf" in work.columns else np.nan
    result["n"] = pd.to_numeric(work["n"], errors="coerce") if "n" in work.columns else np.nan
    if result[["beta", "se", "pval"]].isna().any().any():
        raise ValueError("association beta, se and pval must be finite numeric values")
    if (result["se"] <= 0).any() or ((result["pval"] < 0) | (result["pval"] > 1)).any():
        raise ValueError("association se must be positive and pval must lie within [0, 1]")
    if result["eaf"].notna().any() and ((result["eaf"].dropna() <= 0) | (result["eaf"].dropna() >= 1)).any():
        raise ValueError("association eaf must lie within (0, 1)")
    result["species"] = species
    result["assembly"] = assembly
    result["source"] = str(source)
    result["source_method"] = str(source_method)
    return result[_ASSOCIATION_COLUMNS]


def load_association(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    return normalize_association(read_table(path), source=str(path), **kwargs)


def require_context(data: pd.DataFrame, *, species: str, assembly: str) -> None:
    """Fail when an imported table declares a different species or assembly."""
    for field, expected in (("species", species), ("assembly", assembly)):
        if field in data.columns:
            declared = {str(value) for value in data[field].dropna().unique() if str(value)}
            if declared and declared != {expected}:
                raise ValueError(f"association {field} mismatch: expected {expected}, found {sorted(declared)}")
