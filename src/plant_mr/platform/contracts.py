"""Shared tabular data contracts for PlantMR platform inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


class InputContractError(ValueError):
    """A declared platform input does not satisfy its role contract."""


_CONTRACTS = {
    "genotype": ("genotype-long", ("sample_id", "variant_id", "dosage")),
    "phenotype": ("phenotype-long", ("sample_id", "trait", "value")),
    "expression": ("molecular-long", ("sample_id", "feature_id", "value")),
    "metabolite": ("molecular-long", ("sample_id", "feature_id", "value")),
    "protein": ("molecular-long", ("sample_id", "feature_id", "value")),
    "annotation": ("annotation", ("feature_id", "chromosome", "position")),
    "gene_annotation": ("gene-annotation", ("feature_id", "chromosome", "start", "end")),
    "gwas": ("gwas-results", ("variant_id", "chromosome", "position", "pval")),
    "go_annotation": ("go-annotation", ("feature_id", "go_term")),
    "selected_features": ("selected-features", ("feature_id",)),
    "edges": ("causal-edges", ("source", "target", "beta", "se", "pval")),
    "environment_correlation": (
        "environment-correlation",
        ("environment", "environment_2", "correlation"),
    ),
    "covariates": ("covariates-wide", ("sample_id",)),
    "kinship": ("kinship-square", ("sample_id",)),
    "ld": ("ld-square", ("variant_id",)),
}


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    try:
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline()
        if "\t" in first_line:
            separator = "\t"
        elif "," in first_line:
            separator = ","
        else:
            separator = "\t"
        return pd.read_csv(path, sep=separator)
    except Exception as exc:
        raise InputContractError(f"cannot read input table {path}: {exc}") from exc


def _finite(df: pd.DataFrame, column: str, role: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise InputContractError(f"{role}: column '{column}' contains non-finite values")
    return values


def _numeric_allow_missing(df: pd.DataFrame, column: str, role: str) -> pd.Series:
    raw = df[column]
    values = pd.to_numeric(raw, errors="coerce")
    invalid_text = raw.notna() & values.isna()
    if invalid_text.any() or np.isinf(values.dropna().to_numpy(dtype=float)).any():
        raise InputContractError(f"{role}: column '{column}' contains non-numeric or infinite values")
    return values


def validate_input_file(
    path: str | Path,
    role: str,
    *,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate one non-summary platform input and return a serializable audit."""
    path = Path(path)
    if role not in _CONTRACTS:
        return {"contract": "untyped", "path": str(path), "exists": path.exists()}
    contract, required = _CONTRACTS[role]
    df = read_table(path)
    if df.empty:
        raise InputContractError(f"{role}: input table is empty")
    if role in {"genotype", "phenotype"}:
        long_required = {"sample_id", "variant_id", "dosage"} if role == "genotype" else {"sample_id", "trait", "value"}
        if not long_required.issubset(df.columns):
            if "sample_id" not in df.columns or len(df.columns) < 2:
                raise InputContractError(f"{role}: expected long format or a wide table with sample_id")
            wide = df.set_index("sample_id")
            if wide.index.duplicated().any():
                raise InputContractError(f"{role}: sample_id values must be unique")
            for column in wide.columns:
                _numeric_allow_missing(wide, column, role)
            return {
                "contract": f"{role}-wide",
                "path": str(path),
                "exists": True,
                "rows": int(len(df)),
                "columns": list(df.columns),
            }
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise InputContractError(f"{role}: missing required columns: {', '.join(missing)}")
    for column in (
        "sample_id", "variant_id", "trait", "feature_id", "environment", "environment_2",
        "source", "target",
    ):
        if column in df.columns and df[column].astype(str).str.strip().eq("").any():
            raise InputContractError(f"{role}: column '{column}' contains empty identifiers")

    if role == "genotype":
        dosage = _numeric_allow_missing(df, "dosage", role)
        ploidy_raw = (metadata or {}).get("ploidy", "")
        if ploidy_raw not in (None, ""):
            try:
                ploidy = float(ploidy_raw)
            except (TypeError, ValueError) as exc:
                raise InputContractError("metadata.ploidy must be numeric when genotype data are supplied") from exc
            if ploidy <= 0 or (dosage < 0).any() or (dosage > ploidy).any():
                raise InputContractError(f"genotype: dosage must lie within [0, {ploidy:g}]")
        if df.duplicated(["sample_id", "variant_id"]).any():
            raise InputContractError("genotype: sample_id/variant_id pairs must be unique")
    elif role in {"phenotype", "expression", "metabolite", "protein"}:
        _numeric_allow_missing(df, "value", role)
        identity = ["sample_id", "trait"] if role == "phenotype" else ["sample_id", "feature_id"]
        if df.duplicated(identity).any():
            raise InputContractError(f"{role}: {'/'.join(identity)} pairs must be unique")
    elif role == "annotation":
        position = _finite(df, "position", role)
        if (position < 1).any():
            raise InputContractError("annotation: position must be >= 1")
        if df["feature_id"].duplicated().any():
            raise InputContractError("annotation: feature_id values must be unique")
    elif role == "gene_annotation":
        for column in ("start", "end"):
            _finite(df, column, role)
        if (pd.to_numeric(df["start"]) < 1).any() or (pd.to_numeric(df["end"]) < pd.to_numeric(df["start"])).any():
            raise InputContractError("gene_annotation: start/end coordinates are invalid")
    elif role == "gwas":
        _finite(df, "position", role)
        pval = _finite(df, "pval", role)
        if ((pval < 0) | (pval > 1)).any():
            raise InputContractError("gwas: pval must lie within [0, 1]")
        if df["variant_id"].duplicated().any():
            raise InputContractError("gwas: variant_id values must be unique")
    elif role == "go_annotation":
        if df["go_term"].astype(str).str.strip().eq("").any():
            raise InputContractError("go_annotation: go_term must not be empty")
    elif role == "selected_features":
        if df["feature_id"].duplicated().any():
            raise InputContractError("selected_features: feature_id values must be unique")
    elif role == "edges":
        for column in ("beta", "se", "pval"):
            _finite(df, column, role)
        if (pd.to_numeric(df["se"]) <= 0).any() or ((pd.to_numeric(df["pval"]) < 0) | (pd.to_numeric(df["pval"]) > 1)).any():
            raise InputContractError("edges: se must be positive and pval must lie within [0, 1]")
    elif role == "environment_correlation":
        correlation = _finite(df, "correlation", role)
        if ((correlation < -1) | (correlation > 1)).any():
            raise InputContractError("environment_correlation: correlation must be within [-1, 1]")
    elif role == "covariates":
        cov = df.set_index("sample_id")
        if cov.index.duplicated().any():
            raise InputContractError("covariates: sample_id values must be unique")
        for column in cov.columns:
            _finite(cov, column, role)
    elif role in {"kinship", "ld"}:
        identifier = "sample_id" if role == "kinship" else "variant_id"
        square = df.set_index(identifier)
        if square.index.duplicated().any() or square.columns.duplicated().any():
            raise InputContractError(f"{role}: row and column identifiers must be unique")
        if set(square.index.astype(str)) != set(square.columns.astype(str)):
            raise InputContractError(f"{role}: row and column identifiers must match")
        for column in square.columns:
            _finite(square, column, role)

    return {"contract": contract, "path": str(path), "exists": True, "rows": int(len(df)), "columns": list(df.columns)}
