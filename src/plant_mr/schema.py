from dataclasses import dataclass
import math
from typing import Iterable

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = (
    "SNP",
    "effect_allele",
    "other_allele",
    "beta",
    "se",
    "pval",
)
OPTIONAL_COLUMNS = ("eaf", "n", "trait", "species", "assembly", "tissue", "stage", "environment", "ploidy")
ALLELES = frozenset("ACGT")


class SchemaError(ValueError):
    """Raised when summary statistics violate the PlantMR input contract."""


@dataclass(frozen=True)
class ValidationResult:
    label: str
    data: pd.DataFrame


def _finite_numeric(data: pd.DataFrame, column: str, label: str) -> None:
    values = pd.to_numeric(data[column], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy()).all():
        raise SchemaError(f"{label}: column {column} contains non-finite values")


def validate_summary(data: pd.DataFrame, label: str) -> ValidationResult:
    if not isinstance(data, pd.DataFrame):
        raise SchemaError(f"{label}: expected a pandas DataFrame")
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise SchemaError(f"{label}: missing required columns: {', '.join(missing)}")
    if data.empty:
        raise SchemaError(f"{label}: summary statistics are empty")
    result = data.copy()
    result["SNP"] = result["SNP"].astype(str)
    if result["SNP"].eq("").any() or result["SNP"].duplicated().any():
        raise SchemaError(f"{label}: SNP identifiers must be non-empty and unique")
    for column in ("beta", "se", "pval"):
        _finite_numeric(result, column, label)
        result[column] = pd.to_numeric(result[column])
    if (result["se"] <= 0).any():
        raise SchemaError(f"{label}: se must be greater than zero")
    if ((result["pval"] < 0) | (result["pval"] > 1)).any():
        raise SchemaError(f"{label}: pval must be within [0, 1]")
    if "eaf" in result.columns:
        _finite_numeric(result, "eaf", label)
        result["eaf"] = pd.to_numeric(result["eaf"])
        if ((result["eaf"] <= 0) | (result["eaf"] >= 1)).any():
            raise SchemaError(f"{label}: eaf must be within (0, 1)")
    else:
        result["eaf"] = np.nan
    for column in ("effect_allele", "other_allele"):
        result[column] = result[column].astype(str).str.upper()
        if (~result[column].isin(ALLELES)).any():
            raise SchemaError(f"{label}: {column} must contain single DNA alleles A/C/G/T")
    if (result["effect_allele"] == result["other_allele"]).any():
        raise SchemaError(f"{label}: effect_allele and other_allele must differ")
    return ValidationResult(label=label, data=result)


def read_summary(path: str, label: str) -> ValidationResult:
    data = pd.read_csv(path, sep=None, engine="python")
    return validate_summary(data, label=label)
